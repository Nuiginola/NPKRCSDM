"""
Module 1.4 — พื้นยื่น (Cantilever Slab)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.cantilever_slab import (
    CantileverSlabInput, calculate as calc_cant,
    ALLOWED_THICKNESS_CM, BAR_DIAMETERS_MM,
)
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import draw_cant_section_png, draw_cant_plan_png
from common.report import build_cant_report_html

st.header("1.4 พื้นยื่น (Cantilever Slab)")

slab_name = st.text_input("รหัสพื้น (Slab No.)", value="S-04")

col1, col2, col3 = st.columns(3)


def _bar_type_label(k):
    return "DB (เหล็กข้ออ้อย)" if k == "DB" else "RB (เหล็กเส้นกลม)"


with col1:
    st.subheader("เหล็กเสริมหลัก (แนวยื่น — รับโมเมนต์ลบ)")
    _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
    fc = st.number_input("กำลังอัดประลัยคอนกรีต f'c (kg/cm²)", value=_default_fc, step=10.0,
                          help="ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้")
    main_steel_type = st.selectbox(
        "ชั้นคุณภาพเหล็กหลัก", options=list(GS_STEEL_FY_KSC.keys()), index=0,
        format_func=lambda k: f"{k} (fy={GS_STEEL_FY_KSC[k]:.0f} ksc) — {_bar_type_label(GS_STEEL_BAR_TYPE[k])}",
        help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)")
    main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
    main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                 index=min(1, len(main_bar_dia_options) - 1))
    main_bar_spacing = st.number_input("ระยะห่างเหล็กหลัก (ซม.)", value=15.0, step=1.0)

    st.subheader("เหล็กเสริมรอง (ขนานแนวจุดรองรับ)")
    temp_steel_type = st.selectbox(
        "ชั้นคุณภาพเหล็กเสริมรอง", options=list(GS_STEEL_FY_KSC.keys()), index=0,
        format_func=lambda k: f"{k} (fy={GS_STEEL_FY_KSC[k]:.0f} ksc) — {_bar_type_label(GS_STEEL_BAR_TYPE[k])}",
        help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)")
    temp_bar_dia_options = bar_dia_options_for_steel(temp_steel_type, BAR_DIAMETERS_MM)
    temp_bar_dia = st.selectbox("ขนาดเหล็กเสริมรอง (มม.)", options=temp_bar_dia_options,
                                 index=min(1, len(temp_bar_dia_options) - 1))
    temp_bar_spacing = st.number_input("ระยะห่างเหล็กเสริมรอง (ซม.)", value=15.0, step=1.0)

with col2:
    st.subheader("น้ำหนักบรรทุก")
    wD = st.number_input("Superimposed Dead Load, SDL (kg/m²)", value=120.0, step=10.0)
    wL = st.number_input("Live Load, LL (kg/m²)", value=200.0, step=10.0,
                          help="ค่าเริ่มต้น 200 กก./ตร.ม. ตามตารางน้ำหนักบรรทุกจร กฎกระทรวง 2566 ประเภทบ้านพักอาศัย")
    fin_wg = st.number_input("น้ำหนักแนวกันตก/ผนังเตี้ยที่ปลายยื่น, Fin Wg. (kg/m)", value=0.0, step=10.0,
                              help="น้ำหนักเชิงเส้นที่ขอบอิสระของพื้นยื่น เช่น ราวกันตก/ผนังเตี้ยระเบียง — "
                                   "ใส่ 0 ถ้าไม่มี")

with col3:
    st.subheader("ขนาดพื้น")
    S = st.number_input("ความยาวยื่น S (m)", value=1.2, step=0.1)
    t = st.selectbox("ความหนาพื้น t (cm)", options=ALLOWED_THICKNESS_CM, index=1)

if st.button("คำนวณ (Compute)", type="primary"):
    inp = CantileverSlabInput(
        fc_ksc=fc,
        main_steel_type=main_steel_type,
        temp_steel_type=temp_steel_type,
        main_bar_dia_mm=main_bar_dia,
        main_bar_spacing_cm=main_bar_spacing,
        temp_bar_dia_mm=temp_bar_dia,
        temp_bar_spacing_cm=temp_bar_spacing,
        wD_kg_m2=wD,
        wL_kg_m2=wL,
        fin_wg_kg_m=fin_wg,
        S_m=S,
        t_cm=t,
    )
    st.session_state["cant_input"] = inp
    st.session_state["cant_result"] = calc_cant(inp)
    st.session_state["cant_project"] = {"slab_name": slab_name}

if "cant_result" in st.session_state:
    inp = st.session_state["cant_input"]
    result = st.session_state["cant_result"]
    project = st.session_state["cant_project"]

    st.header(f"ผลการคำนวณ — {project['slab_name']}")

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("**น้ำหนักบรรทุก**")
        st.write(f"Dead Load (จากความหนาพื้น) = {result.dead_load_kg_m2:.0f} kg/m²")
        st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {result.wu_kg_m2:.0f} kg/m²")
        st.write(f"FIN = 1.4(Fin Wg.) = {result.fin_kg_m:.0f} kg/m.")

        st.markdown("**ตรวจสอบความหนา**")
        st.write(f"tmin = {result.tmin_cm:.2f} cm. (t ที่ใช้ = {inp.t_cm:.1f} cm.):",
                  "OK" if result.t_ok else "ไม่ผ่าน — เพิ่มความหนา")

    with r2:
        st.markdown("**โมเมนต์และเหล็กเสริมหลัก (ที่จุดรองรับ)**")
        warn = "  ⚠️ หน้าตัดเล็กไป (เกิน ρmax)" if result.over_reinforced else ""
        st.write(f"Mu = {result.mu_kgm:.0f} kg-m/m, As ต้องการ (จากโมเมนต์) = "
                 f"{result.as_req_flexure_cm2_m:.2f} cm²/m{warn}")
        st.write(f"As ต้องการสูงสุด (รวม Ast ขั้นต่ำ 0.002bt={result.ast_min_main_cm2_m:.2f}) = "
                 f"{result.as_req_governing_cm2_m:.2f} cm²/m")
        st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_main}** "
                 f"(As={result.as_provided_cm2_m:.2f} cm²/m, ระยะห่างสูงสุดที่ยอมให้={result.main_spacing_max_cm:.1f} cm.)")
        st.write("ผลตรวจสอบเหล็กหลัก:", "ผ่าน ✅" if result.main_reinf_ok else "ไม่ผ่าน ❌")

    r3, r4 = st.columns(2)
    with r3:
        st.markdown("**เหล็กเสริมรอง — กระจายแรง/กันร้าว**")
        st.write(f"Ast ต้องการ = {result.ast_req_cm2_m:.2f} cm²/m")
        st.write(f"เหล็กที่ใช้จริง: {result.reinf_label_temp} (Ast={result.ast_provided_cm2_m:.2f} cm²/m, "
                 f"ระยะห่างสูงสุด={result.temp_spacing_max_cm:.1f} cm.)")
        st.write("ผลตรวจสอบเหล็กเสริมรอง:", "ผ่าน ✅" if result.temp_reinf_ok else "ไม่ผ่าน ❌")

    with r4:
        st.markdown("**แรงเฉือน & ถ่ายน้ำหนักลงคาน/ผนัง**")
        st.write(f"Vu = {result.vu_kg:.0f} kg., &phi;Vc = {result.phi_vc_kg:.0f} kg.:",
                  "OK" if result.shear_ok else "ไม่ผ่าน")
        st.write(f"น้ำหนักลงคาน/ผนัง (Service): DL={result.dl_on_beam_kg_m:.0f} kg/m., "
                 f"LL={result.ll_on_beam_kg_m:.0f} kg/m.")

    st.subheader("รูปขยายรายละเอียดการเสริมเหล็ก")
    section_png = draw_cant_section_png(
        inp.S_m, inp.t_cm,
        inp.main_bar_dia_mm, inp.main_bar_spacing_cm, result.main_bar_type,
        inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm, result.temp_bar_type)
    plan_png = draw_cant_plan_png(
        inp.S_m,
        inp.main_bar_dia_mm, inp.main_bar_spacing_cm, result.main_bar_type,
        inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm, result.temp_bar_type)

    dc1, dc2 = st.columns([3, 2])
    with dc1:
        st.image(section_png, caption="รูปตัด (Cross-section)")
    with dc2:
        st.image(plan_png, caption="แปลนเหล็กเสริม (Plan)")

    st.subheader("รายการคำนวณ")
    report_html = build_cant_report_html(
        project, inp, result, section_png, plan_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    components.html(report_html, height=700, scrolling=True)

    st.download_button(
        "⬇️ ดาวน์โหลดรายการคำนวณ (เปิดแล้วกดพิมพ์ได้)",
        data=report_html,
        file_name=f"รายการคำนวณ_{project['slab_name']}.html",
        mime="text/html",
    )
