"""
common/project_store.py — ชั้นข้อมูลกลางสำหรับ "โปรเจกต์" หนึ่งชุด: ข้อมูลโครงการ +
พารามิเตอร์การออกแบบ + รายการคำนวณที่บันทึกไว้ทุกโมดูล (คนละอย่างกับ common/settings.py
ซึ่งจำแค่ "ค่ามาตรฐานล่าสุด" อัตโนมัติ — ที่นี่คือระบบ "บันทึกหลายรายการ" ที่ผู้ใช้กด
บันทึกเองเป็นชุดๆ ตามรหัสพื้น/คาน เช่น S1, B2 แล้วรวมเป็นไฟล์โปรเจกต์เดียวได้)

โครงสร้าง session_state["saved_items"] = {module_key: {code: input_dict}}
โดย input_dict คือผลลัพธ์ของ dataclasses.asdict(...) ของ *Input dataclass ของโมดูลนั้น
(ครอบคลุมทั้งฟิลด์ scalar และ nested dataclass/list ของ dataclass เช่น point_loads
ของโมดูลคาน — asdict() แปลงให้เป็น dict/list ธรรมดาแบบ JSON-serializable ให้อัตโนมัติ)
"""

import dataclasses

import streamlit as st

MODULE_LABELS = {
    "slab_on_ground": "1.1 พื้นวางบนดิน",
    "one_way_slab": "1.2 พื้นทางเดียว",
    "two_way_slab": "1.3 พื้นสองทาง",
    "cantilever_slab": "1.4 พื้นยื่น",
    "stair_straight": "2.1 บันไดช่วงตรง",
    "stair_u_shape": "2.2 บันไดหักกลับ (U-Shape)",
    "beam_single_span": "3.1 คานช่วงเดียว",
    "continuous_beam": "3.2 คานต่อเนื่อง",
    "cantilever_beam": "3.3 คานยื่น",
    "column_tied": "4.1 เสาสี่เหลี่ยม",
    "column_spiral": "4.2 เสากลม",
    "footing_spread": "5.1 ฐานรากแผ่",
    "footing_pile_cap": "5.2 ฐานรากเสาเข็ม (Pile Cap)",
}

# ลำดับโมดูล -> path ไฟล์หน้า (ใช้ตอนสร้างลิงก์/สลับหน้าจาก sidebar และตอนรวม PDF)
MODULE_PAGES = {
    "slab_on_ground": "app_pages/slab_on_ground.py",
    "one_way_slab": "app_pages/one_way_slab.py",
    "two_way_slab": "app_pages/two_way_slab.py",
    "cantilever_slab": "app_pages/cantilever_slab.py",
    "stair_straight": "app_pages/stair_straight.py",
    "stair_u_shape": "app_pages/stair_u_shape.py",
    "beam_single_span": "app_pages/beam_single_span.py",
    "continuous_beam": "app_pages/continuous_beam.py",
    "cantilever_beam": "app_pages/cantilever_beam.py",
    "column_tied": "app_pages/column_tied.py",
    "column_spiral": "app_pages/column_spiral.py",
    "footing_spread": "app_pages/footing_spread.py",
    "footing_pile_cap": "app_pages/footing_pile_cap.py",
}


def _ensure_store() -> dict:
    store = st.session_state.get("saved_items")
    if not isinstance(store, dict):
        store = {}
    for k in MODULE_LABELS:
        if k not in store or not isinstance(store[k], dict):
            store[k] = {}
    st.session_state["saved_items"] = store
    return store


def get_items(module_key: str) -> dict:
    """คืนค่า dict {code: input_dict} ของโมดูลนั้น (ว่างถ้ายังไม่มีรายการบันทึกไว้)"""
    return _ensure_store().get(module_key, {})


def total_item_count() -> int:
    return sum(len(v) for v in _ensure_store().values())


def save_item(module_key: str, code: str, input_obj) -> str:
    """บันทึก/เขียนทับรายการคำนวณ 1 ชุด ภายใต้รหัส `code` — คืนค่ารหัสที่บันทึกจริง
    (ตัดช่องว่างหัวท้าย) หรือ "" ถ้ารหัสว่างเปล่า (ไม่บันทึก)"""
    code = (code or "").strip()
    if not code:
        return ""
    store = _ensure_store()
    store.setdefault(module_key, {})
    if dataclasses.is_dataclass(input_obj):
        data = dataclasses.asdict(input_obj)
    else:
        data = dict(input_obj)
    store[module_key][code] = data
    return code


def delete_item(module_key: str, code: str) -> None:
    _ensure_store().get(module_key, {}).pop(code, None)


def clear_all_items() -> None:
    """ล้างเฉพาะรายการคำนวณที่บันทึกไว้ทั้งหมดทุกโมดูล — ไม่แตะข้อมูลโครงการ/
    พารามิเตอร์การออกแบบ (ตามที่ผู้ใช้ระบุขอบเขตไว้)"""
    st.session_state["saved_items"] = {k: {} for k in MODULE_LABELS}


def request_load(module_key: str, code: str) -> None:
    """เรียกจาก sidebar ตอนคลิกรายการย่อย — ตั้ง flag ให้หน้าโมดูลนั้นโหลดค่ากลับ
    เข้าฟอร์มตอน rerun ถัดไป (ดู consume_pending_load)"""
    st.session_state["_pending_load"] = {"module": module_key, "code": code}


def consume_pending_load(module_key: str):
    """เรียกจากบนสุดของสคริปต์หน้าโมดูลนั้นๆ เอง — คืนค่า (input_dict, code) ถ้ามี
    pending load ตรงกับโมดูลนี้ (แล้วล้าง flag ทิ้งกันโหลดซ้ำทุก rerun) มิฉะนั้นคืน
    (None, None)"""
    pending = st.session_state.get("_pending_load")
    if not pending or pending.get("module") != module_key:
        return None, None
    code = pending.get("code")
    st.session_state["_pending_load"] = None
    return get_items(module_key).get(code), code


def build_project_bundle() -> dict:
    """รวมข้อมูลโครงการ + พารามิเตอร์การออกแบบ + รายการคำนวณที่บันทึกไว้ทั้งหมด เป็น
    dict เดียวที่ JSON-serialize ได้ตรงๆ สำหรับปุ่ม "บันทึก" (ดาวน์โหลดเป็นไฟล์โปรเจกต์)"""
    return {
        "npk_rc_sdm_project": True,
        "version": 1,
        "project_info": st.session_state.get("project_info") or {},
        "design_params": {
            "fc": st.session_state.get("design_params_fc"),
            "steel_type_sr": st.session_state.get("design_params_steel_sr"),
            "steel_type_sd": st.session_state.get("design_params_steel_sd"),
        },
        "saved_items": _ensure_store(),
    }


def apply_project_bundle(bundle: dict) -> bool:
    """โหลด dict ที่ได้จาก build_project_bundle() (หรือไฟล์ .npkproj ที่ผู้ใช้เปิด)
    กลับเข้า session_state ทั้งหมด (ข้อมูลโครงการ/พารามิเตอร์/รายการที่บันทึกไว้) และ
    เขียนค่าข้อมูลโครงการ/พารามิเตอร์ลง settings.json ด้วย (ให้เป็นค่าที่โปรแกรมจำไว้
    ใช้ต่อในครั้งถัดไปด้วย ไม่ใช่แค่ session ปัจจุบัน) — คืนค่า True ถ้าเป็นไฟล์โปรเจกต์
    ที่ถูกต้อง (มี key "npk_rc_sdm_project"), False ถ้าไฟล์ไม่ถูกรูปแบบ (ไม่ทำอะไรเลย)"""
    if not isinstance(bundle, dict) or not bundle.get("npk_rc_sdm_project"):
        return False

    from common.design_params import STEEL_FY_KSC, calculate as calc_params
    from common.settings import save_settings

    pinfo = bundle.get("project_info")
    if isinstance(pinfo, dict):
        st.session_state["project_info"] = pinfo
        save_settings("project_info", pinfo)

    dp = bundle.get("design_params")
    if isinstance(dp, dict):
        try:
            fc = float(dp.get("fc", 240.0))
        except (TypeError, ValueError):
            fc = 240.0
        sr = dp.get("steel_type_sr")
        sr = sr if sr in STEEL_FY_KSC else "SR24"
        sd = dp.get("steel_type_sd")
        sd = sd if sd in STEEL_FY_KSC else "SD40"
        st.session_state["design_params_fc"] = fc
        st.session_state["design_params_steel_sr"] = sr
        st.session_state["design_params_steel_sd"] = sd
        st.session_state["design_params_sr"] = calc_params(fc, sr)
        st.session_state["design_params_sd"] = calc_params(fc, sd)
        st.session_state["design_params"] = st.session_state["design_params_sd"]
        save_settings("design_params", {"fc": fc, "steel_type_sr": sr, "steel_type_sd": sd})

    items = bundle.get("saved_items")
    if isinstance(items, dict):
        st.session_state["saved_items"] = {
            k: (items.get(k) if isinstance(items.get(k), dict) else {}) for k in MODULE_LABELS
        }
    else:
        st.session_state["saved_items"] = {k: {} for k in MODULE_LABELS}

    return True
