"""
Module 5.2 — ฐานรากเสาเข็ม (Pile Cap)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.footing_pile_cap import (
    PileCapInput, calculate as calc_pile_cap,
    PILE_COUNT_OPTIONS, SOIL_UNIT_WEIGHT_DEFAULT_TON_M3, FOOTING_INVERT_DEPTH_DEFAULT_M,
    PILE_SHAPES, DEFAULT_PILE_SHAPE,
)
from modules.footing_spread import FOOTING_BAR_DIAMETERS_MM, DEFAULT_FOOTING_COVER_CM
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import draw_pile_cap_plan_png, draw_pile_cap_section_png
from common import pile_cap_section as pcs_engine
from common import pile_cap_template as pcs_tmpl
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_pile_cap_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row, render_calc_sheet,
)


def _build_calc_sections(inp, result):
    """วิธีการคำนวณและสูตรที่ใช้ (ฐานรากเสาเข็ม / Pile Cap) — ดึงค่าจาก result (ไม่คำนวณซ้ำ)"""
    g = result.geometry
    pls = result.pile_load_service
    geo = [
        {"desc": "ขนาดฐานรากและการจัดเรียงเสาเข็ม",
         "formula": f"เสาเข็ม {g.n_piles} ต้น (ระยะห่าง {g.spacing_cm:.0f} cm, ระยะขอบ {g.edge_margin_cm:.0f} cm)",
         "result": f"A×B = {g.A_cm:.0f}×{g.B_cm:.0f} cm"},
        {"desc": "ความหนาฐานรากและระยะประสิทธิผล",
         "formula": f"น้ำหนักประลัย W<sub>u</sub> = {result.wu_kg:,.0f} kg → ลงเสาเข็ม {result.pile_load_factored_kg:,.0f} kg/ต้น",
         "result": f"T = {result.t_cm:.0f} cm (d₁ = {result.d1_cm:.1f}, d₂ = {result.d2_cm:.1f} cm)"},
        {"desc": "ตรวจสอบกำลังรับน้ำหนักของเสาเข็ม (Service)",
         "formula": "น้ำหนักลงเสาเข็ม ≤ กำลังปลอดภัย (Safe Load)",
         "sub": f"{pls.service_load_per_pile_ton:.2f} ≤ {pls.safe_load_ton:.2f} ton/ต้น",
         "result": "ผ่าน ✓" if pls.capacity_ok else "ไม่ผ่าน ✗"},
    ]
    bs, cp, pp = result.beam_shear, result.column_punching, result.pile_punching
    shear = []
    if getattr(bs, "applicable", False):
        shear.append(
            {"desc": "แรงเฉือนทางเดียว (One-way / Beam shear)",
             "formula": "V<sub>u</sub> ≤ φV<sub>c</sub> = φ·0.53√f'<sub>c</sub>·b·d",
             "sub": f"{bs.vu_kg:,.0f} ≤ {bs.phi_vc_kg:,.0f} kg",
             "result": "ผ่าน ✓" if bs.shear_ok else "ไม่ผ่าน ✗"})
    else:
        shear.append(
            {"desc": "แรงเฉือนทางเดียว (One-way / Beam shear)",
             "formula": "หน้าตัดวิกฤตพ้นตำแหน่งเสาเข็มริมแล้ว — ไม่เข้าเงื่อนไขตรวจสอบ", "result": "—"})
    shear += [
        {"desc": "แรงเฉือนทะลุรอบเสา (Column Punching / Two-way)",
         "formula": f"เส้นรอบรูปวิกฤต b<sub>o</sub> = {cp.bo_cm:.0f} cm , φV<sub>c</sub> รอบเสา",
         "sub": f"V<sub>u</sub> = {cp.vu_kg:,.0f} ≤ φV<sub>c</sub> = {cp.phi_vc_kg:,.0f} kg",
         "result": "ผ่าน ✓" if cp.shear_ok else "ไม่ผ่าน ✗"},
        {"desc": "แรงเฉือนทะลุรอบเสาเข็ม (Pile Punching)",
         "formula": f"เส้นรอบรูปรอบเสาเข็ม b<sub>o</sub> = {pp.bo_pile_cm:.0f} cm",
         "sub": f"V<sub>u</sub> = {pp.vu_kg:,.0f} ≤ φV<sub>c</sub> = {pp.phi_vc_kg:,.0f} kg",
         "result": "ผ่าน ✓" if pp.shear_ok else "ไม่ผ่าน ✗"},
    ]

    def _flex(f, label, tag):
        note = "ออกแบบเต็มรูปแบบ" if f.full_design else "เหล็กเสริมขั้นต่ำ (ρmin)"
        return [
            {"desc": f"โมเมนต์ดัดที่หน้าเสา — ทิศทาง {tag}",
             "formula": "M<sub>u</sub> = (ผลรวมแรงเสาเข็ม) × ระยะแขน (arm)",
             "sub": f"ระยะแขน = {f.arm_cm:.0f} cm",
             "result": f"{f.mu_kgm:,.0f} kg·m → R<sub>u</sub> = {f.ru_ksc:.2f} ksc"},
            {"desc": f"เหล็กเสริม — ทิศทาง {tag} ({note})",
             "formula": (f"A<sub>s</sub> = ρ·b·d (ρ = {f.rho_used:.4f}) = {f.as_req_cm2:.2f} cm² "
                         f"→ ใช้ {label} (A<sub>s</sub> = {f.as_provided_cm2:.2f} cm²)"),
             "result": "ผ่าน ✓" if f.reinf_ok else "ไม่ผ่าน ✗"},
        ]
    flex_steps = _flex(result.flex_1, result.reinf_label_1, "#1") + _flex(result.flex_2, result.reinf_label_2, "#2")
    other = [
        {"desc": "เหล็กทาบ/เหล็กหนวดกุ้ง (Dowel bar)",
         "formula": "ระยะฝัง L<sub>d</sub> ที่มีจริง ≥ L<sub>bd</sub> ที่ต้องการ",
         "sub": f"{result.dowel.ld_avail_cm:.1f} ≥ {result.dowel.lbd_cm:.1f} cm",
         "result": "ผ่าน ✓" if result.dowel.dowel_ok else "ไม่ผ่าน ✗"},
        {"desc": "ผลการออกแบบโดยรวม",
         "formula": "ผ่านทุกเกณฑ์ (กำลังเสาเข็ม, แรงเฉือน, เหล็กเสริม, เหล็กทาบ)",
         "result": "ผ่าน ✓" if result.design_ok else "ไม่ผ่าน ✗"},
    ]
    return [
        {"title": "ขนาดฐานรากและกำลังรับน้ำหนักเสาเข็ม (Geometry & Pile Capacity)", "steps": geo},
        {"title": "การตรวจสอบแรงเฉือน (Shear Checks)", "steps": shear},
        {"title": "การออกแบบเหล็กเสริมรับแรงดัด (Flexural Design)", "steps": flex_steps},
        {"title": "เหล็กทาบและสรุปผล (Dowel & Summary)", "steps": other},
    ]

inject_card_css()
st.header("5.2 ฐานรากเสาเข็ม (Pile Cap)")

PILE_COUNT_AUTO = "อัตโนมัติ (Auto)"


def _scaled_width(png_bytes, factor):
    """คืนความกว้างเป็นพิกเซล = ความกว้างจริงของภาพ × factor (สำหรับปรับขนาดแสดงผล)."""
    try:
        import io as _io
        from PIL import Image as _PILImage
        return max(1, int(_PILImage.open(_io.BytesIO(png_bytes)).width * factor))
    except Exception:
        return None


def _resolve_pile_count(base_kwargs):
    """โหมดอัตโนมัติ: ไล่ลองจำนวนเสาเข็ม 1→2→3→4 ต้น เลือก 'จำนวนน้อยที่สุด' ที่ผ่านทั้ง
    กำลังรับน้ำหนักเสาเข็ม (service) และการตรวจสอบออกแบบโดยรวม (แรงเฉือน/เหล็กเสริม)."""
    for _n in PILE_COUNT_OPTIONS:      # [1, 2, 3, 4]
        _res = calc_pile_cap(PileCapInput(n_piles=_n, **base_kwargs))
        if _res.pile_load_service.capacity_ok and _res.design_ok:
            return _n, True
    return PILE_COUNT_OPTIONS[-1], False   # ไม่มีจำนวนไหนผ่าน -> ใช้มากสุด (4) แล้วแจ้งเตือน

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "pc_form_gen" not in st.session_state:
    st.session_state["pc_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("footing_pile_cap")
if _loaded_data is not None:
    st.session_state["pc_form_gen"] += 1
    st.session_state["_pc_loaded_data"] = _loaded_data
    st.session_state["_pc_loaded_code"] = _loaded_code
gen = st.session_state["pc_form_gen"]
_loaded = st.session_state.get("_pc_loaded_data") or {}
_loaded_code = st.session_state.get("_pc_loaded_code")

# แถวแรก: 2 กล่องเรียงกัน [รหัสฐานรากเสาเข็ม] [จำนวนเสาเข็ม] — ตามแนวทาง row1 ของ 1.3 พื้นสองทาง
row1_c1, row1_c2 = st.columns([2.2, 1.4])
with row1_c1:
    with st.container(border=True):
        st.markdown("**รหัสฐานรากเสาเข็ม (Pile Cap No.)**")
        footing_name = st.text_input("รหัสฐานรากเสาเข็ม (Pile Cap No.)", value=_loaded_code or "PC-01",
                                      key=f"pc_name_{gen}", label_visibility="collapsed")
with row1_c2:
    with st.container(border=True):
        st.markdown("**จำนวนเสาเข็ม (Pile Count)**")
        _npile_options = [PILE_COUNT_AUTO] + PILE_COUNT_OPTIONS
        n_piles_choice = st.selectbox(
            "จำนวนเสาเข็ม", options=_npile_options,
            index=_npile_options.index(_loaded["n_piles"]) if _loaded.get("n_piles") in _npile_options else 0,
            format_func=lambda v: v if isinstance(v, str) else f"{v} ต้น",
            help="เลือกเองได้ 1/2/3/4 ต้น (1=กึ่งกลางเสา, 2/3=เรียงแถวเดียว, 4=จัดเรียง 2x2) — หรือเลือก "
                 "'อัตโนมัติ' ให้โปรแกรมเลือกจำนวนน้อยที่สุดที่รับน้ำหนักได้และผ่านการตรวจสอบ",
            key=f"pc_npiles_{gen}", label_visibility="collapsed")

st.write("")

# แถวสอง: 4 การ์ดกรอบสี [วัสดุ&เหล็กเสริม (น้ำเงิน)] [แรงออกแบบ (ส้ม)] [เสาเข็ม&ขนาดเสา (เขียว)] [น้ำหนักดินถม (เขียวอมฟ้า)]
col1, col2, col3, col4 = st.columns(4)

with col1:
    with input_card("วัสดุ & เหล็กเสริม", color="blue", icon="🔩", key="pc-material"):
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"pc_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        main_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กเสริม", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 2,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"pc_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, FOOTING_BAR_DIAMETERS_MM)
        _dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                    if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                    else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กเสริม (มม.)", options=main_bar_dia_options,
                                     index=_dia_idx, key=f"pc_dia_{gen}")
        cover_cm = st.number_input("ระยะหุ้มคอนกรีต cv (ซม.)", value=_loaded.get("cover_cm", DEFAULT_FOOTING_COVER_CM),
                                    step=0.5,
                                    help="ค่าเริ่มต้น 7.5 ซม. ตาม ACI 318 20.6.1.3.1 (คอนกรีตหล่อติดดิน/สัมผัสดินถาวร)",
                                    key=f"pc_cover_{gen}")

with col2:
    with input_card("แรงที่ต้องการออกแบบ", color="orange", icon="⚖️", key="pc-load"):
        st.markdown("**บริการ (unfactored)**")
        pd_kg = st.number_input("Pd — น้ำหนักบรรทุกคงที่จากเสา (kg)", value=_loaded.get("pd_kg", 15000.0), step=500.0,
                                 help="แรงตามแนวแกนที่ยังไม่คูณ load factor (service load)", key=f"pc_pd_{gen}")
        pl_kg = st.number_input("Pl — น้ำหนักบรรทุกจรจากเสา (kg)", value=_loaded.get("pl_kg", 8000.0), step=500.0,
                                 help="แรงตามแนวแกนที่ยังไม่คูณ load factor (service load)", key=f"pc_pl_{gen}")

with col3:
    with input_card("เสาเข็ม & ขนาดเสา", color="green", icon="📐", key="pc-geom"):
        _shape_keys = list(PILE_SHAPES.keys())
        pile_shape = st.selectbox(
            "รูปทรงเสาเข็ม", options=_shape_keys,
            index=_shape_keys.index(_loaded["pile_shape"]) if _loaded.get("pile_shape") in _shape_keys
                  else _shape_keys.index(DEFAULT_PILE_SHAPE),
            format_func=lambda k: PILE_SHAPES[k],
            help="มีผลต่อสูตรเส้นรอบรูปวิกฤตของแรงเฉือนทะลุรอบเสาเข็มเดี่ยวเท่านั้น — กลุ่มสี่เหลี่ยม "
                 "(สี่เหลี่ยมตัน/กลวง) ใช้สูตรสี่เหลี่ยมจัตุรัสสมมูล 4×(D+d), รูปทรงอื่น (กลม/หกเหลี่ยม/"
                 "ตัวไอ) ใช้สูตรวงกลม π×(D+d) — แม่นยำสำหรับเสาเข็มกลมโดยตรง และเป็นค่าประมาณฝั่ง"
                 "ปลอดภัยสำหรับรูปทรงที่ไม่มีสูตรมาตรฐานเฉพาะ",
            key=f"pc_shape_{gen}")
        pile_size_cm = st.number_input("ขนาด/เส้นผ่านศูนย์กลางเสาเข็ม D (ซม.)", value=_loaded.get("pile_size_cm", 22.0),
                                        step=1.0, key=f"pc_pilesize_{gen}")
        pile_safe_load_ton = st.number_input("กำลังรับน้ำหนักปลอดภัยต่อต้น (ton)", value=_loaded.get("pile_safe_load_ton", 15.0),
                                              step=0.5, help="Safe Load ต่อต้น (Service) จากผลทดสอบ/spec เสาเข็ม",
                                              key=f"pc_safeload_{gen}")
        st.markdown("**ขนาดเสาที่รองรับ**")
        column_b_cm = st.number_input("ขนาดเสา a1 (ซม., ขนานแนวเรียงเสาเข็ม)", value=_loaded.get("column_b_cm", 30.0),
                                       step=5.0, key=f"pc_colb_{gen}")
        column_h_cm = st.number_input("ขนาดเสา b1 (ซม., ตั้งฉาก)", value=_loaded.get("column_h_cm", 30.0),
                                       step=5.0, key=f"pc_colh_{gen}")

with col4:
    with input_card("น้ำหนักดินถมด้านบน", color="teal", icon="🪨", key="pc-soil"):
        st.caption("สำหรับตรวจสอบน้ำหนักลงเสาเข็ม")
        soil_unit_weight = st.number_input("หน่วยน้ำหนักดิน (ton/m³)",
                                            value=_loaded.get("soil_unit_weight_ton_m3", SOIL_UNIT_WEIGHT_DEFAULT_TON_M3),
                                            step=0.1, key=f"pc_soilgamma_{gen}")
        fi_depth = st.number_input("ความลึกฝังฐานราก F.I. depth (m)",
                                    value=_loaded.get("footing_invert_depth_m", FOOTING_INVERT_DEPTH_DEFAULT_M),
                                    step=0.1, key=f"pc_fidepth_{gen}")

with st.container(border=True):
    st.markdown("**หมายเหตุขอบเขตของโมดูลนี้**")
    st.caption("- รองรับเสาเข็ม 1 ต้น (กึ่งกลางเสาตรงๆ), 2, 3 (เรียงแถวเดียว), 4 ต้น (จัดเรียง 2x2) "
               "เท่านั้น รับแรงตามแนวแกนอย่างเดียว — ยังไม่รองรับโมเมนต์ที่ถ่ายลงฐานราก")
    st.caption("- ระยะขอบ/ระยะห่างเสาเข็มคำนวณจากกฎมาตรฐานทั่วไป (margin=1.5×D, spacing=3×D) แทนตาราง "
               "ผลิตภัณฑ์เสาเข็มเฉพาะยี่ห้อ — ผู้ใช้ควรตรวจสอบกับผู้ผลิตเสาเข็มจริงอีกครั้ง")
    st.caption("- แรงเฉือนทางเดียว (beam shear) ตรวจเฉพาะทิศทาง#1 (ตามแนวเรียงเสาเข็ม) เท่านั้น "
               "ตรงกับไฟล์อ้างอิง — กรณีเสาเป็นสี่เหลี่ยมผืนผ้ามาก ควรตรวจสอบทิศทาง#2 เพิ่มเติมด้วยมือ")
    st.caption("- แรงเฉือนทะลุรอบเสาเข็มเดี่ยวขึ้นกับรูปทรงเสาเข็มที่เลือก: กลุ่มสี่เหลี่ยมใช้เส้นรอบรูป"
               "สี่เหลี่ยมจัตุรัสสมมูล 4×(D+d), รูปทรงอื่น (กลม/หกเหลี่ยม/ตัวไอ) ใช้เส้นรอบรูปวงกลม "
               "π×(D+d) (ค่าประมาณฝั่งปลอดภัยสำหรับรูปทรงที่ไม่มีสูตรมาตรฐานเฉพาะ)")
    st.caption("- Wu (แรงออกแบบ) รวมน้ำหนักตัวเองฐานราก + ดินถมด้านบนแล้ว (ต่างจากฐานรากแผ่ 5.1)")

_base_kwargs = dict(
    fc_ksc=fc,
    main_steel_type=main_steel_type,
    column_b_cm=column_b_cm,
    column_h_cm=column_h_cm,
    pile_size_cm=pile_size_cm,
    pile_safe_load_ton=pile_safe_load_ton,
    pd_kg=pd_kg,
    pl_kg=pl_kg,
    main_bar_dia_mm=main_bar_dia,
    soil_unit_weight_ton_m3=soil_unit_weight,
    footing_invert_depth_m=fi_depth,
    cover_cm=cover_cm,
    pile_shape=pile_shape,
)

# โหมดอัตโนมัติ: ให้โปรแกรมเลือกจำนวนเสาเข็มน้อยที่สุดที่ผ่านทุกการตรวจสอบ
if n_piles_choice == PILE_COUNT_AUTO:
    n_piles, _auto_ok = _resolve_pile_count(_base_kwargs)
    if _auto_ok:
        st.caption(f"🔧 โหมดอัตโนมัติ: เลือกใช้เสาเข็ม **{n_piles} ต้น** (จำนวนน้อยที่สุดที่รับน้ำหนักได้และผ่านการตรวจสอบ)")
    else:
        st.warning(f"โหมดอัตโนมัติ: แม้ใช้ {n_piles} ต้นก็ยังไม่ผ่านทุกเงื่อนไข — ตรวจสอบน้ำหนัก/กำลังรับเสาเข็ม/ขนาดเสา")
else:
    n_piles = n_piles_choice

inp = PileCapInput(n_piles=n_piles, **_base_kwargs)

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ", key="npk-btn-compute-fpc", type="primary", use_container_width=True):
        st.session_state["pc_input"] = inp
        st.session_state["pc_result"] = calc_pile_cap(inp)
        st.session_state["pc_project"] = {"footing_name": footing_name}
        mark_calc_pending_sync("pc")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-fpc", use_container_width=True):
        saved_code = save_item("footing_pile_cap", footing_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสฐานรากเสาเข็ม (Pile Cap No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("pc_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_pc", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "pc_result" in st.session_state:
    inp = st.session_state["pc_input"]
    result = st.session_state["pc_result"]
    project = st.session_state["pc_project"]

    st.header(f"ผลการคำนวณ — {project['footing_name']}")

    if not result.design_ok:
        st.error(f"⚠️ {result.design_fail_reason}")
    elif result.design_fail_reason:
        st.warning(result.design_fail_reason)

    _beam_applicable = result.beam_shear.applicable
    _beam_value = f"{result.beam_shear.vu_kg:,.0f}" if _beam_applicable else "-"
    _beam_note = (f"kg (φVc={result.beam_shear.phi_vc_kg:,.0f})" if _beam_applicable
                  else "ไม่เข้าเงื่อนไขตรวจสอบ")
    _beam_ok = result.beam_shear.shear_ok if _beam_applicable else None

    metric_card_row([
        ("น้ำหนักลงเสาเข็ม (Service)", f"{result.pile_load_service.service_load_per_pile_ton:.2f}",
         f"ton (Safe={result.pile_load_service.safe_load_ton:.2f} ton)", result.pile_load_service.capacity_ok),
        ("แรงเฉือนทางเดียว Vu", _beam_value, _beam_note, _beam_ok),
        ("แรงเฉือนทะลุ (เสา)", f"{result.column_punching.vu_kg:,.0f}",
         f"kg (φVc={result.column_punching.phi_vc_kg:,.0f})", result.column_punching.shear_ok),
        ("แรงเฉือนทะลุ (เสาเข็ม)", f"{result.pile_punching.vu_kg:,.0f}",
         f"kg (φVc={result.pile_punching.phi_vc_kg:,.0f})", result.pile_punching.shear_ok),
        ("เหล็กเสริม #1", f"{result.flex_1.as_provided_cm2:.2f}",
         f"cm² (ต้องการ {result.flex_1.as_req_cm2:.2f})", result.flex_1.reinf_ok),
        ("เหล็กเสริม #2", f"{result.flex_2.as_provided_cm2:.2f}",
         f"cm² (ต้องการ {result.flex_2.as_req_cm2:.2f})", result.flex_2.reinf_ok),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**ขนาดฐานรากเสาเข็ม & น้ำหนักลงเสาเข็ม**")
            st.write(f"**ใช้จริง A×B = {result.geometry.A_cm:.0f}×{result.geometry.B_cm:.0f} cm.** "
                     f"(margin={result.geometry.edge_margin_cm:.1f}cm., spacing={result.geometry.spacing_cm:.1f}cm.)")
            st.write(f"**ความหนา T = {result.t_cm:.0f} cm.** (d1={result.d1_cm:.1f}, d2={result.d2_cm:.1f} cm.)")
            st.write(f"Wu (factored) = {result.wu_kg:,.0f} kg. -> น้ำหนักลงเสาเข็ม (factored) = "
                     f"{result.pile_load_factored_kg:,.0f} kg./ต้น")
            st.write(f"น้ำหนักลงเสาเข็ม (Service) = {result.pile_load_service.service_load_per_pile_ton:.2f} ton "
                     f"(Safe Load = {result.pile_load_service.safe_load_ton:.2f} ton)")
            st.write("ผลตรวจสอบกำลังรับน้ำหนักเสาเข็ม:",
                      "ผ่าน ✅" if result.pile_load_service.capacity_ok else "ไม่ผ่าน ❌")

    with dcol2:
        with st.container(border=True):
            st.markdown("**แรงเฉือน (รายละเอียด)**")
            if result.beam_shear.applicable:
                st.write(f"One-way (ทิศทาง#1): Vu={result.beam_shear.vu_kg:,.0f} kg. / "
                         f"φVc={result.beam_shear.phi_vc_kg:,.0f} kg. "
                         f"({'ผ่าน ✅' if result.beam_shear.shear_ok else 'ไม่ผ่าน ❌'})")
            else:
                st.write("One-way (ทิศทาง#1): ไม่เข้าเงื่อนไขตรวจสอบ (หน้าตัดวิกฤตพ้นตำแหน่งเสาเข็มริมแล้ว)")
            st.write(f"Column punching: Vu={result.column_punching.vu_kg:,.0f} kg. / "
                     f"φVc={result.column_punching.phi_vc_kg:,.0f} kg. "
                     f"({'ผ่าน ✅' if result.column_punching.shear_ok else 'ไม่ผ่าน ❌'})")
            st.write(f"Pile punching: Vu={result.pile_punching.vu_kg:,.0f} kg. / "
                     f"φVc={result.pile_punching.phi_vc_kg:,.0f} kg. "
                     f"({'ผ่าน ✅' if result.pile_punching.shear_ok else 'ไม่ผ่าน ❌'})")

    with dcol3:
        with st.container(border=True):
            st.markdown("**เหล็กเสริม & Dowel**")
            st.write(f"As,req #1 = {result.flex_1.as_req_cm2:.2f} cm² -> **{result.reinf_label_1}** "
                     f"(As={result.flex_1.as_provided_cm2:.2f} cm²)")
            st.write("ผลตรวจสอบ #1:", "ผ่าน ✅" if result.flex_1.reinf_ok else "ไม่ผ่าน ❌")
            _flex2_desc = "ออกแบบเต็มรูปแบบ" if result.flex_2.full_design else "เหล็กเสริมขั้นต่ำ (ρmin)"
            st.write(f"As,req #2 ({_flex2_desc}) = {result.flex_2.as_req_cm2:.2f} cm² -> **{result.reinf_label_2}** "
                     f"(As={result.flex_2.as_provided_cm2:.2f} cm²)")
            st.write("ผลตรวจสอบ #2:", "ผ่าน ✅" if result.flex_2.reinf_ok else "ไม่ผ่าน ❌")

            st.markdown("**เหล็กทาบ/เหล็กหนวดกุ้ง (Dowel Bar)**")
            st.write(f"Lbd ต้องการ = {result.dowel.lbd_cm:.1f} cm. / พื้นที่ฝังที่มีจริง = "
                     f"{result.dowel.ld_avail_cm:.1f} cm.")
            st.write("ผลตรวจสอบ:", "ผ่าน ✅" if result.dowel.dowel_ok else "ไม่ผ่าน ❌")

            st.markdown("**สรุปผล**")
            st.write("ผลตรวจสอบโดยรวม:", "ผ่าน ✅" if result.design_ok else "ไม่ผ่าน ❌")

    st.write("")
    st.subheader("วิธีการคำนวณและสูตรที่ใช้")
    render_calc_sheet(_build_calc_sections(inp, result))

    st.subheader("แปลนฐานรากเสาเข็ม (Pile Cap Plan)")
    plan_png = draw_pile_cap_plan_png(
        result.geometry.A_cm, result.geometry.B_cm, inp.column_b_cm, inp.column_h_cm,
        inp.pile_size_cm, result.geometry.pile_positions_cm,
        inp.main_bar_dia_mm, result.main_bar_type, result.flex_1.n_bars_use, result.flex_2.n_bars_use,
        d_cm=result.d1_cm)
    _plan_w = _scaled_width(plan_png, 0.70)   # ลดขนาดแปลนลง 30% (เหลือ 70%)
    if _plan_w:
        st.image(plan_png, caption="Pile Cap Plan", width=_plan_w)
    else:
        st.image(plan_png, caption="Pile Cap Plan")

    st.subheader("รูปตัดฐานรากเสาเข็ม (Pile Cap Section)")
    # รูปตัดใช้ Geometry Engine (common/pile_cap_section.py): คำนวณพิกัดทุกจุดจากอินพุต
    # -> validateGeometry() -> render (ถ้า geometry ผิดจะไม่วาด แต่ขึ้นการ์ดแจ้ง error)
    # รูปตัด: ใช้ "เทมเพลตจริง" (1/2/3/4 pile.png) แล้วแทนเฉพาะตัวเลขจากการคำนวณ
    # (เหล็กบน/ล่าง, จำนวน+ขนาดเสาเข็ม, Safe Load, cover) — ไม่แตะกราฟิกใดๆ
    section_png = None
    try:
        section_png = pcs_tmpl.render_section_png(inp, result, pile_shape_label=PILE_SHAPES.get(inp.pile_shape))
    except Exception:
        section_png = None
    if section_png is None:   # ไม่มีเทมเพลตสำหรับจำนวนต้นนี้ -> ใช้ Geometry Engine วาดแทน
        try:
            _sec_params = pcs_engine.params_from_pilecap_result(
                inp, result, pedestal_h_mm=inp.column_b_cm * 10.0 * 0.5,
                pile_type_label=f"Pile {inp.pile_size_cm:.0f}")
            section_png = pcs_engine.render_png_mpl(_sec_params, dpi=200)
        except Exception:
            section_png = draw_pile_cap_section_png(
                result.geometry.A_cm, result.t_cm, inp.column_b_cm, inp.cover_cm,
                inp.pile_size_cm, result.geometry.c_dist_cm, inp.n_piles,
                inp.main_bar_dia_mm, result.main_bar_type, result.d1_cm, result.d2_cm,
                pile_safe_load_ton=inp.pile_safe_load_ton,
                n_bars_1=result.flex_1.n_bars_use, n_bars_2=result.flex_2.n_bars_use,
                pile_shape_label=f"Pile {inp.pile_size_cm:.0f}")
    _sec_w = _scaled_width(section_png, 1.70)   # ขยายรูปตัดเป็น 170% ของขนาดจริง
    if _sec_w:
        st.image(section_png, caption="Pile Cap Section", width=_sec_w)
    else:
        st.image(section_png, caption="Pile Cap Section")

    report_html = build_pile_cap_report_html(
        project, inp, result, plan_png, section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("pc", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['footing_name']}")
