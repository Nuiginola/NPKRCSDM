"""
common/stair_detail.py — Engineering Drawing Template Renderer
โมดูล 2.2 บันไดหักกลับ (U-Shape Stair) — รูปแบบรายละเอียด (6) รูปด้านข้างแบบคลี่ (Developed Elevation)

*** สำคัญ: นี่ไม่ใช่ตัวสร้างภาพ (Drawing Generator) ***
เป็น "Engineering Drawing Template Renderer" เท่านั้น — หน้าที่เดียวคือนำค่าตัวเลขที่คำนวณ
ได้จริงไปวางทับ (overlay) บนภาพ template คงที่ (stair_detail_template.png) ที่ผู้ใช้วาดเตรียมไว้เอง

กติกาที่ต้องยึดเคร่งครัด (ตามคำสั่งผู้ใช้):
- ห้ามวาดบันไดใหม่, ห้ามคำนวณ/สร้างพิกัดเรขาคณิตของรูป, ห้ามย่อ/ขยาย/หมุน/ครอปภาพ template,
  ห้ามวาดเหล็กเสริม/เส้นบอกระยะ/ลูกศร/เส้นชี้ (leader) ใหม่ — ทุกอย่างมีอยู่ในภาพ template แล้วครบถ้วน
- ไม่ว่าเรขาคณิตบันไดจริง (ความกว้าง/ความสูง/ความยาวชานพัก/จำนวนขั้น) จะเป็นเท่าไหร่
  เลย์เอาต์ของภาพจะต้องเหมือนเดิมทุกครั้ง — เปลี่ยนแค่ตัวเลขที่แสดงบนภาพเท่านั้น
- ใช้ Pillow (PIL) เท่านั้น ห้ามใช้ matplotlib/OpenCV/SVG/ไลบรารี CAD ใดๆ
- พิกัดวางข้อความทั้งหมดต้องอยู่ใน TEXT_POS เท่านั้น ห้าม hardcode พิกัดกระจายอยู่ในโค้ดจุดอื่น
- ห้ามวาดกล่อง/สี่เหลี่ยมพื้นหลังใดๆ ไว้ใต้ข้อความเด็ดขาด — พื้นหลังของตัวอักษรต้องโปร่งใส 100%
  (วาดเฉพาะ glyph ทับลงบนภาพเดิมตรงๆ เหมือน AutoCAD MTEXT) ห้ามบัง/ทับเส้นแบบ/เส้นชี้/เหล็กเสริม

สถานะ: อยู่ระหว่างพัฒนาแบบ phase-by-phase ตามคำสั่งผู้ใช้ (verify ทีละ phase ก่อนไปต่อ)
- [x] Phase 1-6: load/draw/export PNG+PDF (ดูประวัติในสำเนาเก่าของไฟล์นี้)
- [x] Phase 7: เปลี่ยนวิธีวาง — เลิกลบพื้นหลังด้วยกล่องสีขาว ใช้ anchor ชิดปลายข้อความ/เส้นชี้เดิม
- [x] Phase 8: ผู้ใช้แก้ไข "stair_detail_template.png" ใหม่ทั้งไฟล์ — ตัดข้อความ placeholder
      ("m"/"cm"/"RB @"/"DB @"/สัญลักษณ์ "E") ที่เคยแน่นออกเกือบทั้งหมด เหลือแค่เส้นชี้ (leader)
      /ลูกศรบอกระยะเปล่าๆ + ป้ายภาษาไทยคงที่ 4 ป้าย ("เหล็กเสริมกันร้าว"/"เหล็กเสริมหลัก"/
      "เหล็กมุม RB9"/"เหล็กยึดขั้น") — พิกัดทั้งหมดใน TEXT_POS ถูกวัด/ออกแบบใหม่ทั้งหมดให้เข้ากับ
      template เวอร์ชันนี้ (พิกัดเก่าใน Phase 7 ใช้ไม่ได้แล้ว เพราะอ้างอิงตำแหน่งข้อความที่ถูกลบไป)

หมายเหตุสำคัญของ template เวอร์ชันนี้ (Phase 8):
- เส้นบอกระยะ/ลูกศรเกือบทั้งหมด (ลูกนอน/ลูกตั้ง/ระยะยื่นแนวทแยง/ความหนา waist/ความยาวช่วงพาด/
  ความยาวชานพัก/ความสูงรวม) ไม่มีข้อความกำกับอยู่แล้วเลย (ทั้งไม่มีตัวเลข ไม่มีหน่วย ไม่มีสัญลักษณ์
  "E") — จึงวางข้อความเต็มรูปแบบ (ตัวเลข+หน่วย) ได้อิสระโดยไม่ชนอะไร ไม่ต้องชิดขอบระวังเหมือนเดิม
- เส้น "RB @ ___ m" / "DB @ ___ m" / "RB @ ___ cm" (คำนำหน้า "RB"/"DB"/"@" และหน่วย) ถูกลบออก
  จากภาพทั้งหมด เหลือแค่ป้ายภาษาไทยคงที่ ("เหล็กเสริมกันร้าว"/"เหล็กเสริมหลัก") กับเส้นชี้ที่ปลาย
  มีวงกลมแดงเล็กๆ ชี้ตำแหน่งบนเหล็กเสริมจริง — จึงวางข้อความเต็มรูปแบบ (เช่น "RB9 @ 14 cm")
  เป็นบรรทัดใหม่ในพื้นที่ว่างเหนือป้ายภาษาไทยแต่ละอัน (พื้นที่เดิมที่เคยมี "RB @ m" ตอนนี้ว่างสนิท)
- จุด "เหล็กมุม RB9" / "เหล็กยึดขั้น" (มุมเชื่อมเหล็กหลัก-เหล็กเสริมรอง) ป้าย "RB9" มีอยู่แล้วเป็น
  ส่วนหนึ่งของข้อความคงที่ในภาพ (ไม่ใช่ placeholder) — เติมแค่ "@14 cm" ในช่องว่างระหว่าง 2 บรรทัด
  ตามธรรมเนียมเดิมของโมดูล 2.1 (ใช้ระยะห่างเดียวกับเหล็กเสริมรอง — lesson #68 ในเอกสารโปรเจกต์)
- ฝั่งช่วงล่างมีจุดเดียวที่ข้อความ "RB9@14 cm" ยัง "เบิร์น" เป็นส่วนหนึ่งของภาพอยู่ (ไม่ใช่ placeholder
  เหมือนเดิม) จึงไม่วาดซ้ำที่ตำแหน่งนั้น (เหมือน Phase 7)
- ยังใช้สมมติฐาน TREAD_PROJ = ความกว้างบันได (width_m) เหมือนที่แจ้งไว้ทุกรอบก่อนหน้า (0.88m
  ตรงกับภาพอ้างอิงของผู้ใช้ทุกจุด) — รอผู้ใช้ยืนยันอีกครั้งถ้าผิดจากที่ตั้งใจไว้

หมายเหตุจากรอบตรวจสอบ pixel-level ล่าสุด (หลัง Phase 8):
- พบว่าตำแหน่งเริ่มต้นหลายจุดวางข้อความทับเส้นบอกระยะ/เส้นทแยงโดยตรง (TREAD_PROJ จุดที่ 1,3 /
  WAIST จุดที่ 1,3 / FLIGHT_LENGTH / HEIGHT ทั้ง 2 จุด / DB_MAIN ช่วงล่าง) — ทั้งหมดถูกขยับ/เปลี่ยน
  anchor แล้วให้เลี่ยงเส้นเดิม ตรวจสอบซ้ำด้วย crop ทีละจุดจนสะอาดไม่ทับเส้นแล้ว (ดูค่าปัจจุบันใน
  TEXT_POS ด้านล่าง — เป็นค่าที่ผ่านการตรวจสอบแล้ว ไม่ใช่ค่าจากการวัดครั้งแรก)
- พบ "ของตกค้าง" ในภาพ template จุดเดียว: มีตัวอักษร "m" เดี่ยวๆ ถูกเบิร์นทิ้งไว้ที่ประมาณ
  (555-565, 486-492) ใกล้ตำแหน่ง WAIST จุดที่ 3 (ลูกศรชี้ระยะ waist ฝั่งชานพัก) — ไม่ใช่
  placeholder ที่ตั้งใจเว้นไว้ให้ใส่ข้อความ (ตำแหน่งอื่นๆ ไม่มีลักษณะแบบนี้) จึงเข้าใจว่าเป็นเศษ
  ข้อความเก่าที่ผู้ใช้แก้ภาพแล้วลบไม่หมด — ได้ขยับตำแหน่งข้อความใหม่ (WAIST จุดที่ 3) ให้เลี่ยงไม่
  ทับตัวอักษรนี้แล้ว แต่ตัว "m" เก่ายังปรากฏอยู่ในภาพ (เห็นเป็นข้อความซ้ำซ้อนเล็กน้อยในผลลัพธ์)
  — ควรแจ้งผู้ใช้ให้ลบออกจาก template ต้นฉบับเพิ่มอีกจุดถ้าต้องการภาพที่สะอาดที่สุด
"""
import os
import re
from PIL import Image, ImageDraw, ImageFont

_HERE = os.path.dirname(os.path.abspath(__file__))
_PROJECT_ROOT = os.path.dirname(_HERE)

TEMPLATE_PATH = os.path.join(_PROJECT_ROOT, "data", "stair_detail_template.png")
FONT_REGULAR_PATH = os.path.join(_HERE, "fonts", "NotoSansThai-Regular.ttf")
FONT_BOLD_PATH = os.path.join(_HERE, "fonts", "NotoSansThai-Bold.ttf")
# หมายเหตุ: ไม่มี TH Sarabun New / Sarabun ติดตั้งอยู่ในเครื่อง (ตรวจสอบผ่าน fc-list แล้วไม่พบ)
# ใช้ Noto Sans Thai ที่ bundle เข้าโปรเจกต์อยู่แล้ว (common/fonts/) เป็น fallback ตามลำดับที่ผู้ใช้ระบุ

# ==========================================================================
# TEXT_POS — พิกัด (x, y) เป็นพิกเซล (origin มุมบนซ้ายของภาพ template, 629x764)
# แต่ละจุดคือ (x, y, anchor, font_size) — วัดตำแหน่งจริงจาก template เวอร์ชันล่าสุด (Phase 8)
# ที่ผู้ใช้ตัด placeholder ข้อความออกเกือบทั้งหมดแล้ว เหลือแต่เส้นชี้/ลูกศรเปล่า — ค่าเป็น "list"
# เพราะหลายค่าปรากฏซ้ำมากกว่า 1 ตำแหน่งในภาพเดียวกัน (ช่วงบน/ช่วงล่างของบันไดหักกลับ ซึ่งบังคับ
# ให้เท่ากันเสมอ — ค่าจริงเดียวกัน)
# ==========================================================================
TEXT_POS = {
    "GOING": [(313, 145, "mm", 14)],                  # ลูกนอน (tread) — กึ่งกลางลูกศรที่ว่างอยู่แล้ว
    "RISER": [(365, 192, "mm", 14)],                  # ลูกตั้ง (rise) — กึ่งกลางลูกศรที่ว่างอยู่แล้ว
    # TREAD_PROJ: ป้ายกำกับเส้นทแยง 4 จุด (ดูหมายเหตุที่หัวไฟล์ — สมมติฐาน = width_m)
    "TREAD_PROJ": [
        (215, 45, "mm", 13), (560, 235, "mm", 13),
        (335, 415, "mm", 13), (108, 607, "mm", 13),
    ],
    # RB_DIST/DB_MAIN: บรรทัดใหม่ทั้งหมด (รวม "RB9 @ 14 cm") วางในพื้นที่ว่างเหนือป้ายภาษาไทย
    # "เหล็กเสริมกันร้าว"/"เหล็กเสริมหลัก" ชิดซ้ายตรงกับจุดเริ่มต้นของป้ายภาษาไทยแต่ละอัน
    "RB_DIST": [(151, 228, "lm", 13), (400, 495, "lm", 13)],
    "DB_MAIN": [(198, 275, "lm", 13), (300, 718, "lm", 13)],
    # RB_STEP: เติมเฉพาะ "@14 cm" ต่อจาก "RB9" ที่มีอยู่แล้วในภาพ (ป้ายคงที่ ไม่ใช่ placeholder)
    # วางในช่องว่างระหว่างบรรทัด "เหล็กมุม RB9" กับ "เหล็กยึดขั้น" ของช่วงบน
    "RB_STEP": [(391, 229, "lm", 12)],
    # หมายเหตุ: ตำแหน่งเดียวกันฝั่งช่วงล่างมีข้อความ "RB9@14 cm" ถูก "เบิร์น" เป็นส่วนหนึ่งของภาพ
    # template อยู่แล้ว (ไม่ใช่ placeholder ว่าง) จึงไม่ต้องวาดซ้ำที่จุดนั้น
    "WAIST": [
        (320, 305, "mm", 13), (563, 264, "mm", 12),
        (528, 472, "rm", 13), (365, 607, "mm", 13),
    ],
    "FLIGHT_LENGTH": [(233, 402, "mm", 15)],           # ความยาวช่วงพาดต่อช่วง (แนวราบ)
    "LANDING": [(503, 393, "mm", 15)],                 # ความยาวชานพัก
    # HEIGHT: ลูกศรว่างสนิท ไม่มีสัญลักษณ์ "E" หรือหน่วยเหลืออยู่แล้ว — ข้อความรวมหน่วย " m" เอง
    # ทั้ง 2 จุดมีเส้นบอกระยะแนวตั้งพาดผ่านตำแหน่งเดิม จึงย้ายมาชิดข้าง (rm/mm หลบเส้น) แทนวางทับเส้น
    "HEIGHT": [(584, 147, "rm", 14), (80, 497, "mm", 14)],
}

DEFAULT_FONT_SIZE = 16
DEFAULT_TEXT_COLOR = (0, 0, 0)  # ดำล้วน — ตามธรรมเนียมแบบวิศวกรรม ห้าม highlight/shadow/outline/glow


class StairDetailRenderer:
    """แปะค่าตัวเลขที่คำนวณได้จริงลงบนแบบ template คงที่ (stair_detail_template.png)

    พื้นหลังของข้อความโปร่งใส 100% เสมอ — ไม่มีการวาดกล่อง/สี่เหลี่ยมสีพื้นใต้ข้อความ (ตามกติกา
    ผู้ใช้) ตำแหน่งแต่ละจุดใน TEXT_POS ถูกวัด/เว้นระยะไว้ล่วงหน้าแล้วไม่ให้ชนข้อความ/เส้นเดิม
    """

    def __init__(self, template_path: str = TEMPLATE_PATH):
        self.template_path = template_path
        self.image = None
        self._font_cache = {}

    def load_template(self):
        """โหลดภาพ template ต้นฉบับเข้าหน่วยความจำ (read-only source — ไม่แก้ไขไฟล์ต้นฉบับบนดิสก์)"""
        with Image.open(self.template_path) as src:
            self.image = src.convert("RGB").copy()
        return self.image

    def _get_font(self, size: int = DEFAULT_FONT_SIZE, bold: bool = False):
        key = (size, bold)
        if key not in self._font_cache:
            path = FONT_BOLD_PATH if bold else FONT_REGULAR_PATH
            self._font_cache[key] = ImageFont.truetype(path, size)
        return self._font_cache[key]

    def draw_text(self, key: str, text: str, size: int = None,
                  bold: bool = False, color=DEFAULT_TEXT_COLOR, anchor: str = None):
        """วางข้อความ 1 ค่า ทับบนภาพ (พื้นหลังโปร่งใส) ณ ทุกตำแหน่งที่กำหนดไว้ล่วงหน้าใน
        TEXT_POS[key] — แต่ละจุดมี (x, y, anchor, font_size) ของตัวเอง เว้นแต่ผู้เรียกจะระบุ
        size/anchor เองเพื่อ override ทุกจุดพร้อมกัน (บางค่าปรากฏซ้ำมากกว่า 1 จุดในภาพเดียวกัน —
        วนวางค่าเดียวกันซ้ำทุกจุดในลิสต์)"""
        if self.image is None:
            raise RuntimeError("ต้องเรียก load_template() ก่อน draw_text()")
        if key not in TEXT_POS:
            raise KeyError(f"ไม่มีตำแหน่งที่กำหนดไว้สำหรับ '{key}' ใน TEXT_POS")
        draw = ImageDraw.Draw(self.image)
        for x, y, point_anchor, point_size in TEXT_POS[key]:
            use_anchor = anchor if anchor is not None else point_anchor
            use_size = size if size is not None else point_size
            font = self._get_font(size=use_size, bold=bold)
            # ไม่มีการวาดกล่องพื้นหลังใดๆ — วาด glyph ทับบนภาพเดิมตรงๆ (โปร่งใส 100%)
            draw.text((x, y), text, fill=color, font=font, anchor=use_anchor)

    def render(self, data: dict):
        """วางค่าทุกตัวจาก data (dict: key -> ข้อความที่จะแสดง) ทับบนภาพ ตามตำแหน่งใน TEXT_POS

        หมายเหตุ: RB_STEP (เหล็กมุม/เหล็กยึดขั้น) ไม่ต้องส่งมาใน data แยก — ถ้าไม่มีคีย์นี้
        จะประกอบจาก RB_DIST อัตโนมัติ (ตัดคำนำหน้า "RBxx @ " ออก เหลือแค่ "@สเปซิง cm") ตาม
        ธรรมเนียมเดิมของโมดูล 2.1 (เหล็กมุม/เหล็กยึดขั้นใช้ระยะห่างเดียวกับเหล็กเสริมรอง —
        lesson #68 ในเอกสารโปรเจกต์) — ดูรูปแบบข้อความที่คาดหวังใน docstring ของฟังก์ชันนี้
        """
        if self.image is None:
            self.load_template()
        data = dict(data)  # ไม่แก้ dict ต้นฉบับของผู้เรียก
        if "RB_STEP" not in data and "RB_DIST" in data:
            # template มีคำว่า "RB9" เบิร์นอยู่แล้ว (ไม่ใช่ placeholder) — ตัดคำนำหน้า "RBxx "
            # ออกจาก RB_DIST เหลือแค่ "@ สเปซิง cm" เพื่อไม่ให้ซ้ำคำว่า "RB9" ที่มีอยู่แล้วในภาพ
            m = re.search(r"(@.*)$", str(data["RB_DIST"]))
            data["RB_STEP"] = m.group(1) if m else data["RB_DIST"]
        for key, text in data.items():
            if key not in TEXT_POS:
                continue  # ข้ามคีย์ที่ยังไม่มีตำแหน่งกำหนดไว้ (กัน error ระหว่างพัฒนาเป็น phase)
            self.draw_text(key, str(text))
        return self.image

    def save_png(self, out_path: str):
        if self.image is None:
            raise RuntimeError("ยังไม่มีภาพให้บันทึก — เรียก load_template()/render() ก่อน")
        self.image.save(out_path, format="PNG")
        return out_path

    def save_pdf(self, out_path: str):
        if self.image is None:
            raise RuntimeError("ยังไม่มีภาพให้บันทึก — เรียก load_template()/render() ก่อน")
        self.image.save(out_path, format="PDF")
        return out_path

    def render_to_png_bytes(self, data: dict) -> bytes:
        """เรียก render(data) แล้วคืนผลเป็น PNG bytes ตรงๆ (ไม่บันทึกไฟล์ลงดิสก์) — ใช้จุด
        integration กับแอปจริง (st.image ยอมรับ bytes ได้ตรงๆ เหมือน draw_*_png เดิมทุกฟังก์ชัน)"""
        import io
        self.render(data)
        buf = io.BytesIO()
        self.image.save(buf, format="PNG")
        return buf.getvalue()


def build_data_from_u_shape_result(inp, result) -> dict:
    """แปลง (StairUShapeInput, StairUShapeResult) จาก modules/stair_u_shape.py ให้เป็น data
    dict สำหรับ StairDetailRenderer.render() — จุด integration เดียวที่ผูกกับโครงสร้างข้อมูล
    จริงของแอป (ไม่ปนกับ TEXT_POS/การวาดข้างบน เพื่อให้ปรับสูตร mapping ได้อิสระในอนาคต)

    หมายเหตุสำคัญ — TREAD_PROJ ยืนยันจากผู้ใช้แล้ว (2026-07-11): = L/4 โดย L คือ
    flight_length_m (ระยะช่วงพาดแนวราบต่อ 1 ช่วงบันได) ไม่ใช่ width_m ตามที่เคยสันนิษฐานไว้ผิด
    ในรอบพัฒนาก่อนหน้า — HEIGHT = height_m/2 (ความสูงต่อช่วง ไม่ใช่ความสูงรวมทั้งอาคาร เพราะ
    รูปนี้แสดงแค่ 1 ชุดบันได/ชานพัก/ลง)
    """
    flight = result.flight
    tread_proj_m = inp.flight_length_m / 4.0
    return {
        "GOING": f"{flight.going_cm:.0f} cm",
        "RISER": f"{flight.rise_cm:.0f} cm",
        "TREAD_PROJ": f"{tread_proj_m:.2f} m",
        "RB_DIST": f"{flight.temp_bar_type}{inp.temp_bar_dia_mm:.0f} @ {inp.temp_bar_spacing_cm:.0f} cm",
        "DB_MAIN": f"{flight.main_bar_type}{inp.main_bar_dia_mm:.0f} @ {inp.main_bar_spacing_cm:.0f} cm",
        "WAIST": f"{inp.t_cm / 100.0:.2f} m",
        "FLIGHT_LENGTH": f"{inp.flight_length_m:.2f} m",
        "LANDING": f"{inp.landing_length_m:.2f} m",
        "HEIGHT": f"{inp.height_m / 2.0:.2f} m",
    }


def draw_stair_u_shape_detail_template_png(inp, result) -> bytes:
    """จุดเรียกใช้งานหลักจากแอปจริง (แทนที่ draw_stair_u_shape_elevation_png เดิมที่วาดด้วย
    matplotlib) — คืนภาพ PNG (bytes) ที่รวมทั้งรูปด้านข้างแบบคลี่ + เหล็กเสริมครบทุกจุดในภาพ
    เดียว (template ใหม่นี้รวมสิ่งที่เคยเป็น 2 รูป — elevation + rebar detail zoom — ไว้ในรูป
    เดียวแล้ว ตามที่ผู้ใช้ยืนยัน/confirm ผลลัพธ์แล้วเมื่อ 2026-07-11) — เรียกใช้แทน BOTH
    draw_stair_u_shape_elevation_png และ draw_stair_u_shape_rebar_detail_png เดิม
    """
    data = build_data_from_u_shape_result(inp, result)
    renderer = StairDetailRenderer()
    renderer.load_template()
    return renderer.render_to_png_bytes(data)
