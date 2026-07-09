"""
Shared "Design Parameters" (พารามิเตอร์การออกแบบ) module.

Computes the general Strength Design Method (SDM) constants that will be
used across MULTIPLE future modules (Beam, Column, One-way/Two-way Slab,
etc.) — beta1, rho_min, rho_max, phi factors, load-combination formulas.

NOT used by the Slab-on-Ground module itself, which has its own governing
checks (Temperature Steel / Subgrade Drag / PCA) that don't involve these
flexural-design parameters. This module exists so every future module
that DOES need them can share one consistent source of truth, driven by
a single f'c / steel-type choice set on the "พารามิเตอร์การออกแบบ" page.

Formulas verified against a DRMK RC SDM reference screenshot:
  f'c=240, SR24 (fy=2400) -> Ec=233928, beta1=0.85,
  rho_min=0.0058, rho_max=0.0389 (all matched exactly).
"""

import math
from dataclasses import dataclass

STEEL_FY_KSC = {
    "SR24": 2400,
    "SD30": 3000,
    "SD40": 4000,
    "SD50": 5000,
}

ES_KSC = 2_040_000.0   # steel modulus of elasticity (standard constant)
PHI_B = 0.90            # flexure strength reduction factor
PHI_V = 0.85            # shear strength reduction factor
PHI_C = 0.70            # ตัวคูณลดกำลังอัด (compression strength reduction factor)
                         # ตามคำสั่งผู้ใช้ — ใช้กับโมดูลเสา (Column) ในอนาคต

# ---------------------------------------------------------------------------
# รายการน้ำหนักบรรทุก (Load Schedule) — กฎกระทรวง กำหนดการรับน้ำหนัก ความต้านทาน
# ความคงทนของอาคาร และพื้นดินที่รองรับอาคารในการต้านทานแรงสั่นสะเทือนของแผ่นดินไหว
# พ.ศ. 2566, ข้อ 11 (บรรทัดจร LL) — เฉพาะประเภทที่เกี่ยวข้องกับอาคารบ้านพักอาศัย
# (ขอบเขตงานวิจัยนี้) แหล่งอ้างอิง: download.asa.or.th/03media/04law/cba/mr/mr66-70h.pdf
# หมายเหตุ: น้ำหนักบรรทุกคงที่ (DL) ของแผ่นพื้น/คาน/เสา ผู้ใช้กำหนดเองตามน้ำหนักวัสดุจริง
# ในแต่ละโมดูล ตารางนี้แสดงเฉพาะค่า LL มาตรฐานตามกฎกระทรวงฯ เพื่อใช้อ้างอิงเท่านั้น
# ---------------------------------------------------------------------------
LOAD_SCHEDULE = [
    {"usage": "ห้องนอน ห้องนั่งเล่น ห้องน้ำ ห้องแต่งตัว ห้องต่างๆ ในบ้านพักอาศัย", "ll_kg_m2": 200},
    {"usage": "ระเบียง และบันได", "ll_kg_m2": 200},
    {"usage": "ดาดฟ้า", "ll_kg_m2": 200},
    {"usage": "หลังคา (ไม่มีคนขึ้นไปใช้สอย)", "ll_kg_m2": 50},
    {"usage": "กันสาดคอนกรีต", "ll_kg_m2": 100},
    {"usage": "ที่จอดรถยนต์ (ไม่เกิน 7 ที่นั่ง) หรือรถจักรยานยนต์", "ll_kg_m2": 300},
    {"usage": "พื้นที่เก็บของ", "ll_kg_m2": 500},
]
LOAD_FACTOR_NOTE = "นป. = 1.4นค. + 1.7นจ.  (U = 1.4D + 1.7L)"
LOAD_SCHEDULE_SOURCE = ("กฎกระทรวง กำหนดการรับน้ำหนัก ความต้านทาน ความคงทนของอาคาร และพื้นดินที่รองรับ"
                         "อาคารในการต้านทานแรงสั่นสะเทือนของแผ่นดินไหว พ.ศ. 2566 ข้อ 11 และข้อ 7 "
                         "(เฉพาะประเภทที่เกี่ยวข้องกับอาคารบ้านพักอาศัย)")


def compute_ec(fc_ksc: float) -> float:
    """Concrete modulus of elasticity: Ec = 15100 * sqrt(f'c) (ksc)."""
    return 15100.0 * math.sqrt(fc_ksc)


def compute_beta1(fc_ksc: float) -> float:
    """Whitney stress-block factor beta1 (ACI 318-style, matches reference)."""
    if fc_ksc <= 280.0:
        return 0.85
    beta1 = 0.85 - 0.05 * (fc_ksc - 280.0) / 70.0
    return max(beta1, 0.65)


def compute_rho_b(fc_ksc: float, fy_ksc: float, beta1: float) -> float:
    """Balanced steel ratio (Es*ecu = 2,040,000*0.003 = 6120 ksc)."""
    return 0.85 * beta1 * (fc_ksc / fy_ksc) * (6120.0 / (6120.0 + fy_ksc))


def compute_rho_min(fy_ksc: float) -> float:
    return 14.0 / fy_ksc


def compute_rho_max(rho_b: float) -> float:
    return 0.75 * rho_b


@dataclass
class DesignParameters:
    fc_ksc: float
    steel_type: str
    fy_ksc: float
    ec_ksc: float
    es_ksc: float
    beta1: float
    rho_b: float
    rho_min: float
    rho_max: float
    phi_b: float
    phi_v: float
    phi_c: float


def calculate(fc_ksc: float, steel_type: str) -> DesignParameters:
    fy_ksc = STEEL_FY_KSC[steel_type]
    ec = compute_ec(fc_ksc)
    beta1 = compute_beta1(fc_ksc)
    rho_b = compute_rho_b(fc_ksc, fy_ksc, beta1)
    rho_min = compute_rho_min(fy_ksc)
    rho_max = compute_rho_max(rho_b)
    return DesignParameters(
        fc_ksc=fc_ksc, steel_type=steel_type, fy_ksc=fy_ksc,
        ec_ksc=ec, es_ksc=ES_KSC, beta1=beta1, rho_b=rho_b,
        rho_min=rho_min, rho_max=rho_max, phi_b=PHI_B, phi_v=PHI_V, phi_c=PHI_C,
    )
