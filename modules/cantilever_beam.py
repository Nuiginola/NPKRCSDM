"""
Module 3.3 — คานยื่น (Cantilever Beam)

Scope: คานยื่นแบบยึดแน่นด้านเดียว (fixed-free, ไม่มีจุดรองรับที่ปลายอิสระ) รับ line load
(DL/LL) + point load ได้สูงสุด 10 จุด (วัดจากจุดรองรับ/โคนคาน) — วิเคราะห์หาแรง
(reaction/SFD/BMD) แล้วออกแบบเหล็กเสริมหลัก (เหล็กบน = เหล็กรับแรงดึงหลัก เพราะโมเมนต์เป็น
ลบ/hogging ตลอดความยาวคานยื่น, เหล็กล่าง = เหล็กยึดขั้นต่ำ/hanger) และเหล็กปลอก

สถิตยศาสตร์ของคานยื่น (fixed-free) เป็นกรณีเดียวกันเป๊ะกับ "ปลายยื่น (overhang)" ที่ใช้ใน
โมดูล 3.2 (คานต่อเนื่อง) ซึ่ง verify ผ่านการตรวจสอบอย่างเข้มงวดแล้ว (global equilibrium,
โมเมนต์ปลายอิสระ ≈0, ความต่อเนื่องของเส้นกราฟ, boundary test) — โมดูลนี้จึง reuse ฟังก์ชัน
_overhang_end_moment_and_load / _overhang_local_arrays จาก modules.continuous_beam ตรงๆ
แทนการ re-derive สูตรใหม่ (ลดความเสี่ยง/เวลาพัฒนา เพราะเป็นสถิตยศาสตร์เดียวกันเป๊ะ x_s=0 คือ
จุดรองรับ/โคนคาน, x_s=L คือปลายอิสระ):
  M(ที่จุดรองรับ) = -(w*L²/2 + Σ(P·x))   (hogging เสมอ ไม่มีโมเมนต์บวกในคานยื่นแท้ๆ)
  V(ที่จุดรองรับ) = w*L + ΣP              (= ปฏิกิริยา, ค่าแรงเฉือนสูงสุด)

สูตรออกแบบเหล็กเสริม (flexure, รวมการจัดเหล็กหลายชั้นอัตโนมัติ) และเหล็กปลอก (shear/
stirrup) ใช้ฟังก์ชันร่วมเดียวกับโมดูล 3.1/3.2 ทุกประการ (_flexure_design/_stirrup_design
จาก modules.beam_single_span) — ไม่มีสูตรใหม่ที่ต้องคิดเพิ่มในโมดูลนี้เลย เป็นการประกอบ
ส่วนที่ verify แล้วเข้าด้วยกัน

น้ำหนักบรรทุก: Wu = 1.4(DL_line+DL_selfweight) + 1.7(LL_line) ตามกฎกระทรวง พ.ศ. 2566
(สอดคล้องกับทุกโมดูลก่อนหน้า) น้ำหนักจุด (point load) แต่ละจุดแปลงเป็น
Pu = 1.4·P_DL + 1.7·P_LL แยกทีละจุดก่อนรวมเข้าสถิตยศาสตร์
"""

from dataclasses import dataclass

from common.design_params import (
    compute_beta1, compute_rho_b, compute_rho_min, compute_rho_max,
)
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, CONCRETE_UNIT_WEIGHT_KG_M3
from modules.beam_single_span import (
    PointLoad, _flexure_design, _stirrup_design, reinf_label_with_layers,
    DEFAULT_STIRRUP_LEGS, BAR_DIAMETERS_MM, STIRRUP_DIAMETERS_MM,
    BEAM_WIDTH_CM_OPTIONS, BEAM_DEPTH_CM_OPTIONS,
)
from modules.continuous_beam import _overhang_end_moment_and_load, _overhang_local_arrays

MAX_POINT_LOADS = 10


@dataclass
class CantileverBeamInput:
    fc_ksc: float
    main_steel_type: str
    stirrup_steel_type: str
    b_cm: float
    h_cm: float
    L_m: float                    # ความยาวคานยื่น (จากจุดรองรับ/โคนคาน ถึงปลายอิสระ)
    line_load_dl_kg_m: float
    line_load_ll_kg_m: float
    point_loads: list             # list[PointLoad], x_m จากจุดรองรับ (โคนคาน)
    main_bar_dia_mm: float
    stirrup_bar_dia_mm: float
    stirrup_legs: int = DEFAULT_STIRRUP_LEGS
    stirrup_spacing_use_cm: float = 15.0


@dataclass
class CantileverBeamResult:
    self_weight_kg_m: float
    wu_kg_m: float
    pu_loads: list                 # list[(x_m, pu_kg)]
    end_moment_kgm: float          # โมเมนต์ที่จุดรองรับ (ลบ/hogging เสมอ)
    reaction_kg: float             # = Vu,max ที่จุดรองรับ
    x_arr: list
    v_arr: list
    m_arr: list
    beta1: float
    rho_b: float
    rho_min: float
    rho_max: float
    top: object            # FlexureDesign — เหล็กบน (แรงดึงหลัก, ตามโมเมนต์ลบที่จุดรองรับ)
    bottom: object          # FlexureDesign — เหล็กล่าง (nominal/hanger)
    stirrup: object
    main_bar_type: str
    stirrup_bar_type: str
    reinf_label_top: str
    reinf_label_bottom: str
    reinf_label_stirrup: str


def calculate(inp: CantileverBeamInput) -> CantileverBeamResult:
    fy_main = GS_STEEL_FY_KSC[inp.main_steel_type]
    fy_stirrup = GS_STEEL_FY_KSC[inp.stirrup_steel_type]

    b_m = inp.b_cm / 100.0
    h_m = inp.h_cm / 100.0
    self_weight = CONCRETE_UNIT_WEIGHT_KG_M3 * b_m * h_m   # kg/m
    wd_total = inp.line_load_dl_kg_m + self_weight
    wu = 1.4 * wd_total + 1.7 * inp.line_load_ll_kg_m

    pts = sorted(inp.point_loads, key=lambda p: p.x_m)
    pu_loads = [(p.x_m, 1.4 * p.p_dl_kg + 1.7 * p.p_ll_kg) for p in pts]

    end_moment, reaction = _overhang_end_moment_and_load(inp.L_m, wu, pu_loads)
    x_arr, v_arr, m_arr = _overhang_local_arrays(inp.L_m, wu, pu_loads)

    beta1 = compute_beta1(inp.fc_ksc)
    rho_b = compute_rho_b(inp.fc_ksc, fy_main, beta1)
    rho_min = compute_rho_min(fy_main)
    rho_max = compute_rho_max(rho_b)

    top = _flexure_design(
        abs(end_moment), inp.b_cm, inp.h_cm, inp.fc_ksc, fy_main,
        inp.main_bar_dia_mm, inp.stirrup_bar_dia_mm,
        beta1, rho_b, rho_min, rho_max, is_nominal_only=False,
    )
    bottom = _flexure_design(
        0.0, inp.b_cm, inp.h_cm, inp.fc_ksc, fy_main,
        inp.main_bar_dia_mm, inp.stirrup_bar_dia_mm,
        beta1, rho_b, rho_min, rho_max, is_nominal_only=True,
    )

    stirrup = _stirrup_design(
        reaction, inp.b_cm, top.d_cm, inp.fc_ksc, fy_stirrup,
        inp.stirrup_legs, inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm,
    )

    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    stirrup_bar_type = GS_STEEL_BAR_TYPE[inp.stirrup_steel_type]

    reinf_label_top = reinf_label_with_layers(top, main_bar_type, inp.main_bar_dia_mm)
    reinf_label_bottom = reinf_label_with_layers(bottom, main_bar_type, inp.main_bar_dia_mm)
    reinf_label_stirrup = f"{inp.stirrup_legs}-{stirrup_bar_type}{inp.stirrup_bar_dia_mm:.0f}@{inp.stirrup_spacing_use_cm:.0f}cm."

    return CantileverBeamResult(
        self_weight_kg_m=self_weight, wu_kg_m=wu, pu_loads=pu_loads,
        end_moment_kgm=end_moment, reaction_kg=reaction,
        x_arr=x_arr, v_arr=v_arr, m_arr=m_arr,
        beta1=beta1, rho_b=rho_b, rho_min=rho_min, rho_max=rho_max,
        top=top, bottom=bottom, stirrup=stirrup,
        main_bar_type=main_bar_type, stirrup_bar_type=stirrup_bar_type,
        reinf_label_top=reinf_label_top, reinf_label_bottom=reinf_label_bottom,
        reinf_label_stirrup=reinf_label_stirrup,
    )
