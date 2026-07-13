"""
common/report_preview.py — หน้าต่าง "Preview รายการคำนวณ" แบบ PDF viewer (เปิดหน้าต่างใหม่)

ที่มา: ผู้ใช้ต้องการปุ่ม "แสดงรายการคำนวณ" ที่เปิดหน้าต่างใหม่เต็มจอ แสดงกระดาษ A4
กลางจอ มี toolbar แบบ PDF, ปุ่ม Print, ปุ่ม Close, header/footer, เลขหน้า, รองรับ
หลายหน้า และเผื่อ export PDF — โดย **ไม่พึ่ง auto window.print()** (เคยล้มเหลวใน WebView2
มาแล้ว — ดู npk-rc-sdm-status.md) และ **ไม่ฝังไลบรารีหนักอย่าง paged.js** (~500KB)

กลไก:
- report_html ที่ build มา เป็นเอกสาร A4 สมบูรณ์อยู่แล้ว (มี @page/A4, .page-break,
  header ของโครงการ, รูป base64) — เราแค่ "ห่อ" มันด้วย shell ของ PDF viewer
- ฝั่ง JavaScript ในหน้าต่างใหม่จะ parse report_html แยกเนื้อหา <body> ออกเป็น "แผ่น
  A4" ตามจุด .page-break ที่มีอยู่แล้ว วางกลางจอบนพื้นเทา (เหมือนโปรแกรมอ่าน PDF) และ
  ใส่เลขหน้า "หน้า X / N" ที่ท้ายแต่ละแผ่น
- toolbar ด้านบน (fixed) มีปุ่มพิมพ์/บันทึก PDF (window.print — ผู้ใช้กดเอง ไม่ auto),
  ซูม A-/A+, และปิดหน้าต่าง — เมื่อพิมพ์ @media print จะซ่อน toolbar/กรอบแผ่น แล้วปล่อย
  ให้ @page + .page-break ของ report จัดหน้าจริง (ได้ PDF/พิมพ์แบ่งหน้าถูกต้อง + เลือก
  "Save as PDF" ในกล่องพิมพ์ = export PDF)
- เปิดหน้าต่างด้วย Blob URL + window.open() ภายใน onclick จริง (synchronous กับคลิก)
  ซึ่งเป็นกลไกที่ WebView2 ไม่บล็อก (ต่างจาก data: URL / auto-popup)
"""

import base64
import hashlib
import json
import os
import sys
import tempfile

import streamlit as st
import streamlit.components.v1 as components

# เดสก์ท็อป (Windows + pywebview) = เปิดรายงานเป็นหน้าต่างเนทีฟ
# คลาวด์/มือถือ (Linux, ไม่มี pywebview) = แสดงรายงานฝังในหน้าเว็บแทน
_IS_DESKTOP = sys.platform.startswith("win")

# ---------------------------------------------------------------------------
# HTML shell ของหน้าต่าง Preview — โทเคน __REPORT_B64__ ถูกแทนด้วย base64 ของ report_html
# ---------------------------------------------------------------------------
_PREVIEW_SHELL_TEMPLATE = r"""<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>NPK RC SDM — รายการคำนวณ</title>
<style>
  :root { --pv-bar: #323639; --pv-bar2: #4a4e51; --pv-bg: #525659; --teal: #0D9488; }
  html, body { margin: 0; padding: 0; background: var(--pv-bg); }
  body { font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; }

  .pv-toolbar {
     position: fixed; top: 0; left: 0; right: 0; height: 50px; z-index: 1000;
     background: var(--pv-bar); color: #fff; display: flex; align-items: center;
     gap: 10px; padding: 0 16px; box-shadow: 0 1px 6px rgba(0,0,0,.45);
  }
  .pv-toolbar .title { font-weight: 700; font-size: 15px; white-space: nowrap; }
  .pv-toolbar .pginfo { font-size: 13px; opacity: .8; margin-left: 6px; white-space: nowrap; }
  .pv-toolbar .spacer { flex: 1; }
  .pv-btn {
     background: var(--pv-bar2); color: #fff; border: none; border-radius: 6px;
     padding: 8px 14px; cursor: pointer; font-size: 14px; font-weight: 600;
     font-family: inherit; white-space: nowrap;
  }
  .pv-btn:hover { filter: brightness(1.15); }
  .pv-btn.primary { background: var(--teal); }
  .pv-btn.close { background: #DC2626; }

  .pv-scroll { position: absolute; top: 50px; left: 0; right: 0; bottom: 0; overflow: auto; }
  .pv-pages {
     padding: 26px 0 46px; display: flex; flex-direction: column; align-items: center;
     gap: 22px; transform-origin: top center;
  }
  .pv-sheet {
     width: 210mm; min-height: 297mm; background: #fff; box-sizing: border-box;
     box-shadow: 0 4px 16px rgba(0,0,0,.55); position: relative; padding: 12mm 12mm 16mm 12mm;
  }
  .pv-foot {
     position: absolute; left: 12mm; right: 12mm; bottom: 6mm; text-align: center;
     font-size: 11px; color: #888; border-top: 1px solid #e5e5e5; padding-top: 4px;
  }
  .pv-loading { color: #eee; text-align: center; padding: 60px 20px; font-size: 16px; }

  @media print {
     .pv-toolbar { display: none !important; }
     .pv-scroll { position: static; overflow: visible; top: 0; }
     .pv-pages { padding: 0 !important; gap: 0 !important; transform: none !important; display: block !important; }
     .pv-sheet {
        width: auto !important; min-height: auto !important; box-shadow: none !important;
        margin: 0 !important; padding: 0 !important;
     }
     .pv-foot { display: none !important; }
     html, body { background: #fff !important; }
  }
</style>
</head>
<body>
  <div class="pv-toolbar">
     <span class="title">NPK RC SDM — รายการคำนวณ</span>
     <span class="pginfo" id="pv-pginfo"></span>
     <span class="spacer"></span>
     <button class="pv-btn" onclick="pvZoom(-1)">A−</button>
     <button class="pv-btn" onclick="pvZoom(1)">A+</button>
     <button class="pv-btn primary" onclick="window.print()">🖨️ พิมพ์ / บันทึก PDF</button>
     <button class="pv-btn close" onclick="pvClose()">✕ ปิด</button>
  </div>
  <div class="pv-scroll">
     <div class="pv-pages" id="pv-pages"><div class="pv-loading">กำลังจัดหน้า...</div></div>
  </div>

<script>
  var PV_REPORT_B64 = "__REPORT_B64__";
  var pvScale = 1.0;

  function pvZoom(dir) {
     pvScale = Math.min(1.8, Math.max(0.5, pvScale + dir * 0.1));
     document.getElementById('pv-pages').style.transform = 'scale(' + pvScale + ')';
  }

  function pvClose() {
     // ปิดหน้าต่าง Preview: ผ่าน js_api ของ pywebview ก่อน (window.close ปกติ WebView2 บล็อก)
     try {
        if (window.pywebview && window.pywebview.api && window.pywebview.api.close_win) {
           window.pywebview.api.close_win(); return;
        }
     } catch (e) {}
     try { window.close(); } catch (e) {}
  }

  function pvB64ToUtf8(b64) {
     // decode base64 -> UTF-8 string (รองรับภาษาไทย)
     var bin = atob(b64);
     var bytes = new Uint8Array(bin.length);
     for (var i = 0; i < bin.length; i++) bytes[i] = bin.charCodeAt(i);
     return new TextDecoder('utf-8').decode(bytes);
  }

  function pvBuild() {
     var reportHtml = pvB64ToUtf8(PV_REPORT_B64);
     var doc = new DOMParser().parseFromString(reportHtml, 'text/html');

     // นำ <style> ของรายงานมาใช้ (ก่อน style ของ shell ที่อยู่ใน <head> แล้ว shell จึงชนะจุดที่ทับกัน)
     var firstShellStyle = document.head.querySelector('style');
     doc.querySelectorAll('style').forEach(function (s) {
        var st = document.createElement('style');
        st.textContent = s.textContent;
        document.head.insertBefore(st, firstShellStyle);
     });

     // แยกเนื้อหา body ออกเป็นแผ่นตามจุด .page-break / .page-break-before
     var nodes = Array.prototype.slice.call(doc.body.childNodes);
     var sheets = [[]];
     nodes.forEach(function (node) {
        var isBreak = node.nodeType === 1 && node.classList &&
           (node.classList.contains('page-break') || node.classList.contains('page-break-before'));
        if (isBreak && sheets[sheets.length - 1].length > 0) sheets.push([]);
        sheets[sheets.length - 1].push(node);
     });

     var pages = document.getElementById('pv-pages');
     pages.innerHTML = '';
     var total = sheets.length;
     sheets.forEach(function (group, idx) {
        var sheet = document.createElement('div');
        sheet.className = 'pv-sheet';
        group.forEach(function (n) { sheet.appendChild(document.importNode(n, true)); });
        var foot = document.createElement('div');
        foot.className = 'pv-foot';
        foot.textContent = 'NPK RC SDM  •  หน้า ' + (idx + 1) + ' / ' + total;
        sheet.appendChild(foot);
        pages.appendChild(sheet);
     });
     document.getElementById('pv-pginfo').textContent = total + ' หน้า';
  }

  try { pvBuild(); }
  catch (e) {
     document.getElementById('pv-pages').innerHTML =
        '<div class="pv-loading">แสดงตัวอย่างไม่สำเร็จ: ' + e + '</div>';
  }
</script>
</body>
</html>
"""

# ---------------------------------------------------------------------------
# ปุ่มบนหน้าโมดูล (components.html) ที่กดแล้วเปิดหน้าต่าง Preview
# ---------------------------------------------------------------------------
_OPEN_BTN_TEMPLATE = r"""
<style>
  .npk-openpv-btn {
     width: 100%; box-sizing: border-box; cursor: pointer;
     background: __COLOR__; color: #fff; font-weight: 700; font-size: 0.9rem;
     border: none; border-radius: 8px; padding: 9px 12px; font-family: inherit;
  }
  .npk-openpv-btn:hover { filter: brightness(0.94); }
  .npk-openpv-msg { margin-top: 6px; font-size: 0.76rem; color: #1E3853; }
</style>
<button class="npk-openpv-btn" id="npkpv"></button>
<div class="npk-openpv-msg" id="npkpvmsg"></div>
<script>
  var PV_LABEL = __LABEL_JS__;
  var PV_TMP = __TMP_JS__;
  var b = document.getElementById('npkpv');
  var msg = document.getElementById('npkpvmsg');
  b.textContent = PV_LABEL;

  function pvGetApi() {
     try { if (window.parent && window.parent.pywebview && window.parent.pywebview.api) return window.parent.pywebview.api; } catch (e) {}
     try { if (window.top && window.top.pywebview && window.top.pywebview.api) return window.top.pywebview.api; } catch (e) {}
     return null;
  }

  b.onclick = function () {
     var api = pvGetApi();
     if (api && api.open_preview) {
        // เปิดหน้าต่างเนทีฟผ่านฝั่งโปรแกรม (webview.create_window) — WebView2 บล็อก window.open(blob)
        msg.textContent = 'กำลังเปิดหน้าต่าง Preview...';
        api.open_preview(PV_TMP).then(function (ok) {
           msg.textContent = ok ? '' : 'เปิด Preview ไม่สำเร็จ (ไม่พบไฟล์ชั่วคราว)';
        }).catch(function (e) { msg.textContent = 'ผิดพลาด: ' + e; });
     } else {
        msg.textContent = 'กรุณาเปิดผ่านโปรแกรม NPK RC SDM (โหมดหน้าต่างโปรแกรม)';
     }
  };
</script>
"""


def mark_calc_pending_sync(prefix: str) -> None:
    """เรียกทันทีในบล็อกปุ่ม "คำนวณ" (พร้อมกับตั้งค่า session_state ผลลัพธ์) — ตั้งค่า flag
    บอกว่ารอบ rerun นี้มาจากการกดคำนวณจริง ให้ sync_report_html() (ด้านล่าง) รู้ว่าต้อง
    rerun ซ้ำอีกครั้งหลัง report_html พร้อม ดู sync_report_html() สำหรับเหตุผลเต็ม

    prefix ต้องเป็นค่าเดียวกับที่ส่งให้ sync_report_html() ในหน้าเดียวกัน (ตั้งชื่อเองได้อิสระ
    ไม่ต้องตรงกับชื่อ session_state key อื่นๆ ในหน้า เช่น "tw", "bs", "ct")"""
    st.session_state[f"_pending_report_sync_{prefix}"] = True


def sync_report_html(prefix: str, report_html: str) -> None:
    """เก็บ report_html ที่เพิ่ง build เสร็จลง session_state[f"{prefix}_report_html"] แล้ว
    rerun อัตโนมัติอีกครั้ง **เฉพาะรอบที่มาจากการกดปุ่มคำนวณจริง** (เช็คด้วย flag จาก
    mark_calc_pending_sync() — pop ออกทันทีกันไม่ให้ rerun วนซ้ำไม่รู้จบ)

    แก้บั๊ก 2026-07-12 (ผู้ใช้แจ้ง): ปุ่ม "แสดงรายการคำนวณ" แถวบนของหน้า อ่านค่า
    session_state[f"{prefix}_report_html"] — แต่ Streamlit รันสคริปต์บนลงล่างครั้งเดียวต่อรอบ
    โค้ดส่วนแถวปุ่มด้านบนจึงรันไปแล้ว (อ่านค่าเก่า/ยังไม่มีค่า) ก่อนจะมาถึงจุดนี้ (คำนวณ
    report_html เสร็จ ซึ่งต้องรอผลลัพธ์+รูปวาดด้านล่างของหน้าก่อน) ทำให้ต้องกดคำนวณ 2 ครั้ง
    (หรือดับเบิลคลิก) ปุ่มแถวบนถึงจะอัปเดต — เรียกฟังก์ชันนี้แทนการเซ็ต session_state ตรงๆ
    เพื่อบังคับ rerun เพิ่มอีกหนึ่งรอบทันทีหลังคำนวณเสร็จ (โปร่งใสกับผู้ใช้ เหมือนกดครั้งเดียว)"""
    st.session_state[f"{prefix}_report_html"] = report_html
    if st.session_state.pop(f"_pending_report_sync_{prefix}", False):
        st.rerun()


@st.dialog("📄 รายการคำนวณ", width="large")
def _open_report_dialog(report_html: str) -> None:
    """เปิดรายการคำนวณเป็นหน้าต่างป๊อปอัปเต็มจอ (สำหรับคลาวด์/มือถือ ที่ไม่มี pywebview)
    — แสดงรายงาน A4 ในกรอบเลื่อนดูได้ กดกากบาทมุมบนเพื่อปิด"""
    st.caption("เลื่อนดูรายงานด้านล่าง • บันทึกเป็น PDF ได้จากปุ่ม 📥 ดาวน์โหลด บนหน้าโมดูล")
    components.html(report_html, height=820, scrolling=True)


def build_preview_shell(report_html: str) -> str:
    """ห่อ report_html ด้วย shell ของหน้าต่าง Preview แล้วคืนเป็น HTML สมบูรณ์ (self-contained)"""
    b64 = base64.b64encode(report_html.encode("utf-8")).decode("ascii")
    return _PREVIEW_SHELL_TEMPLATE.replace("__REPORT_B64__", b64)


def open_preview_button(label: str, report_html: str, key: str = "",
                        color: str = "#0D9488", height: int = 64) -> None:
    """ปุ่มบนหน้าโมดูล กดแล้วเปิดหน้าต่าง Preview รายการคำนวณ (PDF viewer)

    เขียนไฟล์ Preview (shell + report) ลงไฟล์ .html ชั่วคราวครั้งเดียว (แคชด้วย hash)
    แล้วให้ปุ่มเรียก window.pywebview.api.open_preview(tempPath) เพื่อให้ฝั่งโปรแกรม
    เปิดหน้าต่างเนทีฟใหม่ชี้ไปที่ไฟล์นั้น — **ไม่ใช้ window.open(blob) เพราะ WebView2
    ไม่เปิดหน้าต่างให้ (พยายามส่ง blob: URL ให้ OS เปิด)** ส่งผ่านหน้าเว็บแค่ path สั้นๆ

    บนคลาวด์/มือถือ (ไม่ใช่ Windows) ไม่มี pywebview — จึงแสดงรายการคำนวณ "ฝังในหน้า"
    (iframe) โดยกดปุ่มเพื่อเปิด/ปิด แทนการเปิดหน้าต่างเนทีฟ ทำให้ดูรายงานบนไอแพด/มือถือได้
    """
    # ===== คลาวด์/มือถือ: แสดงรายการคำนวณเป็นหน้าต่างป๊อปอัป (dialog) เต็มจอ =====
    if not _IS_DESKTOP:
        if st.button(label, key=f"_pvbtn_{key}", use_container_width=True):
            _open_report_dialog(report_html)
        return

    # ===== เดสก์ท็อป (pywebview): เปิดหน้าต่างเนทีฟ (โค้ดเดิม) =====
    shell = build_preview_shell(report_html)
    data = shell.encode("utf-8")
    digest = hashlib.md5(data).hexdigest()
    tmp_key = f"_pvfile_{key}"
    sig_key = f"{tmp_key}_sig"
    if st.session_state.get(sig_key) != digest or not st.session_state.get(tmp_key):
        tmp_path = os.path.join(tempfile.gettempdir(), f"npk_preview_{digest[:12]}.html")
        try:
            with open(tmp_path, "wb") as fh:
                fh.write(data)
            st.session_state[tmp_key] = tmp_path
            st.session_state[sig_key] = digest
        except Exception:
            st.session_state[tmp_key] = ""
    tmp_path = st.session_state.get(tmp_key) or ""

    html = (_OPEN_BTN_TEMPLATE
            .replace("__COLOR__", color)
            .replace("__LABEL_JS__", json.dumps(label))
            .replace("__TMP_JS__", json.dumps(tmp_path)))
    components.html(html, height=height)
