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
from common.report import build_continuous_beam_report_html

st.header("3.2 คานต่อเนื่อง (Continuous Beam)")

beam_name = st.text_input("รหัสคาน (Beam No.)", value="CB-01")

colM, colB = st.columns(2)
with colM:
    st.subheader("วัสดุ")
    _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
    fc = st.number_input("กำลังอัดประลัยคอนกรีต f'c (kg/cm²)", value=_default_fc, step=10.0,
                          help="ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้")

    def _bar_type_label(k):
        return "DB (เหล็กข้ออ้อย)" if k == "DB" else "RB (เหล็กเส้นกลม)"

    main_steel_type = st.selectbox(
        "ชั้นคุณภาพเหล็กหลัก (บน/ล่าง)", options=list(GS_STEEL_FY_KSC.keys()), index=2,
        format_func=lambda k: f"{k} (fy={GS_STEEL_FY_KSC[k]:.0f} ksc) — {_bar_type_label(GS_STEEL_BAR_TYPE[k])}",
        key="cb_main_steel")
    main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
    main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                 index=min(1, len(main_bar_dia_options) - 1), key="cb_main_dia")

    stirrup_steel_type = st.selectbox(
        "ชั้นคุณภาพเหล็กปลอก", options=list(GS_STEEL_FY_KSC.keys()), index=0,
        format_func=lambda k: f"{k} (fy={GS_STEEL_FY_KSC[k]:.0f} ksc) — {_bar_type_label(GS_STEEL_BAR_TYPE[k])}",
        key="cb_stirrup_steel")
    stirrup_bar_dia_options = bar_dia_options_for_steel(stirrup_steel_type, STIRRUP_DIAMETERS_MM)
    stirrup_bar_dia = st.selectbox("ขนาดเหล็กปลอก (มม.)", options=stirrup_bar_dia_options,
                                    index=min(0, len(stirrup_bar_dia_options) - 1), key="cb_stirrup_dia")
    stirrup_spacing = st.number_input("ระยะห่างเหล็กปลอกที่ใช้จริง (ซม.) — ค่าเดียวทั้งคาน", value=15.0, step=1.0,
                                       key="cb_stirrup_spacing")

with colB:
    st.subheader("ขนาดคาน (หน้าตัดเดียวทั้งคาน)")
    b_cm = st.selectbox("ความกว้างคาน b (cm)", options=BEAM_WIDTH_CM_OPTIONS, index=1, key="cb_b")
    h_cm = st.selectbox("ความลึกคาน h (cm)", options=BEAM_DEPTH_CM_OPTIONS, index=2, key="cb_h")
    n_spans = st.number_input(f"จำนวนช่วงคาน ({MIN_SPANS}-{MAX_SPANS} ช่วง)",
                               min_value=MIN_SPANS, max_value=MAX_SPANS, value=3, step=1, key="cb_nspans")

st.subheader("ช่วงคานแต่ละช่วง (Spans)")
span_inputs = []
for i in range(int(n_spans)):
    with st.expander(f"ช่วงที่ {i + 1}", expanded=(i < 2)):
        sc1, sc2, sc3 = st.columns(3)
        with sc1:
            L = st.number_input("ความยาวช่วง L (m.)", value=4.0, step=0.1, min_value=0.1, key=f"cb_span_L_{i}")
        with sc2:
            dl = st.number_input("Line Load DL (kg/m) — ไม่รวมน้ำหนักตัวเองคาน", value=200.0, step=10.0, key=f"cb_span_dl_{i}")
        with sc3:
            ll = st.number_input("Line Load LL (kg/m)", value=300.0, step=10.0, key=f"cb_span_ll_{i}")
        n_pts = st.number_input(f"จำนวนจุด Point Load (สูงสุด {MAX_POINT_LOADS_PER_SPAN})", min_value=0,
                                 max_value=MAX_POINT_LOADS_PER_SPAN, value=0, step=1, key=f"cb_span_npts_{i}")
        pts = []
        for j in range(int(n_pts)):
            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                p_dl = st.number_input("P_DL (kg)", value=0.0, step=50.0, key=f"cb_span_{i}_pl_dl_{j}")
            with pc2:
                p_ll = st.number_input("P_LL (kg)", value=0.0, step=50.0, key=f"cb_span_{i}_pl_ll_{j}")
            with pc3:
                p_x = st.number_input("ระยะ x จากปลายซ้ายช่วงนี้ (m.)", value=0.0, step=0.1, key=f"cb_span_{i}_pl_x_{j}")
            pts.append(PointLoad(p_dl_kg=p_dl, p_ll_kg=p_ll, x_m=p_x))
        span_inputs.append(SpanInput(length_m=L, line_load_dl_kg_m=dl, line_load_ll_kg_m=ll, point_loads=pts))

st.subheader("ปลายยื่น (Overhang) — ถ้ามี")
oc1, oc2 = st.columns(2)
with oc1:
    use_left_ov = st.checkbox("มีปลายยื่นด้านซ้าย (Left Overhang)", value=False, key="cb_use_left_ov")
    left_ov_input = None
    if use_left_ov:
        L0 = st.number_input("ความยาวปลายยื่นซ้าย (m.)", value=1.0, step=0.1, min_value=0.05, key="cb_left_ov_L")
        dl0 = st.number_input("Line Load DL (kg/m)", value=200.0, step=10.0, key="cb_left_ov_dl")
        ll0 = st.number_input("Line Load LL (kg/m)", value=300.0, step=10.0, key="cb_left_ov_ll")
        n_pts0 = st.number_input(f"จำนวนจุด Point Load (สูงสุด {MAX_POINT_LOADS_PER_SPAN})", min_value=0,
                                  max_value=MAX_POINT_LOADS_PER_SPAN, value=0, step=1, key="cb_left_ov_npts")
        pts0 = []
        for j in range(int(n_pts0)):
            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                p_dl = st.number_input("P_DL (kg)", value=0.0, step=50.0, key=f"cb_left_ov_pl_dl_{j}")
            with pc2:
                p_ll = st.number_input("P_LL (kg)", value=0.0, step=50.0, key=f"cb_left_ov_pl_ll_{j}")
            with pc3:
                p_x = st.number_input("ระยะ x จากจุดรองรับ (m.)", value=0.0, step=0.1, key=f"cb_left_ov_pl_x_{j}")
            pts0.append(PointLoad(p_dl_kg=p_dl, p_ll_kg=p_ll, x_m=p_x))
        left_ov_input = OverhangInput(length_m=L0, line_load_dl_kg_m=dl0, line_load_ll_kg_m=ll0, point_loads=pts0)

with oc2:
    use_right_ov = st.checkbox("มีปลายยื่นด้านขวา (Right Overhang)", value=False, key="cb_use_right_ov")
    right_ov_input = None
    if use_right_ov:
        L1 = st.number_input("ความยาวปลายยื่นขวา (m.)", value=1.0, step=0.1, min_value=0.05, key="cb_right_ov_L")
        dl1 = st.number_input("Line Load DL (kg/m)", value=200.0, step=10.0, key="cb_right_ov_dl")
        ll1 = st.number_input("Line Load LL (kg/m)", value=300.0, step=10.0, key="cb_right_ov_ll")
        n_pts1 = st.number_input(f"จำนวนจุด Point Load (สูงสุด {MAX_POINT_LOADS_PER_SPAN})", min_value=0,
                                  max_value=MAX_POINT_LOADS_PER_SPAN, value=0, step=1, key="cb_right_ov_npts")
        pts1 = []
        for j in range(int(n_pts1)):
            pc1, pc2, pc3 = st.columns(3)
            with pc1:
                p_dl = st.number_input("P_DL (kg)", value=0.0, step=50.0, key=f"cb_right_ov_pl_dl_{j}")
            with pc2:
                p_ll = st.number_input("P_LL (kg)", value=0.0, step=50.0, key=f"cb_right_ov_pl_ll_{j}")
            with pc3:
                p_x = st.number_input("ระยะ x จากจุดรองรับ (m.)", value=0.0, step=0.1, key=f"cb_right_ov_pl_x_{j}")
            pts1.append(PointLoad(p_dl_kg=p_dl, p_ll_kg=p_ll, x_m=p_x))
        right_ov_input = OverhangInput(length_m=L1, line_load_dl_kg_m=dl1, line_load_ll_kg_m=ll1, point_loads=pts1)

if st.button("คำนวณ (Compute)", type="primary"):
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
        inp = ContinuousBeamInput(
            fc_ksc=fc, main_steel_type=main_steel_type, stirrup_steel_type=stirrup_steel_type,
            b_cm=b_cm, h_cm=h_cm, spans=span_inputs,
            left_overhang=left_ov_input, right_overhang=right_ov_input,
            main_bar_dia_mm=main_bar_dia, stirrup_bar_dia_mm=stirrup_bar_dia,
            stirrup_legs=DEFAULT_STIRRUP_LEGS, stirrup_spacing_use_cm=stirrup_spacing,
        )
        st.session_state["cbeam_input"] = inp
        st.session_state["cbeam_result"] = calc_cbeam(inp)
        st.session_state["cbeam_project"] = {"beam_name": beam_name}

if "cbeam_result" in st.session_state:
    inp = st.session_state["cbeam_input"]
    result = st.session_state["cbeam_result"]
    project = st.session_state["cbeam_project"]

    st.header(f"ผลการคำนวณ — {project['beam_name']}")

    st.subheader("ผังคาน (Beam Layout)")
    elevation_png = draw_continuous_beam_elevation_png(result)
    st.image(elevation_png, use_container_width=True)

    st.subheader("โมเมนต์ & แรงปฏิกิริยาที่จุดรองรับ")
    for s in result.supports:
        suffix = " (มีปลายยื่น)" if (s.is_exterior and s.has_overhang) else (" (ริม)" if s.is_exterior else "")
        st.write(f"S{s.index}{suffix}: M = {s.moment_kgm:+.2f} kg-m., R = {s.reaction_kg:.2f} kg.")

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
    st.image(sfd_bmd_png, use_container_width=True)

    st.subheader("รูปตัดรายละเอียดการเสริมเหล็ก (Reinforcement Detail Sections)")
    gsp_i = result.governing_span_index
    gsup_i = result.governing_support_index
    gsp = result.spans[gsp_i]
    gsup = result.supports[gsup_i]
    midspan_section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, gsp.bottom.bars_per_layer, result.nominal_bars.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    support_section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, result.nominal_bars.bars_per_layer, gsup.top.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    sec1, sec2 = st.columns(2)
    with sec1:
        st.markdown(f"**กลางคาน (Midspan) — ช่วงที่ {gsp_i + 1}**")
        st.image(midspan_section_png, use_container_width=True)
    with sec2:
        st.markdown(f"**จุดรองรับ (Support) — S{gsup_i}**")
        st.image(support_section_png, use_container_width=True)
    st.caption("แสดงรูปตัดตัวแทน 2 ตำแหน่งที่มีปริมาณเหล็กมากที่สุด (หน้าตัด b×h เดียวกันทั้งคาน) — "
               "ปริมาณเหล็กจริงของทุกช่วง/จุดรองรับดูได้จากตารางด้านบน")

    st.subheader("รายการคำนวณ")
    report_html = build_continuous_beam_report_html(
        project, inp, result, elevation_png, sfd_bmd_png,
        midspan_section_png, support_section_png,
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
