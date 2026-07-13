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
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_ow_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row, render_calc_sheet,
)


def _build_calc_sections(inp, result):
    """วิธีการคำนวณและสูตรที่ใช้ (พื้นทางเดียว) — ดึงค่าจาก result ที่โมดูลคำนวณแล้ว (ไม่คำนวณซ้ำ)"""
    S = inp.S_m
    b = 100.0
    d = next((p.d_cm for p in result.positions if p.active), result.positions[0].d_cm)
    load = [
        {"desc": "อัตราส่วนด้านสั้น/ด้านยาว (ตรวจว่าเป็นพื้นทางเดียว)",
         "formula": "m = S/L", "sub": f"{inp.S_m:.2f}/{inp.L_m:.2f}",
         "result": f"{result.m_ratio:.3f} (≤ 0.50 = พื้นทางเดียว)" if result.one_way_ok else f"{result.m_ratio:.3f} (> 0.50)"},
        {"desc": "น้ำหนักบรรทุกประลัย (Factored load)",
         "formula": "W<sub>u</sub> = 1.4(DL + SDL) + 1.7LL",
         "sub": f"DL(พื้น)={result.dead_load_kg_m2:.0f}",
         "result": f"{result.wu_kg_m2:.0f} kg/m²"},
        {"desc": "ความหนาขั้นต่ำ (Minimum thickness)",
         "formula": "t<sub>min</sub> = (S/denom)(0.40 + f<sub>y</sub>/7000)",
         "result": f"{result.tmin_cm:.2f} cm — ใช้ t = {inp.t_cm:.1f} cm → " + ("ผ่าน ✓" if result.t_ok else "ไม่ผ่าน ✗")},
    ]
    flex = [
        {"desc": "ระยะประสิทธิผล (Effective depth) d",
         "formula": "d = t − ระยะหุ้ม − ⌀หลัก/2", "result": f"{d:.1f} cm"},
        {"desc": "อัตราส่วนเหล็กเสริม (Reinforcement ratios)",
         "formula": (f"ρ<sub>min</sub> = {result.rho_min:.4f} &nbsp; "
                     f"ρ<sub>b</sub> = {result.rho_b:.4f} &nbsp; ρ<sub>max</sub> = 0.75ρ<sub>b</sub> = {result.rho_max:.4f}"
                     f" &nbsp;(β₁ = {result.beta1:.3f})")},
    ]
    for p in result.positions:
        if not p.active:
            continue
        warn = " &nbsp;⚠️ หน้าตัดเล็กไป" if p.over_reinforced else ""
        flex.append({
            "desc": f"โมเมนต์และเหล็กที่ตำแหน่ง: {p.label_th}",
            "formula": (f"M<sub>u</sub> = {p.coeff:.4f}·W<sub>u</sub>·S² = {p.mu_kgm:,.0f} kg·m/m "
                        f"→ A<sub>s</sub> = ρ·b·d = {p.as_req_cm2_m:.2f} cm²/m{warn}")})
    flex.append({
        "desc": "เลือกใช้เหล็กเสริมหลัก",
        "formula": (f"ใช้ {result.reinf_label_main} &nbsp; (A<sub>s,จัดให้</sub> = {result.as_provided_cm2_m:.2f} cm²/m, "
                    f"ระยะห่าง ≤ {result.main_spacing_max_cm:.0f} cm)"),
        "result": "ผ่าน ✓" if result.main_reinf_ok else "ไม่ผ่าน ✗"})
    other = [
        {"desc": "เหล็กเสริมกันร้าว/กระจายแรง (แนว L)",
         "formula": (f"A<sub>st,ต้องการ</sub> = {result.ast_req_cm2_m:.2f} cm²/m → ใช้ {result.reinf_label_temp} "
                     f"(A<sub>st</sub> = {result.ast_provided_cm2_m:.2f} cm²/m, ระยะ ≤ {result.temp_spacing_max_cm:.0f} cm)"),
         "result": "ผ่าน ✓" if result.temp_reinf_ok else "ไม่ผ่าน ✗"},
        {"desc": "ตรวจสอบแรงเฉือน (Shear)",
         "formula": "V<sub>u</sub> ≤ φV<sub>c</sub> = φ·0.53√f'<sub>c</sub>·b·d",
         "sub": f"{result.vu_kg:,.0f} ≤ {result.phi_vc_kg:,.0f} kg",
         "result": "ผ่าน ✓" if result.shear_ok else "ไม่ผ่าน ✗"},
    ]
    return [
        {"title": "การวิเคราะห์น้ำหนักบรรทุกและความหนาพื้น (Load & Thickness)", "steps": load},
        {"title": "การออกแบบเหล็กเสริมหลักรับแรงดัด (Flexural Design — Main Bars)", "steps": flex},
        {"title": "เหล็กเสริมกันร้าวและแรงเฉือน (Temperature Steel & Shear)", "steps": other},
    ]

inject_card_css()
st.header("1.2 พื้นทางเดียว (One-way Slab)")

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "ow_form_gen" not in st.session_state:
    st.session_state["ow_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("one_way_slab")
if _loaded_data is not None:
    st.session_state["ow_form_gen"] += 1
    st.session_state["_ow_loaded_data"] = _loaded_data
    st.session_state["_ow_loaded_code"] = _loaded_code
    # case_key ไม่ใช่ widget แบบมี key=/value= ตรงๆ (เป็นปุ่มแถวเดียวที่ผูกกับ
    # session_state ตรงๆ) จึงตั้งค่าตรงนี้ได้เลย ไม่ต้องรอ gen
    st.session_state["ow_case_key"] = _loaded_data.get("continuity_case", "BOTH")
gen = st.session_state["ow_form_gen"]
_loaded = st.session_state.get("_ow_loaded_data") or {}
_loaded_code = st.session_state.get("_ow_loaded_code")

# --- ตัวเลือกความต่อเนื่องของพื้น: ปุ่มเรียงกัน 1/2/3 แทน dropdown (ดูง่ายกว่า) ---
CASE_KEYS = list(CONTINUITY_CASES.keys())          # ["SS", "ONE", "BOTH"]
CASE_SHORT_TH = {
    "SS": "ไม่ต่อเนื่อง",
    "ONE": "ต่อเนื่องด้านเดียว",
    "BOTH": "ต่อเนื่อง 2 ด้าน",
}

if "ow_case_key" not in st.session_state:
    st.session_state["ow_case_key"] = "BOTH"

# แถวแรก: 3 กล่องเรียงกัน [ความต่อเนื่องของพื้น] [กรณีที่เลือก] [รหัสพื้น] — ตามแนวทาง 1.3 พื้นสองทาง
row1_c1, row1_c2, row1_c3 = st.columns([1.6, 1.2, 1.0])
with row1_c1:
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
                st.markdown(f"<div style='text-align:center; font-weight:bold; font-size:12.5px;'>{CASE_SHORT_TH[k]}</div>",
                            unsafe_allow_html=True)

case_key = st.session_state["ow_case_key"]
with row1_c2:
    with st.container(border=True):
        st.markdown("**กรณีที่เลือก (Case)**")
        st.text_input("กรณีที่เลือก",
                      value=f"{CASE_KEYS.index(case_key) + 1} — {CONTINUITY_CASES[case_key]['label_th']}",
                      disabled=True, label_visibility="collapsed")
with row1_c3:
    with st.container(border=True):
        st.markdown("**รหัสพื้น (Slab No.)**")
        slab_name = st.text_input("รหัสพื้น", value=_loaded_code or "S-01", key=f"ow_slabname_{gen}",
                                   label_visibility="collapsed")

st.write("")

# แถวสอง: 3 การ์ดกรอบสี [เหล็กเสริม (น้ำเงิน)] [น้ำหนักบรรทุก (ส้ม)] [ขนาดพื้น (เขียว)]
col1, col2, col3 = st.columns(3)

with col1:
    with input_card("เหล็กเสริม", color="blue", icon="🔩", key="ow-reinf"):
        st.markdown("**เหล็กเสริมหลัก (แนว S — รับโมเมนต์)**")
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"ow_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        main_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กหลัก", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"ow_main_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
        _main_dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                          if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                          else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                     index=_main_dia_idx, key=f"ow_main_dia_{gen}")
        main_bar_spacing = st.number_input("ระยะห่างเหล็กหลัก (ซม.)", value=_loaded.get("main_bar_spacing_cm", 15.0),
                                            step=1.0, key=f"ow_main_spacing_{gen}")

        st.markdown("**เหล็กเสริมรอง (แนว L — กระจายแรง/กันร้าว)**")
        temp_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กเสริมรอง", options=_steel_options,
            index=_steel_options.index(_loaded["temp_steel_type"]) if _loaded.get("temp_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"ow_temp_steel_{gen}")
        temp_bar_dia_options = bar_dia_options_for_steel(temp_steel_type, BAR_DIAMETERS_MM)
        _temp_dia_idx = (temp_bar_dia_options.index(_loaded["temp_bar_dia_mm"])
                          if _loaded.get("temp_bar_dia_mm") in temp_bar_dia_options
                          else min(1, len(temp_bar_dia_options) - 1))
        temp_bar_dia = st.selectbox("ขนาดเหล็กเสริมรอง (มม.)", options=temp_bar_dia_options,
                                     index=_temp_dia_idx, key=f"ow_temp_dia_{gen}")
        temp_bar_spacing = st.number_input("ระยะห่างเหล็กเสริมรอง (ซม.)", value=_loaded.get("temp_bar_spacing_cm", 15.0),
                                            step=1.0, key=f"ow_temp_spacing_{gen}")

with col2:
    with input_card("น้ำหนักบรรทุก", color="orange", icon="⚖️", key="ow-load"):
        wD = st.number_input("SDL (kg/m²)", value=_loaded.get("wD_kg_m2", 120.0), step=10.0,
                              help="Superimposed Dead Load", key=f"ow_wd_{gen}")
        wL = st.number_input("LL (kg/m²)", value=_loaded.get("wL_kg_m2", 200.0), step=10.0,
                              help="Live Load — ค่าเริ่มต้น 200 กก./ตร.ม. ตามตารางน้ำหนักบรรทุกจร กฎกระทรวง 2566 "
                                   "ประเภทบ้านพักอาศัย",
                              key=f"ow_wl_{gen}")

with col3:
    with input_card("ขนาดพื้น", color="green", icon="📐", key="ow-size"):
        S = st.number_input("ช่วงพาด S — แนวเหล็กหลัก (m)", value=_loaded.get("S_m", 1.5), step=0.5, key=f"ow_S_{gen}")
        L = st.number_input("ด้านยาว L — ทิศตั้งฉาก (m)", value=_loaded.get("L_m", 4.0), step=0.5,
                             help="ต้อง S/L <= 0.5 จึงจะถือเป็นพื้นทางเดียว", key=f"ow_L_{gen}")
        _t_idx = ALLOWED_THICKNESS_CM.index(_loaded["t_cm"]) if _loaded.get("t_cm") in ALLOWED_THICKNESS_CM else 1
        t = st.selectbox("ความหนาพื้น t (cm)", options=ALLOWED_THICKNESS_CM, index=_t_idx, key=f"ow_t_{gen}")

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

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ", key="npk-btn-compute-ow", type="primary", use_container_width=True):
        st.session_state["ow_input"] = inp
        st.session_state["ow_result"] = calc_ow(inp)
        st.session_state["ow_project"] = {"slab_name": slab_name}
        mark_calc_pending_sync("ow")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-ow", use_container_width=True):
        saved_code = save_item("one_way_slab", slab_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสพื้น (Slab No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("ow_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_ow", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

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

    metric_card_row([
        ("น้ำหนักบรรทุกใช้งาน Wu", f"{result.wu_kg_m2:.0f}", "kgf/m²", None),
        ("ตรวจสอบ m=S/L", f"{result.m_ratio:.3f}", "ต้อง <= 0.5", result.one_way_ok),
        ("ตรวจสอบความหนา", f"{result.tmin_cm:.2f}", f"cm. (ใช้ {inp.t_cm:.1f} cm.)", result.t_ok),
        ("แรงเฉือน Vu / φVc", f"{result.vu_kg:.0f}", f"kgf (φVc={result.phi_vc_kg:.0f})", result.shear_ok),
        ("เหล็กเสริมหลัก (S)", f"{result.as_provided_cm2_m:.2f}", "cm²/m", result.main_reinf_ok),
        ("เหล็กเสริมรอง (L)", f"{result.ast_provided_cm2_m:.2f}", "cm²/m", result.temp_reinf_ok),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**น้ำหนักบรรทุก & แรงเฉือน**")
            st.write(f"Dead Load (จากความหนาพื้น) = {result.dead_load_kg_m2:.0f} kg/m²")
            st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {result.wu_kg_m2:.0f} kg/m²")
            st.write(f"Vu = {result.vu_kg:.0f} kg., &phi;Vc = {result.phi_vc_kg:.0f} kg.:",
                      "OK" if result.shear_ok else "ไม่ผ่าน")
            st.write(f"น้ำหนักลงคาน (Service): DL={result.dl_on_beam_kg_m:.0f} kg/m., LL={result.ll_on_beam_kg_m:.0f} kg/m.")

    with dcol2:
        with st.container(border=True):
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

    with dcol3:
        with st.container(border=True):
            st.markdown("**เหล็กเสริมรอง — กระจายแรง/กันร้าว (แนว L)**")
            st.write(f"Ast ต้องการ = {result.ast_req_cm2_m:.2f} cm²/m")
            st.write(f"เหล็กที่ใช้จริง: {result.reinf_label_temp} (Ast={result.ast_provided_cm2_m:.2f} cm²/m, "
                     f"ระยะห่างสูงสุด={result.temp_spacing_max_cm:.1f} cm.)")
            st.write("ผลตรวจสอบเหล็กเสริมรอง:", "ผ่าน ✅" if result.temp_reinf_ok else "ไม่ผ่าน ❌")

    st.write("")
    st.subheader("วิธีการคำนวณและสูตรที่ใช้")
    render_calc_sheet(_build_calc_sections(inp, result))

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

    report_html = build_ow_report_html(
        project, inp, result, section_png, plan_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("ow", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['slab_name']}")
