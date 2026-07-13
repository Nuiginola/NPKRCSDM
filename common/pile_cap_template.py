"""
common/pile_cap_template.py
===========================
Template-swap renderer for the RC Pile Cap SECTION.

Method (per the project's strict rules):
  * Use the supplied template PNG EXACTLY (1/2/3/4 pile).
  * NEVER redraw any engineering graphic, reinforcement, dimension line or leader.
  * Replace TEXT ONLY — erase just the old glyph pixels (no white box over graphics),
    then draw the new value centred on the SAME anchor, in a matching Arial/SHX-style
    font, shrinking slightly if the new text is wider than the old one.
  * Everything else stays pixel-identical; export at the template's own resolution.

Only the numeric values the calculation actually produces are swapped: the two
reinforcement call-outs, the pile description, the safe-load, the concrete cover and
the pile-cap thickness.  Pure drawing-geometry dims (overall height, the nested
detailing dim) are left as the template draws them.
"""

import os
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
_CODE_ROOT = os.path.dirname(_HERE)


# ---- fonts (Arial-metric-compatible; closest to the template's SHX/Arial) --------
def _font_paths():
    cands = [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:\\Windows\\Fonts\\arialbd.ttf", "C:\\Windows\\Fonts\\arial.ttf",
        "arialbd.ttf", "arial.ttf",
    ]
    bold = next((c for c in cands if "Bold" in c or "bd" in c), None)
    reg = next((c for c in cands if c not in (bold,)), None)
    # resolve to first existing of each kind
    def first(kinds):
        for c in cands:
            if any(k in c for k in kinds) and (os.path.exists(c) or not c.startswith("/")):
                if os.path.exists(c):
                    return c
        return None
    b = first(["Bold", "arialbd"]) or first(["Sans"])
    r = first(["Regular", "arial.ttf"]) or b
    return b, r


_FB, _FR = _font_paths()


def _font(bold, size):
    path = _FB if bold else _FR
    try:
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()


# ---- low-level text replacement -------------------------------------------------
def _erase_glyphs(img, bbox, pad=1):
    """Clear only non-white (glyph) pixels inside a tight padded bbox — never paints a
    visible white rectangle over graphics (background here is white)."""
    x, y, w, h = bbox
    px = img.load()
    x0, y0 = max(0, x - pad), max(0, y - pad)
    x1, y1 = min(img.width, x + w + pad), min(img.height, y + h + pad)
    rgba = img.mode == "RGBA"
    for j in range(y0, y1):
        for i in range(x0, x1):
            p = px[i, j]
            if not (p[0] > 234 and p[1] > 234 and p[2] > 234):
                px[i, j] = (255, 255, 255, p[3]) if rgba else (255, 255, 255)


def _fit_font(text, bold, size, max_w):
    """Shrink the font until the text is no wider than max_w (rule: reduce if longer)."""
    s = size
    while s > 6:
        f = _font(bold, s)
        b = f.getbbox(text)
        if (b[2] - b[0]) <= max_w:
            return f
        s -= 1
    return _font(bold, 6)


def _write(img, anchor, text, color, bold, size, rotate=0, max_w=None, align="center"):
    """Draw text centred on `anchor` (glyph-box centre), transparent background."""
    f = _fit_font(text, bold, size, max_w) if max_w else _font(bold, size)
    b = f.getbbox(text)
    tw, th = b[2] - b[0], b[3] - b[1]
    # render onto its own transparent tile
    tile = Image.new("RGBA", (max(1, tw + 4), max(1, th + 4)), (0, 0, 0, 0))
    ImageDraw.Draw(tile).text((2 - b[0], 2 - b[1]), text, fill=color + (255,), font=f)
    if rotate:
        tile = tile.rotate(rotate, expand=True)
    ax, ay = anchor
    if align == "left":
        ox = ax
    elif align == "right":
        ox = ax - tile.width
    else:
        ox = ax - tile.width // 2
    oy = ay - tile.height // 2
    img.alpha_composite(tile, (int(round(ox)), int(round(oy))))


# ======================================================================
# PER-TEMPLATE FIELD CONFIG
#   Each field: (erase_bbox, anchor_center, color, bold, size, rotate, key)
#   anchor_center is the CENTRE of the original glyph box (keeps new text centred).
#   key -> value produced by _values() below.
# ======================================================================
_BLUE = (0, 0, 205)
_BLACK = (0, 0, 0)

# template file names sit in the code root ("1 pile.png" ... "4 pile.png")
_TEMPLATE_FILE = {1: "1 pile.png", 2: "2 pile.png", 3: "3 pile.png", 4: "4 pile.png"}

# fields calibrated from the supplied templates (image pixel coords)
_FIELDS = {
    1: [
        ((283, 121, 30, 9), (298, 125), _BLACK, True, 10, 0, "top_bar"),
        ((283, 136, 30, 9), (298, 140), _BLACK, True, 10, 0, "bot_bar"),
        ((228, 227, 46, 10), (251, 232), _BLACK, False, 10, 0, "pile_desc"),
        ((228, 240, 74, 11), (265, 246), _BLACK, False, 10, 0, "safe_load"),
        ((66, 34, 30, 9), (81, 38), _BLUE, False, 9, 0, "cover"),
    ],
    2: [
        ((483, 145, 32, 10), (499, 150), _BLACK, True, 10, 0, "top_bar"),
        ((483, 168, 32, 10), (499, 173), _BLACK, True, 10, 0, "bot_bar"),
        ((454, 295, 54, 12), (481, 301), _BLACK, False, 11, 0, "pile_desc"),
        ((454, 313, 82, 13), (496, 320), _BLACK, False, 11, 0, "safe_load"),
        ((100, 85, 30, 9), (115, 89), _BLUE, False, 9, 0, "cover"),
    ],
    3: [
        ((499, 205, 32, 10), (515, 210), _BLACK, True, 10, 0, "top_bar"),
        ((499, 220, 38, 10), (517, 225), _BLACK, True, 10, 0, "bot_bar"),
        ((482, 320, 54, 12), (509, 326), _BLACK, False, 11, 0, "pile_desc"),
        ((472, 335, 90, 13), (517, 342), _BLACK, False, 11, 0, "safe_load"),
        ((108, 111, 30, 9), (123, 115), _BLUE, False, 9, 0, "cover"),
    ],
    4: [
        ((450, 137, 32, 10), (466, 142), _BLACK, True, 10, 0, "top_bar"),
        ((450, 159, 32, 10), (466, 164), _BLACK, True, 10, 0, "bot_bar"),
        ((429, 272, 54, 12), (456, 278), _BLACK, False, 11, 0, "pile_desc"),
        ((419, 286, 82, 13), (461, 293), _BLACK, False, 11, 0, "safe_load"),
        ((106, 70, 30, 9), (121, 74), _BLUE, False, 9, 0, "cover"),
    ],
}


def _pile_type_code(pile_shape_label):
    """Short pile-type prefix used in the template (e.g. 'I' for I-section)."""
    if not pile_shape_label:
        return "I"
    s = str(pile_shape_label)
    for c in ("I", "ไอ"):
        if c in s:
            return "I"
    if any(k in s for k in ("กลม", "round", "Round", "O")):
        return "O"
    if any(k in s for k in ("เหลี่ยม", "square", "Square", "S")):
        return "S"
    if any(k in s for k in ("หก", "hex", "Hex")):
        return "H"
    return "I"


def _values(inp, result, pile_shape_label=None):
    """Compute the replacement strings from the calculation result."""
    dia = inp.main_bar_dia_mm
    bt = result.main_bar_type          # "DB" / "RB"
    n1, n2 = result.flex_1.n_bars_use, result.flex_2.n_bars_use
    bottom_n, top_n = (n2, n1) if n2 >= n1 else (n1, n2)
    code = _pile_type_code(pile_shape_label)
    return {
        "top_bar": f"{top_n}{bt}{dia:.0f}",
        "bot_bar": f"{bottom_n}{bt}{dia:.0f}",
        "pile_desc": f"{inp.n_piles} Pile {code}-{inp.pile_size_cm:.0f}",
        "safe_load": f"S.L >= {inp.pile_safe_load_ton:g} t/pile",
        "cover": f"{inp.cover_cm/100.0:.3f}",
        "thickness": f"{result.t_cm/100.0:.2f}".rstrip("0").rstrip(".")
                     if result.t_cm % 10 else f"{result.t_cm/100.0:.1f}",
    }


def render_section_png(inp, result, pile_shape_label=None):
    """Return PNG bytes: the supplied template for `inp.n_piles`, with only the numeric
    text replaced by the calculated values.  Returns None if the template is missing."""
    n = int(inp.n_piles)
    fname = _TEMPLATE_FILE.get(n)
    if not fname:
        return None
    path = os.path.join(_CODE_ROOT, fname)
    if not os.path.exists(path):
        return None
    img = Image.open(path).convert("RGBA")
    vals = _values(inp, result, pile_shape_label)
    for bbox, anchor, color, bold, size, rot, key in _FIELDS.get(n, []):
        if key not in vals:
            continue
        _erase_glyphs(img, bbox)
        max_w = None if rot else int(bbox[2] * 1.25)
        _write(img, anchor, vals[key], color, bold, size, rotate=rot, max_w=max_w)
    import io
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
