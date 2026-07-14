"""
NPK RC SDM — Desktop launcher (หน้าต่างโปรแกรมจริง ไม่ใช่เบราว์เซอร์)

เดิม run_app.bat เรียก "streamlit run app.py" ตรงๆ ทำให้ Streamlit เปิด Chrome/Edge
ขึ้นมาแสดงผล ซึ่งมีแถบที่อยู่ (address bar) แท็บ และ UI ของเบราว์เซอร์ให้เห็น ทำให้
ดูเหมือน "เว็บไซต์" มากกว่า "โปรแกรม"

ไฟล์นี้แก้ปัญหานั้นโดย:
1. รัน Streamlit server เป็น subprocess เบื้องหลัง (--server.headless true = ไม่เปิด
   เบราว์เซอร์เอง, --server.address 127.0.0.1 = ผูกกับเครื่องตัวเองเท่านั้น) บน port
   ที่สุ่มหาว่าง เพื่อกันปัญหา "port 8501 ถูกใช้งานอยู่แล้ว" ที่เจอบ่อยตอนใช้ port ตายตัว
2. รอให้ server พร้อม (poll endpoint /_stcore/health ของ Streamlit เอง)
3. เปิดหน้าต่างเนทีฟของ Windows ผ่าน pywebview (บน Windows ใช้ WebView2 / Microsoft
   Edge Chromium engine ผ่าน pythonnet เป็นตัวเรนเดอร์ — ไม่ใช่เปิดโปรแกรม Edge/Chrome
   แยกต่างหาก) ชี้ไปที่ Streamlit server — ผลลัพธ์คือหน้าต่างเปล่าไม่มี address bar/แท็บ
   ดูเหมือนโปรแกรม desktop จริง แม้เบื้องหลังยังเป็นเว็บแอป Streamlit เหมือนเดิม
4. เมื่อผู้ใช้ปิดหน้าต่าง จะสั่ง terminate() ปิด Streamlit server ทันที ไม่ปล่อยค้าง
   เป็น process กำพร้า (orphan) อยู่เบื้องหลัง

การซ่อนหน้าต่าง console (2026-07-12): subprocess ของ Streamlit ถูกสั่งด้วยธง
CREATE_NO_WINDOW บน Windows เพื่อไม่ให้เด้งหน้าต่าง console ดำขึ้นมาต่างหาก — สำคัญมาก
เมื่อ launcher เรียกไฟล์นี้ด้วย pythonw.exe (ซึ่งไม่มี console ของตัวเอง) เพราะถ้าไม่ใส่
ธงนี้ ตัว subprocess ที่เป็น console app จะสร้าง console หน้าต่างใหม่ขึ้นมาเอง

Run with: pythonw.exe desktop_app.py   (แนะนำ — ไม่มี console)
      หรือ python.exe desktop_app.py    (มี console สำหรับดู error ตอน debug)
"""

import os
import shutil
import socket
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import webview

APP_DIR = Path(__file__).resolve().parent
APP_FILE = APP_DIR / "app.py"

# ไฟล์ log สำหรับ debug ตอนเปิดโปรแกรม — เขียนได้แม้รันด้วย pythonw.exe (ที่ไม่มี console
# และ print()/traceback ไม่ถูกเก็บใน run_log.txt) เพื่อให้เห็นสาเหตุจริงเวลาเปิดไม่ขึ้น
_STARTUP_LOG = APP_DIR / "startup_log.txt"


def _dbg(msg: str) -> None:
    """เขียนข้อความ debug ต่อท้าย startup_log.txt พร้อม timestamp (ไม่ให้ error เขียน log
    ทำให้โปรแกรมพัง — ห่อ try/except เงียบๆ)"""
    try:
        with open(_STARTUP_LOG, "a", encoding="utf-8", errors="replace") as fh:
            fh.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass

# ธงสำหรับ subprocess.Popen บน Windows: ไม่สร้างหน้าต่าง console ให้ subprocess
# (subprocess.CREATE_NO_WINDOW = 0x08000000) — กำหนดเป็นค่าคงที่ตรงๆ กันกรณีรันบน
# Python ที่ไม่มี attribute นี้ (เช่นบางแพลตฟอร์ม) แล้วค่อยเลือกใช้เฉพาะบน win32
_CREATE_NO_WINDOW = 0x08000000


class _PreviewApi:
    """js_api สำหรับหน้าต่าง Preview รายการคำนวณ — ให้ปุ่ม "✕ ปิด" ในหน้า Preview เรียก
    ปิดหน้าต่างตัวเองได้จริงผ่าน window.pywebview.api.close_win() (เพราะ window.close()
    ปกติ WebView2 บล็อกไม่ให้สคริปต์ปิดหน้าต่างที่ตัวเองไม่ได้เปิด)

    ⚠️ บั๊กที่แก้ 2026-07-12 (ผู้ใช้ยืนยันบนเครื่องจริง): เดิม close_win() เรียก self._window.destroy()
    — พบว่า destroy() หน้าต่าง Preview (ที่สร้างแบบไดนามิก) ทำให้ "ทั้งโปรแกรม" ปิดตามไปด้วย
    ไม่ใช่แค่หน้าต่าง Preview

    วิธีแก้: ไม่ destroy() หน้าต่าง Preview อีกเลย — ใช้ hide() แทน (ซ่อนไว้เฉยๆ) แล้วครั้งต่อไป
    ที่เปิดค่อย load_url()+show() หน้าต่างเดิมซ้ำ (ดู _Api.open_preview) — หน้าต่างเดียวใช้ตลอด
    อายุโปรแกรม ไม่สร้างใหม่/ทำลายทิ้งไปมา"""

    def __init__(self):
        self._window = None

    def bind_window(self, window) -> None:
        self._window = window

    def close_win(self) -> None:
        # ปุ่ม "✕ ปิด" ในหน้าเว็บ Preview — ซ่อนหน้าต่างแทนการทำลาย (destroy ทำให้ทั้งโปรแกรมปิด)
        if self._window is not None:
            try:
                self._window.hide()
            except Exception as exc:  # noqa: BLE001
                print("close_win error:", exc)

    def on_closing(self) -> bool:
        # ผู้ใช้กดปุ่ม X ที่กรอบหน้าต่าง Preview เอง (ไม่ใช่ปุ่มในหน้าเว็บ) — ซ่อนแทนปิดจริง
        # แล้วคืน False เพื่อยกเลิกการปิดจริงของ pywebview (กันหน้าต่างถูกทำลาย ซึ่งกระทบทั้งโปรแกรม)
        if self._window is not None:
            try:
                self._window.hide()
            except Exception:  # noqa: BLE001
                pass
        return False


class _Api:
    """js_api ผูกกับหน้าต่าง pywebview — ให้ฝั่ง JavaScript ของหน้าเว็บ Streamlit (ที่โหลด
    อยู่ในหน้าต่างนี้) เรียกปิดหน้าต่างโปรแกรมได้โดยตรงผ่าน window.pywebview.api.close_app()
    ใช้กับปุ่ม "ไม่ยินยอม" ในหน้าจอข้อจำกัดความรับผิดชอบของ app.py — เพราะ JS window.close()
    ปกติเบราว์เซอร์/WebView2 จะบล็อกไม่ให้สคริปต์ปิดหน้าต่างที่ตัวเองไม่ได้เป็นคนเปิดขึ้นมาเอง
    แต่ close_app() นี้เรียก window.destroy() ของ pywebview ตรงๆ ปิดได้จริงเสมอ"""

    def __init__(self):
        self._window = None
        self._preview_window = None   # หน้าต่าง Preview (สร้างครั้งแรกที่กดเปิด แล้วใช้ซ้ำ)
        self._preview_api = None

    def bind_window(self, window) -> None:
        self._window = window

    def close_app(self) -> None:
        if self._window is not None:
            self._window.destroy()

    def save_file(self, temp_path: str, suggested_name: str) -> str:
        """เปิดกล่อง "Save As" เนทีฟของ Windows ให้ผู้ใช้เลือกที่บันทึก แล้วคัดลอกไฟล์
        ชั่วคราว `temp_path` (ที่ฝั่ง Streamlit เขียนเตรียมไว้) ไปยังตำแหน่งที่เลือก

        ใช้แก้ปัญหา st.download_button ที่ WebView2 บล็อกการดาวน์โหลดแบบเบราว์เซอร์ —
        ฝั่งหน้าเว็บ (JavaScript) เรียกเมธอดนี้ผ่าน window.pywebview.api.save_file(...)
        โดยส่งมาแค่ "ที่อยู่ไฟล์ชั่วคราว" (สตริงสั้นๆ) ไม่ต้องส่งข้อมูลไฟล์ทั้งก้อนผ่าน
        หน้าเว็บ (ทั้งสอง process อยู่บนเครื่องเดียวกัน เข้าถึงไฟล์ชั่วคราวร่วมกันได้)

        คืนค่า: path ที่บันทึกจริง (str) หรือสตริงว่าง "" ถ้าผู้ใช้กดยกเลิก/เกิดข้อผิดพลาด
        """
        try:
            if self._window is None or not temp_path or not os.path.exists(temp_path):
                return ""
            ext = os.path.splitext(suggested_name)[1].lstrip(".")
            if ext:
                file_types = (f"{ext.upper()} file (*.{ext})", "All files (*.*)")
            else:
                file_types = ("All files (*.*)",)
            result = self._window.create_file_dialog(
                webview.SAVE_DIALOG,
                save_filename=suggested_name,
                file_types=file_types,
            )
            if not result:
                return ""
            dest = result[0] if isinstance(result, (list, tuple)) else result
            if not dest:
                return ""
            shutil.copyfile(temp_path, dest)
            return str(dest)
        except Exception as exc:  # noqa: BLE001 — คืน "" เสมอเมื่อพลาด ไม่ให้แอปพัง
            print("save_file error:", exc)
            return ""

    def open_preview(self, temp_path: str) -> bool:
        """แสดงไฟล์ Preview รายการคำนวณ (PDF viewer) เป็นหน้าต่างเนทีฟ

        ใช้แก้ปัญหา window.open(blob) ที่ WebView2 ไม่เปิดหน้าต่างให้ (พยายามส่ง blob:
        URL ให้ OS เปิด → ขึ้น "Get an app to open this blob link") — แทนที่ด้วยการให้
        ฝั่ง Python เปิดหน้าต่างเนทีฟจริงชี้ไปที่ไฟล์ preview (ที่ฝั่ง Streamlit เขียนเตรียมไว้
        เป็นไฟล์ .html ชั่วคราว) ผ่าน file:// URL

        กลไก (ปรับ 2026-07-12 กันบั๊ก 2 อย่าง):
        - ครั้งแรกที่กด: สร้างหน้าต่าง Preview แบบไดนามิกด้วย webview.create_window() (เส้นทางนี้
          พิสูจน์แล้วว่าเปิดหน้าต่างได้จริงบนเครื่องผู้ใช้) — **ไม่สร้างล่วงหน้าก่อน webview.start()**
          เพราะการสร้างหน้าต่างที่สองก่อน start() เคยทำให้โปรแกรมเปิดไม่ขึ้นเลย
        - ครั้งต่อไป: ใช้หน้าต่างเดิมซ้ำ (load_url ไฟล์ใหม่ + show) ไม่สร้างใหม่
        - ไม่มีการ destroy() หน้าต่าง Preview เลย — ปุ่มปิด/ปุ่ม X แค่ hide() (destroy ทำให้ทั้ง
          โปรแกรมปิดตาม — ดู _PreviewApi)

        คืน True ถ้าเปิดสำเร็จ, False ถ้าไฟล์ไม่มี/เกิดข้อผิดพลาด (ไม่ทำให้แอปพัง)
        """
        try:
            if not temp_path or not os.path.exists(temp_path):
                return False
            url = Path(temp_path).resolve().as_uri()

            if self._preview_window is None:
                # สร้างครั้งแรก (แบบไดนามิก = เส้นทางที่ทำงานได้จริง) แล้วเก็บไว้ใช้ซ้ำ
                self._preview_api = _PreviewApi()
                win = webview.create_window(
                    "NPK RC SDM - Preview",
                    url=url,
                    width=1200,
                    height=900,
                    js_api=self._preview_api,
                )
                self._preview_api.bind_window(win)
                # กันปุ่ม X ที่กรอบหน้าต่าง: ให้ซ่อนแทนทำลาย (ถ้าเวอร์ชัน pywebview รองรับ event นี้
                # — ถ้าไม่รองรับก็ข้ามไป ไม่ให้กระทบการเปิดหน้าต่าง)
                try:
                    win.events.closing += self._preview_api.on_closing
                except Exception as exc:  # noqa: BLE001
                    print("preview closing hook not available:", exc)
                self._preview_window = win
            else:
                # ใช้หน้าต่างเดิมซ้ำ: โหลดไฟล์ preview ใหม่ แล้วแสดง (ถ้าถูกซ่อนอยู่)
                self._preview_window.load_url(url)
                self._preview_window.show()
            return True
        except Exception as exc:  # noqa: BLE001
            print("open_preview error:", exc)
            return False


def _find_free_port() -> int:
    """หา port ว่างบนเครื่องแบบสุ่ม (bind กับ port 0 แล้วอ่านค่าที่ OS จัดสรรให้)
    กันปัญหา 'port 8501 ถูกใช้งานอยู่แล้ว' จากรอบก่อนที่ปิดโปรแกรมไม่สนิท"""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for_server(health_url: str, timeout: float = 40.0) -> bool:
    """รอจนกว่า Streamlit server จะพร้อมตอบ (poll /_stcore/health)
    คืน False ถ้าเกิน timeout (เผื่อเครื่องช้า/antivirus สแกนช้าตอนเริ่มโปรแกรมครั้งแรก)

    ปรับ 2026-07-12: poll ถี่ขึ้น (ทุก 0.15 วินาที แทน 0.4) และ timeout ต่อครั้งสั้นลง
    (1.0 วินาที) เพื่อให้เปิดหน้าต่างโปรแกรมได้เร็วขึ้นทันทีที่ server พร้อม"""
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(health_url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            pass
        time.sleep(0.15)
    return False


def _kill_streamlit_tree(proc) -> None:
    """ปิด Streamlit ให้สนิท "ทั้ง process tree" — proc.terminate() ฆ่าแค่ process ลูกตัวตรง
    (ตัว launcher ของ streamlit) แต่ Streamlit มี process ลูกหลานที่ไม่ถูกฆ่า เลยค้างเป็น orphan
    ถือ port/ไฟล์ล็อกไว้ → เปิดโปรแกรมครั้งต่อไปไม่ได้ (อาการ "เปิดได้ครั้งแรก ครั้งต่อไปไม่ได้")
    — taskkill /T ฆ่าทั้งต้นไม้ process (เงียบ ไม่มีหน้าต่าง console เด้ง)"""
    try:
        if sys.platform == "win32":
            subprocess.run(
                ["taskkill", "/F", "/T", "/PID", str(proc.pid)],
                creationflags=_CREATE_NO_WINDOW, capture_output=True, timeout=10,
            )
        else:
            proc.terminate()
    except Exception as exc:  # noqa: BLE001
        _dbg(f"kill streamlit tree failed: {exc}")
    try:
        proc.wait(timeout=5)
    except Exception:
        try:
            proc.kill()
        except Exception:
            pass


def _shutdown_and_exit(proc, st_log) -> None:
    """ปิดทุกอย่างให้สนิทแล้วจบ process ตัวเองทันที — ใช้เมื่อผู้ใช้ปิดหน้าต่างหลัก (= ปิดโปรแกรม)

    ⚠️ จำเป็นมาก: หน้าต่าง Preview รายการคำนวณถูกปิดด้วย hide() (ซ่อน ไม่ทำลาย) เพื่อกันบั๊ก
    "ปิด Preview แล้วโปรแกรมปิดตาม" — แต่ผลข้างเคียงคือเมื่อผู้ใช้ปิดหน้าต่างหลัก pywebview จะยัง
    เห็นว่ามีหน้าต่าง (ที่ซ่อนอยู่) ค้าง เลยไม่คืนค่าจาก webview.start() → โปรแกรมปิดไม่ลง (ค้าง)
    วิธีแก้: ดักอีเวนต์ปิดหน้าต่างหลัก แล้วบังคับ ฆ่า Streamlit ทั้ง tree + os._exit(0) ปิด process
    ทันที ไม่รอ pywebview"""
    _dbg("main window closed — shutting down everything (kill streamlit tree + os._exit)")
    _kill_streamlit_tree(proc)
    if st_log is not None:
        try:
            st_log.close()
        except Exception:
            pass
    os._exit(0)


def main() -> None:
    port = _find_free_port()
    base_url = f"http://127.0.0.1:{port}"

    print("============================================")
    print("  NPK RC SDM - Reinforced Concrete Design App")
    print("============================================")
    print("Starting the program, please wait...")
    _dbg(f"main() start — python={sys.executable} port={port}")

    # เรียก python ตัวเดียวกับที่รันสคริปต์นี้อยู่ (ใน .venv/embeddable ที่ bundle มากับ
    # โปรแกรม) รับประกันว่าใช้ streamlit ชุดเดียวกับที่ pip install ไว้ ไม่พึ่ง PATH เครื่อง
    popen_kwargs = {"cwd": str(APP_DIR)}
    if sys.platform == "win32":
        # ไม่สร้างหน้าต่าง console ให้ subprocess ของ streamlit (สำคัญเมื่อรันด้วย
        # pythonw.exe ที่ไม่มี console — กันหน้าต่างดำเด้งขึ้นมาต่างหาก)
        popen_kwargs["creationflags"] = _CREATE_NO_WINDOW

    # เก็บ stdout/stderr ของ Streamlit ลงไฟล์ (แทนที่จะหายไปกับ pythonw ที่ไม่มี console) —
    # ถ้า Streamlit เปิดไม่ขึ้น จะได้เห็นสาเหตุจริงใน streamlit_log.txt
    st_log = None
    try:
        st_log = open(APP_DIR / "streamlit_log.txt", "w", encoding="utf-8", errors="replace")
        popen_kwargs["stdout"] = st_log
        popen_kwargs["stderr"] = subprocess.STDOUT
    except Exception as exc:  # noqa: BLE001
        _dbg(f"cannot open streamlit_log.txt: {exc}")

    _dbg("launching streamlit subprocess...")
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run", str(APP_FILE),
            "--server.port", str(port),
            "--server.headless", "true",
            "--server.address", "127.0.0.1",
            "--browser.gatherUsageStats", "false",
        ],
        **popen_kwargs,
    )
    _dbg(f"streamlit subprocess pid={proc.pid} — waiting for server...")

    try:
        if not _wait_for_server(f"{base_url}/_stcore/health"):
            print("ERROR: Streamlit server did not start within 40 seconds.")
            print("Please close this window and try running again.")
            _dbg("ERROR: streamlit server did not become healthy within 40s "
                 "(ดู streamlit_log.txt สำหรับสาเหตุ)")
            return

        print("Ready. Opening program window...")
        _dbg("server healthy — creating main window")
        api = _Api()
        window = webview.create_window(
            "NPK RC SDM",
            base_url,
            width=1400,
            height=900,
            min_size=(1000, 700),
            maximized=True,   # เปิดโปรแกรมแบบเต็มจอ (ขยายเต็มหน้าจอ) ตั้งแต่ครั้งแรก
            js_api=api,
        )
        api.bind_window(window)

        # ดักอีเวนต์ "ปิดหน้าต่างหลัก" = ผู้ใช้สั่งปิดโปรแกรม → บังคับปิดทุกอย่างสนิททันที
        # (ฆ่า Streamlit ทั้ง tree + os._exit) — จำเป็นเพราะหน้าต่าง Preview ถูก hide() ค้างไว้
        # ทำให้ webview.start() ไม่คืนค่าเอง (ยังเห็นหน้าต่างซ่อนอยู่) → ถ้าไม่ดักตรงนี้ โปรแกรมปิดไม่ลง
        window.events.closed += lambda *a: _shutdown_and_exit(proc, st_log)

        # หมายเหตุ 2026-07-12: **ไม่สร้างหน้าต่าง Preview ล่วงหน้าตรงนี้ก่อน webview.start()**
        # เพราะการสร้างหน้าต่างที่สองก่อน start() ทำให้โปรแกรมเปิดไม่ขึ้นเลยบนเครื่องผู้ใช้
        # หน้าต่าง Preview ถูกสร้างแบบไดนามิกครั้งแรกที่ผู้ใช้กดปุ่ม "แสดงรายการคำนวณ" แทน
        # (ดู _Api.open_preview) แล้วใช้หน้าต่างเดิมซ้ำตลอด ไม่มีการ destroy อีกเลย
        _dbg("main window created — calling webview.start()")
        # ตั้งไอคอนหน้าต่าง/ทาสก์บาร์เป็นไอคอนโปรแกรม (data/app_icon.ico) — ถ้า pywebview เวอร์ชันนี้
        # รองรับพารามิเตอร์ icon; ถ้าไม่รองรับ (TypeError) หรือไม่มีไฟล์ ก็เริ่มแบบปกติ ไม่ให้พัง
        _icon = APP_DIR / "data" / "app_icon.ico"
        try:
            if _icon.exists():
                webview.start(icon=str(_icon))
            else:
                webview.start()
        except TypeError:
            webview.start()
        _dbg("webview.start() returned (program closed normally)")
    finally:
        # เผื่อกรณี webview.start() คืนค่าเอง (ไม่เคยเปิด Preview) — ปิด Streamlit ทั้ง tree + close log
        _kill_streamlit_tree(proc)
        if st_log is not None:
            try:
                st_log.close()
            except Exception:
                pass

    # ปิดโปรแกรมตามปกติแล้ว — บังคับให้ pythonw ตัวเองปิดสนิทด้วย os._exit(0) กัน thread เบื้องหลัง
    # ของ pywebview/WebView2/tornado ที่บางครั้งค้าง ทำให้ pythonw ไม่ตายจริงแล้วไปถือ run_log.txt
    # ล็อกไว้ = run_app.bat รอบต่อไปเปิด Python ไม่ได้ (ต้นเหตุ "เปิดได้ครั้งเดียว")
    _dbg("program closed — forcing full process exit (os._exit 0)")
    os._exit(0)


if __name__ == "__main__":
    # ดักจับ error ทุกอย่างตอนเปิดโปรแกรม เขียน traceback เต็มลง crash_log.txt — สำคัญมากเมื่อรัน
    # ด้วย pythonw.exe (ไม่มี console) เพราะ traceback ปกติจะหายไป มองไม่เห็นว่าพังเพราะอะไร
    try:
        _dbg("=== desktop_app.py __main__ started ===")
        main()
    except Exception:
        import traceback
        tb = traceback.format_exc()
        _dbg("FATAL EXCEPTION:\n" + tb)
        try:
            (APP_DIR / "crash_log.txt").write_text(tb, encoding="utf-8", errors="replace")
        except Exception:
            pass
        raise
