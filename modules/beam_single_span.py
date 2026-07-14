"""
Module 3.1 — คานช่วงเดียว (Single-span Beam)

Scope: คานช่วงเดียวแบบมีจุดรองรับสองด้าน (simply supported, ไม่มี overhang,
ไม่มีความต่อเนื่องไปช่วงอื่น) — ครอบคลุมตั้งแต่การวิเคราะห์หาแรง (reaction/SFD/BMD)
ไปจนถึงออกแบบเหล็กเสริมหลัก (บน/ล่าง รวมกรณีเสริมเหล็กสองชั้น) และเหล็กปลอก (stirrup)
คานต่อเนื่องหลายช่วง (Continuous Beam) และคานยื่น (Cantilever Beam) เป็นขอบเขตของ
โมดูล 3.2/3.3 ตามลำดับ ไม่ได้ครอบคลุมในโมดูลนี้.

อ้างอิง/ที่มา: "SDM Plus_Beam_Analysis.xlsx" (โฟลเดอร์ SDM+beta) — ไฟล์อ้างอิงจริง
รองรับคานต่อเนื่องได้สูงสุด 20 ช่วง + คานยื่นซ้าย/ขวา (overhang) ในตัวเดียวกัน โดยวิเคราะห์
โครงสร้างด้วยวิธี Three Moment Equation (ระบุไว้ในชีท "Input Data", cell BC22) — สำหรับ
โมดูลนี้ (3.1, คานช่วงเดียวแท้ๆ ไม่มี overhang/ความต่อเนื่อง) กรณีพิเศษของ Three Moment
Equation ที่ spans=1 และไม่มี overhang จะลดรูปเหลือแค่ "คานช่วงเดียวรับแรงกระจาย+แรงจุด
แบบ simply supported" ธรรมดา ซึ่งเป็นสถิตยศาสตร์มาตรฐาน (statics) ที่ไม่ต้องพึ่งพา
Three Moment Equation เลย — คำนวณจาก reaction/shear/moment โดยตรง ไม่ได้อ้างอิงตัวเลข
เฉพาะจากไฟล์ (ไฟล์มีแต่ตัวอย่างคานต่อเนื่อง 3 ช่วง ไม่มีตัวอย่างช่วงเดียวโดยตรง) แต่
วิธีการนี้เป็นสถิตยศาสตร์พื้นฐานที่ไม่มีความกำกวม.

สูตรออกแบบเหล็กเสริม (flexure) และเหล็กปลอก (shear/stirrup) ยืนยัน/อ้างอิงจากชีท
"Calculation A" ของไฟล์เดียวกัน (สูตรระบุเป็น label ตรงๆ ในชีท ไม่ใช่ตัวอย่างตัวเลขที่ต้อง
เดา):
  - rho_b = 0.85*beta1*(fc'/fy)*(6120/(6120+fy)) — สูตรเดียวกับ common.design_params
    (compute_rho_b) ยืนยันตรงกันแล้วก่อนหน้านี้ในโมดูลอื่น
  - Ru = Mu/(phi_b*b*d^2), rreq = 0.85(fc'/fy)(1-sqrt(1-2Ru/(0.85fc')))
    — สูตรเดียวกับโมดูลพื้นทุกโมดูล (ยืนยันตรงไฟล์มาแล้วหลายรอบ)
  - rho_min = 14/fy — ตรงกับ note "<< [Use 14/fy]" ในไฟล์ (ยืนยันตรง)
  - Vc = 0.53*sqrt(fc')*b*d, phi_v*Vc — สูตรเดียวกับโมดูลพื้นทุกโมดูล
  - เกณฑ์ stirrup spacing (ACI 318-63 แบบดั้งเดิม): ถ้า Vs<=1.1sqrt(fc')bd ใช้
    s_max=min(d/2,60cm), ถ้า Vs<=2.1sqrt(fc')bd ใช้ s_max=min(d/4,30cm), เกินกว่านั้น
    หน้าตัดเล็กเกินไปต้องขยายขนาด — สอดคล้องกับ label ในไฟล์ "fv1.1(√fc')bd" /
    "fv2.1(√fc')bd" ที่ปรากฏในชีท Calculation A ตรงๆ (คำนวณแล้วแต่ไม่มีตัวอย่างที่
    Vs เกินขีดนี้จริงในไฟล์ให้ยืนยันตัวเลข — ใช้สูตรมาตรฐานตรงตามที่ label ระบุ)

จุดที่ "ยืนยันได้จากป้ายชื่อสูตรในไฟล์ แต่ไม่มีตัวอย่างตัวเลขที่ทำให้เกิดกรณีนั้นจริง"
(ผู้ใช้ทราบและอนุมัติให้ proceed แบบนี้แล้ว ผ่าน AskUserQuestion ก่อนเริ่มเขียนโค้ด):
  - **เหล็กเสริมสองชั้น (doubly-reinforced)**: ไฟล์มีสูตร As2/Mu2/d' ("Mu2=Mu-Mu1",
    "As2=Mu2/fbfy(d-d')") แต่ตัวอย่างในไฟล์ทั้งสองตำแหน่ง (Middle Span, Support Span)
    Mu2=0 เสมอ (ไม่เคยเกิดกรณีเสริมเหล็กสองชั้นจริงในตัวอย่าง) — คำนวณ Mu1_max จาก
    Ru_max ที่ rho_max (=0.75*rho_b มาตรฐาน) แล้วเทียบกับ Mu จริง ถ้า Mu>Mu1_max จึง
    เสริมเหล็กสองชั้น สมมติเหล็กรับแรงอัด fs'=fy (ให้ผลครากเต็มที่ ตามธรรมเนียมตำรามาตรฐาน
    แบบง่าย ไม่ตรวจสอบ fs' อย่างละเอียด) — เป็น edge case ที่ไม่ค่อยเกิดกับคานบ้านพักอาศัย
    ทั่วไป (span/load ระดับที่พบบ่อย) แต่รองรับไว้ตามที่พี่ขอ
  - **การจัดชั้นเหล็กเสริม (bar layering)**: โมดูลนี้จำกัดไว้แค่ "เหล็กเสริมชั้นเดียว"
    (single layer) เท่านั้นในรอบแรกนี้ — ถ้าจำนวนเหล็กที่ต้องการเกินกว่าจะใส่ได้ใน 1 ชั้น
    (ตามความกว้างคาน b, ระยะหุ้ม, ระยะห่างขั้นต่ำระหว่างเหล็ก) จะแจ้งเตือนให้ผู้ใช้ขยาย
    ขนาดคาน/เปลี่ยนขนาดเหล็กใหญ่ขึ้น แทนที่จะจัดชั้นที่ 2 ให้อัตโนมัติ (ไฟล์ DRMK รองรับ
    ได้ถึง 3 ชั้น 6 เส้น/ชั้น — ยังไม่ implement ส่วนนี้ เผื่อทำเพิ่มทีหลังถ้าจำเป็นจริง)
  - **Vu สำหรับออกแบบเหล็กปลอก**: ใช้ค่า max(|R_left|,|R_right|) ตรงๆ (แรงเฉือนสูงสุด
    ที่หน้าตัดรองรับ) ไม่ได้ลดตามระยะ d จากหน้ารองรับแบบที่โมดูลพื้น (one-way) ทำ (สูตร
    "1.15(WuS/2)-Wu·d" ของพื้นเป็นตัวคูณเฉพาะของวิธี coefficient method ของพื้น ไม่ใช่
    ค่ามาตรฐานที่ควรใช้ตรงๆ กับคานที่คำนวณจาก statics จริงอยู่แล้ว) — ยืนยันจากไฟล์ว่า
    Vu ที่ใช้ออกแบบเหล็กปลอกทั้ง Middle Span และ Support Span ในตัวอย่างเป็นค่าเดียวกัน
    (3615.275 ทั้งคู่) สอดคล้องกับการใช้ค่า "max shear ทั้งช่วง" เป็นค่าออกแบบเดียว ไม่ใช่
    ค่าเฉพาะตำแหน่ง

น้ำหนักบรรทุก: Wu = 1.4(DL_line+DL_selfweight) + 1.7(LL_line) ตามกฎกระทรวง พ.ศ. 2566
(ไฟล์ใช้ "1.7DL+2.0LL" แบบเก่า — ตั้งใจให้ต่างกันเหมือนทุกโมดูลก่อนหน้า) น้ำหนักจุด
(point load) แต่ละจุดก็แปลงเป็น Pu = 1.4·P_DL + 1.7·P_LL แยกทีละจุดก่อนรวมเข้าสถิตยศาสตร์
"""

import math
from dataclasses import dataclass, field

from common.design_params import (
    compute_beta1, compute_rho_b, compute_rho_min, compute_rho_max, PHI_B, PHI_V,
)
from modules.slab_on_ground import (
    GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2, CONCRETE_UNIT_WEIGHT_KG_M3,
)

COVER_CM = 3.0                       # ระยะหุ้มคอนกรีตถึงเหล็กปลอก (clear cover to stirrup)
MIN_CLEAR_SPACING_CM = 2.5           # ระยะห่างสุทธิขั้นต่ำระหว่างเหล็กเสริมในชั้นเดียวกัน (แนวนอน)
MAX_BARS_PER_LAYER = 4               # ตามคำสั่งผู้ใช้ (ปรับจากเดิม 6 ตามไฟล์ DRMK): 1 แถวเสริมเหล็กได้ไม่เกิน 4 เส้น
MAX_LAYERS = 3                       # ตามหมายเหตุไฟล์ DRMK: รองรับได้ถึง 3 ชั้น — ถ้าชั้น 1 ไม่พอ เติมชั้น 2/3 อัตโนมัติ
LAYER_CLEAR_SPACING_CM = 2.5         # ระยะห่างสุทธิแนวดิ่งระหว่างชั้นเหล็ก (มาตรฐานทั่วไป เท่ากับระยะห่างแนวนอน)

BEAM_WIDTH_CM_OPTIONS = [15, 20, 25, 30, 35, 40]
BEAM_DEPTH_CM_OPTIONS = [30, 35, 40, 45, 50, 55, 60, 70, 80]

BAR_DIAMETERS_MM = [10, 12, 16, 19, 20, 22, 25, 28, 32]      # เหล็กเสริมหลัก/รับแรงอัด
STIRRUP_DIAMETERS_MM = [6, 9, 10, 12]                        # เหล็กปลอก

DEFAULT_STIRRUP_LEGS = 2   # เหล็กปลอกแบบ 2 ขา (closed stirrup มาตรฐาน)


@dataclass
class PointLoad:
    p_dl_kg: float
    p_ll_kg: float
    x_m: float          # ระยะจากจุดรองรับซ้าย (m.)


@dataclass
class BeamSingleSpanInput:
    fc_ksc: float
    main_steel_type: str        # เหล็กเสริมหลัก (บน/ล่าง)
    stirrup_steel_type: str     # เหล็กปลอก
    b_cm: float
    h_cm: float
    L_m: float
    line_load_dl_kg_m: float
    line_load_ll_kg_m: float
    point_loads: list           # list[PointLoad]
    main_bar_dia_mm: float
    stirrup_bar_dia_mm: float
    stirrup_legs: int = DEFAULT_STIRRUP_LEGS
    left_fixed: bool = False     # จุดรองรับปลายซ้ายเป็นแบบยึดแน่น (Fix) — False=Pin (default)
    right_fixed: bool = False    # จุดรองรับปลายขวาเป็นแบบยึดแน่น (Fix) — False=Pin (default)
    stirrup_spacing_use_cm: float = 15.0   # ระยะห่างเหล็กปลอกที่ผู้ใช้เลือกใช้จริง


@dataclass
class FlexureDesign:
    mu_kgm: float
    d_cm: float
    ru_ksc: float
    doubly_reinforced: bool
    mu1_kgm: float               # โมเมนต์ที่รับได้แบบเสริมเหล็กชั้นเดียวสูงสุด (ที่ rho_max)
    mu2_kgm: float                # โมเมนต์ส่วนเกิน (ถ้ามี) ที่ต้องใช้เหล็กรับแรงอัดช่วย
    rreq: float
    rho_used: float
    as_req_cm2: float             # เหล็กรับแรงดึงที่ต้องการทั้งหมด (As1+As2)
    as_comp_req_cm2: float        # เหล็กรับแรงอัดที่ต้องการ (As2, ถ้าเสริมสองชั้น)
    n_bars_req: int
    n_bars_use: int
    as_provided_cm2: float
    fits_single_layer: bool
    max_bars_single_layer: int
    reinf_ok: bool
    n_layers: int = 1                 # จำนวนชั้นเหล็กที่ใช้จริง (1=ชั้นเดียว, >1=จัดชั้นที่ 2/3 อัตโนมัติ)
    bars_per_layer: list = field(default_factory=lambda: [0])   # จำนวนเส้นต่อชั้น เรียงจากชั้นใกล้ผิวรับแรงดึงสุดออกไป


@dataclass
class StirrupDesign:
    vu_kg: float
    vc_kg: float                  # กำลังรับแรงเฉือนคอนกรีต (ไม่คูณ phi)
    phi_vc_kg: float
    vs_req_kg: float
    limit_1p1_kg: float           # phi*1.1*sqrt(fc')*b*d — เกณฑ์เปลี่ยนช่วง s_max
    limit_2p1_kg: float           # phi*2.1*sqrt(fc')*b*d — เกณฑ์หน้าตัดเล็กเกินไป
    section_too_small: bool
    av_cm2: float
    s_max_from_vs_cm: float
    s_max_code_cm: float
    s_max_cm: float
    s_use_cm: float
    stirrup_ok: bool


@dataclass
class BeamSingleSpanResult:
    self_weight_kg_m: float
    wd_total_kg_m: float
    wu_kg_m: float
    pu_loads: list                # list[(x_m, pu_kg)]
    r_left_kg: float
    r_right_kg: float
    vu_max_kg: float
    mu_max_kg_m: float
    mu_max_x_m: float
    x_arr: list                   # สำหรับวาดกราฟ SFD/BMD
    v_arr: list
    m_arr: list
    beta1: float
    rho_b: float
    rho_min: float
    rho_max: float
    bottom: FlexureDesign          # เหล็กล่าง (ตามโมเมนต์บวกสูงสุด)
    top: FlexureDesign             # เหล็กบน (nominal, As_req=0 เสมอสำหรับคานช่วงเดียว)
    stirrup: StirrupDesign
    main_bar_type: str
    stirrup_bar_type: str
    reinf_label_bottom: str
    reinf_label_top: str
    reinf_label_stirrup: str
    left_fixed: bool = False
    right_fixed: bool = False
    m_a_kgm: float = 0.0          # โมเมนต์ดัดที่จุดรองรับซ้าย (ลบ=hogging; 0 เมื่อ Pin)
    m_b_kgm: float = 0.0          # โมเมนต์ดัดที่จุดรองรับขวา
    mu_neg_max_kgm: float = 0.0   # โมเมนต์ลบสูงสุด (ขนาด) — ใช้ออกแบบเหล็กบน


def _max_bars_single_layer(b_cm: float, main_dia_mm: float, stirrup_dia_mm: float) -> int:
    """จำนวนเหล็กเสริมหลักสูงสุดที่ใส่ได้ใน 1 ชั้น ตามความกว้างคาน b, ระยะหุ้ม,
    ขนาดเหล็กปลอก และระยะห่างสุทธิขั้นต่ำระหว่างเหล็กเสริม (MIN_CLEAR_SPACING_CM)."""
    edge = COVER_CM + stirrup_dia_mm / 10.0
    avail_width_cm = b_cm - 2.0 * edge - main_dia_mm / 10.0
    if avail_width_cm < 0:
        return 0
    pitch = main_dia_mm / 10.0 + MIN_CLEAR_SPACING_CM
    n = int(math.floor(avail_width_cm / pitch)) + 1
    return max(0, min(n, MAX_BARS_PER_LAYER))


def _distribute_bars_layers(n_bars: int, max_per_layer: int) -> list:
    """แจกจำนวนเหล็กทั้งหมดออกเป็นชั้นๆ (สูงสุด MAX_LAYERS ชั้น, ไม่เกิน MAX_BARS_PER_LAYER=4
    เส้น/ชั้น) — เติมชั้นที่ 1 (ใกล้ผิวรับแรงดึงสุด ให้ d มากที่สุด ประหยัดเหล็กสุด) ให้เต็มก่อน
    เสมอตามมาตรฐานทั่วไป แล้วค่อยล้นไปชั้นถัดไปเมื่อไม่พอ — คืน list เช่น [4,2] หมายถึงชั้น 1
    มี 4 เส้น ชั้น 2 มี 2 เส้น.

    ห้ามวางเหล็กไว้กลางแถวเดี่ยวๆ เส้นเดียว (ตามคำสั่งผู้ใช้): ถ้าการแจกแบบเติมเต็มชั้นแรกก่อน
    ทำให้ชั้นสุดท้ายเหลือเหล็กแค่ 1 เส้น (เช่น 5 เส้น จัดเต็มชั้น 1=4 จะเหลือชั้น 2=1 เส้นเดี่ยวๆ
    กลางแถว) ให้ยืมเหล็ก 1 เส้นจากชั้นก่อนหน้ามาสมทบ ทำให้ชั้นสุดท้ายมีอย่างน้อย 2 เส้นเสมอ
    (5 เส้น -> 3+2 แทน 4+1, 9 เส้น -> 4+3+2 แทน 4+4+1) — ยกเว้นกรณีคานแคบมากจน
    max_per_layer<=1 ที่ไม่มีทางเลี่ยงเหล็กเดี่ยวได้ทางกายภาพ."""
    if n_bars <= 0 or max_per_layer <= 0:
        return [0]
    layers = []
    remaining = n_bars
    for _ in range(MAX_LAYERS):
        take = min(remaining, max_per_layer)
        layers.append(take)
        remaining -= take
        if remaining <= 0:
            break
    if len(layers) > 1 and layers[-1] == 1 and layers[-2] >= 2:
        layers[-2] -= 1
        layers[-1] += 1
    return layers


def _layer_y_distances_cm(n_layers: int, cover_cm: float, stirrup_dia_mm: float, main_dia_mm: float) -> list:
    """ระยะจากผิวคอนกรีตด้านรับแรงดึง ถึง centroid ของเหล็กแต่ละชั้น (ชั้น 1 = ใกล้ผิวสุด)
    เรียงชั้นถัดไปห่างออกด้วยระยะห่างสุทธิแนวดิ่งมาตรฐาน (LAYER_CLEAR_SPACING_CM)."""
    edge = cover_cm + stirrup_dia_mm / 10.0 + main_dia_mm / 10.0 / 2.0
    pitch = main_dia_mm / 10.0 + LAYER_CLEAR_SPACING_CM
    return [edge + i * pitch for i in range(n_layers)]


def _effective_depth_multilayer(h_cm: float, layers: list, ys: list) -> float:
    """ระยะประสิทธิผล d จริงเมื่อเสริมเหล็กหลายชั้น = h - ระยะถ่วงน้ำหนักตามพื้นที่ (ประมาณ
    ด้วยจำนวนเส้น เพราะเหล็กหลักทุกเส้นใช้ขนาดเดียวกันในหน้าตัดเดียวกัน) ถึง centroid รวม."""
    total = sum(layers)
    if total <= 0:
        return h_cm
    ybar = sum(n * y for n, y in zip(layers, ys)) / total
    return h_cm - ybar


def _flexure_design(mu_kgm: float, b_cm: float, h_cm: float, fc_ksc: float, fy_ksc: float,
                     main_bar_dia_mm: float, stirrup_bar_dia_mm: float,
                     beta1: float, rho_b: float, rho_min: float, rho_max: float,
                     is_nominal_only: bool = False) -> FlexureDesign:
    """ออกแบบเหล็กเสริมด้านที่มีโมเมนต์ mu_kgm (แรงดึง) — is_nominal_only=True สำหรับ
    เหล็กบนของคานช่วงเดียว (ไม่มีโมเมนต์ลบจริง ใช้แค่เหล็กยึดเหล็กปลอกขั้นต่ำ 2 เส้น
    ตาม pattern ที่ยืนยันจากไฟล์ DRMK: As_req=0 แต่ As_use ยังมีอยู่).

    รองรับการจัดชั้นเหล็กหลายชั้น (สูงสุด MAX_LAYERS=3 ชั้น ตามหมายเหตุไฟล์ DRMK) — ถ้า
    จำนวนเหล็กที่ต้องการเกินกว่าจะใส่ได้ใน 1 ชั้น จะเติมชั้นที่ 2/3 อัตโนมัติแทนการแจ้งเตือน
    ให้ขยายขนาดคาน (เดิมรองรับแค่ชั้นเดียว) — d ที่แท้จริงจะลดลงตามระยะ centroid ของเหล็ก
    หลายชั้น จึงวนคำนวณซ้ำ (iterate) จนกว่าจำนวนเหล็ก/d จะลงตัว (เกิดจาก As ต้องการเปลี่ยน
    ตาม d ที่เปลี่ยนตามจำนวนชั้น)."""
    max_bars_layer1 = _max_bars_single_layer(b_cm, main_bar_dia_mm, stirrup_bar_dia_mm)
    d_cm = h_cm - COVER_CM - stirrup_bar_dia_mm / 10.0 - main_bar_dia_mm / 10.0 / 2.0

    if is_nominal_only or mu_kgm <= 0:
        n_req = 2 if max_bars_layer1 >= 2 else max(max_bars_layer1, 1)
        layers = _distribute_bars_layers(n_req, max_bars_layer1)
        if len(layers) > 1:
            ys = _layer_y_distances_cm(len(layers), COVER_CM, stirrup_bar_dia_mm, main_bar_dia_mm)
            d_cm = _effective_depth_multilayer(h_cm, layers, ys)
        as_provided = n_req * bar_area_cm2(main_bar_dia_mm)
        return FlexureDesign(
            mu_kgm=0.0, d_cm=d_cm, ru_ksc=0.0, doubly_reinforced=False,
            mu1_kgm=0.0, mu2_kgm=0.0, rreq=0.0, rho_used=0.0,
            as_req_cm2=0.0, as_comp_req_cm2=0.0,
            n_bars_req=n_req, n_bars_use=n_req, as_provided_cm2=as_provided,
            fits_single_layer=(len(layers) <= 1), max_bars_single_layer=max_bars_layer1,
            n_layers=len(layers), bars_per_layer=layers,
            reinf_ok=(n_req <= max_bars_layer1 * MAX_LAYERS),
        )

    n_bars_req = 0
    layers = [0]
    ru = rreq = rho_used = as_req = as_comp_req = mu2 = 0.0
    mu1_report = mu_kgm
    doubly = False
    for _ in range(4):   # วนซ้ำจนกว่า d/จำนวนเหล็ก/จำนวนชั้นจะลงตัว (โดยทั่วไปลู่เข้า 2-3 รอบ)
        ru = (mu_kgm * 100.0) / (PHI_B * b_cm * d_cm ** 2)
        ru_max = rho_max * fy_ksc * (1.0 - 0.59 * rho_max * fy_ksc / fc_ksc)
        mu1_max_kgm = (PHI_B * ru_max * b_cm * d_cm ** 2) / 100.0

        if mu_kgm <= mu1_max_kgm:
            under_sqrt = 1.0 - (2.0 * ru) / (0.85 * fc_ksc)
            under_sqrt = max(under_sqrt, 0.0)
            rreq = 0.85 * (fc_ksc / fy_ksc) * (1.0 - math.sqrt(under_sqrt))
            rho_used = max(rreq, rho_min)
            as_req = rho_used * b_cm * d_cm
            as_comp_req = 0.0
            doubly = False
            mu2 = 0.0
            mu1_report = mu_kgm
        else:
            doubly = True
            mu1_report = mu1_max_kgm
            mu2 = mu_kgm - mu1_max_kgm
            rreq = rho_max
            rho_used = rho_max
            as1 = rho_max * b_cm * d_cm
            d_prime_cm = COVER_CM + stirrup_bar_dia_mm / 10.0 + main_bar_dia_mm / 10.0 / 2.0
            as2 = (mu2 * 100.0) / (PHI_B * fy_ksc * max(d_cm - d_prime_cm, 1.0))
            as_req = as1 + as2
            as_comp_req = as2

        n_bars_new = max(1, math.ceil(as_req / bar_area_cm2(main_bar_dia_mm)))
        layers_new = _distribute_bars_layers(n_bars_new, max_bars_layer1)
        if len(layers_new) > 1:
            ys = _layer_y_distances_cm(len(layers_new), COVER_CM, stirrup_bar_dia_mm, main_bar_dia_mm)
            d_new = _effective_depth_multilayer(h_cm, layers_new, ys)
        else:
            d_new = h_cm - COVER_CM - stirrup_bar_dia_mm / 10.0 - main_bar_dia_mm / 10.0 / 2.0

        converged = (n_bars_new == n_bars_req) and (abs(d_new - d_cm) < 1e-6)
        n_bars_req, layers, d_cm = n_bars_new, layers_new, d_new
        if converged:
            break

    # n_bars_req = จำนวนเหล็กที่ "ต้องการ" ตามทฤษฎี (ไม่ถูก cap) — ใช้แสดงในข้อความเตือนตอน
    # เกินขีดจำกัด — ส่วนจำนวนที่ "ใช้จริง"/As ที่ใช้จริง ต้อง cap ตามที่จัดชั้นได้จริง
    # (sum(layers), สูงสุด MAX_LAYERS ชั้น) ไม่งั้น As ที่ใช้จริงจะโป่งเกินกว่าที่วาดจริงในรูปตัด
    n_bars_use = sum(layers)
    as_provided = n_bars_use * bar_area_cm2(main_bar_dia_mm)
    fits_single_layer = len(layers) <= 1
    max_total_bars = max_bars_layer1 * MAX_LAYERS

    return FlexureDesign(
        mu_kgm=mu_kgm, d_cm=d_cm, ru_ksc=ru, doubly_reinforced=doubly,
        mu1_kgm=mu1_report, mu2_kgm=mu2, rreq=rreq, rho_used=rho_used,
        as_req_cm2=as_req, as_comp_req_cm2=as_comp_req,
        n_bars_req=n_bars_req, n_bars_use=n_bars_use, as_provided_cm2=as_provided,
        fits_single_layer=fits_single_layer, max_bars_single_layer=max_bars_layer1,
        n_layers=len(layers), bars_per_layer=layers,
        reinf_ok=(as_provided >= as_req and n_bars_req <= max_total_bars),
    )


def reinf_label_with_layers(flex: FlexureDesign, bar_type: str, dia_mm: float) -> str:
    """สร้าง label เหล็กเสริม เช่น '8-DB16' (ชั้นเดียว) หรือ '8-DB16 (2 ชั้น: 6+2)' (หลายชั้น)
    — factored ออกมาให้ทั้ง 3.1/3.2 ใช้ร่วมกัน กันบั๊กจากการต่อ string ซ้ำคนละที่."""
    total = flex.n_bars_use
    base = f"{total}-{bar_type}{dia_mm:.0f}"
    if flex.n_layers <= 1:
        return base
    breakdown = "+".join(str(n) for n in flex.bars_per_layer if n > 0)
    return f"{base} ({flex.n_layers} ชั้น: {breakdown})"


def _stirrup_design(vu_max_kg: float, b_cm: float, d_cm: float, fc_ksc: float, fy_stirrup: float,
                     stirrup_legs: int, stirrup_bar_dia_mm: float,
                     stirrup_spacing_use_cm: float) -> StirrupDesign:
    """ออกแบบเหล็กปลอก (stirrup) จาก Vu governing ค่าเดียว (max shear ในช่วง/ตำแหน่งนั้นๆ)
    factored ออกมาจาก calculate() เพื่อให้โมดูล 3.2 (คานต่อเนื่อง) เรียกใช้ซ้ำได้ต่อ
    span/support โดยไม่ต้องคัดลอกสูตรซ้ำ (กันบั๊กจากการ copy-paste สูตร)."""
    vc = 0.53 * math.sqrt(fc_ksc) * b_cm * d_cm
    phi_vc = PHI_V * vc
    vs_req = max(0.0, vu_max_kg / PHI_V - vc)
    limit_1p1 = 1.1 * math.sqrt(fc_ksc) * b_cm * d_cm
    limit_2p1 = 2.1 * math.sqrt(fc_ksc) * b_cm * d_cm
    section_too_small = vs_req > limit_2p1

    av = stirrup_legs * bar_area_cm2(stirrup_bar_dia_mm)
    if vs_req > 0:
        s_from_vs = av * fy_stirrup * d_cm / vs_req
    else:
        s_from_vs = 999.0

    if vs_req <= limit_1p1:
        s_max_code = min(d_cm / 2.0, 60.0)
    elif vs_req <= limit_2p1:
        s_max_code = min(d_cm / 4.0, 30.0)
    else:
        s_max_code = min(d_cm / 4.0, 30.0)   # แสดงค่าไว้อ้างอิง แม้ section_too_small=True

    s_max = min(s_from_vs, s_max_code)
    stirrup_ok = (not section_too_small) and (stirrup_spacing_use_cm <= s_max)

    return StirrupDesign(
        vu_kg=vu_max_kg, vc_kg=vc, phi_vc_kg=phi_vc, vs_req_kg=vs_req,
        limit_1p1_kg=limit_1p1, limit_2p1_kg=limit_2p1,
        section_too_small=section_too_small, av_cm2=av,
        s_max_from_vs_cm=s_from_vs, s_max_code_cm=s_max_code, s_max_cm=s_max,
        s_use_cm=stirrup_spacing_use_cm, stirrup_ok=stirrup_ok,
    )


def calculate(inp: BeamSingleSpanInput) -> BeamSingleSpanResult:
    fy_main = GS_STEEL_FY_KSC[inp.main_steel_type]
    fy_stirrup = GS_STEEL_FY_KSC[inp.stirrup_steel_type]

    b_m = inp.b_cm / 100.0
    h_m = inp.h_cm / 100.0
    self_weight = CONCRETE_UNIT_WEIGHT_KG_M3 * b_m * h_m   # kg/m
    wd_total = inp.line_load_dl_kg_m + self_weight
    wu = 1.4 * wd_total + 1.7 * inp.line_load_ll_kg_m

    pts = sorted(inp.point_loads, key=lambda p: p.x_m)
    pu_loads = [(p.x_m, 1.4 * p.p_dl_kg + 1.7 * p.p_ll_kg) for p in pts]

    L = inp.L_m
    sum_pu = sum(pu for _, pu in pu_loads)
    # --- ปฏิกิริยา/แรงเฉือน/โมเมนต์ของคานยึดหมุน (simply supported, released structure) ---
    moment_about_right = wu * L * (L / 2.0) + sum(pu * (L - x) for x, pu in pu_loads)
    r_left_ss = moment_about_right / L if L > 0 else 0.0
    r_right_ss = wu * L + sum_pu - r_left_ss

    def _shear_ss(x: float, include_load_at_x: bool = True) -> float:
        v = r_left_ss - wu * x
        for xi, pu in pu_loads:
            if (xi < x) or (include_load_at_x and abs(xi - x) < 1e-9):
                v -= pu
        return v

    def _moment_ss(x: float) -> float:
        m = r_left_ss * x - wu * x ** 2 / 2.0
        for xi, pu in pu_loads:
            if xi <= x:
                m -= pu * (x - xi)
        return m

    # --- จุดรองรับแบบยึดแน่น (Fix): หาโมเมนต์ปลาย M_A/M_B ด้วยวิธี flexibility (consistent
    #     deformation). โมเมนต์ปลายไม่ขึ้นกับ EI สำหรับคานช่วงเดียวปริซึม — คำนวณจากการหมุนปลาย
    #     ของคานยึดหมุนภายใต้โหลด (a_A, a_B = θ·EI) แล้วบังคับให้การหมุนที่ปลายยึดแน่น = 0.
    #     ยืนยันกับสูตรมือ: UDL Fix-Fix → −wL²/12, Fix-Pin → −wL²/8 ; จุดกลาง Fix-Pin → −3PL/16 ---
    m_a = m_b = 0.0
    if L > 1e-9:
        _NI = 240
        _xsI = [L * i / _NI for i in range(_NI + 1)]
        _M0I = [_moment_ss(xx) for xx in _xsI]

        def _trap(vals):
            s = 0.0
            for i in range(len(_xsI) - 1):
                s += (vals[i] + vals[i + 1]) / 2.0 * (_xsI[i + 1] - _xsI[i])
            return s

        a_A = _trap([m * (L - xx) for m, xx in zip(_M0I, _xsI)]) / L   # = θ_A0 · EI
        a_B = _trap([m * xx for m, xx in zip(_M0I, _xsI)]) / L         # = θ_B0 · EI
        lf, rf = inp.left_fixed, inp.right_fixed
        if lf and rf:
            m_a = (-4.0 * a_A + 2.0 * a_B) / L
            m_b = (2.0 * a_A - 4.0 * a_B) / L
        elif lf:
            m_a = -3.0 * a_A / L
        elif rf:
            m_b = -3.0 * a_B / L

    dV = (m_b - m_a) / L if L > 1e-9 else 0.0   # แรงเฉือนคงที่ที่เพิ่มจากโมเมนต์ปลาย
    r_left = r_left_ss + dV
    r_right = r_right_ss - dV

    def shear_at(x: float, include_load_at_x: bool = True) -> float:
        return _shear_ss(x, include_load_at_x) + dV

    def moment_at(x: float) -> float:
        frac = (x / L) if L > 1e-9 else 0.0
        return _moment_ss(x) + m_a * (1.0 - frac) + m_b * frac

    # --- หาโมเมนต์บวกสูงสุด: ค้นหาจุด V=0 ในแต่ละช่วงระหว่างแรงจุด (segment) ---
    boundaries = [0.0] + [x for x, _ in pu_loads] + [L]
    boundaries = sorted(set(boundaries))
    critical_x = set(boundaries)
    for i in range(len(boundaries) - 1):
        x_start, x_end = boundaries[i], boundaries[i + 1]
        v_start = shear_at(x_start, include_load_at_x=True)
        if wu > 0:
            x_star = x_start + v_start / wu
            if x_start <= x_star <= x_end:
                critical_x.add(x_star)

    mu_max = -1.0
    mu_max_x = 0.0
    # เพิ่มปลายทั้งสอง (จุดรองรับยึดแน่นมีโมเมนต์จริง) เข้าไปในจุดวิกฤตด้วย
    for x in critical_x | {0.0, L}:
        m = moment_at(x)
        if m > mu_max:
            mu_max = m
            mu_max_x = x
    mu_max = max(mu_max, 0.0)

    # --- อาเรย์สำหรับวาดกราฟ SFD/BMD (sample ละเอียด + จุดหักเห/แรงจุดทุกจุด) ---
    n_samples = 120
    xs = sorted(set(
        [i * L / n_samples for i in range(n_samples + 1)] + list(critical_x)
    ))
    x_arr, v_arr, m_arr = [], [], []
    for x in xs:
        x_arr.append(x)
        v_arr.append(shear_at(x, include_load_at_x=False))
        m_arr.append(moment_at(x))
        # เพิ่มจุดหลังแรงจุดทันที เพื่อให้กราฟ SFD แสดง "การกระโดด" (step) ชัดเจน
        for xi, pu in pu_loads:
            if abs(xi - x) < 1e-9:
                x_arr.append(x)
                v_arr.append(shear_at(x, include_load_at_x=True))
                m_arr.append(moment_at(x))

    # แรงเฉือน/โมเมนต์ลบสูงสุดจากอาเรย์จริง (รองรับกรณี Fix ที่ค่าสุดขั้วอยู่ปลาย)
    vu_max = max(abs(v) for v in v_arr) if v_arr else max(abs(r_left), abs(r_right))
    mu_neg_max = max(0.0, -min(m_arr)) if m_arr else 0.0

    beta1 = compute_beta1(inp.fc_ksc)
    rho_b = compute_rho_b(inp.fc_ksc, fy_main, beta1)
    rho_min = compute_rho_min(fy_main)
    rho_max = compute_rho_max(rho_b)

    bottom = _flexure_design(
        mu_max, inp.b_cm, inp.h_cm, inp.fc_ksc, fy_main,
        inp.main_bar_dia_mm, inp.stirrup_bar_dia_mm,
        beta1, rho_b, rho_min, rho_max, is_nominal_only=False,
    )
    # เหล็กบน: ถ้ามีจุดรองรับยึดแน่น (มีโมเมนต์ลบจริง) ออกแบบตามโมเมนต์ลบสูงสุด — มิฉะนั้น nominal
    _top_nominal = mu_neg_max < 1e-6
    top = _flexure_design(
        mu_neg_max, inp.b_cm, inp.h_cm, inp.fc_ksc, fy_main,
        inp.main_bar_dia_mm, inp.stirrup_bar_dia_mm,
        beta1, rho_b, rho_min, rho_max, is_nominal_only=_top_nominal,
    )

    # --- ออกแบบเหล็กปลอก (stirrup) — ใช้ d ของเหล็กล่าง (ตำแหน่งวิกฤตแรงดึงหลัก) ---
    d_cm = bottom.d_cm
    stirrup = _stirrup_design(
        vu_max, inp.b_cm, d_cm, inp.fc_ksc, fy_stirrup,
        inp.stirrup_legs, inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm,
    )

    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    stirrup_bar_type = GS_STEEL_BAR_TYPE[inp.stirrup_steel_type]

    reinf_label_bottom = reinf_label_with_layers(bottom, main_bar_type, inp.main_bar_dia_mm)
    reinf_label_top = reinf_label_with_layers(top, main_bar_type, inp.main_bar_dia_mm)
    reinf_label_stirrup = f"{inp.stirrup_legs}-{stirrup_bar_type}{inp.stirrup_bar_dia_mm:.0f}@{inp.stirrup_spacing_use_cm:.0f}cm."

    return BeamSingleSpanResult(
        self_weight_kg_m=self_weight, wd_total_kg_m=wd_total, wu_kg_m=wu,
        pu_loads=pu_loads, r_left_kg=r_left, r_right_kg=r_right,
        vu_max_kg=vu_max, mu_max_kg_m=mu_max, mu_max_x_m=mu_max_x,
        x_arr=x_arr, v_arr=v_arr, m_arr=m_arr,
        beta1=beta1, rho_b=rho_b, rho_min=rho_min, rho_max=rho_max,
        bottom=bottom, top=top, stirrup=stirrup,
        main_bar_type=main_bar_type, stirrup_bar_type=stirrup_bar_type,
        reinf_label_bottom=reinf_label_bottom, reinf_label_top=reinf_label_top,
        reinf_label_stirrup=reinf_label_stirrup,
        left_fixed=inp.left_fixed, right_fixed=inp.right_fixed,
        m_a_kgm=m_a, m_b_kgm=m_b, mu_neg_max_kgm=mu_neg_max,
    )
