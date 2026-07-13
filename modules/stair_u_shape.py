"""
Module 2.2 — บันไดหักกลับ (U-Shape Stair, มีชานพัก)

ขอบเขต: บันได 2 ช่วง (ช่วงล่าง + ช่วงบน) เชื่อมด้วยชานพักกลาง (landing) ระหว่างชั้น —
ต่างจากโมดูล 2.1 บันไดช่วงตรงที่เดินขึ้นตรงช่วงเดียวไม่มีชานพัก

การตัดสินใจด้านวิศวกรรม/ขอบเขต (ยืนยันกับผู้ใช้ผ่าน AskUserQuestion ก่อนเขียนโค้ด
2026-07-10 — เลือกตัวเลือก "แนะนำ"/ง่ายทั้งสองข้อ):

1. **ทั้งสองช่วงบังคับให้เท่ากันเสมอ (สมมาตร)**: จำนวนขั้นรวม n_riser_total แบ่งครึ่งอัตโนมัติ
   เป็น n_riser_per_flight ต่อช่วง (ปัดให้เป็นเลขคู่เสมอถ้าผู้ใช้กรอกเลขคี่) ความสูงรวม H
   แบ่งครึ่งเป็นความสูงต่อช่วง — ทั้งสองช่วงจึงมีลูกตั้ง/ลูกนอน/มุมลาดเท่ากันทุกประการ ไม่ต้อง
   คำนวณแยก 2 ชุด

2. **ชานพักออกแบบแบบง่าย (ต่อเนื่องจากบันได ไม่มีการคำนวณ Mu/As แยก)**: waist ของชานพัก
   หนาเท่าแผ่นบันได (t_cm เดียวกัน) เหล็กเสริมหลัก/รองที่ใช้ในช่วงบันไดวิ่งต่อเนื่องผ่านชานพัก
   (ไม่มีเหล็กชุดใหม่/ระยะห่างใหม่สำหรับชานพักโดยเฉพาะ) — เป็นธรรมเนียมทั่วไปสำหรับบันได
   บ้านพักอาศัยขนาดเล็กที่ชานพักไม่กว้างมาก (ตรงตามภาพตัวอย่างที่ผู้ใช้ส่งมา ซึ่งแสดงเหล็ก
   หลัก/เหล็กเสริมรองวิ่งต่อเนื่องผ่านชานพักด้วยขนาด/ระยะห่างเดียวกับช่วงบันได)

**แต่ละช่วงบันได (flight) คำนวณด้วยวิธี "Equivalent Horizontal Span" เดียวกับโมดูล 2.1
ทุกประการ (นำ `StairStraightInput`/`calculate()` จาก `modules.stair_straight` มาใช้ตรงๆ ไม่
ก็อปปี้สูตรซ้ำ)** — รองรับ simply supported เท่านั้น (`continuity_case="SS"`) เพราะปลายบันได
แต่ละช่วงวางบน (1) คาน/ผนังชั้นล่าง-ชั้นบน และ (2) ชานพัก ซึ่งไม่ถือเป็นจุดต่อเนื่องทาง
โครงสร้างในโมดูลนี้ (ตามข้อ 2 ข้างต้น — ไม่คำนวณโมเมนต์ลบที่ปลายชานพัก) — เนื่องจากทั้งสอง
ช่วงเหมือนกันทุกประการ (ข้อ 1) จึงคำนวณแค่ชุดเดียวแล้วใช้ผลเดียวกันกับทั้งสองช่วง

ขอบเขตที่ระบุไว้ชัดเจน (เหมือนโมดูล 2.1 บวกเพิ่มเรื่องชานพัก):
  - ไม่ตรวจสอบสัดส่วนขั้นบันได/ชานพักตามกฎหมายอาคาร/สถาปัตยกรรม (ขนาดชานพักขั้นต่ำ,
    ราวจับ ฯลฯ) — ขอบเขตของโมดูลนี้เป็นการออกแบบโครงสร้าง (Strength Design) เท่านั้น
  - ไม่ออกแบบคาน/ผนังรองรับชานพัก (landing beam) แยกต่างหาก — โมดูลนี้แสดงน้ำหนักตัวเอง
    ของชานพัก (informational) เพื่อให้วิศวกรนำไปใช้ออกแบบคานรองรับชานพักเองภายนอกโมดูลนี้
  - Live Load เริ่มต้น 200 kg/m² อ้างอิงตาราง LOAD_SCHEDULE ("ระเบียง และบันได") เหมือนโมดูล 2.1
"""

from dataclasses import dataclass

from modules.stair_straight import (
    StairStraightInput, StairStraightResult, calculate as calculate_flight,
    CONCRETE_UNIT_WEIGHT_KG_M3,
)


@dataclass
class StairUShapeInput:
    fc_ksc: float
    main_steel_type: str
    temp_steel_type: str
    main_bar_dia_mm: float
    main_bar_spacing_cm: float
    temp_bar_dia_mm: float
    temp_bar_spacing_cm: float
    wD_kg_m2: float
    wL_kg_m2: float
    n_riser_total: int      # จำนวนขั้นรวมทั้งสองช่วง — แบ่งครึ่งอัตโนมัติ (ปัดเป็นเลขคู่)
    flight_length_m: float  # ความยาวช่วงพาดแนวราบของ 1 ช่วงบันได (L ต่อช่วง)
    landing_length_m: float # ความยาวชานพัก (แนวราบ ตามทิศทางเดิน)
    width_m: float          # ความกว้างบันได B (ทั้งสองช่วงเท่ากัน)
    height_m: float         # ความสูงระหว่างชั้น H รวม (ทั้งสองช่วงรวมกัน)
    t_cm: float              # ความหนาแผ่น waist — ใช้ทั้งช่วงบันไดและชานพัก (ข้อ 2)


@dataclass
class StairUShapeResult:
    n_riser_per_flight: int
    n_riser_total_used: int          # = n_riser_per_flight*2 (ค่าจริงที่ใช้ หลังปัดเป็นเลขคู่)
    n_riser_rounded: bool             # True ถ้าผู้ใช้กรอกเลขคี่แล้วถูกปัด
    flight: StairStraightResult       # ผลการคำนวณของ 1 ช่วง (ทั้งสองช่วงเหมือนกันทุกประการ)
    total_horizontal_length_m: float  # 2xflight_length_m + landing_length_m (footprint รวม)
    landing_dead_load_self_kg_m2: float  # น้ำหนักตัวเองชานพัก (แผ่นเรียบ ไม่มีขั้นบันได)
    landing_wu_kg_m2: float
    landing_area_m2: float            # width_m x landing_length_m
    landing_total_dl_kg: float        # น้ำหนักชานพักรวม (Service) — ข้อมูลให้วิศวกรออกแบบคานรองรับเอง
    landing_total_ll_kg: float


def calculate(inp: StairUShapeInput) -> StairUShapeResult:
    # --- แบ่งครึ่งจำนวนขั้น/ความสูงให้ทั้งสองช่วงเท่ากันเสมอ (ข้อ 1) — ปัดจำนวนขั้นรวมให้เป็น
    # เลขคู่เสมอ (ปัดลง แล้วรายงานให้ผู้ใช้ทราบถ้าค่าที่กรอกเป็นเลขคี่) ---
    n_riser_rounded = (inp.n_riser_total % 2) != 0
    n_per_flight = max(int(inp.n_riser_total) // 2, 2)
    n_total_used = n_per_flight * 2

    flight_input = StairStraightInput(
        fc_ksc=inp.fc_ksc,
        main_steel_type=inp.main_steel_type,
        temp_steel_type=inp.temp_steel_type,
        main_bar_dia_mm=inp.main_bar_dia_mm,
        main_bar_spacing_cm=inp.main_bar_spacing_cm,
        temp_bar_dia_mm=inp.temp_bar_dia_mm,
        temp_bar_spacing_cm=inp.temp_bar_spacing_cm,
        wD_kg_m2=inp.wD_kg_m2,
        wL_kg_m2=inp.wL_kg_m2,
        n_riser=n_per_flight,
        length_m=inp.flight_length_m,
        width_m=inp.width_m,
        height_m=inp.height_m / 2.0,
        t_cm=inp.t_cm,
        continuity_case="SS",
    )
    flight_result = calculate_flight(flight_input)

    # --- ชานพัก: แผ่นเรียบหนา t_cm เท่ากัน ไม่มีขั้นบันได (ไม่มี dl_steps) — คำนวณน้ำหนักตัวเอง/
    # น้ำหนักรวม (Service, unfactored) เพื่อเป็นข้อมูลให้วิศวกรออกแบบคาน/ผนังรองรับชานพักเอง
    # (ตามขอบเขตข้อ 2 — โมดูลนี้ไม่คำนวณ Mu/As ของชานพักเอง ใช้เหล็กชุดเดียวกับช่วงบันไดต่อเนื่อง) ---
    t_m = inp.t_cm / 100.0
    landing_dl_self = CONCRETE_UNIT_WEIGHT_KG_M3 * t_m
    landing_wu = 1.4 * (landing_dl_self + inp.wD_kg_m2) + 1.7 * inp.wL_kg_m2
    landing_area = inp.width_m * inp.landing_length_m
    landing_total_dl = (landing_dl_self + inp.wD_kg_m2) * landing_area
    landing_total_ll = inp.wL_kg_m2 * landing_area

    total_horizontal_length_m = 2.0 * inp.flight_length_m + inp.landing_length_m

    return StairUShapeResult(
        n_riser_per_flight=n_per_flight,
        n_riser_total_used=n_total_used,
        n_riser_rounded=n_riser_rounded,
        flight=flight_result,
        total_horizontal_length_m=total_horizontal_length_m,
        landing_dead_load_self_kg_m2=landing_dl_self,
        landing_wu_kg_m2=landing_wu,
        landing_area_m2=landing_area,
        landing_total_dl_kg=landing_total_dl,
        landing_total_ll_kg=landing_total_ll,
    )
