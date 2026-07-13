"""
Module 2.2 — บันไดหักกลับ (U-Shape Stair, มีชานพัก)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.stair_u_shape import (
    StairUShapeInput, calculate as calc_stair_u,
)
from modules.stair_straight import ALLOWED_THICKNESS_CM, BAR_DIAMETERS_MM
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.stair_detail import draw_stair_u_shape_detail_template_png
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_stair_u_shape_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row, render_calc_sheet,
)

inject_card_css()
st.header("2.2 บันไดหักกลับ (U-Shape Stair, มีชานพัก)")


def _build_calc_sections(inp, result):
    """วิธีการคำนวณและสูตรที่ใช้ (บันไดหักกลับ) — คิดต่อช่วง (ทั้งสองช่วงเท่ากัน) จาก result.flight
    + ข้อมูลชานพัก ดึงค่าจาก result (ไม่คำนวณซ้ำ)"""
    f = result.flight
    d = next((p.d_cm for p in f.positions if p.active), f.positions[0].d_cm)
    geo = [
        {"desc": "จำนวนขั้นและสัดส่วนขั้น (ต่อช่วง, ทั้งสองช่วงเท่ากัน)",
         "formula": f"n รวม = {result.n_riser_total_used:.0f} ขั้น ({result.n_riser_per_flight:.0f} ขั้น/ช่วง, ลูกนอน {f.n_going:.0f})",
         "result": f"R = {f.rise_cm:.1f} cm, G = {f.going_cm:.1f} cm"},
        {"desc": "มุมลาดและความยาวจริงตามแนวลาด (ต่อช่วง)",
         "formula": "ความยาวลาด = √(ราบ² + สูง²)",
         "result": f"มุมลาด {f.slope_deg:.1f}° , ความยาวลาด {f.incline_length_m:.2f} m"},
    ]
    load = [
        {"desc": "น้ำหนักตัวเอง (Dead load)",
         "formula": f"DL = waist {f.dead_load_waist_kg_m2:.0f} + ขั้นบันได {f.dead_load_steps_kg_m2:.0f}",
         "result": f"{f.dead_load_self_kg_m2:.0f} kg/m²"},
        {"desc": "น้ำหนักบรรทุกประลัย (Factored load)",
         "formula": "W<sub>u</sub> = 1.4(DL + SDL) + 1.7LL", "result": f"{f.wu_kg_m2:.0f} kg/m²"},
        {"desc": "ความหนาแผ่นพื้นเอียงขั้นต่ำ (Minimum waist)",
         "formula": "t<sub>min</sub> = (S/denom)(0.40 + f<sub>y</sub>/7000)",
         "result": f"{f.tmin_cm:.2f} cm — ใช้ t = {inp.t_cm:.1f} cm → " + ("ผ่าน ✓" if f.t_ok else "ไม่ผ่าน ✗")},
    ]
    flex = [
        {"desc": "ระยะประสิทธิผล (Effective depth) d",
         "formula": "d = t − ระยะหุ้ม − ⌀หลัก/2", "result": f"{d:.1f} cm"},
        {"desc": "อัตราส่วนเหล็กเสริม (Reinforcement ratios)",
         "formula": (f"ρ<sub>min</sub> = {f.rho_min:.4f} &nbsp; ρ<sub>b</sub> = {f.rho_b:.4f} &nbsp; "
                     f"ρ<sub>max</sub> = 0.75ρ<sub>b</sub> = {f.rho_max:.4f} &nbsp;(β₁ = {f.beta1:.3f})")},
    ]
    for p in f.positions:
        if not p.active:
            continue
        warn = " &nbsp;⚠️ หน้าตัดเล็กไป" if p.over_reinforced else ""
        flex.append({
            "desc": f"โมเมนต์และเหล็กที่ตำแหน่ง: {p.label_th}",
            "formula": (f"M<sub>u</sub> = {p.coeff:.4f}·W<sub>u</sub>·S² = {p.mu_kgm:,.0f} kg·m/m "
                        f"→ A<sub>s</sub> = ρ·b·d = {p.as_req_cm2_m:.2f} cm²/m{warn}")})
    flex.append({
        "desc": "เลือกใช้เหล็กเสริมหลัก (ต่อเนื่องผ่านชานพัก)",
        "formula": (f"ใช้ {f.reinf_label_main} &nbsp; (A<sub>s,จัดให้</sub> = {f.as_provided_cm2_m:.2f} cm²/m, "
                    f"ระยะห่าง ≤ {f.main_spacing_max_cm:.0f} cm, {f.main_bar_count} เส้น/ช่วง)"),
        "result": "ผ่าน ✓" if f.main_reinf_ok else "ไม่ผ่าน ✗"})
    other = [
        {"desc": "เหล็กเสริมกันร้าว/กระจายแรง",
         "formula": (f"A<sub>st,ต้องการ</sub> = {f.ast_req_cm2_m:.2f} cm²/m → ใช้ {f.reinf_label_temp} "
                     f"(A<sub>st</sub> = {f.ast_provided_cm2_m:.2f} cm²/m, ระยะ ≤ {f.temp_spacing_max_cm:.0f} cm)"),
         "result": "ผ่าน ✓" if f.temp_reinf_ok else "ไม่ผ่าน ✗"},
        {"desc": "ตรวจสอบแรงเฉือน (Shear)",
         "formula": "V<sub>u</sub> ≤ φV<sub>c</sub> = φ·0.53√f'<sub>c</sub>·b·d",
         "sub": f"{f.vu_kg:,.0f} ≤ {f.phi_vc_kg:,.0f} kg",
         "result": "ผ่าน ✓" if f.shear_ok else "ไม่ผ่าน ✗"},
        {"desc": "ชานพัก (Landing) — น้ำหนักสำหรับออกแบบคาน/ผนังรองรับ",
         "formula": (f"พื้นที่ชานพัก = {result.landing_area_m2:.2f} m² , W<sub>u</sub> = {result.landing_wu_kg_m2:.0f} kg/m² "
                     f"→ น้ำหนักรวม (Service): DL = {result.landing_total_dl_kg:,.0f} kg, LL = {result.landing_total_ll_kg:,.0f} kg"),
         "note": "ชานพักออกแบบต่อเนื่องจากบันได (ใช้เหล็กชุดเดียวกัน) — ตัวเลขนี้ให้นำไปออกแบบคานรองรับเอง"},
    ]
    return [
        {"title": "เรขาคณิตบันได (Stair Geometry — ต่อช่วง)", "steps": geo},
        {"title": "การวิเคราะห์น้ำหนักบรรทุกและความหนา (Load & Thickness)", "steps": load},
        {"title": "การออกแบบเหล็กเสริมหลักรับแรงดัด (Flexural Design — Main Bars)", "steps": flex},
        {"title": "เหล็กเสริมกันร้าว แรงเฉือน และชานพัก (Temperature Steel, Shear & Landing)", "steps": other},
    ]

st.caption("บันได 2 ช่วง (ช่วงล่าง+ช่วงบน) เชื่อมด้วยชานพักกลาง — ตามข้อตกลง (2026-07-10): "
           "**ทั้งสองช่วงบังคับให้เท่ากันเสมอ** (แบ่งครึ่งจำนวนขั้น/ความสูงอัตโนมัติ) และ "
           "**ชานพักออกแบบแบบง่าย** (ต่อเนื่องจากบันได ใช้เหล็กชุดเดียวกัน ไม่คำนวณ Mu/As แยก)")

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "stu_form_gen" not in st.session_state:
    st.session_state["stu_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("stair_u_shape")
if _loaded_data is not None:
    st.session_state["stu_form_gen"] += 1
    st.session_state["_stu_loaded_data"] = _loaded_data
    st.session_state["_stu_loaded_code"] = _loaded_code
gen = st.session_state["stu_form_gen"]
_loaded = st.session_state.get("_stu_loaded_data") or {}
_loaded_code = st.session_state.get("_stu_loaded_code")

with st.container(border=True):
    st.markdown("**รหัสบันได (Stair No.)**")
    stair_name = st.text_input("รหัสบันได (Stair No.)", value=_loaded_code or "ST-02", key=f"stu_name_{gen}",
                                label_visibility="collapsed")

st.caption("ความต่อเนื่องของบันไดแต่ละช่วง: **Simply Supported** (ปลายวางบนคาน/ผนัง และชานพัก "
           "ซึ่งไม่ถือเป็นจุดต่อเนื่องทางโครงสร้างในโมดูลนี้)")

st.write("")

# การ์ดกรอบสี 3 ใบ: [ขนาดบันได (เขียว)] [เหล็กเสริม (น้ำเงิน)] [น้ำหนักบรรทุก (ส้ม)]
col1, col2, col3 = st.columns(3)

with col1:
    with input_card("ขนาดบันได (U-Shape)", color="green", icon="📐", key="stu-size"):
        n_riser_total = st.number_input(
            "จำนวนขั้นรวม n (ทั้งสองช่วง)", value=int(_loaded.get("n_riser_total", 18)),
            step=1, min_value=4,
            help="จำนวนลูกตั้งรวมทั้งช่วงล่าง+ช่วงบน — แบ่งครึ่งอัตโนมัติให้แต่ละช่วงเท่ากัน "
                 "(ถ้ากรอกเลขคี่ โปรแกรมจะปัดลงเป็นเลขคู่)",
            key=f"stu_nriser_{gen}")
        flight_length_m = st.number_input(
            "ความยาวช่วงพาด ต่อช่วง L1=L2 (ม.)", value=_loaded.get("flight_length_m", 2.00), step=0.05,
            min_value=0.10,
            help="L = (n/2-1) × ลูกนอน — ช่วงพาดแนวราบของ 1 ช่วงบันได (ทั้งสองช่วงเท่ากัน)",
            key=f"stu_flen_{gen}")
        landing_length_m = st.number_input(
            "ความยาวชานพัก (ม.)", value=_loaded.get("landing_length_m", 1.50), step=0.05,
            min_value=0.10,
            help="ความยาวชานพักตามทิศทางเดิน (แนวราบ)",
            key=f"stu_llen_{gen}")
        width_m = st.number_input(
            "ความกว้างบันได B (ม.)", value=_loaded.get("width_m", 1.00), step=0.05,
            min_value=0.10,
            help="ใช้คำนวณจำนวนเหล็กหลักที่ต้องใช้จริง และน้ำหนักรวมที่ถ่ายลงคานรองรับ "
                 "(ทั้งสองช่วงและชานพักกว้างเท่ากัน)",
            key=f"stu_width_{gen}")
        height_m = st.number_input(
            "ความสูงระหว่างชั้น H รวม (ม.)", value=_loaded.get("height_m", 3.60), step=0.05,
            min_value=0.20,
            help="H = n × ลูกตั้ง — ความสูงรวมทั้งสองช่วง (แบ่งครึ่งอัตโนมัติ)",
            key=f"stu_height_{gen}")
        _n_per_flight_preview = max(int(n_riser_total) // 2, 2)
        _rise_preview_cm = (height_m / 2.0) / _n_per_flight_preview * 100.0 if _n_per_flight_preview else 0.0
        _going_preview_cm = flight_length_m / max(_n_per_flight_preview - 1, 1) * 100.0
        st.caption(f"→ ต่อช่วง: {_n_per_flight_preview} ขั้น, ลูกตั้ง R = {_rise_preview_cm:.1f} cm., "
                   f"ลูกนอน G = {_going_preview_cm:.1f} cm. (คำนวณอัตโนมัติจาก L/H/n)")
        if int(n_riser_total) % 2 != 0:
            st.caption(f"⚠️ จำนวนขั้นรวมที่กรอก ({int(n_riser_total)}) เป็นเลขคี่ — จะถูกปัดลงเป็น "
                       f"{_n_per_flight_preview * 2} ขั้น ({_n_per_flight_preview} ขั้นต่อช่วง)")
        _t_idx = ALLOWED_THICKNESS_CM.index(_loaded["t_cm"]) if _loaded.get("t_cm") in ALLOWED_THICKNESS_CM else 3
        t = st.selectbox("ความหนาแผ่น waist, t (cm)", options=ALLOWED_THICKNESS_CM, index=_t_idx,
                          help="ความหนาวัดตั้งฉากกับแนวลาดของบันได — ใช้ร่วมกันทั้งช่วงบันไดและชานพัก",
                          key=f"stu_t_{gen}")

with col2:
    with input_card("เหล็กเสริม", color="blue", icon="🔩", key="stu-reinf"):
        st.markdown("**เหล็กเสริมหลัก (ตามแนวลาด — รับโมเมนต์)**")
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"stu_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        main_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กหลัก", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 2,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"stu_main_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
        _main_dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                          if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                          else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                     index=_main_dia_idx, key=f"stu_main_dia_{gen}")
        main_bar_spacing = st.number_input("ระยะห่างเหล็กหลัก (ซม.)", value=_loaded.get("main_bar_spacing_cm", 16.0),
                                            step=1.0, key=f"stu_main_spacing_{gen}")

        st.markdown("**เหล็กเสริมรอง (ตามแนวขั้น — กระจายแรง/กันร้าว)**")
        temp_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กเสริมรอง", options=_steel_options,
            index=_steel_options.index(_loaded["temp_steel_type"]) if _loaded.get("temp_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"stu_temp_steel_{gen}")
        temp_bar_dia_options = bar_dia_options_for_steel(temp_steel_type, BAR_DIAMETERS_MM)
        _temp_dia_idx = (temp_bar_dia_options.index(_loaded["temp_bar_dia_mm"])
                          if _loaded.get("temp_bar_dia_mm") in temp_bar_dia_options
                          else min(1, len(temp_bar_dia_options) - 1))
        temp_bar_dia = st.selectbox("ขนาดเหล็กเสริมรอง (มม.)", options=temp_bar_dia_options,
                                     index=_temp_dia_idx, key=f"stu_temp_dia_{gen}")
        temp_bar_spacing = st.number_input("ระยะห่างเหล็กเสริมรอง (ซม.)", value=_loaded.get("temp_bar_spacing_cm", 14.0),
                                            step=1.0, key=f"stu_temp_spacing_{gen}")
        st.caption("เหล็กเสริมหลัก/เสริมรองชุดนี้ใช้ต่อเนื่องผ่านชานพักด้วย (ไม่มีเหล็กชุดใหม่สำหรับชานพัก)")

with col3:
    with input_card("น้ำหนักบรรทุก", color="orange", icon="⚖️", key="stu-load"):
        wD = st.number_input("SDL (kg/m²)", value=_loaded.get("wD_kg_m2", 100.0), step=10.0,
                              help="Superimposed Dead Load — ผิวสำเร็จ/ปูน/กระเบื้องขั้นบันได+ชานพัก "
                                   "(ไม่รวมน้ำหนักตัวเองของ waist/ขั้นบันได — โปรแกรมคำนวณให้อัตโนมัติจากเรขาคณิต)",
                              key=f"stu_wd_{gen}")
        wL = st.number_input("LL (kg/m²)", value=_loaded.get("wL_kg_m2", 200.0), step=10.0,
                              help="Live Load — ค่าเริ่มต้น 200 กก./ตร.ม. ตามตารางน้ำหนักบรรทุกจร กฎกระทรวง 2566 "
                                   "ประเภท \"ระเบียง และบันได\"",
                              key=f"stu_wl_{gen}")
        st.caption("- ขอบเขต: ไม่ตรวจสอบสัดส่วนขั้นบันได/ชานพักตามกฎหมายอาคาร/สถาปัตยกรรม "
                   "(ขนาดชานพักขั้นต่ำ, ราวจับ ฯลฯ) — เฉพาะการออกแบบโครงสร้าง (Strength Design)")
        st.caption("- ไม่ออกแบบคาน/ผนังรองรับชานพัก (landing beam) แยกต่างหาก — แสดงน้ำหนักตัวเองของชานพัก "
                   "(informational) ให้วิศวกรนำไปใช้ออกแบบเอง")

inp = StairUShapeInput(
    fc_ksc=fc,
    main_steel_type=main_steel_type,
    temp_steel_type=temp_steel_type,
    main_bar_dia_mm=main_bar_dia,
    main_bar_spacing_cm=main_bar_spacing,
    temp_bar_dia_mm=temp_bar_dia,
    temp_bar_spacing_cm=temp_bar_spacing,
    wD_kg_m2=wD,
    wL_kg_m2=wL,
    n_riser_total=int(n_riser_total),
    flight_length_m=flight_length_m,
    landing_length_m=landing_length_m,
    width_m=width_m,
    height_m=height_m,
    t_cm=t,
)

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ (Compute)", key="npk-btn-compute-usw", type="primary", use_container_width=True):
        st.session_state["stu_input"] = inp
        st.session_state["stu_result"] = calc_stair_u(inp)
        st.session_state["stu_project"] = {"stair_name": stair_name}
        mark_calc_pending_sync("stu")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-usw", use_container_width=True):
        saved_code = save_item("stair_u_shape", stair_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสบันได (Stair No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("stu_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_stu", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "stu_result" in st.session_state:
    inp = st.session_state["stu_input"]
    result = st.session_state["stu_result"]
    project = st.session_state["stu_project"]
    flight = result.flight

    st.header(f"ผลการคำนวณ — {project['stair_name']}")

    if result.n_riser_rounded:
        st.warning(f"จำนวนขั้นรวมที่กรอก ({inp.n_riser_total:.0f} ขั้น) เป็นเลขคี่ — ปัดลงเป็น "
                   f"{result.n_riser_total_used:.0f} ขั้น ({result.n_riser_per_flight:.0f} ขั้นต่อช่วง) "
                   "เพื่อให้ทั้งสองช่วงเท่ากันทุกประการ")

    metric_card_row([
        ("น้ำหนักบรรทุกใช้งาน Wu", f"{flight.wu_kg_m2:.0f}", "kgf/m² (ต่อช่วง)", None),
        ("ตรวจสอบความหนา waist", f"{flight.tmin_cm:.2f}", f"cm. (ใช้ {inp.t_cm:.1f} cm.)", flight.t_ok),
        ("แรงเฉือน Vu / φVc", f"{flight.vu_kg:.0f}", f"kgf (φVc={flight.phi_vc_kg:.0f})", flight.shear_ok),
        ("เหล็กเสริมหลัก", f"{flight.as_provided_cm2_m:.2f}", "cm²/m", flight.main_reinf_ok),
        ("เหล็กเสริมรอง", f"{flight.ast_provided_cm2_m:.2f}", "cm²/m", flight.temp_reinf_ok),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**เรขาคณิตบันได & น้ำหนักบรรทุก**")
            st.write(f"L1 = L2 = {inp.flight_length_m:.2f} m., ชานพัก = {inp.landing_length_m:.2f} m., "
                     f"B = {inp.width_m:.2f} m., H รวม = {inp.height_m:.2f} m.")
            st.write(f"จำนวนขั้นรวม n = {result.n_riser_total_used:.0f} ขั้น "
                     f"({result.n_riser_per_flight:.0f} ขั้น/ช่วง, ลูกนอน {flight.n_going:.0f} ขั้น/ช่วง)")
            st.write(f"ลูกตั้ง R = {flight.rise_cm:.1f} cm., ลูกนอน G = {flight.going_cm:.1f} cm. "
                     f"(ทั้งสองช่วงเท่ากันทุกประการ)")
            st.write(f"มุมลาด = {flight.slope_deg:.1f}°, ความยาวจริงตามแนวลาด (ต่อช่วง) = {flight.incline_length_m:.2f} m.")
            st.write(f"DL ตัวเอง: waist = {flight.dead_load_waist_kg_m2:.0f} kg/m², "
                     f"ขั้นบันได = {flight.dead_load_steps_kg_m2:.0f} kg/m² "
                     f"(รวม = {flight.dead_load_self_kg_m2:.0f} kg/m²)")
            st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {flight.wu_kg_m2:.0f} kg/m²")

    with dcol2:
        with st.container(border=True):
            st.markdown("**โมเมนต์และเหล็กเสริมหลัก (ต่อช่วง)**")
            for p in flight.positions:
                if not p.active:
                    st.write(f"- {p.label_th}: ไม่มีการออกแบบ (ปลายไม่ต่อเนื่อง)")
                else:
                    warn = "  ⚠️ หน้าตัดเล็กไป (เกิน ρmax)" if p.over_reinforced else ""
                    st.write(f"- {p.label_th}: Mu={p.mu_kgm:.0f} kg-m/m, As ต้องการ={p.as_req_cm2_m:.2f} cm²/m{warn}")
            st.write(f"**เหล็กที่ใช้จริง: {flight.reinf_label_main}** (ต่อเนื่องผ่านชานพักด้วย) "
                     f"(As={flight.as_provided_cm2_m:.2f} cm²/m, ระยะห่างสูงสุดที่ยอมให้={flight.main_spacing_max_cm:.1f} cm.)")
            st.write(f"จำนวนเหล็กหลักที่ต้องใช้จริง ตลอดความกว้าง B = {inp.width_m:.2f} m. (ต่อช่วง) → "
                     f"**{flight.main_bar_count} เส้น**")

    with dcol3:
        with st.container(border=True):
            st.markdown("**เหล็กเสริมรอง & แรงเฉือน (ต่อช่วง)**")
            st.write(f"Ast ต้องการ = {flight.ast_req_cm2_m:.2f} cm²/m")
            st.write(f"เหล็กที่ใช้จริง: {flight.reinf_label_temp} (Ast={flight.ast_provided_cm2_m:.2f} cm²/m, "
                     f"ระยะห่างสูงสุด={flight.temp_spacing_max_cm:.1f} cm.)")
            st.write(f"จำนวนเหล็กเสริมรองที่ต้องใช้จริง ตลอดความยาวลาดจริง = {flight.incline_length_m:.2f} m. (ต่อช่วง) "
                     f"→ **{flight.temp_bar_count} เส้น**")
            st.write(f"Vu = {flight.vu_kg:.0f} kg., φVc = {flight.phi_vc_kg:.0f} kg.")
            st.write(f"น้ำหนักลงคาน (Service, ต่อ 1 ม.): DL={flight.dl_on_beam_kg_m:.0f} kg/m., LL={flight.ll_on_beam_kg_m:.0f} kg/m.")
            st.write(f"น้ำหนักลงคานรวม (Service, ตลอดความกว้าง B={inp.width_m:.2f} m.): "
                     f"DL={flight.dl_on_beam_total_kg:.0f} kg., LL={flight.ll_on_beam_total_kg:.0f} kg.")

    with st.container(border=True):
        st.markdown("**ชานพัก — น้ำหนักตัวเอง (Informational)**")
        st.write(f"พื้นที่ชานพัก = {result.landing_area_m2:.2f} m² (B×ความยาวชานพัก), "
                 f"Wu ชานพัก = {result.landing_wu_kg_m2:.0f} kg/m²")
        st.write(f"น้ำหนักรวม (Service): DL = {result.landing_total_dl_kg:.0f} kg., LL = {result.landing_total_ll_kg:.0f} kg.")
        st.caption("ตัวเลขนี้ให้วิศวกรนำไปใช้ออกแบบคาน/ผนังรองรับชานพักเอง — อยู่นอกขอบเขตของโมดูลนี้")

    st.write("")
    st.subheader("วิธีการคำนวณและสูตรที่ใช้")
    render_calc_sheet(_build_calc_sections(inp, result))

    st.subheader("(6) แบบรายละเอียด — รูปด้านข้าง (Developed Elevation)")
    elevation_png = draw_stair_u_shape_detail_template_png(inp, result)
    # ลดสัดส่วนการแสดงผลแบบขยายลง 30% (แสดงที่ 70% ของความกว้าง) ตามคำขอผู้ใช้ 2026-07-13
    _el_l, _el_r = st.columns([7, 3])
    with _el_l:
        st.image(elevation_png, use_container_width=True)

    st.caption("เหล็กมุม และเหล็กยึดขึ้น เป็นเหล็กเสริมพิเศษ (secondary/constructive) ที่ไม่มีการคำนวณ"
               f"ออกแบบแยกในโมดูลนี้ — ใช้ขนาด/ระยะห่างเดียวกับเหล็กเสริมรอง ({flight.reinf_label_temp}) "
               "ตามธรรมเนียมงานเสริมเหล็กบันไดทั่วไป — เหล็กเสริมหลัก/เสริมรองวิ่งต่อเนื่องจากชานพักเข้าสู่ช่วง"
               "บันได ไม่มีจุดตัดที่ชานพัก (รูปนี้ใช้แทนได้ทั้งจุดต่อชานพัก-ช่วงล่าง และจุดต่อชานพัก-ช่วงบน "
               "เนื่องจากทั้งสองช่วงเหมือนกันทุกประการ) วิศวกรผู้ควบคุมงานควรตรวจสอบ/ปรับตามมาตรฐานของแต่ละโครงการ")

    report_html = build_stair_u_shape_report_html(
        project, inp, result, elevation_png,
        detail_png=None,
        project_info=st.session_state.get("project_info"),
        logo_bytes=st.session_state.get("project_logo_bytes"),
        logo_mime=st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("stu", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['stair_name']}")
