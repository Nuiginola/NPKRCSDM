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
from common.report import build_cantilever_beam_report_html

st.header("3.3 คานยื่น (Cantilever Beam)")

beam_name = st.text_input("รหัสคาน (Beam No.)", value="CB-01")

col1, col2, col3 = st.columns(3)


def _bar_type_label(k):
    return "DB (เหล็กข้ออ้อย)" if k == "DB" else "RB (เหล็กเส้นกลม)"


with col1:
    st.subheader("วัสดุ")
    _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
    fc = st.number_input("กำลังอัดประลัยคอนกรีต f'c (kg/cm²)", value=_default_fc, step=10.0,
                          help="ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้")
    main_steel_type = st.selectbox(
        "ชั้นคุณภาพเหล็กหลัก (บน/ล่าง)", options=list(GS_STEEL_FY_KSC.keys()), index=2,
        format_func=lambda k: f"{k} (fy={GS_STEEL_FY_KSC[k]:.0f} ksc) — {_bar_type_label(GS_STEEL_BAR_TYPE[k])}",
        help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)")
    main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
    main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                 index=min(1, len(main_bar_dia_options) - 1))

    st.subheader("เหล็กปลอก (Stirrup)")
    stirrup_steel_type = st.selectbox(
        "ชั้นคุณภาพเหล็กปลอก", options=list(GS_STEEL_FY_KSC.keys()), index=0,
        format_func=lambda k: f"{k} (fy={GS_STEEL_FY_KSC[k]:.0f} ksc) — {_bar_type_label(GS_STEEL_BAR_TYPE[k])}",
        help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)")
    stirrup_bar_dia_options = bar_dia_options_for_steel(stirrup_steel_type, STIRRUP_DIAMETERS_MM)
    stirrup_bar_dia = st.selectbox("ขนาดเหล็กปลอก (มม.)", options=stirrup_bar_dia_options,
                                    index=min(0, len(stirrup_bar_dia_options) - 1))
    stirrup_spacing = st.number_input("ระยะห่างเหล็กปลอกที่ใช้จริง (ซม.)", value=15.0, step=1.0)

with col2:
    st.subheader("ขนาดคาน & ความยาวคานยื่น")
    b_cm = st.selectbox("ความกว้างคาน b (cm)", options=BEAM_WIDTH_CM_OPTIONS, index=1)
    h_cm = st.selectbox("ความลึกคาน h (cm)", options=BEAM_DEPTH_CM_OPTIONS, index=2)
    L_m = st.number_input("ความยาวคานยื่น L (m) — จากจุดรองรับ/โคนคาน ถึงปลายอิสระ", value=1.5, step=0.1)

    st.subheader("น้ำหนักแผ่กระจาย (Line Load)")
    line_dl = st.number_input("Line Load, DL (kg/m) — ไม่รวมน้ำหนักตัวเองคาน", value=200.0, step=10.0,
                               help="น้ำหนักตัวเองของคาน (จาก b×h×2400) จะถูกบวกเพิ่มให้อัตโนมัติในการคำนวณ")
    line_ll = st.number_input("Line Load, LL (kg/m)", value=200.0, step=10.0)

with col3:
    st.subheader("น้ำหนักจุด (Point Loads)")
    n_points = st.number_input("จำนวนจุด Point Load", min_value=0, max_value=MAX_POINT_LOADS, value=0, step=1)
    point_loads_input = []
    for i in range(int(n_points)):
        st.markdown(f"**จุดที่ {i + 1}**")
        pc1, pc2, pc3 = st.columns(3)
        with pc1:
            p_dl = st.number_input(f"P_DL (kg)", value=0.0, step=50.0, key=f"cant_pl_dl_{i}")
        with pc2:
            p_ll = st.number_input(f"P_LL (kg)", value=0.0, step=50.0, key=f"cant_pl_ll_{i}")
        with pc3:
            p_x = st.number_input(f"ระยะ x (m) จากจุดรองรับ", value=0.0, step=0.1, key=f"cant_pl_x_{i}")
        point_loads_input.append(PointLoad(p_dl_kg=p_dl, p_ll_kg=p_ll, x_m=p_x))

if st.button("คำนวณ (Compute)", type="primary"):
    bad_x = [p for p in point_loads_input if not (0.0 <= p.x_m <= L_m)]
    if bad_x:
        st.error(f"ระยะ x ของน้ำหนักจุดต้องอยู่ระหว่าง 0 ถึง {L_m:.2f} m. (ความยาวคานยื่น) — กรุณาตรวจสอบ")
    else:
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
        st.session_state["cant_input"] = inp
        st.session_state["cant_result"] = calc_cant(inp)
        st.session_state["cant_project"] = {"beam_name": beam_name}

if "cant_result" in st.session_state:
    inp = st.session_state["cant_input"]
    result = st.session_state["cant_result"]
    project = st.session_state["cant_project"]

    st.header(f"ผลการคำนวณ — {project['beam_name']}")

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("**น้ำหนักบรรทุก**")
        st.write(f"น้ำหนักตัวเองคาน = {result.self_weight_kg_m:.0f} kg/m")
        st.write(f"Wu = 1.4(DL+น้ำหนักตัวเอง)+1.7LL = {result.wu_kg_m:.0f} kg/m")
        if inp.point_loads:
            st.write(f"Point loads (factored): " +
                     ", ".join(f"Pu={pu:.0f}kg@x={x:.2f}m" for x, pu in result.pu_loads))

        st.markdown("**ผลการวิเคราะห์หาแรงที่จุดรองรับ/โคนคาน**")
        st.write(f"R (ปฏิกิริยา) = Vu,max = {result.reaction_kg:.2f} kg.")
        st.write(f"Mu (ที่จุดรองรับ, hogging) = {result.end_moment_kgm:+.2f} kg-m.")

    with r2:
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
    st.image(sfd_bmd_png, use_container_width=True)

    st.subheader("รูปตัดคาน (ที่จุดรองรับ/โคนคาน)")
    section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, result.bottom.bars_per_layer, result.top.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    st.image(section_png, caption="Beam Section (at support)")

    st.subheader("รายการคำนวณ")
    report_html = build_cantilever_beam_report_html(
        project, inp, result, elevation_png, sfd_bmd_png, section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    components.html(report_html, height=700, scrolling=True)

    st.download_button(
        "⬇️ ดาวน์โหลดรายการคำนวณ (เปิดแล้วกดพิมพ์ได้)",
        data=report_html,
        file_name=f"รายการคำนวณ_{project['beam_name']}.html",
        mime="text/html",
    )
