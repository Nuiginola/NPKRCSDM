"""
Module 1.3 — พื้นสองทาง (Two-way Slab)

Source: "Two way Slab.xlsx" (provided by user — a DRMK RC SDM-style export
containing ONE fully worked numeric example: fc'=150 ksc, fy=3000 ksc,
S=2.5m, L=3m (m=S/L=0.833), t=10cm, DB12 rebar, SDL=150 kg/m2, LL=200 kg/m2,
case = "1 Edge Discontinuous" (เสาขอบสั้นไม่ต่อเนื่อง 1 ด้าน). Method is
ACI 318-63 "Method 3" (moment-coefficient method, 9 standard edge-condition
cases), applied here with a SINGLE combined coefficient per position against
the total factored load Wu (Mu = C * Wu * S^2 for BOTH directions — the
workbook does NOT split dead/live load coefficients the way the full ACI
textbook table does).

============================================================================
IMPORTANT — confirmed vs. standard-sourced data, READ BEFORE RELYING ON THIS
============================================================================
The reference workbook only contains a fully worked coefficient table for
ONE of the 9 standard edge-condition cases ("1 Edge Discontinuous", i.e.
CASE2 below), and only directly gives numbers for the SHORT direction
(11 points, m=0.50-1.00 step 0.05) — confirmed cell-by-cell against the
workbook's own "Two way Slab" sheet (columns GO:GY, rows 56-106). The long
direction of that same case has exactly ONE confirmed data point (the
worked example itself, m=0.833: con-=0.041, mid+=0.031) — everything else
below is estimated.

All coefficients for CASE1, CASE3, CASE4, CASE5, and the un-shown long
direction of CASE2, come from an external published lecture-note reference
(a university RC-design course PDF reproducing the classic ACI 318-63
9-case moment-coefficient table) — see project doc for the exact source.
That source uses a DIFFERENT case-numbering convention than the workbook,
so the case-to-case mapping below was determined by physical/structural
reasoning (checking which columns have zero negative-moment coefficient in
which direction — a case with a fully-discontinuous edge pair in one
direction always shows all-zero negative coefficients in that direction —
plus a magnitude sanity check for the "interior panel" and "1 edge
discontinuous" assignments), NOT by directly matching case labels. The one
genuinely independent cross-check available (CASE2, m=0.80 breakpoint,
BOTH directions) matched the workbook's confirmed numbers closely, which
is reassuring but is still only a single-point check, not a full
verification.

The user was informed of this limitation and explicitly asked to proceed
using the best standard values available, with a clear caveat — per their
instruction, this module ships with all 5 named cases, but:
  - CASE2 short direction: ✅ fully confirmed against the workbook (exact).
  - CASE2 long direction: ⚠ spot-checked at one point only.
  - CASE1, CASE3, CASE4, CASE5: ⚠ NOT verified against the workbook or any
    second independent source. Please confirm against a proper textbook
    (or your advisor) before relying on these for the actual thesis
    design — this is explicitly flagged in the UI and the printed report.

Cases 6-9 (the un-named sub-variants of "2 edges discontinuous" and
"3 edges discontinuous" — e.g. adjacent-vs-opposite, or which side the
surviving continuous edge is on) are NOT implemented — the workbook itself
only names cases 1-5 (by discontinuous-edge COUNT), leaving 6-9 unlabeled
and unconfirmed. Deferred to a later round if/when better reference data
is available.

Within a case, "mid+" (positive/midspan coefficient) and "disc-" (negative
coefficient at a discontinuous edge, where that edge exists) are DERIVED
from "con-" (negative coefficient at a continuous edge) using two ratios
discovered by analysing the one confirmed case's full 11-point curve:
    mid+  ≈ 0.75 * con-   (ratio held within 1.5% across all 11 m-points)
    disc- ≈ 0.50 * con-   (ratio held within 3% across all 11 m-points)
This derivation was cross-checked against CASE2's long-direction data point
(predicted mid+=0.0307 vs. confirmed 0.031 — excellent agreement) which is
why it was preferred over directly summing the external source's separate
dead-load/live-load coefficients (that approach was tried first and gave
answers roughly 2x too high compared to the confirmed worked example, so
it was discarded — kept in project-doc history as a rejected approach).
CASE5 (all 4 edges discontinuous, con-=0 identically) cannot use this ratio
(0.75*0=0 is meaningless) — its mid+ is instead taken directly from the
external source's dead-load coefficient, which for that specific case
happens to equal the live-load coefficient exactly (physically sensible:
with no continuous edge anywhere, there is no adjacent-span pattern-loading
effect to make dead/live coefficients differ).

Formulas confirmed exactly against the workbook's own numbers (the
calculation chain around the coefficients, independent of which case is
selected):
  - tmin = (2*S_cm + 2*L_cm) / 180  cm.
  - DL = 2400 * t_m  kg/m2.
  - Wu = 1.4*(DL+SDL) + 1.7*LL kg/m2 (กฎกระทรวง 2566, per standing project
    instruction — same substitution already applied in Module 1.2).
  - Mu = C * Wu * S^2  kg-m/m  — S (short side), SQUARED, for BOTH short
    AND long direction moments (a known quirk/simplification of this
    particular method — confirmed exactly: Z28=265.75=0.04*1063*2.5^2).
  - d_short = t - cover - dia_short/10/2 cm.
  - d_long  = t - cover - dia_short/10 - dia_long/10/2 cm (two-layer mesh:
    long-direction bars sit under/over the short-direction bars, losing one
    additional full short-bar diameter of effective depth).
  - Ru1 = r*fy*(1-0.59*r*fy/fc'), r = 0.50*rho_b (same as Module 1.2/1.1).
  - Ru2 = Mu*100/(phi_b*100*d^2) ksc, phi_b=0.90.
  - rreq = 0.85*(fc'/fy)*(1-sqrt(1-2*Ru2/(0.85*fc'))).
  - As = max(rreq, rho_min) * 100 * d  cm2/m.
  - Ast(min) = 0.002 * b * t  cm2/m, FLAT — confirmed to NOT vary by fy
    (unlike Module 1.2's temperature steel, which does vary by fy).
  - Max spacing = min(bar_area/As_req*100, 3t, 45cm) cm (same pattern as
    Module 1.2).
  - Vu = 1.15 * Wu * S / 4  kg (per metre strip) — NOTE this is a
    DIFFERENT formula from Module 1.2's one-way shear (Wu*S/2), and has NO
    "-Wu*d" reduction term.
  - phi*Vc = phi_v * 0.53 * sqrt(fc') * b * d kg, phi_v=0.85 (same formula
    as Module 1.2).
  - A SECOND shear check exists in the workbook: (2/3)*phi*Vc compared
    against Vu, reported as an independent Ok/NG. Its formulas trace to no
    further cells in the workbook (a dead-end for the forensic analysis) —
    its precise code basis/engineering intent is UNCONFIRMED. Implemented
    here as a second, more conservative pass/fail flag; treat with caution.
  - Load transfer to supporting beam (service, unfactored, per metre run of
    beam): triangular tributary area = w*S/3; trapezoidal tributary area =
    w*(S/2)*(1 - m^2/3), with m = S/L rounded to 2 decimals — both formulas
    verified exactly against all 4 target numbers in the workbook.

พื้นยื่น (Cantilever) is out of scope for this module — belongs to 1.4.
"""

import math
from dataclasses import dataclass

from common.design_params import (
    compute_beta1, compute_rho_b, compute_rho_min, compute_rho_max, PHI_B, PHI_V,
)
from modules.slab_on_ground import (
    GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2,
)

CONCRETE_UNIT_WEIGHT_KG_M3 = 2400.0
COVER_CM = 3.0
AST_MIN_RATIO = 0.002   # flat, ไม่ขึ้นกับ fy (ยืนยันจากไฟล์ตัวอย่าง)

ALLOWED_THICKNESS_CM = [8, 10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30]
BAR_DIAMETERS_MM = [6, 9, 10, 12, 16, 19, 20, 22, 25, 28, 32]

M_BREAKPOINTS = [0.50, 0.55, 0.60, 0.65, 0.70, 0.75, 0.80, 0.85, 0.90, 0.95, 1.00]

POSITION_LABELS_TH = ["ขอบต่อเนื่อง (Con.-)", "กลางช่วง (Mid.+)", "ขอบไม่ต่อเนื่อง (Disc.-)"]


def _derive_mid(con_list, factor=0.75):
    return [round(c * factor, 5) for c in con_list]


def _derive_disc(con_list, factor=0.50):
    return [round(c * factor, 5) for c in con_list]


# ตารางค่าสัมประสิทธิ์โมเมนต์ (con-/mid+/disc-) ต่อทิศทาง ต่อกรณี — ดู docstring
# ด้านบนสำหรับที่มาและระดับความมั่นใจของแต่ละชุดตัวเลข
TWO_WAY_CASES = {
    "CASE1": {
        "label_th": "4 ด้านต่อเนื่อง (4 Edge Continuous — พื้นภายใน)",
        "confirmed": False,
        "short": {
            "has_disc": False,
            "con": [0.094, 0.092, 0.089, 0.085, 0.081, 0.076, 0.071, 0.066, 0.060, 0.055, 0.050],
        },
        "long": {
            "has_disc": False,
            "con": [0.006, 0.008, 0.011, 0.015, 0.019, 0.024, 0.029, 0.034, 0.040, 0.045, 0.050],
        },
    },
    "CASE2": {
        "label_th": "ไม่ต่อเนื่อง 1 ด้าน (1 Edge Discontinuous)",
        "confirmed": True,   # ทิศทางสั้น ยืนยันครบ / ทิศทางยาว ยืนยัน 1 จุด
        "short": {
            "has_disc": True,
            "con":  [0.085, 0.077, 0.069, 0.0655, 0.062, 0.0585, 0.055, 0.0515, 0.048, 0.0445, 0.041],
            "mid":  [0.064, 0.058, 0.052, 0.0495, 0.047, 0.044, 0.041, 0.0385, 0.036, 0.0335, 0.031],
            "disc": [0.042, 0.0385, 0.035, 0.033, 0.031, 0.029, 0.027, 0.0255, 0.024, 0.0225, 0.021],
        },
        "long": {
            "has_disc": False,
            "con": [0.010, 0.014, 0.018, 0.024, 0.029, 0.036, 0.041, 0.046, 0.052, 0.056, 0.061],
        },
    },
    "CASE3": {
        "label_th": "ไม่ต่อเนื่อง 2 ด้าน ติดกัน (2 Edge Discontinuous, adjacent — พื้นมุม)",
        "confirmed": False,
        "short": {
            "has_disc": True,
            "con": [0.086, 0.084, 0.081, 0.077, 0.074, 0.069, 0.065, 0.060, 0.055, 0.050, 0.045],
        },
        "long": {
            "has_disc": True,
            "con": [0.006, 0.007, 0.010, 0.014, 0.017, 0.022, 0.027, 0.031, 0.037, 0.041, 0.045],
        },
    },
    "CASE4": {
        "label_th": "ไม่ต่อเนื่อง 3 ด้าน (3 Edge Discontinuous)",
        "confirmed": False,
        "short": {
            "has_disc": False,   # ด้านสั้นไม่ต่อเนื่องทั้งคู่ — ไม่มีขอบต่อเนื่องให้คำนวณ Con.-
            "fully_disc": True,
            "con": [0.0] * 11,
            "mid": [0.084, 0.0755, 0.0665, 0.059, 0.0515, 0.0455, 0.0395, 0.0345, 0.030, 0.026, 0.0225],
        },
        "long": {
            "has_disc": True,
            "con": [0.022, 0.028, 0.035, 0.043, 0.050, 0.056, 0.061, 0.065, 0.070, 0.072, 0.076],
        },
    },
    "CASE5": {
        "label_th": "ไม่ต่อเนื่องทั้ง 4 ด้าน (4 Edge Discontinuous — พื้นแยกโดด)",
        "confirmed": False,
        "short": {
            "has_disc": False,
            "fully_disc": True,
            "con": [0.0] * 11,
            "mid": [0.095, 0.088, 0.081, 0.074, 0.068, 0.061, 0.056, 0.050, 0.045, 0.040, 0.036],
        },
        "long": {
            "has_disc": False,
            "fully_disc": True,
            "con": [0.0] * 11,
            "mid": [0.006, 0.008, 0.010, 0.013, 0.016, 0.019, 0.023, 0.026, 0.029, 0.033, 0.036],
        },
    },
}

# เติม mid/disc ที่ยังไม่ได้ระบุตรง ๆ ด้วยอัตราส่วนที่ยืนยันจาก CASE2 (0.75 / 0.50 ของ con-)
for _case_key, _case in TWO_WAY_CASES.items():
    for _dir_key in ("short", "long"):
        _d = _case[_dir_key]
        if "mid" not in _d:
            _d["mid"] = _derive_mid(_d["con"])
        if _d.get("has_disc") and "disc" not in _d:
            _d["disc"] = _derive_disc(_d["con"])


def _interp(m_ratio: float, table: list) -> float:
    """เชิงเส้น interpolate ค่าจากตาราง M_BREAKPOINTS (0.50-1.00 step 0.05)."""
    m = max(0.50, min(1.00, m_ratio))
    for i in range(len(M_BREAKPOINTS) - 1):
        m0, m1 = M_BREAKPOINTS[i], M_BREAKPOINTS[i + 1]
        if m0 <= m <= m1:
            t = (m - m0) / (m1 - m0) if m1 != m0 else 0.0
            return table[i] + t * (table[i + 1] - table[i])
    return table[-1]


@dataclass
class TwoWaySlabInput:
    fc_ksc: float
    short_steel_type: str
    long_steel_type: str
    short_bar_dia_mm: float
    short_bar_spacing_cm: float
    long_bar_dia_mm: float
    long_bar_spacing_cm: float
    wD_kg_m2: float
    wL_kg_m2: float
    S_m: float
    L_m: float
    t_cm: float
    case_key: str = "CASE2"   # key of TWO_WAY_CASES


@dataclass
class DirectionPositionResult:
    label_th: str
    active: bool
    coeff: float
    mu_kgm: float
    d_cm: float
    ru_ksc: float
    rreq: float
    rho_used: float
    over_reinforced: bool
    as_req_cm2_m: float


@dataclass
class TwoWaySlabResult:
    m_ratio: float
    two_way_ok: bool          # m > 0.5 (ถ้า <=0.5 ควรออกแบบเป็นพื้นทางเดียวแทน)
    dead_load_kg_m2: float
    wu_kg_m2: float
    beta1: float
    rho_b: float
    rho_min: float
    rho_max: float
    tmin_cm: float
    t_ok: bool
    short_positions: list      # list[DirectionPositionResult], len 3
    long_positions: list
    short_d_cm: float
    long_d_cm: float
    as_req_short_cm2_m: float
    as_req_long_cm2_m: float
    as_provided_short_cm2_m: float
    as_provided_long_cm2_m: float
    short_spacing_max_cm: float
    long_spacing_max_cm: float
    short_reinf_ok: bool
    long_reinf_ok: bool
    ast_min_cm2_m: float
    vu_kg: float
    phi_vc_kg: float
    shear_ok: bool
    shear_ok_secondary: bool           # (2/3)*phiVc >= Vu — ที่มายังไม่ยืนยัน ดู docstring
    dl_on_beam_triangular_kg_m: float
    dl_on_beam_trapezoidal_kg_m: float
    ll_on_beam_triangular_kg_m: float
    ll_on_beam_trapezoidal_kg_m: float
    reinf_label_short: str
    reinf_label_long: str
    short_bar_type: str
    long_bar_type: str
    case_confirmed: bool


def provided_as_cm2_per_m(dia_mm: float, spacing_cm: float) -> float:
    return round(((100.0 / spacing_cm) + 1.0) * bar_area_cm2(dia_mm), 2)


def _solve_direction(coeffs_at_m: dict, wu: float, S_m: float, d_cm: float,
                      fc_ksc: float, fy: float, rho_min: float, rho_max: float) -> list:
    """คำนวณ 3 ตำแหน่ง (Con-/Mid+/Disc-) ของทิศทางหนึ่ง — Mu = C * Wu * S^2 เสมอ
    (ทั้งสองทิศทางใช้ S ด้านสั้นยกกำลังสอง ตามที่ยืนยันจากไฟล์ตัวอย่าง)."""
    positions = []
    for label, coeff in zip(POSITION_LABELS_TH, coeffs_at_m):
        if coeff is None or coeff <= 0:
            positions.append(DirectionPositionResult(
                label_th=label, active=False, coeff=0.0, mu_kgm=0.0, d_cm=d_cm,
                ru_ksc=0.0, rreq=0.0, rho_used=0.0, over_reinforced=False,
                as_req_cm2_m=0.0,
            ))
            continue

        mu_kgm = coeff * wu * S_m ** 2
        ru = mu_kgm * 100.0 / (PHI_B * 100.0 * d_cm ** 2)
        under_sqrt = 1.0 - (2.0 * ru) / (0.85 * fc_ksc)
        over_reinforced = under_sqrt < 0
        if over_reinforced:
            rreq = rho_max
        else:
            rreq = 0.85 * (fc_ksc / fy) * (1.0 - math.sqrt(under_sqrt))

        rho_used = max(rreq, rho_min)
        over_reinforced = over_reinforced or (rho_used > rho_max)
        as_req = rho_used * 100.0 * d_cm

        positions.append(DirectionPositionResult(
            label_th=label, active=True, coeff=coeff, mu_kgm=mu_kgm, d_cm=d_cm,
            ru_ksc=ru, rreq=rreq, rho_used=rho_used, over_reinforced=over_reinforced,
            as_req_cm2_m=as_req,
        ))
    return positions


def calculate(inp: TwoWaySlabInput) -> TwoWaySlabResult:
    fy_short = GS_STEEL_FY_KSC[inp.short_steel_type]
    fy_long = GS_STEEL_FY_KSC[inp.long_steel_type]
    t_m = inp.t_cm / 100.0
    case = TWO_WAY_CASES[inp.case_key]

    m_ratio = inp.S_m / inp.L_m if inp.L_m else None
    two_way_ok = (m_ratio is not None) and (m_ratio > 0.5)

    # --- loads (กฎกระทรวง 2566) ---
    dead_load = CONCRETE_UNIT_WEIGHT_KG_M3 * t_m
    wu = 1.4 * (dead_load + inp.wD_kg_m2) + 1.7 * inp.wL_kg_m2

    # --- material parameters (ใช้ fy ของเหล็กแนวสั้นเป็นหลักในการหา rho_b/rho_max
    #     เหมือน Module 1.2 — เหล็กสองทิศทางมักเป็นชั้นคุณภาพเดียวกันในทางปฏิบัติ) ---
    beta1 = compute_beta1(inp.fc_ksc)
    rho_b = compute_rho_b(inp.fc_ksc, fy_short, beta1)
    rho_min = compute_rho_min(fy_short)
    rho_max = compute_rho_max(rho_b)

    # --- minimum thickness (deflection control) ---
    tmin_cm = (2.0 * inp.S_m * 100.0 + 2.0 * inp.L_m * 100.0) / 180.0
    t_ok = inp.t_cm >= tmin_cm

    # --- effective depth: ตะแกรง 2 ชั้น เหล็กแนวยาวอยู่ใต้/บนเหล็กแนวสั้น ---
    short_d_cm = inp.t_cm - COVER_CM - inp.short_bar_dia_mm / 10.0 / 2.0
    long_d_cm = inp.t_cm - COVER_CM - inp.short_bar_dia_mm / 10.0 - inp.long_bar_dia_mm / 10.0 / 2.0

    m_for_lookup = m_ratio if m_ratio else 1.0
    short_coeffs = [
        _interp(m_for_lookup, case["short"]["con"]) if case["short"].get("con") else 0.0,
        _interp(m_for_lookup, case["short"]["mid"]),
        _interp(m_for_lookup, case["short"]["disc"]) if case["short"].get("has_disc") else None,
    ]
    long_coeffs = [
        _interp(m_for_lookup, case["long"]["con"]) if case["long"].get("con") else 0.0,
        _interp(m_for_lookup, case["long"]["mid"]),
        _interp(m_for_lookup, case["long"]["disc"]) if case["long"].get("has_disc") else None,
    ]
    if not case["short"].get("has_disc") and not case["short"].get("fully_disc"):
        pass  # con- ใช้ค่าเดียวกันทั้งสองขอบ (ไม่มี disc-)
    if case["short"].get("fully_disc"):
        short_coeffs[0] = None  # ไม่มีขอบต่อเนื่อง -> ไม่คำนวณ Con.-
    if case["long"].get("fully_disc"):
        long_coeffs[0] = None

    short_positions = _solve_direction(short_coeffs, wu, inp.S_m, short_d_cm,
                                        inp.fc_ksc, fy_short, rho_min, rho_max)
    long_positions = _solve_direction(long_coeffs, wu, inp.S_m, long_d_cm,
                                       inp.fc_ksc, fy_long, rho_min, rho_max)

    as_req_short = max((p.as_req_cm2_m for p in short_positions), default=0.0)
    as_req_long = max((p.as_req_cm2_m for p in long_positions), default=0.0)

    # --- Ast ขั้นต่ำ (flat 0.002, ไม่ขึ้น fy — ยืนยันจากไฟล์) ---
    ast_min = AST_MIN_RATIO * 100.0 * inp.t_cm
    as_req_short = max(as_req_short, ast_min)
    as_req_long = max(as_req_long, ast_min)

    as_provided_short = provided_as_cm2_per_m(inp.short_bar_dia_mm, inp.short_bar_spacing_cm)
    as_provided_long = provided_as_cm2_per_m(inp.long_bar_dia_mm, inp.long_bar_spacing_cm)

    short_area = bar_area_cm2(inp.short_bar_dia_mm)
    long_area = bar_area_cm2(inp.long_bar_dia_mm)
    short_spacing_max = min(short_area / as_req_short * 100.0 if as_req_short > 0 else 999.0,
                             3.0 * inp.t_cm, 45.0)
    long_spacing_max = min(long_area / as_req_long * 100.0 if as_req_long > 0 else 999.0,
                            3.0 * inp.t_cm, 45.0)
    short_reinf_ok = (as_provided_short >= as_req_short) and (inp.short_bar_spacing_cm <= short_spacing_max)
    long_reinf_ok = (as_provided_long >= as_req_long) and (inp.long_bar_spacing_cm <= long_spacing_max)

    # --- shear ---
    vu = 1.15 * wu * inp.S_m / 4.0
    phi_vc = PHI_V * 0.53 * math.sqrt(inp.fc_ksc) * 100.0 * short_d_cm
    shear_ok = phi_vc >= vu
    shear_ok_secondary = (2.0 / 3.0) * phi_vc >= vu

    # --- load transfer to beam (service, unfactored) ---
    m_round = round(m_for_lookup, 2)
    w_service = dead_load + inp.wD_kg_m2
    dl_tri = w_service * inp.S_m / 3.0
    dl_trap = w_service * (inp.S_m / 2.0) * (1.0 - m_round ** 2 / 3.0)
    ll_tri = inp.wL_kg_m2 * inp.S_m / 3.0
    ll_trap = inp.wL_kg_m2 * (inp.S_m / 2.0) * (1.0 - m_round ** 2 / 3.0)

    short_bar_type = GS_STEEL_BAR_TYPE[inp.short_steel_type]
    long_bar_type = GS_STEEL_BAR_TYPE[inp.long_steel_type]
    reinf_label_short = f"{short_bar_type}{inp.short_bar_dia_mm:.0f}@{inp.short_bar_spacing_cm:.0f}cm."
    reinf_label_long = f"{long_bar_type}{inp.long_bar_dia_mm:.0f}@{inp.long_bar_spacing_cm:.0f}cm."

    return TwoWaySlabResult(
        m_ratio=m_ratio, two_way_ok=two_way_ok,
        dead_load_kg_m2=dead_load, wu_kg_m2=wu,
        beta1=beta1, rho_b=rho_b, rho_min=rho_min, rho_max=rho_max,
        tmin_cm=tmin_cm, t_ok=t_ok,
        short_positions=short_positions, long_positions=long_positions,
        short_d_cm=short_d_cm, long_d_cm=long_d_cm,
        as_req_short_cm2_m=as_req_short, as_req_long_cm2_m=as_req_long,
        as_provided_short_cm2_m=as_provided_short, as_provided_long_cm2_m=as_provided_long,
        short_spacing_max_cm=short_spacing_max, long_spacing_max_cm=long_spacing_max,
        short_reinf_ok=short_reinf_ok, long_reinf_ok=long_reinf_ok,
        ast_min_cm2_m=ast_min,
        vu_kg=vu, phi_vc_kg=phi_vc, shear_ok=shear_ok, shear_ok_secondary=shear_ok_secondary,
        dl_on_beam_triangular_kg_m=dl_tri, dl_on_beam_trapezoidal_kg_m=dl_trap,
        ll_on_beam_triangular_kg_m=ll_tri, ll_on_beam_trapezoidal_kg_m=ll_trap,
        reinf_label_short=reinf_label_short, reinf_label_long=reinf_label_long,
        short_bar_type=short_bar_type, long_bar_type=long_bar_type,
        case_confirmed=case["confirmed"],
    )
