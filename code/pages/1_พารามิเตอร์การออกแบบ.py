"""
หน้ากลาง — พารามิเตอร์การออกแบบ (Design Parameters)

ใช้ร่วมกันในโมดูลที่ต้องใช้ beta1/rho_min/rho_max/phi (คาน เสา พื้นทางเดียว/สองทาง
ฯลฯ ที่จะสร้างต่อไป) — ไม่ได้ใช้ในโมดูลพื้นวางบนดินซึ่งมีเกณฑ์ของตัวเอง
"""

import streamlit as st
import streamlit.components.v1 as components
from common.design_params import calculate as calc_params, STEEL_FY_KSC
from common.report import build_design_params_report_html

st.set_page_config(page_title="NPK RC SDM - พารามิเตอร์การออกแบบ", layout="wide")

st.header("พารามิเตอร์การออกแบบ (Design Parameters)")
st.caption("ตั้งค่า f'c และชนิดเหล็กเสริมหลักที่นี่ครั้งเดียว ใช้ร่วมกันในโมดูลคาน เสา พื้นทางเดียว/สองทาง ฯลฯ ที่จะสร้างต่อไป")

col1, col2 = st.columns(2)
with col1:
    fc = st.number_input("กำลังอัดประลัยคอนกรีตที่อายุ 28 วัน f'c (kg/cm²)", value=240.0, step=10.0)
with col2:
    steel_type = st.selectbox("เหล็กเสริม", options=list(STEEL_FY_KSC.keys()),
                               format_func=lambda k: f"{k} (fy={STEEL_FY_KSC[k]:.0f} ksc)")

params = calc_params(fc, steel_type)
st.session_state["design_params"] = params

st.subheader("คุณสมบัติวัสดุ")
p1, p2 = st.columns(2)
with p1:
    st.write(f"f'c = {params.fc_ksc:.0f} kg/cm²")
    st.write(f"Ec = 15,100√f'c = {params.ec_ksc:.0f} kg/cm²")
with p2:
    st.write(f"เหล็กเสริม {params.steel_type} — fy = {params.fy_ksc:.0f} kg/cm²")
    st.write(f"Es = {params.es_ksc:.0f} kg/cm²")

st.subheader("วิธีกำลัง (Strength Design Method)")
p3, p4 = st.columns(2)
with p3:
    st.write(f"β1 = {params.beta1:.2f}")
    st.write(f"ρb = {params.rho_b:.4f}")
    st.write(f"ρmin = 14/fy = {params.rho_min:.4f}")
    st.write(f"ρmax = 0.75ρb = {params.rho_max:.4f}")
with p4:
    st.write("กฎกระทรวง พ.ศ. 2566: U = 1.4D + 1.7L")
    st.write("มาตรฐาน วสท. 011008-21: U = 1.4D + 1.7L")
    st.write(f"ตัวคูณลดกำลังดัด φb = {params.phi_b:.2f}")
    st.write(f"ตัวคูณลดกำลังเฉือน φv = {params.phi_v:.2f}")

st.divider()
report_html = build_design_params_report_html(params)
components.html(report_html, height=550, scrolling=True)
st.download_button(
    "⬇️ ดาวน์โหลด/พิมพ์พารามิเตอร์การออกแบบ",
    data=report_html,
    file_name="พารามิเตอร์การออกแบบ.html",
    mime="text/html",
)
