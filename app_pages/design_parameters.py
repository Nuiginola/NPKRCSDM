"""
หน้ากลาง — พารามิเตอร์การออกแบบ (Design Parameters)

ใช้ร่วมกันในโมดูลที่ต้องใช้ beta1/rho_min/rho_max/phi (คาน เสา พื้นทางเดียว/สองทาง
ฯลฯ ที่จะสร้างต่อไป) — ไม่ได้ใช้ในโมดูลพื้นวางบนดินซึ่งมีเกณฑ์ของตัวเอง

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import streamlit as st
import streamlit.components.v1 as components
from common.design_params import calculate as calc_params, STEEL_FY_KSC, LOAD_SCHEDULE, LOAD_FACTOR_NOTE, LOAD_SCHEDULE_SOURCE
from common.pdf_export import download_report_button
from common.report import build_design_params_report_html
from common.report_preview import open_preview_button
from common.settings import save_settings
from common.ui_style import inject_card_css, input_card, metric_card_row

st.header("พารามิเตอร์การออกแบบ (Design Parameters)")
inject_card_css()

# แยกช่องเลือกเหล็ก SR (เหล็กเส้นกลม) กับ SD (เหล็กข้ออ้อย) ออกจากกันคนละช่อง
# ตามคำขอผู้ใช้ — ใช้พร้อมกันได้ทั้งคู่ (ไม่ใช่เลือกอย่างใดอย่างหนึ่ง) เพราะงานจริง
# มักใช้เหล็กสองชนิดร่วมกันในโครงสร้างเดียว (เช่น SD40 เป็นเหล็กหลัก, SR24 เป็น
# เหล็กปลอก/เหล็กรอง)
SR_OPTIONS = [k for k in STEEL_FY_KSC if k.startswith("SR")]
SD_OPTIONS = [k for k in STEEL_FY_KSC if k.startswith("SD")]

# ค่าเริ่มต้นของฟอร์ม — ดึงจากค่าที่บันทึกไว้ล่าสุด (ตั้งไว้แล้วที่ app.py ผ่าน
# common.app_state.ensure_initialized() ก่อนเข้าหน้าไหนก็ได้เสมอ) แทนที่จะ hardcode
# 240.0/SR24/SD40 ตรงๆ — เพื่อให้ฟอร์มโชว์ค่าที่ผู้ใช้เคยตั้งไว้ล่าสุดทุกครั้ง
_fc_default = st.session_state.get("design_params_fc", 240.0)
_sr_default = st.session_state.get("design_params_steel_sr", "SR24")
_sd_default = st.session_state.get("design_params_steel_sd", "SD40")

with input_card("พารามิเตอร์หลัก", color="blue", icon="⚙️", key="dp-main"):
    col1, col2, col3 = st.columns(3)
    with col1:
        fc = st.number_input("กำลังอัดประลัยคอนกรีตที่อายุ 28 วัน f'c (kg/cm²)", value=_fc_default, step=10.0)
    with col2:
        steel_type_sr = st.selectbox(
            "เหล็กเสริม SR (เหล็กเส้นกลม)", options=SR_OPTIONS,
            index=SR_OPTIONS.index(_sr_default) if _sr_default in SR_OPTIONS else 0,
            format_func=lambda k: f"{k} (fy={STEEL_FY_KSC[k]:.0f} ksc)")
    with col3:
        steel_type_sd = st.selectbox(
            "เหล็กเสริม SD (เหล็กข้ออ้อย)", options=SD_OPTIONS,
            index=SD_OPTIONS.index(_sd_default) if _sd_default in SD_OPTIONS else 0,
            format_func=lambda k: f"{k} (fy={STEEL_FY_KSC[k]:.0f} ksc)")

params_sr = calc_params(fc, steel_type_sr)
params_sd = calc_params(fc, steel_type_sd)
# เก็บ key เดิม "design_params" ไว้เพื่อ backward-compat กับหน้าโมดูลอื่นที่อ่านแค่
# .fc_ksc มาเป็นค่าเริ่มต้น (fc_ksc เหมือนกันทั้งสองชุดอยู่แล้ว ไม่กระทบ) — เพิ่ม 2
# key ใหม่แยกชุด SR/SD ไว้เผื่ออนาคตอยากใช้ fy แยกชนิดในโมดูลอื่น
st.session_state["design_params"] = params_sd
st.session_state["design_params_sr"] = params_sr
st.session_state["design_params_sd"] = params_sd
st.session_state["design_params_fc"] = fc
st.session_state["design_params_steel_sr"] = steel_type_sr
st.session_state["design_params_steel_sd"] = steel_type_sd

# บันทึกค่านี้ลงไฟล์ทันทีทุกครั้งที่มีการเปลี่ยนแปลง (ไม่ต้องกดปุ่ม "บันทึก" ใดๆ) —
# เพื่อให้โปรแกรมจำค่านี้ไว้ใช้เป็นค่าเริ่มต้นทุกครั้งที่เปิดโปรแกรมใหม่ในอนาคต
# (ตามคำขอผู้ใช้ — ไม่ต้องคลิกเข้าหน้านี้โปรแกรมก็ต้องจำค่าไว้)
_dp_to_save = {"fc": fc, "steel_type_sr": steel_type_sr, "steel_type_sd": steel_type_sd}
if st.session_state.get("_design_params_last_saved") != _dp_to_save:
    save_settings("design_params", _dp_to_save)
    st.session_state["_design_params_last_saved"] = _dp_to_save

st.subheader("คุณสมบัติวัสดุ")
metric_card_row([
    ("f'c", f"{params_sd.fc_ksc:.0f}", "kg/cm²", None),
    ("Ec = 15,100√f'c", f"{params_sd.ec_ksc:.0f}", "kg/cm²", None),
    ("β1", f"{params_sd.beta1:.2f}", "ขึ้นกับ f'c เท่านั้น (ใช้ค่าเดียวกันทั้งสองชนิดเหล็ก)", None),
    (f"fy — {params_sr.steel_type}", f"{params_sr.fy_ksc:.0f}", "kg/cm²", None),
    (f"fy — {params_sd.steel_type}", f"{params_sd.fy_ksc:.0f}", "kg/cm²", None),
    ("Es", f"{params_sd.es_ksc:.0f}", "kg/cm² (ค่าเดียวกันทุกชั้นคุณภาพ)", None),
])

with st.container(border=True):
    st.subheader("วิธีกำลัง (Strength Design Method)")
    rho_rows = [
        {"ชนิดเหล็ก": params_sr.steel_type, "ρb": f"{params_sr.rho_b:.4f}",
         "ρmin = 14/fy": f"{params_sr.rho_min:.4f}", "ρmax = 0.75ρb": f"{params_sr.rho_max:.4f}"},
        {"ชนิดเหล็ก": params_sd.steel_type, "ρb": f"{params_sd.rho_b:.4f}",
         "ρmin = 14/fy": f"{params_sd.rho_min:.4f}", "ρmax = 0.75ρb": f"{params_sd.rho_max:.4f}"},
    ]
    st.table(rho_rows)
    p4 = st.container()
    with p4:
        st.write("กฎกระทรวง พ.ศ. 2566: U = 1.4D + 1.7L")
        st.write("มาตรฐาน วสท. 011008-21: U = 1.4D + 1.7L")
        st.write(f"ตัวคูณลดกำลังดัด φb = {params_sd.phi_b:.2f}")
        st.write(f"ตัวคูณลดกำลังเฉือน φv = {params_sd.phi_v:.2f}")
        st.write(f"ตัวคูณลดกำลังอัด φ = {params_sd.phi_c:.2f}")

with st.container(border=True):
    st.subheader("รายการน้ำหนักบรรทุกจร (Live Load) มาตรฐาน")
    load_rows = [{"ลักษณะการใช้งาน": r["usage"], "น้ำหนักบรรทุกจร LL (kg/m²)": r["ll_kg_m2"]}
                 for r in LOAD_SCHEDULE]
    st.table(load_rows)
    st.write(f"ตัวคูณน้ำหนักบรรทุก: {LOAD_FACTOR_NOTE}")
    st.caption(LOAD_SCHEDULE_SOURCE)

st.divider()
report_html = build_design_params_report_html(
    params_sr,
    params_sd,
    st.session_state.get("project_info"),
    st.session_state.get("project_logo_bytes"),
    st.session_state.get("project_logo_mime"),
    load_schedule=LOAD_SCHEDULE,
    load_factor_note=LOAD_FACTOR_NOTE,
    load_schedule_source=LOAD_SCHEDULE_SOURCE,
)
# ปุ่ม "แสดง/พิมพ์พารามิเตอร์" — เปิดหน้าต่าง Preview เหมือนปุ่ม "แสดงรายการคำนวณ" ในหน้าโมดูล
# (ไม่ฝังพรีวิวในหน้าอีกต่อไป — ตัดส่วนซ้ำออก) หน้าต่าง Preview มีปุ่มพิมพ์/บันทึก PDF ในตัวอยู่แล้ว
open_preview_button("📄 แสดงพารามิเตอร์การออกแบบ", report_html, key="pvtop_dp", color="#2563EB", height=52)
download_report_button("ดาวน์โหลดพารามิเตอร์การออกแบบ", report_html, "พารามิเตอร์การออกแบบ")
