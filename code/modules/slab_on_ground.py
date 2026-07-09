"""
Module 1.1 — Slab on Ground (พื้นวางบนดิน)

Source: "Excel Lesson 10 RC Ground Slab GS.xlsx" (provided by user — actual
calculation worksheet used for this exact module, matches DRMK RC SDM
software output). Formulas extracted directly from the workbook's cell
formulas (sheets "Ground Slab IN" and "Ground Slab OUT"), not reverse
engineered. This supersedes the earlier version of this module that was
based only on the general textbook chapter (ALL_SDM_BasicBOOK_DRMK.pdf
Ch.6) and contained assumptions later found to be WRONG (see CHANGELOG).

CHANGELOG vs previous version:
  - Subgrade Drag now correctly uses Wu = 1.4(DL+SDL) + 1.7*LL (the
    FACTORED load), not just DL+SDL as previously (wrongly) assumed.
  - Added the PCA check (As = 1800 * S * 10 * t / fy) — third governing
    reinforcement requirement, uses the SHORT side S (not L).
  - Temperature steel ratio now depends on steel type per the sheet:
    SR24 -> 0.0025, SD40 -> 0.0018, wire mesh (CDR/CDD) -> 0.0015.
    (Previously a flat 0.0025 was assumed for all types.)
  - fy values and steel type options now match the sheet exactly:
    SR24=2350, SD40=3900, CDR (Wire Mesh SW485)=4850,
    CDD (Wire Mesh SW515)=5150 ksc. These are the sheet's stated
    (tested) yield values — confirm with advisor if nominal values
    (SR24=2400, SD40=4000) should be used instead for design.
  - Provided steel area now uses the sheet's exact bar-count formula
    As = ((100/spacing) + 1) * bar_area, not the simpler area*100/spacing.
  - Slab thickness is restricted to the 9 discrete values the sheet's
    lookup table covers (10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30 cm) —
    matches the sheet's exact-match IF() logic (no interpolation).
  - L (long side) and S (short side) plan dimensions must each fall
    within a min/max range that depends on slab thickness (from the
    sheet's lookup table, which matches book Fig. 6.32). Two variants
    are provided per the two sheets found: "IN" (พื้นภายในอาคาร/มีคาน)
    and "OUT" (พื้นภายนอกอาคาร/ไม่มีคาน) — the max-spacing values differ
    slightly between them.
"""

import math
from dataclasses import dataclass

# --- Steel types: standard nominal fy per SR24/SD30/SD40/SD50 (confirmed
# by user, per มยผ./มอก. nominal grade values) — supersedes the workbook's
# own tested fy values (2350/3900/4850/5150 for SR24/SD40/CDR/CDD) which
# were mill-certificate figures, not the standard nominal design values. ---
GS_STEEL_FY_KSC = {
    "SR24": 2400,
    "SD30": 3000,
    "SD40": 4000,
    "SD50": 5000,
}

# Temperature/shrinkage steel ratio: SR24 and SD40 confirmed against the
# workbook (Excel Lesson 10) at 0.0025 / 0.0018 respectively. SD30 and SD50
# are not covered by that source (it only had SR24/SD40/CDR/CDD) — assigned
# here by the standard ACI 318-style temperature-steel provision (ratio
# 0.0020 for fy <= ~350 MPa deformed bars, 0.0018*420/fy for fy > 420 MPa),
# giving a smooth 0.0025 -> 0.0020 -> 0.0018 -> 0.0015 progression with
# strength. Worth confirming with your advisor since it's not Excel-verified.
GS_TEMP_STEEL_RATIO = {
    "SR24": 0.0025,
    "SD30": 0.0020,
    "SD40": 0.0018,
    "SD50": 0.0015,
}

# ชนิดเหล็ก (RB/DB) กำหนดตายตัวจากชั้นคุณภาพเหล็กอยู่แล้วตามมาตรฐานผลิตภัณฑ์ — ไม่ต้องให้
# ผู้ใช้เลือกแยกต่างหาก: SR (Steel Round) = เหล็กเส้นกลม RB ตาม มอก. 20-2559,
# SD (Steel Deform) = เหล็กข้ออ้อย DB ตาม มอก. 24-2559. ใช้ร่วมกันได้ทุกโมดูลที่มีตัวเลือก
# ชั้นคุณภาพเหล็กจากชุด GS_STEEL_FY_KSC นี้ (เช่น one_way_slab).
GS_STEEL_BAR_TYPE = {
    "SR24": "RB",
    "SD30": "DB",
    "SD40": "DB",
    "SD50": "DB",
}

# เหล็กเส้นกลม (RB, ชั้นคุณภาพ SR24) มีขนาดผลิตจริงแค่ 6/9 มม. เท่านั้น ส่วนเหล็กข้ออ้อย
# (DB, ชั้นคุณภาพ SD30/SD40/SD50) ไม่มีขนาด 6/9 มม. (เล็กสุดคือ DB10) — ใช้กรองตัวเลือก
# ขนาดเหล็กใน dropdown ของทุกโมดูล ตามที่ผู้ใช้แจ้งแก้ไข (2026-07)
_RB_ONLY_DIAMETERS_MM = (6, 9)


def bar_dia_options_for_steel(steel_type: str, full_list) -> list:
    """กรองรายการขนาดเหล็ก (มม.) ให้เหลือเฉพาะขนาดที่ผลิตจริงตามชั้นคุณภาพที่เลือก:
    SR24 (RB) เหลือแค่ 6/9 มม., SD30/40/50 (DB) ตัด 6/9 มม. ออก (เหลือ DB10 ขึ้นไป)."""
    is_round = GS_STEEL_BAR_TYPE.get(steel_type) == "RB"
    if is_round:
        return [d for d in full_list if d in _RB_ONLY_DIAMETERS_MM]
    return [d for d in full_list if d not in _RB_ONLY_DIAMETERS_MM]


CONCRETE_UNIT_WEIGHT_KG_M3 = 2400.0
SUBGRADE_DRAG_F = 1.5   # book/sheet default friction coefficient (no soil data)

# Joint-spacing / dimension lookup table (matches "Ground Slab IN" sheet, rows 25-31)
JOINT_TABLE_IN = [
    {"t_cm": 10.0, "min_m": 1.0, "max_m": 5.55},
    {"t_cm": 12.5, "min_m": 1.0, "max_m": 6.55},
    {"t_cm": 15.0, "min_m": 1.0, "max_m": 7.05},
    {"t_cm": 17.5, "min_m": 1.0, "max_m": 8.05},
    {"t_cm": 20.0, "min_m": 1.0, "max_m": 8.05},
    {"t_cm": 22.5, "min_m": 1.0, "max_m": 8.05},
    {"t_cm": 25.0, "min_m": 1.0, "max_m": 8.55},
    {"t_cm": 27.5, "min_m": 1.0, "max_m": 8.55},
    {"t_cm": 30.0, "min_m": 1.0, "max_m": 9.00},
]

# "Ground Slab OUT" sheet (พื้นภายนอกอาคาร/ไม่มีคาน) — slightly different max values
JOINT_TABLE_OUT = [
    {"t_cm": 10.0, "min_m": 1.0, "max_m": 5.55},
    {"t_cm": 12.5, "min_m": 1.0, "max_m": 6.5},
    {"t_cm": 15.0, "min_m": 1.0, "max_m": 7.0},
    {"t_cm": 17.5, "min_m": 1.0, "max_m": 8.0},
    {"t_cm": 20.0, "min_m": 1.0, "max_m": 8.0},
    {"t_cm": 22.5, "min_m": 1.0, "max_m": 8.0},
    {"t_cm": 25.0, "min_m": 1.0, "max_m": 8.5},
    {"t_cm": 27.5, "min_m": 1.0, "max_m": 8.5},
    {"t_cm": 30.0, "min_m": 1.0, "max_m": 9.0},
]

ALLOWED_THICKNESS_CM = [row["t_cm"] for row in JOINT_TABLE_IN]

# Bar diameters available for the main slab reinforcement in this module (mm)
GS_BAR_DIAMETERS_MM = [6, 9, 10, 12, 16, 20, 25]


def bar_area_cm2(dia_mm: float) -> float:
    """Cross-sectional area of a single round bar, cm^2, from diameter in mm."""
    d_cm = dia_mm / 10.0
    return math.pi * d_cm ** 2 / 4.0


def provided_as_cm2_per_m(dia_mm: float, spacing_cm: float) -> float:
    """
    Steel area per metre width, per the workbook's exact formula (cell M37):
    As = ((100/spacing) + 1) * bar_area
    """
    return round(((100.0 / spacing_cm) + 1.0) * bar_area_cm2(dia_mm), 2)


def joint_table_for(slab_context: str):
    return JOINT_TABLE_IN if slab_context == "IN" else JOINT_TABLE_OUT


def lookup_dimension_limits(t_cm: float, slab_context: str = "IN"):
    """Return {min_m, max_m} for the given thickness, or None if t_cm is not
    one of the table's discrete values."""
    for row in joint_table_for(slab_context):
        if abs(row["t_cm"] - t_cm) < 1e-6:
            return {"min_m": row["min_m"], "max_m": row["max_m"]}
    return None


@dataclass
class SlabOnGroundInput:
    fc_ksc: float
    steel_type: str          # "SR24" / "SD40" / "CDR" / "CDD"
    main_bar_dia_mm: float
    main_bar_spacing_cm: float
    wD_kg_m2: float           # Superimposed Dead Load (SDL)
    wL_kg_m2: float           # Live Load (LL)
    L_m: float                # ด้านยาว (long side) — must be >= S
    S_m: float                # ด้านสั้น (short side)
    t_cm: float                # slab thickness — must be one of ALLOWED_THICKNESS_CM
    slab_context: str = "IN"  # "IN" (มีคาน) or "OUT" (ไม่มีคาน)


@dataclass
class SlabOnGroundResult:
    dead_load_kg_m2: float
    wu_kg_m2: float
    L_ge_S_ok: bool
    dimension_limits: dict
    L_within_range: bool
    S_within_range: bool
    t_ok: bool
    as_temperature_cm2_m: float
    as_subgrade_drag_cm2_m: float
    as_pca_cm2_m: float
    as_provided_cm2_m: float
    temperature_ok: bool
    subgrade_drag_ok: bool
    pca_ok: bool
    all_reinf_ok: bool
    reinf_label: str


def calculate(inp: SlabOnGroundInput) -> SlabOnGroundResult:
    fy = GS_STEEL_FY_KSC[inp.steel_type]
    t_m = inp.t_cm / 100.0

    # --- Loads (workbook rows 17-20) ---
    dead_load = CONCRETE_UNIT_WEIGHT_KG_M3 * t_m          # K17 = E10 * D21
    wu = 1.4 * (dead_load + inp.wD_kg_m2) + 1.7 * inp.wL_kg_m2   # K20

    # --- Geometry checks ---
    L_ge_S_ok = inp.L_m >= inp.S_m
    limits = lookup_dimension_limits(inp.t_cm, inp.slab_context)
    if limits is None:
        L_within_range = False
        S_within_range = False
    else:
        L_within_range = limits["min_m"] < inp.L_m < limits["max_m"]
        S_within_range = limits["min_m"] < inp.S_m < limits["max_m"]
    t_ok = inp.t_cm >= 10.0

    # --- Reinforcement requirements (workbook rows 34, 36, 38) ---
    ratio = GS_TEMP_STEEL_RATIO[inp.steel_type]
    as_temperature = ratio * 100.0 * inp.t_cm    # ratio * b(cm) * t(cm), b = 100 cm strip

    as_subgrade_drag = (SUBGRADE_DRAG_F * inp.L_m * wu) / (1.43 * fy)

    as_pca = (1800.0 * inp.S_m * 10.0 * t_m) / fy

    as_provided = provided_as_cm2_per_m(inp.main_bar_dia_mm, inp.main_bar_spacing_cm)

    temperature_ok = as_provided > as_temperature
    subgrade_drag_ok = as_provided > as_subgrade_drag
    pca_ok = as_provided > as_pca
    all_reinf_ok = temperature_ok and subgrade_drag_ok and pca_ok

    reinf_label = f"RB{inp.main_bar_dia_mm:.0f}@{inp.main_bar_spacing_cm:.0f}cm."

    return SlabOnGroundResult(
        dead_load_kg_m2=dead_load,
        wu_kg_m2=wu,
        L_ge_S_ok=L_ge_S_ok,
        dimension_limits=limits,
        L_within_range=L_within_range,
        S_within_range=S_within_range,
        t_ok=t_ok,
        as_temperature_cm2_m=as_temperature,
        as_subgrade_drag_cm2_m=as_subgrade_drag,
        as_pca_cm2_m=as_pca,
        as_provided_cm2_m=as_provided,
        temperature_ok=temperature_ok,
        subgrade_drag_ok=subgrade_drag_ok,
        pca_ok=pca_ok,
        all_reinf_ok=all_reinf_ok,
        reinf_label=reinf_label,
    )
