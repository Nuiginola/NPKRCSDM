"""
common/stair_section_template.py
================================
Template-swap renderer for module 2.1 (บันไดช่วงตรง / Straight-Run Stair).

Same method as the footing/pile-cap versions: use the supplied template PNG
("stair_rebar_template1.png") EXACTLY and add TEXT ONLY — never redraw any graphic,
reinforcement or leader.  The template already carries the flight geometry and the
reinforcement with pre-drawn (blank) green leader lines; this module writes the
calculated main-reinforcement call-out on each leader shelf.  No dimensions / detail
blow-ups are drawn (those were removed per the user's request).
"""

import io
import os

from PIL import Image, ImageDraw, ImageFont

from common.pile_cap_template import _CODE_ROOT

_TEMPLATE_FILE = "stair_rebar_template1.png"

# the 6 pre-drawn leaders — the template already marks the distribution ones with a GREEN
# CIRCLE at the tip (drawn by the user), so this module only writes the call-out text.
# each entry: (text_x, text_y, side, kind)
#   text_(x,y) = outer shelf endpoint (where the call-out text sits)
#   side       = 'TOP' (shelf above the flight) / 'BOT' (below)
#   kind       = 'temp' (distribution / green-circle) or 'main'
#   mapping per the user's template (2026-07-12): 1,3,4 = distribution ; 2,5,6 = main
_LEADERS = [
    (140, 325, "TOP", "temp"),   # 1
    (216, 265, "TOP", "main"),   # 2
    (372, 168, "TOP", "temp"),   # 3
    (499, 88, "TOP", "temp"),    # 4
    (596, 30, "TOP", "main"),    # 5
    (631, 142, "BOT", "main"),   # 6
]

_FONT_BOLD = "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"
_FONT_BOLD_WIN = "C:\\Windows\\Fonts\\arialbd.ttf"

# the two centre arrows point at the waist thickness t — text landing (left-aligned)
_THICKNESS_ANCHOR = (358, 294)

# --- พิกัดอ้างอิงบนภาพ template (802×511) สำหรับวาดเส้นบอกระยะ (2026-07-13) ---
# ช่วงแนวนอนของบันได (สำหรับระยะ L) / ช่วงแนวตั้ง (สำหรับระยะ H) / จุดโคน-ปลายแนวลาด (สำหรับ L/4)
_STAIR_X_LEFT = 84      # ขอบซ้ายสุดของบันได (โคนล่าง)
_STAIR_X_RIGHT = 725    # ขอบขวาสุด (ปลายบน)
_STAIR_Y_TOP = 8        # บนสุดของบันได
_STAIR_Y_BOT = 449      # ล่างสุด
_INCLINE_BOT = (129, 405)   # โคนแนวลาด (มุมบนคานซ้าย)
_INCLINE_TOP = (681, 74)    # ปลายแนวลาด (มุมล่างคานขวา)
_PAD_RIGHT = 96
_PAD_BOTTOM = 58


def _font(size):
    for p in (_FONT_BOLD, _FONT_BOLD_WIN, "arialbd.ttf"):
        try:
            if os.path.exists(p) or not p.startswith("/"):
                return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _arrow(draw, p, ang, size=7, fill=(0, 0, 0, 255)):
    """วาดหัวลูกศรที่จุด p ชี้ไปตามมุม ang (เรเดียน)"""
    import math
    for da in (math.radians(150), math.radians(-150)):
        x2 = p[0] + size * math.cos(ang + da)
        y2 = p[1] + size * math.sin(ang + da)
        draw.line([p, (x2, y2)], fill=fill, width=2)


def _dim_line(draw, p1, p2, font, text, text_pos, fill=(0, 0, 0, 255)):
    """เส้นบอกระยะ: เส้นตรง p1→p2 พร้อมหัวลูกศรทั้งสองปลาย + ข้อความที่ text_pos"""
    import math
    draw.line([p1, p2], fill=fill, width=2)
    ang = math.atan2(p2[1] - p1[1], p2[0] - p1[0])
    _arrow(draw, p1, ang + math.pi, fill=fill)   # ปลาย p1 ชี้ออก
    _arrow(draw, p2, ang, fill=fill)             # ปลาย p2 ชี้ออก
    draw.text(text_pos, text, fill=fill, font=font)


def render_section_png(inp, result, font_size=12):
    """Return PNG bytes: the stair reinforcement template with the calculated main-bar
    call-out written on every leader shelf.  Returns None if the template is missing."""
    path = os.path.join(_CODE_ROOT, _TEMPLATE_FILE)
    if not os.path.exists(path):
        return None
    import math
    base = Image.open(path).convert("RGBA")
    # ขยาย canvas เพิ่มขอบขวา+ล่าง เพื่อมีที่วางเส้นบอกระยะ L (ล่าง) และ H (ขวา) โดยไม่ทับแบบเดิม
    img = Image.new("RGBA", (base.width + _PAD_RIGHT, base.height + _PAD_BOTTOM), (255, 255, 255, 255))
    img.paste(base, (0, 0))
    draw = ImageDraw.Draw(img)
    f = _font(font_size)
    fdim = _font(font_size + 2)
    main_label = result.reinf_label_main       # e.g. "DB12@15cm."
    temp_label = result.reinf_label_temp       # e.g. "RB9@15cm."
    for x, y, side, kind in _LEADERS:
        label = temp_label if kind == "temp" else main_label
        b = f.getbbox(label)
        tw, th = b[2] - b[0], b[3] - b[1]
        if side == "TOP":
            tx, ty = x - tw - 2, y - th - 4     # text sits to the left, above the shelf
        else:
            tx, ty = x + 3, y - 2              # below-flight shelf: text to the right
        draw.text((tx, ty), label, fill=(0, 0, 0, 255), font=f)
    # waist thickness at the two centre arrows
    draw.text(_THICKNESS_ANCHOR, f"t={inp.t_cm:.0f}cm.", fill=(0, 0, 0, 255), font=f)

    # ===== เส้นบอกระยะ L (ความยาวตามแนวราบ) — แนวนอนด้านล่าง (2026-07-13) =====
    yL = base.height + 30
    draw.line([(_STAIR_X_LEFT, _STAIR_Y_BOT), (_STAIR_X_LEFT, yL + 6)], fill=(120, 120, 120, 255), width=1)
    draw.line([(_STAIR_X_RIGHT, _STAIR_Y_BOT), (_STAIR_X_RIGHT, yL + 6)], fill=(120, 120, 120, 255), width=1)
    L_txt = f"L = {inp.length_m:.2f} m."
    lb = fdim.getbbox(L_txt)
    _dim_line(draw, (_STAIR_X_LEFT, yL), (_STAIR_X_RIGHT, yL), fdim, L_txt,
              ((_STAIR_X_LEFT + _STAIR_X_RIGHT) // 2 - (lb[2] - lb[0]) // 2, yL - (lb[3] - lb[1]) - 6))

    # ===== เส้นบอกระยะ H (ความสูง) — แนวตั้งด้านขวา =====
    xH = base.width + 44
    draw.line([(_STAIR_X_RIGHT, _STAIR_Y_TOP), (xH + 6, _STAIR_Y_TOP)], fill=(120, 120, 120, 255), width=1)
    draw.line([(_STAIR_X_RIGHT, _STAIR_Y_BOT), (xH + 6, _STAIR_Y_BOT)], fill=(120, 120, 120, 255), width=1)
    _dim_line(draw, (xH, _STAIR_Y_TOP), (xH, _STAIR_Y_BOT), fdim, "", (0, 0))
    H_txt = f"H = {inp.height_m:.2f} m."
    timg = Image.new("RGBA", (fdim.getbbox(H_txt)[2] + 6, font_size + 8), (0, 0, 0, 0))
    ImageDraw.Draw(timg).text((0, 0), H_txt, fill=(0, 0, 0, 255), font=fdim)
    timg = timg.rotate(90, expand=True)
    img.paste(timg, (xH + 6, (_STAIR_Y_TOP + _STAIR_Y_BOT) // 2 - timg.height // 2), timg)

    # ===== ระยะยื่นเหล็กบน L/4 (ตามแนวลาด) — bracket ที่ช่วงบนของบันได =====
    bx, by = _INCLINE_BOT
    tx2, ty2 = _INCLINE_TOP
    ux, uy = tx2 - bx, ty2 - by
    ilen = math.hypot(ux, uy)
    ux, uy = ux / ilen, uy / ilen            # เวกเตอร์หน่วยตามแนวลาด (โคน→ปลาย)
    nx, ny = -uy, ux                          # เวกเตอร์ตั้งฉาก (ชี้ออกด้านบนซ้าย)
    off = 26                                  # ระยะ offset เส้น bracket ออกจากแนวเหล็ก
    p_top = (tx2 + nx * off, ty2 + ny * off)                       # ที่ปลายบน
    p_q = (tx2 - ux * (ilen * 0.25) + nx * off, ty2 - uy * (ilen * 0.25) + ny * off)  # ยื่นลงมา L/4
    q_txt = f"L/4 = {result.incline_length_m / 4.0:.2f} m."
    qb = fdim.getbbox(q_txt)
    mid = ((p_top[0] + p_q[0]) / 2, (p_top[1] + p_q[1]) / 2)
    _dim_line(draw, p_top, p_q, fdim, q_txt,
              (mid[0] - (qb[2] - qb[0]) // 2, mid[1] - (qb[3] - qb[1]) - 16))
    # ขีดเชื่อมจากแนวเหล็กจริงมายังเส้น bracket (2 ปลาย)
    draw.line([(tx2, ty2), p_top], fill=(120, 120, 120, 255), width=1)
    draw.line([(tx2 - ux * (ilen * 0.25), ty2 - uy * (ilen * 0.25)), p_q], fill=(120, 120, 120, 255), width=1)

    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()
