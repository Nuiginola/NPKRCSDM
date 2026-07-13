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
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_cant_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row,
)

inject_card_css()
st.header("1.4 พื้นยื่น (Cantilever Slab)")

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "cant_slab_form_gen" not in st.session_state:
    st.session_state["cant_slab_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("cantilever_slab")
if _loaded_data is not None:
    st.session_state["cant_slab_form_gen"] += 1
    st.session_state["_cant_slab_loaded_data"] = _loaded_data
    st.session_state["_cant_slab_loaded_code"] = _loaded_code
gen = st.session_state["cant_slab_form_gen"]
_loaded = st.session_state.get("_cant_slab_loaded_data") or {}
_loaded_code = st.session_state.get("_cant_slab_loaded_code")

with st.container(border=True):
    st.markdown("**รหัสพื้น (Slab No.)**")
    slab_name = st.text_input("รหัสพื้น (Slab No.)", value=_loaded_code or "S-04", key=f"cs_slabname_{gen}",
                               label_visibility="collapsed")

st.write("")

# แถวการ์ดกรอบสี [เหล็กเสริม (น้ำเงิน)] [น้ำหนักบรรทุก (ส้ม)] [ขนาดพื้น (เขียว)]
col1, col2, col3 = st.columns(3)

with col1:
    with input_card("เหล็กเสริม", color="blue", icon="🔩", key="cs-reinf"):
        st.markdown("**เหล็กเสริมหลัก (แนวยื่น — รับโมเมนต์ลบ)**")
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"cs_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        main_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กหลัก", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"cs_main_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
        _main_dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                          if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                          else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                     index=_main_dia_idx, key=f"cs_main_dia_{gen}")
        main_bar_spacing = st.number_input("ระยะห่างเหล็กหลัก (ซม.)", value=_loaded.get("main_bar_spacing_cm", 15.0),
                                            step=1.0, key=f"cs_main_spacing_{gen}")

        st.markdown("**เหล็กเสริมรอง (ขนานแนวจุดรองรับ)**")
        temp_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กเสริมรอง", options=_steel_options,
            index=_steel_options.index(_loaded["temp_steel_type"]) if _loaded.get("temp_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"cs_temp_steel_{gen}")
        temp_bar_dia_options = bar_dia_options_for_steel(temp_steel_type, BAR_DIAMETERS_MM)
        _temp_dia_idx = (temp_bar_dia_options.index(_loaded["temp_bar_dia_mm"])
                          if _loaded.get("temp_bar_dia_mm") in temp_bar_dia_options
                          else min(1, len(temp_bar_dia_options) - 1))
        temp_bar_dia = st.selectbox("ขนาดเหล็กเสริมรอง (มม.)", options=temp_bar_dia_options,
                                     index=_temp_dia_idx, key=f"cs_temp_dia_{gen}")
        temp_bar_spacing = st.number_input("ระยะห่างเหล็กเสริมรอง (ซม.)", value=_loaded.get("temp_bar_spacing_cm", 15.0),
                                            step=1.0, key=f"cs_temp_spacing_{gen}")

with col2:
    with input_card("น้ำหนักบรรทุก", color="orange", icon="⚖️", key="cs-load"):
        wD = st.number_input("SDL (kg/m²)", value=_loaded.get("wD_kg_m2", 120.0), step=10.0,
                              help="Superimposed Dead Load", key=f"cs_wd_{gen}")
        wL = st.number_input("LL (kg/m²)", value=_loaded.get("wL_kg_m2", 200.0), step=10.0,
                              help="Live Load — ค่าเริ่มต้น 200 กก./ตร.ม. ตามตารางน้ำหนักบรรทุกจร กฎกระทรวง 2566 "
                                   "ประเภทบ้านพักอาศัย",
                              key=f"cs_wl_{gen}")
        fin_wg = st.number_input("Fin Wg. (kg/m)", value=_loaded.get("fin_wg_kg_m", 0.0), step=10.0,
                                  help="น้ำหนักแนวกันตก/ผนังเตี้ยที่ปลายยื่น — น้ำหนักเชิงเส้นที่ขอบอิสระของพื้นยื่น "
                                       "เช่น ราวกันตก/ผนังเตี้ยระเบียง ใส่ 0 ถ้าไม่มี", key=f"cs_finwg_{gen}")

with col3:
    with input_card("ขนาดพื้น", color="green", icon="📐", key="cs-size"):
        S = st.number_input("ความยาวยื่น S (m)", value=_loaded.get("S_m", 1.2), step=0.1, key=f"cs_S_{gen}")
        _t_idx = ALLOWED_THICKNESS_CM.index(_loaded["t_cm"]) if _loaded.get("t_cm") in ALLOWED_THICKNESS_CM else 1
        t = st.selectbox("ความหนาพื้น t (cm)", options=ALLOWED_THICKNESS_CM, index=_t_idx, key=f"cs_t_{gen}")

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

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ (Compute)", key="npk-btn-compute-cs", type="primary", use_container_width=True):
        st.session_state["cant_input"] = inp
        st.session_state["cant_result"] = calc_cant(inp)
        st.session_state["cant_project"] = {"slab_name": slab_name}
        mark_calc_pending_sync("cs")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-cs", use_container_width=True):
        saved_code = save_item("cantilever_slab", slab_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสพื้น (Slab No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("cs_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_cs", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "cant_result" in st.session_state:
    inp = st.session_state["cant_input"]
    result = st.session_state["cant_result"]
    project = st.session_state["cant_project"]

    st.header(f"ผลการคำนวณ — {project['slab_name']}")

    metric_card_row([
        ("น้ำหนักบรรทุกใช้งาน Wu", f"{result.wu_kg_m2:.0f}", "kgf/m²", None),
        ("ตรวจสอบความหนา", f"{result.tmin_cm:.2f}", f"cm. (ใช้ {inp.t_cm:.1f} cm.)", result.t_ok),
        ("แรงเฉือน Vu / φVc", f"{result.vu_kg:.0f}", f"kgf (φVc={result.phi_vc_kg:.0f})", result.shear_ok),
        ("เหล็กเสริมหลัก", f"{result.as_provided_cm2_m:.2f}", "cm²/m", result.main_reinf_ok),
        ("เหล็กเสริมรอง", f"{result.ast_provided_cm2_m:.2f}", "cm²/m", result.temp_reinf_ok),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**น้ำหนักบรรทุก / ความหนา**")
            st.write(f"Dead Load (จากความหนาพื้น) = {result.dead_load_kg_m2:.0f} kg/m²")
            st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {result.wu_kg_m2:.0f} kg/m²")
            st.write(f"FIN = 1.4(Fin Wg.) = {result.fin_kg_m:.0f} kg/m.")
            st.write(f"tmin = {result.tmin_cm:.2f} cm. (t ที่ใช้ = {inp.t_cm:.1f} cm.):",
                      "OK" if result.t_ok else "ไม่ผ่าน — เพิ่มความหนา")

    with dcol2:
        with st.container(border=True):
            st.markdown("**โมเมนต์และเหล็กเสริมหลัก (ที่จุดรองรับ)**")
            warn = "  ⚠️ หน้าตัดเล็กไป (เกิน ρmax)" if result.over_reinforced else ""
            st.write(f"Mu = {result.mu_kgm:.0f} kg-m/m, As ต้องการ (จากโมเมนต์) = "
                     f"{result.as_req_flexure_cm2_m:.2f} cm²/m{warn}")
            st.write(f"As ต้องการสูงสุด (รวม Ast ขั้นต่ำ 0.002bt={result.ast_min_main_cm2_m:.2f}) = "
                     f"{result.as_req_governing_cm2_m:.2f} cm²/m")
            st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_main}** "
                     f"(As={result.as_provided_cm2_m:.2f} cm²/m, ระยะห่างสูงสุดที่ยอมให้={result.main_spacing_max_cm:.1f} cm.)")
            st.write("ผลตรวจสอบเหล็กหลัก:", "ผ่าน ✅" if result.main_reinf_ok else "ไม่ผ่าน ❌")

    with dcol3:
        with st.container(border=True):
            st.markdown("**เหล็กเสริมรอง & แรงเฉือน/ถ่ายน้ำหนัก**")
            st.write(f"Ast ต้องการ = {result.ast_req_cm2_m:.2f} cm²/m")
            st.write(f"เหล็กที่ใช้จริง: {result.reinf_label_temp} (Ast={result.ast_provided_cm2_m:.2f} cm²/m, "
                     f"ระยะห่างสูงสุด={result.temp_spacing_max_cm:.1f} cm.)")
            st.write("ผลตรวจสอบเหล็กเสริมรอง:", "ผ่าน ✅" if result.temp_reinf_ok else "ไม่ผ่าน ❌")
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

    report_html = build_cant_report_html(
        project, inp, result, section_png, plan_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("cs", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['slab_name']}")
