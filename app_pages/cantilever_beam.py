"""
Module 3.3 — คานยื่น (Cantilever Beam)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.cantilever_beam import CantileverBeamInput, calculate as calc_cant, MAX_POINT_LOADS
from modules.beam_single_span import (
    PointLoad, BEAM_WIDTH_CM_OPTIONS, BEAM_DEPTH_CM_OPTIONS,
    BAR_DIAMETERS_MM, STIRRUP_DIAMETERS_MM, DEFAULT_STIRRUP_LEGS,
)
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import (
    draw_cantilever_beam_elevation_png, draw_cantilever_beam_sfd_bmd_png, draw_beam_section_png,
)
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_cantilever_beam_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row,
)

inject_card_css()
st.header("3.3 คานยื่น (Cantilever Beam)")


def _scaled_width(png_bytes, factor):
    """คืนความกว้างเป็นพิกเซล = ความกว้างจริงของภาพ × factor (สำหรับปรับขนาดแสดงผล)."""
    try:
        import io as _io
        from PIL import Image as _PILImage
        return max(1, int(_PILImage.open(_io.BytesIO(png_bytes)).width * factor))
    except Exception:
        return None

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "cbm_form_gen" not in st.session_state:
    st.session_state["cbm_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("cantilever_beam")
if _loaded_data is not None:
    st.session_state["cbm_form_gen"] += 1
    st.session_state["_cbm_loaded_data"] = _loaded_data
    st.session_state["_cbm_loaded_code"] = _loaded_code
gen = st.session_state["cbm_form_gen"]
_loaded = st.session_state.get("_cbm_loaded_data") or {}
_loaded_code = st.session_state.get("_cbm_loaded_code")
_loaded_points = _loaded.get("point_loads") or []

# แถวแรก: กล่องเล็กสำหรับรหัสคาน (ชิ้นงาน) ตามรูปแบบเดียวกับหน้า 1.3 พื้นสองทาง
row1_c1, row1_c2 = st.columns([1.0, 3.0])
with row1_c1:
    with st.container(border=True):
        st.markdown("**รหัสคาน (Beam No.)**")
        beam_name = st.text_input("รหัสคาน", value=_loaded_code or "CB-01", key=f"cbm_name_{gen}",
                                   label_visibility="collapsed")

st.write("")

# แถวสอง: 3 การ์ดกรอบสี [เหล็กเสริม (น้ำเงิน)] [ขนาดคาน (เขียว)] [น้ำหนักบรรทุก (ส้ม)]
col1, col2, col3 = st.columns(3)

with col1:
    with input_card("เหล็กเสริม", color="blue", icon="🔩", key="cbm-reinf"):
        st.markdown("**วัสดุ**")
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"cbm_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        main_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กหลัก (บน/ล่าง)", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 2,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"cbm_main_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
        _main_dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                          if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                          else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                     index=_main_dia_idx, key=f"cbm_main_dia_{gen}")

        st.markdown("**เหล็กปลอก (Stirrup)**")
        stirrup_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กปลอก", options=_steel_options,
            index=_steel_options.index(_loaded["stirrup_steel_type"]) if _loaded.get("stirrup_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"cbm_stirrup_steel_{gen}")
        stirrup_bar_dia_options = bar_dia_options_for_steel(stirrup_steel_type, STIRRUP_DIAMETERS_MM)
        _stirrup_dia_idx = (stirrup_bar_dia_options.index(_loaded["stirrup_bar_dia_mm"])
                             if _loaded.get("stirrup_bar_dia_mm") in stirrup_bar_dia_options
                             else min(0, len(stirrup_bar_dia_options) - 1))
        stirrup_bar_dia = st.selectbox("ขนาดเหล็กปลอก (มม.)", options=stirrup_bar_dia_options,
                                        index=_stirrup_dia_idx, key=f"cbm_stirrup_dia_{gen}")
        stirrup_spacing = st.number_input("ระยะห่างเหล็กปลอกที่ใช้จริง (ซม.)", value=_loaded.get("stirrup_spacing_use_cm", 15.0),
                                           step=1.0, key=f"cbm_stirrup_spacing_{gen}")

with col2:
    with input_card("ขนาดคาน & ความยาว", color="green", icon="📐", key="cbm-size"):
        _b_idx = BEAM_WIDTH_CM_OPTIONS.index(_loaded["b_cm"]) if _loaded.get("b_cm") in BEAM_WIDTH_CM_OPTIONS else 1
        b_cm = st.selectbox("ความกว้างคาน b (cm)", options=BEAM_WIDTH_CM_OPTIONS, index=_b_idx, key=f"cbm_b_{gen}")
        _h_idx = BEAM_DEPTH_CM_OPTIONS.index(_loaded["h_cm"]) if _loaded.get("h_cm") in BEAM_DEPTH_CM_OPTIONS else 2
        h_cm = st.selectbox("ความลึกคาน h (cm)", options=BEAM_DEPTH_CM_OPTIONS, index=_h_idx, key=f"cbm_h_{gen}")
        L_m = st.number_input("L คานยื่น (m)", value=_loaded.get("L_m", 1.5), step=0.1,
                               help="ความยาวคานยื่น — จากจุดรองรับ/โคนคาน ถึงปลายอิสระ", key=f"cbm_L_{gen}")

with col3:
    with input_card("น้ำหนักบรรทุก", color="orange", icon="⚖️", key="cbm-load"):
        st.markdown("**น้ำหนักแผ่กระจาย (Line Load)**")
        line_dl = st.number_input("DL (kg/m)", value=_loaded.get("line_load_dl_kg_m", 200.0), step=10.0,
                                   help="ไม่รวมน้ำหนักตัวเองคาน — น้ำหนักตัวเองของคาน (จาก b×h×2400) จะถูกบวกเพิ่มให้"
                                        "อัตโนมัติในการคำนวณ",
                                   key=f"cbm_line_dl_{gen}")
        line_ll = st.number_input("LL (kg/m)", value=_loaded.get("line_load_ll_kg_m", 200.0), step=10.0,
                                   key=f"cbm_line_ll_{gen}")

        st.markdown("**น้ำหนักจุด (Point Loads)**")
        n_points = st.number_input("จำนวนจุด Point Load", min_value=0, max_value=MAX_POINT_LOADS,
                                    value=len(_loaded_points), step=1, key=f"cbm_npoints_{gen}")
        point_loads_input = []
        for i in range(int(n_points)):
            st.markdown(f"จุดที่ {i + 1}")
            _pl_default = _loaded_points[i] if i < len(_loaded_points) else {}
            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                p_dl = st.number_input("P_DL (kg)", value=_pl_default.get("p_dl_kg", 0.0), step=50.0,
                                        key=f"cbm_pl_dl_{gen}_{i}")
            with pc2:
                p_ll = st.number_input("P_LL (kg)", value=_pl_default.get("p_ll_kg", 0.0), step=50.0,
                                        key=f"cbm_pl_ll_{gen}_{i}")
            with pc3:
                p_x = st.number_input("x (m) จากจุดรองรับ", value=_pl_default.get("x_m", 0.0), step=0.1,
                                       key=f"cbm_pl_x_{gen}_{i}")
            point_loads_input.append(PointLoad(p_dl_kg=p_dl, p_ll_kg=p_ll, x_m=p_x))

inp = CantileverBeamInput(
    fc_ksc=fc,
    main_steel_type=main_steel_type,
    stirrup_steel_type=stirrup_steel_type,
    b_cm=b_cm,
    h_cm=h_cm,
    L_m=L_m,
    line_load_dl_kg_m=line_dl,
    line_load_ll_kg_m=line_ll,
    point_loads=point_loads_input,
    main_bar_dia_mm=main_bar_dia,
    stirrup_bar_dia_mm=stirrup_bar_dia,
    stirrup_legs=DEFAULT_STIRRUP_LEGS,
    stirrup_spacing_use_cm=stirrup_spacing,
)

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ (Compute)", key="npk-btn-compute-cb", type="primary", use_container_width=True):
        bad_x = [p for p in point_loads_input if not (0.0 <= p.x_m <= L_m)]
        if bad_x:
            st.error(f"ระยะ x ของน้ำหนักจุดต้องอยู่ระหว่าง 0 ถึง {L_m:.2f} m. (ความยาวคานยื่น) — กรุณาตรวจสอบ")
        else:
            st.session_state["cbm_input"] = inp
            st.session_state["cbm_result"] = calc_cant(inp)
            st.session_state["cbm_project"] = {"beam_name": beam_name}
            mark_calc_pending_sync("cbm")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-cb", use_container_width=True):
        saved_code = save_item("cantilever_beam", beam_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสคาน (Beam No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("cbm_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_cbm", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "cbm_result" in st.session_state:
    inp = st.session_state["cbm_input"]
    result = st.session_state["cbm_result"]
    project = st.session_state["cbm_project"]

    st.header(f"ผลการคำนวณ — {project['beam_name']}")

    metric_card_row([
        ("น้ำหนักบรรทุกใช้งาน Wu", f"{result.wu_kg_m:.0f}", "kgf/m", None),
        ("ปฏิกิริยา R = Vu,max", f"{result.reaction_kg:.0f}", "kgf", None),
        ("โมเมนต์ที่จุดรองรับ Mu", f"{result.end_moment_kgm:+.0f}", "kg-m (hogging)", None),
        ("เหล็กเสริมบน (Top)", f"{result.top.as_provided_cm2:.2f}",
         f"cm² (ต้องการ {result.top.as_req_cm2:.2f})", result.top.reinf_ok),
        ("เหล็กปลอก (Stirrup)", f"{inp.stirrup_spacing_use_cm:.1f}",
         f"cm (Smax={result.stirrup.s_max_cm:.1f})", result.stirrup.stirrup_ok),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**น้ำหนักบรรทุก**")
            st.write(f"น้ำหนักตัวเองคาน = {result.self_weight_kg_m:.0f} kg/m")
            st.write(f"Wu = 1.4(DL+น้ำหนักตัวเอง)+1.7LL = {result.wu_kg_m:.0f} kg/m")
            if inp.point_loads:
                st.write("Point loads (factored): " +
                         ", ".join(f"Pu={pu:.0f}kg@x={x:.2f}m" for x, pu in result.pu_loads))

            st.markdown("**ผลการวิเคราะห์หาแรงที่จุดรองรับ/โคนคาน**")
            st.write(f"R (ปฏิกิริยา) = Vu,max = {result.reaction_kg:.2f} kg.")
            st.write(f"Mu (ที่จุดรองรับ, hogging) = {result.end_moment_kgm:+.2f} kg-m.")

    with dcol2:
        with st.container(border=True):
            st.markdown("**เหล็กเสริมบน (Top Bars — เหล็กรับแรงดึงหลัก)**")
            st.write(f"As ต้องการ = {result.top.as_req_cm2:.2f} cm² "
                     f"({result.top.n_bars_req} เส้น)")
            if result.top.doubly_reinforced:
                st.warning(f"⚠️ ต้องเสริมเหล็กสองชั้น (doubly-reinforced): Mu2={result.top.mu2_kgm:.0f} kg-m., "
                           f"As2={result.top.as_comp_req_cm2:.2f} cm²")
            if result.top.n_layers > 1:
                breakdown = "+".join(str(n) for n in result.top.bars_per_layer if n > 0)
                st.info(f"ℹ️ เหล็กบนเกิน 1 ชั้น จัดเป็น {result.top.n_layers} ชั้นอัตโนมัติตามมาตรฐาน "
                        f"({breakdown} เส้น) — d ที่ใช้ออกแบบจริงคำนวณจาก centroid ของเหล็กทุกชั้นแล้ว")
            if not result.top.reinf_ok:
                st.error(f"⚠️ เหล็กที่ต้องการ ({result.top.n_bars_req} เส้น) เกินกว่าจะใส่ได้แม้จัดหลายชั้นแล้ว "
                         f"(สูงสุด {result.top.max_bars_single_layer * 3} เส้น) — กรุณาขยายความกว้างคานหรือเปลี่ยนขนาดเหล็ก")
            st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_top}** (As={result.top.as_provided_cm2:.2f} cm²)")
            st.write("ผลตรวจสอบ:", "ผ่าน ✅" if result.top.reinf_ok else "ไม่ผ่าน ❌")

            st.markdown("**เหล็กเสริมล่าง (Bottom Bars — เหล็กยึดขั้นต่ำ)**")
            st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_bottom}**")

    with dcol3:
        with st.container(border=True):
            st.markdown("**เหล็กปลอก (Stirrup)**")
            st.write(f"S_max ที่คำนวณได้ = {result.stirrup.s_max_cm:.1f} cm.")
            if result.stirrup.section_too_small:
                st.error("⚠️ หน้าตัดคานเล็กเกินไปสำหรับแรงเฉือนนี้ — กรุณาขยายขนาดคาน")
            st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_stirrup}**")
            st.write("ผลตรวจสอบ:", "ผ่าน ✅" if result.stirrup.stirrup_ok else "ไม่ผ่าน ❌")

    st.subheader("ผังคาน (Beam Layout)")
    elevation_png = draw_cantilever_beam_elevation_png(inp, result)
    st.image(elevation_png, use_container_width=True)

    st.subheader("กราฟแรงเฉือน & โมเมนต์ (SFD/BMD)")
    sfd_bmd_png = draw_cantilever_beam_sfd_bmd_png(result, inp.L_m)
    _sfd_l, _sfd_r = st.columns([4, 1])   # ลดสัดส่วน SFD/BMD ลง 20% (แสดง 80% ของความกว้าง)
    with _sfd_l:
        st.image(sfd_bmd_png, use_container_width=True)

    st.subheader("รูปตัดคาน (ที่จุดรองรับ/โคนคาน)")
    section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, result.bottom.bars_per_layer, result.top.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    _sec_w = _scaled_width(section_png, 1.4)   # ขยายรูปตัดคาน 1.4 เท่า
    if _sec_w:
        st.image(section_png, caption="Beam Section (at support)", width=_sec_w)
    else:
        st.image(section_png, caption="Beam Section (at support)")

    report_html = build_cantilever_beam_report_html(
        project, inp, result, elevation_png, sfd_bmd_png, section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("cbm", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['beam_name']}")
