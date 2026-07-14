"""
common/app_state.py — ตั้งค่า session_state เริ่มต้นของ "ข้อมูลโครงการ" และ
"พารามิเตอร์การออกแบบ" ให้พร้อมใช้งานตั้งแต่โปรแกรมเริ่มทำงาน (เรียกจาก app.py
ก่อน st.navigation()/pg.run() เสมอ ไม่ว่าผู้ใช้จะเปิดหน้าไหนเป็นหน้าแรกก็ตาม)

เหตุผล: เดิม session_state["project_info"]/["design_params"] จะถูกตั้งค่าก็ต่อเมื่อ
สคริปต์ของหน้า "ข้อมูลโครงการ"/"พารามิเตอร์การออกแบบ" ถูกรันเท่านั้น (คือต้องคลิก
เข้าไปที่เมนูนั้นก่อน) ทำให้ถ้าผู้ใช้เปิดโมดูลคำนวณอื่น (เช่น 1.2, 3.1 ฯลฯ) เป็น
หน้าแรกโดยไม่เคยผ่านหน้า "ข้อมูลโครงการ"/"พารามิเตอร์" เลย หัวกระดาษของรายการ
คำนวณจะว่าง/ใช้ค่ามาตรฐานที่ไม่ตรงกับที่ผู้ใช้เคยตั้งไว้ — ย้ายมาตั้งค่าที่นี่แทน
เพื่อให้พร้อมใช้งานตั้งแต่แรกเสมอ โดยดึงค่าที่บันทึกไว้ล่าสุด (common.settings) มา
ใช้ก่อน ถ้ายังไม่เคยบันทึกเลยจึงใช้ค่ามาตรฐาน (defaults ด้านล่าง)
"""

from pathlib import Path

import streamlit as st

from common.design_params import STEEL_FY_KSC, calculate as calc_params
from common.settings import load_settings

PROJECT_INFO_DEFAULTS = {
    "owner": "NPK RC SDM",
    "project_name": "อาคารคอนกรีตเสริมเหล็ก",
    "location": "ต.ฟ้าฮ่าม อ.เมือง จ.เชียงใหม่",
    "engineer": "นายเก่งมาก เชียวชาญ",
}

DESIGN_PARAMS_DEFAULTS = {"fc": 240.0, "steel_type_sr": "SR24", "steel_type_sd": "SD40"}

_LOGO_PATH = Path(__file__).resolve().parent.parent / "data" / "logo.png"


def load_default_logo():
    """คืนค่า (bytes, mime) ของโลโก้เริ่มต้นจาก data/logo.png ถ้ามีไฟล์อยู่จริง
    ไม่งั้นคืน (None, None) (กันแอปพังถ้าไฟล์หาย)"""
    if _LOGO_PATH.exists():
        return _LOGO_PATH.read_bytes(), "image/png"
    return None, None


def _valid_steel_type(value, fallback: str) -> str:
    return value if value in STEEL_FY_KSC else fallback


def ensure_initialized() -> None:
    """เรียกครั้งเดียวจาก app.py ทุกครั้งที่โปรแกรมเริ่มทำงาน (ก่อนเลือกหน้าใดๆ) —
    ถ้า session_state มีค่าอยู่แล้ว (เช่น rerun ระหว่างใช้งานปกติ) จะไม่ทำอะไรซ้ำ"""
    saved = load_settings()

    if "project_info" not in st.session_state:
        pinfo = dict(PROJECT_INFO_DEFAULTS)
        saved_pinfo = saved.get("project_info")
        if isinstance(saved_pinfo, dict):
            pinfo.update({k: v for k, v in saved_pinfo.items() if k in PROJECT_INFO_DEFAULTS})
        st.session_state["project_info"] = pinfo

    if "project_logo_bytes" not in st.session_state:
        logo_bytes, logo_mime = load_default_logo()
        st.session_state["project_logo_bytes"] = logo_bytes
        st.session_state["project_logo_mime"] = logo_mime

    if "project_cover_image_bytes" not in st.session_state:
        st.session_state["project_cover_image_bytes"] = None
        st.session_state["project_cover_image_mime"] = None

    if "pi_form_gen" not in st.session_state:
        st.session_state["pi_form_gen"] = 0

    if "design_params" not in st.session_state:
        dp = dict(DESIGN_PARAMS_DEFAULTS)
        saved_dp = saved.get("design_params")
        if isinstance(saved_dp, dict):
            try:
                dp["fc"] = float(saved_dp.get("fc", dp["fc"]))
            except (TypeError, ValueError):
                pass
            dp["steel_type_sr"] = _valid_steel_type(saved_dp.get("steel_type_sr"), dp["steel_type_sr"])
            dp["steel_type_sd"] = _valid_steel_type(saved_dp.get("steel_type_sd"), dp["steel_type_sd"])

        params_sr = calc_params(dp["fc"], dp["steel_type_sr"])
        params_sd = calc_params(dp["fc"], dp["steel_type_sd"])
        st.session_state["design_params"] = params_sd
        st.session_state["design_params_sr"] = params_sr
        st.session_state["design_params_sd"] = params_sd
        st.session_state["design_params_fc"] = dp["fc"]
        st.session_state["design_params_steel_sr"] = dp["steel_type_sr"]
        st.session_state["design_params_steel_sd"] = dp["steel_type_sd"]
