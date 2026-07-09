"""
Module 1.2 — พื้นทางเดียว (One-way Slab)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.one_way_slab import (
    OneWaySlabInput, calculate as calc_ow,
    CONTINUITY_CASES, ALLOWED_THICKNESS_CM,
    BAR_DIAMETERS_MM,
)
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import draw_ow_section_png, draw_ow_plan_png
from common.report import build_ow_report_html

st.header("1.2 พื้นทางเดียว (One-way Slab)")

slab_name = st.text_input("รหัสพื้น (Slab No.)", value="S-01")

# --- ตัวเลือกความต่อเนื่องของพื้น: ปุ่มเรียงกัน 1/2/3 แทน dropdown (ดูง่ายกว่า) ---
CASE_KEYS = list(CONTINUITY_CASES.keys())          # ["SS", "ONE", "BOTH"]
CASE_SHORT_TH = {
    "SS": "ไม่ต่อเนื่อง",
    "ONE": "ต่อเนื่องด้านเดียว",
    "BOTH": "ต่อเนื่อง 2 ด้าน",
}

if "ow_case_key" not in st.session_state:
    st.session_state["ow_case_key"] = "BOTH"

with st.container(border=True):
    st.markdown("**ความต่อเนื่องของพื้น (Slab Continuity Cases)**")
    case_btn_cols = st.columns(len(CASE_KEYS))
    for i, k in enumerate(CASE_KEYS):
        with case_btn_cols[i]:
            is_selected = st.session_state["ow_case_key"] == k
            if st.button(str(i + 1), key=f"ow_case_btn_{k}",
                         type="primary" if is_selected else "secondary",
                         use_container_width=True):
                if not is_selected:
                    st.session_state["ow_case_key"] = k
                    st.rerun()
            st.markdown(f"<div style='text-align:center; font-weight:bold;'>{CASE_SHORT_TH[k]}</div>",
                        unsafe_allow_html=True)

    case_key = st.session_state["ow_case_key"]
    st.text_input("กรณีที่เลือก (Case)",
                  value=f"{CASE_KEYS.index(case_key) + 1} — {CONTINUITY_CASES[case_key]['label_th']}",
                  disabled=True)

col1, col2, col3 = st.columns(3)

def _bar_type_label(k):
    return "DB (เหล็กข้ออ้อย)" if k == "DB" else "RB (เหล็กเส้นกลม)"

with col1:
    st.subheader("เหล็กเสริมหลัก (แนว S — รับโมเมนต์)")
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

    st.subheader("เหล็กเสริมรอง (แนว L — กระจายแรง/กันร้าว)")
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

with col3:
    st.subheader("ขนาดพื้น")
    S = st.number_input("ช่วงพาด S — ทิศทางเสริมเหล็กหลัก (m)", value=1.5, step=0.5)
    L = st.number_input("ด้านยาว L — ทิศตั้งฉาก (m)", value=4.0, step=0.5,
                         help="ต้อง S/L <= 0.5 จึงจะถือเป็นพื้นทางเดียว")
    t = st.selectbox("ความหนาพื้น t (cm)", options=ALLOWED_THICKNESS_CM, index=1)

if st.button("คำนวณ (Compute)", type="primary"):
    inp = OneWaySlabInput(
        fc_ksc=fc,
        main_steel_type=main_steel_type,
        temp_steel_type=temp_steel_type,
        main_bar_dia_mm=main_bar_dia,
        main_bar_spacing_cm=main_bar_spacing,
        temp_bar_dia_mm=temp_bar_dia,
        temp_bar_spacing_cm=temp_bar_spacing,
        wD_kg_m2=wD,
        wL_kg_m2=wL,
        S_m=S,
        L_m=L,
        t_cm=t,
        continuity_case=case_key,
    )
    st.session_state["ow_input"] = inp
    st.session_state["ow_result"] = calc_ow(inp)
    st.session_state["ow_project"] = {"slab_name": slab_name}

if "ow_result" in st.session_state:
    inp = st.session_state["ow_input"]
    result = st.session_state["ow_result"]
    project = st.session_state["ow_project"]
    case = CONTINUITY_CASES[inp.continuity_case]

    st.header(f"ผลการคำนวณ — {project['slab_name']}")

    if not result.one_way_ok:
        st.warning(f"⚠️ m = S/L = {result.m_ratio:.3f} > 0.5 — พฤติกรรมของพื้นแผ่นนี้เป็นแบบ **สองทาง (Two-way)** "
                   "ไม่ใช่ทางเดียวแล้ว ผลการคำนวณด้านล่างจึงไม่ถูกต้องตามพฤติกรรมจริง แนะนำให้ใช้โมดูล "
                   "1.3 พื้นสองทาง (Two-way Slab) ในการออกแบบแทน")
        try:
            st.page_link("app_pages/two_way_slab.py",
                         label="ไปที่โมดูล 1.3 พื้นสองทาง (Two-way Slab)", icon="↪️")
        except Exception:
            st.caption("(โมดูล 1.3 พื้นสองทาง ยังไม่เปิดใช้งานในขณะนี้ — ลิงก์จะใช้งานได้ทันทีที่สร้างโมดูลนี้เสร็จ)")

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("**น้ำหนักบรรทุก**")
        st.write(f"Dead Load (จากความหนาพื้น) = {result.dead_load_kg_m2:.0f} kg/m²")
        st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {result.wu_kg_m2:.0f} kg/m²")

        st.markdown("**ตรวจสอบขนาด/ความหนา**")
        st.write(f"m = S/L = {result.m_ratio:.3f} (ต้อง <= 0.5):",
                 "OK" if result.one_way_ok else "ไม่ผ่าน — พฤติกรรมเป็นพื้นสองทาง")
        st.write(f"tmin = {result.tmin_cm:.2f} cm. (t ที่ใช้ = {inp.t_cm:.1f} cm.):",
                  "OK" if result.t_ok else "ไม่ผ่าน — เพิ่มความหนา")

    with r2:
        st.markdown("**โมเมนต์และเหล็กเสริมหลัก (แนว S) ตามตำแหน่ง**")
        for p in result.positions:
            if not p.active:
                st.write(f"- {p.label_th}: ไม่มีการออกแบบ (ปลายไม่ต่อเนื่อง)")
            else:
                warn = "  ⚠️ หน้าตัดเล็กไป (เกิน ρmax)" if p.over_reinforced else ""
                st.write(f"- {p.label_th}: Mu={p.mu_kgm:.0f} kg-m/m, As ต้องการ={p.as_req_cm2_m:.2f} cm²/m{warn}")
        st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_main}** "
                 f"(As={result.as_provided_cm2_m:.2f} cm²/m, ระยะห่างสูงสุดที่ยอมให้={result.main_spacing_max_cm:.1f} cm.)")
        st.write("ผลตรวจสอบเหล็กหลัก:", "ผ่าน ✅" if result.main_reinf_ok else "ไม่ผ่าน ❌")

    r3, r4 = st.columns(2)
    with r3:
        st.markdown("**เหล็กเสริมรอง — กระจายแรง/กันร้าว (แนว L)**")
        st.write(f"Ast ต้องการ = {result.ast_req_cm2_m:.2f} cm²/m")
        st.write(f"เหล็กที่ใช้จริง: {result.reinf_label_temp} (Ast={result.ast_provided_cm2_m:.2f} cm²/m, "
                 f"ระยะห่างสูงสุด={result.temp_spacing_max_cm:.1f} cm.)")
        st.write("ผลตรวจสอบเหล็กเสริมรอง:", "ผ่าน ✅" if result.temp_reinf_ok else "ไม่ผ่าน ❌")

    with r4:
        st.markdown("**แรงเฉือน & ถ่ายน้ำหนักลงคาน**")
        st.write(f"Vu = {result.vu_kg:.0f} kg., &phi;Vc = {result.phi_vc_kg:.0f} kg.:",
                  "OK" if result.shear_ok else "ไม่ผ่าน")
        st.write(f"น้ำหนักลงคาน (Service): DL={result.dl_on_beam_kg_m:.0f} kg/m., LL={result.ll_on_beam_kg_m:.0f} kg/m.")

    st.subheader("รูปขยายรายละเอียดการเสริมเหล็ก")
    end1_active = result.positions[0].active
    end2_active = result.positions[2].active
    section_png = draw_ow_section_png(
        inp.t_cm, inp.main_bar_dia_mm, inp.main_bar_spacing_cm,
        inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm, inp.S_m,
        end1_active, end2_active,
        main_bar_type=result.main_bar_type, temp_bar_type=result.temp_bar_type)
    plan_png = draw_ow_plan_png(
        inp.main_bar_dia_mm, inp.main_bar_spacing_cm,
        inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm,
        inp.S_m, inp.L_m, end1_active, end2_active,
        main_bar_type=result.main_bar_type, temp_bar_type=result.temp_bar_type)

    dc1, dc2 = st.columns([3, 2])
    with dc1:
        st.image(section_png, caption="รูปตัด (Cross-section)")
    with dc2:
        st.image(plan_png, caption="แปลนเหล็กเสริม (Plan)")

    st.subheader("รายการคำนวณ")
    report_html = build_ow_report_html(
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
