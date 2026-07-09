"""
Module 1.1 — พื้นวางบนดิน (Slab on Ground)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
Functionality otherwise unchanged.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.slab_on_ground import (
    SlabOnGroundInput, calculate as calc_sg,
    GS_STEEL_FY_KSC, GS_BAR_DIAMETERS_MM, ALLOWED_THICKNESS_CM,
    bar_dia_options_for_steel,
)
from common.diagram import draw_gs_detail_png
from common.report import build_gs_report_html

st.header("1.1 พื้นวางบนดิน (Slab on Ground)")

slab_name = st.text_input("รหัสพื้น (Slab No.)", value="GS1",
                           help="ข้อมูลโครงการ/เจ้าของ/สถานที่/วิศวกร จะย้ายไปอยู่หน้าข้อมูลโครงการกลาง (ใช้ร่วมกันทุกหมวด) ในภายหลัง")

slab_context = st.radio("ลักษณะพื้น", options=["IN", "OUT"],
                         format_func=lambda x: "พื้นภายในอาคาร / มีโครงสร้างคาน (IN)" if x == "IN"
                         else "พื้นภายนอกอาคาร / ไม่มีคาน (OUT)",
                         horizontal=True)

col1, col2, col3 = st.columns(3)

with col1:
    st.subheader("กำลังวัสดุ")
    _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
    fc = st.number_input("กำลังอัดประลัยคอนกรีต f'c (kg/cm²)", value=_default_fc, step=10.0,
                          help="ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้")
    steel_type = st.selectbox(
        "ชนิดเหล็กเสริม", options=list(GS_STEEL_FY_KSC.keys()),
        format_func=lambda k: f"{k} (fy={GS_STEEL_FY_KSC[k]:.0f} ksc)")
    main_bar_dia_options = bar_dia_options_for_steel(steel_type, GS_BAR_DIAMETERS_MM)
    main_bar_dia = st.selectbox("ขนาดเหล็กเสริม (มม.)", options=main_bar_dia_options,
                                 index=min(1, len(main_bar_dia_options) - 1))
    main_bar_spacing = st.number_input("ระยะห่างเหล็กเสริม (ซม.)", value=15.0, step=1.0)

with col2:
    st.subheader("น้ำหนักบรรทุก")
    wD = st.number_input("Superimposed Dead Load, SDL (kg/m²)", value=120.0, step=10.0,
                          help="น้ำหนักวัสดุปูพื้น/ผิวพื้น ไม่รวมน้ำหนักพื้นคอนกรีตเอง (โปรแกรมคำนวณ Dead Load จากความหนาให้อัตโนมัติ)")
    wL = st.number_input("Live Load, LL (kg/m²)", value=200.0, step=10.0,
                          help="ค่าเริ่มต้น 200 กก./ตร.ม. ตามตารางน้ำหนักบรรทุกจร กฎกระทรวง 2566 ประเภทบ้านพักอาศัย")

with col3:
    st.subheader("ขนาดพื้น")
    L = st.number_input("ด้านยาว L (m)", value=5.0, step=0.5, help="ต้อง L >= S")
    S = st.number_input("ด้านสั้น S (m)", value=5.0, step=0.5)
    t = st.selectbox("ความหนาพื้น t (cm)", options=ALLOWED_THICKNESS_CM, index=0,
                      help="จำกัดเฉพาะค่าที่มีในตารางอ้างอิง (10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30 ซม.)")

if st.button("คำนวณ (Compute)", type="primary"):
    inp = SlabOnGroundInput(
        fc_ksc=fc,
        steel_type=steel_type,
        main_bar_dia_mm=main_bar_dia,
        main_bar_spacing_cm=main_bar_spacing,
        wD_kg_m2=wD,
        wL_kg_m2=wL,
        L_m=L,
        S_m=S,
        t_cm=t,
        slab_context=slab_context,
    )
    st.session_state["gs_input"] = inp
    st.session_state["gs_result"] = calc_sg(inp)
    st.session_state["gs_project"] = {
        "slab_name": slab_name,
        # โครงการ/เจ้าของ/สถานที่/วิศวกร: รอหน้าข้อมูลโครงการกลาง (ใช้ร่วมกันทุกหมวด)
        "project_name": "", "owner": "", "location": "", "engineer": "",
    }

if "gs_result" in st.session_state:
    inp = st.session_state["gs_input"]
    result = st.session_state["gs_result"]
    project = st.session_state["gs_project"]

    st.header(f"ผลการคำนวณ — {project['slab_name']}")

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("**น้ำหนักบรรทุก**")
        st.write(f"Dead Load (จากความหนาพื้น) = {result.dead_load_kg_m2:.0f} kg/m²")
        st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {result.wu_kg_m2:.0f} kg/m²")

        st.markdown("**ตรวจสอบขนาดพื้น**")
        st.write("L >= S:", "OK" if result.L_ge_S_ok else "ไม่ผ่าน — L ต้อง >= S")
        if result.dimension_limits:
            lim = result.dimension_limits
            st.write(f"ช่วงที่ยอมรับสำหรับ t={inp.t_cm} ซม.: {lim['min_m']} - {lim['max_m']} m")
            st.write("L อยู่ในช่วง:", "OK" if result.L_within_range else "ไม่ผ่าน")
            st.write("S อยู่ในช่วง:", "OK" if result.S_within_range else "ไม่ผ่าน")

    with r2:
        st.markdown("**เหล็กเสริม (ต้องผ่านทั้ง 3 ข้อ)**")
        st.write(f"1) Temperature Steel = {result.as_temperature_cm2_m:.2f} cm²/m —",
                  "OK" if result.temperature_ok else "ไม่ผ่าน")
        st.write(f"2) Subgrade Drag = {result.as_subgrade_drag_cm2_m:.2f} cm²/m —",
                  "OK" if result.subgrade_drag_ok else "ไม่ผ่าน")
        st.write(f"3) PCA (พื้นที่มีรถวิ่งผ่าน) = {result.as_pca_cm2_m:.2f} cm²/m —",
                  "OK" if result.pca_ok else "ไม่ผ่าน")
        st.write(f"เหล็กที่ใช้จริง = {result.as_provided_cm2_m:.2f} cm²/m")
        if result.all_reinf_ok:
            st.success(f"ผ่านทั้งหมด: {result.reinf_label}")
        else:
            st.error("ไม่ผ่านอย่างน้อย 1 ข้อ — เพิ่มขนาดเหล็กหรือลดระยะห่าง")

    st.subheader("รูปขยายรายละเอียดการเสริมเหล็ก")
    diagram_png = draw_gs_detail_png(inp.t_cm, inp.main_bar_dia_mm, inp.main_bar_spacing_cm)
    st.image(diagram_png, caption="Ground Slab — Joint & Reinforcement Detail")

    st.subheader("รายการคำนวณ")
    report_html = build_gs_report_html(
        project, inp, result, diagram_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    components.html(report_html, height=650, scrolling=True)

    st.download_button(
        "⬇️ ดาวน์โหลดรายการคำนวณ (เปิดแล้วกดพิมพ์ได้)",
        data=report_html,
        file_name=f"รายการคำนวณ_{project['slab_name']}.html",
        mime="text/html",
    )
