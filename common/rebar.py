"""
Thai standard reinforcing bar (rebar) database and utility functions.

Sources:
- RB = Round Bar (SR24 mild steel, fy = 2400 ksc typical)
- DB = Deformed Bar (SD40 fy = 4000 ksc, SD50 fy = 5000 ksc typical)
Nominal diameters and cross-sectional areas per TIS (มอก.) standard sizes,
as commonly published in Thai RC design references (matches
ALL_SDM_BasicBOOK_DRMK.pdf and standard Thai rebar tables).
"""

import math

# Nominal bar diameter (mm) -> cross-sectional area (cm^2)
REBAR_AREA_CM2 = {
    "RB6": 0.283,
    "RB9": 0.636,
    "DB10": 0.785,
    "DB12": 1.131,
    "DB16": 2.011,
    "DB20": 3.146,
    "DB25": 4.909,
    "DB28": 6.158,
    "DB32": 8.042,
    "DB36": 10.179,
}

# Steel grade -> yield strength fy (ksc = kg/cm^2)
STEEL_GRADE_FY = {
    "SR24": 2400,
    "SD40": 4000,
    "SD50": 5000,
}

# Which bar series are typically available in each grade (for UI dropdown filtering)
ROUND_BARS = ["RB6", "RB9"]
DEFORMED_BARS = ["DB10", "DB12", "DB16", "DB20", "DB25", "DB28", "DB32", "DB36"]


def bar_area_cm2(bar_size: str) -> float:
    """Cross-sectional area of a single bar, cm^2."""
    return REBAR_AREA_CM2[bar_size]


def as_per_meter(bar_size: str, spacing_cm: float) -> float:
    """
    Steel area per metre width of slab, cm^2/m, for a given bar size
    and centre-to-centre spacing (cm).
    """
    if spacing_cm <= 0:
        raise ValueError("spacing_cm must be positive")
    return bar_area_cm2(bar_size) * (100.0 / spacing_cm)


def spacing_for_required_as(bar_size: str, as_required_cm2_per_m: float,
                             round_down_to_cm: float = 1.0) -> float:
    """
    Given a required steel area (cm^2/m), find the maximum practical
    centre-to-centre spacing (cm) for the chosen bar size that still
    provides at least the required area. Result is rounded DOWN to the
    nearest `round_down_to_cm` (default 1 cm) so the provided area is
    conservative (>= required).
    """
    if as_required_cm2_per_m <= 0:
        raise ValueError("as_required_cm2_per_m must be positive")
    raw_spacing = bar_area_cm2(bar_size) * 100.0 / as_required_cm2_per_m
    spacing = math.floor(raw_spacing / round_down_to_cm) * round_down_to_cm
    return max(spacing, round_down_to_cm)
