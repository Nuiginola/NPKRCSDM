"""
common/footing_section_template.py
==================================
Template-swap renderer for the RC **Spread Footing SECTION** (module 5.1).

Same method as the pile-cap version: use the supplied template PNG ("Footing F1.png")
EXACTLY and replace TEXT ONLY — never redraw any graphic, reinforcement, dimension
line or leader.  Only the values the calculation actually produces are swapped: the two
reinforcement call-outs (X- and Y-direction) and the concrete cover.  Pure drawing
dimensions (overall height, footing thickness rotated dim, lean/sand constants) are left
exactly as the template draws them.
"""

import io
import os

from PIL import Image

# reuse the low-level text-replacement primitives from the pile-cap template module
from common.pile_cap_template import _erase_glyphs, _write, _CODE_ROOT

_BLUE = (0, 0, 205)
_BLACK = (0, 0, 0)

_TEMPLATE_FILE = "Footing F1.png"

# ระยะฝังฐานรากรวม (ground -> ใต้ฐานราก) ค่าเริ่มต้นตามข้อกำหนด = 1.50 ม.
# ความสูงช่วงบน (พื้นดิน -> หลังฐานราก) = TOTAL_DEPTH - ความหนาฐาน
TOTAL_DEPTH_M = 1.50

# fields calibrated from the supplied template (image pixel coords, 490x350)
#   (erase_bbox, anchor_center, color, bold, size, rotate, key)
_FIELDS = [
    ((393, 140, 40, 16), (411, 147), _BLACK, True, 10, 0, "bar_x"),      # top call-out  (X dir)
    ((393, 166, 40, 14), (411, 173), _BLACK, True, 10, 0, "bar_y"),      # bottom call-out (Y dir)
    ((137, 178, 32, 10), (153, 182), _BLUE, False, 9, 0, "cover"),       # cover (left)
    ((407, 217, 32, 10), (423, 221), _BLUE, False, 9, 0, "cover"),       # cover (right)
    ((47, 104, 14, 40), (54, 123), _BLUE, False, 9, 90, "height"),       # top height (rotated)
    ((47, 221, 14, 38), (54, 240), _BLUE, False, 9, 90, "thickness"),    # footing thickness (rotated)
]


def _values(inp, result):
    dia = inp.main_bar_dia_mm
    bt = result.main_bar_type              # "DB" / "RB"
    t_m = result.t_cm / 100.0
    total_depth = float(getattr(inp, "founding_depth_m", TOTAL_DEPTH_M) or TOTAL_DEPTH_M)
    return {
        "bar_x": f"{result.flex_x.n_bars_use}{bt}{dia:.0f}",
        "bar_y": f"{result.flex_y.n_bars_use}{bt}{dia:.0f}",
        "cover": f"{inp.cover_cm/100.0:.3f}",
        "thickness": f"{t_m:.2f}",
        "height": f"{max(0.0, total_depth - t_m):.2f}",
    }


def render_section_png(inp, result):
    """Return PNG bytes: the 'Footing F1' template with only the numeric text replaced by
    the calculated values.  Returns None if the template file is missing."""
    path = os.path.join(_CODE_ROOT, _TEMPLATE_FILE)
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA")
    vals = _values(inp, result)
    for bbox, anchor, color, bold, size, rot, key in _FIELDS:
        if key not in vals:
            continue
        _erase_glyphs(img, bbox)
        max_w = None if rot else int(bbox[2] * 1.25)
        _write(img, anchor, vals[key], color, bold, size, rotate=rot, max_w=max_w)
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
