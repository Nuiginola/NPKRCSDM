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
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_gs_report_html
from common.ui_style import inject_card_css, input_card, metric_card_row, render_calc_sheet


def _build_calc_sections(inp, result):
    """วิธีการคำนวณและสูตรที่ใช้ (พื้นวางบนดิน) — เหล็กกันร้าว/หดตัว คิดจาก 3 วิธี เลือกมากสุด
    ดึงค่าจาก result (ไม่คำนวณซ้ำ)"""
    load = [
        {"desc": "น้ำหนักบรรทุกประลัย (Factored load)",
         "formula": "W<sub>u</sub> = 1.4(DL + SDL) + 1.7LL",
         "sub": f"DL(พื้น)={result.dead_load_kg_m2:.0f}",
         "result": f"{result.wu_kg_m2:.0f} kg/m²"},
        {"desc": "ตรวจสอบสัดส่วนขนาดพื้น (ด้านยาว ≥ ด้านสั้น)",
         "formula": "L ≥ S", "sub": f"{inp.L_m:.1f} ≥ {inp.S_m:.1f} m",
         "result": "ผ่าน ✓" if result.L_ge_S_ok else "ไม่ผ่าน ✗"},
    ]
    steel = [
        {"desc": "วิธีที่ 1 — เหล็กกันการหดตัว/อุณหภูมิ (Temperature/Shrinkage)",
         "formula": "A<sub>s,temp</sub> = ρ<sub>temp</sub> · b · t",
         "result": f"{result.as_temperature_cm2_m:.2f} cm²/m"},
        {"desc": "วิธีที่ 2 — แรงเสียดทานพื้นดิน (Subgrade Drag)",
         "formula": "A<sub>s,drag</sub> = F·L·W<sub>u</sub> / (1.43·f<sub>y</sub>) &nbsp;(F = 1.5)",
         "result": f"{result.as_subgrade_drag_cm2_m:.2f} cm²/m"},
        {"desc": "วิธีที่ 3 — วิธี PCA (พื้นที่มีรถวิ่งผ่าน)",
         "formula": "A<sub>s,PCA</sub> = 1800·S·t / f<sub>y</sub>",
         "result": f"{result.as_pca_cm2_m:.2f} cm²/m"},
        {"desc": "เลือกใช้เหล็กเสริม (ต้อง ≥ ทั้ง 3 วิธี)",
         "formula": f"ใช้ {result.reinf_label} → A<sub>s,จัดให้</sub> = {result.as_provided_cm2_m:.2f} cm²/m",
         "result": "ผ่าน ✓" if result.all_reinf_ok else "ไม่ผ่าน ✗"},
    ]
    return [
        {"title": "การวิเคราะห์น้ำหนักบรรทุกและขนาดพื้น (Load & Geometry)", "steps": load},
        {"title": "เหล็กเสริมกันการหดตัว/อุณหภูมิ — 3 วิธี (Shrinkage/Temperature Steel)", "steps": steel},
    ]

inject_card_css()
st.header("1.1 พื้นวางบนดิน (Slab on Ground)")

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง) — ถ้ามีคำขอโหลด
# ค้างอยู่ ให้เพิ่มเลขรุ่นฟอร์ม (form-gen) เพื่อบังคับให้ widget ทุกตัวสร้างใหม่ด้วยค่า
# จากรายการที่บันทึกไว้ (ใช้เทคนิคเดียวกับหน้าข้อมูลโครงการ — pi_form_gen)
if "gs_form_gen" not in st.session_state:
    st.session_state["gs_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("slab_on_ground")
if _loaded_data is not None:
    st.session_state["gs_form_gen"] += 1
    st.session_state["_gs_loaded_data"] = _loaded_data
    st.session_state["_gs_loaded_code"] = _loaded_code
gen = st.session_state["gs_form_gen"]
_loaded = st.session_state.get("_gs_loaded_data") or {}
_loaded_code = st.session_state.get("_gs_loaded_code")

# แถวแรก: 2 กล่องเรียงกัน [รหัสพื้น] [ลักษณะพื้น] — ตามแนวทางเดียวกับหน้า 1.3 พื้นสองทาง
row1_c1, row1_c2 = st.columns([1.0, 2.0])
with row1_c1:
    with st.container(border=True):
        st.markdown("**รหัสพื้น (Slab No.)**")
        slab_name = st.text_input(
            "รหัสพื้น (Slab No.)", value=_loaded_code or "GS1", key=f"gs_slabname_{gen}",
            label_visibility="collapsed",
            help="ข้อมูลโครงการ/เจ้าของ/สถานที่/วิศวกร จะย้ายไปอยู่หน้าข้อมูลโครงการกลาง (ใช้ร่วมกันทุกหมวด) ในภายหลัง")
with row1_c2:
    with st.container(border=True):
        st.markdown("**ลักษณะพื้น**")
        _context_options = ["IN", "OUT"]
        slab_context = st.radio("ลักษณะพื้น", options=_context_options,
                                 index=_context_options.index(_loaded.get("slab_context", "IN"))
                                 if _loaded.get("slab_context") in _context_options else 0,
                                 format_func=lambda x: "พื้นภายในอาคาร / มีโครงสร้างคาน (IN)" if x == "IN"
                                 else "พื้นภายนอกอาคาร / ไม่มีคาน (OUT)",
                                 horizontal=True, key=f"gs_context_{gen}", label_visibility="collapsed")

st.write("")

# แถวสอง: 3 การ์ดกรอบสี [กำลังวัสดุ (น้ำเงิน)] [น้ำหนักบรรทุก (ส้ม)] [ขนาดพื้น (เขียว)]
col1, col2, col3 = st.columns(3)

with col1:
    with input_card("กำลังวัสดุ", color="blue", icon="🔩", key="gs-material"):
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("กำลังอัดประลัยคอนกรีต f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้", key=f"gs_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        steel_type = st.selectbox(
            "ชนิดเหล็กเสริม", options=_steel_options,
            index=_steel_options.index(_loaded["steel_type"]) if _loaded.get("steel_type") in _steel_options else 0,
            format_func=lambda k: k, help="fy ของแต่ละชั้นคุณภาพ: " +
            ", ".join(f"{k}={v:.0f}" for k, v in GS_STEEL_FY_KSC.items()) + " ksc",
            key=f"gs_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(steel_type, GS_BAR_DIAMETERS_MM)
        _dia_default_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                             if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                             else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = st.selectbox("ขนาดเหล็กเสริม (มม.)", options=main_bar_dia_options,
                                     index=_dia_default_idx, key=f"gs_dia_{gen}")
        main_bar_spacing = st.number_input("ระยะห่างเหล็กเสริม (ซม.)", value=_loaded.get("main_bar_spacing_cm", 15.0),
                                            step=1.0, key=f"gs_spacing_{gen}")

with col2:
    with input_card("น้ำหนักบรรทุก", color="orange", icon="⚖️", key="gs-load"):
        wD = st.number_input("SDL (kg/m²)", value=_loaded.get("wD_kg_m2", 120.0), step=10.0,
                              help="Superimposed Dead Load — น้ำหนักวัสดุปูพื้น/ผิวพื้น ไม่รวมน้ำหนักพื้นคอนกรีตเอง "
                                   "(โปรแกรมคำนวณ Dead Load จากความหนาให้อัตโนมัติ)",
                              key=f"gs_wd_{gen}")
        wL = st.number_input("LL (kg/m²)", value=_loaded.get("wL_kg_m2", 200.0), step=10.0,
                              help="Live Load — ค่าเริ่มต้น 200 กก./ตร.ม. ตามตารางน้ำหนักบรรทุกจร กฎกระทรวง 2566 "
                                   "ประเภทบ้านพักอาศัย",
                              key=f"gs_wl_{gen}")

with col3:
    with input_card("ขนาดพื้น", color="green", icon="📐", key="gs-size"):
        L = st.number_input("ด้านยาว L (m)", value=_loaded.get("L_m", 5.0), step=0.5, help="ต้อง L >= S", key=f"gs_L_{gen}")
        S = st.number_input("ด้านสั้น S (m)", value=_loaded.get("S_m", 5.0), step=0.5, key=f"gs_S_{gen}")
        _t_default_idx = (ALLOWED_THICKNESS_CM.index(_loaded["t_cm"]) if _loaded.get("t_cm") in ALLOWED_THICKNESS_CM else 0)
        t = st.selectbox("ความหนาพื้น t (cm)", options=ALLOWED_THICKNESS_CM, index=_t_default_idx,
                          help="จำกัดเฉพาะค่าที่มีในตารางอ้างอิง (10, 12.5, 15, 17.5, 20, 22.5, 25, 27.5, 30 ซม.)",
                          key=f"gs_t_{gen}")

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

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ (Compute)", key="npk-btn-compute-sg", type="primary", use_container_width=True):
        st.session_state["gs_input"] = inp
        st.session_state["gs_result"] = calc_sg(inp)
        st.session_state["gs_project"] = {
            "slab_name": slab_name,
            # โครงการ/เจ้าของ/สถานที่/วิศวกร: รอหน้าข้อมูลโครงการกลาง (ใช้ร่วมกันทุกหมวด)
            "project_name": "", "owner": "", "location": "", "engineer": "",
        }
        mark_calc_pending_sync("gs")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-sg", use_container_width=True):
        saved_code = save_item("slab_on_ground", slab_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสพื้น (Slab No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("gs_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_gs", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "gs_result" in st.session_state:
    inp = st.session_state["gs_input"]
    result = st.session_state["gs_result"]
    project = st.session_state["gs_project"]

    st.header(f"ผลการคำนวณ — {project['slab_name']}")

    metric_card_row([
        ("น้ำหนักบรรทุกใช้งาน Wu", f"{result.wu_kg_m2:.0f}", "kgf/m²", None),
        ("ตรวจสอบ L >= S", "ผ่าน" if result.L_ge_S_ok else "ไม่ผ่าน", f"L={inp.L_m:.1f}, S={inp.S_m:.1f} m", result.L_ge_S_ok),
        ("Temperature Steel", f"{result.as_temperature_cm2_m:.2f}", "cm²/m", result.temperature_ok),
        ("Subgrade Drag", f"{result.as_subgrade_drag_cm2_m:.2f}", "cm²/m", result.subgrade_drag_ok),
        ("PCA (พื้นที่มีรถวิ่งผ่าน)", f"{result.as_pca_cm2_m:.2f}", "cm²/m", result.pca_ok),
        ("เหล็กเสริม", f"{result.as_provided_cm2_m:.2f}", "cm²/m ใช้จริง", result.all_reinf_ok),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**น้ำหนักบรรทุก**")
            st.write(f"Dead Load (จากความหนาพื้น) = {result.dead_load_kg_m2:.0f} kg/m²")
            st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {result.wu_kg_m2:.0f} kg/m²")

    with dcol2:
        with st.container(border=True):
            st.markdown("**ตรวจสอบขนาดพื้น**")
            st.write("L >= S:", "OK" if result.L_ge_S_ok else "ไม่ผ่าน — L ต้อง >= S")
            if result.dimension_limits:
                lim = result.dimension_limits
                st.write(f"ช่วงที่ยอมรับสำหรับ t={inp.t_cm} ซม.: {lim['min_m']} - {lim['max_m']} m")
                st.write("L อยู่ในช่วง:", "OK" if result.L_within_range else "ไม่ผ่าน")
                st.write("S อยู่ในช่วง:", "OK" if result.S_within_range else "ไม่ผ่าน")

    with dcol3:
        with st.container(border=True):
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

    st.write("")
    st.subheader("วิธีการคำนวณและสูตรที่ใช้")
    render_calc_sheet(_build_calc_sections(inp, result))

    st.subheader("รูปขยายรายละเอียดการเสริมเหล็ก")
    diagram_png = draw_gs_detail_png(inp.t_cm, inp.main_bar_dia_mm, inp.main_bar_spacing_cm)
    st.image(diagram_png, caption="Ground Slab — Joint & Reinforcement Detail")

    report_html = build_gs_report_html(
        project, inp, result, diagram_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("gs", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['slab_name']}")
