"""
Module 2.1 — บันไดช่วงตรง (Straight-Run Stair)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.stair_straight import (
    StairStraightInput, calculate as calc_stair,
    CONTINUITY_CASES, ALLOWED_THICKNESS_CM, BAR_DIAMETERS_MM,
)
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import draw_stair_section_png, draw_stair_rebar_detail_png
from common import stair_section_template as stair_tmpl
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_stair_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row,
)

inject_card_css()
st.header("2.1 บันไดช่วงตรง (Straight-Run Stair)")

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "st_form_gen" not in st.session_state:
    st.session_state["st_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("stair_straight")
if _loaded_data is not None:
    st.session_state["st_form_gen"] += 1
    st.session_state["_st_loaded_data"] = _loaded_data
    st.session_state["_st_loaded_code"] = _loaded_code
gen = st.session_state["st_form_gen"]
_loaded = st.session_state.get("_st_loaded_data") or {}
_loaded_code = st.session_state.get("_st_loaded_code")

# --- ความต่อเนื่องของบันได: กำหนดเป็น "ต่อเนื่องทั้งสองด้าน" (Both Ends Continuous) เป็น
# มาตรฐานของโปรแกรมตามคำสั่งผู้ใช้ (2026-07-12) — ล็อกเป็น BOTH กรณีเดียวเสมอ ไม่มีตัวเลือก
# ให้เลือก (ยังคงฟิลด์ continuity_case ไว้ใน StairStraightInput/calculate() เพื่อความยืดหยุ่นภายใน)
case_key = "BOTH"

# แถวแรก: กล่องรหัสบันได + หมายเหตุความต่อเนื่อง (ไม่มีตัวเลือกกรณีให้เลือก — ล็อกเป็น SS เดียว)
row1_c1, row1_c2 = st.columns([1.0, 3.0])
with row1_c1:
    with st.container(border=True):
        st.markdown("**รหัสบันได (Stair No.)**")
        stair_name = st.text_input("รหัสบันได (Stair No.)", value=_loaded_code or "ST-01",
                                    key=f"st_name_{gen}", label_visibility="collapsed")
with row1_c2:
    with st.container(border=True):
        st.markdown("**ความต่อเนื่อง (Continuity)**")
        st.caption(f"**{CONTINUITY_CASES[case_key]['label_th']}** "
                   "(มาตรฐานของโปรแกรม: ออกแบบบันไดช่วงตรงเป็นแบบต่อเนื่องทั้งสองด้านเสมอ)")

st.write("")

# แถวสอง: 3 การ์ดกรอบสี [เหล็กเสริม (น้ำเงิน)] [น้ำหนักบรรทุก (ส้ม)] [ขนาดบันได (เขียว)]
col1, col2, col3 = st.columns(3)

with col2:
    with input_card("เหล็กเสริม", color="blue", icon="🔩", key="st-reinf"):
        st.markdown("**เหล็กเสริมหลัก (ตามแนวลาด — รับโมเมนต์)**")
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"st_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        main_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กหลัก", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 2,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"st_main_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
        _main_dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                          if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                          else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                     index=_main_dia_idx, key=f"st_main_dia_{gen}")
        main_bar_spacing = st.number_input("ระยะห่างเหล็กหลัก (ซม.)", value=_loaded.get("main_bar_spacing_cm", 15.0),
                                            step=1.0, key=f"st_main_spacing_{gen}")

        st.markdown("**เหล็กเสริมรอง (ตามแนวขั้น — กระจายแรง/กันร้าว)**")
        temp_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กเสริมรอง", options=_steel_options,
            index=_steel_options.index(_loaded["temp_steel_type"]) if _loaded.get("temp_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"st_temp_steel_{gen}")
        temp_bar_dia_options = bar_dia_options_for_steel(temp_steel_type, BAR_DIAMETERS_MM)
        _temp_dia_idx = (temp_bar_dia_options.index(_loaded["temp_bar_dia_mm"])
                          if _loaded.get("temp_bar_dia_mm") in temp_bar_dia_options
                          else min(1, len(temp_bar_dia_options) - 1))
        temp_bar_dia = st.selectbox("ขนาดเหล็กเสริมรอง (มม.)", options=temp_bar_dia_options,
                                     index=_temp_dia_idx, key=f"st_temp_dia_{gen}")
        temp_bar_spacing = st.number_input("ระยะห่างเหล็กเสริมรอง (ซม.)", value=_loaded.get("temp_bar_spacing_cm", 15.0),
                                            step=1.0, key=f"st_temp_spacing_{gen}")

with col3:
    with input_card("น้ำหนักบรรทุก", color="orange", icon="⚖️", key="st-load"):
        wD = st.number_input("SDL (kg/m²)", value=_loaded.get("wD_kg_m2", 100.0), step=10.0,
                              help="Superimposed Dead Load — ผิวสำเร็จ/ปูน/กระเบื้องขั้นบันได "
                                   "(ไม่รวมน้ำหนักตัวเองของ waist/ขั้นบันได — โปรแกรมคำนวณให้อัตโนมัติจากเรขาคณิต)",
                              key=f"st_wd_{gen}")
        wL = st.number_input("LL (kg/m²)", value=_loaded.get("wL_kg_m2", 200.0), step=10.0,
                              help="Live Load — ค่าเริ่มต้น 200 กก./ตร.ม. ตามตารางน้ำหนักบรรทุกจร กฎกระทรวง 2566 "
                                   "ประเภท \"ระเบียง และบันได\"",
                              key=f"st_wl_{gen}")
        st.caption("- ขอบเขต: บันไดช่วงตรงเดียว ไม่มีชานพัก (ย้ายไปโมดูล 2.2 บันไดหักกลับ)")
        st.caption("- ไม่ตรวจสอบสัดส่วนขั้นบันไดตามกฎหมายอาคาร/สถาปัตยกรรม — ขอบเขตเฉพาะการออกแบบโครงสร้าง")

with col1:
    with input_card("ขนาดบันได", color="green", icon="🪜", key="st-size"):
        n_riser = st.number_input("จำนวนขั้น n", value=int(_loaded.get("n_riser", 10)),
                                   step=1, min_value=2,
                                   help="จำนวนลูกตั้ง (risers) — ลูกตั้งขั้นบนสุดขึ้นถึงระดับพื้นชั้นบนโดยตรง "
                                        "ไม่มีลูกนอนเพิ่มอีกช่วง",
                                   key=f"st_nriser_{gen}")
        length_m = st.number_input("ความยาวทั้งหมด L (ม.)", value=_loaded.get("length_m", 2.25), step=0.05,
                                    min_value=0.10,
                                    help="L = (n-1) × ลูกนอน — ช่วงพาดแนวราบของบันได (horizontal projected span)",
                                    key=f"st_length_{gen}")
        width_m = st.number_input("ความกว้างบันได B (ม.)", value=_loaded.get("width_m", 1.00), step=0.05,
                                   min_value=0.10,
                                   help="ใช้คำนวณจำนวนเหล็กหลักที่ต้องใช้จริง และน้ำหนักรวมที่ถ่ายลงคานรองรับ "
                                        "(ไม่กระทบสูตรโมเมนต์/เหล็กเสริมต่อความกว้าง 1 ม.)",
                                   key=f"st_width_{gen}")
        height_m = st.number_input("ความสูงระหว่างชั้น H (ม.)", value=_loaded.get("height_m", 1.70), step=0.05,
                                    min_value=0.10,
                                    help="H = n × ลูกตั้ง — ความสูงจากพื้นชั้นล่างถึงพื้นชั้นบน",
                                    key=f"st_height_{gen}")
        _rise_preview_cm = height_m / n_riser * 100.0 if n_riser else 0.0
        _going_preview_cm = length_m / max(n_riser - 1, 1) * 100.0
        st.caption(f"→ ลูกตั้ง R = {_rise_preview_cm:.1f} cm., ลูกนอน G = {_going_preview_cm:.1f} cm. ต่อขั้น "
                   "(คำนวณอัตโนมัติจาก L/H/n)")
        _t_idx = ALLOWED_THICKNESS_CM.index(_loaded["t_cm"]) if _loaded.get("t_cm") in ALLOWED_THICKNESS_CM else 3
        t = st.selectbox("ความหนาแผ่น waist, t (cm)", options=ALLOWED_THICKNESS_CM, index=_t_idx,
                          help="ความหนาวัดตั้งฉากกับแนวลาดของบันได", key=f"st_t_{gen}")

inp = StairStraightInput(
    fc_ksc=fc,
    main_steel_type=main_steel_type,
    temp_steel_type=temp_steel_type,
    main_bar_dia_mm=main_bar_dia,
    main_bar_spacing_cm=main_bar_spacing,
    temp_bar_dia_mm=temp_bar_dia,
    temp_bar_spacing_cm=temp_bar_spacing,
    wD_kg_m2=wD,
    wL_kg_m2=wL,
    n_riser=int(n_riser),
    length_m=length_m,
    width_m=width_m,
    height_m=height_m,
    t_cm=t,
    continuity_case=case_key,
)

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ (Compute)", key="npk-btn-compute-st", type="primary", use_container_width=True):
        st.session_state["st_input"] = inp
        st.session_state["st_result"] = calc_stair(inp)
        st.session_state["st_project"] = {"stair_name": stair_name}
        mark_calc_pending_sync("st")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-st", use_container_width=True):
        saved_code = save_item("stair_straight", stair_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสบันได (Stair No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("st_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_st", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "st_result" in st.session_state:
    inp = st.session_state["st_input"]
    result = st.session_state["st_result"]
    project = st.session_state["st_project"]
    case = CONTINUITY_CASES[inp.continuity_case]

    st.header(f"ผลการคำนวณ — {project['stair_name']}")

    metric_card_row([
        ("น้ำหนักบรรทุกใช้งาน Wu", f"{result.wu_kg_m2:.0f}", "kgf/m²", None),
        ("ตรวจสอบความหนา waist", f"{result.tmin_cm:.2f}", f"cm. (ใช้ {inp.t_cm:.1f} cm.)", result.t_ok),
        ("แรงเฉือน Vu / φVc", f"{result.vu_kg:.0f}", f"kgf (φVc={result.phi_vc_kg:.0f})", result.shear_ok),
        ("เหล็กเสริมหลัก", f"{result.as_provided_cm2_m:.2f}", "cm²/m", result.main_reinf_ok),
        ("เหล็กเสริมรอง", f"{result.ast_provided_cm2_m:.2f}", "cm²/m", result.temp_reinf_ok),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**ขนาดบันได**")
            st.write(f"L = {inp.length_m:.2f} m., B = {inp.width_m:.2f} m., H = {inp.height_m:.2f} m., "
                     f"n = {inp.n_riser:.0f} ขั้น (ลูกนอน = {result.n_going:.0f} ขั้น)")
            st.write(f"ลูกตั้ง R = {result.rise_cm:.1f} cm., ลูกนอน G = {result.going_cm:.1f} cm. (คำนวณจาก L/H/n)")
            st.write(f"มุมลาด = {result.slope_deg:.1f}°, ความยาวจริงตามแนวลาด = {result.incline_length_m:.2f} m.")

            st.markdown("**น้ำหนักบรรทุก**")
            st.write(f"DL ตัวเอง: waist = {result.dead_load_waist_kg_m2:.0f} kg/m², "
                     f"ขั้นบันได = {result.dead_load_steps_kg_m2:.0f} kg/m² "
                     f"(รวม = {result.dead_load_self_kg_m2:.0f} kg/m²)")
            st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {result.wu_kg_m2:.0f} kg/m²")

    with dcol2:
        with st.container(border=True):
            st.markdown("**โมเมนต์และเหล็กเสริมหลัก ตามตำแหน่ง**")
            for p in result.positions:
                if not p.active:
                    st.write(f"- {p.label_th}: ไม่มีการออกแบบ (ปลายไม่ต่อเนื่อง)")
                else:
                    warn = "  ⚠️ หน้าตัดเล็กไป (เกิน ρmax)" if p.over_reinforced else ""
                    st.write(f"- {p.label_th}: Mu={p.mu_kgm:.0f} kg-m/m, As ต้องการ={p.as_req_cm2_m:.2f} cm²/m{warn}")
            st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_main}** "
                     f"(As={result.as_provided_cm2_m:.2f} cm²/m, ระยะห่างสูงสุดที่ยอมให้={result.main_spacing_max_cm:.1f} cm.)")
            st.write("ผลตรวจสอบเหล็กหลัก:", "ผ่าน ✅" if result.main_reinf_ok else "ไม่ผ่าน ❌")
            st.write(f"จำนวนเหล็กหลักที่ต้องใช้จริง ตลอดความกว้าง B = {inp.width_m:.2f} m. → **{result.main_bar_count} เส้น**")

    with dcol3:
        with st.container(border=True):
            st.markdown("**เหล็กเสริมรอง — กระจายแรง/กันร้าว**")
            st.write(f"Ast ต้องการ = {result.ast_req_cm2_m:.2f} cm²/m")
            st.write(f"เหล็กที่ใช้จริง: {result.reinf_label_temp} (Ast={result.ast_provided_cm2_m:.2f} cm²/m, "
                     f"ระยะห่างสูงสุด={result.temp_spacing_max_cm:.1f} cm.)")
            st.write("ผลตรวจสอบเหล็กเสริมรอง:", "ผ่าน ✅" if result.temp_reinf_ok else "ไม่ผ่าน ❌")
            st.write(f"จำนวนเหล็กเสริมรองที่ต้องใช้จริง ตลอดความยาวลาดจริง = {result.incline_length_m:.2f} m. "
                     f"→ **{result.temp_bar_count} เส้น**")

            st.markdown("**แรงเฉือน & ถ่ายน้ำหนักลงคาน**")
            st.write(f"Vu = {result.vu_kg:.0f} kg., &phi;Vc = {result.phi_vc_kg:.0f} kg.:",
                      "OK" if result.shear_ok else "ไม่ผ่าน")
            st.write(f"น้ำหนักลงคาน (Service, ต่อ 1 ม.): DL={result.dl_on_beam_kg_m:.0f} kg/m., LL={result.ll_on_beam_kg_m:.0f} kg/m.")
            st.write(f"น้ำหนักลงคานรวม (Service, ตลอดความกว้าง B={inp.width_m:.2f} m.): "
                     f"DL={result.dl_on_beam_total_kg:.0f} kg., LL={result.ll_on_beam_total_kg:.0f} kg.")

    # หมายเหตุ (2026-07-11 รอบแปด): เดิมมี st.subheader("(6) แบบรายละเอียด — รูปด้านข้าง...")
    # ซ้ำกับหัวข้อ "(6) แบบรายละเอียด" ที่ฝังอยู่ในรูป section_png เอง (มุมซ้ายบน สีน้ำเงิน) —
    # เอาออกเพราะซ้ำซ้อน/ดูรกตามที่ผู้ใช้ทักท้วง ให้รูปเป็นผู้แสดงหัวข้อเองจุดเดียว
    # รูปตัดบันได: ใช้ "เทมเพลตจริง" (stair_rebar_template1.png) แล้วเขียนป้ายเหล็กหลักจากการคำนวณ
    # ลงบนเส้นชี้ — ยกเลิกแบบขยาย/ดิมเดิมทั้งหมด (draw_stair_section_png / draw_stair_rebar_detail_png)
    section_png = None
    try:
        section_png = stair_tmpl.render_section_png(inp, result)
    except Exception:
        section_png = None
    if section_png is None:   # ไม่มีเทมเพลต -> วาดด้วยของเดิม
        section_png = draw_stair_section_png(
            inp.n_riser, result.rise_cm, result.going_cm, inp.t_cm, result.S_m)
    st.image(section_png, use_container_width=True)

    st.caption(f"เหล็กเสริมหลัก (ตามแนวลาด) {result.reinf_label_main} — เหล็กเสริมรอง/กระจายแรง "
               f"{result.reinf_label_temp} (ตามแนวขั้น) เหล็กมุม/เหล็กยึดขึ้นใช้ขนาดเดียวกับเหล็กเสริมรอง "
               "ตามธรรมเนียมงานเสริมเหล็กบันได")

    report_html = build_stair_report_html(
        project, inp, result, section_png,
        detail_png=None,
        project_info=st.session_state.get("project_info"),
        logo_bytes=st.session_state.get("project_logo_bytes"),
        logo_mime=st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("st", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['stair_name']}")
