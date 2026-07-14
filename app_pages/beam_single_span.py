"""
Module 3.1 — คานช่วงเดียว (Single-span Beam)

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from modules.beam_single_span import (
    BeamSingleSpanInput, PointLoad, calculate as calc_beam,
    BEAM_WIDTH_CM_OPTIONS, BEAM_DEPTH_CM_OPTIONS,
    BAR_DIAMETERS_MM, STIRRUP_DIAMETERS_MM, DEFAULT_STIRRUP_LEGS,
)
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_dia_options_for_steel
from common.diagram import (
    draw_beam_sfd_bmd_png, draw_beam_section_png,
    compute_service_deflection, build_deflection_calc_section,
)
from common.pdf_export import download_report_button
from common.report_preview import open_preview_button, mark_calc_pending_sync, sync_report_html
from common.project_store import consume_pending_load, save_item
from common.report import build_beam_report_html
from common.ui_style import (
    bar_type_label as _bar_type_label,
    inject_card_css, input_card, metric_card_row, render_calc_sheet, centered_image,
    inject_etabs_css, etabs_card, etabs_group, etabs_number, etabs_select, etabs_text,
)
from common.design_params import PHI_B, PHI_V

inject_card_css()
inject_etabs_css()
st.header("3.1 คานช่วงเดียว (Single-span Beam)")


def _scaled_width(png_bytes, factor):
    """คืนความกว้างเป็นพิกเซล = ความกว้างจริงของภาพ × factor (สำหรับปรับขนาดแสดงผล)."""
    try:
        import io as _io
        from PIL import Image as _PILImage
        return max(1, int(_PILImage.open(_io.BytesIO(png_bytes)).width * factor))
    except Exception:
        return None

def _build_calc_sections(inp, result):
    """สร้างขั้นตอน "วิธีการคำนวณและสูตรที่ใช้" ของคานช่วงเดียว — ดึงค่าที่โมดูลคำนวณเสร็จแล้ว
    จาก result มาแสดง (ไม่คำนวณเลขซ้ำ) พร้อมสูตรและการแทนค่า สไตล์แผ่นคำนวณของวิศวกร"""
    fy_main = GS_STEEL_FY_KSC[inp.main_steel_type]
    fy_stir = GS_STEEL_FY_KSC[inp.stirrup_steel_type]
    b = inp.b_cm
    fc = inp.fc_ksc
    d = result.bottom.d_cm
    flex = result.bottom
    stir = result.stirrup

    flex_steps = [
        {"desc": "ระยะประสิทธิผล (Effective depth) d",
         "formula": "d = h − ระยะหุ้ม − ⌀ปลอก − ⌀หลัก/2",
         "result": f"{d:.1f} cm"},
        {"desc": "อัตราส่วนเหล็กเสริม (Reinforcement ratios)",
         "formula": (f"ρ<sub>min</sub> = 14/f<sub>y</sub> = {result.rho_min:.4f}<br>"
                     f"ρ<sub>b</sub> = 0.85·β₁·(f'<sub>c</sub>/f<sub>y</sub>)·6120/(6120+f<sub>y</sub>) = {result.rho_b:.4f}"
                     f" &nbsp;(β₁ = {result.beta1:.3f})<br>"
                     f"ρ<sub>max</sub> = 0.75·ρ<sub>b</sub> = {result.rho_max:.4f}")},
        {"desc": "สัมประสิทธิ์ต้านทานโมเมนต์ R<sub>u</sub>",
         "formula": "R<sub>u</sub> = M<sub>u</sub>/(φ<sub>b</sub>·b·d²)",
         "sub": f"{result.mu_max_kg_m*100:,.0f}/({PHI_B:.2f}×{b:.0f}×{d:.1f}²)",
         "result": f"{flex.ru_ksc:.2f} ksc"},
    ]
    if not flex.doubly_reinforced:
        flex_steps += [
            {"desc": "อัตราส่วนเหล็กที่ต้องการ",
             "formula": (f"ρ<sub>req</sub> = 0.85(f'<sub>c</sub>/f<sub>y</sub>)"
                         f"[1−√(1−2R<sub>u</sub>/0.85f'<sub>c</sub>)] = {flex.rreq:.4f}"),
             "result": f"ใช้ ρ = max(ρ<sub>req</sub>, ρ<sub>min</sub>) = {flex.rho_used:.4f}"},
            {"desc": "พื้นที่เหล็กรับแรงดึงที่ต้องการ A<sub>s</sub>",
             "formula": "A<sub>s</sub> = ρ·b·d",
             "sub": f"{flex.rho_used:.4f}×{b:.0f}×{d:.1f}",
             "result": f"{flex.as_req_cm2:.2f} cm²"},
        ]
    else:
        flex_steps += [
            {"desc": "โมเมนต์เกินกำลังเหล็กชั้นเดียว → ต้องเสริมเหล็กรับแรงอัด (Doubly-reinforced)",
             "formula": (f"M<sub>u1,max</sub> = {flex.mu1_kgm:,.0f} kg·m &nbsp; (ที่ ρ<sub>max</sub>)<br>"
                         f"M<sub>u2</sub> = M<sub>u</sub> − M<sub>u1,max</sub> = {flex.mu2_kgm:,.0f} kg·m"),
             "note": "โมเมนต์เกินกว่าเหล็กรับแรงดึงชั้นเดียวจะรับได้ จึงเพิ่มเหล็กรับแรงอัดช่วย"},
            {"desc": "พื้นที่เหล็กรวม (รับแรงดึง)",
             "formula": "A<sub>s</sub> = A<sub>s1</sub> + A<sub>s2</sub>",
             "result": f"{flex.as_req_cm2:.2f} cm² (เหล็กรับแรงอัด A<sub>s2</sub> = {flex.as_comp_req_cm2:.2f} cm²)"},
        ]
    flex_steps.append(
        {"desc": "เลือกใช้เหล็กเสริม",
         "formula": (f"ใช้ {result.reinf_label_bottom} → A<sub>s,จัดให้</sub> = {flex.as_provided_cm2:.2f} cm² "
                     f"{'≥' if flex.reinf_ok else '<'} A<sub>s,ต้องการ</sub> = {flex.as_req_cm2:.2f} cm²"),
         "result": "ผ่าน ✓" if flex.reinf_ok else "ไม่ผ่าน ✗"})

    shear_steps = [
        {"desc": "กำลังรับแรงเฉือนของคอนกรีต V<sub>c</sub>",
         "formula": "V<sub>c</sub> = 0.53√f'<sub>c</sub>·b·d",
         "sub": f"0.53×√{fc:.0f}×{b:.0f}×{d:.1f}",
         "result": f"{stir.vc_kg:,.0f} kg → φV<sub>c</sub> = {stir.phi_vc_kg:,.0f} kg"},
        {"desc": "แรงเฉือนที่เหล็กปลอกต้องรับ V<sub>s</sub>",
         "formula": "V<sub>s</sub> = V<sub>u</sub>/φ<sub>v</sub> − V<sub>c</sub>",
         "sub": f"{result.vu_max_kg:,.0f}/{PHI_V:.2f} − {stir.vc_kg:,.0f}",
         "result": f"{stir.vs_req_kg:,.0f} kg"},
        {"desc": f"พื้นที่เหล็กปลอก A<sub>v</sub> ({inp.stirrup_legs} ขา)",
         "formula": f"A<sub>v</sub> = {inp.stirrup_legs} × พื้นที่เหล็ก⌀{inp.stirrup_bar_dia_mm:.0f}",
         "result": f"{stir.av_cm2:.2f} cm²"},
    ]
    if stir.vs_req_kg > 0:
        shear_steps.append(
            {"desc": "ระยะเรียงตามกำลังรับแรงเฉือน",
             "formula": "s = A<sub>v</sub>·f<sub>y</sub>·d / V<sub>s</sub>",
             "result": f"{stir.s_max_from_vs_cm:.1f} cm"})
    else:
        shear_steps.append(
            {"desc": "ตรวจสอบความเพียงพอของคอนกรีต",
             "formula": "V<sub>u</sub> ≤ φV<sub>c</sub> : คอนกรีตรับแรงเฉือนได้เพียงพอ",
             "note": "ไม่ต้องการเหล็กปลอกจากกำลัง — ใช้ระยะเรียงสูงสุดตามข้อกำหนดขั้นต่ำ"})
    shear_steps += [
        {"desc": "ระยะเรียงสูงสุดตามมาตรฐาน",
         "formula": "s<sub>max,code</sub> = min(d/2 หรือ d/4, 60 หรือ 30 cm) ตามระดับ V<sub>s</sub>",
         "result": f"{stir.s_max_code_cm:.1f} cm"},
        {"desc": "ระยะเรียงที่ใช้ได้",
         "formula": "s<sub>max</sub> = min(ระยะตามกำลัง, ระยะตามมาตรฐาน)",
         "result": f"{stir.s_max_cm:.1f} cm"},
        {"desc": "เลือกใช้เหล็กปลอก",
         "formula": (f"ใช้ {result.reinf_label_stirrup} "
                     f"{'≤' if stir.stirrup_ok else '>'} s<sub>max</sub> = {stir.s_max_cm:.1f} cm"),
         "result": "ผ่าน ✓" if stir.stirrup_ok else ("หน้าตัดเล็กเกินไป" if stir.section_too_small else "ไม่ผ่าน ✗")},
    ]
    # --- ส่วนวิเคราะห์โครงสร้าง (แสดงเงื่อนไขจุดรองรับ + โมเมนต์ปลายยึดแน่น) ---
    def _sup_name(fx):
        return "ยึดแน่น (Fix)" if fx else "ยึดหมุน (Pin)"
    analysis_steps = [
        {"desc": "เงื่อนไขจุดรองรับ (Support Condition)",
         "formula": f"ปลายซ้าย = {_sup_name(result.left_fixed)} , ปลายขวา = {_sup_name(result.right_fixed)}",
         "result": f"{'Fix' if result.left_fixed else 'Pin'}–{'Fix' if result.right_fixed else 'Pin'}"},
        {"desc": "แรงปฏิกิริยาที่จุดรองรับ (Reactions)",
         "formula": "R<sub>ซ้าย</sub> , R<sub>ขวา</sub>",
         "result": f"{result.r_left_kg:,.0f} , {result.r_right_kg:,.0f} kg"},
    ]
    if result.left_fixed or result.right_fixed:
        analysis_steps.append(
            {"desc": "โมเมนต์ที่ปลายยึดแน่น (Fixed-End Moments) — วิธี Consistent Deformation",
             "formula": "หาโมเมนต์ปลายโดยบังคับมุมหมุน = 0 ที่ปลายยึดแน่น (M ปลาย ไม่ขึ้นกับ EI)",
             "sub": f"M<sub>ซ้าย</sub> = {result.m_a_kgm:+,.0f} , M<sub>ขวา</sub> = {result.m_b_kgm:+,.0f} kg·m",
             "note": "โมเมนต์ลบ (hogging) ที่ปลายยึดแน่น → ต้องเสริมเหล็กบนที่ปลายรับโมเมนต์นี้"})
    analysis_steps.append(
        {"desc": "โมเมนต์บวกสูงสุดกลางช่วง (Max Positive Moment)",
         "formula": "M<sub>u,max+</sub>", "result": f"{result.mu_max_kg_m:,.0f} kg·m ที่ x={result.mu_max_x_m:.2f} m"})

    sections = [
        {"title": "การวิเคราะห์โครงสร้าง (Structural Analysis)", "steps": analysis_steps},
        {"title": "การออกแบบเหล็กรับแรงดัด — เหล็กล่าง (โมเมนต์บวก)", "steps": flex_steps},
        {"title": "การออกแบบเหล็กปลอกรับแรงเฉือน (Shear Design)", "steps": shear_steps},
    ]
    # เหล็กบน: แสดงการออกแบบจริงเมื่อมีโมเมนต์ลบที่ปลายยึดแน่น
    if result.mu_neg_max_kgm > 1e-6:
        top = result.top
        top_steps = [
            {"desc": "โมเมนต์ลบสูงสุดที่จุดรองรับยึดแน่น", "formula": "M<sub>u,max−</sub>",
             "result": f"{result.mu_neg_max_kgm:,.0f} kg·m"},
            {"desc": "สัมประสิทธิ์ต้านทานโมเมนต์ R<sub>u</sub>",
             "formula": "R<sub>u</sub> = M<sub>u</sub>/(φ<sub>b</sub>·b·d²)", "result": f"{top.ru_ksc:.2f} ksc"},
            {"desc": "พื้นที่เหล็กบนที่ต้องการ A<sub>s,top</sub>", "formula": "A<sub>s</sub> = ρ·b·d",
             "result": f"{top.as_req_cm2:.2f} cm²"},
            {"desc": "เลือกใช้เหล็กบน",
             "formula": f"ใช้ {result.reinf_label_top} → A<sub>s,จัดให้</sub> = {top.as_provided_cm2:.2f} cm²",
             "result": "ผ่าน ✓" if top.reinf_ok else "ไม่ผ่าน ✗"},
        ]
        sections.insert(2, {"title": "การออกแบบเหล็กรับแรงดัด — เหล็กบน (โมเมนต์ลบที่ปลายยึดแน่น)",
                            "steps": top_steps})
    return sections


# รองรับ "เปิดกลับมาแก้ไข" จากรายการที่บันทึกไว้ (คลิกจากแถบด้านข้าง)
if "beam_form_gen" not in st.session_state:
    st.session_state["beam_form_gen"] = 0
_loaded_data, _loaded_code = consume_pending_load("beam_single_span")
if _loaded_data is not None:
    st.session_state["beam_form_gen"] += 1
    st.session_state["_beam_loaded_data"] = _loaded_data
    st.session_state["_beam_loaded_code"] = _loaded_code
gen = st.session_state["beam_form_gen"]
_loaded = st.session_state.get("_beam_loaded_data") or {}
_loaded_code = st.session_state.get("_beam_loaded_code")
_loaded_points = _loaded.get("point_loads") or []

# แถวรหัสคาน
id_c1, _id_gap = st.columns([1.4, 2.6])
with id_c1:
    with etabs_card("ข้อมูลรายการ", color="navy", icon="🏷️", key="beam-id"):
        beam_name = etabs_text("รหัสคาน (No.)", value=_loaded_code or "B-01",
                               ratio=(1.0, 1.3, 0.1), key=f"beam_name_{gen}")

st.write("")

# 3 การ์ดสไตล์ ETABS สูงเท่ากัน: [วัสดุ/เหล็กเสริม] [น้ำหนักบรรทุก] [ขนาดคาน & ช่วง]
col1, col2, col3 = st.columns(3)

with col1:
    with etabs_card("วัสดุ / เหล็กเสริม", color="blue", icon="🪵", key="beam-material"):
        etabs_group("คุณสมบัติวัสดุ")
        _default_fc = st.session_state["design_params"].fc_ksc if "design_params" in st.session_state else 210.0
        fc = etabs_number("f'c", "kg/cm²", value=_loaded.get("fc_ksc", _default_fc), step=10.0,
                          help="กำลังอัดประลัยคอนกรีต — ค่าเริ่มต้นดึงจากหน้า \"พารามิเตอร์การออกแบบ\" ถ้าเคยตั้งค่าไว้",
                          key=f"beam_fc_{gen}")
        _steel_options = list(GS_STEEL_FY_KSC.keys())
        etabs_group("เหล็กเสริมหลัก (บน/ล่าง)")
        main_steel_type = etabs_select(
            "ชั้นคุณภาพ", options=_steel_options,
            index=_steel_options.index(_loaded["main_steel_type"]) if _loaded.get("main_steel_type") in _steel_options else 2,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"beam_main_steel_{gen}")
        main_bar_dia_options = bar_dia_options_for_steel(main_steel_type, BAR_DIAMETERS_MM)
        _main_dia_idx = (main_bar_dia_options.index(_loaded["main_bar_dia_mm"])
                          if _loaded.get("main_bar_dia_mm") in main_bar_dia_options
                          else min(1, len(main_bar_dia_options) - 1))
        main_bar_dia = etabs_select("ขนาดเหล็ก (มม.)", options=main_bar_dia_options,
                                    index=_main_dia_idx, key=f"beam_main_dia_{gen}")

        etabs_group("เหล็กปลอก (Stirrup)")
        stirrup_steel_type = etabs_select(
            "ชั้นคุณภาพ", options=_steel_options,
            index=_steel_options.index(_loaded["stirrup_steel_type"]) if _loaded.get("stirrup_steel_type") in _steel_options else 0,
            format_func=lambda k: f"{k} ({_bar_type_label(GS_STEEL_BAR_TYPE[k])})",
            help="ชนิดเหล็ก (DB/RB) กำหนดอัตโนมัติตามชั้นคุณภาพ: SR=RB (เส้นกลม), SD=DB (ข้ออ้อย)", key=f"beam_stirrup_steel_{gen}")
        stirrup_bar_dia_options = bar_dia_options_for_steel(stirrup_steel_type, STIRRUP_DIAMETERS_MM)
        _stirrup_dia_idx = (stirrup_bar_dia_options.index(_loaded["stirrup_bar_dia_mm"])
                             if _loaded.get("stirrup_bar_dia_mm") in stirrup_bar_dia_options
                             else min(0, len(stirrup_bar_dia_options) - 1))
        stirrup_bar_dia = etabs_select("ขนาดเหล็ก (มม.)", options=stirrup_bar_dia_options,
                                       index=_stirrup_dia_idx, key=f"beam_stirrup_dia_{gen}")
        stirrup_spacing = etabs_number("ระยะห่าง @", "cm", value=_loaded.get("stirrup_spacing_use_cm", 15.0),
                                       step=1.0, key=f"beam_stirrup_spacing_{gen}")

with col2:
    with etabs_card("น้ำหนักบรรทุก", color="orange", icon="⚖️", key="beam-load"):
        etabs_group("น้ำหนักแผ่กระจาย (Line Load)")
        line_dl = etabs_number("DL (ไม่รวม SW)", "kg/m", value=_loaded.get("line_load_dl_kg_m", 200.0), step=10.0,
                               help="ไม่รวมน้ำหนักตัวเองคาน — น้ำหนักตัวเองของคาน (จาก b×h×2400) จะถูกบวกเพิ่มให้"
                                    "อัตโนมัติในการคำนวณ",
                               key=f"beam_line_dl_{gen}")
        line_ll = etabs_number("LL", "kg/m", value=_loaded.get("line_load_ll_kg_m", 300.0), step=10.0,
                               key=f"beam_line_ll_{gen}")

        etabs_group("น้ำหนักจุด (Point Loads)")
        n_points = etabs_number("จำนวนจุด", "จุด", min_value=0, max_value=10,
                                value=len(_loaded_points), step=1, key=f"beam_npoints_{gen}")
        point_loads_input = []
        for i in range(int(n_points)):
            _pl_default = _loaded_points[i] if i < len(_loaded_points) else {}
            etabs_group(f"จุดที่ {i + 1}")
            p_dl = etabs_number("P·DL", "kg", value=_pl_default.get("p_dl_kg", 0.0), step=50.0,
                                key=f"beam_pl_dl_{gen}_{i}")
            p_ll = etabs_number("P·LL", "kg", value=_pl_default.get("p_ll_kg", 0.0), step=50.0,
                                key=f"beam_pl_ll_{gen}_{i}")
            p_x = etabs_number("ระยะ x", "m", value=_pl_default.get("x_m", 0.0), step=0.1,
                               key=f"beam_pl_x_{gen}_{i}")
            point_loads_input.append(PointLoad(p_dl_kg=p_dl, p_ll_kg=p_ll, x_m=p_x))

with col3:
    with etabs_card("ขนาดคาน & ช่วงคาน", color="green", icon="📐", key="beam-size"):
        etabs_group("หน้าตัดคาน")
        _b_idx = BEAM_WIDTH_CM_OPTIONS.index(_loaded["b_cm"]) if _loaded.get("b_cm") in BEAM_WIDTH_CM_OPTIONS else 1
        b_cm = etabs_select("ความกว้าง b (cm)", options=BEAM_WIDTH_CM_OPTIONS, index=_b_idx, key=f"beam_b_{gen}")
        _h_idx = BEAM_DEPTH_CM_OPTIONS.index(_loaded["h_cm"]) if _loaded.get("h_cm") in BEAM_DEPTH_CM_OPTIONS else 2
        h_cm = etabs_select("ความลึก h (cm)", options=BEAM_DEPTH_CM_OPTIONS, index=_h_idx, key=f"beam_h_{gen}")
        etabs_group("ความยาวช่วง")
        L_m = etabs_number("ช่วงคาน L", "m", value=_loaded.get("L_m", 4.0), step=0.1, key=f"beam_L_{gen}")
        etabs_group("จุดรองรับ (Support)")
        _sup_opts = ["Pin (ยึดหมุน)", "Fix (ยึดแน่น)"]
        left_sup = etabs_select("ปลายซ้าย", options=_sup_opts,
                                index=1 if _loaded.get("left_fixed") else 0, key=f"beam_lsup_{gen}")
        right_sup = etabs_select("ปลายขวา", options=_sup_opts,
                                 index=1 if _loaded.get("right_fixed") else 0, key=f"beam_rsup_{gen}")
        left_fixed = left_sup.startswith("Fix")
        right_fixed = right_sup.startswith("Fix")

inp = BeamSingleSpanInput(
    fc_ksc=fc,
    main_steel_type=main_steel_type,
    stirrup_steel_type=stirrup_steel_type,
    b_cm=b_cm,
    h_cm=h_cm,
    L_m=L_m,
    line_load_dl_kg_m=line_dl,
    line_load_ll_kg_m=line_ll,
    point_loads=point_loads_input,
    main_bar_dia_mm=main_bar_dia,
    stirrup_bar_dia_mm=stirrup_bar_dia,
    stirrup_legs=DEFAULT_STIRRUP_LEGS,
    stirrup_spacing_use_cm=stirrup_spacing,
    left_fixed=left_fixed,
    right_fixed=right_fixed,
)

# --- ทางเลือก: ออกแบบรับแรงบิด (Torsion) ตาม ACI 318 — ผู้ใช้กรอก Tu เอง ---
with st.container(border=True):
    _tc1, _tc2 = st.columns([1.1, 1.0])
    with _tc1:
        torsion_enabled = st.checkbox(
            "ออกแบบรับแรงบิด (Torsion) ตาม ACI 318",
            value=_loaded.get("torsion_enabled", False), key=f"beam_tors_en_{gen}")
    with _tc2:
        tu_kgm = st.number_input("แรงบิดประลัย Tu (kg·m)", min_value=0.0,
                                 value=float(_loaded.get("tu_kgm", 0.0)), step=50.0,
                                 key=f"beam_tu_{gen}", disabled=not torsion_enabled,
                                 help="แรงบิดประลัย (factored) ที่กระทำต่อคาน — โปรแกรมจะคำนวณเหล็กปลอก"
                                      "และเหล็กยืนรับแรงบิดเพิ่มตามวิธี space truss ของ ACI 318")

st.write("")
bcol1, bcol2, bcol3 = st.columns(3)
with bcol1:
    if st.button("🧮 คำนวณ (Compute)", key="npk-btn-compute-bs", type="primary", use_container_width=True):
        bad_x = [p for p in point_loads_input if not (0.0 <= p.x_m <= L_m)]
        if bad_x:
            st.error(f"ระยะ x ของน้ำหนักจุดต้องอยู่ระหว่าง 0 ถึง {L_m:.2f} m. (ความยาวช่วงคาน) — กรุณาตรวจสอบ")
        else:
            st.session_state["beam_input"] = inp
            st.session_state["beam_result"] = calc_beam(inp)
            st.session_state["beam_project"] = {"beam_name": beam_name}
            st.session_state["beam_torsion_enabled"] = bool(torsion_enabled)
            st.session_state["beam_tu_kgm"] = float(tu_kgm)
            mark_calc_pending_sync("bs")
with bcol2:
    if st.button("💾 บันทึกรายการนี้", key="npk-btn-save-bs", use_container_width=True):
        saved_code = save_item("beam_single_span", beam_name, inp)
        if saved_code:
            st.success(f'บันทึกรายการ "{saved_code}" แล้ว (ดูได้ที่แถบด้านข้าง)')
        else:
            st.warning("กรุณาระบุรหัสคาน (Beam No.) ก่อนบันทึก")
with bcol3:
    _pv_html = st.session_state.get("bs_report_html")
    if _pv_html:
        open_preview_button("📄 แสดงรายการคำนวณ", _pv_html, key="pvtop_bs", height=52)
    else:
        st.button("📄 แสดงรายการคำนวณ", use_container_width=True, disabled=True, help="กดคำนวณก่อน")

if "beam_result" in st.session_state:
    inp = st.session_state["beam_input"]
    result = st.session_state["beam_result"]
    project = st.session_state["beam_project"]

    st.header(f"ผลการคำนวณ — {project['beam_name']}")

    _stirrup_status = "warn" if result.stirrup.section_too_small else result.stirrup.stirrup_ok
    metric_card_row([
        ("น้ำหนักบรรทุกใช้งาน Wu", f"{result.wu_kg_m:.0f}", "kgf/m", None),
        ("โมเมนต์สูงสุด Mu,max", f"{result.mu_max_kg_m:.0f}", f"kgf-m ที่ x={result.mu_max_x_m:.2f} m.", None),
        ("เหล็กเสริมล่าง As", f"{result.bottom.as_provided_cm2:.2f}", "cm²", result.bottom.reinf_ok),
        ("เหล็กปลอก (Stirrup)", result.reinf_label_stirrup, f"Vu,max={result.vu_max_kg:.0f} kg", _stirrup_status),
    ])
    st.write("")

    dcol1, dcol2, dcol3 = st.columns(3)
    with dcol1:
        with st.container(border=True):
            st.markdown("**น้ำหนักบรรทุกและผลการวิเคราะห์แรง**")
            st.write(f"น้ำหนักตัวเองคาน = {result.self_weight_kg_m:.0f} kg/m")
            st.write(f"Wu = 1.4(DL+น้ำหนักตัวเอง)+1.7LL = {result.wu_kg_m:.0f} kg/m")
            if inp.point_loads:
                st.write("Point loads (factored): " +
                         ", ".join(f"Pu={pu:.0f}kg@x={x:.2f}m" for x, pu in result.pu_loads))
            _sn = lambda fx: "Fix" if fx else "Pin"
            st.write(f"จุดรองรับ: ปลายซ้าย = **{_sn(result.left_fixed)}**, ปลายขวา = **{_sn(result.right_fixed)}**")
            st.write(f"R ซ้าย = {result.r_left_kg:.2f} kg., R ขวา = {result.r_right_kg:.2f} kg.")
            if result.left_fixed or result.right_fixed:
                st.write(f"โมเมนต์ปลายยึดแน่น: M ซ้าย = {result.m_a_kgm:+.0f}, M ขวา = {result.m_b_kgm:+.0f} kg-m.")
            st.write(f"Vu,max = {result.vu_max_kg:.2f} kg.")
            st.write(f"Mu,max (บวก) = {result.mu_max_kg_m:.2f} kg-m. (ที่ x={result.mu_max_x_m:.2f} m.)")
            if result.mu_neg_max_kgm > 1e-6:
                st.write(f"Mu,max (ลบ ที่ปลาย) = {result.mu_neg_max_kgm:.2f} kg-m. → ออกแบบเหล็กบน")

    with dcol2:
        with st.container(border=True):
            st.markdown("**เหล็กเสริมล่าง (Bottom Bars)**")
            st.write(f"As ต้องการ = {result.bottom.as_req_cm2:.2f} cm² "
                     f"({result.bottom.n_bars_req} เส้น)")
            if result.bottom.doubly_reinforced:
                st.warning(f"⚠️ ต้องเสริมเหล็กสองชั้น (doubly-reinforced): Mu2={result.bottom.mu2_kgm:.0f} kg-m., "
                           f"As2={result.bottom.as_comp_req_cm2:.2f} cm²")
            if result.bottom.n_layers > 1:
                breakdown = "+".join(str(n) for n in result.bottom.bars_per_layer if n > 0)
                st.info(f"ℹ️ เหล็กล่างเกิน 1 ชั้น จัดเป็น {result.bottom.n_layers} ชั้นอัตโนมัติตามมาตรฐาน "
                        f"({breakdown} เส้น) — d ที่ใช้ออกแบบจริงคำนวณจาก centroid ของเหล็กทุกชั้นแล้ว")
            if not result.bottom.reinf_ok:
                st.error(f"⚠️ เหล็กที่ต้องการ ({result.bottom.n_bars_req} เส้น) เกินกว่าจะใส่ได้แม้จัดหลายชั้นแล้ว "
                         f"(สูงสุด {result.bottom.max_bars_single_layer * 3} เส้น) — กรุณาขยายความกว้างคานหรือเปลี่ยนขนาดเหล็ก")
            st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_bottom}** (As={result.bottom.as_provided_cm2:.2f} cm²)")
            st.write("ผลตรวจสอบ:", "ผ่าน ✅" if result.bottom.reinf_ok else "ไม่ผ่าน ❌")

    with dcol3:
        with st.container(border=True):
            st.markdown("**เหล็กปลอก (Stirrup)**")
            st.write(f"S_max ที่คำนวณได้ = {result.stirrup.s_max_cm:.1f} cm.")
            if result.stirrup.section_too_small:
                st.error("⚠️ หน้าตัดคานเล็กเกินไปสำหรับแรงเฉือนนี้ — กรุณาขยายขนาดคาน")
            st.write(f"**เหล็กที่ใช้จริง: {result.reinf_label_stirrup}**")
            st.write("ผลตรวจสอบ:", "ผ่าน ✅" if result.stirrup.stirrup_ok else "ไม่ผ่าน ❌")

    # ทางเลือก: ออกแบบรับแรงบิด (Torsion) — คำนวณเมื่อผู้ใช้เปิดใช้งานและกรอก Tu > 0
    _calc_sections = _build_calc_sections(inp, result)
    _tor = None
    if st.session_state.get("beam_torsion_enabled") and st.session_state.get("beam_tu_kgm", 0.0) > 0:
        from common.torsion import design_beam_torsion
        from modules.beam_single_span import COVER_CM as _BEAM_COVER
        _fyv = GS_STEEL_FY_KSC[inp.stirrup_steel_type]
        _fyl = GS_STEEL_FY_KSC[inp.main_steel_type]
        _tor = design_beam_torsion(
            st.session_state["beam_tu_kgm"], result.vu_max_kg, inp.b_cm, inp.h_cm,
            result.bottom.d_cm, inp.fc_ksc, _fyv, _fyl, _BEAM_COVER,
            inp.stirrup_bar_dia_mm, inp.stirrup_legs, result.stirrup.vc_kg,
            result.stirrup.av_cm2, inp.stirrup_spacing_use_cm)
        _tstatus = "warn" if (_tor.required and not _tor.section_ok) else (_tor.stirrup_ok if _tor.required else True)
        metric_card_row([
            {"name": "แรงบิด Tu", "sym": "Torsion", "value": f"{_tor.tu_kgm:,.0f}", "unit": "kg·m",
             "ok": None},
            {"name": "ต้องออกแบบแรงบิด?", "sym": f"เกณฑ์ {_tor.tth_kgm:,.0f}", "value": "ใช่" if _tor.required else "ไม่",
             "unit": "kg·m", "ok": None},
            {"name": "เหล็กปลอกรับบิด At/s", "sym": "ต่อขา", "value": f"{_tor.at_s:.4f}", "unit": "cm²/cm",
             "ok": _tor.stirrup_ok if _tor.required else None,
             "reason": f"@{_tor.s_required_cm:.0f}cm" if _tor.required else "-"},
            {"name": "เหล็กยืนรับบิด Al", "sym": "รวมรอบรูป", "value": f"{_tor.al_design_cm2:.2f}", "unit": "cm²",
             "ok": _tor.section_ok if _tor.required else None,
             "reason": "หน้าตัดพอ" if _tor.section_ok else "หน้าตัดเล็กไป"},
        ])
        st.write("")
        from common.torsion import build_torsion_section
        _calc_sections = _calc_sections + [build_torsion_section(_tor, result.stirrup_bar_type)]

    # --- การโก่งตัว (Deflection) ตามมาตรฐาน ACI: โหลด service + Ie (Branson) + long-term ---
    _w_dl_s = inp.line_load_dl_kg_m + result.self_weight_kg_m      # โหลดคงค้าง (DL) รวมน้ำหนักตัวเอง
    _w_ll_s = inp.line_load_ll_kg_m
    _tot_service = (_w_dl_s + _w_ll_s) * inp.L_m + sum(p.p_dl_kg + p.p_ll_kg for p in inp.point_loads)
    _tot_factored = result.wu_kg_m * inp.L_m + sum(pu for _, pu in result.pu_loads)
    _tot_sustained = _w_dl_s * inp.L_m + sum(p.p_dl_kg for p in inp.point_loads)
    _r_service = (_tot_service / _tot_factored) if _tot_factored > 0 else 0.0
    _sustained_frac = (_tot_sustained / _tot_service) if _tot_service > 0 else 0.0
    _as_comp = result.bottom.as_comp_req_cm2 if result.bottom.doubly_reinforced else 0.0
    _dpkg = compute_service_deflection(
        result.x_arr, result.m_arr, inp.b_cm, inp.h_cm, result.bottom.d_cm, inp.fc_ksc,
        result.bottom.as_provided_cm2, _as_comp, result.mu_max_kg_m,
        r_service=_r_service, sustained_frac=_sustained_frac, span_L_m=inp.L_m,
        support_xs=[0.0, inp.L_m], allow_ratio=360.0)
    _calc_sections = _calc_sections + [build_deflection_calc_section(_dpkg, inp.b_cm, inp.h_cm, inp.fc_ksc)]

    metric_card_row([
        ("โก่งทันที δi (service+Ie)", f"{_dpkg['imm_max']:.2f}", "mm", None),
        ("โก่งรวม δtotal (+long-term)", f"{_dpkg['total_max']:.2f}", f"mm ที่ x={_dpkg['imm_x']:.2f} m", None),
        ("ค่าที่ยอมให้ δallow", f"{_dpkg['allow_mm']:.2f}", "mm (L/360)", None),
        ("ผลตรวจสอบการโก่งตัว", "ผ่าน" if _dpkg["ok"] else "ไม่ผ่าน", "δtotal ≤ δallow", _dpkg["ok"]),
    ])
    st.write("")

    st.subheader("วิธีการคำนวณและสูตรที่ใช้")
    render_calc_sheet(_calc_sections)

    st.subheader("กราฟแรงเฉือน & โมเมนต์ & การโก่งตัว (SFD / BMD / Deflection)")
    sfd_bmd_png = draw_beam_sfd_bmd_png(
        result.x_arr, result.v_arr, result.m_arr, inp.L_m,
        result.vu_max_kg, result.mu_max_kg_m, result.mu_max_x_m,
        defl_mm=_dpkg["total_arr"], defl_max_mm=_dpkg["total_max"], defl_max_x_m=_dpkg["imm_x"])
    _sfd_lm, _sfd_c, _sfd_rm = st.columns([1.5, 7, 1.5])   # SFD/BMD 70% ของความกว้าง จัดกึ่งกลางหน้า
    with _sfd_c:
        st.image(sfd_bmd_png, use_container_width=True)

    st.subheader("รูปตัดคาน (Beam Section)")
    section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, result.bottom.bars_per_layer, result.top.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type,
        torsion=_tor)
    _sec_w = _scaled_width(section_png, 2.0)   # ขยายรูปตัดคาน 2 เท่า + จัดกึ่งกลางหน้า
    centered_image(section_png, width=_sec_w, caption="Beam Section")

    # --- ทางเลือก: จัดเหล็กเสริมเอง (Manual Rebar Arrangement) แบบตารางตามภาพอ้างอิง ---
    from common.rebar_editor import manual_beam_section, MANUAL_REBAR_CSS
    st.markdown(MANUAL_REBAR_CSS, unsafe_allow_html=True)
    with st.container(key="npk-manual-rebar"):
        with st.expander("🔧 จัดเหล็กเสริมเอง (Manual Rebar Arrangement)", expanded=False):
            st.caption("ปรับจำนวน/ขนาดเหล็กแต่ละชั้น (Main / Extra) เอง — คำนวณ As,use เทียบ As,req (OK/NG) "
                       "และวาดรูปตัดใหม่ตามที่จัด (ตาราง=ซ้าย รูปตัด=ขวา เห็นพร้อมกัน / ค่าชั่วคราว ไม่บันทึก)")
            _ecol, _dcol = st.columns([2.3, 1.1])
            with _ecol:
                _mres = manual_beam_section(
                    "bs_manual", "รูปตัดคาน (Beam Section)",
                    as_req_top=result.top.as_req_cm2, as_req_bot=result.bottom.as_req_cm2,
                    default_top=result.top.bars_per_layer, default_bot=result.bottom.bars_per_layer,
                    b_cm=inp.b_cm, h_cm=inp.h_cm, main_bar_type=result.main_bar_type, main_dia=inp.main_bar_dia_mm,
                    bar_sizes=BAR_DIAMETERS_MM, stirrup_dia=inp.stirrup_bar_dia_mm, stirrup_type=result.stirrup_bar_type,
                    s_use_default=inp.stirrup_spacing_use_cm, s_max_cm=result.stirrup.s_max_cm, gen=gen, torsion=_tor,
                    stirrup_sizes=STIRRUP_DIAMETERS_MM)
            with _dcol:
                centered_image(_mres["png"], caption="Beam Section (Manual)")

    report_html = build_beam_report_html(
        project, inp, result, sfd_bmd_png, section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )

    # กดปุ่ม "แสดงรายการคำนวณ" ด้านบนแล้วเท่านั้นถึงจะฝังรายการคำนวณฉบับเต็มไว้ในหน้า (ลดความ
    # หนักของหน้าเมื่อยังไม่ต้องการดู) — ปุ่มดาวน์โหลดใช้ได้เสมอไม่ต้องรอแสดงรายการคำนวณก่อน
    sync_report_html("bs", report_html)

    download_report_button("ดาวน์โหลดรายการคำนวณ", report_html, f"รายการคำนวณ_{project['beam_name']}")
