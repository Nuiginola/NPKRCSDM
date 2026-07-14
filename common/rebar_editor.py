"""
Manual Rebar Arrangement Editor — ตารางจัดเหล็กเสริมเองแบบ ETABS (ตามภาพอ้างอิงของผู้ใช้)
ใช้ร่วมกับโมดูลคานทั้ง 3 (3.1 ช่วงเดียว / 3.2 ต่อเนื่อง / 3.3 ยื่น).

แต่ละหน้าตัดมีตาราง "Top Bars" และ "Bot Bars" (วางซ้อนกันตามภาพ) — แต่ละตารางมี 3 ชั้น
(1st/2nd/3rd) และแต่ละชั้นกรอก 2 กลุ่ม: Main / Extra (จำนวน=ดรอปดาวน์ + ขนาด⌀=ดรอปดาวน์)
→ คำนวณ As,use = Σ n×พื้นที่⌀ เทียบ As,req → OK/NG พร้อมช่องระยะเหล็กปลอก แล้ววาดรูปตัดใหม่

ค่าเป็น "ชั่วคราว" (session เท่านั้น ไม่ persist ลงไฟล์โปรเจกต์)
"""

import math

import streamlit as st

from common.diagram import draw_beam_section_png

_LAYER_NAMES = ["1st", "2nd", "3rd"]
_COUNT_OPTIONS = list(range(0, 21))   # ตัวเลือกจำนวนเหล็ก (ดรอปดาวน์) 0–20 เส้น

# CSS กล่อง "จัดเหล็กเสริมเอง": พื้นหลังขาว — ใส่สีเขียวเฉพาะหัวข้อแทป + กรอบนอก
# (สโคปด้วย st.container(key="npk-manual-rebar"))
MANUAL_REBAR_CSS = """<style>
.st-key-npk-manual-rebar div[data-testid="stExpander"]{
  border:2px solid #15803D; border-radius:12px; background:#FFFFFF;
  box-shadow:0 2px 6px rgba(21,128,61,0.15);
}
.st-key-npk-manual-rebar div[data-testid="stExpander"] summary{
  background:#DCFCE7; border-radius:10px; padding:6px 12px;
}
.st-key-npk-manual-rebar div[data-testid="stExpander"] summary p{
  color:#166534; font-weight:700; font-size:1.02rem;
}
/* ทำให้ช่องกรอก (ตารางจัดเหล็ก) กระชับ เตี้ย/ชิดขึ้น เพื่อให้พอดีหน้าเดียว — รูปตัดคงขนาดเดิม */
.st-key-npk-manual-rebar div[data-testid="stExpander"] [data-testid="stVerticalBlock"]{ gap:0.28rem; }
.st-key-npk-manual-rebar div[data-testid="stExpander"] [data-testid="stHorizontalBlock"]{ gap:0.4rem; }
.st-key-npk-manual-rebar div[data-testid="stExpander"] [data-baseweb="select"] > div{
  min-height:30px; padding-top:0; padding-bottom:0;
}
.st-key-npk-manual-rebar div[data-testid="stExpander"] [data-baseweb="select"] input{ height:26px; }
.st-key-npk-manual-rebar div[data-testid="stExpander"] p{ margin-bottom:0.15rem; }
</style>"""


def _bar_area_cm2(dia_mm: float) -> float:
    return math.pi / 4.0 * (dia_mm / 10.0) ** 2


_ROW_RATIO = [0.5, 1.0, 1.0, 1.25, 1.25]   # ชั้น / Main จำนวน / Main ⌀ / Extra จำนวน / Extra ⌀


def _rebar_table(key: str, title: str, as_req_cm2: float, default_layers,
                 bar_sizes: list, default_dia: float, gen) -> tuple:
    """เรนเดอร์ตารางจัดเหล็ก 1 ชุด (Top หรือ Bot) — 3 ชั้น × (Main/Extra: จำนวน+⌀).
    ใช้ st.selectbox ทุกช่อง (มีลูกศรดรอปดาวน์ให้เห็นชัดทุกช่อง). คืน (total_per_layer, as_use, ok)."""
    dl = [min(int(n), 20) for n in (list(default_layers) or [0]) if n is not None]
    dl = (dl + [0, 0, 0])[:3]
    bar_sizes = list(bar_sizes)
    if int(default_dia) not in bar_sizes:
        bar_sizes = sorted(set(bar_sizes + [int(default_dia)]))
    _def_di = bar_sizes.index(int(default_dia))

    st.markdown(f"**{title}**")
    hc = st.columns(_ROW_RATIO)
    for _c, _t in zip(hc, ["ชั้น", "Main จำนวน", "Main ⌀(มม.)",
                           "Extra (พิเศษ) จำนวน", "Extra (พิเศษ) ⌀(มม.)"]):
        _c.caption(_t)

    as_use = 0.0
    main_layers, extra_layers = [], []   # จำนวนเหล็กต่อชั้น แยกหลัก/พิเศษ (สำหรับวาดคนละแถว)
    rep_dia = None   # ขนาดเหล็กตัวแทน (ของชั้นแรกที่มีเหล็ก Main) ใช้วาดวงกลมในรูปตัด
    comp_main = {}   # {ขนาด⌀: จำนวนรวม} ของเหล็กหลัก
    comp_extra = {}  # {ขนาด⌀: จำนวนรวม} ของเหล็กเสริมพิเศษ
    for i, lname in enumerate(_LAYER_NAMES):
        rc = st.columns(_ROW_RATIO)
        rc[0].markdown(f"<div style='padding-top:6px;font-weight:600;'>{lname}</div>", unsafe_allow_html=True)
        n_main = rc[1].selectbox("mn", _COUNT_OPTIONS, index=_COUNT_OPTIONS.index(dl[i]),
                                 key=f"{key}_mn_{i}_{gen}", label_visibility="collapsed")
        d_main = rc[2].selectbox("md", bar_sizes, index=_def_di,
                                 key=f"{key}_md_{i}_{gen}", label_visibility="collapsed")
        n_ext = rc[3].selectbox("en", _COUNT_OPTIONS, index=0,
                                key=f"{key}_en_{i}_{gen}", label_visibility="collapsed")
        d_ext = rc[4].selectbox("ed", bar_sizes, index=_def_di,
                                key=f"{key}_ed_{i}_{gen}", label_visibility="collapsed")
        as_use += int(n_main) * _bar_area_cm2(d_main) + int(n_ext) * _bar_area_cm2(d_ext)
        if int(n_main) > 0:
            main_layers.append(int(n_main))
            comp_main[int(d_main)] = comp_main.get(int(d_main), 0) + int(n_main)
            if rep_dia is None:
                rep_dia = float(d_main)
        if int(n_ext) > 0:
            extra_layers.append(int(n_ext))
            comp_extra[int(d_ext)] = comp_extra.get(int(d_ext), 0) + int(n_ext)
            if rep_dia is None:
                rep_dia = float(d_ext)

    ok = as_use >= as_req_cm2 - 1e-6
    m1, m2, m3 = st.columns([1.2, 1.2, 1.0])
    m1.markdown(f"As,req = **{as_req_cm2:.2f}** cm²")
    m2.markdown(f"As,use = **{as_use:.2f}** cm²")
    m3.markdown(f"**{'✅ OK' if ok else '❌ NG'}**")
    comp = {"main": comp_main, "extra": comp_extra}
    return main_layers, extra_layers, as_use, ok, (rep_dia or float(default_dia)), comp


def manual_beam_section(key_prefix: str, label: str,
                        as_req_top: float, as_req_bot: float,
                        default_top, default_bot,
                        b_cm: float, h_cm: float, main_bar_type: str, main_dia: float,
                        bar_sizes: list, stirrup_dia: float, stirrup_type: str,
                        s_use_default: float, s_max_cm: float, gen,
                        torsion=None, stirrup_sizes=None) -> dict:
    """เรนเดอร์ตัวแก้ไขจัดเหล็กเองของหน้าตัดคาน 1 หน้าตัด (Top → Bot → Stirrup → รูปตัด วางซ้อนแนวตั้ง
    เพื่อให้วางหลายหน้าตัดในแถวเดียวกันได้). เหล็กปลอกเลือกขนาด⌀ (ค่าเริ่มต้น 6 มม.) + จำนวนขาได้.
    คืน dict ผลลัพธ์ + png."""
    st.markdown(f"##### {label}")
    top_main, top_extra, as_use_top, ok_top, top_dia, top_comp = _rebar_table(
        f"{key_prefix}_top", "Top Bars (เหล็กบน)", as_req_top, default_top, bar_sizes, main_dia, gen)
    bot_main, bot_extra, as_use_bot, ok_bot, bot_dia, bot_comp = _rebar_table(
        f"{key_prefix}_bot", "Bot Bars (เหล็กล่าง)", as_req_bot, default_bot, bar_sizes, main_dia, gen)
    # ลำดับแถวในรูปตัด: เหล็กหลัก (ใกล้ผิว) ก่อน แล้วเหล็กเสริมพิเศษ (Ext.) อยู่แถวถัดเข้าใน
    # (เหล็ก Ext. ล่างจึงอยู่ "เหนือ" เหล็กล่างหลัก / Ext. บนอยู่ "ใต้" เหล็กบนหลัก)
    bot_layers = (list(bot_main) + list(bot_extra)) or [0]
    top_layers = (list(top_main) + list(top_extra)) or [0]

    # --- เหล็กปลอก: เลือกขนาด⌀ (default 6 มม.) + จำนวนขา + ระยะเรียง ---
    _stir_sizes = list(stirrup_sizes) if stirrup_sizes else [6, 9, 10, 12]
    if int(stirrup_dia) not in _stir_sizes:
        _stir_sizes = sorted(set(_stir_sizes + [int(stirrup_dia)]))
    _def_dia = 6 if 6 in _stir_sizes else int(stirrup_dia)
    st.markdown("**Stirrup (เหล็กปลอก)**")
    c1, c2, c3 = st.columns(3)
    stir_dia = c1.selectbox("ขนาด ⌀(มม.)", _stir_sizes, index=_stir_sizes.index(_def_dia),
                            key=f"{key_prefix}_sdia_{gen}")
    stir_legs = c2.selectbox("จำนวนขา", [1, 2, 3, 4], index=1, key=f"{key_prefix}_slegs_{gen}")
    s_use = c3.number_input("ระยะ @ ใช้ (cm)", min_value=1.0, value=float(s_use_default), step=1.0,
                            key=f"{key_prefix}_stir_{gen}")
    stirrup_ok = s_use <= s_max_cm + 1e-6
    st.markdown(f"เหล็กปลอก = **{stir_legs}-{stirrup_type}{stir_dia:.0f}@{s_use:.0f}cm** &nbsp; "
                f"(@ max = **{s_max_cm:.1f}** cm) &nbsp; → &nbsp; **{'✅ OK' if stirrup_ok else '❌ NG'}**")

    # สร้างป้ายเหล็ก: เหล็กหลัก (Main) + เหล็กเสริมพิเศษ (Ext.) คนละบรรทัด, ไม่มีเส้นชี้
    def _label_lines(comp, side, bar_type):
        lines = []
        main_parts = [f"{c}-{bar_type}{d}" for d, c in sorted(comp["main"].items()) if c > 0]
        if main_parts:
            lines.append(" + ".join(main_parts) + f" ({side})")
        ext_parts = [f"{c}-{bar_type}{d}" for d, c in sorted(comp["extra"].items()) if c > 0]
        if ext_parts:
            lines.append(" + ".join(ext_parts) + " Ext.")
        return lines or None

    png = draw_beam_section_png(
        b_cm, h_cm, bot_layers, top_layers, main_dia, main_bar_type,
        stir_dia, s_use, stirrup_type, torsion=torsion,
        bot_dia_mm=bot_dia, top_dia_mm=top_dia,
        bot_label_lines=_label_lines(bot_comp, "Bottom", main_bar_type),
        top_label_lines=_label_lines(top_comp, "Top", main_bar_type),
        hide_bar_leader=True)
    return {
        "png": png, "as_use_top": as_use_top, "as_use_bot": as_use_bot,
        "ok_top": ok_top, "ok_bot": ok_bot, "s_use": s_use, "stirrup_ok": stirrup_ok,
        "stir_dia": stir_dia, "stir_legs": stir_legs, "top_dia": top_dia, "bot_dia": bot_dia,
        "top_layers": top_layers, "bot_layers": bot_layers,
    }
