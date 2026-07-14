"""
Module 1.2 — พื้นทางเดียว (One-way Slab)

Scope note: พื้นยื่น (Cantilever) is NOT handled by this module — it belongs
to module 1.4 (พื้นยื่น / Cantilever Slab) instead, per explicit user
instruction. This module only covers the 3 two-support continuity cases:
Simply Supported / One End Continuous / Both Ends Continuous.

Source: "One way Slab.xlsx" (provided by user — a DRMK RC SDM-style export
containing ONE fully worked numeric example: fc'=150 ksc, fy1(DB,main)=3000,
fy2(RB,temp)=2400, S=1.5m, L=4m, t=10cm, continuity case "Both ends
continuous.") plus the exact coordinate data for its two detail drawings
(cross-section at support, and plan-view rebar layout). Every formula below
was checked cell-by-cell against that worked example (see the numbers in
the comments) EXCEPT the moment coefficients for the 2 continuity cases
other than "both ends continuous" (see CONTINUITY_CASES note below), which
the workbook does not contain a worked example for.

Formulas confirmed exactly against the workbook's own numbers:
  - beta1 / rho_b / rho_min / rho_max: identical to common.design_params
    (rho_b=0.0242, rho_max=0.0182, rho_min=0.0047 all matched for
    fc'=150, fy=3000).
  - tmin = (S_m/denom) * 100 * (0.40 + fy1/7000) cm, denom = 20/24/28
    for Simply Supported / One End Continuous / Both Ends Continuous
    respectively (matches ACI 318 Table 9.5(a) minimum thickness ratios
    exactly) -> tmin=4.44cm confirmed for the example.
  - Wu = 1.4(DL+SDL) + 1.7LL kg/m2 — per user's explicit instruction this
    module uses กฎกระทรวง 2566 (NOT the workbook's own "1.7DL+2.0LL /
    AISC-EIT" load factors, which the workbook used for its own worked
    example — the Wu=1012 in the workbook's numbers therefore will NOT
    be reproduced exactly by this module; every OTHER formula below still
    matches the workbook once the correct Wu/Mu chain is followed through).
  - Mu = C * Wu * S^2 (kg-m/m strip), Ru1 = r*fy*(1-0.59 r fy/fc') with
    r = 0.50*rho_b (confirmed Ru1=31.12 at r=0.0121).
  - d = t - cover - main_dia_mm/10/2, cover=3cm (confirmed d=6.4cm).
  - Ru2 = Mu*100/(phi_b*100*d^2) ksc (phi_b=0.90, confirmed Ru2=5.62).
  - rreq = 0.85(fc'/fy)(1-sqrt(1-2Ru2/(0.85fc'))) (confirmed 0.0019).
  - As = max(rreq,rho_min)*100*d cm2/m (confirmed As=3.01 with rho_min
    governing since rreq<rho_min).
  - Max spacing = min(bar_area/As_req*100, 3t, 45cm) cm, for BOTH the
    main (flexural) and temperature/distribution direction (with 5t
    instead of 3t for temperature) — confirmed S_max=30cm (main) and
    25.4cm (temperature) exactly.
  - Vu = 1.15(Wu*S/2) - Wu*d_m kg (confirmed Vu=808.08).
  - phi*Vc = phi_v * 0.53 * sqrt(fc') * b * d kg, phi_v=0.85, b=100cm
    (confirmed phiVc=3531.18).
  - Load transfer to beam (SERVICE, unfactored): DL_on_beam=(DL+SDL)*S/2,
    LL_on_beam=LL*S/2 kg/m (confirmed 270 and 150 kg/m).

Temperature-steel ratio table: reuses modules.slab_on_ground.GS_TEMP_STEEL_RATIO
(SR24=0.0025 confirmed exactly against the workbook's Ast=2.5 for the long/
temperature direction; SD30/SD40/SD50 carried over from that module's own
ACI-318-style estimate — same "confirm with advisor" caveat applies here).

CONTINUITY_CASES moment coefficients — ONLY "Both ends continuous" (Con.-
1/11, Mid.+ 1/16, Con.- 1/11) is directly confirmed against the workbook.
The other 2 cases use the standard ACI 318 Section 8.3.3 "moment
coefficient method" values that are conventionally tabulated ALONGSIDE the
same tmin denominators (20/24/28) found in this exact workbook, i.e.
they are the standard textbook counterpart of the one confirmed case, not
an independent guess — but they have not been individually checked
against a DRMK worked example the way every other formula in this module
has. Worth a quick confirm with your advisor if that matters for the
thesis writeup:
  Simply Supported        : Mid.+ = 1/8,  ends = 0 (no continuity)
  One End Continuous      : continuous end Con.- = 1/10, Mid.+ = 1/14,
                             discontinuous end = 0
  Both Ends Continuous    : Con.- = 1/11, Mid.+ = 1/16, Con.- = 1/11  [CONFIRMED]

พื้นยื่น (Cantilever, tmin_denom=10, coeff=1/2 at fixed end) belongs to
module 1.4 instead — not implemented here.
"""

import math
from dataclasses import dataclass, field

from common.design_params import (
    compute_beta1, compute_rho_b, compute_rho_min, compute_rho_max, PHI_B, PHI_V,
)
from modules.slab_on_ground import (
    GS_TEMP_STEEL_RATIO, GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2,
)

CONCRETE_UNIT_WEIGHT_KG_M3 = 2400.0
COVER_CM = 3.0

ALLOWED_THICKNESS_CM = [8, 10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30]

# ขนาดเหล็กเสริม (มม.) — รวมขนาดที่พบทั่วไปทั้งเหล็กเส้นกลม (RB) และเหล็กข้ออ้อย (DB)
# ชนิดเหล็ก (RB/DB) ไม่ต้องให้ผู้ใช้เลือกแยก —กำหนดอัตโนมัติจากชั้นคุณภาพเหล็กที่เลือก
# (ดู GS_STEEL_BAR_TYPE ใน modules.slab_on_ground: SR=RB, SD=DB)
BAR_DIAMETERS_MM = [6, 9, 10, 12, 16, 19, 20, 22, 25, 28, 32]
BAR_TYPES = ["DB", "RB"]   # DB = เหล็กข้ออ้อย (deformed), RB = เหล็กเส้นกลม (round) — คงไว้เพื่ออ้างอิง

# ปลาย1(End 1) / กลางช่วง(Mid) / ปลาย2(End 2) — None = ไม่มีการออกแบบที่ตำแหน่งนั้น
# (ใช้เหล็กเสริมรองขั้นต่ำเท่านั้น)
CONTINUITY_CASES = {
    "SS": {
        "label_th": "ปลายทั้งสองข้างไม่ยึดรั้ง (Simply Supported)",
        "tmin_denom": 20,
        "coeffs": [None, 1.0 / 8, None],
    },
    "ONE": {
        "label_th": "ปลายข้างหนึ่งต่อเนื่อง (One End Continuous)",
        "tmin_denom": 24,
        "coeffs": [1.0 / 10, 1.0 / 14, None],
    },
    "BOTH": {
        "label_th": "ปลายต่อเนื่องทั้งสองด้าน (Both Ends Continuous)",
        "tmin_denom": 28,
        "coeffs": [1.0 / 11, 1.0 / 16, 1.0 / 11],
    },
}
# หมายเหตุ: พื้นยื่น (Cantilever) ไม่รวมอยู่ในโมดูลนี้ — ย้ายไปอยู่หัวข้อ 1.4
# พื้นยื่น (Cantilever Slab) ต่างหากตามที่ผู้ใช้ระบุ

POSITION_LABELS_TH = ["ปลาย 1 (End 1)", "กลางช่วง (Midspan)", "ปลาย 2 (End 2)"]


@dataclass
class OneWaySlabInput:
    fc_ksc: float
    main_steel_type: str          # fy1 — เหล็กหลัก (แนว S, รับโมเมนต์)
    temp_steel_type: str          # fy2 — เหล็กเสริมรอง (แนว L, กระจายแรง/กันร้าว)
    main_bar_dia_mm: float
    main_bar_spacing_cm: float
    temp_bar_dia_mm: float
    temp_bar_spacing_cm: float
    wD_kg_m2: float                # SDL
    wL_kg_m2: float                # LL
    S_m: float                     # short span (แนวเสริมเหล็กหลัก)
    L_m: float                     # long span (ทิศตั้งฉาก)
    t_cm: float
    continuity_case: str = "BOTH"  # key of CONTINUITY_CASES
    # หมายเหตุ: ไม่มีฟิลด์ main_bar_type/temp_bar_type แยกแล้ว — ชนิดเหล็ก (RB/DB) คำนวณ
    # อัตโนมัติจาก main_steel_type/temp_steel_type ใน calculate() ด้านล่าง (ดู
    # GS_STEEL_BAR_TYPE) ตามที่ผู้ใช้แจ้งว่าทราบชนิดเหล็กจากชั้นคุณภาพอยู่แล้ว


@dataclass
class PositionResult:
    label_th: str
    active: bool
    coeff: float
    mu_kgm: float
    d_cm: float
    ru_ksc: float
    rreq: float
    rho_used: float
    over_reinforced: bool          # rreq > rho_max (section too small)
    as_req_cm2_m: float


@dataclass
class OneWaySlabResult:
    m_ratio: float                  # S/L
    one_way_ok: bool                # m <= 0.5
    dead_load_kg_m2: float
    wu_kg_m2: float
    beta1: float
    rho_b: float
    rho_min: float
    rho_max: float
    tmin_cm: float
    t_ok: bool
    positions: list                 # list[PositionResult], len 3
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
    main_bar_type: str               # กำหนดอัตโนมัติจากชั้นคุณภาพเหล็กหลัก (SR->RB, SD->DB)
    temp_bar_type: str                # กำหนดอัตโนมัติจากชั้นคุณภาพเหล็กเสริมรอง


def provided_as_cm2_per_m(dia_mm: float, spacing_cm: float) -> float:
    """เหล็กเสริมที่ใช้จริงต่อความกว้าง 1 ม. (เหมือน Ground Slab: นับจำนวนเส้นจริง)."""
    return round(((100.0 / spacing_cm) + 1.0) * bar_area_cm2(dia_mm), 2)


def calculate(inp: OneWaySlabInput) -> OneWaySlabResult:
    fy1 = GS_STEEL_FY_KSC[inp.main_steel_type]
    fy2 = GS_STEEL_FY_KSC[inp.temp_steel_type]
    t_m = inp.t_cm / 100.0
    case = CONTINUITY_CASES[inp.continuity_case]

    # --- one-way behaviour check ---
    if inp.L_m and inp.L_m > 0:
        m_ratio = inp.S_m / inp.L_m
        one_way_ok = m_ratio <= 0.5
    else:
        m_ratio = None
        one_way_ok = True

    # --- loads (กฎกระทรวง 2566) ---
    dead_load = CONCRETE_UNIT_WEIGHT_KG_M3 * t_m
    wu = 1.4 * (dead_load + inp.wD_kg_m2) + 1.7 * inp.wL_kg_m2

    # --- material parameters (ใช้สูตรเดียวกับหน้าพารามิเตอร์การออกแบบ) ---
    beta1 = compute_beta1(inp.fc_ksc)
    rho_b = compute_rho_b(inp.fc_ksc, fy1, beta1)
    rho_min = compute_rho_min(fy1)
    rho_max = compute_rho_max(rho_b)

    # --- minimum thickness (deflection control) ---
    factor = 0.40 + fy1 / 7000.0
    tmin_cm = (inp.S_m / case["tmin_denom"]) * 100.0 * factor
    t_ok = inp.t_cm >= tmin_cm

    d_cm = inp.t_cm - COVER_CM - inp.main_bar_dia_mm / 10.0 / 2.0
    r_design = 0.50 * rho_b   # จุดออกแบบทางปฏิบัติที่ใช้หา Ru1 (ยืนยันตรงตัวอย่าง)

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

        mu_kgm = coeff * wu * inp.S_m ** 2   # kg-m ต่อความกว้าง 1 ม.
        ru = mu_kgm * 100.0 / (PHI_B * 100.0 * d_cm ** 2)   # ksc

        under_sqrt = 1.0 - (2.0 * ru) / (0.85 * inp.fc_ksc)
        over_reinforced = under_sqrt < 0
        if over_reinforced:
            rreq = rho_max   # หน้าตัดเล็กเกินไป — ใช้ rho_max เป็นค่าประมาณ ให้ผู้ใช้เพิ่ม t
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

    # --- temperature / distribution reinforcement (ทิศตั้งฉาก) ---
    temp_ratio = GS_TEMP_STEEL_RATIO[inp.temp_steel_type]
    ast_req = temp_ratio * 100.0 * inp.t_cm
    ast_provided = provided_as_cm2_per_m(inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm)
    temp_area = bar_area_cm2(inp.temp_bar_dia_mm)
    spacing_from_ast_cm = (temp_area / ast_req * 100.0) if ast_req > 0 else 999.0
    temp_spacing_max_cm = min(spacing_from_ast_cm, 5.0 * inp.t_cm, 45.0)
    temp_reinf_ok = (ast_provided >= ast_req) and (inp.temp_bar_spacing_cm <= temp_spacing_max_cm)

    # --- shear check (ที่ระยะ d จากหน้ารองรับ) ---
    vu = 1.15 * (wu * inp.S_m / 2.0) - wu * (d_cm / 100.0)
    phi_vc = PHI_V * 0.53 * math.sqrt(inp.fc_ksc) * 100.0 * d_cm
    shear_ok = phi_vc >= vu

    # --- load transfer to supporting beam (service, unfactored) ---
    dl_on_beam = (dead_load + inp.wD_kg_m2) * inp.S_m / 2.0
    ll_on_beam = inp.wL_kg_m2 * inp.S_m / 2.0

    # --- ชนิดเหล็ก (RB/DB) กำหนดอัตโนมัติจากชั้นคุณภาพเหล็กที่เลือก ไม่ต้องให้ผู้ใช้เลือกแยก ---
    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    temp_bar_type = GS_STEEL_BAR_TYPE[inp.temp_steel_type]

    reinf_label_main = f"{main_bar_type}{inp.main_bar_dia_mm:.0f}@{inp.main_bar_spacing_cm:.0f}cm."
    reinf_label_temp = f"{temp_bar_type}{inp.temp_bar_dia_mm:.0f}@{inp.temp_bar_spacing_cm:.0f}cm."

    return OneWaySlabResult(
        m_ratio=m_ratio, one_way_ok=one_way_ok,
        dead_load_kg_m2=dead_load, wu_kg_m2=wu,
        beta1=beta1, rho_b=rho_b, rho_min=rho_min, rho_max=rho_max,
        tmin_cm=tmin_cm, t_ok=t_ok,
        positions=positions, as_req_governing_cm2_m=as_req_governing,
        as_provided_cm2_m=as_provided, main_spacing_max_cm=main_spacing_max_cm,
        main_reinf_ok=main_reinf_ok,
        ast_req_cm2_m=ast_req, ast_provided_cm2_m=ast_provided,
        temp_spacing_max_cm=temp_spacing_max_cm, temp_reinf_ok=temp_reinf_ok,
        vu_kg=vu, phi_vc_kg=phi_vc, shear_ok=shear_ok,
        dl_on_beam_kg_m=dl_on_beam, ll_on_beam_kg_m=ll_on_beam,
        reinf_label_main=reinf_label_main, reinf_label_temp=reinf_label_temp,
        main_bar_type=main_bar_type, temp_bar_type=temp_bar_type,
    )
