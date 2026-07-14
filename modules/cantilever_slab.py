"""
Module 1.4 — พื้นยื่น (Cantilever Slab)

Scope: พื้นยื่นแบบยึดแน่นที่ขอบเดียว (fixed ด้านหนึ่ง, ปลายอิสระอีกด้านหนึ่ง) ออกแบบเป็น
แถบกว้าง 1 ม. (per-meter-width strip) เหมือนพื้นทางเดียว — ไม่มี "กรณีความต่อเนื่อง" ให้เลือก
เพราะพื้นยื่นมีเงื่อนไขรองรับแบบเดียวเสมอ (fixed-free)

Source: "Cantiliver Slab.xlsx" (ผู้ใช้ให้มา — DRMK RC SDM-style export) ชีท "Calculation CS"
มีตัวอย่างคำนวณสำเร็จ 1 ชุด: fc'=150 ksc, fy1(DB,หลัก)=3000, fy2(RB,รอง)=2400, S(cantilever
projection)=1.2m, t=10cm, SDL=120, LL=200, Fin Wg.=0 — ทุกสูตรด้านล่างตรวจสอบตรงกับตัวเลข
ในไฟล์ทีละบรรทัดแล้ว (ยกเว้น Wu ที่ตั้งใจให้ต่างตามเหตุผลด้านล่าง):

  - tmin = (S_m/10) * 100 * (0.40+fy1/7000) cm — denom=10 คงที่เสมอสำหรับพื้นยื่น (ต่างจาก
    พื้นทางเดียวที่ denom=20/24/28 ตามกรณีความต่อเนื่อง) — confirmed tmin=9.9429cm ตรงไฟล์เป๊ะ
  - rho_b/rho_max/rho_min: สูตรเดียวกับโมดูลอื่น (rho_b=0.0242, rho_max=0.0182 ตรงไฟล์)
  - DL = 2400*(t/100) kg/m² (confirmed DL=240)
  - Wu = 1.4(DL+SDL) + 1.7LL ตามกฎกระทรวง พ.ศ.2566 (ไฟล์ใช้ 1.7(DL+SDL)+2.0LL แบบเก่า ให้
    Wu=1012 — ตั้งใจให้ต่างจากไฟล์ตัวอย่างเหมือนโมดูล 1.2/1.3 ทุกโมดูล)
  - FIN = 1.4*(Fin Wg.) kg/m — น้ำหนักแนวกันตก/ผนังเตี้ยที่ปลายพื้นยื่น (line load ที่ขอบอิสระ)
    ไฟล์ใช้ 1.7*(Fin Wg.) (ระบบเก่า) — โมดูลนี้ปรับเป็น 1.4 ให้สอดคล้องกับ DL factor 2566
    เหมือนกัน (Fin Wg. เป็น dead-load ชนิดหนึ่ง) — ไม่มีตัวอย่างยืนยันตรง (Fin Wg.=0 ในไฟล์
    ตัวอย่าง) แต่เป็นการปรับ factor แบบเดียวกับที่ทำกับ Wu อยู่แล้วอย่างสมเหตุสมผล
  - Mu = Wu*S²/2 + FIN*S kg-m/m — เทอมแรก (Wu*S²/2) confirmed ตรงไฟล์เป๊ะ (728.64 ที่ FIN=0)
    เทอมสอง (FIN*S, โมเมนต์จาก line load ที่ปลายอิสระ) เป็นการต่อยอดทางฟิสิกส์ที่ยังไม่มี
    ตัวอย่างไฟล์ที่ FIN>0 ให้ตรวจสอบ (เพราะตัวอย่างมี Fin Wg.=0) แต่สมเหตุสมผลตามหลักสถิตยศาสตร์
    (จุดรองรับที่ระยะ S จาก line load จุดเดียว)
  - r_design = 0.50*rho_b (จุดออกแบบ Ru1, confirmed Ru1=31.12 ตรงไฟล์)
  - d = t - cover - main_dia_mm/10/2, cover=3cm (confirmed d=6.4cm)
  - Ru2 = Mu*100/(phi_b*100*d²) (confirmed Ru2=19.77)
  - rreq = 0.85(fc'/fy)(1-sqrt(1-2Ru2/(0.85fc'))) (confirmed ~0.0072)
  - rmin = 14/fy (confirmed 0.0047)
  - As (แนวหลัก) = max(rho_used*100*d, Ast_min=0.002*100*t) — 0.002bt confirmed ตรงไฟล์
    (แถว "Ast"=2.0 พร้อม note ในไฟล์) ใช้รูปแบบ "As ต้องการสูงสุด (รวม Ast ขั้นต่ำ)" เดียวกับ
    โมดูล 1.3 (AST_MIN_RATIO=0.002 เดียวกัน)
  - Ast (แนวรอง/temperature) = GS_TEMP_STEEL_RATIO[temp_steel_type]*100*t — confirmed
    0.0025bt=2.5 ตรงไฟล์เป๊ะสำหรับ SR24 (มี note "<<[0.0025bt]" ในไฟล์ตรงกับค่าคงที่ที่ใช้ใน
    โมดูล 1.2 อยู่แล้วสำหรับ SR24)
  - Max spacing = min(bar_area/As_req*100, 3t, 45cm) แนวหลัก, min(bar_area/Ast_req*100, 5t,
    45cm) แนวรอง — สูตรเดียวกับโมดูล 1.2 เป๊ะ (confirmed S_max=24cm หลัก, 25cm รอง)
  - Vu = 1.15*(Wu*S+FIN) kg — confirmed Vu=1396.56 ตรงไฟล์เป๊ะ (ไม่มีเทอม -Wu*d แบบพื้นทางเดียว
    เพราะพื้นยื่นแรงเฉือนวิกฤตอยู่ที่หน้าตัดรองรับพอดี ไม่ใช่ระยะ d จากหน้ารองรับ — ตามที่ไฟล์แสดง)
  - phiVc = phi_v*0.53*sqrt(fc')*b*d — สูตรเดียวกับทุกโมดูล (confirmed phiVc=3531)
  - Load to beam (service, unfactored, เต็ม tributary เพราะพื้นยื่นมีจุดรองรับเดียว ไม่แบ่งครึ่ง
    เหมือนพื้นทางเดียว): DL_on_beam=(DL+SDL)*S (confirmed 432), LL_on_beam=LL*S (confirmed 240)

Excel forensic analysis สำหรับรูปวาด (Slab Diagram): sheet "Cantiliver Slab" มี chart1 (แปลน)
+ sheet "Calculation CS" มี chart2 (รูปตัด) — geometry constants (คาน 0.20x0.40, embedment
top=0.17, hook depth=0.25, cover=0.03) ตรงกับค่า OW_* ของพื้นทางเดียวเป๊ะ เหมือนทุกโมดูลก่อนหน้า
**ข้อค้นพบสำคัญที่ต่างจากฟังก์ชัน draw_ow_cantilever_section_png เดิม (ที่เขียนไว้เดาก่อนมีไฟล์
จริง)**: รูปตัดจริงมีเหล็กเสริมอยู่ "ชั้นบนเดียว" เท่านั้น (ไม่มีเหล็กล่างแยกต่างหาก) — ทั้งเหล็ก
หลัก (DB12, วิ่งตามแนวยื่น) และเหล็กรอง (RB9, แสดงเป็นจุดตัดขวาง) อยู่ที่ y~-0.03 ถึง -0.045
ใกล้ผิวบนทั้งคู่ เพราะพื้นยื่นมีแรงดึงเกิดที่ผิวบนเท่านั้น (โมเมนต์ลบที่จุดรองรับ) — ฟังก์ชันวาด
รูปใหม่ (draw_cant_section_png/draw_cant_plan_png ใน common/diagram.py) เขียนขึ้นใหม่ทั้งคู่ให้
ตรงกับ geometry จริงนี้ แทนที่ฟังก์ชันเดิม
"""

import math
from dataclasses import dataclass

from common.design_params import (
    compute_beta1, compute_rho_b, compute_rho_min, compute_rho_max, PHI_B, PHI_V,
)
from modules.slab_on_ground import (
    GS_TEMP_STEEL_RATIO, GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2,
)

CONCRETE_UNIT_WEIGHT_KG_M3 = 2400.0
COVER_CM = 3.0
TMIN_DENOM = 10.0          # พื้นยื่น: denom คงที่เสมอ (confirmed จากไฟล์)
AST_MIN_RATIO_MAIN = 0.002  # เหล็กขั้นต่ำแนวหลัก (0.002bt) — confirmed จากไฟล์ เหมือนโมดูล 1.3

ALLOWED_THICKNESS_CM = [8, 10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30]

# ขนาดเหล็กเสริม (มม.) — เหมือนโมดูลอื่น กรองตามชั้นคุณภาพผ่าน bar_dia_options_for_steel
BAR_DIAMETERS_MM = [6, 9, 10, 12, 16, 19, 20, 22, 25, 28, 32]


@dataclass
class CantileverSlabInput:
    fc_ksc: float
    main_steel_type: str          # fy1 — เหล็กหลัก (แนวยื่น, รับโมเมนต์ลบที่จุดรองรับ)
    temp_steel_type: str          # fy2 — เหล็กเสริมรอง (แนวขนานจุดรองรับ, กระจายแรง/กันร้าว)
    main_bar_dia_mm: float
    main_bar_spacing_cm: float
    temp_bar_dia_mm: float
    temp_bar_spacing_cm: float
    wD_kg_m2: float                # SDL
    wL_kg_m2: float                # LL
    fin_wg_kg_m: float             # น้ำหนักแนวกันตก/ผนังเตี้ยที่ปลายพื้นยื่น (kg/m, line load)
    S_m: float                     # ความยาวยื่น (cantilever projection)
    t_cm: float


@dataclass
class CantileverSlabResult:
    dead_load_kg_m2: float
    wu_kg_m2: float
    fin_kg_m: float
    beta1: float
    rho_b: float
    rho_min: float
    rho_max: float
    tmin_cm: float
    t_ok: bool
    mu_kgm: float
    d_cm: float
    ru_ksc: float
    rreq: float
    rho_used: float
    over_reinforced: bool
    as_req_flexure_cm2_m: float
    ast_min_main_cm2_m: float
    as_req_governing_cm2_m: float
    as_provided_cm2_m: float
    main_spacing_max_cm: float
    main_reinf_ok: bool
    ast_req_cm2_m: float
    ast_provided_cm2_m: float
    temp_spacing_max_cm: float
    temp_reinf_ok: bool
    vu_kg: float
    phi_vc_kg: float
    shear_ok: bool
    dl_on_beam_kg_m: float
    ll_on_beam_kg_m: float
    reinf_label_main: str
    reinf_label_temp: str
    main_bar_type: str
    temp_bar_type: str


def provided_as_cm2_per_m(dia_mm: float, spacing_cm: float) -> float:
    """เหล็กเสริมที่ใช้จริงต่อความกว้าง 1 ม. (สูตรเดียวกับทุกโมดูล)."""
    return round(((100.0 / spacing_cm) + 1.0) * bar_area_cm2(dia_mm), 2)


def calculate(inp: CantileverSlabInput) -> CantileverSlabResult:
    fy1 = GS_STEEL_FY_KSC[inp.main_steel_type]
    fy2 = GS_STEEL_FY_KSC[inp.temp_steel_type]
    t_m = inp.t_cm / 100.0

    # --- loads (กฎกระทรวง 2566) ---
    dead_load = CONCRETE_UNIT_WEIGHT_KG_M3 * t_m
    wu = 1.4 * (dead_load + inp.wD_kg_m2) + 1.7 * inp.wL_kg_m2
    fin = 1.4 * inp.fin_wg_kg_m   # Fin Wg. เป็น dead load ชนิดหนึ่ง ใช้ factor เดียวกับ DL/SDL

    # --- material parameters ---
    beta1 = compute_beta1(inp.fc_ksc)
    rho_b = compute_rho_b(inp.fc_ksc, fy1, beta1)
    rho_min = compute_rho_min(fy1)
    rho_max = compute_rho_max(rho_b)

    # --- minimum thickness (deflection control, denom=10 เสมอสำหรับพื้นยื่น) ---
    factor = 0.40 + fy1 / 7000.0
    tmin_cm = (inp.S_m / TMIN_DENOM) * 100.0 * factor
    t_ok = inp.t_cm >= tmin_cm

    d_cm = inp.t_cm - COVER_CM - inp.main_bar_dia_mm / 10.0 / 2.0
    r_design = 0.50 * rho_b   # จุดออกแบบทางปฏิบัติที่ใช้หา Ru1 (ยืนยันตรงตัวอย่าง)
    ru1 = r_design * fy1 * (1.0 - 0.59 * r_design * fy1 / inp.fc_ksc)

    # --- moment (ที่จุดรองรับ, โมเมนต์ลบสูงสุด) ---
    mu_kgm = wu * inp.S_m ** 2 / 2.0 + fin * inp.S_m   # kg-m ต่อความกว้าง 1 ม.
    ru2 = mu_kgm * 100.0 / (PHI_B * 100.0 * d_cm ** 2)

    under_sqrt = 1.0 - (2.0 * ru2) / (0.85 * inp.fc_ksc)
    over_reinforced = under_sqrt < 0
    if over_reinforced:
        rreq = rho_max
    else:
        rreq = 0.85 * (inp.fc_ksc / fy1) * (1.0 - math.sqrt(under_sqrt))

    rho_used = max(rreq, rho_min)
    over_reinforced = over_reinforced or (rho_used > rho_max)
    as_req_flexure = rho_used * 100.0 * d_cm

    ast_min_main = AST_MIN_RATIO_MAIN * 100.0 * inp.t_cm
    as_req_governing = max(as_req_flexure, ast_min_main)

    # --- main (flexural) reinforcement provided ---
    as_provided = provided_as_cm2_per_m(inp.main_bar_dia_mm, inp.main_bar_spacing_cm)
    main_area = bar_area_cm2(inp.main_bar_dia_mm)
    spacing_from_as_cm = (main_area / as_req_governing * 100.0) if as_req_governing > 0 else 999.0
    main_spacing_max_cm = min(spacing_from_as_cm, 3.0 * inp.t_cm, 45.0)
    main_reinf_ok = (as_provided >= as_req_governing) and (inp.main_bar_spacing_cm <= main_spacing_max_cm)

    # --- temperature / distribution reinforcement (ทิศขนานจุดรองรับ) ---
    temp_ratio = GS_TEMP_STEEL_RATIO[inp.temp_steel_type]
    ast_req = temp_ratio * 100.0 * inp.t_cm
    ast_provided = provided_as_cm2_per_m(inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm)
    temp_area = bar_area_cm2(inp.temp_bar_dia_mm)
    spacing_from_ast_cm = (temp_area / ast_req * 100.0) if ast_req > 0 else 999.0
    temp_spacing_max_cm = min(spacing_from_ast_cm, 5.0 * inp.t_cm, 45.0)
    temp_reinf_ok = (ast_provided >= ast_req) and (inp.temp_bar_spacing_cm <= temp_spacing_max_cm)

    # --- shear check (ที่หน้าตัดรองรับพอดี — ไม่มีเทอม -Wu*d แบบพื้นทางเดียว, confirmed จากไฟล์) ---
    vu = 1.15 * (wu * inp.S_m + fin)
    phi_vc = PHI_V * 0.53 * math.sqrt(inp.fc_ksc) * 100.0 * d_cm
    shear_ok = phi_vc >= vu

    # --- load transfer to supporting beam/wall (service, unfactored, เต็ม tributary) ---
    dl_on_beam = (dead_load + inp.wD_kg_m2) * inp.S_m
    ll_on_beam = inp.wL_kg_m2 * inp.S_m

    # --- ชนิดเหล็ก (RB/DB) กำหนดอัตโนมัติจากชั้นคุณภาพเหล็กที่เลือก ---
    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    temp_bar_type = GS_STEEL_BAR_TYPE[inp.temp_steel_type]

    reinf_label_main = f"{main_bar_type}{inp.main_bar_dia_mm:.0f}@{inp.main_bar_spacing_cm:.0f}cm."
    reinf_label_temp = f"{temp_bar_type}{inp.temp_bar_dia_mm:.0f}@{inp.temp_bar_spacing_cm:.0f}cm."

    return CantileverSlabResult(
        dead_load_kg_m2=dead_load, wu_kg_m2=wu, fin_kg_m=fin,
        beta1=beta1, rho_b=rho_b, rho_min=rho_min, rho_max=rho_max,
        tmin_cm=tmin_cm, t_ok=t_ok,
        mu_kgm=mu_kgm, d_cm=d_cm, ru_ksc=ru2, rreq=rreq, rho_used=rho_used,
        over_reinforced=over_reinforced,
        as_req_flexure_cm2_m=as_req_flexure, ast_min_main_cm2_m=ast_min_main,
        as_req_governing_cm2_m=as_req_governing,
        as_provided_cm2_m=as_provided, main_spacing_max_cm=main_spacing_max_cm,
        main_reinf_ok=main_reinf_ok,
        ast_req_cm2_m=ast_req, ast_provided_cm2_m=ast_provided,
        temp_spacing_max_cm=temp_spacing_max_cm, temp_reinf_ok=temp_reinf_ok,
        vu_kg=vu, phi_vc_kg=phi_vc, shear_ok=shear_ok,
        dl_on_beam_kg_m=dl_on_beam, ll_on_beam_kg_m=ll_on_beam,
        reinf_label_main=reinf_label_main, reinf_label_temp=reinf_label_temp,
        main_bar_type=main_bar_type, temp_bar_type=temp_bar_type,
    )
