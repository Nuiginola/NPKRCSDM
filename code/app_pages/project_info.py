"""
หน้ากลาง — ข้อมูลโครงการ (Project Information)

ใช้กรอกข้อมูลโลโก้บริษัท/เจ้าของ/โครงการ/ที่ตั้ง/ผู้ออกแบบ ครั้งเดียว
เก็บไว้ใน st.session_state["project_info"] (และโลโก้ใน project_logo_bytes/
project_logo_mime) เพื่อใช้พิมพ์เป็นปกรายงาน — และในอนาคตโมดูลอื่น ๆ จะดึง
ข้อมูลนี้ไปแสดงหัวรายการคำนวณร่วมกันได้

Note: st.set_page_config() is NOT called here — it is called once in app.py
before st.navigation(), which is required when using the navigation API.
"""

from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components
from common.report import build_cover_page_html

# ค่าเริ่มต้นของข้อมูลโครงการ — ให้โปรแกรมเปิดมาแสดงข้อมูลชุดนี้ทุกครั้ง (ตามที่ผู้ใช้ระบุ)
DEFAULTS = {
    "owner": "NPK RC SDM",
    "project_name": "อาคารคอนกรีตเสริมเหล็ก",
    "location": "ต.ฟ้าฮ่าม อ.เมือง จ.เชียงใหม่",
    "engineer": "นายเก่งมาก เชียวชาญ",
}

# โลโก้เริ่มต้น — ไฟล์ที่ผู้ใช้เตรียมไว้ใน data/logo.png (ส่งมาพร้อมโค้ด) โหลดอัตโนมัติ
# ทุกครั้งที่โปรแกรมเปิด/กด "คืนค่าเริ่มต้น" โดยไม่ต้องอัพโหลดใหม่เอง
_DEFAULT_LOGO_PATH = Path(__file__).resolve().parent.parent / "data" / "logo.png"


def _load_default_logo():
    """คืนค่า (bytes, mime) ของโลโก้เริ่มต้นจาก data/logo.png ถ้ามีไฟล์อยู่จริง
    ไม่งั้นคืน (None, None) (กันแอปพังถ้าไฟล์หาย)"""
    if _DEFAULT_LOGO_PATH.exists():
        return _DEFAULT_LOGO_PATH.read_bytes(), "image/png"
    return None, None


if "project_info" not in st.session_state:
    st.session_state["project_info"] = dict(DEFAULTS)
if "project_logo_bytes" not in st.session_state:
    logo_bytes, logo_mime = _load_default_logo()
    st.session_state["project_logo_bytes"] = logo_bytes
    st.session_state["project_logo_mime"] = logo_mime
if "project_cover_image_bytes" not in st.session_state:
    # ภาพแบบก่อสร้าง/รูปบ้าน ที่แสดงกลางหน้าปกรายงาน — ไม่มีค่าเริ่มต้น (ผู้ใช้อัพโหลดเอง)
    st.session_state["project_cover_image_bytes"] = None
    st.session_state["project_cover_image_mime"] = None
if "pi_form_gen" not in st.session_state:
    # นับรุ่นของฟอร์ม — ใช้เปลี่ยน key ของ text_input ตอนกด "คืนค่าเริ่มต้น"
    # (แค่ลบ session_state[key] แล้ว rerun() เฉย ๆ ยังโชว์ค่าเดิมค้างอยู่ ต้อง
    # เปลี่ยน key ให้เป็น widget ใหม่จริง ๆ ถึงจะเคลียร์ค่าที่พิมพ์ไว้ได้)
    st.session_state["pi_form_gen"] = 0

st.header("ข้อมูลโครงการ")

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

col_logo, col_fields = st.columns([1, 2])

with col_logo:
    st.markdown("**โลโก้บริษัท**")
    if st.session_state["project_logo_bytes"]:
        st.image(st.session_state["project_logo_bytes"], width=160)
    else:
        st.markdown(
            '<div style="width:160px;height:110px;border:1px dashed #999;'
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

st.write("")
st.markdown("**ภาพหน้าปก (แบบก่อสร้าง / รูปบ้าน)**")
st.caption("แสดงกลางหน้าปกรายงาน ขนาดจะปรับให้พอดีอัตโนมัติโดยไม่บิดเบี้ยว (ไม่มีค่าเริ่มต้น — อัพโหลดเองได้)")
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
            st.success("บันทึกข้อมูลแล้ว")

with b2:
    with st.container(key="btn_reset"):
        if st.button("คืนค่าเริ่มต้น", use_container_width=True):
            st.session_state["project_info"] = dict(DEFAULTS)
            logo_bytes, logo_mime = _load_default_logo()  # กลับไปใช้โลโก้เริ่มต้น data/logo.png
            st.session_state["project_logo_bytes"] = logo_bytes
            st.session_state["project_logo_mime"] = logo_mime
            st.session_state["project_cover_image_bytes"] = None
            st.session_state["project_cover_image_mime"] = None
            st.session_state["show_cover"] = False
            st.session_state["pi_form_gen"] += 1  # เปลี่ยน key ฟอร์ม -> เคลียร์ช่องกรอกจริง
            st.rerun()

with b3:
    with st.container(key="btn_print"):
        if st.button("พิมพ์ปกรายงาน", use_container_width=True):
            st.session_state["show_cover"] = True

if st.session_state.get("show_cover"):
    st.divider()
    cover_html = build_cover_page_html(
        st.session_state["project_info"],
        st.session_state["project_logo_bytes"],
        st.session_state["project_logo_mime"],
        st.session_state["project_cover_image_bytes"],
        st.session_state["project_cover_image_mime"],
    )
    components.html(cover_html, height=880, scrolling=True)
    st.download_button(
        "⬇️ ดาวน์โหลดปกรายงาน (เปิดแล้วกดพิมพ์ได้)",
        data=cover_html,
        file_name=f"ปกรายงาน_{st.session_state['project_info']['project_name'] or 'project'}.html",
        mime="text/html",
    )
