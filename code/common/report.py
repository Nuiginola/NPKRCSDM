"""
Printable Thai-language calculation report ("รายการคำนวณ") builder.

Produces a single self-contained HTML string, styled to be compact and
fit on a single A4 page when printed (dense header block + side-by-side
data tables, similar in spirit to the reference "Slab No. GS-01" sheet),
with an embedded print button that calls window.print().
"""

import base64
import datetime

from common.diagram import png_to_data_uri
from modules.slab_on_ground import GS_STEEL_FY_KSC
from modules.one_way_slab import CONTINUITY_CASES
from modules.two_way_slab import TWO_WAY_CASES
from modules.cantilever_slab import TMIN_DENOM as CANT_TMIN_DENOM
from modules.beam_single_span import reinf_label_with_layers, MAX_LAYERS

_THAI_MONTHS = [
    "", "มกราคม", "กุมภาพันธ์", "มีนาคม", "เมษายน", "พฤษภาคม", "มิถุนายน",
    "กรกฎาคม", "สิงหาคม", "กันยายน", "ตุลาคม", "พฤศจิกายน", "ธันวาคม",
]


def thai_date_str(d: datetime.date | None = None) -> str:
    """Format a date as 'DD เดือนไทย YYYY' (Gregorian year, matching the
    reference cover-page sample which used a Gregorian, not Buddhist-Era, year)."""
    d = d or datetime.date.today()
    return f"{d.day:02d} {_THAI_MONTHS[d.month]} {d.year}"


def image_bytes_to_data_uri(data: bytes, mime: str) -> str:
    b64 = base64.b64encode(data).decode("ascii")
    return f"data:{mime};base64,{b64}"


# CSS สำหรับหัวกระดาษมาตรฐาน (ตาราง โครงการ/เจ้าของ/สถานที่/ผู้ออกแบบ/วันที่ + โลโก้
# + บรรทัดหัวข้อสีน้ำเงินใต้ตาราง) ที่ทุกหน้ารายการคำนวณต้องมีเหมือนกัน — ผนวกเข้าไปใน
# <style> ของแต่ละรายงานที่เรียกใช้ build_report_header_html()
REPORT_HEADER_CSS = """
  .rpt-header { border-collapse: collapse; width: 100%; margin-bottom: 4px; }
  .rpt-header td { border: 1px solid #333; padding: 3px 8px; font-size: 12.5px; }
  .rpt-logo-cell { width: 70px; text-align: center; vertical-align: middle; }
  .rpt-logo-cell img { display: block; margin: 0 auto; max-width: 60px; max-height: 60px; object-fit: contain; }
  .rpt-subtitle { text-align: center; color: #2563eb; font-weight: bold; font-size: 14px; margin: 4px 0 10px 0; }
"""


def build_report_header_html(project_info: dict, logo_bytes: bytes, logo_mime: str,
                              doc_label: str, subtitle: str) -> str:
    """
    หัวกระดาษมาตรฐานที่ทุกหน้ารายการคำนวณต้องมี: โลโก้ + ตาราง 3 แถว
    (โครงการ/doc_label, เจ้าของ/ผู้ออกแบบ, สถานที่/วันที่) + บรรทัดหัวข้อสีน้ำเงิน
    กึ่งกลางใต้ตาราง เรียกใช้ก่อนเนื้อหาของแต่ละรายงาน (แทนที่ <h1> เดิม)

    project_info: dict จากหน้า "ข้อมูลโครงการ" (keys: owner, project_name,
                  location, engineer)
    doc_label: ข้อความมุมขวาบนของตาราง เช่น "พื้น : GS1" หรือ "คาน : B1 หน้าที่ 1/2"
    subtitle: บรรทัดสีน้ำเงินใต้ตาราง เช่น "รายการคำนวณโดยวิธีกำลังตามกฎกระทรวง พ.ศ.2566"
    """
    project_info = project_info or {}
    owner = project_info.get("owner") or "-"
    project_name = project_info.get("project_name") or "-"
    location = project_info.get("location") or "-"
    engineer = project_info.get("engineer") or "-"
    date_str = thai_date_str()

    if logo_bytes and logo_mime:
        logo_html = f'<img src="{image_bytes_to_data_uri(logo_bytes, logo_mime)}" alt="logo">'
    else:
        logo_html = ""

    return f"""
<table class="rpt-header">
  <tr>
    <td class="rpt-logo-cell" rowspan="3">{logo_html}</td>
    <td style="width:55%">โครงการ : {project_name}</td>
    <td>{doc_label}</td>
  </tr>
  <tr>
    <td>เจ้าของ : {owner}</td>
    <td>ผู้ออกแบบ : {engineer}</td>
  </tr>
  <tr>
    <td>สถานที่ : {location}</td>
    <td>วันที่ : {date_str}</td>
  </tr>
</table>
<p class="rpt-subtitle">{subtitle}</p>
"""


def build_design_params_report_html(params, project_info: dict = None,
                                     logo_bytes: bytes = None, logo_mime: str = None,
                                     load_schedule=None, load_factor_note: str = "",
                                     load_schedule_source: str = "") -> str:
    """
    Compact printable "พารามิเตอร์การออกแบบ" (Design Parameters) sheet.
    params: common.design_params.DesignParameters
    project_info/logo_bytes/logo_mime: จากหน้า "ข้อมูลโครงการ" — ใช้กับหัวกระดาษ
    มาตรฐานที่ทุกหน้ารายการคำนวณต้องมี
    load_schedule/load_factor_note/load_schedule_source: จาก common.design_params
    (LOAD_SCHEDULE/LOAD_FACTOR_NOTE/LOAD_SCHEDULE_SOURCE) — รายการน้ำหนักบรรทุกจรมาตรฐาน
    """
    load_rows_html = "".join(
        f"<tr><td>{r['usage']}</td><td>{r['ll_kg_m2']:.0f}</td><td>kg/m&sup2;</td></tr>"
        for r in (load_schedule or [])
    )
    header_html = build_report_header_html(
        project_info, logo_bytes, logo_mime,
        doc_label="คอนกรีตเสริมเหล็ก",
        subtitle="ข้อกำหนดในการคำนวณออกแบบคอนกรีตเสริมเหล็ก",
    )
    html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>พารามิเตอร์การออกแบบ</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ margin: 0; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; font-size: 14px; color: #111;
          max-width: 700px; margin: 14px auto; padding: 0 14px; line-height: 1.4; }}
  h2 {{ font-size: 13.5px; background:#dbe7f5; padding: 3px 8px; margin: 12px 0 4px 0; border-left: 4px solid #2563eb; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #999; padding: 4px 8px; font-size: 13px; }}
  .no-split {{ page-break-inside: avoid; break-inside: avoid; }}
  th {{ background: #eee; text-align: left; }}
  .print-btn {{ background:#2563eb; color:white; border:none; padding:8px 18px;
                border-radius:6px; font-size:14px; cursor:pointer; }}
  .center {{ text-align: center; }}
{REPORT_HEADER_CSS}
</style>
</head>
<body>

<div class="no-print" style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
  <span style="font-size:16px; font-weight:bold; color:#111;">ข้อกำหนดการออกแบบ</span>
  <button class="print-btn" onclick="window.print()">🖨️ พิมพ์ข้อกำหนด</button>
</div>

{header_html}

<h2>คุณสมบัติวัสดุ</h2>
<table>
  <tr><td>กำลังอัดประลัยคอนกรีตที่อายุ 28 วัน f'c</td><td>{params.fc_ksc:.0f}</td><td>kg/cm²</td></tr>
  <tr><td>โมดูลัสยืดหยุ่นคอนกรีต Ec = 15,100&radic;f'c</td><td>{params.ec_ksc:.0f}</td><td>kg/cm²</td></tr>
  <tr><td>เหล็กเสริม</td><td colspan="2">{params.steel_type}</td></tr>
  <tr><td>กำลังคราก fy</td><td>{params.fy_ksc:.0f}</td><td>kg/cm²</td></tr>
  <tr><td>โมดูลัสยืดหยุ่นเหล็กเสริม Es</td><td>{params.es_ksc:.0f}</td><td>kg/cm²</td></tr>
</table>

<h2>วิธีกำลัง (Strength Design Method)</h2>
<table>
  <tr><td>&beta;1</td><td>{params.beta1:.2f}</td><td>-</td></tr>
  <tr><td>&rho;b</td><td>{params.rho_b:.4f}</td><td>-</td></tr>
  <tr><td>&rho;min = 14 / fy</td><td>{params.rho_min:.4f}</td><td>-</td></tr>
  <tr><td>&rho;max = 0.75&rho;b</td><td>{params.rho_max:.4f}</td><td>-</td></tr>
  <tr><td>กฎกระทรวง พ.ศ. 2566</td><td colspan="2">U = 1.4D + 1.7L</td></tr>
  <tr><td>มาตรฐาน วสท. 011008-21</td><td colspan="2">U = 1.4D + 1.7L</td></tr>
  <tr><td>ตัวคูณลดกำลังดัด &phi;b</td><td>{params.phi_b:.2f}</td><td>-</td></tr>
  <tr><td>ตัวคูณลดกำลังเฉือน &phi;v</td><td>{params.phi_v:.2f}</td><td>-</td></tr>
  <tr><td>ตัวคูณลดกำลังอัด &phi;</td><td>{params.phi_c:.2f}</td><td>-</td></tr>
</table>

<h2 class="no-split">รายการน้ำหนักบรรทุกจร (Live Load) มาตรฐาน</h2>
<table class="no-split">
  <tr><th>ลักษณะการใช้งาน</th><th>LL</th><th>หน่วย</th></tr>
  {load_rows_html}
</table>
<p style="margin-top:6px; font-size:12px;">ตัวคูณน้ำหนักบรรทุก: {load_factor_note}</p>
<p style="margin-top:2px; font-size:10.5px; color:#666;">{load_schedule_source}</p>

<p style="margin-top:16px; font-size:11px; color:#666;">
พารามิเตอร์เหล่านี้ใช้ร่วมกันในโมดูลที่ใช้วิธีออกแบบดัด/แรงเฉือนโดยตรง (คาน เสา พื้นสองทาง ฯลฯ) — ไม่ได้ใช้ในโมดูลพื้นวางบนดิน (Slab on Ground) ซึ่งใช้เกณฑ์ Temperature/Subgrade Drag/PCA แยกต่างหาก
</p>

</body>
</html>
"""
    return html


def build_cover_page_html(project_info: dict, logo_bytes: bytes = None, logo_mime: str = None,
                           cover_image_bytes: bytes = None, cover_image_mime: str = None) -> str:
    """
    ปกรายงาน (report cover page) — generated from the "ข้อมูลโครงการ" (Project
    Information) page. Layout: logo + title "รายการคำนวณออกแบบ" + project name
    subtitle at top, an optional construction-drawing/house photo centered in
    the middle (scaled proportionally, never stretched/cropped), footer block
    (owner / site / designer / date) centered at bottom. Fits exactly one A4
    page (no visible border/frame — the @page margin defines the page edge).

    project_info: dict with keys owner, project_name, location, engineer.
    logo_bytes/logo_mime: optional uploaded logo image; if omitted, a plain
    placeholder box is shown instead.
    cover_image_bytes/cover_image_mime: optional construction-drawing/house
    photo shown centered in the middle of the page; if omitted, that area is
    simply left blank (no placeholder on the printed page).
    """
    owner = project_info.get("owner") or "-"
    project_name = project_info.get("project_name") or "-"
    location = project_info.get("location") or "-"
    engineer = project_info.get("engineer") or "-"
    date_str = thai_date_str()

    if logo_bytes and logo_mime:
        logo_uri = image_bytes_to_data_uri(logo_bytes, logo_mime)
        logo_html = f'<img src="{logo_uri}" alt="logo" style="max-width:140px; max-height:140px;">'
    else:
        logo_html = ('<div style="width:120px; height:90px; border:1px dashed #999; '
                     'display:flex; align-items:center; justify-content:center; '
                     'color:#999; font-size:12px; margin:0 auto;">ไม่มีโลโก้</div>')

    if cover_image_bytes and cover_image_mime:
        cover_img_uri = image_bytes_to_data_uri(cover_image_bytes, cover_image_mime)
        cover_image_html = (f'<img src="{cover_img_uri}" alt="cover drawing/photo" '
                             'style="max-width:100%; max-height:100%; object-fit:contain;">')
    else:
        cover_image_html = ""

    html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>ปกรายงาน {project_name}</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  @media print {{
    .no-print {{ display: none !important; }}
    html, body {{ margin: 0; height: 100%; }}
  }}
  * {{ box-sizing: border-box; }}
  html, body {{ height: 100%; }}
  body {{ font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; color: #111; margin: 0; }}
  .print-btn {{ background:#2563eb; color:white; border:none; padding:8px 18px;
                border-radius:6px; font-size:14px; cursor:pointer; }}
  .center {{ text-align: center; }}
  .cover-page {{ width: 100%; height: 273mm; margin: 0 auto; padding: 6mm 10mm;
                 display: flex; flex-direction: column; align-items: center; text-align: center; }}
  .cover-title {{ color: #2563eb; font-size: 24px; font-weight: bold; margin: 18px 0 6px 0; }}
  .cover-subtitle {{ font-size: 18px; margin: 0; }}
  .cover-image-area {{ flex: 1; width: 100%; min-height: 0; display: flex;
                        align-items: center; justify-content: center; overflow: hidden; padding: 10mm 0; }}
  .cover-footer {{ font-size: 15px; line-height: 1.8; text-align: center; margin-bottom: 6mm; }}
  .cover-footer b {{ font-size: 16px; }}
</style>
</head>
<body>

<div class="no-print" style="margin:10px 0; display:flex; justify-content:space-between; align-items:center;">
  <span style="font-size:16px; font-weight:bold; color:#111;">ปกรายงาน</span>
  <button class="print-btn" onclick="window.print()">🖨️ พิมพ์ปกรายงาน</button>
</div>

<div class="cover-page">
  {logo_html}
  <div class="cover-title">รายการคำนวณออกแบบ</div>
  <div class="cover-subtitle">{project_name}</div>
  <div class="cover-image-area">{cover_image_html}</div>
  <div class="cover-footer">
    <b>{owner}</b><br>
    สถานที่ก่อสร้าง : {location}<br>
    วิศวกรผู้ออกแบบ : {engineer}<br>
    วันที่ : {date_str}
  </div>
</div>

</body>
</html>
"""
    return html


def build_gs_report_html(project: dict, inp, result, diagram_png: bytes,
                          project_info: dict = None, logo_bytes: bytes = None,
                          logo_mime: str = None) -> str:
    """
    project: dict with key slab_name (module-specific; not part of the shared
             project info).
    project_info/logo_bytes/logo_mime: จากหน้า "ข้อมูลโครงการ" — ใช้กับหัวกระดาษ
    มาตรฐานที่ทุกหน้ารายการคำนวณต้องมี
    inp: SlabOnGroundInput
    result: SlabOnGroundResult
    """
    diagram_uri = png_to_data_uri(diagram_png)

    def ok_th(flag: bool) -> str:
        return "ผ่าน" if flag else "ไม่ผ่าน"

    def ok_class(flag: bool) -> str:
        return "ok" if flag else "ng"

    limits = result.dimension_limits or {"min_m": "-", "max_m": "-"}
    slab_type_th = "พื้นภายในอาคาร / มีคาน (IN)" if inp.slab_context == "IN" else "พื้นภายนอกอาคาร / ไม่มีคาน (OUT)"
    slab_name = project.get("slab_name", "GS1")
    header_html = build_report_header_html(
        project_info, logo_bytes, logo_mime,
        doc_label=f"พื้น : {slab_name}",
        subtitle="รายการคำนวณโดยวิธีกำลังตามกฎกระทรวง พ.ศ.2566",
    )

    html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>รายการคำนวณ {project.get('slab_name', 'GS1')}</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ margin: 0; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; font-size: 13.5px; color: #111;
          max-width: 780px; margin: 14px auto; padding: 0 14px; line-height: 1.35; }}
  h2 {{ font-size: 13.5px; background:#dbe7f5; padding: 3px 8px; margin: 10px 0 4px 0; border-left: 4px solid #2563eb; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #999; padding: 3px 7px; font-size: 12.5px; }}
  th {{ background: #eee; text-align: left; }}
  .row3 {{ display: flex; gap: 10px; margin-bottom: 4px; }}
  .row3 > div {{ flex: 1; }}
  .mini-table td, .mini-table th {{ padding: 2px 6px; font-size: 12px; }}
  .ok {{ color: #0a7a0a; font-weight: bold; }}
  .ng {{ color: #b30000; font-weight: bold; }}
  .print-btn {{ background:#2563eb; color:white; border:none; padding:8px 18px;
                border-radius:6px; font-size:14px; cursor:pointer; }}
  img.detail {{ max-width: 100%; border: 1px solid #ccc; margin-top: 4px; display:block; }}
  .center {{ text-align: center; }}
  .summary-line {{ font-size: 14px; margin: 6px 0 2px 0; }}
{REPORT_HEADER_CSS}
</style>
</head>
<body>

<div class="no-print" style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
  <span style="font-size:16px; font-weight:bold; color:#111;">รายการคำนวณ</span>
  <button class="print-btn" onclick="window.print()">🖨️ พิมพ์รายการคำนวณ</button>
</div>

{header_html}

<div class="row3">
  <div>
    <table class="mini-table">
      <tr><th colspan="3">1. คุณสมบัติวัสดุ</th></tr>
      <tr><td>f'c</td><td>{inp.fc_ksc:.0f}</td><td>ksc.</td></tr>
      <tr><td>ชนิดเหล็ก</td><td colspan="2">{inp.steel_type}</td></tr>
      <tr><td>fy</td><td>{GS_STEEL_FY_KSC[inp.steel_type]:.0f}</td><td>ksc.</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">2. น้ำหนักบรรทุก</th></tr>
      <tr><td>Dead Load</td><td>{result.dead_load_kg_m2:.0f}</td><td>kg/m²</td></tr>
      <tr><td>SDL / LL</td><td>{inp.wD_kg_m2:.0f} / {inp.wL_kg_m2:.0f}</td><td>kg/m²</td></tr>
      <tr><td><b>Wu</b></td><td><b>{result.wu_kg_m2:.0f}</b></td><td>kg/m²</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">3. ขนาดพื้น</th></tr>
      <tr><td>L / S</td><td>{inp.L_m:.2f} / {inp.S_m:.2f}</td><td>m.</td></tr>
      <tr><td>t</td><td>{inp.t_cm:.1f}</td><td>cm.</td></tr>
      <tr><td>ช่วงยอมรับ</td><td colspan="2">{limits['min_m']}-{limits['max_m']} m.</td></tr>
      <tr><td>ลักษณะพื้น</td><td colspan="2">{slab_type_th}</td></tr>
    </table>
  </div>
</div>

<h2>4. ออกแบบเหล็กเสริม (ต้องผ่านทั้ง 3 ข้อกำหนด)</h2>
<table class="mini-table">
  <tr><th>ข้อกำหนด</th><th>สูตร</th><th>As ต้องการ (cm²/m)</th><th>ผลตรวจสอบ</th></tr>
  <tr><td>1. Temperature Steel</td><td>ratio &times; b &times; t</td><td>{result.as_temperature_cm2_m:.2f}</td>
      <td class="{ok_class(result.temperature_ok)}">{ok_th(result.temperature_ok)}</td></tr>
  <tr><td>2. Subgrade Drag</td><td>1.5&times;L&times;Wu / (1.43&times;fy)</td><td>{result.as_subgrade_drag_cm2_m:.2f}</td>
      <td class="{ok_class(result.subgrade_drag_ok)}">{ok_th(result.subgrade_drag_ok)}</td></tr>
  <tr><td>3. PCA (มีรถวิ่งผ่าน)</td><td>1800&times;S&times;10&times;t / fy</td><td>{result.as_pca_cm2_m:.2f}</td>
      <td class="{ok_class(result.pca_ok)}">{ok_th(result.pca_ok)}</td></tr>
  <tr><th colspan="2">เหล็กเสริมที่ใช้จริง</th><th>{result.as_provided_cm2_m:.2f}</th>
      <th class="{ok_class(result.all_reinf_ok)}">{ok_th(result.all_reinf_ok)}</th></tr>
</table>
<p class="summary-line"><b>สรุปเหล็กเสริมที่ใช้:  {result.reinf_label}</b>
   &nbsp;&nbsp; L&ge;S: <span class="{ok_class(result.L_ge_S_ok)}">{ok_th(result.L_ge_S_ok)}</span>
   &nbsp;&nbsp; t: <span class="{ok_class(result.t_ok)}">{ok_th(result.t_ok)}</span>
</p>

<h2>5. รูปขยายรายละเอียดการเสริมเหล็ก (Detail Drawing)</h2>
<div class="center">
  <img class="detail" src="{diagram_uri}" alt="Ground slab detail">
</div>

</body>
</html>
"""
    return html


def build_ow_report_html(project: dict, inp, result, section_png: bytes, plan_png: bytes = None,
                          project_info: dict = None, logo_bytes: bytes = None,
                          logo_mime: str = None) -> str:
    """
    project: dict with key slab_name (module-specific).
    inp: modules.one_way_slab.OneWaySlabInput
    result: modules.one_way_slab.OneWaySlabResult
    section_png / plan_png: PNG bytes for the two detail drawings
    (cross-section + plan-view rebar layout). This module only covers the
    3 two-support continuity cases (พื้นยื่น/Cantilever is module 1.4
    instead), so plan_png is always provided in normal use; the
    plan_png=None fallback below is kept only for defensive robustness.
    """
    section_uri = png_to_data_uri(section_png)
    plan_uri = png_to_data_uri(plan_png) if plan_png else None

    def ok_th(flag: bool) -> str:
        return "ผ่าน" if flag else "ไม่ผ่าน"

    def ok_class(flag: bool) -> str:
        return "ok" if flag else "ng"

    def ok_en(flag: bool) -> str:
        return "Ok" if flag else "NG"

    slab_name = project.get("slab_name", "S-01")
    case = CONTINUITY_CASES[inp.continuity_case]
    header_html = build_report_header_html(
        project_info, logo_bytes, logo_mime,
        doc_label=f"พื้น : {slab_name}",
        subtitle="รายการคำนวณโดยวิธีกำลังตามกฎกระทรวง พ.ศ.2566",
    )

    pos_rows = ""
    for p in result.positions:
        if not p.active:
            pos_rows += f"<tr><td>{p.label_th}</td><td colspan='5' style='color:#888;'>ไม่มีการออกแบบ (ใช้เหล็กเสริมรองขั้นต่ำ)</td></tr>"
        else:
            over_html = ' <span class="ng">(หน้าตัดเล็กไป)</span>' if p.over_reinforced else ""
            pos_rows += (
                f"<tr><td>{p.label_th}</td><td>C={p.coeff:.4f}</td>"
                f"<td>{p.mu_kgm:.0f}</td><td>{p.ru_ksc:.2f}</td>"
                f"<td>{p.rho_used:.4f}</td><td>{p.as_req_cm2_m:.2f}{over_html}</td></tr>"
            )

    html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>รายการคำนวณ {slab_name}</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ margin: 0; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; font-size: 13.5px; color: #111;
          max-width: 780px; margin: 14px auto; padding: 0 14px; line-height: 1.35; }}
  h2 {{ font-size: 13.5px; background:#dbe7f5; padding: 3px 8px; margin: 10px 0 4px 0; border-left: 4px solid #2563eb; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #999; padding: 3px 7px; font-size: 12.5px; }}
  th {{ background: #eee; text-align: left; }}
  .row3 {{ display: flex; gap: 10px; margin-bottom: 4px; }}
  .row3 > div {{ flex: 1; }}
  .mini-table td, .mini-table th {{ padding: 2px 6px; font-size: 12px; }}
  .ok {{ color: #0a7a0a; font-weight: bold; }}
  .ng {{ color: #b30000; font-weight: bold; }}
  .drmk-table th {{ background: #dbe7f5; }}
  .drmk-table td.dv {{ color: #b45f06; }}
  .print-btn {{ background:#2563eb; color:white; border:none; padding:8px 18px;
                border-radius:6px; font-size:14px; cursor:pointer; }}
  img.detail {{ margin: 0 auto; display:block; }}
  img.detail-lg {{ max-width: 100%; }}
  img.detail-sm {{ max-width: 62%; }}
  .detail-frame {{ border: 1px solid #ccc; padding: 8px; margin: 4px 0 0 0; }}
  .center {{ text-align: center; }}
  .summary-line {{ font-size: 14px; margin: 6px 0 2px 0; }}
  .page-break {{ page-break-before: always; break-before: page; }}
{REPORT_HEADER_CSS}
</style>
</head>
<body>

<div class="no-print" style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
  <span style="font-size:16px; font-weight:bold; color:#111;">รายการคำนวณ</span>
  <button class="print-btn" onclick="window.print()">🖨️ พิมพ์รายการคำนวณ</button>
</div>

{header_html}

<div class="row3">
  <div>
    <table class="mini-table">
      <tr><th colspan="3">1. คุณสมบัติวัสดุ</th></tr>
      <tr><td>f'c</td><td>{inp.fc_ksc:.0f}</td><td>ksc.</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กหลัก (แนว S)</td><td colspan="2">{inp.main_steel_type} (fy={GS_STEEL_FY_KSC[inp.main_steel_type]:.0f})</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กเสริมรอง (แนว L)</td><td colspan="2">{inp.temp_steel_type} (fy={GS_STEEL_FY_KSC[inp.temp_steel_type]:.0f})</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">2. น้ำหนักบรรทุก</th></tr>
      <tr><td>Dead Load</td><td>{result.dead_load_kg_m2:.0f}</td><td>kg/m²</td></tr>
      <tr><td>SDL / LL</td><td>{inp.wD_kg_m2:.0f} / {inp.wL_kg_m2:.0f}</td><td>kg/m²</td></tr>
      <tr><td><b>Wu</b></td><td><b>{result.wu_kg_m2:.0f}</b></td><td>kg/m²</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">3. ขนาดพื้น</th></tr>
      <tr><td>S / L</td><td>{inp.S_m:.2f} / {inp.L_m:.2f}</td><td>m.</td></tr>
      <tr><td>t</td><td>{inp.t_cm:.1f}</td><td>cm.</td></tr>
      <tr><td>m=S/L</td><td>{result.m_ratio:.3f}</td>
          <td class="{ok_class(result.one_way_ok)}">{ok_th(result.one_way_ok)}</td></tr>
    </table>
  </div>
</div>

<h2>4. ความต่อเนื่องของพื้น &amp; ความหนาต่ำสุด</h2>
<table class="mini-table">
  <tr><th>กรณี</th><td colspan="3">{case['label_th']}</td></tr>
  <tr><td>tmin = (S/{case['tmin_denom']}) &times; (0.40+fy/7000)</td><td>{result.tmin_cm:.2f}</td><td>cm.</td>
      <td class="{ok_class(result.t_ok)}">{ok_th(result.t_ok)}</td></tr>
</table>

<h2>5. โมเมนต์ &amp; เหล็กเสริมหลัก (แนว S) ตามตำแหน่ง</h2>
<table class="mini-table">
  <tr><th>ตำแหน่ง</th><th>Coeff. C</th><th>Mu (kg-m/m)</th><th>Ru (ksc)</th><th>&rho; ที่ใช้</th><th>As ต้องการ (cm²/m)</th></tr>
  {pos_rows}
  <tr><th colspan="5">เหล็กที่ใช้จริง (ทุกตำแหน่ง)</th><th>{result.reinf_label_main}</th></tr>
  <tr><td colspan="2">As ต้องการสูงสุด</td><td colspan="2">{result.as_req_governing_cm2_m:.2f} cm²/m</td>
      <td>As ที่ใช้จริง</td><td>{result.as_provided_cm2_m:.2f} cm²/m</td></tr>
  <tr><td colspan="2">ระยะห่างสูงสุดที่ยอมให้ (min[As-based, 3t, 45cm])</td><td colspan="2">{result.main_spacing_max_cm:.1f} cm.</td>
      <th>ผลตรวจสอบ</th><th class="{ok_class(result.main_reinf_ok)}">{ok_th(result.main_reinf_ok)}</th></tr>
</table>

<h2>6. เหล็กเสริมรอง — กระจายแรง/กันร้าว (แนว L)</h2>
<table class="mini-table">
  <tr><td>Ast ต้องการ</td><td>{result.ast_req_cm2_m:.2f}</td><td>cm²/m</td>
      <td>เหล็กที่ใช้จริง</td><td>{result.reinf_label_temp} = {result.ast_provided_cm2_m:.2f} cm²/m</td></tr>
  <tr><td>ระยะห่างสูงสุดที่ยอมให้ (min[Ast-based, 5t, 45cm])</td><td>{result.temp_spacing_max_cm:.1f}</td><td>cm.</td>
      <th>ผลตรวจสอบ</th><th class="{ok_class(result.temp_reinf_ok)}">{ok_th(result.temp_reinf_ok)}</th></tr>
</table>

<h2>7. ตรวจสอบแรงเฉือน (Shear Check)</h2>
<table class="mini-table drmk-table">
  <tr><th>Data</th><th>Short Span</th><th>Long Span</th><th>Unit</th></tr>
  <tr><td>Vu&nbsp;&nbsp;=&nbsp;1.15(WuS/2)-Wud</td>
      <td class="dv">{result.vu_kg:.2f}</td><td class="dv">-</td><td class="dv">kg.</td></tr>
  <tr><td>&phi;<sub>v</sub>Vc&nbsp;=&nbsp;&phi;<sub>v</sub>&middot;0.53(&radic;fc')bd</td>
      <td class="dv">{result.phi_vc_kg:.2f} <span class="{ok_class(result.shear_ok)}">&lt;&lt; [{ok_en(result.shear_ok)}]</span></td>
      <td class="dv">-</td><td class="dv">kg.</td></tr>
</table>

<h2>8. ถ่ายน้ำหนักลงคาน (Load Transfer to the Beam)</h2>
<table class="mini-table drmk-table">
  <tr><th>Data</th><th>Short Span</th><th>Long Span</th><th>Unit</th></tr>
  <tr><td>Dead Load on Beam</td><td class="dv">{result.dl_on_beam_kg_m:.2f}</td><td class="dv">-</td><td class="dv">kg./m.</td></tr>
  <tr><td>Live Load on Beam</td><td class="dv">{result.ll_on_beam_kg_m:.2f}</td><td class="dv">-</td><td class="dv">kg./m.</td></tr>
</table>

<h2 class="page-break">9. รูปขยายรายละเอียดการเสริมเหล็ก — รูปตัด (Cross-section)</h2>
<div class="center detail-frame">
  <img class="detail detail-lg" src="{section_uri}" alt="One way slab section detail">
</div>

{f'''<h2>10. รูปขยายรายละเอียดการเสริมเหล็ก — แปลน (Plan)</h2>
<div class="center detail-frame">
  <img class="detail detail-sm" src="{plan_uri}" alt="One way slab plan detail">
</div>''' if plan_uri else ""}

</body>
</html>
"""
    return html


def build_tw_report_html(project: dict, inp, result,
                          section_s_png: bytes = None, section_l_png: bytes = None, plan_png: bytes = None,
                          project_info: dict = None, logo_bytes: bytes = None,
                          logo_mime: str = None) -> str:
    """
    project: dict with key slab_name.
    inp: modules.two_way_slab.TwoWaySlabInput
    result: modules.two_way_slab.TwoWaySlabResult
    section_s_png / section_l_png / plan_png: PNG bytes for the three detail
    drawings (short-direction cross-section, long-direction cross-section,
    reinforcement plan) — see common/diagram.py draw_tw_section_png /
    draw_tw_plan_png. Optional (kept defensive-optional the same way
    build_ow_report_html keeps plan_png optional) so older call sites don't
    break, but normal use always supplies all three.

    NOTE: this module's moment coefficients are only fully confirmed
    against the user's reference file for ONE of the 5 cases (CASE2, short
    direction; long direction spot-checked at one point) — see the
    docstring in modules/two_way_slab.py for the full explanation. The
    report prints a visible caveat banner whenever an unconfirmed case is
    selected, per that module's documentation requirement.
    """
    section_s_uri = png_to_data_uri(section_s_png) if section_s_png else None
    section_l_uri = png_to_data_uri(section_l_png) if section_l_png else None
    plan_uri = png_to_data_uri(plan_png) if plan_png else None

    def ok_th(flag: bool) -> str:
        return "ผ่าน" if flag else "ไม่ผ่าน"

    def ok_class(flag: bool) -> str:
        return "ok" if flag else "ng"

    def ok_en(flag: bool) -> str:
        return "Ok" if flag else "NG"

    slab_name = project.get("slab_name", "S2-01")
    case = TWO_WAY_CASES[inp.case_key]
    header_html = build_report_header_html(
        project_info, logo_bytes, logo_mime,
        doc_label=f"พื้น : {slab_name}",
        subtitle="รายการคำนวณโดยวิธีกำลังตามกฎกระทรวง พ.ศ.2566 (ACI 318-63 Method 3 — Moment Coefficient Method)",
    )

    def pos_rows(positions):
        rows = ""
        for p in positions:
            if not p.active:
                rows += f"<tr><td>{p.label_th}</td><td colspan='4' style='color:#888;'>ไม่มีการออกแบบ (ไม่มีขอบต่อเนื่อง/ไม่ต่อเนื่องในตำแหน่งนี้)</td></tr>"
            else:
                over_html = ' <span class="ng">(หน้าตัดเล็กไป)</span>' if p.over_reinforced else ""
                rows += (
                    f"<tr><td>{p.label_th}</td><td>C={p.coeff:.4f}</td>"
                    f"<td>{p.mu_kgm:.0f}</td><td>{p.rho_used:.4f}</td>"
                    f"<td>{p.as_req_cm2_m:.2f}{over_html}</td></tr>"
                )
        return rows

    # ข้อ 9-10 (รูปตัด + แปลน) ประกอบเป็น HTML แยกไว้ก่อน (ไม่ใช้ f-string ซ้อน f-string
    # หลายชั้น เพื่อเลี่ยงปัญหา backslash ใน f-string expression) แล้วค่อยแทรกเข้า
    # ในแม่แบบหลักทีเดียว — ข้อ 9 กับ 10 อยู่ในบล็อกเดียวกัน (ไม่มี page-break คั่นกลาง)
    # เพื่อให้พิมพ์ออกมาอยู่หน้าเดียวกันได้ตามที่ผู้ใช้แจ้งแก้ไข (2026-07)
    if section_s_uri and section_l_uri:
        detail_block_html = f'''<div id="tw-detail-block">
<h2 class="page-break">9. รูปขยายรายละเอียดการเสริมเหล็ก — รูปตัด (Cross-section)</h2>
<div class="tw-sections">
  <div class="center detail-frame">
    <img class="detail detail-lg" src="{section_s_uri}" alt="Two way slab short-direction section">
  </div>
  <div class="center detail-frame">
    <img class="detail detail-lg" src="{section_l_uri}" alt="Two way slab long-direction section">
  </div>
</div>
'''
        if plan_uri:
            detail_block_html += f'''<h2>10. รูปขยายรายละเอียดการเสริมเหล็ก — แปลน (Plan)</h2>
<div class="center detail-frame tw-plan-frame">
  <img class="detail detail-lg" src="{plan_uri}" alt="Two way slab reinforcement plan">
</div>
'''
        detail_block_html += "</div>"
    elif plan_uri:
        detail_block_html = f'''<h2 class="page-break">10. รูปขยายรายละเอียดการเสริมเหล็ก — แปลน (Plan)</h2>
<div class="center detail-frame tw-plan-frame">
  <img class="detail detail-lg" src="{plan_uri}" alt="Two way slab reinforcement plan">
</div>'''
    else:
        detail_block_html = ""

    html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>รายการคำนวณ {slab_name}</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ margin: 0; }}
    /* ข้อ 9-10 (รูปตัด + แปลน) ให้อยู่หน้าเดียวกันตอนพิมพ์: จำกัดความสูงรูปโดยตรง
       (max-height, สเกลตามสัดส่วนอัตโนมัติ) แทนการพึ่งพา flex เรียงข้างกัน — วิธีนี้ทำงาน
       แน่นอนกว่าไม่ว่าจะพิมพ์จากเบราว์เซอร์ไหน ข้อ 10 (แปลน) ความสำคัญรองจากข้อ 9
       (รูปตัด) จึงย่อเล็กกว่า ตามที่ผู้ใช้แจ้งแก้ไข (2026-07) */
    #tw-detail-block img.detail {{ max-height: 205px; width: auto; max-width: 100%; }}
    #tw-detail-block .tw-plan-frame img.detail {{ max-height: 480px; }}
    #tw-detail-block h2 {{ margin-top: 3px; margin-bottom: 3px; }}
    #tw-detail-block .detail-frame {{ padding: 3px; margin-top: 3px; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; font-size: 13.5px; color: #111;
          max-width: 780px; margin: 14px auto; padding: 0 14px; line-height: 1.35; }}
  h2 {{ font-size: 13.5px; background:#dbe7f5; padding: 3px 8px; margin: 10px 0 4px 0; border-left: 4px solid #2563eb; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #999; padding: 3px 7px; font-size: 12.5px; }}
  th {{ background: #eee; text-align: left; }}
  .row3 {{ display: flex; gap: 10px; margin-bottom: 4px; }}
  .row3 > div {{ flex: 1; }}
  .mini-table td, .mini-table th {{ padding: 2px 6px; font-size: 12px; }}
  .ok {{ color: #0a7a0a; font-weight: bold; }}
  .ng {{ color: #b30000; font-weight: bold; }}
  .drmk-table th {{ background: #dbe7f5; }}
  .drmk-table td.dv {{ color: #b45f06; }}
  .print-btn {{ background:#2563eb; color:white; border:none; padding:8px 18px;
                border-radius:6px; font-size:14px; cursor:pointer; }}
  img.detail {{ margin: 0 auto; display:block; }}
  img.detail-lg {{ max-width: 100%; }}
  img.detail-sm {{ max-width: 62%; }}
  .detail-frame {{ border: 1px solid #ccc; padding: 8px; margin: 4px 0 0 0; }}
  .center {{ text-align: center; }}
  .summary-line {{ font-size: 13px; margin: 6px 0 4px 0; padding: 4px 8px; border-radius: 4px; background:#f4f4f4; }}
  .page-break {{ page-break-before: always; break-before: page; }}
{REPORT_HEADER_CSS}
</style>
</head>
<body>

<div class="no-print" style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
  <span style="font-size:16px; font-weight:bold; color:#111;">รายการคำนวณ</span>
  <button class="print-btn" onclick="window.print()">🖨️ พิมพ์รายการคำนวณ</button>
</div>

{header_html}

<div class="row3">
  <div>
    <table class="mini-table">
      <tr><th colspan="3">1. คุณสมบัติวัสดุ</th></tr>
      <tr><td>f'c</td><td>{inp.fc_ksc:.0f}</td><td>ksc.</td></tr>
      <tr><td>ชั้นคุณภาพเหล็ก (แนวสั้น)</td><td colspan="2">{inp.short_steel_type} (fy={GS_STEEL_FY_KSC[inp.short_steel_type]:.0f})</td></tr>
      <tr><td>ชั้นคุณภาพเหล็ก (แนวยาว)</td><td colspan="2">{inp.long_steel_type} (fy={GS_STEEL_FY_KSC[inp.long_steel_type]:.0f})</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">2. น้ำหนักบรรทุก</th></tr>
      <tr><td>Dead Load</td><td>{result.dead_load_kg_m2:.0f}</td><td>kg/m²</td></tr>
      <tr><td>SDL / LL</td><td>{inp.wD_kg_m2:.0f} / {inp.wL_kg_m2:.0f}</td><td>kg/m²</td></tr>
      <tr><td><b>Wu</b></td><td><b>{result.wu_kg_m2:.0f}</b></td><td>kg/m²</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">3. ขนาดพื้น</th></tr>
      <tr><td>S / L</td><td>{inp.S_m:.2f} / {inp.L_m:.2f}</td><td>m.</td></tr>
      <tr><td>t</td><td>{inp.t_cm:.1f}</td><td>cm.</td></tr>
      <tr><td>m=S/L</td><td>{result.m_ratio:.3f}</td>
          <td class="{ok_class(result.two_way_ok)}">{ok_th(result.two_way_ok)}</td></tr>
    </table>
  </div>
</div>

<h2>4. กรณีขอบเขตพื้น &amp; ความหนาต่ำสุด</h2>
<table class="mini-table">
  <tr><th>กรณี</th><td colspan="3">{case['label_th']}</td></tr>
  <tr><td>tmin = (2S<sub>cm</sub>+2L<sub>cm</sub>)/180</td><td>{result.tmin_cm:.2f}</td><td>cm.</td>
      <td class="{ok_class(result.t_ok)}">{ok_th(result.t_ok)}</td></tr>
</table>

<h2>5. โมเมนต์ &amp; เหล็กเสริม — ทิศทางสั้น (Short Direction)</h2>
<table class="mini-table">
  <tr><th>ตำแหน่ง</th><th>Coeff. C</th><th>Mu (kg-m/m)</th><th>&rho; ที่ใช้</th><th>As ต้องการ (cm²/m)</th></tr>
  {pos_rows(result.short_positions)}
  <tr><th colspan="4">เหล็กที่ใช้จริง</th><th>{result.reinf_label_short}</th></tr>
  <tr><td colspan="2">As ต้องการสูงสุด (รวม Ast ขั้นต่ำ 0.002bt)</td><td>{result.as_req_short_cm2_m:.2f} cm²/m</td>
      <td>As ที่ใช้จริง</td><td>{result.as_provided_short_cm2_m:.2f} cm²/m</td></tr>
  <tr><td colspan="2">ระยะห่างสูงสุดที่ยอมให้</td><td>{result.short_spacing_max_cm:.1f} cm.</td>
      <th>ผลตรวจสอบ</th><th class="{ok_class(result.short_reinf_ok)}">{ok_th(result.short_reinf_ok)}</th></tr>
</table>

<h2>6. โมเมนต์ &amp; เหล็กเสริม — ทิศทางยาว (Long Direction)</h2>
<table class="mini-table">
  <tr><th>ตำแหน่ง</th><th>Coeff. C</th><th>Mu (kg-m/m)</th><th>&rho; ที่ใช้</th><th>As ต้องการ (cm²/m)</th></tr>
  {pos_rows(result.long_positions)}
  <tr><th colspan="4">เหล็กที่ใช้จริง</th><th>{result.reinf_label_long}</th></tr>
  <tr><td colspan="2">As ต้องการสูงสุด (รวม Ast ขั้นต่ำ 0.002bt)</td><td>{result.as_req_long_cm2_m:.2f} cm²/m</td>
      <td>As ที่ใช้จริง</td><td>{result.as_provided_long_cm2_m:.2f} cm²/m</td></tr>
  <tr><td colspan="2">ระยะห่างสูงสุดที่ยอมให้</td><td>{result.long_spacing_max_cm:.1f} cm.</td>
      <th>ผลตรวจสอบ</th><th class="{ok_class(result.long_reinf_ok)}">{ok_th(result.long_reinf_ok)}</th></tr>
</table>

<h2>7. ตรวจสอบแรงเฉือน (Shear Check)</h2>
<table class="mini-table drmk-table">
  <tr><th>Data</th><th>Value</th><th>Unit</th></tr>
  <tr><td>Vu&nbsp;=&nbsp;1.15&middot;Wu&middot;S/4</td>
      <td class="dv">{result.vu_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>&phi;<sub>v</sub>Vc&nbsp;=&nbsp;&phi;<sub>v</sub>&middot;0.53(&radic;fc')bd</td>
      <td class="dv">{result.phi_vc_kg:.2f} <span class="{ok_class(result.shear_ok)}">&lt;&lt; [{ok_en(result.shear_ok)}]</span></td>
      <td class="dv">kg.</td></tr>
  <tr><td>(2/3)&phi;<sub>v</sub>Vc <span style="color:#888;">(เกณฑ์เสริม — ที่มายังไม่ยืนยัน)</span></td>
      <td class="dv">{(2.0/3.0)*result.phi_vc_kg:.2f} <span class="{ok_class(result.shear_ok_secondary)}">&lt;&lt; [{ok_en(result.shear_ok_secondary)}]</span></td>
      <td class="dv">kg.</td></tr>
</table>

<h2>8. ถ่ายน้ำหนักลงคาน (Load Transfer to the Beam, Service)</h2>
<table class="mini-table drmk-table">
  <tr><th>Data</th><th>Short Span (w&middot;S/3)</th><th>Long Span (w&middot;S/2&middot;(1-m&sup2;/3))</th><th>Unit</th></tr>
  <tr><td>Dead Load on Beam</td><td class="dv">{result.dl_on_beam_triangular_kg_m:.2f}</td>
      <td class="dv">{result.dl_on_beam_trapezoidal_kg_m:.2f}</td><td class="dv">kg./m.</td></tr>
  <tr><td>Live Load on Beam</td><td class="dv">{result.ll_on_beam_triangular_kg_m:.2f}</td>
      <td class="dv">{result.ll_on_beam_trapezoidal_kg_m:.2f}</td><td class="dv">kg./m.</td></tr>
</table>
<p style="font-size:11px; color:#888; margin-top:2px;">
  หมายเหตุ: ทิศทางสั้น (S) ใช้พื้นที่รับน้ำหนักรูปสามเหลี่ยม (Triangular) —
  ทิศทางยาว (L) ใช้พื้นที่รับน้ำหนักรูปคางหมู (Trapezoidal)
</p>

{detail_block_html}

</body>
</html>
"""
    return html


def build_cant_report_html(project: dict, inp, result, section_png: bytes, plan_png: bytes = None,
                            project_info: dict = None, logo_bytes: bytes = None,
                            logo_mime: str = None) -> str:
    """
    project: dict with key slab_name.
    inp: modules.cantilever_slab.CantileverSlabInput
    result: modules.cantilever_slab.CantileverSlabResult
    section_png / plan_png: PNG bytes for the two detail drawings (cross-
    section + plan-view rebar layout) — see common/diagram.py
    draw_cant_section_png / draw_cant_plan_png.
    """
    section_uri = png_to_data_uri(section_png)
    plan_uri = png_to_data_uri(plan_png) if plan_png else None

    def ok_th(flag: bool) -> str:
        return "ผ่าน" if flag else "ไม่ผ่าน"

    def ok_class(flag: bool) -> str:
        return "ok" if flag else "ng"

    def ok_en(flag: bool) -> str:
        return "Ok" if flag else "NG"

    slab_name = project.get("slab_name", "S-01")
    header_html = build_report_header_html(
        project_info, logo_bytes, logo_mime,
        doc_label=f"พื้น : {slab_name}",
        subtitle="รายการคำนวณโดยวิธีกำลังตามกฎกระทรวง พ.ศ.2566 (พื้นยื่น — Cantilever Slab)",
    )

    over_html = ' <span class="ng">(หน้าตัดเล็กไป — เพิ่มความหนา)</span>' if result.over_reinforced else ""

    html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>รายการคำนวณ {slab_name}</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ margin: 0; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; font-size: 13.5px; color: #111;
          max-width: 780px; margin: 14px auto; padding: 0 14px; line-height: 1.35; }}
  h2 {{ font-size: 13.5px; background:#dbe7f5; padding: 3px 8px; margin: 10px 0 4px 0; border-left: 4px solid #2563eb; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #999; padding: 3px 7px; font-size: 12.5px; }}
  th {{ background: #eee; text-align: left; }}
  .row3 {{ display: flex; gap: 10px; margin-bottom: 4px; }}
  .row3 > div {{ flex: 1; }}
  .mini-table td, .mini-table th {{ padding: 2px 6px; font-size: 12px; }}
  .ok {{ color: #0a7a0a; font-weight: bold; }}
  .ng {{ color: #b30000; font-weight: bold; }}
  .drmk-table th {{ background: #dbe7f5; }}
  .drmk-table td.dv {{ color: #b45f06; }}
  .print-btn {{ background:#2563eb; color:white; border:none; padding:8px 18px;
                border-radius:6px; font-size:14px; cursor:pointer; }}
  img.detail {{ margin: 0 auto; display:block; }}
  img.detail-lg {{ max-width: 100%; }}
  img.detail-sm {{ max-width: 62%; }}
  .detail-frame {{ border: 1px solid #ccc; padding: 8px; margin: 4px 0 0 0; }}
  .center {{ text-align: center; }}
  .summary-line {{ font-size: 14px; margin: 6px 0 2px 0; }}
  .page-break {{ page-break-before: always; break-before: page; }}
{REPORT_HEADER_CSS}
</style>
</head>
<body>

<div class="no-print" style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
  <span style="font-size:16px; font-weight:bold; color:#111;">รายการคำนวณ</span>
  <button class="print-btn" onclick="window.print()">🖨️ พิมพ์รายการคำนวณ</button>
</div>

{header_html}

<div class="row3">
  <div>
    <table class="mini-table">
      <tr><th colspan="3">1. คุณสมบัติวัสดุ</th></tr>
      <tr><td>f'c</td><td>{inp.fc_ksc:.0f}</td><td>ksc.</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กหลัก</td><td colspan="2">{inp.main_steel_type} (fy={GS_STEEL_FY_KSC[inp.main_steel_type]:.0f})</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กเสริมรอง</td><td colspan="2">{inp.temp_steel_type} (fy={GS_STEEL_FY_KSC[inp.temp_steel_type]:.0f})</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">2. น้ำหนักบรรทุก</th></tr>
      <tr><td>Dead Load</td><td>{result.dead_load_kg_m2:.0f}</td><td>kg/m²</td></tr>
      <tr><td>SDL / LL</td><td>{inp.wD_kg_m2:.0f} / {inp.wL_kg_m2:.0f}</td><td>kg/m²</td></tr>
      <tr><td>Fin Wg. (ที่ปลายยื่น)</td><td>{inp.fin_wg_kg_m:.0f}</td><td>kg/m.</td></tr>
      <tr><td><b>Wu</b></td><td><b>{result.wu_kg_m2:.0f}</b></td><td>kg/m²</td></tr>
      <tr><td><b>FIN</b> (=1.4&middot;Fin Wg.)</td><td><b>{result.fin_kg_m:.0f}</b></td><td>kg/m.</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">3. ขนาดพื้น</th></tr>
      <tr><td>S (ความยาวยื่น)</td><td colspan="2">{inp.S_m:.2f} m.</td></tr>
      <tr><td>t</td><td colspan="2">{inp.t_cm:.1f} cm.</td></tr>
    </table>
  </div>
</div>

<h2>4. ความหนาต่ำสุด (Minimum Thickness)</h2>
<table class="mini-table">
  <tr><td>tmin = (S/{CANT_TMIN_DENOM:.0f}) &times; (0.40+fy/7000)</td><td>{result.tmin_cm:.2f}</td><td>cm.</td>
      <td class="{ok_class(result.t_ok)}">{ok_th(result.t_ok)}</td></tr>
</table>

<h2>5. โมเมนต์ &amp; เหล็กเสริมหลัก (ที่จุดรองรับ, โมเมนต์ลบสูงสุด)</h2>
<table class="mini-table">
  <tr><th>ตำแหน่ง</th><th>Mu (kg-m/m)</th><th>Ru (ksc)</th><th>&rho; ที่ใช้</th><th>As ต้องการ (cm²/m)</th></tr>
  <tr><td>จุดรองรับ (Fixed End)</td><td>{result.mu_kgm:.0f}</td><td>{result.ru_ksc:.2f}</td>
      <td>{result.rho_used:.4f}</td><td>{result.as_req_flexure_cm2_m:.2f}{over_html}</td></tr>
  <tr><th colspan="4">เหล็กที่ใช้จริง</th><th>{result.reinf_label_main}</th></tr>
  <tr><td colspan="2">As ต้องการสูงสุด (รวม Ast ขั้นต่ำ 0.002bt = {result.ast_min_main_cm2_m:.2f})</td>
      <td>{result.as_req_governing_cm2_m:.2f} cm²/m</td>
      <td>As ที่ใช้จริง</td><td>{result.as_provided_cm2_m:.2f} cm²/m</td></tr>
  <tr><td colspan="2">ระยะห่างสูงสุดที่ยอมให้ (min[As-based, 3t, 45cm])</td><td>{result.main_spacing_max_cm:.1f} cm.</td>
      <th>ผลตรวจสอบ</th><th class="{ok_class(result.main_reinf_ok)}">{ok_th(result.main_reinf_ok)}</th></tr>
</table>

<h2>6. เหล็กเสริมรอง — กระจายแรง/กันร้าว (ขนานแนวจุดรองรับ)</h2>
<table class="mini-table">
  <tr><td>Ast ต้องการ (0.0025bt, SR24)</td><td>{result.ast_req_cm2_m:.2f}</td><td>cm²/m</td>
      <td>เหล็กที่ใช้จริง</td><td>{result.reinf_label_temp} = {result.ast_provided_cm2_m:.2f} cm²/m</td></tr>
  <tr><td>ระยะห่างสูงสุดที่ยอมให้ (min[Ast-based, 5t, 45cm])</td><td>{result.temp_spacing_max_cm:.1f}</td><td>cm.</td>
      <th>ผลตรวจสอบ</th><th class="{ok_class(result.temp_reinf_ok)}">{ok_th(result.temp_reinf_ok)}</th></tr>
</table>

<h2>7. ตรวจสอบแรงเฉือน (Shear Check, ที่หน้าตัดรองรับ)</h2>
<table class="mini-table drmk-table">
  <tr><th>Data</th><th>Value</th><th>Unit</th></tr>
  <tr><td>Vu&nbsp;&nbsp;=&nbsp;1.15(WuS+FIN)</td>
      <td class="dv">{result.vu_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>&phi;<sub>v</sub>Vc&nbsp;=&nbsp;&phi;<sub>v</sub>&middot;0.53(&radic;fc')bd</td>
      <td class="dv">{result.phi_vc_kg:.2f} <span class="{ok_class(result.shear_ok)}">&lt;&lt; [{ok_en(result.shear_ok)}]</span></td>
      <td class="dv">kg.</td></tr>
</table>

<h2>8. ถ่ายน้ำหนักลงคาน/ผนัง (Load Transfer to the Beam, Service)</h2>
<table class="mini-table drmk-table">
  <tr><th>Data</th><th>Value</th><th>Unit</th></tr>
  <tr><td>Dead Load on Beam &nbsp;=&nbsp;(DL+SDL)&middot;S</td><td class="dv">{result.dl_on_beam_kg_m:.2f}</td><td class="dv">kg./m.</td></tr>
  <tr><td>Live Load on Beam &nbsp;=&nbsp;LL&middot;S</td><td class="dv">{result.ll_on_beam_kg_m:.2f}</td><td class="dv">kg./m.</td></tr>
</table>
<p style="font-size:11px; color:#888; margin-top:2px;">
  หมายเหตุ: พื้นยื่นมีจุดรองรับเดียว น้ำหนักที่ถ่ายลงคาน/ผนังจึงเป็นค่าเต็ม tributary (ไม่แบ่งครึ่ง
  เหมือนพื้นทางเดียว)
</p>

<h2 class="page-break">9. รูปขยายรายละเอียดการเสริมเหล็ก — รูปตัด (Cross-section)</h2>
<div class="center detail-frame">
  <img class="detail detail-lg" src="{section_uri}" alt="Cantilever slab section detail">
</div>

{f'''<h2>10. รูปขยายรายละเอียดการเสริมเหล็ก — แปลน (Plan)</h2>
<div class="center detail-frame">
  <img class="detail detail-lg" src="{plan_uri}" alt="Cantilever slab plan detail">
</div>''' if plan_uri else ""}

</body>
</html>
"""
    return html


def build_beam_report_html(project: dict, inp, result, sfd_bmd_png: bytes, section_png: bytes,
                            project_info: dict = None, logo_bytes: bytes = None,
                            logo_mime: str = None) -> str:
    """
    project: dict with key beam_name.
    inp: modules.beam_single_span.BeamSingleSpanInput
    result: modules.beam_single_span.BeamSingleSpanResult
    sfd_bmd_png / section_png: PNG bytes — see common/diagram.py
    draw_beam_sfd_bmd_png / draw_beam_section_png.
    """
    sfd_bmd_uri = png_to_data_uri(sfd_bmd_png)
    section_uri = png_to_data_uri(section_png)

    def ok_th(flag: bool) -> str:
        return "ผ่าน" if flag else "ไม่ผ่าน"

    def ok_class(flag: bool) -> str:
        return "ok" if flag else "ng"

    def ok_en(flag: bool) -> str:
        return "Ok" if flag else "NG"

    beam_name = project.get("beam_name", "B-01")
    header_html = build_report_header_html(
        project_info, logo_bytes, logo_mime,
        doc_label=f"คาน : {beam_name}",
        subtitle="รายการคำนวณโดยวิธีกำลังตามกฎกระทรวง พ.ศ.2566 (คานช่วงเดียว — Single-span Beam)",
    )

    if inp.point_loads:
        pt_rows = "".join(
            f"<tr><td>จุดที่ {i + 1}</td><td>{p.x_m:.2f}</td><td>{p.p_dl_kg:.0f}</td>"
            f"<td>{p.p_ll_kg:.0f}</td><td>{pu:.0f}</td></tr>"
            for i, (p, (x, pu)) in enumerate(zip(sorted(inp.point_loads, key=lambda q: q.x_m), result.pu_loads))
        )
        point_load_table = f'''<h2>3. น้ำหนักจุด (Point Loads)</h2>
<table class="mini-table">
  <tr><th>ตำแหน่ง</th><th>ระยะจากจุดรองรับซ้าย (m.)</th><th>P_DL (kg.)</th><th>P_LL (kg.)</th><th>Pu (kg.)</th></tr>
  {pt_rows}
</table>'''
    else:
        point_load_table = ""

    bottom_doubly_html = ""
    if result.bottom.doubly_reinforced:
        bottom_doubly_html = f'''
  <tr><th colspan="5">เสริมเหล็กสองชั้น (Doubly-reinforced) — หน้าตัดเดียวรับโมเมนต์เกิน Ru,max</th></tr>
  <tr><td>Mu1 (รับได้ที่ &rho;max)</td><td colspan="2">{result.bottom.mu1_kgm:.0f} kg-m.</td>
      <td>Mu2 (ส่วนเกิน)</td><td>{result.bottom.mu2_kgm:.0f} kg-m.</td></tr>
  <tr><td colspan="2">As2 (เหล็กรับแรงอัดที่ต้องเพิ่ม, สมมติ f<sub>s</sub>&prime;=fy)</td>
      <td colspan="3">{result.bottom.as_comp_req_cm2:.2f} cm&sup2;</td></tr>'''

    layer_warn_html = ""
    if result.bottom.n_layers > 1:
        breakdown = "+".join(str(n) for n in result.bottom.bars_per_layer if n > 0)
        layer_warn_html += (f'<p style="font-size:11.5px; color:#555;">'
                             f'&#8505; เหล็กล่างเกินกว่าจะใส่ได้ใน 1 ชั้น (ใส่ได้สูงสุด {result.bottom.max_bars_single_layer} '
                             f'เส้น/ชั้น ที่ความกว้างคานนี้) — จัดเป็น {result.bottom.n_layers} ชั้นอัตโนมัติตามมาตรฐาน '
                             f'({breakdown} เส้น) — d ที่ใช้ออกแบบจริงคำนวณจาก centroid ของเหล็กทุกชั้นแล้ว</p>')
    if not result.bottom.reinf_ok:
        layer_warn_html += (f'<p class="ng" style="font-size:11.5px;">'
                             f'&#9888; จำนวนเหล็กที่ต้องการ ({result.bottom.n_bars_req} เส้น) '
                             f'เกินกว่าจะใส่ได้แม้จัด {MAX_LAYERS} ชั้นแล้ว (สูงสุด {result.bottom.max_bars_single_layer * MAX_LAYERS} เส้น '
                             f'ที่ความกว้างคานนี้) — กรุณาขยายความกว้างคาน หรือเปลี่ยนขนาดเหล็กให้ใหญ่ขึ้น</p>')

    section_too_small_html = ""
    if result.stirrup.section_too_small:
        section_too_small_html = ('<p class="ng" style="font-size:11.5px;">&#9888; '
                                   'Vs ที่ต้องการเกินขีดจำกัด 2.1&radic;fc&prime;bd — หน้าตัดคานเล็กเกินไป '
                                   'สำหรับแรงเฉือนนี้ กรุณาขยายขนาดคาน (b หรือ h)</p>')

    html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>รายการคำนวณ {beam_name}</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ margin: 0; }}
    #beam-detail-block img.detail.detail-lg {{ max-height: 560px; width: auto; max-width: 100%; }}
    #beam-detail-block img.detail.detail-sm {{ max-height: 280px; width: auto; max-width: 100%; }}
    #beam-detail-block h2 {{ margin-top: 3px; margin-bottom: 3px; }}
    #beam-detail-block .detail-frame {{ padding: 3px; margin-top: 3px; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; font-size: 13.5px; color: #111;
          max-width: 780px; margin: 14px auto; padding: 0 14px; line-height: 1.35; }}
  h2 {{ font-size: 13.5px; background:#dbe7f5; padding: 3px 8px; margin: 10px 0 4px 0; border-left: 4px solid #2563eb; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #999; padding: 3px 7px; font-size: 12.5px; }}
  th {{ background: #eee; text-align: left; }}
  .row3 {{ display: flex; gap: 10px; margin-bottom: 4px; }}
  .row3 > div {{ flex: 1; }}
  .mini-table td, .mini-table th {{ padding: 2px 6px; font-size: 12px; }}
  .ok {{ color: #0a7a0a; font-weight: bold; }}
  .ng {{ color: #b30000; font-weight: bold; }}
  .drmk-table th {{ background: #dbe7f5; }}
  .drmk-table td.dv {{ color: #b45f06; }}
  .print-btn {{ background:#2563eb; color:white; border:none; padding:8px 18px;
                border-radius:6px; font-size:14px; cursor:pointer; }}
  img.detail {{ margin: 0 auto; display:block; }}
  img.detail-lg {{ max-width: 100%; }}
  img.detail-sm {{ max-width: 62%; }}
  .detail-frame {{ border: 1px solid #ccc; padding: 8px; margin: 4px 0 0 0; }}
  .center {{ text-align: center; }}
  .summary-line {{ font-size: 14px; margin: 6px 0 2px 0; }}
  .page-break {{ page-break-before: always; break-before: page; }}
{REPORT_HEADER_CSS}
</style>
</head>
<body>

<div class="no-print" style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
  <span style="font-size:16px; font-weight:bold; color:#111;">รายการคำนวณ</span>
  <button class="print-btn" onclick="window.print()">🖨️ พิมพ์รายการคำนวณ</button>
</div>

{header_html}

<div class="row3">
  <div>
    <table class="mini-table">
      <tr><th colspan="3">1. คุณสมบัติวัสดุ</th></tr>
      <tr><td>f'c</td><td colspan="2">{inp.fc_ksc:.0f} ksc.</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กหลัก</td><td colspan="2">{inp.main_steel_type} (fy={GS_STEEL_FY_KSC[inp.main_steel_type]:.0f})</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กปลอก</td><td colspan="2">{inp.stirrup_steel_type} (fy={GS_STEEL_FY_KSC[inp.stirrup_steel_type]:.0f})</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">2. ขนาดคาน &amp; น้ำหนักแผ่กระจาย</th></tr>
      <tr><td>b &times; h</td><td colspan="2">{inp.b_cm:.0f} &times; {inp.h_cm:.0f} cm.</td></tr>
      <tr><td>ช่วงคาน L</td><td colspan="2">{inp.L_m:.2f} m.</td></tr>
      <tr><td>น้ำหนักตัวเอง (Self weight)</td><td colspan="2">{result.self_weight_kg_m:.0f} kg/m.</td></tr>
      <tr><td>Line Load DL / LL</td><td colspan="2">{inp.line_load_dl_kg_m:.0f} / {inp.line_load_ll_kg_m:.0f} kg/m.</td></tr>
      <tr><td><b>Wu</b> = 1.4(DL+SW)+1.7LL</td><td colspan="2"><b>{result.wu_kg_m:.0f}</b> kg/m.</td></tr>
    </table>
  </div>
</div>

{point_load_table}

<h2>4. ผลการวิเคราะห์หาแรง (Structural Analysis)</h2>
<table class="mini-table drmk-table">
  <tr><th>Data</th><th>Value</th><th>Unit</th></tr>
  <tr><td>R (จุดรองรับซ้าย)</td><td class="dv">{result.r_left_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>R (จุดรองรับขวา)</td><td class="dv">{result.r_right_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>Vu,max</td><td class="dv">{result.vu_max_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>Mu,max (ที่ x={result.mu_max_x_m:.2f} m. จากจุดรองรับซ้าย)</td>
      <td class="dv">{result.mu_max_kg_m:.2f}</td><td class="dv">kg-m.</td></tr>
</table>

<h2>5. เหล็กเสริมล่าง (Bottom Bars — ตามโมเมนต์บวกสูงสุด)</h2>
<table class="mini-table">
  <tr><th>Mu (kg-m.)</th><th>d (cm.)</th><th>Ru (ksc)</th><th>&rho; ที่ใช้</th><th>As ต้องการ (cm&sup2;)</th></tr>
  <tr><td>{result.bottom.mu_kgm:.0f}</td><td>{result.bottom.d_cm:.2f}</td><td>{result.bottom.ru_ksc:.2f}</td>
      <td>{result.bottom.rho_used:.4f}</td><td>{result.bottom.as_req_cm2:.2f}</td></tr>
  {bottom_doubly_html}
  <tr><th colspan="4">เหล็กที่ใช้จริง</th><th>{result.reinf_label_bottom}</th></tr>
  <tr><td colspan="2">จำนวนเหล็กที่ต้องการ</td><td>{result.bottom.n_bars_req} เส้น</td>
      <td>As ที่ใช้จริง</td><td>{result.bottom.as_provided_cm2:.2f} cm&sup2;</td></tr>
  <tr><td colspan="4"></td><th class="{ok_class(result.bottom.reinf_ok)}">{ok_th(result.bottom.reinf_ok)}</th></tr>
</table>
{layer_warn_html}

<h2>6. เหล็กเสริมบน (Top Bars — เหล็กยึดเหล็กปลอกขั้นต่ำ)</h2>
<table class="mini-table">
  <tr><td colspan="2">คานช่วงเดียวแบบยึดหมุนทั้งสองด้าน (simply supported) ไม่มีโมเมนต์ลบที่จุดรองรับ —
      เหล็กบนใช้เป็นเหล็กยึดเหล็กปลอก (hanger bars) ขั้นต่ำเท่านั้น</td>
      <th>เหล็กที่ใช้จริง</th><th colspan="2">{result.reinf_label_top}</th></tr>
</table>

<h2>7. ออกแบบเหล็กปลอก (Stirrup Design)</h2>
<table class="mini-table drmk-table">
  <tr><th>Data</th><th>Value</th><th>Unit</th></tr>
  <tr><td>Vu,max</td><td class="dv">{result.stirrup.vu_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>&phi;<sub>v</sub>Vc&nbsp;=&nbsp;&phi;<sub>v</sub>&middot;0.53(&radic;fc&prime;)bd</td>
      <td class="dv">{result.stirrup.phi_vc_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>Vs ต้องการ&nbsp;=&nbsp;Vu/&phi;<sub>v</sub> &minus; Vc</td>
      <td class="dv">{result.stirrup.vs_req_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>&phi;&middot;1.1(&radic;fc&prime;)bd</td><td class="dv">{result.stirrup.limit_1p1_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>&phi;&middot;2.1(&radic;fc&prime;)bd</td><td class="dv">{result.stirrup.limit_2p1_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>ระยะห่างสูงสุดที่คำนวณได้ (S_max)</td><td class="dv">{result.stirrup.s_max_cm:.1f}</td><td class="dv">cm.</td></tr>
  <tr><th colspan="2">เหล็กปลอกที่ใช้จริง</th><th colspan="1">{result.reinf_label_stirrup}</th></tr>
  <tr><td colspan="2">ผลตรวจสอบ</td>
      <td class="{ok_class(result.stirrup.stirrup_ok)}">{ok_th(result.stirrup.stirrup_ok)}</td></tr>
</table>
{section_too_small_html}

<div id="beam-detail-block">
<h2 class="page-break">8. กราฟแรงเฉือน &amp; โมเมนต์ (SFD/BMD)</h2>
<div class="center detail-frame">
  <img class="detail detail-lg" src="{sfd_bmd_uri}" alt="Beam SFD/BMD">
</div>

<h2>9. รูปตัดคาน (Beam Section)</h2>
<div class="center detail-frame">
  <img class="detail detail-sm" src="{section_uri}" alt="Beam cross-section">
</div>
</div>

</body>
</html>
"""
    return html


def build_continuous_beam_report_html(project: dict, inp, result, elevation_png: bytes, sfd_bmd_png: bytes,
                                       midspan_section_png: bytes = None, support_section_png: bytes = None,
                                       project_info: dict = None, logo_bytes: bytes = None,
                                       logo_mime: str = None) -> str:
    """
    project: dict with key beam_name.
    inp: modules.continuous_beam.ContinuousBeamInput
    result: modules.continuous_beam.ContinuousBeamResult
    elevation_png / sfd_bmd_png: PNG bytes — see common/diagram.py
    draw_continuous_beam_elevation_png / draw_continuous_beam_sfd_bmd_png.
    midspan_section_png / support_section_png: PNG bytes จาก draw_beam_section_png — รูปตัด
    รายละเอียดการเสริมเหล็กตัวแทน "กลางคาน" (ช่วงที่มีเหล็กล่างมากสุด, result.governing_span_index)
    และ "จุดรองรับ/หัวเสา" (จุดที่มี |M| มากสุด, result.governing_support_index)
    """
    elevation_uri = png_to_data_uri(elevation_png)
    sfd_bmd_uri = png_to_data_uri(sfd_bmd_png)
    midspan_section_uri = png_to_data_uri(midspan_section_png) if midspan_section_png else None
    support_section_uri = png_to_data_uri(support_section_png) if support_section_png else None

    def ok_th(flag: bool) -> str:
        return "ผ่าน" if flag else "ไม่ผ่าน"

    def ok_class(flag: bool) -> str:
        return "ok" if flag else "ng"

    beam_name = project.get("beam_name", "B-01")
    header_html = build_report_header_html(
        project_info, logo_bytes, logo_mime,
        doc_label=f"คาน : {beam_name}",
        subtitle="รายการคำนวณโดยวิธีกำลังตามกฎกระทรวง พ.ศ.2566 (คานต่อเนื่อง — Continuous Beam)",
    )

    n_spans = len(result.spans)
    has_left = result.left_overhang is not None
    has_right = result.right_overhang is not None

    # --- 2. ผังคาน (layout table: overhang ซ้าย + ทุกช่วง + overhang ขวา) ---
    layout_rows = []
    if has_left:
        ov = result.left_overhang
        layout_rows.append(
            f"<tr><td>ปลายยื่นซ้าย (OH-L)</td><td>{ov.length_m:.2f}</td>"
            f"<td>{ov.wu_kg_m:.0f}</td><td>{len(ov.pu_loads)}</td></tr>"
        )
    for i, sp in enumerate(result.spans):
        layout_rows.append(
            f"<tr><td>ช่วงที่ {i + 1} (S{i}-S{i + 1})</td><td>{sp.length_m:.2f}</td>"
            f"<td>{sp.wu_kg_m:.0f}</td><td>{len(sp.pu_loads)}</td></tr>"
        )
    if has_right:
        ov = result.right_overhang
        layout_rows.append(
            f"<tr><td>ปลายยื่นขวา (OH-R)</td><td>{ov.length_m:.2f}</td>"
            f"<td>{ov.wu_kg_m:.0f}</td><td>{len(ov.pu_loads)}</td></tr>"
        )
    layout_table = f'''<h2>2. ผังคาน (Beam Layout)</h2>
<div class="center detail-frame">
  <img class="detail detail-elev" src="{elevation_uri}" alt="Beam elevation">
</div>
<table class="mini-table">
  <tr><th>ตำแหน่ง</th><th>ความยาว (m.)</th><th>Wu (kg/m.)</th><th>จำนวนจุดแรง</th></tr>
  {"".join(layout_rows)}
</table>'''

    # --- 3. โมเมนต์ & แรงปฏิกิริยาที่จุดรองรับ ---
    support_rows = []
    for s in result.supports:
        suffix = ""
        if s.is_exterior and s.has_overhang:
            suffix = " (มีปลายยื่น)"
        elif s.is_exterior:
            suffix = " (ริม)"
        support_rows.append(
            f"<tr><td>S{s.index}{suffix}</td><td class='dv'>{s.moment_kgm:+.2f}</td>"
            f"<td class='dv'>{s.reaction_kg:.2f}</td></tr>"
        )
    support_table = f'''<h2>3. โมเมนต์ &amp; แรงปฏิกิริยาที่จุดรองรับ (Support Moments &amp; Reactions)</h2>
<table class="mini-table drmk-table">
  <tr><th>จุดรองรับ</th><th>M (kg-m.)</th><th>R (kg.)</th></tr>
  {"".join(support_rows)}
</table>'''

    # --- 4. เหล็กเสริมล่าง (บวก) ต่อช่วง — รายละเอียดครบ (d, Ru, rho, As_req, As_provided) ---
    warnings = []
    bottom_rows = []
    for i, sp in enumerate(result.spans):
        b = sp.bottom
        label = reinf_label_with_layers(b, result.main_bar_type, inp.main_bar_dia_mm)
        bottom_rows.append(
            f"<tr><td>ช่วงที่ {i + 1}</td><td>{sp.mu_pos_max_kgm:.0f}</td>"
            f"<td>{sp.mu_pos_max_x_m:.2f}</td><td>{b.d_cm:.2f}</td><td>{b.ru_ksc:.2f}</td>"
            f"<td>{b.rho_used:.4f}</td><td>{b.as_req_cm2:.2f}</td><td>{b.as_provided_cm2:.2f}</td>"
            f"<td>{label}</td><td class='{ok_class(b.reinf_ok)}'>{ok_th(b.reinf_ok)}</td></tr>"
        )
        if b.n_layers > 1:
            warnings.append(f"ช่วงที่ {i + 1}: เหล็กล่างเกิน 1 ชั้น จัดเป็น {b.n_layers} ชั้น "
                             f"({'+'.join(str(n) for n in b.bars_per_layer if n > 0)} เส้น) — d ที่ใช้จริงลดลงตามระยะ centroid")
        if not b.reinf_ok:
            warnings.append(f"ช่วงที่ {i + 1}: เหล็กล่างที่ต้องการ ({b.n_bars_req} เส้น) "
                             f"เกินกว่าจะใส่ได้แม้จัด {MAX_LAYERS} ชั้นแล้ว (สูงสุด {b.max_bars_single_layer * 3} เส้น) — กรุณาขยายขนาดคาน/เปลี่ยนขนาดเหล็ก")
        if b.doubly_reinforced:
            warnings.append(f"ช่วงที่ {i + 1}: โมเมนต์เกิน Ru,max ต้องเสริมเหล็กสองชั้น "
                             f"(As2={b.as_comp_req_cm2:.2f} cm&sup2;)")
    bottom_table = f'''<h2>4. เหล็กเสริมล่าง (Bottom Bars — ตามโมเมนต์บวกสูงสุดแต่ละช่วง)</h2>
<table class="mini-table">
  <tr><th>ช่วง</th><th>Mu+ (kg-m.)</th><th>ที่ x (m.)</th><th>d (cm.)</th><th>Ru (ksc)</th>
      <th>&rho; ที่ใช้</th><th>As ต้องการ (cm&sup2;)</th><th>As ที่ใช้จริง (cm&sup2;)</th><th>เหล็กที่ใช้</th><th>ผล</th></tr>
  {"".join(bottom_rows)}
</table>'''

    # --- 5. เหล็กเสริมบน (ลบ) ต่อจุดรองรับ (ข้ามจุดรองรับริมที่ไม่มี overhang และ M=0) ---
    top_rows = []
    for s in result.supports:
        is_nominal = abs(s.moment_kgm) < 1e-6
        if s.is_exterior and not s.has_overhang:
            continue   # จุดรองรับริมไม่มี overhang และไม่มีโมเมนต์ลบจริง — ข้าม (เหมือน hanger bar เหล็กบนช่วงเดียว ไม่ต้องคำนวณซ้ำที่นี่)
        t = s.top
        label = reinf_label_with_layers(t, result.main_bar_type, inp.main_bar_dia_mm)
        as_req_disp = "0.00 (nominal)" if is_nominal else f"{t.as_req_cm2:.2f}"
        ru_disp = "-" if is_nominal else f"{t.ru_ksc:.2f}"
        rho_disp = "-" if is_nominal else f"{t.rho_used:.4f}"
        top_rows.append(
            f"<tr><td>S{s.index}</td><td>{abs(s.moment_kgm):.0f}</td><td>{t.d_cm:.2f}</td>"
            f"<td>{ru_disp}</td><td>{rho_disp}</td>"
            f"<td>{as_req_disp}</td><td>{t.as_provided_cm2:.2f}</td><td>{label}</td>"
            f"<td class='{ok_class(t.reinf_ok)}'>{ok_th(t.reinf_ok)}</td></tr>"
        )
        if t.n_layers > 1:
            warnings.append(f"S{s.index}: เหล็กบนเกิน 1 ชั้น จัดเป็น {t.n_layers} ชั้น "
                             f"({'+'.join(str(n) for n in t.bars_per_layer if n > 0)} เส้น) — d ที่ใช้จริงลดลงตามระยะ centroid")
        if not t.reinf_ok:
            warnings.append(f"S{s.index}: เหล็กบนที่ต้องการ ({t.n_bars_req} เส้น) "
                             f"เกินกว่าจะใส่ได้แม้จัด {MAX_LAYERS} ชั้นแล้ว (สูงสุด {t.max_bars_single_layer * 3} เส้น) — กรุณาขยายขนาดคาน/เปลี่ยนขนาดเหล็ก")
    top_table = f'''<h2>5. เหล็กเสริมบน (Top Bars — ตามโมเมนต์ลบที่จุดรองรับ)</h2>
<table class="mini-table">
  <tr><th>จุดรองรับ</th><th>|M| (kg-m.)</th><th>d (cm.)</th><th>Ru (ksc)</th><th>&rho; ที่ใช้</th>
      <th>As ต้องการ (cm&sup2;)</th><th>As ที่ใช้จริง (cm&sup2;)</th><th>เหล็กที่ใช้</th><th>ผล</th></tr>
  {"".join(top_rows)}
</table>
<p style="font-size:11px; color:#666;">* จุดรองรับริมที่ไม่มีปลายยื่น ไม่มีโมเมนต์ลบจริง (M&asymp;0) — เหล็กบนใช้เป็นเหล็กยึดเหล็กปลอกขั้นต่ำ ไม่แสดงแยกในตารางนี้</p>'''

    # --- 6. เหล็กปลอก ต่อช่วง+ปลายยื่น ---
    stirrup_rows = []
    for i, sp in enumerate(result.spans):
        st = sp.stirrup
        stirrup_rows.append(
            f"<tr><td>ช่วงที่ {i + 1}</td><td>{st.vu_kg:.0f}</td>"
            f"<td>{st.s_max_cm:.1f}</td><td class='{ok_class(st.stirrup_ok)}'>{ok_th(st.stirrup_ok)}</td></tr>"
        )
        if st.section_too_small:
            warnings.append(f"ช่วงที่ {i + 1}: Vs ต้องการเกินขีดจำกัด 2.1&radic;fc&prime;bd — หน้าตัดคานเล็กเกินไป")
    if has_left:
        st = result.left_overhang.stirrup
        stirrup_rows.append(
            f"<tr><td>ปลายยื่นซ้าย</td><td>{st.vu_kg:.0f}</td>"
            f"<td>{st.s_max_cm:.1f}</td><td class='{ok_class(st.stirrup_ok)}'>{ok_th(st.stirrup_ok)}</td></tr>"
        )
        if st.section_too_small:
            warnings.append("ปลายยื่นซ้าย: Vs ต้องการเกินขีดจำกัด 2.1&radic;fc&prime;bd — หน้าตัดคานเล็กเกินไป")
    if has_right:
        st = result.right_overhang.stirrup
        stirrup_rows.append(
            f"<tr><td>ปลายยื่นขวา</td><td>{st.vu_kg:.0f}</td>"
            f"<td>{st.s_max_cm:.1f}</td><td class='{ok_class(st.stirrup_ok)}'>{ok_th(st.stirrup_ok)}</td></tr>"
        )
        if st.section_too_small:
            warnings.append("ปลายยื่นขวา: Vs ต้องการเกินขีดจำกัด 2.1&radic;fc&prime;bd — หน้าตัดคานเล็กเกินไป")

    stirrup_table = f'''<h2>6. ออกแบบเหล็กปลอก (Stirrup Design — ระยะห่างเดียวกันทั้งคาน {inp.stirrup_spacing_use_cm:.0f} cm.)</h2>
<table class="mini-table drmk-table">
  <tr><th>ตำแหน่ง</th><th>Vu,max (kg.)</th><th>S_max (cm.)</th><th>ผล</th></tr>
  {"".join(stirrup_rows)}
</table>
<table class="mini-table" style="margin-top:4px;">
  <tr><th>เหล็กปลอกที่ใช้จริงทั้งคาน</th>
      <td>{inp.stirrup_legs}-{result.stirrup_bar_type}{inp.stirrup_bar_dia_mm:.0f}@{inp.stirrup_spacing_use_cm:.0f}cm.</td></tr>
</table>'''

    warning_html = ""
    if warnings:
        items = "".join(f"<li>{w}</li>" for w in warnings)
        warning_html = f'<div class="ng" style="font-size:11.5px; margin-top:6px;">&#9888; ข้อควรระวัง:<ul>{items}</ul></div>'

    section_block_html = ""
    if midspan_section_uri and support_section_uri:
        gsp_i = result.governing_span_index
        gsup_i = result.governing_support_index
        section_block_html = f'''<div class="no-split">
<h2>8. รูปตัดรายละเอียดการเสริมเหล็ก (Reinforcement Detail Sections)</h2>
<p style="font-size:11.5px; color:#666; margin:2px 0 6px 0;">แสดงรูปตัดตัวแทน 2 ตำแหน่ง (หน้าตัด b&times;h เดียวกันทั้งคาน) —
กลางช่วงที่มีเหล็กล่างมากที่สุด (ช่วงที่ {gsp_i + 1}) และจุดรองรับที่มีโมเมนต์ลบมากที่สุด (S{gsup_i}) —
ปริมาณเหล็กจริงของทุกตำแหน่งดูได้จากตารางข้อ 4-5 ด้านบน</p>
<div class="row3">
  <div class="center detail-frame no-split">
    <div style="font-weight:bold; font-size:12.5px; margin-bottom:4px;">กลางคาน (Midspan) — ช่วงที่ {gsp_i + 1}</div>
    <img class="detail detail-md" src="{midspan_section_uri}" alt="Midspan reinforcement section">
  </div>
  <div class="center detail-frame no-split">
    <div style="font-weight:bold; font-size:12.5px; margin-bottom:4px;">จุดรองรับ (Support) — S{gsup_i}</div>
    <img class="detail detail-md" src="{support_section_uri}" alt="Support reinforcement section">
  </div>
</div>
</div>'''

    html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>รายการคำนวณ {beam_name}</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ margin: 0; }}
    #cbeam-detail-block img.detail.detail-lg {{ max-height: 400px; width: auto; max-width: 100%; }}
    #cbeam-detail-block img.detail.detail-md {{ max-height: 220px; width: auto; max-width: 100%; }}
    #cbeam-detail-block h2 {{ margin-top: 3px; margin-bottom: 3px; }}
    #cbeam-detail-block .detail-frame {{ padding: 3px; margin-top: 3px; }}
    #cbeam-detail-block p {{ margin: 2px 0 4px 0; }}
    img.detail.detail-elev {{ max-height: 150px; width: auto; max-width: 100%; }}
    .no-split {{ page-break-inside: avoid; break-inside: avoid; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; font-size: 13.5px; color: #111;
          max-width: 780px; margin: 14px auto; padding: 0 14px; line-height: 1.35; }}
  h2 {{ font-size: 13.5px; background:#dbe7f5; padding: 3px 8px; margin: 10px 0 4px 0; border-left: 4px solid #2563eb; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #999; padding: 3px 7px; font-size: 12.5px; }}
  th {{ background: #eee; text-align: left; }}
  .row3 {{ display: flex; gap: 10px; margin-bottom: 4px; }}
  .row3 > div {{ flex: 1; }}
  .mini-table td, .mini-table th {{ padding: 2px 6px; font-size: 12px; }}
  .ok {{ color: #0a7a0a; font-weight: bold; }}
  .ng {{ color: #b30000; font-weight: bold; }}
  .drmk-table th {{ background: #dbe7f5; }}
  .drmk-table td.dv {{ color: #b45f06; }}
  .print-btn {{ background:#2563eb; color:white; border:none; padding:8px 18px;
                border-radius:6px; font-size:14px; cursor:pointer; }}
  img.detail {{ margin: 0 auto; display:block; }}
  img.detail-lg {{ max-width: 100%; }}
  img.detail-md {{ max-width: 92%; }}
  img.detail-elev {{ max-width: 70%; }}
  .detail-frame {{ border: 1px solid #ccc; padding: 8px; margin: 4px 0 0 0; }}
  .center {{ text-align: center; }}
  .page-break {{ page-break-before: always; break-before: page; }}
{REPORT_HEADER_CSS}
</style>
</head>
<body>

<div class="no-print" style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
  <span style="font-size:16px; font-weight:bold; color:#111;">รายการคำนวณ</span>
  <button class="print-btn" onclick="window.print()">🖨️ พิมพ์รายการคำนวณ</button>
</div>

{header_html}

<div class="row3">
  <div>
    <table class="mini-table">
      <tr><th colspan="3">1. คุณสมบัติวัสดุ &amp; หน้าตัด</th></tr>
      <tr><td>f'c</td><td colspan="2">{inp.fc_ksc:.0f} ksc.</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กหลัก</td><td colspan="2">{inp.main_steel_type} (fy={GS_STEEL_FY_KSC[inp.main_steel_type]:.0f})</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กปลอก</td><td colspan="2">{inp.stirrup_steel_type} (fy={GS_STEEL_FY_KSC[inp.stirrup_steel_type]:.0f})</td></tr>
      <tr><td>b &times; h</td><td colspan="2">{inp.b_cm:.0f} &times; {inp.h_cm:.0f} cm. (หน้าตัดเดียวทั้งคาน)</td></tr>
      <tr><td>จำนวนช่วงคาน</td><td colspan="2">{n_spans} ช่วง</td></tr>
      <tr><td>ความยาวรวม</td><td colspan="2">{result.total_length_m:.2f} m.</td></tr>
    </table>
  </div>
</div>

{layout_table}

{support_table}

{bottom_table}

{top_table}

{stirrup_table}
{warning_html}

<div id="cbeam-detail-block">
<h2>7. กราฟแรงเฉือน &amp; โมเมนต์รวมทั้งคาน (SFD/BMD)</h2>
<div class="center detail-frame">
  <img class="detail detail-lg" src="{sfd_bmd_uri}" alt="Continuous beam SFD/BMD">
</div>
{section_block_html}
</div>

</body>
</html>
"""
    return html


def build_cantilever_beam_report_html(project: dict, inp, result, elevation_png: bytes, sfd_bmd_png: bytes,
                                       section_png: bytes, project_info: dict = None,
                                       logo_bytes: bytes = None, logo_mime: str = None) -> str:
    """
    project: dict with key beam_name.
    inp: modules.cantilever_beam.CantileverBeamInput
    result: modules.cantilever_beam.CantileverBeamResult
    elevation_png / sfd_bmd_png: PNG bytes จาก draw_cantilever_beam_elevation_png /
    draw_cantilever_beam_sfd_bmd_png. section_png: PNG bytes จาก draw_beam_section_png
    (หน้าตัดตัวแทนที่จุดรองรับ — ตำแหน่งที่มี |M| และ Vu สูงสุดของคานยื่น).
    หมายเหตุ: คานยื่นมีโมเมนต์ลบ (hogging) ตลอดความยาว — เหล็กบน (top) คือเหล็กรับแรงดึงหลัก
    ตามโมเมนต์ที่จุดรองรับ, เหล็กล่าง (bottom) คือเหล็กยึดขั้นต่ำ (nominal/hanger) กลับกันกับ
    คานช่วงเดียว (3.1) ที่เหล็กล่างเป็นเหล็กรับแรงดึงหลัก.
    """
    elevation_uri = png_to_data_uri(elevation_png)
    sfd_bmd_uri = png_to_data_uri(sfd_bmd_png)
    section_uri = png_to_data_uri(section_png)

    def ok_th(flag: bool) -> str:
        return "ผ่าน" if flag else "ไม่ผ่าน"

    def ok_class(flag: bool) -> str:
        return "ok" if flag else "ng"

    beam_name = project.get("beam_name", "B-01")
    header_html = build_report_header_html(
        project_info, logo_bytes, logo_mime,
        doc_label=f"คาน : {beam_name}",
        subtitle="รายการคำนวณโดยวิธีกำลังตามกฎกระทรวง พ.ศ.2566 (คานยื่น — Cantilever Beam)",
    )

    if inp.point_loads:
        pt_rows = "".join(
            f"<tr><td>จุดที่ {i + 1}</td><td>{p.x_m:.2f}</td><td>{p.p_dl_kg:.0f}</td>"
            f"<td>{p.p_ll_kg:.0f}</td><td>{pu:.0f}</td></tr>"
            for i, (p, (x, pu)) in enumerate(zip(sorted(inp.point_loads, key=lambda q: q.x_m), result.pu_loads))
        )
        point_load_table = f'''<h2>3. น้ำหนักจุด (Point Loads — ระยะวัดจากจุดรองรับ/โคนคาน)</h2>
<table class="mini-table">
  <tr><th>ตำแหน่ง</th><th>ระยะจากจุดรองรับ (m.)</th><th>P_DL (kg.)</th><th>P_LL (kg.)</th><th>Pu (kg.)</th></tr>
  {pt_rows}
</table>'''
    else:
        point_load_table = ""

    top_doubly_html = ""
    if result.top.doubly_reinforced:
        top_doubly_html = f'''
  <tr><th colspan="5">เสริมเหล็กสองชั้น (Doubly-reinforced) — หน้าตัดเดียวรับโมเมนต์เกิน Ru,max</th></tr>
  <tr><td>Mu1 (รับได้ที่ &rho;max)</td><td colspan="2">{result.top.mu1_kgm:.0f} kg-m.</td>
      <td>Mu2 (ส่วนเกิน)</td><td>{result.top.mu2_kgm:.0f} kg-m.</td></tr>
  <tr><td colspan="2">As2 (เหล็กรับแรงอัดที่ต้องเพิ่ม, สมมติ f<sub>s</sub>&prime;=fy)</td>
      <td colspan="3">{result.top.as_comp_req_cm2:.2f} cm&sup2;</td></tr>'''

    layer_warn_html = ""
    if result.top.n_layers > 1:
        breakdown = "+".join(str(n) for n in result.top.bars_per_layer if n > 0)
        layer_warn_html += (f'<p style="font-size:11.5px; color:#555;">'
                             f'&#8505; เหล็กบนเกินกว่าจะใส่ได้ใน 1 ชั้น (ใส่ได้สูงสุด {result.top.max_bars_single_layer} '
                             f'เส้น/ชั้น ที่ความกว้างคานนี้) — จัดเป็น {result.top.n_layers} ชั้นอัตโนมัติตามมาตรฐาน '
                             f'({breakdown} เส้น) — d ที่ใช้ออกแบบจริงคำนวณจาก centroid ของเหล็กทุกชั้นแล้ว</p>')
    if not result.top.reinf_ok:
        layer_warn_html += (f'<p class="ng" style="font-size:11.5px;">'
                             f'&#9888; จำนวนเหล็กที่ต้องการ ({result.top.n_bars_req} เส้น) '
                             f'เกินกว่าจะใส่ได้แม้จัด {MAX_LAYERS} ชั้นแล้ว (สูงสุด {result.top.max_bars_single_layer * MAX_LAYERS} เส้น '
                             f'ที่ความกว้างคานนี้) — กรุณาขยายความกว้างคาน หรือเปลี่ยนขนาดเหล็กให้ใหญ่ขึ้น</p>')

    section_too_small_html = ""
    if result.stirrup.section_too_small:
        section_too_small_html = ('<p class="ng" style="font-size:11.5px;">&#9888; '
                                   'Vs ที่ต้องการเกินขีดจำกัด 2.1&radic;fc&prime;bd — หน้าตัดคานเล็กเกินไป '
                                   'สำหรับแรงเฉือนนี้ กรุณาขยายขนาดคาน (b หรือ h)</p>')

    html = f"""
<!DOCTYPE html>
<html lang="th">
<head>
<meta charset="utf-8">
<title>รายการคำนวณ {beam_name}</title>
<style>
  @page {{ size: A4; margin: 12mm; }}
  @media print {{
    .no-print {{ display: none !important; }}
    body {{ margin: 0; }}
    #cant-detail-block img.detail.detail-lg {{ max-height: 400px; width: auto; max-width: 100%; }}
    #cant-detail-block img.detail.detail-md {{ max-height: 220px; width: auto; max-width: 100%; }}
    #cant-detail-block h2 {{ margin-top: 3px; margin-bottom: 3px; }}
    #cant-detail-block .detail-frame {{ padding: 3px; margin-top: 3px; }}
    img.detail.detail-elev {{ max-height: 90px; width: auto; max-width: 45%; }}
    .elev-frame {{ padding: 2px !important; margin: 2px 0 0 0 !important; }}
    .no-split {{ page-break-inside: avoid; break-inside: avoid; }}
  }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: 'TH Sarabun New', 'Sarabun', Tahoma, sans-serif; font-size: 13.5px; color: #111;
          max-width: 780px; margin: 14px auto; padding: 0 14px; line-height: 1.35; }}
  h2 {{ font-size: 13.5px; background:#dbe7f5; padding: 3px 8px; margin: 10px 0 4px 0; border-left: 4px solid #2563eb; }}
  table {{ border-collapse: collapse; width: 100%; }}
  td, th {{ border: 1px solid #999; padding: 3px 7px; font-size: 12.5px; }}
  th {{ background: #eee; text-align: left; }}
  .row3 {{ display: flex; gap: 10px; margin-bottom: 4px; }}
  .row3 > div {{ flex: 1; }}
  .mini-table td, .mini-table th {{ padding: 2px 6px; font-size: 12px; }}
  .ok {{ color: #0a7a0a; font-weight: bold; }}
  .ng {{ color: #b30000; font-weight: bold; }}
  .drmk-table th {{ background: #dbe7f5; }}
  .drmk-table td.dv {{ color: #b45f06; }}
  .print-btn {{ background:#2563eb; color:white; border:none; padding:8px 18px;
                border-radius:6px; font-size:14px; cursor:pointer; }}
  img.detail {{ margin: 0 auto; display:block; }}
  img.detail-lg {{ max-width: 100%; }}
  img.detail-md {{ max-width: 62%; }}
  img.detail-elev {{ max-width: 45%; }}
  .detail-frame {{ border: 1px solid #ccc; padding: 8px; margin: 4px 0 0 0; }}
  .center {{ text-align: center; }}
  .page-break {{ page-break-before: always; break-before: page; }}
{REPORT_HEADER_CSS}
</style>
</head>
<body>

<div class="no-print" style="margin-bottom:10px; display:flex; justify-content:space-between; align-items:center;">
  <span style="font-size:16px; font-weight:bold; color:#111;">รายการคำนวณ</span>
  <button class="print-btn" onclick="window.print()">🖨️ พิมพ์รายการคำนวณ</button>
</div>

{header_html}

<div class="row3">
  <div>
    <table class="mini-table">
      <tr><th colspan="3">1. คุณสมบัติวัสดุ</th></tr>
      <tr><td>f'c</td><td colspan="2">{inp.fc_ksc:.0f} ksc.</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กหลัก</td><td colspan="2">{inp.main_steel_type} (fy={GS_STEEL_FY_KSC[inp.main_steel_type]:.0f})</td></tr>
      <tr><td>ชั้นคุณภาพเหล็กปลอก</td><td colspan="2">{inp.stirrup_steel_type} (fy={GS_STEEL_FY_KSC[inp.stirrup_steel_type]:.0f})</td></tr>
    </table>
  </div>
  <div>
    <table class="mini-table">
      <tr><th colspan="3">2. ขนาดคาน &amp; น้ำหนักแผ่กระจาย</th></tr>
      <tr><td>b &times; h</td><td colspan="2">{inp.b_cm:.0f} &times; {inp.h_cm:.0f} cm.</td></tr>
      <tr><td>ความยาวคานยื่น L</td><td colspan="2">{inp.L_m:.2f} m.</td></tr>
      <tr><td>น้ำหนักตัวเอง (Self weight)</td><td colspan="2">{result.self_weight_kg_m:.0f} kg/m.</td></tr>
      <tr><td>Line Load DL / LL</td><td colspan="2">{inp.line_load_dl_kg_m:.0f} / {inp.line_load_ll_kg_m:.0f} kg/m.</td></tr>
      <tr><td><b>Wu</b> = 1.4(DL+SW)+1.7LL</td><td colspan="2"><b>{result.wu_kg_m:.0f}</b> kg/m.</td></tr>
    </table>
  </div>
</div>

<div class="center detail-frame elev-frame">
  <img class="detail detail-elev" src="{elevation_uri}" alt="Cantilever beam elevation">
</div>

{point_load_table}

<h2>4. ผลการวิเคราะห์หาแรงที่จุดรองรับ/โคนคาน (Structural Analysis)</h2>
<table class="mini-table drmk-table">
  <tr><th>Data</th><th>Value</th><th>Unit</th></tr>
  <tr><td>R (ปฏิกิริยาที่จุดรองรับ) = Vu,max</td><td class="dv">{result.reaction_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>Mu (ที่จุดรองรับ/โคนคาน — hogging ตลอดคาน)</td>
      <td class="dv">{result.end_moment_kgm:+.2f}</td><td class="dv">kg-m.</td></tr>
</table>

<h2>5. เหล็กเสริมบน (Top Bars — เหล็กรับแรงดึงหลัก ตามโมเมนต์ลบที่จุดรองรับ)</h2>
<table class="mini-table no-split">
  <tr><th>Mu (kg-m.)</th><th>d (cm.)</th><th>Ru (ksc)</th><th>&rho; ที่ใช้</th><th>As ต้องการ (cm&sup2;)</th></tr>
  <tr><td>{result.top.mu_kgm:.0f}</td><td>{result.top.d_cm:.2f}</td><td>{result.top.ru_ksc:.2f}</td>
      <td>{result.top.rho_used:.4f}</td><td>{result.top.as_req_cm2:.2f}</td></tr>
  {top_doubly_html}
  <tr><th colspan="4">เหล็กที่ใช้จริง</th><th>{result.reinf_label_top}</th></tr>
  <tr><td colspan="2">จำนวนเหล็กที่ต้องการ</td><td>{result.top.n_bars_req} เส้น</td>
      <td>As ที่ใช้จริง</td><td>{result.top.as_provided_cm2:.2f} cm&sup2;</td></tr>
  <tr><td colspan="4"></td><th class="{ok_class(result.top.reinf_ok)}">{ok_th(result.top.reinf_ok)}</th></tr>
</table>
{layer_warn_html}

<h2>6. เหล็กเสริมล่าง (Bottom Bars — เหล็กยึดเหล็กปลอกขั้นต่ำ)</h2>
<table class="mini-table">
  <tr><td colspan="2">คานยื่นมีโมเมนต์ลบ (hogging) ตลอดความยาว ไม่มีโมเมนต์บวกจริง —
      เหล็กล่างใช้เป็นเหล็กยึดเหล็กปลอก (hanger bars) ขั้นต่ำเท่านั้น</td>
      <th>เหล็กที่ใช้จริง</th><th colspan="2">{result.reinf_label_bottom}</th></tr>
</table>

<h2>7. ออกแบบเหล็กปลอก (Stirrup Design)</h2>
<table class="mini-table drmk-table no-split">
  <tr><th>Data</th><th>Value</th><th>Unit</th></tr>
  <tr><td>Vu,max</td><td class="dv">{result.stirrup.vu_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>&phi;<sub>v</sub>Vc&nbsp;=&nbsp;&phi;<sub>v</sub>&middot;0.53(&radic;fc&prime;)bd</td>
      <td class="dv">{result.stirrup.phi_vc_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>Vs ต้องการ&nbsp;=&nbsp;Vu/&phi;<sub>v</sub> &minus; Vc</td>
      <td class="dv">{result.stirrup.vs_req_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>&phi;&middot;1.1(&radic;fc&prime;)bd</td><td class="dv">{result.stirrup.limit_1p1_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>&phi;&middot;2.1(&radic;fc&prime;)bd</td><td class="dv">{result.stirrup.limit_2p1_kg:.2f}</td><td class="dv">kg.</td></tr>
  <tr><td>ระยะห่างสูงสุดที่คำนวณได้ (S_max)</td><td class="dv">{result.stirrup.s_max_cm:.1f}</td><td class="dv">cm.</td></tr>
  <tr><th colspan="2">เหล็กปลอกที่ใช้จริง</th><th colspan="1">{result.reinf_label_stirrup}</th></tr>
  <tr><td colspan="2">ผลตรวจสอบ</td>
      <td class="{ok_class(result.stirrup.stirrup_ok)}">{ok_th(result.stirrup.stirrup_ok)}</td></tr>
</table>
{section_too_small_html}

<div id="cant-detail-block">
<h2 class="page-break">8. กราฟแรงเฉือน &amp; โมเมนต์ (SFD/BMD)</h2>
<div class="center detail-frame">
  <img class="detail detail-lg" src="{sfd_bmd_uri}" alt="Cantilever beam SFD/BMD">
</div>

<h2>9. รูปตัดคาน (ที่จุดรองรับ/โคนคาน — ตำแหน่งโมเมนต์สูงสุด)</h2>
<div class="center detail-frame">
  <img class="detail detail-md" src="{section_uri}" alt="Cantilever beam cross-section">
</div>
</div>

</body>
</html>
"""
    return html
