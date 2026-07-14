"""
Module 4.1 — เสาสี่เหลี่ยม (Rectangular Tied Column)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.column_tied import (
    ColumnTiedInput, calculate as calc_column,
    COLUMN_SIZE_CM_OPTIONS, COLUMN_BAR_DIAMETERS_MM, TIE_DIAMETERS_MM,
    DEFAULT_COVER_CM, BETA_DNS_DEFAULT,
)
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import draw_column_section_png, draw_column_interaction_png
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_column_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row, render_calc_sheet,
)


def _build_calc_sections(inp, result):
    """วิธีการคำนวณและสูตรที่ใช้ (เสาสี่เหลี่ยม ปลอกเดี่ยว) — ดึงค่าจาก result (ไม่คำนวณซ้ำ)"""
    s = result.slenderness
    tie = result.tie
    axial = [
        {"desc": "พื้นที่หน้าตัดเสา (Gross area)",
         "formula": "A<sub>g</sub> = b × h", "sub": f"{inp.b_cm:.0f} × {inp.h_cm:.0f}",
         "result": f"{result.ag_cm2:,.0f} cm²"},
        {"desc": "ขอบเขตเหล็กยืน (1%–8% ของ A<sub>g</sub>)",
         "formula": "A<sub>s,min</sub> = 0.01A<sub>g</sub> , A<sub>s,max</sub> = 0.08A<sub>g</sub>",
         "result": f"{result.as_min_cm2:.1f} – {result.as_max_cm2:.1f} cm²"},
        {"desc": "เลือกใช้เหล็กยืน",
         "formula": (f"ใช้ {result.reinf_label} → A<sub>s</sub> = {result.as_provided_cm2:.2f} cm² "
                     f"(ρ<sub>g</sub> = {result.rho_g*100:.2f}%)"),
         "result": "ผ่าน ✓" if result.as_min_cm2 <= result.as_provided_cm2 <= result.as_max_cm2 else "ตรวจสอบ ρg"},
        {"desc": "กำลังรับแรงตามแนวแกนสูงสุด (Axial capacity)",
         "formula": "P<sub>o</sub> = 0.85f'<sub>c</sub>(A<sub>g</sub>−A<sub>s</sub>) + f<sub>y</sub>A<sub>s</sub>",
         "result": f"{result.po_kg:,.0f} kg → φP<sub>n,max</sub> = 0.80·φ·P<sub>o</sub> = {result.phi_pn_max_kg:,.0f} kg"},
    ]
    slender = [
        {"desc": "ตรวจสอบความชะลูด (Slenderness)",
         "formula": "kL<sub>u</sub>/r &nbsp;(เกณฑ์เสาสั้น ≤ 22)",
         "result": f"{s.klu_r:.1f} → " + ("เสาสั้น (ไม่ต้องขยายโมเมนต์)" if s.is_short else "เสาชะลูด (ต้องขยายโมเมนต์)")},
    ]
    if not s.is_short:
        slender.append(
            {"desc": "ตัวขยายโมเมนต์ (Moment magnification)",
             "formula": (f"EI = {s.ei_tm2:,.1f} t·m² , P<sub>c</sub> = {s.pc_ton:,.1f} ton , "
                         f"δ<sub>ns</sub> = C<sub>m</sub>/(1−P<sub>u</sub>/0.75P<sub>c</sub>) = {s.delta_ns:.2f}"),
             "result": f"M<sub>u,design</sub> = δ<sub>ns</sub>·M<sub>u</sub> = {s.mu_design_kgm:,.0f} kg·m"})
    pm = [
        {"desc": f"กำลังรับโมเมนต์ที่ระดับ P<sub>u</sub> = {inp.pu_kg:,.0f} kg (จาก P-M Interaction Diagram)",
         "formula": "φM<sub>n</sub> (ที่ P<sub>u</sub>)", "result": f"{result.phi_mn_capacity_at_pu_kgm:,.0f} kg·m"},
        {"desc": "อัตราส่วนการใช้งาน (Utilization)",
         "formula": "M<sub>u,design</sub> / φM<sub>n</sub>",
         "sub": f"{s.mu_design_kgm:,.0f} / {result.phi_mn_capacity_at_pu_kgm:,.0f}",
         "result": f"{result.utilization:.2f} " + ("(≤ 1.0) ผ่าน ✓" if result.utilization <= 1.0 else "(> 1.0) ไม่ผ่าน ✗")},
        {"desc": "ผลการออกแบบโดยรวม",
         "formula": "ตรวจสอบกำลังรับแรงตามแนวแกนและโมเมนต์ร่วมกัน",
         "result": "ผ่าน ✓" if result.design_ok else "ไม่ผ่าน ✗"},
    ]
    ties = [
        {"desc": "ระยะเรียงเหล็กปลอกสูงสุด (Tie spacing)",
         "formula": "s<sub>max</sub> = min(16⌀เหล็กยืน, 48⌀ปลอก, ด้านเล็กสุดของเสา)",
         "sub": f"min({tie.s_max_16db_cm:.0f}, {tie.s_max_48dt_cm:.0f}, {tie.s_max_dim_cm:.0f})",
         "result": f"{tie.s_max_cm:.1f} cm"},
        {"desc": "เลือกใช้เหล็กปลอก",
         "formula": (f"ใช้ {result.reinf_label_tie} &nbsp; (ระยะที่ใช้ {inp.tie_spacing_use_cm:.0f} cm "
                     f"{'≤' if tie.tie_ok else '>'} s<sub>max</sub>)"),
         "result": "ผ่าน ✓" if tie.tie_ok else "ไม่ผ่าน ✗"},
    ]
    return [
        {"title": "เหล็กเสริมตามแนวแกนและกำลังรับแรงอัด (Longitudinal Steel & Axial Capacity)", "steps": axial},
        {"title": "ความชะลูดและการขยายโมเมนต์ (Slenderness & Moment Magnification)", "steps": slender},
        {"title": "ตรวจสอบกำลังรับแรงอัดร่วมโมเมนต์ (P-M Interaction Check)", "steps": pm},
        {"title": "การออกแบบเหล็กปลอก (Tie Design)", "steps": ties},
    ]

inject_card_css()
st.header("4.1 เสาสี่เหลี่ยม (Rectangular Tied Column)")

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "column_form_gen" not in st.session_state:
    st.session_state["column_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("column_tied")
if _loaded_data is not None:
    st.session_state["column_form_gen"] += 1
    st.session_state["_column_loaded_data"] = _loaded_data
    st.session_state["_column_loaded_code"] = _loaded_code
gen = st.session_state["column_form_gen"]
_loaded = st.session_state.get("_column_loaded_data") or {}
_loaded_code = st.session_state.get("_column_loaded_code")

# แถวแรก: กล่องเล็กสำหรับรหัสเสา (identifying field) — ตามแนวทางเดียวกับหน้า 1.3 พื้นสองทาง
row1_c1, _row1_spacer = st.columns([1.0, 2.8])
with row1_c1:
    with st.container(border=True):
        st.markdown("**รหัสเสา (Column No.)**")
        column_name = st.text_input("รหัสเสา (Column No.)", value=_loaded_code or "C-01",
                                     key=f"col_name_{gen}", label_visibility="collapsed")

st.write("")

# แถวสอง: 4 การ์ดกรอบสี [วัสดุ (น้ำเงิน)] [แรงที่ต้องการออกแบบ (ส้ม)] [ขนาดหน้าตัดเสา (เขียว)]
# [เหล็กปลอก & ความชะลูด (เขียวน้ำทะเล)]
col1, col2, col3, col4 = st.columns(4)

with col1:
    with input_card("วัสดุ / เหล็กเสริมหลัก", color="blue", icon="🧱", key="ct-material"):
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"col_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        main_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กหลัก", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 2,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"col_main_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, COLUMN_BAR_DIAMETERS_MM)
        _main_dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                          if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                          else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กหลัก (มม.)", options=main_bar_dia_options,
                                     index=_main_dia_idx, key=f"col_main_dia_{gen}")

with col2:
    with input_card("แรงที่ต้องการออกแบบ", color="orange", icon="⚖️", key="ct-load"):
        Lu_m = st.number_input("ความสูงช่วงเสาไม่มีค้ำยัน Lu (m)", value=_loaded.get("Lu_m", 3.0), step=0.1,
                                help="ใช้ตรวจสอบความชะลูด (slenderness) เบื้องต้นเท่านั้น", key=f"col_Lu_{gen}")
        pu = st.number_input("Pu — แรงตามแนวแกน (kg)", value=_loaded.get("pu_kg", 20000.0), step=500.0,
                              help="แรงตามแนวแกนที่ผ่านการคูณ load factor แล้ว (factored)", key=f"col_pu_{gen}")
        mu = st.number_input("Mu — โมเมนต์ดัด ทิศทางเดียว (kg-m)", value=_loaded.get("mu_kgm", 1000.0), step=100.0,
                              help="โมเมนต์รอบแกนขนานด้าน b (uniaxial) — ยังไม่รองรับโมเมนต์สองทิศทาง",
                              key=f"col_mu_{gen}")

with col3:
    with input_card("ขนาดหน้าตัดเสา", color="green", icon="📐", key="ct-size"):
        _b_idx = COLUMN_SIZE_CM_OPTIONS.index(_loaded["b_cm"]) if _loaded.get("b_cm") in COLUMN_SIZE_CM_OPTIONS else 2
        b_cm = st.selectbox("ความกว้างเสา b (cm)", options=COLUMN_SIZE_CM_OPTIONS, index=_b_idx,
                             help="ด้านตั้งฉากกับทิศทางโมเมนต์ดัด", key=f"col_b_{gen}")
        _h_idx = COLUMN_SIZE_CM_OPTIONS.index(_loaded["h_cm"]) if _loaded.get("h_cm") in COLUMN_SIZE_CM_OPTIONS else 2
        h_cm = st.selectbox("ความลึกเสา h (cm)", options=COLUMN_SIZE_CM_OPTIONS, index=_h_idx,
                             help="ด้านขนานกับทิศทางโมเมนต์ดัด", key=f"col_h_{gen}")
        cover_cm = st.number_input("ระยะหุ้มคอนกรีต cv (ซม.)", value=_loaded.get("cover_cm", DEFAULT_COVER_CM),
                                    step=0.5, help="ระยะหุ้มคอนกรีตถึงเหล็กปลอก", key=f"col_cover_{gen}")

with col4:
    with input_card("เหล็กปลอก & ความชะลูด", color="teal", icon="🔗", key="ct-tie"):
        tie_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็กปลอก", options=_steel_options,
            index=_steel_options.index(_loaded["tie_steel_type"]) if _loaded.get("tie_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"col_tie_steel_{gen}")
        tie_bar_dia_options = bar_dia_options_for_steel(tie_steel_type, TIE_DIAMETERS_MM)
        _tie_dia_idx = (tie_bar_dia_options.index(_loaded["tie_bar_dia_mm"])
                         if _loaded.get("tie_bar_dia_mm") in tie_bar_dia_options
                         else min(0, len(tie_bar_dia_options) - 1))
        tie_bar_dia = st.selectbox("ขนาดเหล็กปลอก (มม.)", options=tie_bar_dia_options,
                                    index=_tie_dia_idx, key=f"col_tie_dia_{gen}")
        tie_spacing = st.number_input("ระยะห่างเหล็กปลอกที่ใช้จริง (ซม.)", value=_loaded.get("tie_spacing_use_cm", 15.0),
                                       step=1.0, key=f"col_tie_spacing_{gen}")
        beta_dns = st.number_input("βdns (สัดส่วนน้ำหนักบรรทุกคงค้าง)", value=_loaded.get("beta_dns", BETA_DNS_DEFAULT),
                                    step=0.05, min_value=0.0, max_value=1.0,
                                    help="สัดส่วนน้ำหนักบรรทุกคงค้าง(DL)ต่อน้ำหนักบรรทุกออกแบบรวม — ใช้คำนวณขยาย"
                                         "โมเมนต์ (moment magnification) เมื่อเสาชะลูดเท่านั้น (kLu/r > 22)",
                                    key=f"col_beta_dns_{gen}")

with st.container(border=True):
    st.markdown("**หมายเหตุขอบเขตของโมดูลนี้**")
    st.caption("- ออกแบบเหล็กเสริมอัตโนมัติ (auto-design) ด้วยวิธี P-M Interaction Diagram "
               "(strain compatibility) — ไม่ใช่การตรวจสอบ (check) หน้าตัด/เหล็กที่กำหนดเอง")
    st.caption("- รองรับเฉพาะโมเมนต์ทิศทางเดียว (uniaxial) — ยังไม่รองรับโมเมนต์สองทิศทาง (biaxial)")
    st.caption("- ตรวจสอบความชะลูดด้วย kLu/r &le; 22 (เกณฑ์อนุรักษ์นิยม) ถ้าเกินเกณฑ์จะขยายโมเมนต์"
               "อัตโนมัติ (moment magnification ตาม ACI 318 6.6.4.5)")
    st.caption("- ยังไม่รวมการออกแบบรับแรงเฉือนด้านข้าง (ขอบเขตอาคารบ้านพักอาศัยตามกฎกระทรวง 2566)")

inp = ColumnTiedInput(
    fc_ksc=fc,
    main_steel_type=main_steel_type,
    tie_steel_type=tie_steel_type,
    b_cm=b_cm,
    h_cm=h_cm,
    Lu_m=Lu_m,
    pu_kg=pu,
    mu_kgm=mu,
    main_bar_dia_mm=main_bar_dia,
    tie_bar_dia_mm=tie_bar_dia,
    tie_spacing_use_cm=tie_spacing,
    cover_cm=cover_cm,
    beta_dns=beta_dns,
)

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ (Compute)", key="npk-btn-compute-ct", type="primary", use_container_width=True):
        st.session_state["column_input"] = inp
        st.session_state["column_result"] = calc_column(inp)
        st.session_state["column_project"] = {"column_name": column_name}
        mark_calc_pending_sync("ct")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-ct", use_container_width=True):
        saved_code = save_item("column_tied", column_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสเสา (Column No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("ct_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_ct", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "column_result" in st.session_state:
    inp = st.session_state["column_input"]
    result = st.session_state["column_result"]
    project = st.session_state["column_project"]

    st.header(f"ผลการคำนวณ — {project['column_name']}")

    if not result.design_ok:
        st.error(f"⚠️ {result.design_fail_reason}")
    elif result.design_fail_reason:
        st.warning(result.design_fail_reason)

    metric_card_row([
        ("ผลการออกแบบโดยรวม", "ผ่าน" if result.design_ok else "ไม่ผ่าน", "-", result.design_ok),
        ("ความชะลูด kLu/r", f"{result.slenderness.klu_r:.1f}", "เกณฑ์ ≤ 22 (เตือนเท่านั้น)",
         True if result.slenderness.is_short else "warn"),
        ("อัตราส่วนใช้งาน Mu/φMn", f"{result.utilization:.2f}",
         f"φMn={result.phi_mn_capacity_at_pu_kgm:,.0f} kg-m.", result.utilization <= 1.0),
        ("เหล็กปลอก S ที่ใช้จริง", f"{inp.tie_spacing_use_cm:.1f}",
         f"cm. (Smax={result.tie.s_max_cm:.1f})", result.tie.tie_ok),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**ความชะลูด (Slenderness) & Moment Magnification**")
            st.write(f"kLu/r = {result.slenderness.klu_r:.1f} "
                     f"({'เสาสั้น ✅' if result.slenderness.is_short else 'เสาชะลูด ⚠️'})")
            if not result.slenderness.is_short:
                s = result.slenderness
                st.caption(f"EI = {s.ei_tm2:,.1f} t-m², Pc = {s.pc_ton:,.1f} ton, "
                           f"δns = {s.delta_ns:.2f} (Cm={s.cm_factor:.1f}, βdns={inp.beta_dns:.2f})")
            else:
                st.caption("เสาสั้น — ไม่ต้องขยายโมเมนต์ (δns = 1.0)")

    with dcol2:
        with st.container(border=True):
            st.markdown("**เหล็กเสริมตามแนวแกน**")
            st.write(f"As,min–As,max = {result.as_min_cm2:.1f} – {result.as_max_cm2:.1f} cm²")
            st.write(f"Po = {result.po_kg:,.0f} kg., φPn,max = {result.phi_pn_max_kg:,.0f} kg.")
            st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label}** "
                     f"(As={result.as_provided_cm2:.2f} cm², ρg={result.rho_g*100:.2f}%)")

    with dcol3:
        with st.container(border=True):
            st.markdown("**กำลังที่ระดับ Pu & เหล็กปลอก (Tie)**")
            st.write(f"φMn (ที่ Pu={inp.pu_kg:,.0f} kg.) = {result.phi_mn_capacity_at_pu_kgm:,.0f} kg-m.")
            st.write(f"Mu ที่กรอก = {inp.mu_kgm:,.0f} kg-m.")
            if not result.slenderness.is_short and not result.slenderness.pu_exceeds_075pc:
                st.write(f"Mu ที่ใช้ตรวจ (ขยายแล้ว) = {result.slenderness.mu_design_kgm:,.0f} kg-m.")
            st.write(f"S_max ที่คำนวณได้ = {result.tie.s_max_cm:.1f} cm.")
            st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_tie}**")

    st.write("")
    st.subheader("วิธีการคำนวณและสูตรที่ใช้")
    render_calc_sheet(_build_calc_sections(inp, result))

    st.subheader("รูปตัดเสา (Column Section)")
    section_png = draw_column_section_png(
        inp.b_cm, inp.h_cm, result.bar_layers, inp.main_bar_dia_mm, result.main_bar_type,
        inp.tie_bar_dia_mm, inp.tie_spacing_use_cm, result.tie_bar_type, inp.cover_cm)
    # ขยายรูปตัดเสาให้ใหญ่ขึ้นและวางไว้ตรงกลาง (คอลัมน์กลาง ~75% ของความกว้าง) ตามคำขอผู้ใช้ 2026-07-12
    _sec_l, _sec_mid, _sec_r = st.columns([1, 6, 1])
    with _sec_mid:
        st.image(section_png, use_container_width=True, caption="Column Section")

    st.subheader("กราฟ P-M Interaction Diagram")
    interaction_png = draw_column_interaction_png(
        result.interaction_points, inp.pu_kg, result.slenderness.mu_design_kgm,
        result.phi_mn_capacity_at_pu_kgm, mu_applied_kgm=inp.mu_kgm,
        b_cm=inp.b_cm, h_cm=inp.h_cm)
    # ลดสเกลกราฟ P-M ลง ~40% (แสดงที่คอลัมน์กลาง ~60% ของความกว้าง) + วางตรงกลาง ตามคำขอผู้ใช้ 2026-07-12
    _pm_l, _pm_mid, _pm_r = st.columns([1, 3, 1])
    with _pm_mid:
        st.image(interaction_png, use_container_width=True)

    report_html = build_column_report_html(
        project, inp, result, section_png, interaction_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("ct", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['column_name']}")
