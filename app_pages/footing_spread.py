"""
Module 5.1 — ฐานรากแผ่เดี่ยว (Isolated Spread Footing)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.footing_spread import (
    FootingSpreadInput, calculate as calc_footing,
    FOOTING_BAR_DIAMETERS_MM, DEFAULT_FOOTING_COVER_CM, FOUNDING_DEPTH_DEFAULT_M,
)
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import draw_footing_plan_png, draw_footing_section_png
from common import footing_section_template as fs_tmpl
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_footing_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row,
)

inject_card_css()
st.header("5.1 ฐานรากแผ่เดี่ยว (Isolated Spread Footing)")


def _scaled_width(png_bytes, factor):
    """คืนความกว้างเป็นพิกเซล = ความกว้างจริงของภาพ × factor (สำหรับปรับขนาดแสดงผล)."""
    try:
        import io as _io
        from PIL import Image as _PILImage
        return max(1, int(_PILImage.open(_io.BytesIO(png_bytes)).width * factor))
    except Exception:
        return None

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "footing_form_gen" not in st.session_state:
    st.session_state["footing_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("footing_spread")
if _loaded_data is not None:
    st.session_state["footing_form_gen"] += 1
    st.session_state["_footing_loaded_data"] = _loaded_data
    st.session_state["_footing_loaded_code"] = _loaded_code
gen = st.session_state["footing_form_gen"]
_loaded = st.session_state.get("_footing_loaded_data") or {}
_loaded_code = st.session_state.get("_footing_loaded_code")

with st.container(border=True):
    st.markdown("**รหัสฐานราก (Footing No.)**")
    footing_name = st.text_input("รหัสฐานราก (Footing No.)", value=_loaded_code or "F-01",
                                  key=f"ftg_name_{gen}", label_visibility="collapsed")

st.write("")

# แถวการ์ดกรอบสี: [วัสดุ & เหล็กเสริม (น้ำเงิน)] [ขนาดเสา (เขียว)] [แรงออกแบบ (ส้ม)] [ขอบเขตโมดูล (ม่วง)]
col1, col2, col3, col4 = st.columns(4)

with col1:
    with input_card("วัสดุ & เหล็กเสริม", color="blue", icon="🔩", key="ftg-material"):
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"ftg_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        main_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กเสริม", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 2,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"ftg_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, FOOTING_BAR_DIAMETERS_MM)
        _dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                    if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                    else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กเสริม (มม.)", options=main_bar_dia_options,
                                     index=_dia_idx, key=f"ftg_dia_{gen}")
        cover_cm = st.number_input("ระยะหุ้มคอนกรีต cv (ซม.)", value=_loaded.get("cover_cm", DEFAULT_FOOTING_COVER_CM),
                                    step=0.5,
                                    help="ค่าเริ่มต้น 7.5 ซม. ตาม ACI 318 20.6.1.3.1 (คอนกรีตหล่อติดดิน/สัมผัสดินถาวร)",
                                    key=f"ftg_cover_{gen}")

with col2:
    with input_card("ขนาดเสาที่รองรับ", color="green", icon="📐", key="ftg-column"):
        column_b_cm = st.number_input("ขนาดเสา b (ซม.)", value=_loaded.get("column_b_cm", 30.0), step=5.0,
                                       key=f"ftg_colb_{gen}")
        column_h_cm = st.number_input("ขนาดเสา h (ซม.)", value=_loaded.get("column_h_cm", 30.0), step=5.0,
                                       key=f"ftg_colh_{gen}")
        founding_depth_m = st.number_input(
            "ระยะฝังฐานราก (พื้นดิน→ใต้ฐานราก) (ม.)",
            value=_loaded.get("founding_depth_m", FOUNDING_DEPTH_DEFAULT_M), step=0.05, min_value=0.30,
            help="ใช้ในรูปตัด: ความสูงช่วงบน = ระยะฝังนี้ − ความหนาฐาน (ค่าเริ่มต้น 1.50 ม. ตามข้อกำหนด)",
            key=f"ftg_depth_{gen}")

with col3:
    with input_card("แรงออกแบบ & แบกทานดิน", color="orange", icon="⚖️", key="ftg-load"):
        pd_kg = st.number_input("Pd — น้ำหนักบรรทุกคงที่จากเสา (kg)", value=_loaded.get("pd_kg", 15000.0), step=500.0,
                                 help="แรงตามแนวแกนที่ยังไม่คูณ load factor (service load)", key=f"ftg_pd_{gen}")
        pl_kg = st.number_input("Pl — น้ำหนักบรรทุกจรจากเสา (kg)", value=_loaded.get("pl_kg", 8000.0), step=500.0,
                                 help="แรงตามแนวแกนที่ยังไม่คูณ load factor (service load)", key=f"ftg_pl_{gen}")
        qa_net = st.number_input("qa,net — แบกทานดินสุทธิที่ยอมให้ (kg/m²)", value=_loaded.get("qa_net_kg_m2", 8000.0),
                                  step=500.0,
                                  help="ค่าจากผลทดสอบดิน (สมมติเป็นค่าสุทธิ หักน้ำหนักฐานราก/ดินถมด้านบนแล้ว)",
                                  key=f"ftg_qa_{gen}")

with col4:
    with input_card("ขอบเขตของโมดูลนี้", color="purple", icon="ℹ️", key="ftg-scope", compact=False):
        st.caption("- ออกแบบขนาดฐานราก (B), ความหนา (t) และเหล็กเสริมอัตโนมัติ (auto-design) — "
                   "ไม่ใช่การตรวจสอบขนาดที่กำหนดเอง")
        st.caption("- รองรับเฉพาะฐานรากสี่เหลี่ยมจัตุรัส (square) รับแรงตามแนวแกนอย่างเดียว — "
                   "ยังไม่รองรับโมเมนต์ที่ถ่ายลงฐานราก")
        st.caption("- แรงเฉือนทะลุ (punching shear) สมมติเป็นเสาใน (interior column, เส้นรอบรูป 4 ด้านเต็ม, "
                   "&alpha;s=40) — ยังไม่รองรับเสาขอบ/เสามุมอาคาร", unsafe_allow_html=True)
        st.caption("- น้ำหนักฐานราก/ดินถมด้านบนไม่รวมเป็นแรงที่ก่อโมเมนต์/เฉือนภายในฐานราก (ใช้เฉพาะหาขนาด B "
                   "เทียบกับ qa,net)")

inp = FootingSpreadInput(
    fc_ksc=fc,
    main_steel_type=main_steel_type,
    column_b_cm=column_b_cm,
    column_h_cm=column_h_cm,
    pd_kg=pd_kg,
    pl_kg=pl_kg,
    qa_net_kg_m2=qa_net,
    main_bar_dia_mm=main_bar_dia,
    cover_cm=cover_cm,
    founding_depth_m=founding_depth_m,
)

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ (Compute)", key="npk-btn-compute-fs", type="primary", use_container_width=True):
        st.session_state["footing_input"] = inp
        st.session_state["footing_result"] = calc_footing(inp)
        st.session_state["footing_project"] = {"footing_name": footing_name}
        mark_calc_pending_sync("ftg")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-fs", use_container_width=True):
        saved_code = save_item("footing_spread", footing_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสฐานราก (Footing No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("ftg_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_ftg", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "footing_result" in st.session_state:
    inp = st.session_state["footing_input"]
    result = st.session_state["footing_result"]
    project = st.session_state["footing_project"]

    st.header(f"ผลการคำนวณ — {project['footing_name']}")

    if not result.design_ok:
        st.error(f"⚠️ {result.design_fail_reason}")
    elif result.design_fail_reason:
        st.warning(result.design_fail_reason)

    metric_card_row([
        ("แรงแบกทานดิน q,actual", f"{result.q_actual_kg_m2:,.0f}",
         f"kg/m² (qa,net={inp.qa_net_kg_m2:,.0f})", result.bearing_ok),
        ("แรงเฉือนทางเดียว X", f"{result.shear_x.vu_kg:,.0f}",
         f"kg (φVc={result.shear_x.phi_vc_kg:,.0f})", result.shear_x.shear_ok),
        ("แรงเฉือนทางเดียว Y", f"{result.shear_y.vu_kg:,.0f}",
         f"kg (φVc={result.shear_y.phi_vc_kg:,.0f})", result.shear_y.shear_ok),
        ("แรงเฉือนทะลุ (Punching)", f"{result.punching.vu_kg:,.0f}",
         f"kg (φVc={result.punching.phi_vc_kg:,.0f})", result.punching.shear_ok),
        ("เหล็กเสริม X", f"{result.flex_x.as_provided_cm2:.2f}",
         f"cm² ({result.reinf_label_x})", result.flex_x.reinf_ok),
        ("เหล็กเสริม Y", f"{result.flex_y.as_provided_cm2:.2f}",
         f"cm² ({result.reinf_label_y})", result.flex_y.reinf_ok),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**ขนาดฐานราก & แรงแบกทานดิน**")
            st.write(f"B ที่ต้องการ = {result.b_req_m:.2f} m. -> **ใช้จริง {result.B_cm:.0f}×{result.B_cm:.0f} cm.**")
            st.write(f"q,actual = {result.q_actual_kg_m2:,.0f} kg/m² (qa,net = {inp.qa_net_kg_m2:,.0f} kg/m²)")
            st.write("ผลตรวจสอบแบกทานดิน:", "ผ่าน ✅" if result.bearing_ok else "ไม่ผ่าน ❌")
            st.write(f"**ความหนา t = {result.t_cm:.0f} cm.** (dx={result.d_x_cm:.1f}, dy={result.d_y_cm:.1f} cm.)")

    with dcol2:
        with st.container(border=True):
            st.markdown("**เหล็กเสริม (As รวมทั้งแถบกว้าง B)**")
            st.write(f"As,req X = {result.flex_x.as_req_cm2:.2f} cm² -> **{result.reinf_label_x}** "
                     f"(As={result.flex_x.as_provided_cm2:.2f} cm²)")
            st.write("ผลตรวจสอบ X:", "ผ่าน ✅" if result.flex_x.reinf_ok else "ไม่ผ่าน ❌")
            st.write(f"As,req Y = {result.flex_y.as_req_cm2:.2f} cm² -> **{result.reinf_label_y}** "
                     f"(As={result.flex_y.as_provided_cm2:.2f} cm²)")
            st.write("ผลตรวจสอบ Y:", "ผ่าน ✅" if result.flex_y.reinf_ok else "ไม่ผ่าน ❌")

    with dcol3:
        with st.container(border=True):
            st.markdown("**เหล็กทาบ/เหล็กหนวดกุ้ง (Dowel Bar)**")
            st.write(f"Lbd ต้องการ = {result.dowel.lbd_cm:.1f} cm. / พื้นที่ฝังที่มีจริง = "
                     f"{result.dowel.ld_avail_cm:.1f} cm.")
            st.write("ผลตรวจสอบ:", "ผ่าน ✅" if result.dowel.dowel_ok else "ไม่ผ่าน ❌")
            st.markdown("**สรุปผล**")
            st.write("ผลตรวจสอบโดยรวม:", "ผ่าน ✅" if result.design_ok else "ไม่ผ่าน ❌")

    st.subheader("แปลนฐานราก (Footing Plan)")
    plan_png = draw_footing_plan_png(
        result.B_cm, inp.column_b_cm, inp.column_h_cm, inp.main_bar_dia_mm, result.main_bar_type,
        result.flex_x.n_bars_use, result.flex_y.n_bars_use)
    _plan_w = _scaled_width(plan_png, 0.70)   # ลดขนาดแปลนลง 30% (เหลือ 70%)
    if _plan_w:
        st.image(plan_png, caption="Footing Plan", width=_plan_w)
    else:
        st.image(plan_png, caption="Footing Plan")

    st.subheader("รูปตัดฐานราก (Footing Section)")
    # รูปตัด: ใช้เทมเพลตจริง "Footing F1.png" แล้วแทนเฉพาะตัวเลขจากการคำนวณ
    # (เหล็กเสริม X/Y, cover) — ไม่แตะกราฟิกใดๆ
    section_png = None
    try:
        section_png = fs_tmpl.render_section_png(inp, result)
    except Exception:
        section_png = None
    if section_png is None:   # ไม่มีเทมเพลต -> วาดด้วยของเดิม
        section_png = draw_footing_section_png(
            result.B_cm, result.t_cm, inp.column_b_cm, inp.cover_cm, inp.main_bar_dia_mm, result.main_bar_type,
            result.d_x_cm, result.d_y_cm, result.flex_x.n_bars_use, result.flex_y.n_bars_use,
            result.q_actual_kg_m2)
    _sec_w = _scaled_width(section_png, 1.70)   # ขยายรูปตัดเป็น 170% ของขนาดจริง
    if _sec_w:
        st.image(section_png, caption="Footing Section", width=_sec_w)
    else:
        st.image(section_png, caption="Footing Section")

    report_html = build_footing_report_html(
        project, inp, result, plan_png, section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("ftg", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['footing_name']}")
