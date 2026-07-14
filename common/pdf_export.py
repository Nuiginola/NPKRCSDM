"""
common/pdf_export.py — แปลงรายงาน HTML เป็นไฟล์ PDF สำหรับปุ่มดาวน์โหลด

วิธีที่เลือกใช้: เรียก Microsoft Edge (msedge.exe) แบบ headless
(--headless=new --print-to-pdf=...) ซึ่งมีอยู่แล้วในเครื่อง Windows ทุกเครื่อง
(เป็นส่วนหนึ่งของ Windows 10/11 และเป็นตัวเดียวกับ WebView2 runtime ที่โปรแกรมนี้
ใช้แสดงหน้าต่างอยู่แล้วผ่าน pywebview — ดู desktop_app.py) — เลือกวิธีนี้แทน
weasyprint/wkhtmltopdf/playwright เพราะไม่ต้องเพิ่มไลบรารี/ไบนารีเข้าไปในตัว
ติดตั้งเลยแม้แต่ไบต์เดียว (weasyprint ต้องพึ่ง native library Pango/Cairo ที่
ติดตั้งยากบน embeddable Python แบบพกพา, playwright ต้องแนบ Chromium ~300MB)

ถ้าหา Edge ไม่เจอ หรือแปลงไม่สำเร็จด้วยเหตุใดก็ตาม (เช่น timeout, ไม่มีสิทธิ์เขียน
ไฟล์ชั่วคราว) ฟังก์ชันจะคืนค่า None แทนที่จะทำให้แอปพัง — download_report_button()
จะ fallback ไปให้ดาวน์โหลดเป็นไฟล์ HTML แทนโดยอัตโนมัติ พร้อมข้อความแจ้งเตือน

หมายเหตุสำคัญ: การเรียก msedge.exe จริงทดสอบได้เฉพาะบนเครื่อง Windows ของผู้ใช้
เท่านั้น (ไม่มี Edge ในแซนด์บ็อกซ์ Linux ที่ใช้พัฒนา) — โค้ดนี้อ้างอิงจาก Chromium
headless command-line switches ที่มีเอกสารรองรับ (--headless=new, --disable-gpu,
--print-to-pdf, --no-pdf-header-footer) แต่ยังไม่เคยยืนยันผลจริงบนเครื่องผู้ใช้
"""

import base64
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

_IS_WINDOWS = sys.platform == "win32"

# ถ้าไฟล์เล็กกว่านี้ จะฝัง base64 ไว้ในปุ่มเผื่อ fallback (ดาวน์โหลดแบบเบราว์เซอร์) เมื่อ
# ไม่ได้เปิดผ่านหน้าต่างโปรแกรม — ไฟล์ใหญ่กว่านี้ (เช่น PDF หลายหน้า) จะไม่ฝัง กันหน้าเว็บอืด
_NATIVE_SAVE_FALLBACK_MAX = 3 * 1024 * 1024  # 3 MB

# เทมเพลต HTML/JS ของปุ่ม "บันทึกไฟล์" ที่เรียกกล่อง Save As เนทีฟผ่าน pywebview bridge
# (แทน st.download_button ที่ WebView2 บล็อก) — โทเคน __XXX__ ถูกแทนค่าใน native_save_button()
_NATIVE_SAVE_TEMPLATE = """
<style>
  .npk-save-wrap { font-family: "Source Sans Pro", system-ui, sans-serif; }
  .npk-save-btn {
     width: 100%; box-sizing: border-box; cursor: pointer;
     background: __COLOR__; color: #ffffff; font-weight: 700; font-size: 0.9rem;
     border: none; border-radius: 8px; padding: 9px 12px; line-height: 1.3;
  }
  .npk-save-btn:hover { filter: brightness(0.94); }
  .npk-save-btn:disabled { opacity: 0.6; cursor: default; }
  .npk-save-msg { margin-top: 6px; font-size: 0.78rem; color: #1E3853; word-break: break-all; }
</style>
<div class="npk-save-wrap">
  <button class="npk-save-btn" id="npkbtn"></button>
  <div class="npk-save-msg" id="npkmsg"></div>
</div>
<script>
  var LABEL   = __LABEL_JS__;
  var TMP     = __TMP_JS__;
  var NAME    = __NAME_JS__;
  var DATAURL = __DATAURL_JS__;
  var btn = document.getElementById('npkbtn');
  var msg = document.getElementById('npkmsg');
  btn.textContent = LABEL;

  function npkGetApi() {
     try { if (window.parent && window.parent.pywebview && window.parent.pywebview.api) return window.parent.pywebview.api; } catch (e) {}
     try { if (window.top && window.top.pywebview && window.top.pywebview.api) return window.top.pywebview.api; } catch (e) {}
     return null;
  }

  btn.onclick = function () {
     var api = npkGetApi();
     if (api && api.save_file) {
        msg.textContent = 'กำลังเปิดกล่องบันทึก...';
        api.save_file(TMP, NAME).then(function (saved) {
           msg.textContent = saved ? ('บันทึกแล้ว: ' + saved) : 'ยกเลิกการบันทึก';
        }).catch(function (e) { msg.textContent = 'ผิดพลาด: ' + e; });
     } else if (DATAURL) {
        var a = document.createElement('a');
        a.href = DATAURL; a.download = NAME;
        document.body.appendChild(a); a.click(); a.remove();
        msg.textContent = 'ดาวน์โหลดไฟล์แล้ว';
     } else {
        msg.textContent = 'กรุณาเปิดผ่านโปรแกรม (ไฟล์ขนาดใหญ่บันทึกผ่านเบราว์เซอร์ไม่ได้)';
     }
  };
</script>
"""


def native_save_button(label: str, data, file_name: str, key: str,
                       mime: str = "application/octet-stream",
                       color: str = "#2563EB", height: int = 70) -> None:
    """ปุ่ม "บันทึกไฟล์" ที่เปิดกล่อง Save As เนทีฟของ Windows (ผ่าน pywebview bridge)
    ใช้แทน st.download_button ซึ่งถูก WebView2/pywebview บล็อก (กดแล้วไม่มีอะไรเกิดขึ้น)

    กลไก: เขียน `data` ลงไฟล์ชั่วคราวครั้งเดียว (แคชด้วย hash ของเนื้อหา ไม่เขียนซ้ำทุก
    rerun) แล้วแสดงปุ่ม HTML ที่กดแล้วเรียก window.pywebview.api.save_file(tempPath, name)
    ให้ฝั่งโปรแกรมเปิดกล่อง Save As แล้วคัดลอกไฟล์ไปยังที่ผู้ใช้เลือก — ส่งผ่านหน้าเว็บแค่
    "ที่อยู่ไฟล์ชั่วคราว" ไม่ใช่ข้อมูลไฟล์ทั้งก้อน; ถ้าเปิดผ่านเบราว์เซอร์ (ไม่มี pywebview)
    จะ fallback เป็นดาวน์โหลด blob ปกติ (เฉพาะไฟล์ <= 3 MB ที่ฝัง base64 ไว้)
    """
    if isinstance(data, str):
        data = data.encode("utf-8")

    digest = hashlib.md5(data).hexdigest()
    tmp_key = f"_npksave_tmp_{key}"
    sig_key = f"{tmp_key}_sig"
    if st.session_state.get(sig_key) != digest or not st.session_state.get(tmp_key):
        ext = os.path.splitext(file_name)[1] or ".dat"
        tmp_path = os.path.join(tempfile.gettempdir(), f"npk_save_{digest[:12]}{ext}")
        try:
            with open(tmp_path, "wb") as fh:
                fh.write(data)
            st.session_state[tmp_key] = tmp_path
            st.session_state[sig_key] = digest
        except Exception:
            st.session_state[tmp_key] = ""
    tmp_path = st.session_state.get(tmp_key) or ""

    if len(data) <= _NATIVE_SAVE_FALLBACK_MAX:
        dataurl_js = json.dumps(f"data:{mime};base64,{base64.b64encode(data).decode('ascii')}")
    else:
        dataurl_js = "null"

    html = (_NATIVE_SAVE_TEMPLATE
            .replace("__COLOR__", color)
            .replace("__LABEL_JS__", json.dumps(label))
            .replace("__TMP_JS__", json.dumps(tmp_path))
            .replace("__NAME_JS__", json.dumps(file_name))
            .replace("__DATAURL_JS__", dataurl_js))
    components.html(html, height=height)

_EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def _find_edge() -> str | None:
    for path in _EDGE_CANDIDATES:
        if Path(path).exists():
            return path
    found = shutil.which("msedge")
    if found:
        return found
    return None


def html_to_pdf(html: str, timeout: float = 25.0) -> bytes | None:
    """แปลง HTML string เป็น PDF bytes ด้วย Microsoft Edge headless mode
    คืนค่า None ถ้าแปลงไม่สำเร็จไม่ว่าด้วยเหตุใด (ไม่มี Edge / timeout / error)"""
    if not _IS_WINDOWS:
        return None
    edge = _find_edge()
    if not edge:
        return None
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            html_path = Path(tmpdir) / "report.html"
            pdf_path = Path(tmpdir) / "report.pdf"
            html_path.write_text(html, encoding="utf-8")
            subprocess.run(
                [
                    edge,
                    "--headless=new",
                    "--disable-gpu",
                    "--disable-software-rasterizer",
                    "--no-pdf-header-footer",
                    f"--print-to-pdf={pdf_path}",
                    html_path.as_uri(),
                ],
                capture_output=True,
                timeout=timeout,
                check=False,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            if pdf_path.exists() and pdf_path.stat().st_size > 0:
                return pdf_path.read_bytes()
    except Exception:
        pass
    return None


def download_report_button(base_label: str, report_html: str, file_stem: str, key: str = None) -> None:
    """แสดงปุ่มดาวน์โหลดรายงาน — เป็น PDF ถ้าแปลงสำเร็จ (ค่าเริ่มต้นที่ต้องการ),
    หรือ HTML ถ้าแปลงไม่ได้ (fallback อัตโนมัติ พร้อมคำอธิบาย ไม่ทำให้ใช้งานไม่ได้)

    ทำงานแบบ 2 จังหวะโดยตั้งใจ (ไม่แปลงอัตโนมัติ): ครั้งแรกที่เห็นรายงานนี้ (หรือเนื้อหา
    รายงานเปลี่ยนไปจากเดิม) จะแสดงปุ่ม "สร้างไฟล์ PDF" ให้กดเอง — กดแล้วถึงจะเรียก Edge
    headless แปลงเป็น PDF (มี spinner ระหว่างรอ) จากนั้นจึงเปลี่ยนเป็นปุ่มดาวน์โหลดจริง
    ต้องกดปุ่มดาวน์โหลดอีกครั้งไฟล์ถึงจะลงเครื่อง (พฤติกรรมปกติของเบราว์เซอร์) — ไม่มี
    การแปลง PDF เกิดขึ้นเองระหว่างที่ผู้ใช้แค่แก้ไขค่าอื่นๆ ในหน้าแล้ว rerun ตามคำขอผู้ใช้
    ("การดาวน์โหลดจะไม่ทำงานอัตโนมัติ ต้องคลิกที่ปุ่มดาวน์โหลดเท่านั้น")

    base_label: ข้อความหลักไม่ต้องมีคำว่า PDF/HTML ต่อท้าย เช่น "ดาวน์โหลดรายการคำนวณ"
    file_stem: ชื่อไฟล์ไม่รวมนามสกุล (จะเติม .pdf/.html ให้เอง)
    key: ใช้แยกแคชการแปลง PDF ต่อรายงาน (ถ้าไม่ระบุจะใช้ file_stem แทน) — จำเป็นถ้า
    มีปุ่มดาวน์โหลดมากกว่า 1 ปุ่มในหน้าเดียวกันที่ใช้ file_stem ซ้ำกัน
    """
    cache_key = f"_pdf_cache_{key or file_stem}"
    src_key = f"{cache_key}_src"

    # เนื้อหารายงานเปลี่ยนไปจากรอบก่อน (เช่นผู้ใช้แก้ input แล้วคำนวณใหม่) — ล้าง PDF
    # เดิมทิ้ง บังคับให้ต้องกด "สร้างไฟล์ PDF" ใหม่เอง ไม่ auto-regenerate ให้เงียบๆ
    if st.session_state.get(src_key) != report_html:
        st.session_state[cache_key] = None
        st.session_state[src_key] = report_html

    pdf_bytes = st.session_state.get(cache_key)

    if pdf_bytes is None:
        if st.button(f"📄 สร้างไฟล์ {base_label} (PDF)", key=f"{key or file_stem}_gen"):
            with st.spinner("กำลังสร้างไฟล์ PDF..."):
                generated = html_to_pdf(report_html)
            # เก็บ b"" (falsy แต่ไม่ใช่ None) แทน "ลองแปลงแล้วแต่ไม่สำเร็จ" เพื่อแยกจาก
            # None ("ยังไม่เคยกดสร้างเลย") — ให้ fallback แสดงปุ่ม HTML แทนได้ทันที
            st.session_state[cache_key] = generated if generated else b""
            st.rerun()
        return

    if pdf_bytes:
        native_save_button(
            f"⬇️ {base_label} (PDF)",
            pdf_bytes,
            f"{file_stem}.pdf",
            key=key or file_stem,
            mime="application/pdf",
            color="#0D9488",
        )
    else:
        native_save_button(
            f"⬇️ {base_label} (HTML — เปิดแล้วกดพิมพ์ได้)",
            report_html,
            f"{file_stem}.html",
            key=key or file_stem,
            mime="text/html",
            color="#0D9488",
        )
        st.caption("⚠️ ไม่พบ Microsoft Edge สำหรับแปลงเป็น PDF อัตโนมัติ — บันทึกเป็น HTML แทนชั่วคราว")

