"""
Module 3.2 — คานต่อเนื่อง (Continuous Beam)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.continuous_beam import (
    ContinuousBeamInput, SpanInput, OverhangInput, calculate as calc_cbeam,
    MAX_SPANS, MIN_SPANS, MAX_POINT_LOADS_PER_SPAN,
    BEAM_WIDTH_CM_OPTIONS, BEAM_DEPTH_CM_OPTIONS,
    BAR_DIAMETERS_MM, STIRRUP_DIAMETERS_MM, DEFAULT_STIRRUP_LEGS,
)
from modules.beam_single_span import PointLoad, reinf_label_with_layers
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import draw_continuous_beam_sfd_bmd_png, draw_continuous_beam_elevation_png, draw_beam_section_png
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_continuous_beam_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row,
)

inject_card_css()
st.header("3.2 คานต่อเนื่อง (Continuous Beam)")


def _scaled_width(png_bytes, factor):
    """คืนความกว้างเป็นพิกเซล = ความกว้างจริงของภาพ × factor (สำหรับปรับขนาดแสดงผล)."""
    try:
        import io as _io
        from PIL import Image as _PILImage
        return max(1, int(_PILImage.open(_io.BytesIO(png_bytes)).width * factor))
    except Exception:
        return None

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง) — โมดูลนี้ซับซ้อน
# ที่สุด (ช่วงคานหลายช่วง + ปลายยื่น 2 ฝั่ง + point load ซ้อนหลายชั้น) จึงต้อง gen-suffix
# ทุก key ในหน้านี้ (เดิมบาง key เช่น cb_main_steel/cb_b/cb_nspans เป็น key คงที่ ไม่เคย
# รีเซ็ตได้ — ต้องแก้ให้ผูกกับ gen เหมือนกันหมด ไม่งั้นโหลดค่าเก่าทับค่าที่โหลดใหม่ไม่ได้)
if "cb_form_gen" not in st.session_state:
    st.session_state["cb_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("continuous_beam")
if _loaded_data is not None:
    st.session_state["cb_form_gen"] += 1
    st.session_state["_cb_loaded_data"] = _loaded_data
    st.session_state["_cb_loaded_code"] = _loaded_code
gen = st.session_state["cb_form_gen"]
_loaded = st.session_state.get("_cb_loaded_data") or {}
_loaded_code = st.session_state.get("_cb_loaded_code")
_loaded_spans = _loaded.get("spans") or []
_loaded_left_ov = _loaded.get("left_overhang")
_loaded_right_ov = _loaded.get("right_overhang")

# แถวแรก: กล่องกรอบระบุรหัสคาน (ตามมาตรฐาน UI การ์ด — เทียบหน้า 1.3 พื้นสองทาง)
with st.container(border=True):
    st.markdown("**รหัสคาน (Beam No.)**")
    beam_name = st.text_input("รหัสคาน (Beam No.)", value=_loaded_code or "CB-01", key=f"cb_name_{gen}",
                               label_visibility="collapsed")

st.write("")

_steel_options = list(GS_STEEL_FY_KSC.keys())
_default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0

# แถวสอง: 2 การ์ดกรอบสี [วัสดุ/เหล็กเสริม (น้ำเงิน)] [ขนาดคาน/ผังคาน (เขียว)]
mcol1, mcol2 = st.columns(2)
with mcol1:
    with input_card("วัสดุ/เหล็กเสริม", color="blue", icon="🔩", key="cb-material"):
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"cb_fc_{gen}")
        main_steel_type = st.selectbox(
            "เหล็กหลัก (บน/ล่าง)", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 2,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            key=f"cb_main_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
        _main_dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                          if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                          else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                     index=_main_dia_idx, key=f"cb_main_dia_{gen}")
        stirrup_steel_type = st.selectbox(
            "เหล็กปลอก", options=_steel_options,
            index=_steel_options.index(_loaded["stirrup_steel_type"]) if _loaded.get("stirrup_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            key=f"cb_stirrup_steel_{gen}")
        stirrup_bar_dia_options = bar_dia_options_for_steel(stirrup_steel_type, STIRRUP_DIAMETERS_MM)
        _stirrup_dia_idx = (stirrup_bar_dia_options.index(_loaded["stirrup_bar_dia_mm"])
                             if _loaded.get("stirrup_bar_dia_mm") in stirrup_bar_dia_options
                             else min(0, len(stirrup_bar_dia_options) - 1))
        stirrup_bar_dia = st.selectbox("ขนาดเหล็กปลอก (มม.)", options=stirrup_bar_dia_options,
                                        index=_stirrup_dia_idx, key=f"cb_stirrup_dia_{gen}")
        stirrup_spacing = st.number_input("ระยะห่างปลอกที่ใช้ (ซม.)",
                                           value=_loaded.get("stirrup_spacing_use_cm", 15.0), step=1.0,
                                           key=f"cb_stirrup_spacing_{gen}")

with mcol2:
    with input_card("ขนาดคาน/ผังคาน", color="green", icon="📐", key="cb-geometry"):
        _b_idx = BEAM_WIDTH_CM_OPTIONS.index(_loaded["b_cm"]) if _loaded.get("b_cm") in BEAM_WIDTH_CM_OPTIONS else 1
        b_cm = st.selectbox("ความกว้างคาน b (cm)", options=BEAM_WIDTH_CM_OPTIONS, index=_b_idx, key=f"cb_b_{gen}")
        _h_idx = BEAM_DEPTH_CM_OPTIONS.index(_loaded["h_cm"]) if _loaded.get("h_cm") in BEAM_DEPTH_CM_OPTIONS else 2
        h_cm = st.selectbox("ความลึกคาน h (cm)", options=BEAM_DEPTH_CM_OPTIONS, index=_h_idx, key=f"cb_h_{gen}")
        n_spans = st.number_input(f"จำนวนช่วงคาน ({MIN_SPANS}-{MAX_SPANS})",
                                   min_value=MIN_SPANS, max_value=MAX_SPANS,
                                   value=len(_loaded_spans) if _loaded_spans else 3, step=1, key=f"cb_nspans_{gen}")

st.write("")

# การ์ดกรอบสีม่วง ครอบทั้งส่วน "ช่วงคานแต่ละช่วง" (dynamic loop) — ⚠️ คงโครงสร้าง loop และ
# widget key เดิมทุกจุดตามคำเตือนโครงการ (gen + index i/j ผูกกับทุก key ของช่วง/point-load
# เพื่อรองรับ "เปิดกลับมาแก้ไข") ไม่แตะต้องแม้แต่จุดเดียว — เปลี่ยนแค่ "ภาชนะ" ที่ห่อ loop
# จาก container เปล่า (เดิม inject_compact_input_css("cb-span-box") + container ต่อช่วง)
# มาเป็นการ์ดกรอบสีใบเดียวครอบทั้งหมด (compact CSS ของ input_card ครอบคลุมถึงลูกใน
# expander ด้วยเพราะเป็น descendant selector เหมือนของเดิม)
# compact=False: การ์ดนี้วางช่องกรอก 3 ช่องต่อแถว (st.columns(3)) + label ยาว — ถ้าใช้ compact
# (label ชิดซ้าย/ช่องชิดขวาในคอลัมน์แคบ) label จะถูกบีบจนอ่านไม่ออก จึงให้ label อยู่เหนือช่องกรอก
with input_card("ช่วงคาน/น้ำหนักจร", color="purple", icon="📏", key="continuous-spans", compact=False):
    span_inputs = []
    for i in range(int(n_spans)):
        _span_default = _loaded_spans[i] if i < len(_loaded_spans) else {}
        _span_pts_default = _span_default.get("point_loads") or []
        with st.expander(f"ช่วงที่ {i + 1}", expanded=(i < 2)):
            sc1, sc2, sc3 = st.columns(3)
            with sc1:
                L = st.number_input("ความยาวช่วง L (m.)", value=_span_default.get("length_m", 4.0), step=0.1,
                                     min_value=0.1, key=f"cb_span_L_{gen}_{i}")
            with sc2:
                dl = st.number_input("Line Load DL (kg/m) — ไม่รวมน้ำหนักตัวเองคาน",
                                      value=_span_default.get("line_load_dl_kg_m", 200.0), step=10.0,
                                      key=f"cb_span_dl_{gen}_{i}")
            with sc3:
                ll = st.number_input("Line Load LL (kg/m)", value=_span_default.get("line_load_ll_kg_m", 300.0),
                                      step=10.0, key=f"cb_span_ll_{gen}_{i}")
            n_pts = st.number_input(f"จำนวนจุด Point Load (สูงสุด {MAX_POINT_LOADS_PER_SPAN})", min_value=0,
                                     max_value=MAX_POINT_LOADS_PER_SPAN, value=len(_span_pts_default), step=1,
                                     key=f"cb_span_npts_{gen}_{i}")
            pts = []
            for j in range(int(n_pts)):
                _pt_default = _span_pts_default[j] if j < len(_span_pts_default) else {}
                pc1, pc2, pc3 = st.columns(3)
                with pc1:
                    p_dl = st.number_input("P_DL (kg)", value=_pt_default.get("p_dl_kg", 0.0), step=50.0,
                                            key=f"cb_span_{gen}_{i}_pl_dl_{j}")
                with pc2:
                    p_ll = st.number_input("P_LL (kg)", value=_pt_default.get("p_ll_kg", 0.0), step=50.0,
                                            key=f"cb_span_{gen}_{i}_pl_ll_{j}")
                with pc3:
                    p_x = st.number_input("ระยะ x จากปลายซ้ายช่วงนี้ (m.)", value=_pt_default.get("x_m", 0.0), step=0.1,
                                           key=f"cb_span_{gen}_{i}_pl_x_{j}")
                pts.append(PointLoad(p_dl_kg=p_dl, p_ll_kg=p_ll, x_m=p_x))
        span_inputs.append(SpanInput(length_m=L, line_load_dl_kg_m=dl, line_load_ll_kg_m=ll, point_loads=pts))

st.write("")

# การ์ดกรอบสีเขียวอมฟ้า (teal) ครอบส่วนปลายยื่น — เช่นเดียวกับข้างบน คงโครงสร้าง/key เดิม
# ทุกจุด (point-load loop ของปลายยื่นแต่ละฝั่งผูกกับ gen + index j เหมือนเดิม ไม่ใช่ index
# ของช่วง เพราะปลายยื่นมีแค่ฝั่งละหนึ่งเดียว ไม่ใช่ list หลายช่วงแบบ spans ด้านบน)
# compact=False: เหตุผลเดียวกับการ์ดช่วงคาน (มี st.columns หลายช่อง + point-load แถวละ 3 ช่อง)
with input_card("ปลายยื่น (Overhang) — ถ้ามี", color="teal", icon="↔️", key="cb-overhang", compact=False):
    oc1, oc2 = st.columns(2)
    with oc1:
        use_left_ov = st.checkbox("มีปลายยื่นด้านซ้าย (Left Overhang)", value=bool(_loaded_left_ov),
                                   key=f"cb_use_left_ov_{gen}")
        left_ov_input = None
        if use_left_ov:
            _lov = _loaded_left_ov or {}
            _lov_pts = _lov.get("point_loads") or []
            with st.container(border=True, key="cb-ov-box-left"):
                L0 = st.number_input("ความยาวปลายยื่นซ้าย (m.)", value=_lov.get("length_m", 1.0), step=0.1, min_value=0.05,
                                      key=f"cb_left_ov_L_{gen}")
                dl0 = st.number_input("Line Load DL (kg/m)", value=_lov.get("line_load_dl_kg_m", 200.0), step=10.0,
                                       key=f"cb_left_ov_dl_{gen}")
                ll0 = st.number_input("Line Load LL (kg/m)", value=_lov.get("line_load_ll_kg_m", 300.0), step=10.0,
                                       key=f"cb_left_ov_ll_{gen}")
                n_pts0 = st.number_input(f"จำนวนจุด Point Load (สูงสุด {MAX_POINT_LOADS_PER_SPAN})", min_value=0,
                                          max_value=MAX_POINT_LOADS_PER_SPAN, value=len(_lov_pts), step=1,
                                          key=f"cb_left_ov_npts_{gen}")
                pts0 = []
                for j in range(int(n_pts0)):
                    _pt_default = _lov_pts[j] if j < len(_lov_pts) else {}
                    pc1, pc2, pc3 = st.columns(3)
                    with pc1:
                        p_dl = st.number_input("P_DL (kg)", value=_pt_default.get("p_dl_kg", 0.0), step=50.0,
                                                key=f"cb_left_ov_pl_dl_{gen}_{j}")
                    with pc2:
                        p_ll = st.number_input("P_LL (kg)", value=_pt_default.get("p_ll_kg", 0.0), step=50.0,
                                                key=f"cb_left_ov_pl_ll_{gen}_{j}")
                    with pc3:
                        p_x = st.number_input("ระยะ x จากจุดรองรับ (m.)", value=_pt_default.get("x_m", 0.0), step=0.1,
                                               key=f"cb_left_ov_pl_x_{gen}_{j}")
                    pts0.append(PointLoad(p_dl_kg=p_dl, p_ll_kg=p_ll, x_m=p_x))
            left_ov_input = OverhangInput(length_m=L0, line_load_dl_kg_m=dl0, line_load_ll_kg_m=ll0, point_loads=pts0)

    with oc2:
        use_right_ov = st.checkbox("มีปลายยื่นด้านขวา (Right Overhang)", value=bool(_loaded_right_ov),
                                    key=f"cb_use_right_ov_{gen}")
        right_ov_input = None
        if use_right_ov:
            _rov = _loaded_right_ov or {}
            _rov_pts = _rov.get("point_loads") or []
            with st.container(border=True, key="cb-ov-box-right"):
                L1 = st.number_input("ความยาวปลายยื่นขวา (m.)", value=_rov.get("length_m", 1.0), step=0.1, min_value=0.05,
                                      key=f"cb_right_ov_L_{gen}")
                dl1 = st.number_input("Line Load DL (kg/m)", value=_rov.get("line_load_dl_kg_m", 200.0), step=10.0,
                                       key=f"cb_right_ov_dl_{gen}")
                ll1 = st.number_input("Line Load LL (kg/m)", value=_rov.get("line_load_ll_kg_m", 300.0), step=10.0,
                                       key=f"cb_right_ov_ll_{gen}")
                n_pts1 = st.number_input(f"จำนวนจุด Point Load (สูงสุด {MAX_POINT_LOADS_PER_SPAN})", min_value=0,
                                          max_value=MAX_POINT_LOADS_PER_SPAN, value=len(_rov_pts), step=1,
                                          key=f"cb_right_ov_npts_{gen}")
                pts1 = []
                for j in range(int(n_pts1)):
                    _pt_default = _rov_pts[j] if j < len(_rov_pts) else {}
                    pc1, pc2, pc3 = st.columns(3)
                    with pc1:
                        p_dl = st.number_input("P_DL (kg)", value=_pt_default.get("p_dl_kg", 0.0), step=50.0,
                                                key=f"cb_right_ov_pl_dl_{gen}_{j}")
                    with pc2:
                        p_ll = st.number_input("P_LL (kg)", value=_pt_default.get("p_ll_kg", 0.0), step=50.0,
                                                key=f"cb_right_ov_pl_ll_{gen}_{j}")
                    with pc3:
                        p_x = st.number_input("ระยะ x จากจุดรองรับ (m.)", value=_pt_default.get("x_m", 0.0), step=0.1,
                                               key=f"cb_right_ov_pl_x_{gen}_{j}")
                    pts1.append(PointLoad(p_dl_kg=p_dl, p_ll_kg=p_ll, x_m=p_x))
            right_ov_input = OverhangInput(length_m=L1, line_load_dl_kg_m=dl1, line_load_ll_kg_m=ll1, point_loads=pts1)

# --- ตัวเลือกวิเคราะห์ & การจัดเหล็ก ---
with st.container(border=True):
    st.markdown("**ตัวเลือกวิเคราะห์ & การจัดเหล็ก**")
    fixed_end_supports = st.checkbox(
        "จุดรองรับปลายเป็นแบบ FIX เมื่อด้านนั้นไม่มีคานยื่น (ออกแบบเหล็กบนที่ปลายได้จริง)",
        value=bool(_loaded.get("fixed_end_supports", True)),
        help="เมื่อปลายด้านใดไม่มีคานยื่น จะถือว่าจุดรองรับปลายนั้นยึดแน่น (FIX) เกิดโมเมนต์ลบที่ปลาย → "
             "ออกแบบเหล็กบนที่ปลายได้จริง (ด้านที่มีคานยื่นใช้โมเมนต์คานยื่นเสมอ ไม่กระทบ) — "
             "ปิดสวิตช์นี้เพื่อกลับไปเป็นปลายอิสระ (Pinned, M=0)",
        key=f"cb_fixend_{gen}")
    _reinf_mode = st.radio(
        "การจัดเหล็กเสริม", options=["อัตโนมัติ (Auto)", "จัดเอง (Manual)"],
        index=1 if _loaded.get("manual_reinf") else 0, horizontal=True, key=f"cb_reinfmode_{gen}")
    manual_reinf = (_reinf_mode == "จัดเอง (Manual)")
    manual_bot_row1 = manual_bot_row2 = manual_top_row1 = manual_top_row2 = 0
    if manual_reinf:
        st.caption(f"ระบุจำนวนเส้น (เหล็กหลักขนาด {main_bar_dia:.0f} มม.) ใช้ทั้งคาน — "
                   "โปรแกรมจะตรวจสอบว่าพอกับ As ที่ต้องการที่ตำแหน่ง governing หรือไม่ (ถ้าไม่พอ = ไม่ผ่าน)")
        mr1, mr2, mr3, mr4 = st.columns(4)
        with mr1:
            manual_bot_row1 = int(st.number_input("เหล็กล่าง แถวที่ 1", min_value=0, step=1,
                value=int(_loaded.get("manual_bot_row1", 2)), key=f"cb_mbot1_{gen}"))
        with mr2:
            manual_bot_row2 = int(st.number_input("เหล็กล่าง แถวที่ 2", min_value=0, step=1,
                value=int(_loaded.get("manual_bot_row2", 0)), key=f"cb_mbot2_{gen}"))
        with mr3:
            manual_top_row1 = int(st.number_input("เหล็กบน แถวที่ 1", min_value=0, step=1,
                value=int(_loaded.get("manual_top_row1", 2)), key=f"cb_mtop1_{gen}"))
        with mr4:
            manual_top_row2 = int(st.number_input("เหล็กบน แถวที่ 2", min_value=0, step=1,
                value=int(_loaded.get("manual_top_row2", 0)), key=f"cb_mtop2_{gen}"))

inp = ContinuousBeamInput(
    fc_ksc=fc, main_steel_type=main_steel_type, stirrup_steel_type=stirrup_steel_type,
    b_cm=b_cm, h_cm=h_cm, spans=span_inputs,
    left_overhang=left_ov_input, right_overhang=right_ov_input,
    main_bar_dia_mm=main_bar_dia, stirrup_bar_dia_mm=stirrup_bar_dia,
    stirrup_legs=DEFAULT_STIRRUP_LEGS, stirrup_spacing_use_cm=stirrup_spacing,
    fixed_end_supports=fixed_end_supports,
    manual_reinf=manual_reinf,
    manual_bot_row1=manual_bot_row1, manual_bot_row2=manual_bot_row2,
    manual_top_row1=manual_top_row1, manual_top_row2=manual_top_row2,
)

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ (Compute)", key="npk-btn-compute-cbeam", type="primary", use_container_width=True):
        bad = []
        for i, s in enumerate(span_inputs):
            for p in s.point_loads:
                if not (0.0 <= p.x_m <= s.length_m):
                    bad.append(f"ช่วงที่ {i + 1}: ระยะ x ของน้ำหนักจุดต้องอยู่ระหว่าง 0 ถึง {s.length_m:.2f} m.")
        if left_ov_input is not None:
            for p in left_ov_input.point_loads:
                if not (0.0 <= p.x_m <= left_ov_input.length_m):
                    bad.append(f"ปลายยื่นซ้าย: ระยะ x ต้องอยู่ระหว่าง 0 ถึง {left_ov_input.length_m:.2f} m.")
        if right_ov_input is not None:
            for p in right_ov_input.point_loads:
                if not (0.0 <= p.x_m <= right_ov_input.length_m):
                    bad.append(f"ปลายยื่นขวา: ระยะ x ต้องอยู่ระหว่าง 0 ถึง {right_ov_input.length_m:.2f} m.")

        if bad:
            for b in bad:
                st.error(b)
        else:
            st.session_state["cbeam_input"] = inp
            st.session_state["cbeam_result"] = calc_cbeam(inp)
            st.session_state["cbeam_project"] = {"beam_name": beam_name}
            mark_calc_pending_sync("cb")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-cbeam", use_container_width=True):
        saved_code = save_item("continuous_beam", beam_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสคาน (Beam No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("cb_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_cb", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "cbeam_result" in st.session_state:
    inp = st.session_state["cbeam_input"]
    result = st.session_state["cbeam_result"]
    project = st.session_state["cbeam_project"]

    st.header(f"ผลการคำนวณ — {project['beam_name']}")

    if getattr(result, "fixed_end_supports", False) and (result.left_fixed or result.right_fixed):
        _ends = []
        if result.left_fixed:
            _ends.append("ปลายซ้าย")
        if result.right_fixed:
            _ends.append("ปลายขวา")
        st.info(f"🔩 จุดรองรับ {' และ '.join(_ends)} = FIX (ยึดแน่น เพราะไม่มีคานยื่น) — "
                "ออกแบบเหล็กบนที่ปลายจากโมเมนต์ลบจริง")

    if getattr(result, "manual_reinf", False):
        if result.design_ok:
            st.success(f"✅ โหมดจัดเหล็กเอง — ผ่าน: เหล็กล่างจัด {result.manual_bottom.as_provided_cm2:.2f} ≥ ต้องการ "
                       f"{result.manual_req_bottom_cm2:.2f} cm² และเหล็กบนจัด {result.manual_top.as_provided_cm2:.2f} ≥ "
                       f"{result.manual_req_top_cm2:.2f} cm²")
        else:
            st.error(f"❌ โหมดจัดเหล็กเอง — **ไม่ผ่าน**: {result.design_fail_reason}")
        st.caption("หมายเหตุ: ตารางเหล็กล่าง/บนด้านล่างแสดง **As ที่ต้องการ** แต่ละตำแหน่ง (ออกแบบอัตโนมัติไว้เทียบ) "
                   "— ส่วนเหล็กที่ใช้จริงคือค่าที่คุณจัดเอง ตามผลตรวจสอบด้านบน และแสดงในรูปตัดด้านล่าง")

    st.subheader("ผังคาน (Beam Layout)")
    elevation_png = draw_continuous_beam_elevation_png(result)
    st.image(elevation_png, use_container_width=True)

    gsp_i = result.governing_span_index
    gsup_i = result.governing_support_index
    gsp = result.spans[gsp_i]
    gsup = result.supports[gsup_i]

    metric_card_row([
        ("โมเมนต์บวกสูงสุด (ช่วงวิกฤต)", f"{gsp.mu_pos_max_kgm:.0f}", f"kg-m. ช่วงที่ {gsp_i + 1}", gsp.bottom.reinf_ok),
        ("เหล็กล่างที่ใช้ (ช่วงวิกฤต)", f"{gsp.bottom.as_provided_cm2:.2f}",
         f"cm² (ต้องการ {gsp.bottom.as_req_cm2:.2f})", gsp.bottom.reinf_ok),
        ("โมเมนต์ลบสูงสุด (จุดรองรับวิกฤต)", f"{abs(gsup.moment_kgm):.0f}", f"kg-m. S{gsup_i}", gsup.top.reinf_ok),
        ("เหล็กปลอก (ช่วงวิกฤต)", f"{gsp.stirrup.vu_kg:.0f}",
         f"kg. S_max={gsp.stirrup.s_max_cm:.1f} cm", gsp.stirrup.stirrup_ok),
    ])
    st.write("")

    with st.container(border=True):
        st.subheader("โมเมนต์ & แรงปฏิกิริยาที่จุดรองรับ")
        for s in result.supports:
            suffix = " (มีปลายยื่น)" if (s.is_exterior and s.has_overhang) else (" (ริม)" if s.is_exterior else "")
            st.write(f"S{s.index}{suffix}: M = {s.moment_kgm:+.2f} kg-m., R = {s.reaction_kg:.2f} kg.")

    with st.container(border=True):
        st.subheader("เหล็กเสริมล่าง (Bottom Bars) ต่อช่วง — รายละเอียดครบ")
        for i, sp in enumerate(result.spans):
            b = sp.bottom
            label = reinf_label_with_layers(b, result.main_bar_type, inp.main_bar_dia_mm)
            st.write(f"ช่วงที่ {i + 1}: Mu+ = {sp.mu_pos_max_kgm:.0f} kg-m. @x={sp.mu_pos_max_x_m:.2f}m. → "
                     f"d = {b.d_cm:.2f} cm., Ru = {b.ru_ksc:.2f} ksc, ρ ที่ใช้ = {b.rho_used:.4f} → "
                     f"As ต้องการ = {b.as_req_cm2:.2f} cm² (As ใช้จริง = {b.as_provided_cm2:.2f} cm²) → **{label}** "
                     f"({'ผ่าน ✅' if b.reinf_ok else 'ไม่ผ่าน ❌'})")
            if b.doubly_reinforced:
                st.warning(f"⚠️ ช่วงที่ {i + 1}: ต้องเสริมเหล็กสองชั้น (As2={b.as_comp_req_cm2:.2f} cm²)")
            if b.n_layers > 1:
                breakdown = "+".join(str(n) for n in b.bars_per_layer if n > 0)
                st.info(f"ℹ️ ช่วงที่ {i + 1}: เหล็กล่างเกิน 1 ชั้น จัดเป็น {b.n_layers} ชั้นอัตโนมัติ ({breakdown} เส้น)")
            if not b.reinf_ok:
                st.error(f"⚠️ ช่วงที่ {i + 1}: เหล็กล่างเกินกว่าจะใส่ได้แม้จัดหลายชั้นแล้ว (สูงสุด {b.max_bars_single_layer * 3} เส้น)")

    with st.container(border=True):
        st.subheader("เหล็กเสริมบน (Top Bars) ต่อจุดรองรับ — รายละเอียดครบ")
        for s in result.supports:
            if s.is_exterior and not s.has_overhang:
                continue
            t = s.top
            label = reinf_label_with_layers(t, result.main_bar_type, inp.main_bar_dia_mm)
            st.write(f"S{s.index}: |M| = {abs(s.moment_kgm):.0f} kg-m. → d = {t.d_cm:.2f} cm., "
                     f"Ru = {t.ru_ksc:.2f} ksc, ρ ที่ใช้ = {t.rho_used:.4f} → "
                     f"As ต้องการ = {t.as_req_cm2:.2f} cm² (As ใช้จริง = {t.as_provided_cm2:.2f} cm²) → "
                     f"**{label}** ({'ผ่าน ✅' if t.reinf_ok else 'ไม่ผ่าน ❌'})")
            if t.n_layers > 1:
                breakdown = "+".join(str(n) for n in t.bars_per_layer if n > 0)
                st.info(f"ℹ️ S{s.index}: เหล็กบนเกิน 1 ชั้น จัดเป็น {t.n_layers} ชั้นอัตโนมัติ ({breakdown} เส้น)")
            if not t.reinf_ok:
                st.error(f"⚠️ S{s.index}: เหล็กบนเกินกว่าจะใส่ได้แม้จัดหลายชั้นแล้ว (สูงสุด {t.max_bars_single_layer * 3} เส้น)")

    with st.container(border=True):
        st.subheader("เหล็กปลอก (Stirrup) ต่อช่วง/ปลายยื่น")
        for i, sp in enumerate(result.spans):
            st_ = sp.stirrup
            st.write(f"ช่วงที่ {i + 1}: Vu,max = {st_.vu_kg:.0f} kg. → S_max = {st_.s_max_cm:.1f} cm. → "
                     f"{'ผ่าน ✅' if st_.stirrup_ok else 'ไม่ผ่าน ❌'}")
            if st_.section_too_small:
                st.error(f"⚠️ ช่วงที่ {i + 1}: หน้าตัดคานเล็กเกินไปสำหรับแรงเฉือนนี้")
        if result.left_overhang is not None:
            st_ = result.left_overhang.stirrup
            st.write(f"ปลายยื่นซ้าย: Vu,max = {st_.vu_kg:.0f} kg. → S_max = {st_.s_max_cm:.1f} cm. → "
                     f"{'ผ่าน ✅' if st_.stirrup_ok else 'ไม่ผ่าน ❌'}")
        if result.right_overhang is not None:
            st_ = result.right_overhang.stirrup
            st.write(f"ปลายยื่นขวา: Vu,max = {st_.vu_kg:.0f} kg. → S_max = {st_.s_max_cm:.1f} cm. → "
                     f"{'ผ่าน ✅' if st_.stirrup_ok else 'ไม่ผ่าน ❌'}")
        st.write(f"**เหล็กปลอกที่ใช้จริงทั้งคาน: {DEFAULT_STIRRUP_LEGS}-{result.stirrup_bar_type}"
                 f"{inp.stirrup_bar_dia_mm:.0f}@{inp.stirrup_spacing_use_cm:.0f}cm.**")

    st.subheader("กราฟแรงเฉือน & โมเมนต์รวมทั้งคาน (SFD/BMD)")
    sfd_bmd_png = draw_continuous_beam_sfd_bmd_png(result)
    _sfd_l, _sfd_r = st.columns([4, 1])   # ลดสัดส่วน SFD/BMD ลง 20% (แสดง 80% ของความกว้าง)
    with _sfd_l:
        st.image(sfd_bmd_png, use_container_width=True)

    st.subheader("รูปตัดรายละเอียดการเสริมเหล็ก (Reinforcement Detail Sections)")
    # โหมดจัดเหล็กเอง: ใช้การจัดเหล็กที่ผู้ใช้กรอก (ทั้งคาน) แทนการจัดอัตโนมัติ
    _mid_bot = (result.manual_bottom.bars_per_layer
                if result.manual_reinf and result.manual_bottom else gsp.bottom.bars_per_layer)
    _sup_top = (result.manual_top.bars_per_layer
                if result.manual_reinf and result.manual_top else gsup.top.bars_per_layer)
    midspan_section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, _mid_bot, result.nominal_bars.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    support_section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, result.nominal_bars.bars_per_layer, _sup_top,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    # ขยายรูปตัดคาน 1.4 เท่า — แสดงเรียงบน-ล่าง (ไม่ใช่คู่กัน) เพื่อไม่ให้ล้นคอลัมน์
    _ms_w = _scaled_width(midspan_section_png, 1.4)
    _sp_w = _scaled_width(support_section_png, 1.4)
    st.markdown(f"**กลางคาน (Midspan) — ช่วงที่ {gsp_i + 1}**")
    if _ms_w:
        st.image(midspan_section_png, width=_ms_w)
    else:
        st.image(midspan_section_png, use_container_width=True)
    st.markdown(f"**จุดรองรับ (Support) — S{gsup_i}**")
    if _sp_w:
        st.image(support_section_png, width=_sp_w)
    else:
        st.image(support_section_png, use_container_width=True)
    st.caption("แสดงรูปตัดตัวแทน 2 ตำแหน่งที่มีปริมาณเหล็กมากที่สุด (หน้าตัด b×h เดียวกันทั้งคาน) — "
               "ปริมาณเหล็กจริงของทุกช่วง/จุดรองรับดูได้จากตารางด้านบน")

    report_html = build_continuous_beam_report_html(
        project, inp, result, elevation_png, sfd_bmd_png,
        midspan_section_png, support_section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("cb", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['beam_name']}")
