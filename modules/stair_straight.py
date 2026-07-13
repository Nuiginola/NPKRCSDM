"""
Module 2.1 — บันไดช่วงตรง (Straight-Run Stair)

ขอบเขต: บันไดช่วงเดียว เดินตรงจากพื้นชั้นล่างขึ้นพื้นชั้นบนโดยตรง ไม่มีชานพักกลาง
(ต่างจากโมดูล 2.2 บันไดหักกลับ/U-Shape Stair ที่มีชานพักและเดิน 2 ช่วง — ยังไม่ได้ทำ)

แนวทางวิศวกรรม — "Equivalent Horizontal Span" (วิธีมาตรฐานทั่วไปสำหรับออกแบบพื้นบันได):
วิเคราะห์แผ่นพื้นเอียง (waist slab) เสมือนพื้นทางเดียวแนวราบที่มีช่วงพาด = ช่วงพาดแนวราบ
(horizontal projected span, S) เหมือนโมดูล 1.2 พื้นทางเดียวทุกประการ — สูตรโมเมนต์/
เหล็กเสริม/แรงเฉือน/ตารางความต่อเนื่อง 3 กรณี (SS/ONE/BOTH) ใช้ร่วมกับโมดูล 1.2 ผ่าน
import โดยตรง (ไม่ก็อปปี้ซ้ำ) — ต่างกันเฉพาะการคำนวณน้ำหนักบรรทุกคงที่ (Dead Load) ที่
ต้องรวมน้ำหนักตัวเอง 2 ส่วนแทนที่จะเป็นแผ่นเรียบส่วนเดียว:

  1) แผ่น waist เอียงมุม θ (cosθ = S/L_incline, L_incline = ความยาวจริงตามแนวลาด):
     น้ำหนักต่อพื้นที่ราบ 1 ตร.ม. = γc &times; t / cosθ  (หนา t วัดตั้งฉากกับแนวลาด แต่
     ปริมาตรคอนกรีตต่อพื้นที่ราบ 1 ตร.ม. มากกว่าแผ่นเรียบเพราะความยาวจริงตามแนวลาด
     มากกว่าช่วงพาดแนวราบด้วยตัวคูณ 1/cosθ)
  2) ขั้นบันได (รูปสามเหลี่ยมฐาน g สูง r วางซ้อนบน waist ทุกช่วงขั้น):
     น้ำหนักต่อพื้นที่ราบ 1 ตร.ม. = γc &times; r / 2  (พื้นที่หน้าตัดสามเหลี่ยม 0.5&times;r&times;g
     หารด้วยความกว้างช่วงขั้น g ที่มันครอบคลุมพอดี ผลลัพธ์จึงไม่ขึ้นกับ g)

  รวม: DL_self = γc &times; (t/cosθ + r/2)  kg/m² (ต่อพื้นที่ราบ)

เรขาคณิตขั้นบันได (ตัวแปรที่ผู้ใช้กรอกจริง — "ขนาดบันได" ในหน้า UI): จำนวนขั้น n (=
n_riser, จำนวนลูกตั้ง), ความยาวทั้งหมด L = (n-1) &times; ลูกนอน (ช่วงพาดแนวราบ, ป้อนตรงแทน
ลูกนอนทีละขั้น), ความกว้างบันได B (ใช้คำนวณจำนวนเหล็กเสริมหลักที่ต้องใช้จริง/น้ำหนัก
รวมลงคาน ไม่ใช้ในสูตรโมเมนต์ต่อความกว้าง 1 ม. ซึ่งไม่ขึ้นกับ B อยู่แล้ว), ความสูงระหว่างชั้น
H = n &times; ลูกตั้ง — ลูกตั้ง (rise_cm) และลูกนอน (going_cm) ต่อขั้น จึงเป็นค่าที่ "คำนวณย้อนกลับ"
จาก L/H/n (rise_cm = H/n, going_cm = L/(n-1)) แทนที่จะเป็นค่าที่ผู้ใช้กรอกตรงๆ แบบเดิม —
เก็บเป็นผลลัพธ์ (StairStraightResult.rise_cm/.going_cm) ให้โมดูลรูปวาด/รายงานเรียกใช้
ต่อ (ค่าเดียวกับที่เคยเป็นอินพุตตรง ผลการคำนวณเชิงโครงสร้างทั้งหมดจึงเหมือนเดิมทุกประการ
เพียงเปลี่ยนว่าใครเป็นคนคำนวณ ลูกตั้ง/ลูกนอน เท่านั้น) — ช่วงพาดแนวราบ S = length_m (m.)
ใช้แทน S_m ของโมดูล 1.2 ในทุกสูตร (Mu, tmin, Vu, ถ่ายน้ำหนักลงคาน) เหมือนเดิมทุกประการ

ขอบเขตที่ระบุไว้ชัดเจน:
  - ไม่รวมชานพัก (Landing) — บันไดช่วงตรงเดียวไม่มีชานพักกลาง (ย้ายไปโมดูล 2.2)
  - ไม่ตรวจสอบสัดส่วนขั้นบันไดตามกฎหมายอาคาร/สถาปัตยกรรม (เช่น ลูกตั้งสูงสุด/ลูกนอน
    ต่ำสุดที่อนุญาต, ราวจับ, ความกว้างขั้นต่ำ) — ขอบเขตของโมดูลนี้เป็นการออกแบบโครงสร้าง
    (Strength Design) ตามกฎกระทรวง พ.ศ. 2566 เท่านั้น ไม่ใช่การตรวจสอบข้อกำหนดทาง
    สถาปัตยกรรม/ความปลอดภัยการใช้งาน
  - Live Load เริ่มต้น 200 kg/m² อ้างอิงตาราง LOAD_SCHEDULE ("ระเบียง และบันได") ใน
    common/design_params.py — ผู้ใช้ปรับได้เอง
"""

import math
from dataclasses import dataclass

from common.design_params import (
    compute_beta1, compute_rho_b, compute_rho_min, compute_rho_max, PHI_B, PHI_V,
)
from modules.slab_on_ground import (
    GS_TEMP_STEEL_RATIO, GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2,
)
from modules.one_way_slab import (
    CONTINUITY_CASES, POSITION_LABELS_TH, PositionResult, provided_as_cm2_per_m,
)

CONCRETE_UNIT_WEIGHT_KG_M3 = 2400.0
COVER_CM = 3.0

ALLOWED_THICKNESS_CM = [8, 10, 12.5, 15, 17.5, 20, 22.5, 25]
BAR_DIAMETERS_MM = [6, 9, 10, 12, 16, 19, 20, 22, 25]


@dataclass
class StairStraightInput:
    fc_ksc: float
    main_steel_type: str          # fy1 — เหล็กหลัก (ตามแนวลาด, รับโมเมนต์)
    temp_steel_type: str          # fy2 — เหล็กเสริมรอง (ตามแนวขั้น, กระจายแรง/กันร้าว)
    main_bar_dia_mm: float
    main_bar_spacing_cm: float
    temp_bar_dia_mm: float
    temp_bar_spacing_cm: float
    wD_kg_m2: float                # SDL (ผิวสำเร็จ/ปูน/กระเบื้องขั้นบันได — ไม่รวมน้ำหนักตัวเอง)
    wL_kg_m2: float                # LL
    n_riser: int                   # "จำนวนขั้น n" ในหน้า UI (= จำนวนลูกตั้ง/risers)
    length_m: float                # "ความยาวทั้งหมด L" = (n-1) x ลูกนอน — ช่วงพาดแนวราบ
    width_m: float                 # "ความกว้างบันได B" — ใช้นับจำนวนเหล็กหลัก/น้ำหนักรวมลงคาน
    height_m: float                # "ความสูงระหว่างชั้น H" = n x ลูกตั้ง
    t_cm: float                    # ความหนาแผ่น waist (วัดตั้งฉากกับแนวลาด)
    continuity_case: str = "SS"    # key of CONTINUITY_CASES — บันไดช่วงตรงมักออกแบบเป็น
                                    # simply supported เป็นค่าเริ่มต้น (ต่างจากพื้นทางเดียว)


@dataclass
class StairStraightResult:
    n_going: int
    rise_cm: float                  # ลูกตั้ง R ต่อขั้น — คำนวณย้อนกลับจาก H/n (เพื่อใช้วาดรูป/
                                     # รายงาน — ดูคำอธิบายที่หัวไฟล์)
    going_cm: float                 # ลูกนอน G ต่อขั้น — คำนวณย้อนกลับจาก L/(n-1)
    S_m: float                     # ช่วงพาดแนวราบ (horizontal projected span) = length_m
    total_rise_m: float
    incline_length_m: float
    slope_deg: float
    dead_load_waist_kg_m2: float
    dead_load_steps_kg_m2: float
    dead_load_self_kg_m2: float
    wu_kg_m2: float
    beta1: float
    rho_b: float
    rho_min: float
    rho_max: float
    tmin_cm: float
    t_ok: bool
    positions: list                 # list[PositionResult], len 3 (เหมือนโมดูล 1.2)
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
    dl_on_beam_total_kg: float       # = dl_on_beam_kg_m x width_m — น้ำหนักรวมตลอดความกว้างบันได
    ll_on_beam_total_kg: float       # = ll_on_beam_kg_m x width_m
    main_bar_count: int              # จำนวนเหล็กหลักที่ต้องใช้จริงตลอดความกว้าง B (นับเป็นเส้น)
    temp_bar_count: int              # จำนวนเหล็กเสริมรองที่ต้องใช้จริงตลอดความยาวลาดจริง (เส้น)
    reinf_label_main: str
    reinf_label_temp: str
    main_bar_type: str
    temp_bar_type: str


def calculate(inp: StairStraightInput) -> StairStraightResult:
    fy1 = GS_STEEL_FY_KSC[inp.main_steel_type]
    case = CONTINUITY_CASES[inp.continuity_case]

    # --- เรขาคณิตของช่วงบันได — ผู้ใช้กรอก L (ความยาวทั้งหมด), H (ความสูงระหว่างชั้น),
    # n (จำนวนขั้น) ตรงๆ ("ขนาดบันได") แล้วคำนวณย้อนกลับเป็นลูกตั้ง/ลูกนอนต่อขั้น (rise_m/
    # going_m) จากนั้นสูตรทั้งหมดที่เหลือ (S_m, มุมลาด, น้ำหนักตัวเอง ฯลฯ) เหมือนเดิมทุก
    # ประการกับตอนที่ผู้ใช้กรอกลูกตั้ง/ลูกนอนตรงๆ ---
    n_going = max(inp.n_riser - 1, 1)
    going_m = inp.length_m / n_going
    rise_m = inp.height_m / inp.n_riser
    S_m = inp.length_m
    total_rise_m = inp.height_m
    incline_length_m = math.sqrt(S_m ** 2 + total_rise_m ** 2)
    cos_theta = (S_m / incline_length_m) if incline_length_m > 0 else 1.0
    slope_deg = math.degrees(math.atan2(total_rise_m, S_m)) if S_m > 0 else 0.0

    # --- น้ำหนักบรรทุกตัวเอง (waist เอียง + ขั้นบันไดสามเหลี่ยม) ---
    t_m = inp.t_cm / 100.0
    dl_waist = CONCRETE_UNIT_WEIGHT_KG_M3 * (t_m / cos_theta if cos_theta > 0 else t_m)
    dl_steps = CONCRETE_UNIT_WEIGHT_KG_M3 * rise_m / 2.0
    dead_load_self = dl_waist + dl_steps

    wu = 1.4 * (dead_load_self + inp.wD_kg_m2) + 1.7 * inp.wL_kg_m2

    # --- material parameters (ใช้สูตรเดียวกับหน้าพารามิเตอร์การออกแบบ) ---
    beta1 = compute_beta1(inp.fc_ksc)
    rho_b = compute_rho_b(inp.fc_ksc, fy1, beta1)
    rho_min = compute_rho_min(fy1)
    rho_max = compute_rho_max(rho_b)

    # --- minimum thickness (deflection control) — ใช้ตาราง denom เดียวกับพื้นทางเดียว
    # โดยแทนช่วงพาดด้วย S แนวราบของบันได (สอดคล้องกับวิธี Equivalent Horizontal Span
    # ที่ใช้ทั้งฉบับ — โมเมนต์/tmin/แรงเฉือนใช้ S เดียวกันตลอด) ---
    factor = 0.40 + fy1 / 7000.0
    tmin_cm = (S_m / case["tmin_denom"]) * 100.0 * factor
    t_ok = inp.t_cm >= tmin_cm

    d_cm = inp.t_cm - COVER_CM - inp.main_bar_dia_mm / 10.0 / 2.0

    positions = []
    as_req_governing = 0.0
    for label, coeff in zip(POSITION_LABELS_TH, case["coeffs"]):
        if coeff is None:
            positions.append(PositionResult(
                label_th=label, active=False, coeff=0.0, mu_kgm=0.0, d_cm=d_cm,
                ru_ksc=0.0, rreq=0.0, rho_used=0.0, over_reinforced=False,
                as_req_cm2_m=0.0,
            ))
            continue

        mu_kgm = coeff * wu * S_m ** 2   # kg-m ต่อความกว้าง 1 ม. (ราบ)
        ru = mu_kgm * 100.0 / (PHI_B * 100.0 * d_cm ** 2)   # ksc

        under_sqrt = 1.0 - (2.0 * ru) / (0.85 * inp.fc_ksc)
        over_reinforced = under_sqrt < 0
        if over_reinforced:
            rreq = rho_max
        else:
            rreq = 0.85 * (inp.fc_ksc / fy1) * (1.0 - math.sqrt(under_sqrt))

        rho_used = max(rreq, rho_min)
        over_reinforced = over_reinforced or (rho_used > rho_max)
        as_req = rho_used * 100.0 * d_cm

        positions.append(PositionResult(
            label_th=label, active=True, coeff=coeff, mu_kgm=mu_kgm, d_cm=d_cm,
            ru_ksc=ru, rreq=rreq, rho_used=rho_used, over_reinforced=over_reinforced,
            as_req_cm2_m=as_req,
        ))
        as_req_governing = max(as_req_governing, as_req)

    # --- main (flexural) reinforcement provided ---
    as_provided = provided_as_cm2_per_m(inp.main_bar_dia_mm, inp.main_bar_spacing_cm)
    main_area = bar_area_cm2(inp.main_bar_dia_mm)
    spacing_from_as_cm = (main_area / as_req_governing * 100.0) if as_req_governing > 0 else 999.0
    main_spacing_max_cm = min(spacing_from_as_cm, 3.0 * inp.t_cm, 45.0)
    main_reinf_ok = (as_provided >= as_req_governing) and (inp.main_bar_spacing_cm <= main_spacing_max_cm)

    # --- temperature / distribution reinforcement (ตามแนวขั้น) ---
    temp_ratio = GS_TEMP_STEEL_RATIO[inp.temp_steel_type]
    ast_req = temp_ratio * 100.0 * inp.t_cm
    ast_provided = provided_as_cm2_per_m(inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm)
    temp_area = bar_area_cm2(inp.temp_bar_dia_mm)
    spacing_from_ast_cm = (temp_area / ast_req * 100.0) if ast_req > 0 else 999.0
    temp_spacing_max_cm = min(spacing_from_ast_cm, 5.0 * inp.t_cm, 45.0)
    temp_reinf_ok = (ast_provided >= ast_req) and (inp.temp_bar_spacing_cm <= temp_spacing_max_cm)

    # --- shear check (ที่ระยะ d จากหน้ารองรับ, ใช้ S แนวราบเช่นเดียวกับ Mu) ---
    vu = 1.15 * (wu * S_m / 2.0) - wu * (d_cm / 100.0)
    phi_vc = PHI_V * 0.53 * math.sqrt(inp.fc_ksc) * 100.0 * d_cm
    shear_ok = phi_vc >= vu

    # --- load transfer to supporting beam (service, unfactored) ---
    dl_on_beam = (dead_load_self + inp.wD_kg_m2) * S_m / 2.0
    ll_on_beam = inp.wL_kg_m2 * S_m / 2.0
    # น้ำหนักรวมตลอดความกว้างบันได B (ใช้ตรวจสอบ/ออกแบบคานรองรับจริง — คานรับบันได 1 ช่วง
    # เต็มความกว้าง ไม่ใช่แค่ต่อเมตร)
    dl_on_beam_total = dl_on_beam * inp.width_m
    ll_on_beam_total = ll_on_beam * inp.width_m

    # --- ชนิดเหล็ก (RB/DB) กำหนดอัตโนมัติจากชั้นคุณภาพเหล็กที่เลือก ---
    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    temp_bar_type = GS_STEEL_BAR_TYPE[inp.temp_steel_type]

    reinf_label_main = f"{main_bar_type}{inp.main_bar_dia_mm:.0f}@{inp.main_bar_spacing_cm:.0f}cm."
    reinf_label_temp = f"{temp_bar_type}{inp.temp_bar_dia_mm:.0f}@{inp.temp_bar_spacing_cm:.0f}cm."

    # --- จำนวนเหล็กจริงที่ต้องใช้ (เส้น) — เหล็กหลักวางเรียงขวางความกว้าง B (ระยะห่างตาม
    # main_bar_spacing_cm), เหล็กเสริมรองวางเรียงตามแนวยาวจริงของบันได (ระยะห่างตาม
    # temp_bar_spacing_cm) — ปัดขึ้นเสมอ (จำนวนเส้นจริงต้องไม่น้อยกว่าที่คำนวณ) ---
    main_bar_count = int(math.ceil(inp.width_m * 100.0 / inp.main_bar_spacing_cm)) + 1 \
        if inp.width_m > 0 else 0
    temp_bar_count = int(math.ceil(incline_length_m * 100.0 / inp.temp_bar_spacing_cm)) + 1 \
        if incline_length_m > 0 else 0

    return StairStraightResult(
        n_going=n_going, rise_cm=rise_m * 100.0, going_cm=going_m * 100.0,
        S_m=S_m, total_rise_m=total_rise_m,
        incline_length_m=incline_length_m, slope_deg=slope_deg,
        dead_load_waist_kg_m2=dl_waist, dead_load_steps_kg_m2=dl_steps,
        dead_load_self_kg_m2=dead_load_self, wu_kg_m2=wu,
        beta1=beta1, rho_b=rho_b, rho_min=rho_min, rho_max=rho_max,
        tmin_cm=tmin_cm, t_ok=t_ok,
        positions=positions, as_req_governing_cm2_m=as_req_governing,
        as_provided_cm2_m=as_provided, main_spacing_max_cm=main_spacing_max_cm,
        main_reinf_ok=main_reinf_ok,
        ast_req_cm2_m=ast_req, ast_provided_cm2_m=ast_provided,
        temp_spacing_max_cm=temp_spacing_max_cm, temp_reinf_ok=temp_reinf_ok,
        vu_kg=vu, phi_vc_kg=phi_vc, shear_ok=shear_ok,
        dl_on_beam_kg_m=dl_on_beam, ll_on_beam_kg_m=ll_on_beam,
        dl_on_beam_total_kg=dl_on_beam_total, ll_on_beam_total_kg=ll_on_beam_total,
        main_bar_count=main_bar_count, temp_bar_count=temp_bar_count,
        reinf_label_main=reinf_label_main, reinf_label_temp=reinf_label_temp,
        main_bar_type=main_bar_type, temp_bar_type=temp_bar_type,
    )
