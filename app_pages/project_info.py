"""
หน้ากลาง — ข้อมูลโครงการ (Project Information)

ใช้กรอกข้อมูลโลโก้บริษัท/เจ้าของ/โครงการ/ที่ตั้ง/ผู้ออกแบบ ครั้งเดียว
เก็บไว้ใน st.session_state["project_info"] (และโลโก้ใน project_logo_bytes/
project_logo_mime) เพื่อใช้พิมพ์เป็นปกรายงาน — และในอนาคตโมดูลอื่น ๆ จะดึง
ข้อมูลนี้ไปแสดงหัวรายการคำนวณร่วมกันได้

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

import base64

import streamlit as st
import streamlit.components.v1 as components
from common.app_state import PROJECT_INFO_DEFAULTS as DEFAULTS, load_default_logo
from common.pdf_export import download_report_button
from common.report import build_cover_page_html
from common.report_preview import open_preview_button
from common.settings import save_settings
from common.ui_style import inject_card_css, input_card

# หมายเหตุ: session_state["project_info"]/["project_logo_bytes"]/["project_logo_mime"]/
# ["project_cover_image_bytes"]/["pi_form_gen"] ถูกตั้งค่าเริ่มต้นไว้แล้วที่ app.py
# (เรียก common.app_state.ensure_initialized() ก่อนเข้าหน้าไหนก็ได้เสมอ) โดยดึงค่า
# ที่บันทึกไว้ล่าสุดจากไฟล์ (common.settings) มาใช้ก่อน ถ้ายังไม่เคยบันทึกเลยจึงใช้
# DEFAULTS ด้านบน — หน้านี้จึงไม่ต้อง init เองซ้ำอีก

st.header("ข้อมูลโครงการ")
inject_card_css()

# สี 4 ปุ่ม (เลือกโลโก้ใหม่=ฟ้า / บันทึกข้อมูล=ส้ม / คืนค่าเริ่มต้น=เหลือง / พิมพ์ปกรายงาน=เขียว)
# ให้ใกล้เคียงต้นแบบ โดยอ้างอิง CSS ผ่าน key ของ st.container
st.markdown("""
<style>
.st-key-btn_logo section[data-testid="stFileUploaderDropzone"] button,
.st-key-btn_logo button { background-color:#3b82f6 !important; color:white !important; border:none !important; }
.st-key-btn_cover_img section[data-testid="stFileUploaderDropzone"] button { background-color:#3b82f6 !important; color:white !important; border:none !important; }
.st-key-btn_save button { background-color:#f97316 !important; color:white !important; border:none !important; }
.st-key-btn_reset button { background-color:#facc15 !important; color:#111 !important; border:none !important; }
.st-key-btn_print button { background-color:#22c55e !important; color:white !important; border:none !important; }
</style>
""", unsafe_allow_html=True)

# นับรุ่นฟอร์มไว้ก่อน (ใช้ตั้ง key ของ text_input และ file_uploader ทุกตัวในหน้านี้) —
# ต้องอยู่ก่อนตัว widget ทุกตัวที่ต้องรีเซ็ตได้ เพราะ file_uploader เองก็มีปัญหาเดียวกับ
# text_input (ค้างไฟล์ที่เคยเลือกไว้ข้าม rerun ถ้า key ไม่เปลี่ยน) ไม่ใช่แค่ text_input
gen = st.session_state["pi_form_gen"]
k_owner, k_project, k_location, k_engineer = (
    f"pi_owner_{gen}", f"pi_project_{gen}", f"pi_location_{gen}", f"pi_engineer_{gen}",
)
k_logo_uploader = f"logo_uploader_{gen}"
k_cover_img_uploader = f"cover_img_uploader_{gen}"

with input_card("ข้อมูลโครงการ", color="blue", icon="🏢", key="pi-info"):
    col_logo, col_fields = st.columns([1, 2])

    with col_logo:
        st.markdown("**โลโก้บริษัท**")
        # กล่องโลโก้สัดส่วน 1:1 (สี่เหลี่ยมจตุรัส) — วางโลโก้ไว้กลางกล่องแบบ object-fit:contain
        # (ไม่บิดสัดส่วนภาพจริง) ทั้งกรณีมีโลโก้และยังไม่มีโลโก้ให้เป็นกรอบขนาดเท่ากัน
        if st.session_state["project_logo_bytes"]:
            _logo_b64 = base64.b64encode(st.session_state["project_logo_bytes"]).decode("ascii")
            _logo_mime = st.session_state.get("project_logo_mime") or "image/png"
            st.markdown(
                f'<div style="width:180px;height:180px;border:1px solid #D8DEE7;border-radius:8px;'
                f'display:flex;align-items:center;justify-content:center;background:#fff;'
                f'overflow:hidden;padding:8px;box-sizing:border-box;">'
                f'<img src="data:{_logo_mime};base64,{_logo_b64}" '
                f'style="max-width:100%;max-height:100%;object-fit:contain;"></div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="width:180px;height:180px;border:1px dashed #999;border-radius:8px;'
                'display:flex;align-items:center;justify-content:center;color:#999;'
                'font-size:13px;">ยังไม่มีโลโก้</div>',
                unsafe_allow_html=True,
            )
        with st.container(key="btn_logo"):
            uploaded = st.file_uploader("เลือกโลโก้ใหม่", type=["png", "jpg", "jpeg"], key=k_logo_uploader)
            if uploaded is not None:
                new_bytes = uploaded.getvalue()
                if new_bytes != st.session_state.get("project_logo_bytes"):
                    st.session_state["project_logo_bytes"] = new_bytes
                    st.session_state["project_logo_mime"] = uploaded.type
                    st.rerun()

    with col_fields:
        st.text_input("เจ้าของ", value=st.session_state["project_info"]["owner"], key=k_owner)
        st.text_input("โครงการ", value=st.session_state["project_info"]["project_name"], key=k_project)
        st.text_input("ที่ตั้ง", value=st.session_state["project_info"]["location"], key=k_location)
        st.text_input("ผู้ออกแบบ", value=st.session_state["project_info"]["engineer"], key=k_engineer)

# หน้าข้อมูลโครงการ: ช่องกรอกเป็นข้อความยาว (ชื่อโครงการ/ที่ตั้ง/ผู้ออกแบบ) ไม่ใช่ตัวเลข —
# ทับ CSS แบบ ETABS (ที่บีบช่องเหลือ ~150px ชิดขวา ทำให้ข้อความยาวถูกตัด) ให้ช่องเต็มความกว้าง
# ชิดซ้าย label กว้างเท่ากันทุกแถวเพื่อให้ช่องกรอกเริ่มตรงกัน — วางหลังการ์ดเพื่อให้ทับ compact CSS
st.markdown("""
<style>
.st-key-npk-ic-blue-pi-info [data-testid="stTextInput"] { gap:16px !important; }
.st-key-npk-ic-blue-pi-info [data-testid="stTextInput"] > label {
    flex:0 0 96px !important; width:96px !important; min-width:96px !important;
}
.st-key-npk-ic-blue-pi-info [data-testid="stTextInput"] > div {
    flex:1 1 auto !important; width:auto !important; max-width:none !important;
}
.st-key-npk-ic-blue-pi-info [data-testid="stTextInput"] input {
    text-align:left !important; font-weight:500 !important;
}
</style>
""", unsafe_allow_html=True)

st.write("")
st.markdown("**ภาพหน้าปก (แบบก่อสร้าง / รูปบ้าน)**")
st.caption("แสดงกลางหน้าปกรายงาน ขนาดจะปรับให้พอดีอัตโนมัติโดยไม่บิดเบี้ยว (ไม่มีค่าเริ่มต้น — อัพโหลดเองได้)")
with input_card("ภาพหน้าปก (แบบก่อสร้าง / รูปบ้าน)", color="green", icon="🖼️", key="pi-cover"):
    col_cimg, col_cimg_upload = st.columns([1, 2])
    with col_cimg:
        if st.session_state["project_cover_image_bytes"]:
            st.image(st.session_state["project_cover_image_bytes"], width=200)
        else:
            st.markdown(
                '<div style="width:200px;height:130px;border:1px dashed #999;'
                'display:flex;align-items:center;justify-content:center;color:#999;'
                'font-size:13px;">ยังไม่มีภาพ</div>',
                unsafe_allow_html=True,
            )
    with col_cimg_upload:
        with st.container(key="btn_cover_img"):
            uploaded_cover = st.file_uploader(
                "เลือกภาพแบบก่อสร้าง/รูปบ้าน", type=["png", "jpg", "jpeg"], key=k_cover_img_uploader)
            if uploaded_cover is not None:
                new_cimg_bytes = uploaded_cover.getvalue()
                if new_cimg_bytes != st.session_state.get("project_cover_image_bytes"):
                    st.session_state["project_cover_image_bytes"] = new_cimg_bytes
                    st.session_state["project_cover_image_mime"] = uploaded_cover.type
                    st.rerun()
            if st.session_state["project_cover_image_bytes"] and st.button("ลบภาพหน้าปก"):
                st.session_state["project_cover_image_bytes"] = None
                st.session_state["project_cover_image_mime"] = None
                # ต้องเปลี่ยน key ของ file_uploader ด้วย (เพิ่ม gen) ไม่งั้นตัว uploader
                # จะยังค้างไฟล์เดิมและ set ค่ากลับมาใหม่ทันทีใน rerun ถัดไป (บั๊กเดียวกับ
                # ตอนกด "คืนค่าเริ่มต้น" — ดูคอมเมนต์ตรงปุ่มนั้น)
                st.session_state["pi_form_gen"] += 1
                st.rerun()

st.write("")
b1, b2, b3 = st.columns(3)

with b1:
    with st.container(key="btn_save"):
        if st.button("บันทึกข้อมูล", use_container_width=True):
            st.session_state["project_info"] = {
                "owner": st.session_state[k_owner],
                "project_name": st.session_state[k_project],
                "location": st.session_state[k_location],
                "engineer": st.session_state[k_engineer],
            }
            # บันทึกลงไฟล์ด้วย เพื่อให้โปรแกรมจำค่านี้ไว้ใช้เป็นค่าเริ่มต้นทุกครั้งที่
            # เปิดโปรแกรมใหม่ ไม่ต้องมาคลิกเปิดหน้านี้ก่อน (ตามคำขอผู้ใช้)
            save_settings("project_info", st.session_state["project_info"])
            st.success("บันทึกข้อมูลแล้ว (จำค่านี้ไว้ใช้ทุกครั้งที่เปิดโปรแกรม)")

with b2:
    with st.container(key="btn_reset"):
        if st.button("คืนค่าเริ่มต้น", use_container_width=True):
            st.session_state["project_info"] = dict(DEFAULTS)
            logo_bytes, logo_mime = load_default_logo()  # กลับไปใช้โลโก้เริ่มต้น data/logo.png
            st.session_state["project_logo_bytes"] = logo_bytes
            st.session_state["project_logo_mime"] = logo_mime
            st.session_state["project_cover_image_bytes"] = None
            st.session_state["project_cover_image_mime"] = None
            st.session_state["show_cover"] = False
            st.session_state["pi_form_gen"] += 1  # เปลี่ยน key ฟอร์ม -> เคลียร์ช่องกรอกจริง
            # เคลียร์ค่าที่บันทึกไว้ในไฟล์ด้วย ไม่งั้นเปิดโปรแกรมใหม่จะกลับไปโหลด
            # ค่าที่เคยบันทึกไว้ก่อนกด "คืนค่าเริ่มต้น" อีก (ควรให้ค่ามาตรฐานนี้เป็น
            # ค่าที่จำไว้ใช้ครั้งถัดไปด้วย)
            save_settings("project_info", st.session_state["project_info"])
            st.rerun()

with b3:
    # ปุ่ม "พิมพ์ปกรายงาน" — เปิดหน้าต่าง Preview เหมือนปุ่ม "แสดงรายการคำนวณ" ในหน้าโมดูล
    # (ไม่ฝังพรีวิวปกในหน้าอีกต่อไป — ตัดส่วนซ้ำออกตามหน้าอื่น) หน้าต่าง Preview มีปุ่มพิมพ์/
    # บันทึก PDF ในตัวอยู่แล้ว — สร้าง cover_html ตรงนี้ (หลังคอลัมน์ b1 "บันทึกข้อมูล" รันไปแล้ว
    # ในรอบเดียวกัน) เพื่อให้ได้ค่าล่าสุด
    cover_html = build_cover_page_html(
        st.session_state["project_info"],
        st.session_state["project_logo_bytes"],
        st.session_state["project_logo_mime"],
        st.session_state["project_cover_image_bytes"],
        st.session_state["project_cover_image_mime"],
    )
    open_preview_button("🖨️ พิมพ์ปกรายงาน", cover_html, key="pvcover", color="#22c55e", height=52)
