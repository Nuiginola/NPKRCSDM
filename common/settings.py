"""
common/settings.py — บันทึก/โหลดค่าตั้งค่าที่ผู้ใช้กำหนดล่าสุด (ข้อมูลโครงการ,
พารามิเตอร์การออกแบบ) ลงไฟล์ในเครื่อง เพื่อให้โปรแกรมจำค่าไว้ข้ามการเปิด-ปิด
โปรแกรมแต่ละครั้ง — ไม่ใช้ st.session_state เพราะจะหายทุกครั้งที่เปิดโปรเซส
Streamlit ใหม่ (ทุกครั้งที่เปิดโปรแกรมผ่าน desktop_app.py คือโปรเซสใหม่เสมอ)

เก็บไฟล์ settings.json ไว้ที่โฟลเดอร์ข้อมูลผู้ใช้ (%APPDATA%\\NPK_RC_SDM บน Windows)
แยกออกจากโฟลเดอร์ติดตั้งโปรแกรม (`$INSTDIR\\code`) โดยเจตนา เพื่อไม่ให้ค่าที่
บันทึกไว้หายไปเวลาติดตั้ง/อัปเดตโปรแกรมเวอร์ชันใหม่ทับโฟลเดอร์เดิม
"""

import json
import os
from pathlib import Path


def _settings_dir() -> Path:
    base = os.environ.get("APPDATA")
    if base:
        return Path(base) / "NPK_RC_SDM"
    # ไม่ใช่ Windows (เช่นทดสอบในแซนด์บ็อกซ์ Linux) — ใช้โฟลเดอร์ home แทน
    return Path.home() / ".npk_rc_sdm"


SETTINGS_FILE = _settings_dir() / "settings.json"


def load_settings() -> dict:
    """โหลดค่าตั้งค่าทั้งหมดจากไฟล์ คืน dict ว่างถ้ายังไม่มีไฟล์/ไฟล์เสีย/อ่านไม่ได้
    (กันแอปพังเสมอ ไม่ raise exception ออกไปนอกฟังก์ชันนี้)"""
    try:
        if SETTINGS_FILE.exists():
            data = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                return data
    except Exception:
        pass
    return {}


def save_settings(section: str, data: dict) -> bool:
    """บันทึกค่าตั้งค่าเฉพาะ section (เช่น 'project_info', 'design_params') ลงไฟล์
    โดยไม่ทับ section อื่นที่มีอยู่แล้ว — คืนค่า True ถ้าบันทึกสำเร็จ, False ถ้าเขียน
    ไฟล์ไม่ได้ (เช่น ไม่มีสิทธิ์เขียน) แต่ไม่ raise exception ออกไป (ไม่ทำให้แอปพัง)"""
    try:
        current = load_settings()
        current[section] = data
        SETTINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_FILE.write_text(
            json.dumps(current, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        return True
    except Exception:
        return False
