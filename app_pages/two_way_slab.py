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
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_tw_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row, render_calc_sheet, centered_image,
)

inject_card_css()
st.header("1.3 พื้นสองทาง (Two-way Slab)")


def _build_calc_sections(inp, result):
    """วิธีการคำนวณและสูตรที่ใช้ (พื้นสองทาง — ACI Moment Coefficient Method) — ดึงค่าจาก
    result (ไม่คำนวณซ้ำ)"""
    def _dir_steps(positions, d_cm, label_reinf, as_prov, spacing_max, ok):
        steps = [{"desc": "ระยะประสิทธิผล (Effective depth) d",
                  "formula": "d = t − ระยะหุ้ม − ⌀/2", "result": f"{d_cm:.1f} cm"}]
        for p in positions:
            if not p.active:
                continue
            warn = " &nbsp;⚠️ หน้าตัดเล็กไป" if p.over_reinforced else ""
            steps.append({
                "desc": f"โมเมนต์และเหล็กที่ตำแหน่ง: {p.label_th}",
                "formula": (f"สัมประสิทธิ์ C = {p.coeff:.4f} → M<sub>u</sub> = C·W<sub>u</sub>·S² = {p.mu_kgm:,.0f} kg·m/m "
                            f"→ A<sub>s</sub> = ρ·b·d = {p.as_req_cm2_m:.2f} cm²/m{warn} &nbsp;(S = ช่วงสั้น)")})
        steps.append({
            "desc": "เลือกใช้เหล็กเสริม",
            "formula": (f"ใช้ {label_reinf} &nbsp; (A<sub>s,จัดให้</sub> = {as_prov:.2f} cm²/m, "
                        f"ระยะห่าง ≤ {spacing_max:.0f} cm)"),
            "result": "ผ่าน ✓" if ok else "ไม่ผ่าน ✗"})
        return steps

    load = [
        {"desc": "อัตราส่วนด้านสั้น/ด้านยาว (ตรวจว่าเป็นพื้นสองทาง)",
         "formula": "m = S/L", "sub": f"{inp.S_m:.2f}/{inp.L_m:.2f}",
         "result": f"{result.m_ratio:.3f} (> 0.50 = พื้นสองทาง)" if result.two_way_ok else f"{result.m_ratio:.3f} (≤ 0.50)"},
        {"desc": "น้ำหนักบรรทุกประลัย (Factored load)",
         "formula": "W<sub>u</sub> = 1.4(DL + SDL) + 1.7LL",
         "sub": f"DL(พื้น)={result.dead_load_kg_m2:.0f}",
         "result": f"{result.wu_kg_m2:.0f} kg/m²"},
        {"desc": "ความหนาขั้นต่ำ (Minimum thickness)",
         "formula": "t<sub>min</sub> = เส้นรอบรูป/180",
         "result": f"{result.tmin_cm:.2f} cm — ใช้ t = {inp.t_cm:.1f} cm → " + ("ผ่าน ✓" if result.t_ok else "ไม่ผ่าน ✗")},
        {"desc": "อัตราส่วนเหล็กเสริม (Reinforcement ratios)",
         "formula": (f"ρ<sub>min</sub> = {result.rho_min:.4f} &nbsp; ρ<sub>b</sub> = {result.rho_b:.4f} &nbsp; "
                     f"ρ<sub>max</sub> = 0.75ρ<sub>b</sub> = {result.rho_max:.4f} &nbsp;(β₁ = {result.beta1:.3f})")},
    ]
    shear = [{"desc": "ตรวจสอบแรงเฉือน (Shear)",
              "formula": "V<sub>u</sub> ≤ φV<sub>c</sub> = φ·0.53√f'<sub>c</sub>·b·d",
              "sub": f"{result.vu_kg:,.0f} ≤ {result.phi_vc_kg:,.0f} kg",
              "result": "ผ่าน ✓" if result.shear_ok else "ไม่ผ่าน ✗"}]
    return [
        {"title": "การวิเคราะห์น้ำหนักบรรทุกและความหนาพื้น (Load & Thickness)", "steps": load},
        {"title": "เหล็กเสริมทิศทางสั้น (Flexural Design — Short direction S)",
         "steps": _dir_steps(result.short_positions, result.short_d_cm, result.reinf_label_short,
                             result.as_provided_short_cm2_m, result.short_spacing_max_cm, result.short_reinf_ok)},
        {"title": "เหล็กเสริมทิศทางยาว (Flexural Design — Long direction L)",
         "steps": _dir_steps(result.long_positions, result.long_d_cm, result.reinf_label_long,
                             result.as_provided_long_cm2_m, result.long_spacing_max_cm, result.long_reinf_ok)},
        {"title": "ตรวจสอบแรงเฉือน (Shear Check)", "steps": shear},
    ]


def _tw_end_states(positions):
    """แปลงผล Con-/Mid+/Disc- (positions[0]/[1]/[2]) เป็นสถานะขอบสำหรับรูปวาด:
    - ทั้งสองขอบต่อเนื่อง (Con- active, Disc- ไม่ active) -> "continuous", "continuous"
    - ขอบหนึ่งต่อเนื่อง + ขอบหนึ่งไม่ต่อเนื่อง (ทั้งคู่ active) -> "continuous", "discontinuous"
    - ไม่ต่อเนื่องทั้งสองขอบ (Con- ไม่ active, Disc- active — กรณี fully_disc ที่บังคับ
      เหล็กบนขั้นต่ำแล้ว) -> "discontinuous", "discontinuous"
    หมายเหตุ: ตั้งแต่ 2026-07-12 ขอบไม่ต่อเนื่องต้องมีเหล็กบนขั้นต่ำเสมอ (ไม่มี "none" อีก
    สำหรับกรณี 2-5) — Disc- ถูกเปิดใช้งานใน modules.two_way_slab แล้ว."""
    con_active = positions[0].active
    disc_active = positions[2].active
    if con_active and disc_active:
        return "continuous", "discontinuous"
    if con_active:
        return "continuous", "continuous"
    if disc_active:
        return "discontinuous", "discontinuous"
    return "none", "none"

# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "tw_form_gen" not in st.session_state:
    st.session_state["tw_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("two_way_slab")
if _loaded_data is not None:
    st.session_state["tw_form_gen"] += 1
    st.session_state["_tw_loaded_data"] = _loaded_data
    st.session_state["_tw_loaded_code"] = _loaded_code
    st.session_state["tw_case_key"] = _loaded_data.get("case_key", "CASE2")
gen = st.session_state["tw_form_gen"]
_loaded = st.session_state.get("_tw_loaded_data") or {}
_loaded_code = st.session_state.get("_tw_loaded_code")

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

# แถวแรก: 3 กล่องเรียงกัน [กรณีขอบเขตพื้นที่] [กรณีที่เลือก] [รหัสพื้น] — ตามภาพตัวอย่าง
row1_c1, row1_c2, row1_c3 = st.columns([1.6, 1.2, 1.0])
with row1_c1:
    with st.container(border=True):
        st.markdown("**กรณีขอบเขตพื้นที่ (Edge Condition Cases)**")
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
with row1_c2:
    with st.container(border=True):
        st.markdown("**กรณีที่เลือก (Case)**")
        # ใช้ div ที่ wrap ข้อความได้แทน st.text_input(disabled=True) เดิม — text_input เป็น
        # <input> บรรทัดเดียว ข้อความยาว (เช่น "2 — ไม่ต่อเนื่อง 1 ด้าน (1 Edge Discontinuous)")
        # จะถูกตัดมองไม่เห็นส่วนท้ายเมื่อกล่องแคบ (ย่อจอ/แบ่งหน้าต่าง) — div ให้ข้อความขึ้นบรรทัด
        # ใหม่แทนการซ่อน จึงอ่านได้ครบเสมอไม่ว่าหน้าต่างจะแคบแค่ไหน
        st.markdown(
            f'<div style="background:#F8FAFC; border:1px solid #CBD5E1; border-radius:8px; '
            f'padding:9px 14px; min-height:44px; display:flex; align-items:center; '
            f'font-size:18px; font-weight:600; color:#1D4ED8; line-height:1.3; '
            f'white-space:normal; overflow-wrap:break-word; word-break:break-word;">'
            f'{CASE_KEYS.index(case_key) + 1} — {case["label_th"]}</div>',
            unsafe_allow_html=True,
        )
with row1_c3:
    with st.container(border=True):
        st.markdown("**รหัสพื้น (Slab No.)**")
        slab_name = st.text_input("รหัสพื้น", value=_loaded_code or "S2-01", key=f"tw_slabname_{gen}",
                                   label_visibility="collapsed")

st.write("")

# แถวสอง: 3 การ์ดกรอบสี [เหล็กเสริม (น้ำเงิน)] [น้ำหนักบรรทุก (ส้ม)] [ขนาดพื้น (เขียว)]
col1, col2, col3 = st.columns(3)

with col1:
    with input_card("เหล็กเสริม", color="blue", icon="🔩", key="tw-reinf"):
        st.markdown("**เหล็กเสริมทิศทางสั้น (S)**")
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = st.number_input("f'c (kg/cm²)", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                              help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                              key=f"tw_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        short_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็ก (แนวสั้น)", options=_steel_options,
            index=_steel_options.index(_loaded["short_steel_type"]) if _loaded.get("short_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"tw_short_steel_{gen}")
        short_bar_dia_options = bar_dia_options_for_steel(short_steel_type, BAR_DIAMETERS_MM)
        _short_dia_idx = (short_bar_dia_options.index(_loaded["short_bar_dia_mm"])
                           if _loaded.get("short_bar_dia_mm") in short_bar_dia_options
                           else min(1, len(short_bar_dia_options) - 1))
        short_bar_dia = st.selectbox("ขนาดเหล็ก แนวสั้น (มม.)", options=short_bar_dia_options,
                                      index=_short_dia_idx, key=f"tw_short_dia_{gen}")
        short_bar_spacing = st.number_input("ระยะห่างเหล็ก แนวสั้น (ซม.)", value=_loaded.get("short_bar_spacing_cm", 15.0),
                                             step=1.0, key=f"tw_short_spacing_{gen}")

        st.markdown("**เหล็กเสริมทิศทางยาว (L)**")
        long_steel_type = st.selectbox(
            "ชั้นคุณภาพเหล็ก (แนวยาว)", options=_steel_options,
            index=_steel_options.index(_loaded["long_steel_type"]) if _loaded.get("long_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"tw_long_steel_{gen}")
        long_bar_dia_options = bar_dia_options_for_steel(long_steel_type, BAR_DIAMETERS_MM)
        _long_dia_idx = (long_bar_dia_options.index(_loaded["long_bar_dia_mm"])
                          if _loaded.get("long_bar_dia_mm") in long_bar_dia_options
                          else min(1, len(long_bar_dia_options) - 1))
        long_bar_dia = st.selectbox("ขนาดเหล็ก แนวยาว (มม.)", options=long_bar_dia_options,
                                     index=_long_dia_idx, key=f"tw_long_dia_{gen}")
        long_bar_spacing = st.number_input("ระยะห่างเหล็ก แนวยาว (ซม.)", value=_loaded.get("long_bar_spacing_cm", 15.0),
                                            step=1.0, key=f"tw_long_spacing_{gen}")

with col2:
    with input_card("น้ำหนักบรรทุก", color="orange", icon="⚖️", key="tw-load"):
        wD = st.number_input("SDL (kg/m²)", value=_loaded.get("wD_kg_m2", 150.0), step=10.0,
                              help="Superimposed Dead Load", key=f"tw_wd_{gen}")
        wL = st.number_input("LL (kg/m²)", value=_loaded.get("wL_kg_m2", 200.0), step=10.0,
                              help="Live Load — ค่าเริ่มต้น 200 กก./ตร.ม. ตามตารางน้ำหนักบรรทุกจร กฎกระทรวง 2566 "
                                   "ประเภทบ้านพักอาศัย",
                              key=f"tw_wl_{gen}")

with col3:
    with input_card("ขนาดพื้น", color="green", icon="📐", key="tw-size"):
        S = st.number_input("ช่วงพาด S — ด้านสั้น (m)", value=_loaded.get("S_m", 2.5), step=0.5, key=f"tw_S_{gen}")
        L = st.number_input("ช่วงพาด L — ด้านยาว (m)", value=_loaded.get("L_m", 3.0), step=0.5,
                             help="ต้อง S/L > 0.5 จึงจะถือเป็นพื้นสองทาง (ถ้า <=0.5 ให้ใช้โมดูล 1.2 พื้นทางเดียวแทน)",
                             key=f"tw_L_{gen}")
        _t_idx = ALLOWED_THICKNESS_CM.index(_loaded["t_cm"]) if _loaded.get("t_cm") in ALLOWED_THICKNESS_CM else 1
        t = st.selectbox("ความหนาพื้น t (cm)", options=ALLOWED_THICKNESS_CM, index=_t_idx, key=f"tw_t_{gen}")

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

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ", key="npk-btn-compute-tw", type="primary", use_container_width=True):
        st.session_state["tw_input"] = inp
        st.session_state["tw_result"] = calc_tw(inp)
        st.session_state["tw_project"] = {"slab_name": slab_name}
        mark_calc_pending_sync("tw")
with bcol2:
    if st.button("💾 บันทึกรายการ", key="npk-btn-save-tw", use_container_width=True):
        saved_code = save_item("two_way_slab", slab_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านซ้าย)')
        else:
            st.warning("กรุณาระบุรหัสพื้น (Slab No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("tw_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_tw", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

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

    metric_card_row([
        {"name": "น้ำหนักบรรทุกใช้งาน", "sym": "Wu", "value": f"{result.wu_kg_m2:.0f}",
         "unit": "kgf/m²", "ok": None},
        {"name": "ตรวจสอบ m = S/L", "sym": "m ratio", "value": f"{result.m_ratio:.3f}",
         "unit": "ต้อง > 0.5", "ok": result.two_way_ok,
         "reason": "สองทาง" if result.two_way_ok else "ทางเดียว"},
        {"name": "ตรวจสอบความหนา", "sym": "t min", "value": f"{result.tmin_cm:.2f}",
         "unit": f"cm. (ใช้ {inp.t_cm:.1f} cm.)", "ok": result.t_ok,
         "reason": "หนาเพียงพอ" if result.t_ok else "บางเกินไป"},
        {"name": "แรงเฉือน", "sym": "Vu / φVc", "value": f"{result.vu_kg:.0f}",
         "unit": f"kgf (φVc={result.phi_vc_kg:.0f})", "ok": result.shear_ok,
         "reason": "ปลอดภัย" if result.shear_ok else ""},
        {"name": "เหล็กเสริม แนวสั้น (S)", "sym": "As req.", "value": f"{result.as_provided_short_cm2_m:.2f}",
         "unit": "cm²/m", "ok": result.short_reinf_ok,
         "reason": "พอ" if result.short_reinf_ok else ""},
        {"name": "เหล็กเสริม แนวยาว (L)", "sym": "As req.", "value": f"{result.as_provided_long_cm2_m:.2f}",
         "unit": "cm²/m", "ok": result.long_reinf_ok,
         "reason": "พอ" if result.long_reinf_ok else ""},
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**น้ำหนักบรรทุก**")
            st.write(f"Dead Load (จากความหนาพื้น) = {result.dead_load_kg_m2:.0f} kg/m²")
            st.write(f"Wu = 1.4(DL+SDL) + 1.7LL = {result.wu_kg_m2:.0f} kg/m²")
            st.write(f"น้ำหนักลงคาน (Service, สามเหลี่ยม/คางหมู): "
                     f"DL={result.dl_on_beam_triangular_kg_m:.0f}/{result.dl_on_beam_trapezoidal_kg_m:.0f} kg/m., "
                     f"LL={result.ll_on_beam_triangular_kg_m:.0f}/{result.ll_on_beam_trapezoidal_kg_m:.0f} kg/m.")

    with dcol2:
        with st.container(border=True):
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

    with dcol3:
        with st.container(border=True):
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

    st.write("")
    st.subheader("วิธีการคำนวณและสูตรที่ใช้")
    render_calc_sheet(_build_calc_sections(inp, result))

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

    # รูปตัดแสดงเรียงต่อกันแนวตั้ง จัดกึ่งกลางหน้า (centered_image) เพื่อให้ตัวอักษร/เส้นบอกระยะ
    # อ่านง่ายชัดเจนที่สุด ตามที่ผู้ใช้แจ้งแก้ไข (2026-07)
    centered_image(section_s_png, caption="รูปตัด — ทิศทางสั้น (Short Span Section)")
    centered_image(section_l_png, caption="รูปตัด — ทิศทางยาว (Long Span Section)")
    centered_image(plan_png, caption="แปลนเหล็กเสริม (Reinforcement Plan)")

    report_html = build_tw_report_html(
        project, inp, result, section_s_png, section_l_png, plan_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # ปุ่ม "แสดงรายการคำนวณ" ด้านบนสุดของหน้าเปิดรายงานนี้เป็นหน้าต่าง/แท็บใหม่โดยตรง (ไม่ใช่
    # พรีวิวฝังในหน้าอีกต่อไป ตามคำขอผู้ใช้ 2026-07) — อัปเดตช่องปุ่มที่จองไว้ด้วย report_html จริง
    sync_report_html("tw", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['slab_name']}")
