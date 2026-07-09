"""
Module 1.3 — พื้นสองทาง (Two-way Slab)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.two_way_slab import (
    TwoWaySlabInput, calculate as calc_tw,
    TWO_WAY_CASES, ALLOWED_THICKNESS_CM, BAR_DIAMETERS_MM,
)
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import draw_tw_section_png, draw_tw_plan_png
from common.report import build_tw_report_html

st.header("1.3 พื้นสองทาง (Two-way Slab)")


def _tw_end_states(positions):
    """แปลงผล Con-/Mid+/Disc- (positions[0]/[1]/[2]) เป็นสถานะขอบสำหรับรูปวาด:
    ทั้งสองขอบต่อเนื่อง (Con- active, Disc- ไม่ active), ขอบหนึ่งต่อเนื่อง+ขอบหนึ่งไม่ต่อเนื่อง
    (ทั้งคู่ active), หรือไม่มีเหล็กบนเลย (Con-/Disc- ไม่ active ทั้งคู่ — กรณี fully_disc)."""
    con_active = positions[0].active
    disc_active = positions[2].active
    if con_active and disc_active:
        return "continuous", "discontinuous"
    if con_active:
        return "continuous", "continuous"
    return "none", "none"

slab_name = st.text_input("รหัสพื้น (Slab No.)", value="S2-01")

# --- ตัวเลือกกรณีขอบเขตพื้น: ปุ่มเรียงกัน 1-5 แทน dropdown ---
CASE_KEYS = list(TWO_WAY_CASES.keys())
CASE_SHORT_TH = {
    "CASE1": "4 ด้านต่อเนื่อง",
    "CASE2": "ไม่ต่อเนื่อง 1 ด้าน",
    "CASE3": "ไม่ต่อเนื่อง 2 ด้าน",
    "CASE4": "ไม่ต่อเนื่อง 3 ด้าน",
    "CASE5": "ไม่ต่อเนื่อง 4 ด้าน",
}

if "tw_case_key" not in st.session_state:
    st.session_state["tw_case_key"] = "CASE2"

with st.container(border=True):
    st.markdown("**กรณีขอบเขตพื้น (Edge Condition Cases)**")
    case_btn_cols = st.columns(len(CASE_KEYS))
    for i, k in enumerate(CASE_KEYS):
        with case_btn_cols[i]:
            is_selected = st.session_state["tw_case_key"] == k
            if st.button(str(i + 1), key=f"tw_case_btn_{k}",
                         type="primary" if is_selected else "secondary",
                         use_container_width=True):
                if not is_selected:
                    st.session_state["tw_case_key"] = k
                    st.rerun()
            st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:12.5px;'>{CASE_SHORT_TH[k]}</div>",
                        unsafe_allow_html=True)

    case_key = st.session_state["tw_case_key"]
    case = TWO_WAY_CASES[case_key]
    confirm_note = " ✅ ยืนยันจากไฟล์ตัวอย่าง" if case["confirmed"] else ""
    st.text_input("กรณีที่เลือก (Case)",
                  value=f"{CASE_KEYS.index(case_key) + 1} — {case['label_th']}{confirm_note}",
                  disabled=True)

col1, col2, col3 = st.columns(3)


def _bar_type_label(k):
    return "DB (เหล็กข้ออ้อย)" if k == "DB" else "RB (เหล็กเส้นกลม)"


with col1:
    st.subheader("เหล็กเสริมทิศทางสั้น (S)")
    _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
    fc = st.number_input("กำลังอัดประลัยคอนกรีต f'c (kg/cm²)", value=_default_fc, step=10.0,
                          help="ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้")
    short_steel_type = st.selectbox(
        "ชั้นคุณภาพเหล็ก (แนวสั้น)", options=list(GS_STEEL_FY_KSC.keys()), index=0,
        format_func=lambda k: f"{k} (fy={GS_STEEL_FY_KSC[k]:.0f} ksc) — {_bar_type_label(GS_STEEL_BAR_TYPE[k])}",
        help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)")
    short_bar_dia_options = bar_dia_options_for_steel(short_steel_type, BAR_DIAMETERS_MM)
    short_bar_dia = st.selectbox("ขนาดเหล็ก แนวสั้น (มม.)", options=short_bar_dia_options,
                                  index=min(1, len(short_bar_dia_options) - 1))
    short_bar_spacing = st.number_input("ระยะห่างเหล็ก แนวสั้น (ซม.)", value=15.0, step=1.0)

    st.subheader("เหล็กเสริมทิศทางยาว (L)")
    long_steel_type = st.selectbox(
        "ชั้นคุณภาพเหล็ก (แนวยาว)", options=list(GS_STEEL_FY_KSC.keys()), index=0,
        format_func=lambda k: f"{k} (fy={GS_STEEL_FY_KSC[k]:.0f} ksc) — {_bar_type_label(GS_STEEL_BAR_TYPE[k])}",
        help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)")
    long_bar_dia_options = bar_dia_options_for_steel(long_steel_type, BAR_DIAMETERS_MM)
    long_bar_dia = st.selectbox("ขนาดเหล็ก แนวยาว (มม.)", options=long_bar_dia_options,
                                 index=min(1, len(long_bar_dia_options) - 1))
    long_bar_spacing = st.number_input("ระยะห่างเหล็ก แนวยาว (ซม.)", value=15.0, step=1.0)

with col2:
    st.subheader("น้ำหนักบรรทุก")
    wD = st.number_input("Superimposed Dead Load, SDL (kg/m²)", value=150.0, step=10.0)
    wL = st.number_input("Live Load, LL (kg/m²)", value=200.0, step=10.0,
                          help="ค่าเริ่มต้น 200 กก./ตร.ม. ตามตารางน้ำหนักบรรทุกจร กฎกระทรวง 2566 ประเภทบ้านพักอาศัย")

with col3:
    st.subheader("ขนาดพื้น")
    S = st.number_input("ช่วงพาด S — ด้านสั้น (m)", value=2.5, step=0.5)
    L = st.number_input("ช่วงพาด L — ด้านยาว (m)", value=3.0, step=0.5,
                         help="ต้อง S/L > 0.5 จึงจะถือเป็นพื้นสองทาง (ถ้า <=0.5 ให้ใช้โมดูล 1.2 พื้นทางเดียวแทน)")
    t = st.selectbox("ความหนาพื้น t (cm)", options=ALLOWED_THICKNESS_CM, index=1)

if st.button("คำนวณ (Compute)", type="primary"):
    inp = TwoWaySlabInput(
        fc_ksc=fc,
        short_steel_type=short_steel_type,
        long_steel_type=long_steel_type,
        short_bar_dia_mm=short_bar_dia,
        short_bar_spacing_cm=short_bar_spacing,
        long_bar_dia_mm=long_bar_dia,
        long_bar_spacing_cm=long_bar_spacing,
        wD_kg_m2=wD,
        wL_kg_m2=wL,
        S_m=S,
        L_m=L,
        t_cm=t,
        case_key=case_key,
    )
    st.session_state["tw_input"] = inp
    st.session_state["tw_result"] = calc_tw(inp)
    st.session_state["tw_project"] = {"slab_name": slab_name}

if "tw_result" in st.session_state:
    inp = st.session_state["tw_input"]
    result = st.session_state["tw_result"]
    project = st.session_state["tw_project"]

    st.header(f"ผลการคำนวณ — {project['slab_name']}")

    if not result.two_way_ok:
        st.warning(f"⚠️ m = S/L = {result.m_ratio:.3f} <= 0.5 — พฤติกรรมของพื้นแผ่นนี้เป็นแบบ **ทางเดียว (One-way)** "
                   "ไม่ใช่สองทางแล้ว ผลการคำนวณด้านล่างจึงไม่ถูกต้องตามพฤติกรรมจริง แนะนำให้ใช้โมดูล "
                   "1.2 พื้นทางเดียว (One-way Slab) ในการออกแบบแทน")
        try:
            st.page_link("app_pages/one_way_slab.py",
                         label="ไปที่โมดูล 1.2 พื้นทางเดียว (One-way Slab)", icon="↪️")
        except Exception:
            pass

    r1, r2 = st.columns(2)
    with r1:
        st.markdown("**น้ำหนักบรรทุก**")
        st.write(f"Dead Load (จากความหนาพื้น) = {result.dead_load_kg_m2:.0f} kg/m²")
        st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {result.wu_kg_m2:.0f} kg/m²")

        st.markdown("**ตรวจสอบขนาด/ความหนา**")
        st.write(f"m = S/L = {result.m_ratio:.3f} (ต้อง > 0.5):",
                 "OK" if result.two_way_ok else "ไม่ผ่าน — พฤติกรรมเป็นพื้นทางเดียว")
        st.write(f"tmin = {result.tmin_cm:.2f} cm. (t ที่ใช้ = {inp.t_cm:.1f} cm.):",
                  "OK" if result.t_ok else "ไม่ผ่าน — เพิ่มความหนา")

    with r2:
        st.markdown("**แรงเฉือน & ถ่ายน้ำหนักลงคาน**")
        st.write(f"Vu = {result.vu_kg:.0f} kg., &phi;Vc = {result.phi_vc_kg:.0f} kg.:",
                  "OK" if result.shear_ok else "ไม่ผ่าน")
        st.write(f"น้ำหนักลงคาน (Service, สามเหลี่ยม/คางหมู): "
                 f"DL={result.dl_on_beam_triangular_kg_m:.0f}/{result.dl_on_beam_trapezoidal_kg_m:.0f} kg/m., "
                 f"LL={result.ll_on_beam_triangular_kg_m:.0f}/{result.ll_on_beam_trapezoidal_kg_m:.0f} kg/m.")

    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**โมเมนต์และเหล็กเสริม — ทิศทางสั้น (S)**")
        for p in result.short_positions:
            if not p.active:
                st.write(f"- {p.label_th}: ไม่มีการออกแบบ")
            else:
                warn = "  ⚠️ หน้าตัดเล็กไป (เกิน ρmax)" if p.over_reinforced else ""
                st.write(f"- {p.label_th}: Mu={p.mu_kgm:.0f} kg-m/m, As ต้องการ={p.as_req_cm2_m:.2f} cm²/m{warn}")
        st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_short}** "
                 f"(As={result.as_provided_short_cm2_m:.2f} cm²/m, ระยะห่างสูงสุด={result.short_spacing_max_cm:.1f} cm.)")
        st.write("ผลตรวจสอบ:", "ผ่าน ✅" if result.short_reinf_ok else "ไม่ผ่าน ❌")

    with c2:
        st.markdown("**โมเมนต์และเหล็กเสริม — ทิศทางยาว (L)**")
        for p in result.long_positions:
            if not p.active:
                st.write(f"- {p.label_th}: ไม่มีการออกแบบ")
            else:
                warn = "  ⚠️ หน้าตัดเล็กไป (เกิน ρmax)" if p.over_reinforced else ""
                st.write(f"- {p.label_th}: Mu={p.mu_kgm:.0f} kg-m/m, As ต้องการ={p.as_req_cm2_m:.2f} cm²/m{warn}")
        st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_long}** "
                 f"(As={result.as_provided_long_cm2_m:.2f} cm²/m, ระยะห่างสูงสุด={result.long_spacing_max_cm:.1f} cm.)")
        st.write("ผลตรวจสอบ:", "ผ่าน ✅" if result.long_reinf_ok else "ไม่ผ่าน ❌")

    st.subheader("รูปขยายรายละเอียดการเสริมเหล็ก")
    s_end1, s_end2 = _tw_end_states(result.short_positions)
    l_end1, l_end2 = _tw_end_states(result.long_positions)

    section_s_png = draw_tw_section_png(
        "S", inp.S_m, inp.t_cm,
        inp.short_bar_dia_mm, inp.short_bar_spacing_cm, result.short_bar_type,
        inp.long_bar_dia_mm, inp.long_bar_spacing_cm, result.long_bar_type,
        end1_state=s_end1, end2_state=s_end2)
    section_l_png = draw_tw_section_png(
        "L", inp.L_m, inp.t_cm,
        inp.long_bar_dia_mm, inp.long_bar_spacing_cm, result.long_bar_type,
        inp.short_bar_dia_mm, inp.short_bar_spacing_cm, result.short_bar_type,
        end1_state=l_end1, end2_state=l_end2)
    plan_png = draw_tw_plan_png(
        inp.S_m, inp.L_m,
        inp.short_bar_dia_mm, inp.short_bar_spacing_cm, result.short_bar_type,
        inp.long_bar_dia_mm, inp.long_bar_spacing_cm, result.long_bar_type,
        s_end1_state=s_end1, s_end2_state=s_end2,
        l_end1_state=l_end1, l_end2_state=l_end2)

    # รูปตัดแสดงเรียงต่อกันแนวตั้ง เต็มความกว้าง (ไม่แบ่งคอลัมน์) เพื่อให้ตัวอักษร/เส้นบอกระยะ
    # อ่านง่ายชัดเจนที่สุด ตามที่ผู้ใช้แจ้งแก้ไข (2026-07)
    st.image(section_s_png, caption="รูปตัด — ทิศทางสั้น (Short Span Section)", use_container_width=True)
    st.image(section_l_png, caption="รูปตัด — ทิศทางยาว (Long Span Section)", use_container_width=True)
    st.image(plan_png, caption="แปลนเหล็กเสริม (Reinforcement Plan)", use_container_width=True)

    st.subheader("รายการคำนวณ")
    report_html = build_tw_report_html(
        project, inp, result, section_s_png, section_l_png, plan_png,
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
