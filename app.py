"""
NPK RC SDM — โปรแกรมออกแบบคอนกรีตเสริมเหล็กโดยวิธีกำลัง (Strength Design Method)
งานวิจัยระดับปริญญาโท | ขอบเขต: อาคารบ้านพักอาศัย
กฎกระทรวง กำหนดการออกแบบโครงสร้างอาคารฯ พ.ศ. 2566

หน้าแรก / เมนูหลักของโปรแกรม — ใช้ st.navigation()/st.Page() (ไม่ใช่ pages/ folder
แบบ auto-discovery แบบเดิม) เพราะ st.page_link() แบบอ้างอิงด้วย string path ไปยัง
ไฟล์ที่มีชื่อภาษาไทย เจอบั๊ก KeyError('url_pathname') บนเครื่อง Windows ของผู้ใช้
การอ้างอิงด้วย st.Page object โดยตรงไม่มีปัญหานี้ และคุมชื่อเมนู (Thai label) ผ่าน
พารามิเตอร์ title=/label= ได้ตรงๆ โดยไม่ต้องพึ่งชื่อไฟล์ภาษาไทย

=== หน้าแรก (home()) — ออกแบบ UI ใหม่ทั้งหมด (2026-07-11) ===
ผู้ใช้ส่งภาพ mockup ใหม่ (โครงสร้าง/เลย์เอาต์ต่างจากรอบก่อนหน้าทั้งหมด — ไม่ใช่แค่
ปรับสี/การ์ด) ยืนยันขอบเขตผ่าน AskUserQuestion 2 รอบก่อนลงมือ:
  1. แถบต้นไม้เมนูซ้าย = เมนูนำทางครบ 13 โมดูล + รายการที่บันทึกซ้อนใต้แต่ละหมวด
     (เหมือนฟังก์ชันเดิมของ sidebar เก่า เปลี่ยนแค่สไตล์เป็นแบบ tree ตามภาพ)
  2. Dark mode + Hamburger menu มุมขวาบน = ทำให้ใช้งานได้จริง (ไม่ใช่ placeholder)
  3. ปุ่ม "ดาวน์โหลดข้อมูลทั้งหมด"/"ล้างข้อมูล" = ย้ายมาไว้แผงขวาเท่านั้น (เอาออกจาก
     sidebar เดิม)

สถาปัตยกรรมที่เปลี่ยน: หน้าแรกเลิกใช้ st.sidebar ของ Streamlit (ซึ่งหน้าอื่นๆ ทั้งหมด
ยังใช้อยู่ตามเดิมผ่าน _render_sidebar() — ยังไม่ได้แตะ เพราะขอบเขตรอบนี้คือ "เริ่มที่
Main Menu" เท่านั้น) เปลี่ยนเป็นโครงสร้างการ์ดแบบ 3 คอลัมน์ที่วาดเองทั้งหมด (แถบต้นไม้
ซ้าย / เนื้อหากลาง / แผงสรุปขวา) ใต้แถบหัวข้อ (topbar) แบบเต็มความกว้างที่มี
โลโก้+ปุ่มเปิด/บันทึก+ป้ายโครงการ/วิศวกร+เวอร์ชัน+ปุ่ม dark mode+เมนูแฮมเบอร์เกอร์ —
ตรวจสอบว่าเป็นหน้า "หน้าแรก" จริงก่อนตัดสินใจไม่เรียก _render_sidebar() (เทียบ identity
กับ home_page object ที่ st.navigation() คืนกลับมา พร้อม fallback เทียบ title กันเผื่อ)

ป้ายกำกับ "โครงการ"/"วิศวกร" บน topbar เป็นป้ายแสดงผลอย่างเดียว (ไม่ใช่ dropdown ที่
แก้ไขได้ตรงจุด) เพราะภาพ mockup รอบล่าสุดมีปุ่ม "ข้อมูลโครงการ"/"พารามิเตอร์ในการ
ออกแบบ" แยกต่างหากใต้หัวข้อต้อนรับอยู่แล้วสำหรับแก้ไขค่าจริง — เป็นข้อสันนิษฐานที่
สมเหตุสมผลจากภาพ ไม่ได้ถามผู้ใช้ตรงๆ อีกรอบ (บันทึกไว้ให้ตรวจสอบภายหลังได้)

Dark mode: เคยมีปุ่มสลับโหมดมืด/สว่างบน topbar (session_state["npk_dark_mode"] +
common/settings.py section "ui_prefs") แต่ผู้ใช้สั่งให้ตัดออกทั้งหมดแล้ว (2026-07-12) —
เหลือโหมดสว่างมาตรฐานเพียงโหมดเดียวทั้งแอป ไม่มีปุ่ม/ฟีเจอร์สลับโหมดอีกต่อไป

เมนูแฮมเบอร์เกอร์: เปิด popover แสดงข้อมูลเวอร์ชัน/ผู้พัฒนา + ปุ่มเรียกดูหน้าจอ
ข้อจำกัดความรับผิดชอบ (consent gate) อีกครั้ง — เป็นฟังก์ชันที่เพิ่มเข้ามาใหม่ ไม่ได้
ระบุจากผู้ใช้ตรงๆ ว่าต้องมีเนื้อหาอะไร เลือกเนื้อหาที่สมเหตุสมผลและมีประโยชน์จริง

Sub-item ในต้นไม้เมนู/การ์ดกลาง ใช้ป้ายกำกับสองภาษา "รหัส ชื่อไทย (English Name)"
ตรงกับที่ภาพ mockup แสดงไว้เป๊ะ (ยืนยันชื่อภาษาอังกฤษจากคอมเมนต์/docstring เดิมของ
แต่ละโมดูลในโปรเจกต์)

CSS สโคปเฉพาะหน้านี้เท่านั้น เพราะ st.navigation รัน script ของแต่ละหน้าแยกกัน (ไม่
carry-over ข้าม page) จึงไม่กระทบ st.container(border=True) ที่ใช้อยู่ในหน้าอื่น
(เช่น 1.2, 1.3) การ์ดแต่ละใบใช้ st.container(border=True, key="card-xxx") แล้ว
override สไตล์ด้วย CSS selector [class*="st-key-card-"] (Streamlit เติม class
"st-key-<key>" ให้ทุก container ที่ระบุ key= — วิธีนี้ผูกกับ testid/class จริงที่
ยืนยันแล้วจาก DOM dump ของ Streamlit 1.59.1 ไม่ใช่การเดา)

Entry point (Streamlit). Run with: streamlit run app.py
"""

import base64
import json
import sys
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from common.app_state import ensure_initialized
from common.project_store import (
    MODULE_LABELS,
    apply_project_bundle,
    build_project_bundle,
    get_items,
    clear_all_items,
    request_load,
    total_item_count,
)
st.set_page_config(page_title="NPK RC SDM", layout="wide")

_DATA_DIR = Path(__file__).resolve().parent / "data"
_LOGO_PATH = _DATA_DIR / "logo.png"
_ICON_DIR = _DATA_DIR / "icons"
_DISCLAIMER_PATH = _DATA_DIR / "disclaimer.png"

# สีประจำหมวด — sample จริงจากภาพ mockup ของผู้ใช้ (Main Menu.png) ด้วย PIL (รอบก่อนหน้า)
CATEGORY_COLORS = {
    "slab": "#D99A2B",
    "stair": "#F2762B",
    "beam": "#D63A2A",
    "column": "#1F5C99",
    "footing": "#4C8A3F",
}

# ชื่อภาษาอังกฤษของแต่ละโมดูลย่อย — ใช้คู่กับ MODULE_LABELS (ภาษาไทย) เพื่อแสดงป้าย
# สองภาษาแบบเดียวกับภาพ mockup ล่าสุด ("รหัส ชื่อไทย (English Name)")
MODULE_LABELS_EN = {
    "slab_on_ground": "Slab on Ground",
    "one_way_slab": "One-way Slab",
    "two_way_slab": "Two-way Slab",
    "cantilever_slab": "Cantilever Slab",
    "stair_straight": "Straight Stair",
    "stair_u_shape": "U Shape Stair",
    "beam_single_span": "Single-span Beam",
    "continuous_beam": "Continuous Beam",
    "cantilever_beam": "Cantilever Beam",
    "column_tied": "Rectangular Column",
    "column_spiral": "Circular Column",
    "footing_spread": "Spread Footing",
    "footing_pile_cap": "Pile Cap",
}

# แหล่งความจริงเดียว (single source of truth) ของ 5 หมวดหมู่ — ใช้ร่วมกันทั้งแถบ
# ต้นไม้ซ้าย, การ์ดกลาง, และแผงสรุปขวา กันข้อมูลหลุด sync กันระหว่าง 3 จุด
# แต่ละรายการ: (เลขหมวด, ชื่อหมวด(ไทย+English), icon_key, emoji, คำอธิบายสั้น, [module_key...])
CATEGORY_DEFS = [
    (1, "พื้น (Slab)", "slab", "🧱", "ออกแบบพื้นคอนกรีตเสริมเหล็ก หลากหลายประเภท",
     ["slab_on_ground", "one_way_slab", "two_way_slab", "cantilever_slab"]),
    (2, "บันได (Stair)", "stair", "🪜", "ออกแบบบันไดคอนกรีตเสริมเหล็ก หลายรูปแบบ",
     ["stair_straight", "stair_u_shape"]),
    (3, "คาน (Beam)", "beam", "🪵", "ออกแบบคานคอนกรีตเสริมเหล็ก แบบต่างๆ",
     ["beam_single_span", "continuous_beam", "cantilever_beam"]),
    (4, "เสา (Column)", "column", "🏛️", "ออกแบบเสาคอนกรีตเสริมเหล็ก แบบต่างๆ",
     ["column_tied", "column_spiral"]),
    (5, "ฐานราก (Footing)", "footing", "🏗️", "ออกแบบฐานรากคอนกรีตเสริมเหล็ก แบบต่างๆ",
     ["footing_spread", "footing_pile_cap"]),
]


def _img_base64(path: Path) -> str:
    """คืนค่ารูปเป็น base64 string สำหรับฝังใน HTML โดยตรง
    (คืนค่าว่างถ้าไม่พบไฟล์ กันแอปพัง)"""
    if path.exists():
        return base64.b64encode(path.read_bytes()).decode("utf-8")
    return ""


# ── ระบบเข้าสู่ระบบครั้งแรก (activation) ──────────────────────────────────────────
# กรอก username/password ครั้งเดียวหลังติดตั้ง+เปิดครั้งแรก แล้วจำถาวร (ไม่ถามอีก)
# รายชื่อผู้ใช้ที่เปิดใช้งานได้ (username → password) — เพิ่มผู้ใช้ใหม่ได้ที่นี่
_LOGIN_CREDENTIALS = {
    "PTUCE66": "6601430154032",
    "NPK90s": "1515021259",
}
# เดสก์ท็อป (Windows) = ถาม login ครั้งเดียวแล้วจำถาวร
# บนคลาวด์/มือถือ (Streamlit Cloud, Linux) = ข้ามหน้า login เปิดใช้ได้ทันที
# (เวอร์ชันคลาวด์ใช้ส่วนตัวไว้ตรวจงานนอกโต๊ะ ไม่ได้แจกใคร จึงไม่ต้องกรอกรหัส)
_IS_DESKTOP = sys.platform.startswith("win")


def _login_gate() -> bool:
    """หน้าจอ "เข้าสู่ระบบ" ครั้งแรก (activation) — ต้องกรอก username/password ให้ถูกต้อง
    ครั้งเดียวหลังติดตั้งและเปิดใช้งานครั้งแรก จากนั้นบันทึกสถานะลงไฟล์ถาวรผ่าน common.settings
    (%APPDATA%\\NPK_RC_SDM\\settings.json ซึ่งอยู่นอกโฟลเดอร์ติดตั้ง จึงรอดแม้ปิด-เปิด/ติดตั้งทับ
    เวอร์ชันใหม่) แล้วจะไม่ถามอีก

    คืน True ถ้าเปิดใช้งานแล้ว (ผ่าน), False ถ้ายัง — ผู้เรียกต้อง st.stop() เมื่อได้ False
    """
    # บนคลาวด์/มือถือ (ไม่ใช่ Windows) — ข้ามหน้า login เปิดใช้ได้ทันที
    # (เวอร์ชันคลาวด์ใช้ส่วนตัวไว้ตรวจงานนอกโต๊ะ ไม่แจกใคร จึงไม่ต้องกรอกรหัส)
    if not _IS_DESKTOP:
        return True

    from common.settings import load_settings, save_settings

    if st.session_state.get("_activated"):
        return True
    try:
        if load_settings().get("activation", {}).get("activated"):
            st.session_state["_activated"] = True
            return True
    except Exception:
        pass

    # ยังไม่เปิดใช้งาน — แสดงหน้าเข้าสู่ระบบ (ซ่อนแถบเมนูด้านข้าง เหมือนหน้ายินยอม)
    st.markdown("""
    <style>
    [data-testid="stSidebar"], [data-testid="stSidebarNav"],
    [data-testid="stSidebarCollapseButton"], [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    [data-testid="stAppViewContainer"] > section[data-testid="stSidebar"] { display: none !important; }
    .block-container { max-width: 480px; padding-top: 3.5rem; }
    [data-testid="stFormSubmitButton"] button {
        background-color: #2563EB !important; border-color: #2563EB !important;
        color: #FFFFFF !important; font-weight: 700 !important;
    }
    [data-testid="stFormSubmitButton"] button:hover { background-color: #1D4ED8 !important; }
    </style>
    """, unsafe_allow_html=True)

    b64 = _img_base64(_LOGO_PATH)
    if b64:
        st.markdown(
            f'<div style="text-align:center; margin: 0 0 10px 0;">'
            f'<img src="data:image/png;base64,{b64}" style="max-width:150px;" /></div>',
            unsafe_allow_html=True,
        )
    st.markdown(
        '<div style="text-align:center; margin-bottom:16px;">'
        '<h2 style="color:#1E3853; margin:0 0 4px 0;">เข้าสู่ระบบ</h2>'
        '<p style="color:#64748B; font-size:0.9rem; margin:0;">กรอกชื่อผู้ใช้และรหัสผ่านเพื่อเปิดใช้งานโปรแกรม '
        '(กรอกครั้งเดียวหลังติดตั้ง)</p></div>',
        unsafe_allow_html=True,
    )

    with st.form("npk_login_form", clear_on_submit=False):
        username = st.text_input("ชื่อผู้ใช้ (Username)")
        password = st.text_input("รหัสผ่าน (Password)", type="password")
        submitted = st.form_submit_button("เข้าสู่ระบบ", use_container_width=True)

    if submitted:
        _u = username.strip()
        if _u in _LOGIN_CREDENTIALS and password.strip() == _LOGIN_CREDENTIALS[_u]:
            save_settings("activation", {"activated": True, "username": _u})
            st.session_state["_activated"] = True
            st.rerun()
        else:
            st.error("ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง กรุณาลองใหม่")

    return False


def _consent_gate() -> bool:
    """หน้าจอ 'ข้อจำกัดความรับผิดชอบ' ที่ต้องกดยินยอมก่อนเข้าโปรแกรมทุกครั้งที่เปิดใหม่
    (แสดงก่อนเรียก st.navigation()/pg.run() เลย จึงไม่มีแถบเมนูด้านข้างให้เห็นระหว่างนี้)

    คืนค่า True ถ้ายินยอมแล้ว (ให้สคริปต์หลักทำงานต่อตามปกติ), False ถ้ายังไม่ยินยอม —
    ผู้เรียกต้อง st.stop() ทันทีเมื่อได้ False กลับมา เพื่อไม่ให้ทำงานส่วนอื่นต่อ

    ปุ่ม "ไม่ยินยอม": พยายามปิดหน้าต่างโปรแกรมให้อัตโนมัติ 2 ทาง — (1) ถ้ารันผ่าน
    pywebview (โปรแกรมเวอร์ชันติดตั้ง/native window) desktop_app.py ผูก js_api ชื่อ
    close_app() ไว้ให้เรียกปิดหน้าต่างจริงได้ (2) ถ้ารันผ่านเบราว์เซอร์ปกติ fallback ไปใช้
    window.close() ซึ่งเบราว์เซอร์ส่วนใหญ่จะบล็อกไม่ให้สคริปต์ปิดแท็บที่ผู้ใช้เปิดเอง (ข้อจำกัด
    ของเบราว์เซอร์เอง ไม่ใช่บั๊ก) — กรณีนี้จะมีข้อความให้ปิดหน้าต่างเองแทน
    """
    if st.session_state.get("consent_given"):
        return True

    st.markdown("""
    <style>
    /* หน้าจอเริ่มต้น (ข้อจำกัดความรับผิดชอบ): ซ่อนแถบเมนูด้านข้างทั้งหมด เหลือแค่รูป+ปุ่ม
       (เพราะหน้านี้หยุดก่อน st.navigation ทำงาน Streamlit จึงโชว์เมนู pages/ อัตโนมัติ) */
    [data-testid="stSidebar"],
    [data-testid="stSidebarNav"],
    [data-testid="stSidebarCollapseButton"],
    [data-testid="collapsedControl"],
    [data-testid="stSidebarCollapsedControl"] { display: none !important; }
    [data-testid="stAppViewContainer"] > section[data-testid="stSidebar"] { display: none !important; }

    .block-container { max-width: 900px; padding-top: 2.5rem; }
    [class*="st-key-consent-agree"] button {
        background-color: #2563EB !important; border-color: #2563EB !important;
        color: #FFFFFF !important; font-weight: 700 !important;
    }
    [class*="st-key-consent-agree"] button:hover { background-color: #1D4ED8 !important; }
    [class*="st-key-consent-decline"] button {
        background-color: #DC2626 !important; border-color: #DC2626 !important;
        color: #FFFFFF !important; font-weight: 700 !important;
    }
    [class*="st-key-consent-decline"] button:hover { background-color: #B91C1C !important; }
    </style>
    """, unsafe_allow_html=True)

    if st.session_state.get("consent_declined"):
        st.markdown(
            '<div style="text-align:center; padding: 90px 20px;">'
            '<h2 style="color:#1E3853;">โปรแกรมถูกปิดแล้ว</h2>'
            '<p style="color:#1E3853; font-size:1rem;">คุณเลือก "ไม่ยินยอม" ข้อจำกัดความรับผิดชอบ '
            'ระบบจะปิดหน้าต่างโปรแกรมให้อัตโนมัติ<br>หากหน้าต่างไม่ปิดเอง กรุณาปิดหน้าต่างนี้ด้วยตนเอง</p>'
            '</div>',
            unsafe_allow_html=True,
        )
        components.html(
            """
            <script>
            try {
                if (window.parent && window.parent.pywebview && window.parent.pywebview.api
                    && window.parent.pywebview.api.close_app) {
                    window.parent.pywebview.api.close_app();
                } else if (window.parent) {
                    window.parent.close();
                }
            } catch (e) {}
            </script>
            """,
            height=0,
        )
        st.stop()

    b64 = _img_base64(_DISCLAIMER_PATH)
    if b64:
        st.markdown(
            f'<div style="text-align:center; margin: 4px 0 30px 0;">'
            f'<img src="data:image/png;base64,{b64}" style="max-width:100%; border-radius:12px;" />'
            f'</div>',
            unsafe_allow_html=True,
        )

    _, bc1, bc2, _ = st.columns([2, 1, 1, 2])
    with bc1:
        if st.button("ยินยอม", key="consent-agree", use_container_width=True):
            st.session_state["consent_given"] = True
            st.rerun()
    with bc2:
        if st.button("ไม่ยินยอม", key="consent-decline", use_container_width=True):
            st.session_state["consent_declined"] = True
            st.rerun()

    return False


def _inject_home_css() -> None:
    st.markdown("""
    <style>
    .block-container { padding-top: 1.2rem; padding-bottom: 2rem; max-width: 100% !important; }
    header[data-testid="stHeader"] { display: none !important; }
    [data-testid="collapsedControl"] { display: none !important; }
    /* หน้าแรกไม่เรียก st.sidebar เลย แต่ถ้าผู้ใช้เพิ่งสลับมาจากหน้าอื่นที่มี sidebar
       Streamlit จะยังเก็บ DOM ของ sidebar (ว่างเปล่า) ไว้กินพื้นที่ 300px ทางซ้าย —
       ซ่อนทิ้งทั้งหมดเฉพาะหน้านี้ กันเลย์เอาต์เพี้ยน */
    [data-testid="stSidebar"], [data-testid="stSidebarCollapseButton"] { display: none !important; }

    /* ===== Topbar (แถบหัวข้อเต็มความกว้าง) ===== พื้นหลังสีเข้ม (navy) ตามคำขอผู้ใช้ 2026-07-13
       — เดิมพื้นขาว/ตัวหนังสือกรม สลับเป็นพื้นกรมเข้ม/ตัวหนังสือขาวแทน ให้เด่นเป็นแถบหัวโปรแกรม */
    [class*="st-key-npk-topbar"] {
        background: #1E3853 !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 10px 20px !important;
        box-shadow: 0 2px 10px rgba(20,30,40,0.18);
        margin-bottom: 22px;
    }
    .npk-topbar-logo { display: flex; align-items: center; gap: 10px; height: 100%; }
    .npk-topbar-logo img { height: 50px; width: auto; border-radius: 6px; }
    .npk-topbar-title { display: flex; flex-direction: column; line-height: 1.05; }
    .npk-topbar-title .t1 { font-size: 1.6rem; font-weight: 800; color: #FFFFFF; letter-spacing: .5px; }
    .npk-topbar-title .t2 { font-size: 0.8rem; font-weight: 700; color: #9FC1E8; letter-spacing: 2px; }

    [class*="st-key-topbar_open_pop"] button {
        background-color: #2563EB !important; border-color: #2563EB !important;
        color: #FFFFFF !important; font-weight: 700 !important;
        font-size: 1.05rem !important; min-height: 44px !important; padding: 6px 18px !important;
    }
    [class*="st-key-topbar_save_btn"] button {
        background-color: #15803D !important; border-color: #15803D !important;
        color: #FFFFFF !important; font-weight: 700 !important;
        font-size: 1.05rem !important; min-height: 44px !important; padding: 6px 18px !important;
    }

    .npk-topbar-badge {
        display: flex; align-items: center; gap: 8px;
        border: 1px solid rgba(255,255,255,0.22); border-radius: 10px;
        padding: 5px 12px; background: rgba(255,255,255,0.08); height: 100%;
    }
    .npk-topbar-badge .icon { font-size: 1.35rem; }
    .npk-topbar-badge .txt { line-height: 1.25; overflow: hidden; }
    .npk-topbar-badge .lbl { font-size: 0.82rem; color: #9FC1E8; font-weight: 600; }
    .npk-topbar-badge .val {
        font-size: 1.05rem; color: #FFFFFF; font-weight: 700;
        white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px;
    }
    .npk-topbar-version {
        text-align: center; font-size: 0.98rem; color: #FFFFFF; font-weight: 700;
        padding-top: 8px;
    }
    [class*="st-key-npk_menu_pop"] button {
        border-radius: 8px !important;
    }

    .npk-welcome h1 { color: #1E3853; margin: 4px 0 2px 0; font-size: 2.4rem; font-weight: 800; }
    .npk-welcome p { color: #1E3853; margin: 0 0 18px 0; font-size: 1.22rem; }

    /* ===== การ์ดหมวดหมู่กลาง ===== */
    [class*="st-key-card-"] {
        border-radius: 12px !important;
        border: 1px solid #E2E6EA !important;
        border-top: 4px solid #1E3853 !important;
        background: #F9F9F9 !important;
        box-shadow: 0 2px 8px rgba(20,30,40,0.05);
        padding: 2px 4px 8px 4px !important;
    }
    [class*="st-key-card-slab"]    { border-top-color: #D99A2B !important; }
    [class*="st-key-card-stair"]   { border-top-color: #F2762B !important; }
    [class*="st-key-card-beam"]    { border-top-color: #D63A2A !important; }
    [class*="st-key-card-column"]  { border-top-color: #1F5C99 !important; }
    [class*="st-key-card-footing"] { border-top-color: #4C8A3F !important; }

    .npk-card-header { display: flex; align-items: center; gap: 10px; padding: 8px 8px 0 8px; }
    .npk-card-num {
        display: inline-flex; align-items: center; justify-content: center;
        width: 30px; height: 30px; border-radius: 8px; flex-shrink: 0;
        color: #FFFFFF; font-weight: 700; font-size: 1.05rem;
    }
    .npk-card-header h3 { color: #1E3853; margin: 0; font-size: 1.3rem; font-weight: 700; }
    .npk-card-desc { color: #334155; font-size: 0.98rem; padding: 2px 8px 4px 8px; margin: 0; }

    .npk-card-illust { width: 100%; padding: 4px 10px 8px 10px; text-align: center; }
    .npk-card-illust img { max-width: 72%; height: auto; }

    [class*="st-key-card-"] [data-testid="stPageLink"] {
        border-radius: 8px !important;
        border: 1px solid #E2E6EA !important;
        background: #FFFFFF !important;
        margin: 4px 0 !important;
        padding: 7px 10px !important;
        box-shadow: 0 1px 3px rgba(20,30,40,0.06);
        transition: background 0.15s ease, border-color 0.15s ease;
    }
    [class*="st-key-card-"] [data-testid="stPageLink"]:hover {
        background: #1E3853 !important; border-color: #1E3853 !important;
    }
    [class*="st-key-card-"] [data-testid="stPageLink"] p {
        color: #1E3853 !important; font-weight: 600; font-size: 1.02rem;
        white-space: normal !important; line-height: 1.3;
    }
    [class*="st-key-card-"] [data-testid="stPageLink"]:hover p,
    [class*="st-key-card-"] [data-testid="stPageLink"]:hover span {
        color: #FFFFFF !important;
    }

    /* ===== แถบต้นไม้เมนูซ้าย ===== */
    .npk-tree-title {
        font-size: 1.0rem; font-weight: 700; color: #1E3853;
        margin: 2px 0 10px 4px; letter-spacing: .02em; text-transform: uppercase;
    }
    [class*="st-key-npk-tree-wrap"] [data-testid="stExpander"] {
        border: none !important; box-shadow: none !important; background: transparent !important;
        margin-bottom: 6px !important;
    }
    [class*="st-key-npk-tree-wrap"] [data-testid="stExpander"] summary {
        font-weight: 700 !important; color: #1E3853 !important; font-size: 1.12rem !important;
        padding: 4px 2px !important;
    }
    /* หมวดงาน 1-5: ใส่พื้นหลังสีต่อหมวด (สีเดียวกับที่ใช้บนการ์ดหน้าแรก/CATEGORY_COLORS)
       ที่แถบหัวข้อ (summary) ของ expander ให้ตัวหนังสือ/ลูกศรเป็นสีขาวอ่านชัดบนพื้นสี — 2026-07-13 */
    [class*="st-key-npk-tree-cat-"] [data-testid="stExpander"] summary {
        border-radius: 8px !important; padding: 8px 10px !important; color: #FFFFFF !important;
    }
    [class*="st-key-npk-tree-cat-"] [data-testid="stExpander"] summary svg { fill: #FFFFFF !important; }
    [class*="st-key-npk-tree-cat-slab"]    [data-testid="stExpander"] summary { background: #D99A2B !important; }
    [class*="st-key-npk-tree-cat-stair"]   [data-testid="stExpander"] summary { background: #F2762B !important; }
    [class*="st-key-npk-tree-cat-beam"]    [data-testid="stExpander"] summary { background: #D63A2A !important; }
    [class*="st-key-npk-tree-cat-column"]  [data-testid="stExpander"] summary { background: #1F5C99 !important; }
    [class*="st-key-npk-tree-cat-footing"] [data-testid="stExpander"] summary { background: #4C8A3F !important; }
    [class*="st-key-npk-tree-wrap"] [data-testid="stPageLink"] {
        padding: 4px 6px !important; margin: 1px 0 !important; border-radius: 6px !important;
    }
    [class*="st-key-npk-tree-wrap"] [data-testid="stPageLink"] p {
        font-size: 0.98rem !important; white-space: normal !important; line-height: 1.25;
    }
    [class*="st-key-npk-tree-quicknav"] {
        border-bottom: 1px solid #E2E6EA; margin-bottom: 10px; padding-bottom: 8px;
    }
    /* ปุ่ม "หน้าแรก/ข้อมูลโครงการ/พารามิเตอร์" — ใส่พื้นหลังสีกรมเข้ม (เดิมพื้นเทาอ่อนแทบไม่เห็น) */
    [class*="st-key-npk-tree-quicknav"] [data-testid="stPageLink"] {
        padding: 8px 10px !important; margin: 1px 0 !important; border-radius: 8px !important;
        background: #1E3853 !important;
    }
    [class*="st-key-npk-tree-quicknav"] [data-testid="stPageLink"]:hover { background: #16324A !important; }
    [class*="st-key-npk-tree-quicknav"] [data-testid="stPageLink"] p {
        font-size: 1.02rem !important; font-weight: 700 !important; color: #FFFFFF !important;
    }
    [class*="st-key-npk-tree-wrap"] button {
        background: transparent !important; border: none !important; box-shadow: none !important;
        color: #1E3853 !important; font-size: 0.98rem !important; text-align: left !important;
        justify-content: flex-start !important; padding: 2px 6px 2px 22px !important;
    }
    [class*="st-key-npk-tree-wrap"] button:hover { color: #1E3853 !important; text-decoration: underline; }
    .npk-done-tag {
        background: #E7F6EC; color: #15803D; font-size: 0.8rem; font-weight: 700;
        border-radius: 6px; padding: 3px 6px; text-align: center; margin-top: 3px;
    }

    /* ===== แผงสรุปขวา ===== */
    [class*="st-key-npk-summary-wrap"] {
        border-radius: 12px !important; border: 1px solid #E2E6EA !important;
        background: #FFFFFF !important; box-shadow: 0 2px 8px rgba(20,30,40,0.05);
        padding: 16px 16px 14px 16px !important;
    }
    .npk-summary-title { font-size: 1.22rem; font-weight: 700; color: #1E3853; margin-bottom: 10px; }
    .npk-summary-row {
        display: flex; align-items: center; gap: 10px; padding: 8px 2px;
        border-bottom: 1px solid #F0F2F4;
    }
    .npk-summary-icon { width: 30px; height: 30px; object-fit: contain; flex-shrink: 0; }
    .npk-summary-label { flex: 1; font-size: 1.06rem; font-weight: 600; color: #1E3853; }
    .npk-summary-count {
        font-size: 0.98rem; font-weight: 700; color: #1E3853;
        background: #F3F5F7; border-radius: 8px; padding: 3px 10px; white-space: nowrap;
    }
    .npk-summary-illust { text-align: center; padding: 16px 6px 6px 6px; }
    .npk-summary-illust img { max-width: 62%; filter: grayscale(1) opacity(0.5); }

    [class*="st-key-dl_all_gen"] button,
    [class*="st-key-dl_all_pdf"] button,
    [class*="st-key-dl_all_html"] button {
        background-color: #2563EB !important; border-color: #2563EB !important;
        color: #FFFFFF !important; font-weight: 700 !important;
    }
    [class*="st-key-summary_clear_btn"] button,
    [class*="st-key-summary_clear_confirm"] button {
        background-color: #DC2626 !important; border-color: #DC2626 !important;
        color: #FFFFFF !important; font-weight: 700 !important;
    }

    /* ===== RESPONSIVE: หน้าแรก/แถบเครื่องมือ ย่อตามความกว้างจอ (แบ่งครึ่งจอ/จอเล็กไม่ล้น) ===== */
    @media (max-width: 1366px) {
        .npk-topbar-title .t1 { font-size: 1.4rem; }
        .npk-topbar-title .t2 { font-size: 0.72rem; }
        .npk-topbar-logo img { height: 44px; }
        .npk-topbar-badge .icon { font-size: 1.2rem; }
        .npk-topbar-badge .lbl { font-size: 0.74rem; }
        .npk-topbar-badge .val { font-size: 0.95rem; max-width: 160px; }
        .npk-topbar-version { font-size: 0.88rem; }
        [class*="st-key-topbar_open_pop"] button,
        [class*="st-key-topbar_save_btn"] button { font-size: 0.95rem !important; min-height: 40px !important; }
        .npk-welcome h1 { font-size: 2.05rem; }
        .npk-welcome p { font-size: 1.08rem; }
        .npk-card-header h3 { font-size: 1.15rem; }
        .npk-card-desc { font-size: 0.9rem; }
        [class*="st-key-card-"] [data-testid="stPageLink"] p { font-size: 0.92rem; }
        [class*="st-key-npk-tree-wrap"] [data-testid="stExpander"] summary { font-size: 1.0rem !important; }
        [class*="st-key-npk-tree-wrap"] [data-testid="stPageLink"] p { font-size: 0.9rem !important; }
        [class*="st-key-npk-tree-quicknav"] [data-testid="stPageLink"] p { font-size: 0.92rem !important; }
        .npk-summary-title { font-size: 1.08rem; }
        .npk-summary-label { font-size: 0.95rem; }
        .npk-summary-count { font-size: 0.9rem; }
    }
    @media (max-width: 1024px) {
        .npk-topbar-title .t1 { font-size: 1.25rem; }
        .npk-topbar-title .t2 { font-size: 0.62rem; }
        .npk-topbar-logo img { height: 40px; }
        .npk-topbar-badge .icon { font-size: 1.05rem; }
        .npk-topbar-badge .lbl { font-size: 0.66rem; }
        .npk-topbar-badge .val { font-size: 0.86rem; max-width: 130px; }
        .npk-topbar-version { font-size: 0.8rem; }
        [class*="st-key-topbar_open_pop"] button,
        [class*="st-key-topbar_save_btn"] button { font-size: 0.86rem !important; min-height: 36px !important; }
        .npk-welcome h1 { font-size: 1.8rem; }
        .npk-welcome p { font-size: 0.98rem; }
        .npk-card-header h3 { font-size: 1.02rem; }
        .npk-card-desc { font-size: 0.82rem; }
        [class*="st-key-card-"] [data-testid="stPageLink"] p { font-size: 0.84rem; }
        [class*="st-key-npk-tree-wrap"] [data-testid="stExpander"] summary { font-size: 0.9rem !important; }
        [class*="st-key-npk-tree-wrap"] [data-testid="stPageLink"] p { font-size: 0.82rem !important; }
        [class*="st-key-npk-tree-quicknav"] [data-testid="stPageLink"] p { font-size: 0.84rem !important; }
        .npk-summary-title { font-size: 0.98rem; }
        .npk-summary-label { font-size: 0.86rem; }
        .npk-summary-count { font-size: 0.8rem; }
    }
    </style>
    """, unsafe_allow_html=True)


def _card_header(number: int, title: str, desc: str) -> None:
    color = list(CATEGORY_COLORS.values())[number - 1]
    st.markdown(
        f'<div class="npk-card-header">'
        f'<span class="npk-card-num" style="background:{color}">{number}</span>'
        f'<h3>{title}</h3></div>'
        f'<p class="npk-card-desc">{desc}</p>',
        unsafe_allow_html=True,
    )


def _card_illustration(icon_name: str) -> None:
    b64 = _img_base64(_ICON_DIR / f"{icon_name}.png")
    if b64:
        st.markdown(
            f'<div class="npk-card-illust"><img src="data:image/png;base64,{b64}" /></div>',
            unsafe_allow_html=True,
        )


def _bilingual_label(module_key: str) -> str:
    """ป้ายกำกับสองภาษา 'รหัส ชื่อไทย (English Name)' — ถ้าชื่อไทยมีวงเล็บกำกับอยู่แล้ว
    (เช่น '2.2 บันไดหักกลับ (U-Shape)', '5.2 ฐานรากเสาเข็ม (Pile Cap)') ไม่ต้องเติมซ้ำอีกชั้น
    กันป้ายกลายเป็น '... (U-Shape) (U Shape Stair)' ซ้อนวงเล็บสองชั้น"""
    th_label = MODULE_LABELS[module_key]
    if "(" in th_label:
        return th_label
    return f"{th_label} ({MODULE_LABELS_EN[module_key]})"


def _render_topbar(pages_by_key: dict) -> None:
    project_info = st.session_state.get("project_info") or {}
    project_name = project_info.get("project_name") or "อาคารคอนกรีตเสริมเหล็ก"
    engineer = project_info.get("engineer") or "นายเก่งมาก เชียวชาญ"

    with st.container(key="npk-topbar"):
        c_logo, c_open, c_save, c_gap, c_proj, c_eng, c_ver, c_menu = st.columns(
            [2.7, 0.85, 0.85, 1.1, 1.5, 1.5, 0.6, 0.45], vertical_alignment="center",
        )
        with c_logo:
            st.markdown(
                f'<div class="npk-topbar-logo">'
                f'<img src="data:image/png;base64,{_img_base64(_LOGO_PATH)}" />'
                f'<div class="npk-topbar-title"><span class="t1">NPK RC SDM</span>'
                f'<span class="t2">STRUCTURAL DESIGN</span></div></div>',
                unsafe_allow_html=True,
            )
        with c_open:
            with st.popover("เปิด", key="topbar_open_pop", use_container_width=True):
                st.caption("เลือกไฟล์โปรเจกต์ (.npkproj) ที่เคยบันทึกไว้")
                uploaded = st.file_uploader(
                    "ไฟล์โปรเจกต์", type=["npkproj", "json"], key="topbar_open_uploader",
                    label_visibility="collapsed",
                )
                if uploaded is not None and uploaded.file_id != st.session_state.get("_last_opened_file_id"):
                    st.session_state["_last_opened_file_id"] = uploaded.file_id
                    try:
                        bundle = json.loads(uploaded.getvalue().decode("utf-8"))
                    except Exception:
                        bundle = None
                    if isinstance(bundle, dict) and apply_project_bundle(bundle):
                        st.success("เปิดไฟล์โปรเจกต์สำเร็จ")
                        st.rerun()
                    else:
                        st.error("ไฟล์นี้ไม่ใช่ไฟล์โปรเจกต์ NPK RC SDM ที่ถูกต้อง")
        with c_save:
            with st.popover("บันทึก", key="topbar_save_pop", use_container_width=True):
                bundle = build_project_bundle()
                proj_name = (bundle.get("project_info") or {}).get("project_name") or "โปรเจกต์"
                st.caption("บันทึกไฟล์โปรเจกต์ (.npkproj) เก็บไว้เปิดใช้ภายหลัง")
                from common.pdf_export import native_save_button
                native_save_button(
                    "เลือกที่บันทึกไฟล์",
                    json.dumps(bundle, ensure_ascii=False, indent=2).encode("utf-8"),
                    f"{proj_name}.npkproj",
                    key="topbar_save",
                    mime="application/json",
                    color="#0D9488",
                )
        with c_proj:
            st.markdown(
                f'<div class="npk-topbar-badge">'
                f'<div class="txt"><div class="lbl">โครงการ</div>'
                f'<div class="val">{project_name}</div></div></div>',
                unsafe_allow_html=True,
            )
        with c_eng:
            st.markdown(
                f'<div class="npk-topbar-badge">'
                f'<div class="txt"><div class="lbl">วิศวกร</div>'
                f'<div class="val">{engineer}</div></div></div>',
                unsafe_allow_html=True,
            )
        with c_ver:
            st.markdown('<div class="npk-topbar-version">V.1.2.1</div>', unsafe_allow_html=True)
        with c_menu:
            with st.popover("☰", key="npk_menu_pop", use_container_width=True):
                st.markdown("**NPK RC SDM**")
                st.caption("ซอฟต์แวร์ออกแบบโครงสร้างคอนกรีตเสริมเหล็ก (SDM)\nตามกฎกระทรวง พ.ศ. 2566")
                st.write("เวอร์ชัน 1.2.1")
                st.write("© 2026 Nopphakhun Duangsri")
                st.divider()
                if st.button("↺ แสดงหน้าข้อจำกัดความรับผิดชอบอีกครั้ง",
                             key="menu_show_consent", use_container_width=True):
                    st.session_state["consent_given"] = False
                    st.rerun()


def _tree_column(pages_by_key: dict) -> None:
    with st.container(key="npk-tree-wrap"):
        with st.container(key="npk-tree-quicknav"):
            st.page_link(home_page, label="หน้าแรก", use_container_width=True)
            qn1, qn2 = st.columns(2)
            with qn1:
                st.page_link(project_info_page, label="ข้อมูลโครงการ", use_container_width=True)
            with qn2:
                st.page_link(design_params_page, label="พารามิเตอร์", use_container_width=True)
        st.markdown('<div class="npk-tree-title">งานที่คำนวณเสร็จ</div>', unsafe_allow_html=True)
        for num, name, icon_key, emoji, _desc, module_keys in CATEGORY_DEFS:
            # ห่อด้วย container(key=...) แบบเดียวกับการ์ดหน้าแรก (st-key-card-{icon_key}) เพื่อให้
            # CSS ใส่พื้นหลังสีต่อหมวดที่แถบหัวข้อ (summary) ของ expander ได้ (ดู _inject_home_css)
            with st.container(key=f"npk-tree-cat-{icon_key}"):
                with st.expander(f"{num}. {name}", expanded=True):
                    for mk in module_keys:
                        st.page_link(pages_by_key[mk], label=_bilingual_label(mk))
                        items = get_items(mk)
                        for code in sorted(items.keys()):
                            ic1, ic2 = st.columns([1.5, 1.3])
                            with ic1:
                                if st.button(f"↳ {code}", key=f"tree_btn_{mk}_{code}", use_container_width=True):
                                    request_load(mk, code)
                                    st.switch_page(pages_by_key[mk])
                            with ic2:
                                st.markdown('<div class="npk-done-tag">เสร็จแล้ว</div>', unsafe_allow_html=True)


def _summary_panel() -> None:
    with st.container(key="npk-summary-wrap"):
        st.markdown('<div class="npk-summary-title">สรุปการออกแบบล่าสุด</div>', unsafe_allow_html=True)
        for num, name, icon_key, emoji, _desc, module_keys in CATEGORY_DEFS:
            count = sum(len(get_items(mk)) for mk in module_keys)
            b64 = _img_base64(_ICON_DIR / f"{icon_key}.png")
            st.markdown(
                f'<div class="npk-summary-row">'
                f'<img src="data:image/png;base64,{b64}" class="npk-summary-icon" />'
                f'<div class="npk-summary-label">{name}</div>'
                f'<div class="npk-summary-count">{count} รายการ</div></div>',
                unsafe_allow_html=True,
            )

        st.markdown(
            f'<div class="npk-summary-illust">'
            f'<img src="data:image/png;base64,{_img_base64(_LOGO_PATH)}" /></div>',
            unsafe_allow_html=True,
        )

        from common.combined_report import render_combined_download_button
        render_combined_download_button()

        st.write("")
        confirm_key = "_confirm_clear_items"
        if total_item_count() > 0:
            if not st.session_state.get(confirm_key):
                if st.button("ล้างข้อมูล", key="summary_clear_btn", use_container_width=True):
                    st.session_state[confirm_key] = True
                    st.rerun()
            else:
                st.warning("ยืนยันล้างรายการคำนวณที่บันทึกไว้ทั้งหมด?\n(ไม่กระทบข้อมูลโครงการ/พารามิเตอร์)")
                cc1, cc2 = st.columns(2)
                with cc1:
                    if st.button("ยืนยัน", key="summary_clear_confirm", use_container_width=True):
                        clear_all_items()
                        st.session_state[confirm_key] = False
                        st.rerun()
                with cc2:
                    if st.button("ยกเลิก", key="summary_clear_cancel", use_container_width=True):
                        st.session_state[confirm_key] = False
                        st.rerun()
        else:
            st.button("ล้างข้อมูล", key="summary_clear_btn_disabled",
                      use_container_width=True, disabled=True)


def _page_shell(pages_by_key: dict):
    """เรียกใช้กับ**ทุกหน้า**ของโปรแกรม (ทั้งหน้าแรกและหน้าโมดูล/ข้อมูลโครงการ/พารามิเตอร์)
    — วาด topbar เต็มความกว้าง + แถบต้นไม้นำทางซ้ายที่ใช้ร่วมกันทุกหน้า แล้วคืนค่า
    "คอลัมน์เนื้อหา" (content column) ให้ผู้เรียกใช้ st.columns/st.container วาดเนื้อหา
    เฉพาะของหน้านั้นต่อไป (แทนที่ st.sidebar เดิมที่ใช้แค่บางหน้า — ตามคำสั่งผู้ใช้
    "ทำให้เป็นแบบเดียวกันทุกเมนู" 2026-07-11)

    CSS ที่แทรก (_inject_home_css) เป็น page-scoped อยู่แล้ว
    (st.navigation รันสคริปต์แต่ละหน้าแยกกัน) จึงเรียกซ้ำได้ทุกหน้าอย่างปลอดภัย —
    selector ที่ไม่มี element ตรงบนหน้านั้น (เช่น .npk-welcome บนหน้าโมดูล) จะไม่มีผลใดๆ"""
    _inject_home_css()
    from common.ui_style import render_back_to_top
    render_back_to_top()  # ปุ่มลอย "กลับสู่ด้านบน" มุมขวาล่าง (หน้าแรก/หน้าที่ใช้ shell นี้)
    _render_topbar(pages_by_key)
    tree_col, content_col = st.columns([1.0, 4.3], gap="medium")
    with tree_col:
        _tree_column(pages_by_key)
    return content_col


def home():
    content_col = _page_shell(_module_pages_by_key)

    with content_col:
        col_center, col_right = st.columns([3.3, 1.05], gap="medium")

        with col_center:
            st.markdown(
                '<div class="npk-welcome"><h1>ยินดีต้อนรับสู่ NPK RC SDM</h1>'
                '<p>ซอฟต์แวร์ออกแบบโครงสร้างคอนกรีตเสริมเหล็ก</p></div>',
                unsafe_allow_html=True,
            )

            st.write("")

            cat_cols = st.columns(5)
            for (num, name, icon_key, _emoji, desc, module_keys), col in zip(CATEGORY_DEFS, cat_cols):
                with col:
                    with st.container(border=True, key=f"card-{icon_key}"):
                        _card_header(num, name, desc)
                        _card_illustration(icon_key)
                        for mk in module_keys:
                            st.page_link(_module_pages_by_key[mk], label=_bilingual_label(mk))

        with col_right:
            _summary_panel()


# เข้าสู่ระบบครั้งแรก (activation) — ต้องผ่านก่อนหน้ายินยอม (กรอกครั้งเดียวหลังติดตั้ง)
if not _login_gate():
    st.stop()

if not _consent_gate():
    st.stop()

# ตั้งค่า session_state ของ "ข้อมูลโครงการ"/"พารามิเตอร์การออกแบบ" ให้พร้อมใช้งาน
# ตั้งแต่เริ่มโปรแกรมเสมอ (ใช้ค่าที่บันทึกไว้ล่าสุด หรือค่ามาตรฐานถ้ายังไม่เคยบันทึก)
# — ไม่ต้องคลิกเข้าเมนูนั้นก่อนหัวกระดาษรายการคำนวณถึงจะแสดงถูกต้อง (ตามคำขอผู้ใช้)
ensure_initialized()

home_page = st.Page(home, title="หน้าแรก", default=True)
project_info_page = st.Page("app_pages/project_info.py", title="ข้อมูลโครงการ")
design_params_page = st.Page("app_pages/design_parameters.py", title="พารามิเตอร์การออกแบบ")
slab_on_ground_page = st.Page("app_pages/slab_on_ground.py", title="1.1 พื้นวางบนดิน")
one_way_slab_page = st.Page("app_pages/one_way_slab.py", title="1.2 พื้นทางเดียว")
two_way_slab_page = st.Page("app_pages/two_way_slab.py", title="1.3 พื้นสองทาง")
cantilever_slab_page = st.Page("app_pages/cantilever_slab.py", title="1.4 พื้นยื่น")
stair_straight_page = st.Page("app_pages/stair_straight.py", title="2.1 บันไดช่วงตรง")
stair_u_shape_page = st.Page("app_pages/stair_u_shape.py", title="2.2 บันไดหักกลับ (U-Shape)")
beam_single_span_page = st.Page("app_pages/beam_single_span.py", title="3.1 คานช่วงเดียว")
continuous_beam_page = st.Page("app_pages/continuous_beam.py", title="3.2 คานต่อเนื่อง")
cantilever_beam_page = st.Page("app_pages/cantilever_beam.py", title="3.3 คานยื่น")
column_tied_page = st.Page("app_pages/column_tied.py", title="4.1 เสาสี่เหลี่ยม")
column_spiral_page = st.Page("app_pages/column_spiral.py", title="4.2 เสากลม")
footing_spread_page = st.Page("app_pages/footing_spread.py", title="5.1 ฐานรากแผ่")
footing_pile_cap_page = st.Page("app_pages/footing_pile_cap.py", title="5.2 ฐานรากเสาเข็ม (Pile Cap)")

pg = st.navigation(
    [home_page, project_info_page, design_params_page, slab_on_ground_page,
     one_way_slab_page, two_way_slab_page, cantilever_slab_page, stair_straight_page,
     stair_u_shape_page,
     beam_single_span_page, continuous_beam_page, cantilever_beam_page,
     column_tied_page, column_spiral_page, footing_spread_page, footing_pile_cap_page],
    position="hidden",
)

_pages_by_key_all = {
    "home": home_page,
    "project_info": project_info_page,
    "design_params": design_params_page,
    "slab_on_ground": slab_on_ground_page,
    "one_way_slab": one_way_slab_page,
    "two_way_slab": two_way_slab_page,
    "cantilever_slab": cantilever_slab_page,
    "stair_straight": stair_straight_page,
    "stair_u_shape": stair_u_shape_page,
    "beam_single_span": beam_single_span_page,
    "continuous_beam": continuous_beam_page,
    "cantilever_beam": cantilever_beam_page,
    "column_tied": column_tied_page,
    "column_spiral": column_spiral_page,
    "footing_spread": footing_spread_page,
    "footing_pile_cap": footing_pile_cap_page,
}

# แถบต้นไม้นำทางซ้ายต้องการแค่ 13 โมดูลคำนวณ (ไม่รวมหน้าแรก/ข้อมูลโครงการ/พารามิเตอร์)
# ใช้ตัวแปรเดียวกันนี้ทั้งใน home() และ dispatch ด้านล่าง กันข้อมูลหลุด sync กัน
_module_pages_by_key = {
    "slab_on_ground": slab_on_ground_page, "one_way_slab": one_way_slab_page,
    "two_way_slab": two_way_slab_page, "cantilever_slab": cantilever_slab_page,
    "stair_straight": stair_straight_page, "stair_u_shape": stair_u_shape_page,
    "beam_single_span": beam_single_span_page, "continuous_beam": continuous_beam_page,
    "cantilever_beam": cantilever_beam_page, "column_tied": column_tied_page,
    "column_spiral": column_spiral_page, "footing_spread": footing_spread_page,
    "footing_pile_cap": footing_pile_cap_page,
}

# === 2026-07-11: ขยาย topbar + แถบต้นไม้นำทางซ้าย ให้ใช้กับ "ทุกหน้า" ของโปรแกรม ===
# (เดิมมีแค่หน้าแรก ผู้ใช้ส่งภาพตัวอย่างหน้าโมดูลจริง สั่ง "ทำให้เป็นแบบเดียวกันทุกเมนู"
# — ยืนยันขอบเขตผ่าน AskUserQuestion: ทำทั้ง chrome (topbar+tree) และเนื้อหา (การ์ด
# กรอบสี/การ์ดผลลัพธ์) ครบทุก 15 หน้า ทำทีเดียวทั้งหมด) — เลิกใช้ st.sidebar เดิม
# (_render_sidebar ถูกลบออกจากไฟล์นี้แล้ว) ทุกหน้าที่ไม่ใช่หน้าแรกจะถูกห่อด้วย
# _page_shell() (topbar+tree เดียวกับหน้าแรก) แล้ว pg.run() ของหน้านั้นวาดเนื้อหาลงใน
# content column ที่ได้กลับมา — เทียบ identity กับ home_page object ที่ผูกไว้ก่อน
# (เผื่อ identity ไม่ตรงในบาง edge case จึง fallback เทียบ title ด้วย)
_is_home = (pg is home_page) or (getattr(pg, "title", None) == "หน้าแรก")
if _is_home:
    pg.run()
else:
    _content_col = _page_shell(_module_pages_by_key)
    with _content_col:
        pg.run()
