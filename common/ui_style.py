"""
NPK RC SDM — Typography & Color System (Redesigned 2026-07-11)

Professional engineering software typography and colors.
Optimized for readability during long engineering work sessions.
Complies with WCAG AA contrast requirements.

DESIGN PRINCIPLES:
- High contrast for readability
- Clear visual hierarchy
- Professional engineering software appearance (ETABS, SAP2000, Robot)
- Consistent typography scales and color palette
- No faded/washed-out text for important information
"""

from contextlib import contextmanager

import streamlit as st

# ===========================================================================
# COLOR PALETTE — Engineering Software Professional
# ===========================================================================
COLORS = {
    # Semantic colors — ปรับให้เข้มขึ้นเพื่อความชัด (การแจ้งเตือน/สถานะ ต้องเด่น)
    "primary_blue": "#2563EB",
    "info_blue": "#1D4ED8",       # สีข้อมูล/คำแนะนำ (อ่านชัด)
    "success_green": "#15803D",   # เขียวเข้มขึ้น (เดิม #16A34A)
    "warning_orange": "#C2410C",  # ส้มเข้มขึ้น (เดิม #EA580C)
    "danger_red": "#B91C1C",      # แดงเข้มขึ้น (เดิม #DC2626)

    # Text colors — ระบบใหม่ เน้นคอนทราสต์สูง อ่านออกชัด ไม่มีสีจาง
    "heading": "#0F172A",         # เข้มสุด (slate-900) สำหรับหัวข้อหลัก
    "card_title": "#1E293B",      # หัวการ์ด (slate-800)
    "field_label": "#334155",     # ป้ายกำกับช่องกรอก (slate-700) เข้ม/หนา อ่านง่าย
    "secondary_text": "#475569",  # ข้อความรอง (slate-600) — อ่านชัด ไม่จางเหมือนเดิม
    "unit_text": "#475569",       # หน่วย — เดิมจางมาก (#94A3B8) เปลี่ยนให้อ่านชัด
    "help_icon": "#64748B",

    # Backgrounds & Borders
    "border": "#CBD5E1",
    "background": "#FFFFFF",
    "input_background": "#F8FAFC",
    "placeholder": "#94A3B8",

    # Highlights
    "user_input_bg": "#FFF59D",
    "calculated_result_bg": "#FFCDD2",
    "calculated_result_text": "#C62828",
}

# Typography scales — ขยายขึ้น ~32% จากเดิม (ผู้ใช้แจ้งว่าเดิมเล็กเกินไปเมื่อใช้งานจริง)
TYPOGRAPHY = {
    "main_title": {"size": 40, "weight": 800, "color": COLORS["heading"]},
    "card_title": {"size": 24, "weight": 700, "color": COLORS["card_title"]},
    "section_title": {"size": 21, "weight": 700, "color": COLORS["card_title"]},
    "field_label": {"size": 18, "weight": 600, "color": COLORS["field_label"]},
    "input_value": {"size": 20, "weight": 600, "color": COLORS["heading"]},
    "unit": {"size": 18, "weight": 600, "color": COLORS["unit_text"]},
    "secondary": {"size": 17, "weight": 500, "color": COLORS["secondary_text"]},
}

CARD_ACCENTS = {
    "blue": "#2563EB",
    "orange": "#EA580C",
    "green": "#16A34A",
    "teal": "#0D9488",
    "red": "#DC2626",
    "purple": "#7C3AED",
    "navy": "#1E3853",
}


def inject_card_css() -> None:
    """แทรก CSS สำหรับการ์ดกรอบสี (input_card) และการ์ดผลลัพธ์ (metric_card_row) —
    เรียกครั้งเดียวต่อหน้า (page-scoped)

    REDESIGN 2026-07-11:
    - Typography scales + color system ตาม engineering software standards
    - High contrast for readability
    - WCAG AA compliance
    - Information density + professional appearance"""
    accent_rules = "".join(
        f'[class*="st-key-npk-ic-{name}-"] {{ border-top: 3px solid {color} !important; }}\n'
        for name, color in CARD_ACCENTS.items()
    )
    st.markdown(f"""
<style>
/* ==================================================
   ENGINEERING SOFTWARE TYPOGRAPHY & COLORS
   Designed for readability during long work sessions
   WCAG AA compliant
================================================== */

/* ===== MAIN LAYOUT ===== */
.block-container {{
    padding-top: 0.8rem !important;
    padding-bottom: 0.8rem !important;
    max-width: 100% !important;
}}

/* ===== HEADING TYPOGRAPHY ===== ขยาย ~32% */
h1 {{
    font-size: 40px !important;
    font-weight: 800 !important;
    color: {COLORS['heading']} !important;
    margin: 1rem 0 0.8rem 0 !important;
}}
h2 {{
    font-size: 24px !important;
    font-weight: 700 !important;
    color: {COLORS['card_title']} !important;
    margin: 0.8rem 0 0.6rem 0 !important;
}}
h3 {{
    font-size: 21px !important;
    font-weight: 700 !important;
    color: {COLORS['card_title']} !important;
    margin: 0.6rem 0 0.4rem 0 !important;
}}

/* ===== FIELD LABELS — High contrast, always readable ===== */
label {{
    font-size: 18px !important;
    font-weight: 600 !important;
    color: {COLORS['field_label']} !important;
    margin-bottom: 5px !important;
}}

/* ===== ELEMENT SPACING ===== */
[data-testid="stVerticalBlock"] {{ gap: 0.4rem !important; }}
[data-testid="stHorizontalBlock"] {{ gap: 0.4rem !important; }}

/* ===== INPUT CARD ===== */
[class*="st-key-npk-ic-"] {{
    border-radius: 10px !important;
    border: 1px solid {COLORS['border']} !important;
    background: {COLORS['background']} !important;
    box-shadow: 0 1px 3px rgba(20,30,40,0.08) !important;
    padding: 12px 14px 10px 14px !important;
}}
{accent_rules}

.npk-ic-header {{
    display: flex;
    align-items: center;
    gap: 6px;
    margin: 0 0 4px 0 !important;
}}
.npk-ic-header .ic {{ font-size: 1.2rem; }}
.npk-ic-header .tt {{
    font-weight: 700;
    color: {COLORS['card_title']};
    font-size: 21px;
    margin: 0 !important;
}}

/* ===== INPUT BOXES ===== */
[data-testid="stNumberInput"] input,
[data-testid="stTextInput"] input {{
    font-size: 20px !important;
    font-weight: 600 !important;
    color: {COLORS['heading']} !important;
    background-color: {COLORS['input_background']} !important;
    border-color: {COLORS['border']} !important;
}}
[data-testid="stNumberInput"] input:focus,
[data-testid="stTextInput"] input:focus {{
    border-color: {COLORS['primary_blue']} !important;
    box-shadow: 0 0 0 2px {COLORS['primary_blue']}33 !important;
}}

/* ===== SELECTBOX ===== */
[data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    font-size: 20px !important;
    font-weight: 600 !important;
    color: {COLORS['heading']} !important;
    background-color: {COLORS['input_background']} !important;
    border-color: {COLORS['border']} !important;
}}

/* ===== METRIC CARDS (Results) ===== */
[class*="st-key-npk-mc-"] {{
    border-radius: 10px !important;
    border: 1px solid {COLORS['border']} !important;
    background: {COLORS['background']} !important;
    box-shadow: 0 1px 3px rgba(20,30,40,0.08) !important;
    padding: 10px 12px !important;
    text-align: center;
}}

/* หัวข้อการ์ด (ชื่อเต็ม) — ตัวหนาชัด บรรทัดบน (ขยาย ~32%) */
.npk-mc-label {{
    font-size: 19px !important;
    font-weight: 700 !important;
    color: {COLORS['card_title']} !important;
    margin-bottom: 2px !important;
    line-height: 1.2;
}}
/* บรรทัดสัญลักษณ์ (เช่น Wu, h req., As) — เล็กกว่า อยู่ใต้ชื่อเต็ม (ตาม mockup) */
.npk-mc-sym {{
    font-size: 16px !important;
    font-weight: 600 !important;
    color: {COLORS['secondary_text']} !important;
    margin-bottom: 5px !important;
    line-height: 1.1;
}}
/* ค่าตัวเลข — สีน้ำเงินเด่น ตัวใหญ่ (จุดเด่นหลักตาม mockup) */
.npk-mc-value {{
    font-size: 30px !important;
    font-weight: 800 !important;
    color: #1D4ED8 !important;
    line-height: 1.15;
    margin: 0 !important;
}}
/* หน่วย — สีน้ำเงินอ่อนกว่าค่า */
.npk-mc-note {{
    font-size: 17px !important;
    font-weight: 500 !important;
    color: #1D4ED8 !important;
    margin: 2px 0 5px 0 !important;
}}
/* ป้ายสถานะ OK / ตรวจสอบ / ไม่ผ่าน — เป็นข้อมูลสำคัญที่สุด (ผ่าน/ไม่ผ่านการออกแบบ) ต้องเด่นชัด
   ขนาดใหญ่ อ่านง่ายจากระยะไกล (ผู้ใช้ย้ำว่าเดิมเล็กเกินไป) — ตัวใหญ่ หนา มีกรอบสี พื้นสีเข้มชัด */
.npk-mc-badge {{
    display: inline-block;
    font-size: 17px !important;
    font-weight: 800 !important;
    border-radius: 7px;
    padding: 7px 18px;
    margin-top: 7px;
    letter-spacing: .3px;
    border: 2px solid transparent;
    box-shadow: 0 1px 2px rgba(15,23,42,.10);
}}
.npk-mc-badge.ok {{ background: #DCFCE7; color: #15803D; border-color: #4ADE80; }}
.npk-mc-badge.bad {{ background: #FEE2E2; color: #B91C1C; border-color: #F87171; }}
.npk-mc-badge.warn {{ background: #FEF3C7; color: #B45309; border-color: #FBBF24; }}

/* ===== BUTTONS ===== */
[class*="st-key-npk-btn-compute"] button {{
    min-height: 46px !important;
    height: 46px !important;
    padding: 8px 20px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    background-color: {COLORS['primary_blue']} !important;
    border-color: {COLORS['primary_blue']} !important;
    color: #FFFFFF !important;
}}
[class*="st-key-npk-btn-save"] button {{
    min-height: 46px !important;
    height: 46px !important;
    padding: 8px 20px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    background-color: {COLORS['success_green']} !important;
    border-color: {COLORS['success_green']} !important;
    color: #FFFFFF !important;
}}
[class*="st-key-npk-btn-report"] button {{
    min-height: 46px !important;
    height: 46px !important;
    padding: 8px 20px !important;
    font-size: 18px !important;
    font-weight: 700 !important;
    background-color: {COLORS['primary_blue']} !important;
    border-color: {COLORS['primary_blue']} !important;
    color: #FFFFFF !important;
}}

/* ===== HELP ICON (ⓘ) ===== */
.help-icon {{
    color: {COLORS['help_icon']};
    cursor: pointer;
    transition: color 0.15s;
}}
.help-icon:hover {{
    color: {COLORS['primary_blue']};
}}

/* ===== ELEMENT SPACING ===== */
[data-testid="stElementContainer"] {{
    margin-bottom: 0.4rem !important;
}}

/* ===== ตัวหนังสือสีจาง (เทาเกือบขาว) -> สีน้ำเงินอ่านชัด (ตามคำขอผู้ใช้ ทั้งโปรแกรม) =====
   ผู้ใช้ไม่ชอบข้อความสีเทาจางในส่วนที่ควรอ่านชัด — เปลี่ยนเป็นสีน้ำเงินเข้มทั้งหมด ครอบคลุม:
   st.caption, หมายเหตุใต้การ์ดผลลัพธ์ (.npk-mc-note), หน่วย/label ในการ์ด ETABS
   (.etabs-unit/.etabs-lbl), ข้อความรอง (.npk-mc-note), help text ของ widget, และตาราง st.table */
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
[data-testid="stCaptionContainer"] span,
.npk-mc-note,
[data-testid="stTable"] th,
[data-testid="stTable"] td,
small, .stCaption {{
    color: #1D4ED8 !important;
}}
/* ขยายขนาดตาราง st.table และ caption ให้อ่านง่ายขึ้น */
[data-testid="stTable"] th,
[data-testid="stTable"] td {{
    font-size: 17px !important;
}}
[data-testid="stCaptionContainer"],
[data-testid="stCaptionContainer"] p,
small, .stCaption {{
    font-size: 16px !important;
}}

/* ช่องกรอกที่ปิดใช้งาน (disabled) เช่น "กรณีที่เลือก" — เดิมแสดงสีเทาจาง ทั้งที่เป็นค่าที่ควรอ่านชัด
   บังคับเป็นสีน้ำเงินเต็มความเข้ม ต้อง override ทั้ง color + -webkit-text-fill-color + opacity
   เพราะ Chromium/WebView2 ทำให้ข้อความ disabled จางผ่าน -webkit-text-fill-color และ opacity */
[data-testid="stTextInput"] input:disabled,
[data-testid="stNumberInput"] input:disabled,
[data-testid="stTextArea"] textarea:disabled,
[data-testid="stTextInput"] input[disabled],
[data-testid="stNumberInput"] input[disabled],
input:disabled, textarea:disabled {{
    color: #1D4ED8 !important;
    -webkit-text-fill-color: #1D4ED8 !important;
    opacity: 1 !important;
    font-weight: 600 !important;
}}
/* selectbox / ตัวเลือกที่ปิดใช้งาน */
[data-testid="stSelectbox"] [aria-disabled="true"],
[data-testid="stSelectbox"] [aria-disabled="true"] div,
[data-baseweb="select"][disabled] * {{
    color: #1D4ED8 !important;
    -webkit-text-fill-color: #1D4ED8 !important;
    opacity: 1 !important;
}}
</style>
""", unsafe_allow_html=True)

    # ===== ETABS-STYLE OVERLAY (2026-07-12) — ทำให้ input_card ทุกใบเป็นสไตล์ ETABS =====
    etabs_header_bg = "".join(
        f'[class*="st-key-npk-ic-{name}-"] .npk-ic-header {{ background:{c}; }}\n'
        for name, c in _ETABS_HEADER_COLORS.items()
    )
    st.markdown(f"""
<style>
/* กรอบการ์ด: เอา padding ออก, หัวการ์ดเป็นแถบสีเต็ม, สูงเท่ากันทุกใบ (สมมาตร) */
[class*="st-key-npk-ic-"] {{
    border:1px solid #D8DEE7 !important; border-top:1px solid #D8DEE7 !important;
    border-radius:7px !important; padding:0 !important; overflow:hidden;
    box-shadow:0 1px 2px rgba(15,23,42,.05); height:100%;
}}
[class*="st-key-npk-ic-"] .npk-ic-header {{
    color:#fff !important; font-size:17px !important; font-weight:700 !important;
    padding:12px 16px !important; margin:0 !important; border:none !important;
    display:flex; align-items:center; gap:7px; letter-spacing:.2px;
}}
[class*="st-key-npk-ic-"] .npk-ic-header .tt {{ color:#fff !important; font-size:17px !important; font-weight:700 !important; }}
[class*="st-key-npk-ic-"] .npk-ic-header .ic {{ font-size:1.2rem; }}
{etabs_header_bg}
/* หัวข้อกลุ่มย่อย: st.markdown("**...**") ที่มีแต่ตัวหนา → แถบเทา */
[class*="st-key-npk-ic-"] [data-testid="stMarkdownContainer"]:has(> p > strong:only-child) {{
    background:#F1F5F9; border-top:1px solid #E9EDF2; border-bottom:1px solid #E9EDF2;
    padding:7px 16px !important; margin:0 !important;
}}
[class*="st-key-npk-ic-"] [data-testid="stMarkdownContainer"]:has(> p > strong:only-child) p {{ margin:0 !important; }}
[class*="st-key-npk-ic-"] [data-testid="stMarkdownContainer"]:has(> p > strong:only-child) strong {{
    font-size:15px !important; font-weight:700 !important; color:#334155 !important;
}}

/* การ์ด 3 ใบในแถวคอลัมน์ สูงเท่ากัน */
[data-testid="stColumn"]:has([class*="st-key-npk-ic-"]) > div {{ height:100%; }}
[data-testid="stColumn"]:has([class*="st-key-npk-ic-"]) [data-testid="stElementContainer"]:has(> [class*="st-key-npk-ic-"]) {{ height:100%; }}
</style>
""", unsafe_allow_html=True)

    # ===== RESPONSIVE (ส่วนกลาง) =====
    # เดิมใช้ media query ย่อฟอนต์รายจุด (reflow) เมื่อจอแคบ — ถอดออกแล้ว (2026-07-14)
    # เพราะเปลี่ยนมาใช้ zoom-to-fit (render_zoom_to_fit ด้านล่าง) ที่ย่อทั้งบล็อกลงพอดีจอ
    # อย่างสม่ำเสมอ  ถ้ายังคง media query ย่อฟอนต์ไว้จะย่อซ้ำซ้อนกับ zoom (double-shrink)

    # ปุ่มลอย "กลับสู่ด้านบน" มุมขวาล่าง (ทุกหน้าที่เรียก inject_card_css จะได้อัตโนมัติ)
    render_back_to_top()

    # ย่อทั้งหน้าให้พอดีจอเมื่อจอแคบ (แก้ป้ายกำกับไทยขึ้นบรรทัดทีละตัวอักษร) — ทุกหน้าที่
    # เรียก inject_card_css จะได้อัตโนมัติ
    render_zoom_to_fit()


# JavaScript ที่ inject ปุ่มลอย "กลับสู่ด้านบน" เข้า document แม่ (ผ่าน components.html iframe
# ที่เข้าถึง window.parent) — ต้องสร้าง element ในหน้าแม่โดยตรง เพราะปุ่มที่อยู่ใน iframe เอง
# จะ position:fixed เทียบกับ iframe (ที่สูง 0) ไม่ใช่ทั้งหน้าจอ
_BACK_TO_TOP_JS = r"""
<script>
(function () {
  try {
    var doc = window.parent && window.parent.document;
    if (!doc) return;

    // สไตล์ hover ใส่ไว้ในหน้าแม่ (CSS — คงอยู่แม้ iframe ถูกทำลายตอน rerun)
    if (!doc.getElementById('npk-back-to-top-style')) {
      var stEl = doc.createElement('style');
      stEl.id = 'npk-back-to-top-style';
      stEl.textContent = '#npk-back-to-top:hover{filter:brightness(1.12);}';
      (doc.head || doc.documentElement).appendChild(stEl);
    }

    if (doc.getElementById('npk-back-to-top')) return;   // กันสร้างซ้ำ

    var btn = doc.createElement('button');
    btn.id = 'npk-back-to-top';
    btn.type = 'button';
    btn.title = 'กลับสู่ด้านบน';
    btn.setAttribute('aria-label', 'กลับสู่ด้านบน');
    // ปุ่มทรงแคปซูล (pill) มีตัวหนังสือ "กลับสู่ด้านบน" กำกับข้างลูกศรเสมอ (ไม่ใช่แค่ tooltip
    // ตอน hover เหมือนเดิม) — ผู้ใช้ขอให้เห็นข้อความบอกด้านข้างชัดเจน 2026-07-13
    btn.innerHTML =
      '<span style="font-size:18px; line-height:1;">⬆</span>' +
      '<span style="font-size:15px; font-weight:700; white-space:nowrap;">กลับสู่ด้านบน</span>';
    btn.setAttribute('style',
      'position:fixed; right:22px; bottom:22px; z-index:2147483000;' +
      'display:flex; align-items:center; gap:8px;' +
      'height:48px; padding:0 20px 0 16px; border-radius:999px; border:none; cursor:pointer;' +
      'background:#0D9488; color:#ffffff; font-family:inherit;' +
      'box-shadow:0 3px 12px rgba(0,0,0,.30);');

    // สำคัญ: ตั้ง onclick เป็น attribute (string) เพื่อให้รันในบริบทของ "หน้าแม่" โดยตรง
    // ไม่ผูกกับสคริปต์ใน iframe ตัวนี้ (ซึ่งจะถูกทำลายทุกครั้งที่ Streamlit rerun ทำให้ปุ่ม
    // ยังอยู่แต่กดแล้วไม่ทำงาน) — และหา element ที่กำลัง scroll อยู่จริงเองโดยไม่เดา selector
    // (Streamlit เปลี่ยนโครงสร้าง/ชื่อ container ตามเวอร์ชัน) แล้วเลื่อนกลับบนสุด
    btn.setAttribute('onclick',
      "try{window.scrollTo({top:0,behavior:'smooth'});}catch(e){}" +
      "try{(document.scrollingElement||document.documentElement).scrollTo({top:0,behavior:'smooth'});}catch(e){}" +
      "var a=document.querySelectorAll('*');" +
      "for(var i=0;i<a.length;i++){var el=a[i];" +
      "if(el.scrollTop&&el.scrollTop>0){try{el.scrollTo({top:0,behavior:'smooth'});}catch(x){try{el.scrollTop=0;}catch(y){}}}}");

    doc.body.appendChild(btn);
  } catch (e) {}
})();
</script>
"""


def render_back_to_top() -> None:
    """แสดงปุ่มลอย "กลับสู่ด้านบน" ที่มุมขวาล่างของหน้าจอ (คงอยู่ตลอด) — กดแล้วเลื่อน
    หน้าจอกลับขึ้นบนสุดแบบ smooth เรียกซ้ำได้ปลอดภัย (มีการ์ดกันสร้างปุ่มซ้ำ)"""
    import streamlit.components.v1 as components
    components.html(_BACK_TO_TOP_JS, height=0)


# ===========================================================================
# ZOOM-TO-FIT (2026-07-14) — แก้ปัญหา "เมื่อย่อขนาดจอแล้วป้ายกำกับภาษาไทยถูกตัด
# เป็นตัวอักษรต่อบรรทัด (ข้อความแนวตั้ง)" ในทุกหน้า/ทุกโมดูล
# ---------------------------------------------------------------------------
# วิธีการ: ล็อกความกว้างเนื้อหาไว้ที่ "ความกว้างออกแบบ" (DESIGN) คงที่ แล้วใช้ CSS zoom
# ย่อทั้งบล็อกลงตามอัตราส่วน (viewport / DESIGN) เมื่อจอแคบกว่าความกว้างออกแบบ —
# ผลคือเลย์เอาต์ไม่เปลี่ยน (คอลัมน์/ป้ายไม่ถูกบีบจนขึ้นบรรทัดใหม่ทีละตัวอักษร) แค่ย่อ
# ทั้งภาพลงมาพอดีจอ  ส่วนจอกว้าง (>= DESIGN) ไม่ย่อ (zoom=1) คงหน้าตาเดิมทุกอย่าง
#
# ทำผ่าน components.html iframe ที่เข้าถึง window.parent.document แล้วตั้ง inline style
# ให้ [data-testid="stMainBlockContainer"] โดยตรง — พร้อม resize listener + MutationObserver
# ที่ผูกไว้กับหน้าแม่ (คงอยู่แม้ iframe ถูกทำลายตอน Streamlit rerun) เพื่อคำนวณ/ตั้งค่า zoom
# ใหม่ทุกครั้งที่ปรับขนาดจอหรือหน้าถูก rerun (ซึ่งจะสร้าง container ใหม่ที่ไม่มี inline style)
#
# หมายเหตุ: media query แบบย่อฟอนต์ (reflow) ถูกถอดออกแล้ว เพราะ zoom จัดการย่อทั้งภาพ
# แบบสม่ำเสมออยู่แล้ว — ถ้าปล่อยไว้จะย่อซ้ำซ้อน (double-shrink)
_ZOOM_DESIGN_WIDTH = 1450   # ความกว้างออกแบบ (px): จอกว้างกว่านี้ไม่ย่อ
_ZOOM_MIN = 0.45            # ย่อได้ต่ำสุด (กันจอแคบมากจนเล็กเกินอ่าน — ยอมให้มี scroll แนวนอนแทน)

_ZOOM_TO_FIT_JS = ("""
<script>
(function () {
  try {
    var win = window.parent, doc = win && win.document;
    if (!doc) return;
    var DESIGN = __DESIGN__, MINZOOM = __MINZOOM__;

    // ฟังก์ชันคำนวณ+ตั้งค่า zoom (เก็บไว้บนหน้าแม่ ให้ listener เรียกตัวล่าสุดเสมอ)
    win.__npkZoomApply = function () {
      try {
        var c = doc.querySelector('[data-testid=\"stMainBlockContainer\"]')
              || doc.querySelector('.block-container');
        if (!c) return;
        // ใช้ clientWidth (ไม่รวมแถบเลื่อนแนวตั้ง) กันเกิด scroll แนวนอน
        var vw = doc.documentElement.clientWidth || win.innerWidth || DESIGN;
        if (vw >= DESIGN) {
          c.style.width = ''; c.style.maxWidth = ''; c.style.zoom = ''; c.style.boxSizing = '';
        } else {
          var z = Math.max(MINZOOM, vw / DESIGN);
          // border-box: ให้ความกว้าง 1450 รวม padding แล้ว → กว้างจริงหลัง zoom = 1450*z = vw พอดี
          // (กัน scroll แนวนอนจาก padding เกินขอบ)
          c.style.boxSizing = 'border-box';
          c.style.width = DESIGN + 'px';
          c.style.maxWidth = DESIGN + 'px';
          c.style.zoom = z;
        }
      } catch (e) {}
    };

    // ผูก listener/observer ครั้งเดียว (คงอยู่ข้าม rerun เพราะอยู่บนหน้าแม่)
    if (!win.__npkZoomInit) {
      win.__npkZoomInit = true;
      var pending = false;
      win.__npkZoomSchedule = function () {
        if (pending) return; pending = true;
        var run = function () { pending = false; if (win.__npkZoomApply) win.__npkZoomApply(); };
        if (win.requestAnimationFrame) win.requestAnimationFrame(run); else win.setTimeout(run, 16);
      };
      win.addEventListener('resize', function () { win.__npkZoomSchedule(); });
      try {
        var MO = win.MutationObserver || win.WebKitMutationObserver;
        if (MO) {
          // เฝ้าเฉพาะ childList (Streamlit rerun สร้าง container ใหม่) — ไม่เฝ้า attributes
          // จึงไม่วนซ้ำจากการที่เราตั้ง style.zoom เอง
          new MO(function () { win.__npkZoomSchedule(); }).observe(doc.body, {childList:true, subtree:true});
        }
      } catch (e) {}
    }

    // apply ทันที + ซ้ำอีกเล็กน้อยหลัง render เสร็จ (กัน container ยังไม่ถูกสร้างตอนแรก)
    win.__npkZoomApply();
    win.setTimeout(win.__npkZoomApply, 80);
    win.setTimeout(win.__npkZoomApply, 350);
  } catch (e) {}
})();
</script>
""".replace("__DESIGN__", str(_ZOOM_DESIGN_WIDTH)).replace("__MINZOOM__", str(_ZOOM_MIN)))


def render_zoom_to_fit() -> None:
    """แทรกสคริปต์ zoom-to-fit เข้าหน้าแม่ — ย่อทั้งบล็อกเนื้อหาให้พอดีจอเมื่อจอแคบกว่า
    ความกว้างออกแบบ แทนการปล่อยให้ป้ายกำกับภาษาไทยถูกบีบจนขึ้นบรรทัดใหม่ทีละตัวอักษร
    เรียกซ้ำได้ปลอดภัย (ผูก listener ครั้งเดียว)"""
    import streamlit.components.v1 as components
    components.html(_ZOOM_TO_FIT_JS, height=0)


# ===========================================================================
# ETABS / SAP2000-STYLE INPUT FORM (Redesign 2026-07-12)
# การ์ดกรอกข้อมูลสไตล์ซอฟต์แวร์วิศวกรรม: การ์ด 3 คอลัมน์สูงเท่ากัน (สมมาตร),
# หัวข้อกลุ่มย่อยแถบเทา, แต่ละแถว = label ซ้าย / ช่องกรอกชิดขวา / หน่วยต่อท้าย
# ===========================================================================
_ETABS_HEADER_COLORS = {
    "blue": "#2563EB", "orange": "#EA580C", "green": "#16A34A",
    "teal": "#0D9488", "navy": "#1E3A5F", "purple": "#7C3AED", "red": "#DC2626",
}


def inject_etabs_css() -> None:
    """แทรก CSS สำหรับฟอร์มกรอกข้อมูลสไตล์ ETABS — เรียกครั้งเดียวต่อหน้า"""
    header_rules = "".join(
        f'.etabs-chead.etabs-{name} {{ background:{c}; }}\n'
        for name, c in _ETABS_HEADER_COLORS.items()
    )
    st.markdown(f"""
<style>
/* ===== การ์ด ===== */
[class*="st-key-etabscard-"] {{
    border:1px solid #D8DEE7 !important; border-radius:7px !important;
    padding:0 !important; overflow:hidden; background:#FFFFFF !important;
    box-shadow:0 1px 2px rgba(15,23,42,.05); height:100%;
}}
[data-testid="stColumn"]:has([class*="st-key-etabscard-"]) {{ align-self:stretch; }}
[data-testid="stColumn"]:has([class*="st-key-etabscard-"]) > div {{ height:100%; }}
[class*="st-key-etabscard-"] > div {{ gap:0 !important; }}
[class*="st-key-etabscard-"] [data-testid="stVerticalBlock"] {{ gap:0 !important; }}
[class*="st-key-etabscard-"] [data-testid="stElementContainer"] {{ margin:0 !important; }}

/* ===== หัวการ์ด (แถบสี) ===== ขยาย ~32% */
.etabs-chead {{
    color:#fff; font-size:17px; font-weight:700; padding:12px 16px;
    display:flex; align-items:center; gap:7px; letter-spacing:.2px;
}}
{header_rules}
/* ===== หัวข้อกลุ่มย่อย (แถบเทา) ===== */
.etabs-grp {{
    background:#F1F5F9; color:#334155; font-size:15px; font-weight:700;
    padding:7px 16px; border-top:1px solid #E9EDF2; border-bottom:1px solid #E9EDF2;
    letter-spacing:.2px;
}}

/* ===== แถวฟิลด์ (label ซ้าย / input / unit) ===== ปรับระยะห่าง + ขยายตัวอักษร ~32% */
[class*="st-key-etabscard-"] [data-testid="stHorizontalBlock"] {{
    gap:18px !important; align-items:center !important;
    padding:11px 18px !important; margin:0 !important;
    border-bottom:1px solid #EEF1F5 !important;
}}
.etabs-lbl {{ font-size:16.5px; color:#334155; font-weight:500; white-space:normal; overflow-wrap:break-word; line-height:1.3; }}
.etabs-unit {{ font-size:15px; color:#475569; white-space:nowrap; line-height:38px; }}

/* ===== ช่องกรอกตัวเลข: ชิดขวา, ซ่อนปุ่ม +/- ===== */
[class*="st-key-etabscard-"] [data-testid="stNumberInputStepDown"],
[class*="st-key-etabscard-"] [data-testid="stNumberInputStepUp"] {{ display:none !important; }}
[class*="st-key-etabscard-"] [data-testid="stNumberInput"] input {{
    height:38px !important; min-height:38px !important; padding:3px 12px !important;
    text-align:right !important; font-size:18px !important; font-weight:600 !important;
    background:#F8FAFC !important; border-color:#D8DEE7 !important; color:#0F172A !important;
    font-variant-numeric:tabular-nums;
}}
/* ===== selectbox ===== */
[class*="st-key-etabscard-"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    min-height:38px !important; height:38px !important; padding:2px 11px !important;
    font-size:17px !important; font-weight:600 !important;
    background:#FFFFFF !important; border-color:#D8DEE7 !important; color:#0F172A !important;
}}
/* ===== text input (เช่น รหัส) ===== */
[class*="st-key-etabscard-"] [data-testid="stTextInput"] input {{
    height:38px !important; min-height:38px !important; padding:3px 12px !important;
    text-align:right !important; font-size:18px !important; font-weight:700 !important;
    background:#F8FAFC !important; border-color:#D8DEE7 !important;
}}

/* ===== เก็บกวาดระยะห่างส่วนเกิน ให้ทุกแถวสูงเท่ากัน ===== */
[class*="st-key-etabscard-"] [data-testid="stHorizontalBlock"] {{ min-height:56px; }}
/* ซ่อน label ของ widget (เราวาด label เองในคอลัมน์ซ้าย) — กันช่องว่างส่วนเกิน */
[class*="st-key-etabscard-"] [data-testid="stHorizontalBlock"] label {{ display:none !important; }}
/* ลบ margin ของ markdown / widget containers ภายในการ์ด */
[class*="st-key-etabscard-"] [data-testid="stMarkdown"],
[class*="st-key-etabscard-"] [data-testid="stMarkdownContainer"] p {{ margin:0 !important; }}
[class*="st-key-etabscard-"] [data-testid="stSelectbox"],
[class*="st-key-etabscard-"] [data-testid="stNumberInput"],
[class*="st-key-etabscard-"] [data-testid="stTextInput"] {{ margin:0 !important; }}
[class*="st-key-etabscard-"] [data-testid="stColumn"] > div {{ gap:0 !important; }}

/* ===== การ์ด 3 ใบสูงเท่ากัน (สมมาตร) ===== */
[data-testid="stColumn"]:has([class*="st-key-etabscard-"]) > div {{ height:100%; }}
[data-testid="stColumn"]:has([class*="st-key-etabscard-"]) [data-testid="stElementContainer"]:has(> [class*="st-key-etabscard-"]) {{ height:100%; }}
[data-testid="stColumn"]:has([class*="st-key-etabscard-"]) [data-testid="stVerticalBlock"]:has(> [data-testid="stElementContainer"] > [class*="st-key-etabscard-"]) {{ height:100%; }}
</style>
""", unsafe_allow_html=True)

    # ===== RESPONSIVE (การ์ด ETABS) =====
    # ถอด media query ย่อฟอนต์ออกแล้ว (2026-07-14) — ใช้ zoom-to-fit ส่วนกลางแทน
    # (ดูหมายเหตุใน inject_card_css) เพื่อไม่ให้ย่อซ้ำซ้อนกับ zoom


@contextmanager
def etabs_card(title: str, color: str = "blue", icon: str = "", key: str = ""):
    """การ์ดกรอกข้อมูลสไตล์ ETABS (แถบหัวสี + เนื้อในเป็นแถวฟิลด์กระชับ)
    ต้องเรียก inject_etabs_css() มาก่อนในหน้าเดียวกัน"""
    safe = "".join(c if c.isalnum() else "-" for c in (key or title))
    box_key = f"etabscard-{color}-{safe}"
    with st.container(border=True, key=box_key):
        icon_html = f"<span>{icon}</span> " if icon else ""
        st.markdown(f'<div class="etabs-chead etabs-{color}">{icon_html}{title}</div>',
                    unsafe_allow_html=True)
        yield


def etabs_group(label: str) -> None:
    """หัวข้อกลุ่มย่อย (แถบเทา) ภายใน etabs_card"""
    st.markdown(f'<div class="etabs-grp">{label}</div>', unsafe_allow_html=True)


def etabs_number(label: str, unit: str = "", ratio=(1.15, 1.0, 0.5), **kwargs):
    """แถวกรอกตัวเลข: label ซ้าย / number_input ชิดขวา / หน่วย — คืนค่าที่กรอก"""
    c = st.columns(list(ratio), vertical_alignment="center", gap="small")
    c[0].markdown(f'<div class="etabs-lbl">{label}</div>', unsafe_allow_html=True)
    with c[1]:
        val = st.number_input(label, label_visibility="collapsed", **kwargs)
    c[2].markdown(f'<div class="etabs-unit">{unit}</div>', unsafe_allow_html=True)
    return val


def etabs_select(label: str, ratio=(1.15, 1.5), **kwargs):
    """แถวเลือกตัวเลือก: label ซ้าย / selectbox ขวา — คืนค่าที่เลือก"""
    c = st.columns(list(ratio), vertical_alignment="center", gap="small")
    c[0].markdown(f'<div class="etabs-lbl">{label}</div>', unsafe_allow_html=True)
    with c[1]:
        val = st.selectbox(label, label_visibility="collapsed", **kwargs)
    return val


def etabs_text(label: str, unit: str = "", ratio=(1.15, 1.0, 0.5), **kwargs):
    """แถวกรอกข้อความ: label ซ้าย / text_input ขวา / หน่วย — คืนค่าที่กรอก"""
    c = st.columns(list(ratio), vertical_alignment="center", gap="small")
    c[0].markdown(f'<div class="etabs-lbl">{label}</div>', unsafe_allow_html=True)
    with c[1]:
        val = st.text_input(label, label_visibility="collapsed", **kwargs)
    c[2].markdown(f'<div class="etabs-unit">{unit}</div>', unsafe_allow_html=True)
    return val


@contextmanager
def input_card(title: str, color: str = "blue", icon: str = "", key: str = "", compact: bool = True):
    """Context manager ครอบกลุ่มช่องกรอกข้อมูลเป็นการ์ดกรอบสี (เส้นบนสีตามหมวด) —
    ใช้แทน st.container(border=True) ธรรมดา ต้องเรียก inject_card_css() มาก่อนแล้ว
    ในหน้าเดียวกัน (ที่ไหนก่อนหลังก็ได้) key ต้องไม่ซ้ำกันภายในหน้าเดียวกัน (ไม่ต้องใส่ก็ได้
    ถ้าใช้ title ที่ไม่ซ้ำกันอยู่แล้ว เพราะ default ใช้ title เป็น key)

    compact=True (ค่าเริ่มต้น) จะเรียก inject_compact_input_css() ให้อัตโนมัติ scoped
    เฉพาะการ์ดใบนี้ ทำให้ number_input/selectbox ภายในกระชับตามมาตรฐาน UI เดิมของโปรเจกต์
    โดยไม่ต้องเรียกแยกเองทุกครั้ง — ปิดได้ (compact=False) ถ้าการ์ดนั้นไม่มีช่องกรอกตัวเลข
    (เช่น การ์ดที่มีแต่ข้อความ/ปุ่ม)"""
    safe_key = "".join(c if c.isalnum() else "-" for c in (key or title))
    box_key = f"npk-ic-{color}-{safe_key}"
    icon_html = f'<span class="ic">{icon}</span>' if icon else ""
    if compact:
        inject_compact_input_css(box_key)
    with st.container(border=True, key=box_key):
        if title:
            st.markdown(
                f'<div class="npk-ic-header">{icon_html}'
                f'<span class="tt">{title}</span></div>',
                unsafe_allow_html=True,
            )
        yield


def metric_card_row(items: list) -> None:
    """วาดแถวการ์ดผลลัพธ์สรุป (metric cards) ตามดีไซน์ mockup ของผู้ใช้:
    หัวข้อ 2 บรรทัด (ชื่อเต็ม + สัญลักษณ์) / ตัวเลขค่าสีน้ำเงินเด่น / หน่วย / ป้ายสถานะ
    "OK + เหตุผล" (เช่น "OK หนาเพียงพอ", "OK ปลอดภัย")

    แต่ละ item รับได้ 2 รูปแบบ (backward compatible):
    - **dict (แนะนำ — ตรงตาม mockup)**: {"name": ชื่อเต็ม, "sym": สัญลักษณ์, "value": ค่า,
      "unit": หน่วย, "ok": True/False/"warn"/None, "reason": ข้อความเหตุผลสั้นๆ ต่อท้ายป้าย}
      คีย์ที่ไม่ใส่ถือว่าว่าง; "reason" ใส่หรือไม่ก็ได้
    - **tuple 4 ค่า (เดิม)**: (label, value_str, note_str, ok) — ยังใช้ได้ แสดงหัวข้อบรรทัดเดียว
      ป้ายไม่มีเหตุผลต่อท้าย (โค้ดหน้าเก่าที่ยังไม่ย้ายมา dict ไม่พัง)

    ok: True=เขียว "OK", False=แดง "ไม่ผ่าน", "warn"=เหลือง "ตรวจสอบ", None=ไม่แสดงป้าย"""

    def _badge(ok, reason: str) -> str:
        reason = (reason or "").strip()
        if ok is True:
            txt = ("OK " + reason).strip() if reason else "OK"
            return f'<div class="npk-mc-badge ok">{txt} ✅</div>'
        if ok is False:
            txt = ("ไม่ผ่าน " + reason).strip() if reason else "ไม่ผ่าน"
            return f'<div class="npk-mc-badge bad">{txt} ❌</div>'
        if ok == "warn":
            txt = ("ตรวจสอบ " + reason).strip() if reason else "ตรวจสอบ"
            return f'<div class="npk-mc-badge warn">⚠️ {txt}</div>'
        return ""

    cols = st.columns(len(items))
    for i, (item, col) in enumerate(zip(items, cols)):
        if isinstance(item, dict):
            name = item.get("name", "")
            sym = item.get("sym", "")
            value = item.get("value", "")
            unit = item.get("unit", "")
            ok = item.get("ok", None)
            reason = item.get("reason", "")
        else:  # tuple 4 ค่าแบบเดิม
            name, value, unit, ok = item
            sym, reason = "", ""
        with col:
            with st.container(border=True, key=f"npk-mc-{i}-{name}"):
                sym_html = f'<div class="npk-mc-sym">{sym}</div>' if sym else ""
                st.markdown(
                    f'<div class="npk-mc-label">{name}</div>'
                    f'{sym_html}'
                    f'<div class="npk-mc-value">{value}</div>'
                    f'<div class="npk-mc-note">{unit or ""}</div>'
                    f'{_badge(ok, reason)}',
                    unsafe_allow_html=True,
                )


def inject_compact_input_css(box_key: str) -> None:
    """แทรก CSS จัดช่องกรอกข้อมูลในกล่อง container(key=box_key) ให้กระชับ — ซ่อนปุ่ม
    +/- ของ number_input, จำกัดความกว้างกล่องกรอกให้พอดีเนื้อหา (ตัวเลข/ตัวเลือก),
    ลดขนาด/padding/gap ให้ดูสมส่วน ไม่มีพื้นที่ว่างเหลือในกล่องเหมือนก่อนปรับ

    ขอบเขตของ CSS จำกัดเฉพาะภายใน container ที่มี key=box_key เท่านั้น

    REDESIGN 2026-07-11: High contrast typography + professional engineering software
    """
    st.markdown(f"""
<style>
[class*="st-key-{box_key}"] {{ padding:0 !important; }}
[class*="st-key-{box_key}"] [data-testid="stVerticalBlock"] {{ gap:0 !important; }}
[class*="st-key-{box_key}"] [data-testid="stElementContainer"] {{ margin:0 !important; }}

/* ซ่อนปุ่ม +/- ของ number_input */
[class*="st-key-{box_key}"] [data-testid="stNumberInputStepDown"],
[class*="st-key-{box_key}"] [data-testid="stNumberInputStepUp"] {{ display:none !important; }}

/* แต่ละ widget = แถวเดียว: label ชิดซ้าย / ช่องกรอกชิดขวา (สไตล์ ETABS)
   ปรับระยะห่าง 2026-07-12: เพิ่ม gap label↔ช่องกรอก, เพิ่ม padding บน-ล่าง/ซ้าย-ขวา,
   เพิ่มความสูงแถวขั้นต่ำ — ของเดิมแน่นเกินไป (ผู้ใช้แจ้ง) */
[class*="st-key-{box_key}"] [data-testid="stNumberInput"],
[class*="st-key-{box_key}"] [data-testid="stSelectbox"],
[class*="st-key-{box_key}"] [data-testid="stTextInput"] {{
    display:flex !important; align-items:center !important; gap:20px !important;
    margin:0 !important; padding:11px 18px !important;
    border-bottom:1px solid #EEF1F5 !important; min-height:56px;
}}
[class*="st-key-{box_key}"] [data-testid="stNumberInput"] > label,
[class*="st-key-{box_key}"] [data-testid="stSelectbox"] > label,
[class*="st-key-{box_key}"] [data-testid="stTextInput"] > label {{
    flex:1 1 auto !important; margin:0 !important; min-width:0; display:flex; align-items:center;
}}
[class*="st-key-{box_key}"] [data-testid="stNumberInput"] > label p,
[class*="st-key-{box_key}"] [data-testid="stSelectbox"] > label p,
[class*="st-key-{box_key}"] [data-testid="stTextInput"] > label p {{
    font-size:16.5px !important; font-weight:600 !important; color:{COLORS['field_label']} !important;
    margin:0 !important; white-space:normal !important; overflow-wrap:break-word; word-break:break-word;
    line-height:1.25;
}}

/* number input: ชิดขวา ความกว้างคงที่ (ขยายให้พอกับตัวเลขที่ใหญ่ขึ้น) */
[class*="st-key-{box_key}"] [data-testid="stNumberInputContainer"] {{
    flex:0 0 160px !important; width:160px !important; max-width:160px !important;
}}
[class*="st-key-{box_key}"] [data-testid="stNumberInput"] input {{
    height:38px !important; min-height:38px !important; padding:3px 11px !important;
    text-align:right !important; font-size:18px !important; font-weight:600 !important;
    color:{COLORS['heading']} !important; background:#F8FAFC !important; border-color:#D8DEE7 !important;
    font-variant-numeric:tabular-nums;
}}

/* selectbox: ชิดขวา */
[class*="st-key-{box_key}"] [data-testid="stSelectbox"] {{ max-width:none !important; }}
[class*="st-key-{box_key}"] [data-testid="stSelectbox"] > div[data-baseweb="select"] {{
    flex:0 0 210px !important; width:210px !important;
}}
[class*="st-key-{box_key}"] [data-testid="stSelectbox"] div[data-baseweb="select"] > div {{
    min-height:38px !important; height:38px !important; padding:2px 11px !important;
    font-size:17px !important; font-weight:600 !important;
    color:{COLORS['heading']} !important; background:#FFFFFF !important; border-color:#D8DEE7 !important;
}}

/* text input: ชิดขวา */
[class*="st-key-{box_key}"] [data-testid="stTextInput"] > div {{ flex:0 0 190px !important; width:190px !important; }}
[class*="st-key-{box_key}"] [data-testid="stTextInput"] input {{
    height:38px !important; min-height:38px !important; padding:3px 11px !important;
    text-align:right !important; font-size:18px !important; font-weight:700 !important;
    color:{COLORS['heading']} !important; background:#F8FAFC !important; border-color:#D8DEE7 !important;
}}
</style>
""", unsafe_allow_html=True)

    # ===== RESPONSIVE (ช่องกรอกในการ์ด) =====
    # ถอด media query ย่อฟอนต์/ความกว้าง + flex-wrap ออกแล้ว (2026-07-14) — ใช้ zoom-to-fit
    # ส่วนกลางแทน (ดูหมายเหตุใน inject_card_css) เพื่อไม่ให้ย่อซ้ำซ้อนกับ zoom


def bar_type_label(k: str) -> str:
    """ป้ายชื่อสั้นชนิดเหล็ก (DB/RB) สำหรับใช้ใน format_func ของ selectbox ชนิดเหล็ก
    ในกล่องกระชับ — ใช้คำสั้นแทนข้อความเต็ม (เดิม "DB (เหล็กข้ออ้อย)") เพราะกล่อง
    selectbox ถูกจำกัดความกว้างไว้ที่ 190px ข้อความยาวจะถูกตัด/ล้น"""
    return "DB" if k == "DB" else "RB"


# ===========================================================================
# แผ่นแสดงวิธีการคำนวณ (Calculation Sheet) — สไตล์วิศวกรมืออาชีพ (2026-07-13)
# helper กลางที่ทุกโมดูลใช้ร่วมกัน เพื่อแสดง "ที่มา/สูตร/การแทนค่า/ผลลัพธ์" ของการออกแบบ
# แต่ละขั้นตอน — โมดูลต้องส่ง "ค่าที่คำนวณเสร็จแล้ว" (จาก result ของ calculate()) เข้ามา
# ห้ามคำนวณตัวเลขซ้ำในนี้ (กันเลขไม่ตรงกับที่โมดูลใช้จริง) helper แค่จัดรูปแบบการแสดงผล
# ===========================================================================
_CALC_SHEET_CSS = """
<style>
.npk-calc-sec { border:1px solid #D8DEE7; border-radius:8px; overflow:hidden;
    margin-bottom:14px; box-shadow:0 1px 2px rgba(15,23,42,.05); }
.npk-calc-head { background:#1E3853; color:#fff; font-weight:700; font-size:15.5px;
    padding:10px 16px; letter-spacing:.2px; }
.npk-calc-tbl { width:100%; border-collapse:collapse; background:#fff; }
.npk-calc-tbl td { border-bottom:1px solid #EEF1F5; padding:9px 14px; vertical-align:top; }
.npk-calc-tbl tr:last-child td { border-bottom:none; }
.npk-calc-no { width:34px; color:#94A3B8; font-weight:800; font-size:14px;
    text-align:center; font-family:'Segoe UI',Tahoma,sans-serif; }
.npk-calc-desc { font-size:13.5px; color:#475569; font-weight:600; margin-bottom:4px; }
.npk-calc-eq { font-family:'Consolas','Menlo','Courier New',monospace; font-size:14px;
    color:#0F172A; line-height:1.65; }
.npk-calc-eq .r { color:#1D4ED8; font-weight:700; }
.npk-calc-eq .r.pass { color:#15803D; font-weight:800; font-size:1.2em; }
.npk-calc-eq .r.fail { color:#B91C1C; font-weight:800; font-size:1.2em; }
.npk-calc-eq .op { color:#64748B; }
.npk-calc-note { font-size:12.5px; color:#B45309; margin-top:4px; }
@media (max-width:1024px){ .npk-calc-eq{ font-size:12.5px; } .npk-calc-desc{ font-size:12.5px; } }
</style>
"""


def render_calc_sheet(sections: list) -> None:
    """แสดง 'แผ่นแสดงวิธีการคำนวณ' สไตล์วิศวกร — เรียกครั้งเดียวต่อหน้า (หลังการ์ดสรุปผล)

    sections: list ของ dict:
      {
        "title": ชื่อกลุ่ม เช่น "การออกแบบเหล็กรับแรงดัด (Flexural Design)",
        "steps": [
           {"desc": คำอธิบายขั้นตอน (ไทย),
            "formula": สูตรสัญลักษณ์ (รองรับ HTML/Unicode เช่น φ ρ √ ² · ≤ <br>),
            "sub": การแทนค่าตัวเลข (ไม่บังคับ),
            "result": ผลลัพธ์ที่เน้นสีน้ำเงิน (ไม่บังคับ),
            "note": หมายเหตุ/คำเตือน (ไม่บังคับ) },
           ...
        ]
      }

    ผลลัพธ์แต่ละบรรทัดต่อกันเป็น: สูตร = แทนค่า = ผลลัพธ์(เน้น) โดยส่วนที่ไม่ได้ใส่จะถูกข้าม
    """
    html = [_CALC_SHEET_CSS]
    for sec in sections:
        html.append('<div class="npk-calc-sec">')
        html.append(f'<div class="npk-calc-head">{sec.get("title","")}</div>')
        html.append('<table class="npk-calc-tbl">')
        for i, step in enumerate(sec.get("steps", []), start=1):
            eq_parts = []
            if step.get("formula"):
                eq_parts.append(step["formula"])
            if step.get("sub"):
                eq_parts.append('<span class="op">=</span> ' + step["sub"])
            if step.get("result"):
                # ผลลัพธ์ที่เป็นสถานะ "ผ่าน" -> เขียว/ใหญ่, "ไม่ผ่าน" -> แดง/ใหญ่ (ตรวจ "ไม่ผ่าน" ก่อน
                # เพราะมีคำว่า "ผ่าน" ซ้อนอยู่) อื่นๆ เป็นค่าตัวเลขทั่วไป -> น้ำเงินตามเดิม
                res = step["result"]
                rcls = "r"
                if "ไม่ผ่าน" in res or "เล็กเกินไป" in res:
                    rcls = "r fail"
                elif "ผ่าน" in res:
                    rcls = "r pass"
                eq_parts.append(f'<span class="op">=</span> <span class="{rcls}">' + res + '</span>')
            eq = ' '.join(eq_parts)
            desc = f'<div class="npk-calc-desc">{step["desc"]}</div>' if step.get("desc") else ""
            note = f'<div class="npk-calc-note">{step["note"]}</div>' if step.get("note") else ""
            html.append(
                f'<tr><td class="npk-calc-no">{i}</td>'
                f'<td class="npk-calc-body">{desc}<div class="npk-calc-eq">{eq}</div>{note}</td></tr>'
            )
        html.append('</table></div>')
    st.markdown("".join(html), unsafe_allow_html=True)


# ===========================================================================
# CENTERED IMAGE — แสดงรูปกึ่งกลางหน้า (st.image ปกติชิดซ้ายเสมอ ไม่มีตัวเลือกจัดกึ่งกลาง)
# ===========================================================================

def centered_image(png_bytes: bytes, width=None, caption: str = "") -> None:
    """แสดงรูป PNG กึ่งกลางแนวนอนของพื้นที่เนื้อหา — ใช้ inline <img> แบบ base64
    ห่อด้วย div text-align:center แทน st.image (ซึ่งจัดชิดซ้ายเสมอไม่มีพารามิเตอร์จัดกึ่งกลาง)

    width: ความกว้างที่ต้องการเป็นพิกเซล (None = ขนาดต้นฉบับของภาพ)
    caption: ข้อความใต้ภาพ (ไม่บังคับ) — จัดกึ่งกลางเช่นกัน
    """
    import base64 as _b64
    b64 = _b64.b64encode(png_bytes).decode("ascii")
    # ใช้ inline style กำหนดความกว้างเป็นพิกเซลชัดเจน + max-width:100% กันล้นจอ (ไม่ปล่อยให้
    # เบราว์เซอร์ย่อภาพเองจนเล็กเกิน) — height:auto รักษาสัดส่วน
    if width:
        img_style = f'width:{int(width)}px;max-width:100%;height:auto;'
    else:
        img_style = 'max-width:100%;height:auto;'
    cap_html = (
        f'<div style="text-align:center;color:#5a6472;font-size:0.82rem;margin-top:4px;">{caption}</div>'
        if caption else ""
    )
    st.markdown(
        f'<div style="text-align:center;"><img src="data:image/png;base64,{b64}" style="{img_style}" /></div>{cap_html}',
        unsafe_allow_html=True,
    )
