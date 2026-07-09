"""
Table 6.5 (ALL_SDM_BasicBOOK_DRMK.pdf, p.148) — Dowel bar size and length
for slab-on-ground joints, by slab thickness category.

ตารางที่ 6.5 ขนาดและความยาวเหล็กถ่ายน้ำหนัก สำหรับระยะห่าง 30 ซม.

Each entry: thickness range (cm, inclusive lower, inclusive upper or None
for "greater than") -> dict with expansion-joint and contraction-joint
dowel {diameter_mm, length_cm}.

NOTE: the table in the book is tabulated for dowel spacing = 30 cm.
The reference spacing is stored here (DOWEL_TABLE_SPACING_CM) so the app
can flag when the user's chosen spacing differs from what the table
assumes.
"""

DOWEL_TABLE_SPACING_CM = 30.0

DOWEL_TABLE = [
    {
        "t_min_cm": 15.0, "t_max_cm": 18.0,
        "expansion": {"diameter_mm": 20, "length_cm": 55},
        "contraction": {"diameter_mm": 12, "length_cm": 40},
    },
    {
        "t_min_cm": 19.0, "t_max_cm": 23.0,
        "expansion": {"diameter_mm": 25, "length_cm": 65},
        "contraction": {"diameter_mm": 20, "length_cm": 50},
    },
    {
        "t_min_cm": 24.0, "t_max_cm": None,  # > 24 cm
        "expansion": {"diameter_mm": 30, "length_cm": 75},
        "contraction": {"diameter_mm": 25, "length_cm": 60},
    },
]


def lookup_dowel(t_cm: float, joint_type: str = "expansion"):
    """
    Return the recommended dowel {diameter_mm, length_cm} for a given
    slab thickness (cm) and joint_type ("expansion" or "contraction").
    Returns None if t_cm is below the table's minimum (15 cm) — the book
    does not provide guidance for thinner ground slabs.
    """
    for row in DOWEL_TABLE:
        t_min = row["t_min_cm"]
        t_max = row["t_max_cm"]
        if t_cm >= t_min and (t_max is None or t_cm <= t_max):
            return row[joint_type]
    return None
