"""
Module 4.2 — เสากลม (Circular Spiral Column)

ขอบเขต: เสากลมมีเหล็กปลอกเกลียว (spiral column, ไม่ใช่เสากลมปลอกเดี่ยว/circular-tied ซึ่ง
พบน้อยกว่ามากในทางปฏิบัติ) รับแรงตามแนวแกน (Pu) ร่วมกับโมเมนต์ดัดทิศทางเดียว (uniaxial
bending) — เหมือนขอบเขตของโมดูล 4.1 เสาสี่เหลี่ยมทุกประการ ต่างกันแค่รูปร่างหน้าตัด/ชนิดเหล็ก
ปลอก (spiral แทน tie เดี่ยว) และค่าคงที่ตัวคูณลดกำลัง (φ) ที่สูงกว่าตามข้อกำหนด ACI 318
สำหรับเสาปลอกเกลียวโดยเฉพาะ — ยังไม่รองรับโมเมนต์สองทิศทาง (biaxial bending) เหมือนโมดูล 4.1

ที่มา/ยืนยันขอบเขต: ไฟล์อ้างอิง "SDM Plus_Column_Spiral Pu.xlsx" (โฟลเดอร์ SDM+beta) เป็นไฟล์
เดียวที่มีสำหรับเสากลม (แยกจาก "SDM Plus_Column_Tied Pu.xlsx" ที่ใช้อ้างอิง φc ของโมดูล 4.1)
— ตรวจสอบพบว่าไฟล์นี้ออกแบบเฉพาะแรงตามแนวแกนอย่างเดียว (ไม่มีช่องกรอกโมเมนต์ Mu เลย, ตรวจแค่
φPn,max >= Pu + ระยะห่างเกลียว) ต่างจากโมดูล 4.1 ที่รองรับ P-M interaction diagram เต็มรูปแบบ
— ถามผู้ใช้ผ่าน AskUserQuestion ก่อนเขียนโค้ด (2026-07-11): ผู้ใช้เลือก **"รองรับโมเมนต์ด้วย
(แนะนำ)"** จึงขยายขอบเขตเกินกว่าไฟล์อ้างอิง (ตามหลักการเดียวกับที่โมดูล 5.1/5.2 ขยายขอบเขตให้
auto-design แทนที่จะให้ผู้ใช้ลองผิดลองถูกเอง) — ใช้วิธี **strain compatibility + Whitney stress
block บนหน้าตัดวงกลม (circular segment)** สร้าง P-M interaction diagram เต็มรูปแบบเหมือนโมดูล
4.1 (ใช้ strain-compatibility engine เดียวกัน ต่างแค่สูตรพื้นที่ block คอนกรีต — ดูหัวข้อด้านล่าง)

ค่าคงที่ที่ยืนยันตรงกับไฟล์อ้างอิง SDM Plus_Column_Spiral Pu.xlsx (ต่างจากไฟล์ Tied ของ
โมดูล 4.1 ตามที่ระบุไว้ใน common/design_params.py):
  - **φc = 0.75** (cell H12, เทียบกับ 0.70 ของไฟล์ Tied) — ตามข้อกำหนด ACI 318 21.2.2
  - **φPn,max = 0.85·φc·Po** (cell GA50 = 0.85*H12*Po, เทียบกับ 0.80 ของเสาปลอกเดี่ยว) — ตาม
    ACI 318 22.4.2.1 (เสาปลอกเกลียวยอมให้ eccentricity ขั้นต่ำน้อยกว่าเสาปลอกเดี่ยว เพราะเหล็ก
    ปลอกเกลียวยึดรั้งคอนกรีตแกนกลาง (confinement) ได้ดีกว่าปลอกเดี่ยว)
  - **As_min = 0.01·Ag (1%)** (cell GA44) — เท่ากับเสาปลอกเดี่ยว
  - **จำนวนเหล็กเสริมหลักขั้นต่ำ 6 เส้น** (ไม่พบระบุชัดเจนในไฟล์ แต่เป็นข้อกำหนดมาตรฐาน ACI 318
    10.7.3.1/25.7.3 สำหรับเสาปลอกเกลียวทุกกรณี ต่างจากปลอกเดี่ยวที่ขั้นต่ำ 4 เส้น)
  - **ตำแหน่งเหล็กเสริม**: กระจายสม่ำเสมอรอบเส้นรอบวง เริ่มจากมุม 0° (แนวนอน) แล้วเว้นระยะเชิงมุม
    เท่ากัน 360°/N — ยืนยันจากสูตรตาราง WW48/WO49-68 ของไฟล์ (มุมเพิ่มทีละ 2π/N เริ่มจาก 0)

**ค่าที่ไฟล์อ้างอิงไม่ได้คำนวณจากสูตรจริง (ค่าคงที่/manual input ล้วนๆ) — โมดูลนี้ปรับปรุงให้
เป็นสูตรมาตรฐาน ACI 318 แทน (auto-design แทนที่การกรอกมือ)**:
  - **ระยะห่างเหล็กปลอกเกลียว (spiral pitch, "s")**: ไฟล์อ้างอิงใช้ค่าคงที่ "Maximum Recommend"
    = 0.075 m. (7.5 ซม.) ตายตัว (cell I33/P25 เป็นตัวเลขกรอกตรง ไม่ใช่สูตร) ไม่ได้คำนวณจาก
    อัตราส่วนเหล็กปลอกเกลียวที่ต้องการจริง (ρs) เลย — โมดูลนี้คำนวณ s_max จากสูตร ACI 318
    25.7.3 เต็มรูปแบบแทน:
      ρs,min = 0.45·(Ag/Ach − 1)·(f'c/fyt)   (Ach = พื้นที่แกนกลาง = π/4·Dc², Dc = D − 2·cover)
      s_max,strength = 4·Asp/(Dc·ρs,min)      (Asp = พื้นที่หน้าตัดเหล็กปลอกเกลียว 1 เส้น)
      s_max,code = ขนาดเหล็กปลอก + 7.5 ซม.     (ACI 318 25.7.3.3: clear spacing ≤ 7.5 ซม.)
      s_min,code = ขนาดเหล็กปลอก + 2.5 ซม.     (ACI 318 25.7.3.3: clear spacing ≥ 2.5 ซม.)
      s_max ใช้จริง = min(s_max,strength, s_max,code)
    ตรวจสอบ s_use อยู่ในช่วง [s_min,code, s_max] — เข้มงวดกว่าไฟล์อ้างอิงที่เช็คแค่ s_use<=7.5cm
    คงที่ (ไม่ได้พิจารณาว่าขนาดเสา/ปริมาณเหล็กปลอกจริงเพียงพอหรือไม่)

สูตรหลักที่ใช้สำหรับ P-M interaction diagram หน้าตัดวงกลม (ใหม่ทั้งหมด ไม่มีในไฟล์อ้างอิง —
ขยายจากเอนจินเดียวกับโมดูล 4.1 แต่เปลี่ยนสูตรพื้นที่ block คอนกรีตจากสี่เหลี่ยมเป็นวงกลม):
  - **พื้นที่ compression block เป็นส่วนตัดวงกลม (circular segment)**: กำหนดความลึก block
    a = min(β1·c, D) จากผิวรับแรงอัดสุด — พื้นที่ส่วนตัด (segment) รัศมี R=D/2 ที่ความสูง a:
      θ = 2·arccos((R−a)/R),  Area = (R²/2)·(θ − sinθ)
      ระยะจากศูนย์กลางวงกลมถึงเซนทรอยด์ของส่วนตัด = (4R·sin³(θ/2)) / (3(θ−sinθ))
    (สูตรมาตรฐานเรขาคณิตวงกลม ใช้กันทั่วไปในซอฟต์แวร์ออกแบบเสากลม เช่น PCA/spColumn — เมื่อ
    a→0 พื้นที่→0, เมื่อ a→2R (เต็มหน้าตัด) พื้นที่→πR² ตรงกับ Ag พอดี, เมื่อ a=R (ครึ่งวงกลม)
    พื้นที่=πR²/2 และเซนทรอยด์ห่างจากศูนย์กลาง 4R/3π ตรงกับสูตรครึ่งวงกลมมาตรฐาน — ยืนยันด้วย
    เคสทดสอบเหล่านี้)
  - เหล็กเสริมแต่ละเส้น (ไม่ได้จัดกลุ่มเป็นชั้นเหมือนเสาเหลี่ยม เพราะตำแหน่งกระจายรอบวงไม่ได้อยู่
    y เดียวกันเป็นคู่ๆ เท่านั้น) คำนวณ strain/แรงแยกเส้นต่อเส้นด้วยวิธีเดียวกับโมดูล 4.1 ทุกประการ
    (εi=ecu(c-di)/c, fs=clamp(Es·ε,-fy,fy), หักพื้นที่คอนกรีตที่ถูกแทนที่ถ้าเหล็กอยู่ในโซนอัด)
  - φ แปรผันตาม net tensile strain ของเหล็กเส้นที่ไกลผิวรับแรงอัดสุด (ACI 318 21.2.2 unified
    provisions) เหมือนโมดูล 4.1 ทุกประการ แต่ใช้ φc=0.75 (PHI_C_SPIRAL) แทน φc=0.70 (PHI_C)
    เป็นค่าต่ำสุดของช่วง interpolate

สมมติฐาน/ขอบเขตอื่นที่ตัดออก (เหมือนโมดูล 4.1 ทุกประการ):
  - **Biaxial bending**: ยังไม่รองรับ
  - **ผลกระทบความชะลูด**: ใช้สูตร ACI 318 6.6.4.5 เดียวกับโมดูล 4.1 ทุกประการ (k=1.0, Cm=1.0,
    βdns ปรับได้) ต่างแค่รัศมีไจเรชัน r = D/4 (ACI 318 6.2.5.1 สำหรับหน้าตัดวงกลม แทน 0.3h ของ
    หน้าตัดสี่เหลี่ยม) และโมเมนต์ความเฉื่อย Ig = π·D⁴/64 (แทน b·h³/12)
  - **แรงเฉือน**: เหล็กปลอกเกลียวออกแบบตามข้อกำหนดระยะห่างมาตรฐานเท่านั้น ไม่ตรวจกำลังรับแรง
    เฉือนแยกต่างหาก (เหตุผลเดียวกับโมดูล 4.1 — ขอบเขตอาคารบ้านพักอาศัยตามกฎกระทรวง 2566)
  - **ระยะหุ้มคอนกรีต (cover)**: ค่าเริ่มต้น 4.0 ซม. เท่ากับโมดูล 4.1 (ผู้ใช้ปรับได้)
"""

import math
from dataclasses import dataclass

from common.design_params import PHI_B, PHI_C_SPIRAL, ES_KSC, compute_ec
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2
from modules.column_tied import _min_clear_spacing_cm

DEFAULT_COVER_CM = 4.0
ECU = 0.003
RHO_G_MIN = 0.01
RHO_G_MAX = 0.08
SLENDERNESS_LIMIT_KLU_R = 22.0
K_FACTOR = 1.0
PHI_PN_MAX_FACTOR_SPIRAL = 0.85    # ACI 318 22.4.2.1 (เสาปลอกเกลียว — เทียบกับ 0.80 เสาปลอกเดี่ยว)
CM_FACTOR = 1.0
BETA_DNS_DEFAULT = 0.6
PC_SAFETY_FACTOR = 0.75

MIN_BARS_SPIRAL = 6                # ACI 318 10.7.3.1 / 25.7.3 — ขั้นต่ำ 6 เส้นสำหรับเสาปลอกเกลียว
MAX_BARS_TRY = 24                   # ขีดจำกัดจำนวนเหล็กสูงสุดที่ลองในลูปออกแบบอัตโนมัติ

SPIRAL_CLEAR_SPACING_MAX_CM = 7.5   # ACI 318 25.7.3.3
SPIRAL_CLEAR_SPACING_MIN_CM = 2.5   # ACI 318 25.7.3.3

COLUMN_DIAMETER_CM_OPTIONS = [25, 30, 35, 40, 45, 50, 60, 70]
COLUMN_BAR_DIAMETERS_MM = [12, 16, 20, 22, 25, 28, 32]
SPIRAL_DIAMETERS_MM = [9, 10, 12]

N_C_STEPS = 70


@dataclass
class ColumnSpiralInput:
    fc_ksc: float
    main_steel_type: str
    spiral_steel_type: str
    diameter_cm: float
    Lu_m: float
    pu_kg: float
    mu_kgm: float
    main_bar_dia_mm: float
    spiral_bar_dia_mm: float
    spiral_pitch_use_cm: float = 7.5
    cover_cm: float = DEFAULT_COVER_CM
    beta_dns: float = BETA_DNS_DEFAULT


@dataclass
class BarPoint:
    angle_deg: float
    y_cm: float     # ระยะจากผิวล่างสุดของหน้าตัด (bottom fiber, y=0 ถึง y=D บนสุด)


@dataclass
class InteractionPoint:
    c_cm: float
    phi: float
    pn_kg: float
    mn_kgm: float
    phi_pn_kg: float
    phi_mn_kgm: float
    et: float


@dataclass
class SlendernessCheck:
    r_cm: float
    klu_r: float
    is_short: bool
    ec_ksc: float = 0.0
    ig_cm4: float = 0.0
    ei_tm2: float = 0.0
    pc_ton: float = 0.0
    cm_factor: float = 1.0
    delta_ns: float = 1.0
    pu_exceeds_075pc: bool = False
    mu_design_kgm: float = 0.0


@dataclass
class SpiralDesign:
    ach_cm2: float
    rho_s_min: float
    asp_cm2: float
    s_max_strength_cm: float
    s_max_code_cm: float
    s_min_code_cm: float
    s_max_cm: float
    s_use_cm: float
    spiral_ok: bool
    s_recommend_cm: float = 0.0    # ระยะห่างเกลียวที่โปรแกรมออกแบบให้อัตโนมัติ (ปัดลง 0.5 ซม.)
    feasible: bool = True          # ช่วงระยะห่างที่ยอมให้มีอยู่จริงไหม (s_max >= s_min_code)
    auto_adjusted: bool = False    # โปรแกรมปรับ s ให้อัตโนมัติเพราะค่าที่กรอกอยู่นอกช่วงไหม


@dataclass
class ColumnSpiralResult:
    ag_cm2: float
    as_min_cm2: float
    as_max_cm2: float
    n_bars: int
    as_provided_cm2: float
    rho_g: float
    bar_points: list             # list[BarPoint]
    po_kg: float
    phi_pn_max_kg: float
    interaction_points: list      # list[InteractionPoint] เรียงตาม phi_pn จากน้อยไปมาก
    phi_mn_capacity_at_pu_kgm: float
    utilization: float
    design_ok: bool
    design_fail_reason: str
    slenderness: SlendernessCheck
    spiral: SpiralDesign
    main_bar_type: str
    spiral_bar_type: str
    reinf_label: str
    reinf_label_spiral: str
    spiral_bar_dia_used_mm: float = 0.0     # ขนาดเหล็กปลอกเกลียวที่ใช้จริง (อาจถูกปรับขึ้นอัตโนมัติ)
    spiral_dia_auto_upsized: bool = False   # ปรับขนาดเหล็กปลอกขึ้นอัตโนมัติเพราะขนาดที่เลือกเล็กเกินไปไหม
    main_bar_dia_used_mm: float = 0.0       # ขนาดเหล็กยืนที่ใช้จริง (อาจถูกปรับขึ้นอัตโนมัติแบบหนังสือ)
    main_dia_auto_upsized: bool = False     # ปรับขนาดเหล็กยืนขึ้นอัตโนมัติเพื่อคงจำนวนเส้นน้อยสุด (6 เส้น)


def _max_bars_circular(r_bar_cm: float, main_dia_cm: float) -> int:
    """จำนวนเหล็กเสริมหลักสูงสุดที่กระจายรอบวงได้ (วงกลมรัศมี r_bar_cm ที่ศูนย์กลางเหล็ก) ตาม
    ระยะห่างสุทธิขั้นต่ำระหว่างเหล็ก (สูตรเดียวกับ modules.column_tied._min_clear_spacing_cm)."""
    if r_bar_cm <= 0:
        return 0
    circumference = 2.0 * math.pi * r_bar_cm
    pitch = main_dia_cm + _min_clear_spacing_cm(main_dia_cm)
    return max(0, int(math.floor(circumference / pitch)))


def _build_bar_points(diameter_cm: float, main_dia_cm: float, spiral_dia_cm: float,
                       n_bars: int, cover_cm: float) -> list:
    """สร้างตำแหน่งเหล็กเสริมหลัก n_bars เส้น กระจายสม่ำเสมอรอบวง เริ่มจากมุม 0° (แนวนอน) เว้น
    ระยะเชิงมุมเท่ากัน 360°/n_bars — ตรงกับธรรมเนียมของไฟล์อ้างอิง (ดู docstring ด้านบนของไฟล์)."""
    R = diameter_cm / 2.0
    r_bar = R - cover_cm - spiral_dia_cm - main_dia_cm / 2.0
    points = []
    for i in range(n_bars):
        angle = i * (2.0 * math.pi / n_bars)
        y = R + r_bar * math.sin(angle)
        points.append(BarPoint(angle_deg=math.degrees(angle), y_cm=y))
    return points


def _po_kg(fc_ksc: float, fy_ksc: float, ag_cm2: float, ast_cm2: float) -> float:
    return 0.85 * fc_ksc * (ag_cm2 - ast_cm2) + fy_ksc * ast_cm2


def _phi_from_et(et: float, fy_ksc: float) -> float:
    ey = fy_ksc / ES_KSC
    if et <= ey:
        return PHI_C_SPIRAL
    if et >= 0.005:
        return PHI_B
    return PHI_C_SPIRAL + (et - ey) / (0.005 - ey) * (PHI_B - PHI_C_SPIRAL)


def _circular_segment(R: float, a: float) -> tuple:
    """พื้นที่ + ตำแหน่งเซนทรอยด์ (สัมบูรณ์ วัดจากผิวล่างสุด y=0) ของส่วนตัดวงกลม (circular
    segment) ที่ถูกตัดด้วยคอร์ดในแนวราบ ห่างจากผิวรับแรงอัดสุด (y=2R) ลงมาเป็นระยะ a — ดูสูตร
    เต็มในหมายเหตุด้านบนของไฟล์ (ยืนยันด้วยเคส a=R ให้ครึ่งวงกลมพอดี, a=0/a=2R ให้ขอบเขตถูกต้อง)."""
    a = max(0.0, min(a, 2.0 * R))
    if a <= 1e-9:
        return 0.0, 2.0 * R
    if a >= 2.0 * R - 1e-9:
        return math.pi * R ** 2, R

    d_center_to_chord = R - a   # ระยะจากศูนย์กลางถึงคอร์ด (บวก=คอร์ดอยู่เหนือศูนย์กลาง)
    ratio = max(-1.0, min(1.0, d_center_to_chord / R))
    theta = 2.0 * math.acos(ratio)
    area = (R ** 2 / 2.0) * (theta - math.sin(theta))
    denom = theta - math.sin(theta)
    ybar_offset = (4.0 * R * math.sin(theta / 2.0) ** 3) / (3.0 * denom) if denom > 1e-9 else 0.0
    centroid_abs_y = R + ybar_offset
    return area, centroid_abs_y


def _build_interaction_diagram(diameter_cm: float, fc_ksc: float, fy_ksc: float, beta1: float,
                                bar_points: list, bar_area: float) -> tuple:
    """สร้าง P-M interaction diagram (ก่อน apply φ) ของหน้าตัดวงกลม ด้วยวิธี strain
    compatibility เหมือนโมดูล 4.1 (modules.column_tied._build_interaction_diagram) ทุกประการ
    ต่างแค่สูตรพื้นที่/เซนทรอยด์ compression block เป็นวงกลม (_circular_segment) แทนสี่เหลี่ยม
    ผืนผ้าธรรมดา — คืน (points, po, phi_pn_max)."""
    R = diameter_cm / 2.0
    ag = math.pi * R ** 2
    ast = len(bar_points) * bar_area
    po = _po_kg(fc_ksc, fy_ksc, ag, ast)
    phi_pn_max = PHI_PN_MAX_FACTOR_SPIRAL * PHI_C_SPIRAL * po

    sorted_points = sorted(bar_points, key=lambda p: p.y_cm)   # y น้อยสุด = ไกลผิวรับแรงอัดสุดที่สุด

    c_values = []
    for i in range(N_C_STEPS):
        frac = i / (N_C_STEPS - 1)
        if frac <= 0.6:
            c = 0.02 * diameter_cm + (frac / 0.6) * (1.5 * diameter_cm - 0.02 * diameter_cm)
        else:
            c = 1.5 * diameter_cm + ((frac - 0.6) / 0.4) * (6.0 * diameter_cm - 1.5 * diameter_cm)
        c_values.append(c)

    points = []
    for c in c_values:
        a = min(beta1 * c, diameter_cm)
        seg_area, seg_centroid_y = _circular_segment(R, a)
        cc_force = 0.85 * fc_ksc * seg_area

        pn = cc_force
        moment_sum = cc_force * (seg_centroid_y - R)
        et = None
        for bp in sorted_points:
            di = diameter_cm - bp.y_cm
            strain = ECU * (c - di) / c
            fs = max(-fy_ksc, min(ES_KSC * strain, fy_ksc))
            force = bar_area * fs
            if fs > 0 and di <= a:
                force -= bar_area * 0.85 * fc_ksc
            pn += force
            moment_sum += force * (bp.y_cm - R)
            if et is None:
                et = ECU * (di - c) / c   # net tensile strain ของเหล็กเส้นไกลผิวรับแรงอัดสุด (y น้อยสุด)

        mn = abs(moment_sum) / 100.0
        phi = _phi_from_et(et if et is not None else 0.0, fy_ksc)
        phi_pn = min(phi * pn, phi_pn_max)
        phi_mn = phi * mn

        points.append(InteractionPoint(
            c_cm=c, phi=phi, pn_kg=pn, mn_kgm=mn,
            phi_pn_kg=phi_pn, phi_mn_kgm=phi_mn, et=et if et is not None else 0.0,
        ))

    points.sort(key=lambda p: p.phi_pn_kg)
    return points, po, phi_pn_max


def _capacity_mn_at_pu(points: list, pu_kg: float) -> float:
    if not points:
        return 0.0
    if pu_kg <= points[0].phi_pn_kg:
        return points[0].phi_mn_kgm
    if pu_kg >= points[-1].phi_pn_kg:
        return points[-1].phi_mn_kgm
    for i in range(len(points) - 1):
        p0, p1 = points[i], points[i + 1]
        if p0.phi_pn_kg <= pu_kg <= p1.phi_pn_kg:
            if abs(p1.phi_pn_kg - p0.phi_pn_kg) < 1e-9:
                return min(p0.phi_mn_kgm, p1.phi_mn_kgm)
            t = (pu_kg - p0.phi_pn_kg) / (p1.phi_pn_kg - p0.phi_pn_kg)
            return p0.phi_mn_kgm + t * (p1.phi_mn_kgm - p0.phi_mn_kgm)
    return points[-1].phi_mn_kgm


def _slenderness_check(diameter_cm: float, Lu_m: float) -> SlendernessCheck:
    r_cm = diameter_cm / 4.0   # ACI 318 6.2.5.1 (หน้าตัดวงกลม r=D/4, แทน 0.3h ของหน้าตัดสี่เหลี่ยม)
    klu_r = (K_FACTOR * Lu_m * 100.0) / r_cm if r_cm > 0 else 0.0
    return SlendernessCheck(r_cm=r_cm, klu_r=klu_r, is_short=(klu_r <= SLENDERNESS_LIMIT_KLU_R))


def _moment_magnification(diameter_cm: float, Lu_m: float, fc_ksc: float, beta_dns: float,
                           pu_kg: float, mu_kgm: float) -> tuple:
    """เหมือน modules.column_tied._moment_magnification ทุกประการ ต่างแค่ Ig ของหน้าตัดวงกลม
    = π·D⁴/64 (แทน b·h³/12)."""
    ec_ksc = compute_ec(fc_ksc)
    ig_cm4 = math.pi * (diameter_cm ** 4) / 64.0
    ei_kgcm2 = 0.4 * ec_ksc * ig_cm4 / (1.0 + beta_dns)
    ei_tm2 = ei_kgcm2 * 1e-7

    klu_cm = K_FACTOR * Lu_m * 100.0
    pc_kg = (math.pi ** 2 * ei_kgcm2) / (klu_cm ** 2) if klu_cm > 0 else 0.0

    pu_exceeds_075pc = (pc_kg <= 0) or (pu_kg >= PC_SAFETY_FACTOR * pc_kg)
    if pu_exceeds_075pc:
        delta_ns = None
    else:
        delta_ns = CM_FACTOR / (1.0 - pu_kg / (PC_SAFETY_FACTOR * pc_kg))
        delta_ns = max(delta_ns, 1.0)

    return ec_ksc, ig_cm4, ei_tm2, pc_kg, delta_ns, pu_exceeds_075pc


def _spiral_design(fc_ksc: float, fyt_ksc: float, diameter_cm: float, cover_cm: float,
                    spiral_dia_cm: float, spiral_asp_cm2: float, spiral_pitch_use_cm: float) -> SpiralDesign:
    """ออกแบบระยะห่างเหล็กปลอกเกลียว (spiral pitch) ตามสูตร ACI 318 25.7.3 เต็มรูปแบบ — ดู
    หมายเหตุขอบเขตด้านบนของไฟล์ (ไฟล์อ้างอิงใช้ค่าคงที่ 7.5 ซม. ตายตัว ไม่ได้คำนวณจาก ρs จริง)."""
    R = diameter_cm / 2.0
    dc = diameter_cm - 2.0 * cover_cm   # เส้นผ่านศูนย์กลางแกนกลาง (ถึงขอบนอกของเหล็กปลอกเกลียว)
    ag = math.pi * R ** 2
    ach = math.pi * (dc / 2.0) ** 2 if dc > 0 else 0.0

    rho_s_min = 0.45 * (ag / ach - 1.0) * (fc_ksc / fyt_ksc) if ach > 0 else 999.0
    rho_s_min = max(rho_s_min, 0.0)

    s_max_strength = (4.0 * spiral_asp_cm2) / (dc * rho_s_min) if (dc > 0 and rho_s_min > 0) else 999.0
    s_max_code = spiral_dia_cm + SPIRAL_CLEAR_SPACING_MAX_CM
    s_min_code = spiral_dia_cm + SPIRAL_CLEAR_SPACING_MIN_CM
    s_max = min(s_max_strength, s_max_code)

    # มีช่วงระยะห่างที่ยอมให้อยู่จริงไหม (ถ้า s_max < s_min แปลว่าเหล็กปลอกเล็ก/เกรดต่ำเกินไป
    # สำหรับขนาดเสานี้ — ต้องเพิ่มขนาดเหล็กปลอกเกลียวหรือเปลี่ยนเกรด)
    feasible = s_max >= s_min_code - 1e-9

    # ออกแบบระยะห่างเกลียวอัตโนมัติ (แนวเดียวกับที่โมดูลนี้ auto-design จำนวนเหล็กหลัก):
    # เลือกระยะห่างที่ใหญ่ที่สุดเท่าที่ยังผ่านเกณฑ์ ρs (ปัดลงทีละ 0.5 ซม. เพื่อค่าที่ใช้งานจริง)
    if feasible:
        s_recommend = math.floor(s_max / 0.5) * 0.5          # ปัดลงทีละ 0.5 ซม. (ค่าที่ใช้งานจริง)
        if s_recommend < s_min_code:                          # ช่วงแคบ -> ลองปัดลงทีละ 0.1 ซม.
            s_recommend = math.floor(s_max * 10.0) / 10.0
        if s_recommend < s_min_code:                          # ช่วงแคบมาก -> ใช้ขั้นต่ำพอดี (<= s_max เพราะ feasible)
            s_recommend = s_min_code
    else:
        s_recommend = math.floor(s_max * 10.0) / 10.0

    # ใช้ค่าที่ผู้ใช้กรอกถ้าอยู่ในช่วงที่ยอมให้ มิฉะนั้นปรับเป็นค่าที่ออกแบบอัตโนมัติ (auto-design)
    if feasible and (s_min_code - 1e-9 <= spiral_pitch_use_cm <= s_max + 1e-9):
        s_use = spiral_pitch_use_cm
        auto_adjusted = False
    elif feasible:
        s_use = s_recommend
        auto_adjusted = True
    else:
        s_use = spiral_pitch_use_cm
        auto_adjusted = False

    spiral_ok = feasible and (s_min_code - 1e-9 <= s_use <= s_max + 1e-9)
    return SpiralDesign(
        ach_cm2=ach, rho_s_min=rho_s_min, asp_cm2=spiral_asp_cm2,
        s_max_strength_cm=s_max_strength, s_max_code_cm=s_max_code, s_min_code_cm=s_min_code,
        s_max_cm=s_max, s_use_cm=s_use, spiral_ok=spiral_ok,
        s_recommend_cm=s_recommend, feasible=feasible, auto_adjusted=auto_adjusted,
    )


def calculate(inp: ColumnSpiralInput) -> ColumnSpiralResult:
    from common.design_params import compute_beta1

    fy = GS_STEEL_FY_KSC[inp.main_steel_type]
    fyt = GS_STEEL_FY_KSC[inp.spiral_steel_type]
    beta1 = compute_beta1(inp.fc_ksc)

    R = inp.diameter_cm / 2.0
    ag = math.pi * R ** 2
    as_min = RHO_G_MIN * ag
    as_max = RHO_G_MAX * ag

    slenderness = _slenderness_check(inp.diameter_cm, inp.Lu_m)

    # ออกแบบเหล็กปลอกเกลียวอัตโนมัติ (ทั้งขนาดเส้น + ระยะห่าง): เริ่มจากขนาดที่ผู้ใช้เลือก
    # แล้วไล่ขึ้นถ้าขนาดนั้นเล็กเกินไปจนไม่มีช่วงระยะห่างที่ผ่านเกณฑ์ ρs,min (ACI 318 25.7.3)
    # — เหล็กปลอกเส้นเล็ก (เช่น 9 มม.) บนเสาบางขนาดทำ ρs,min ไม่ได้แม้เรียงถี่สุด ต้องใช้เส้นใหญ่ขึ้น
    spiral_candidates = [d for d in SPIRAL_DIAMETERS_MM if d >= inp.spiral_bar_dia_mm] or list(SPIRAL_DIAMETERS_MM)
    spiral = None
    spiral_bar_dia_used_mm = inp.spiral_bar_dia_mm
    for _sd_mm in spiral_candidates:
        _sp = _spiral_design(inp.fc_ksc, fyt, inp.diameter_cm, inp.cover_cm, _sd_mm / 10.0,
                             bar_area_cm2(_sd_mm), inp.spiral_pitch_use_cm)
        if _sp.feasible:
            spiral = _sp
            spiral_bar_dia_used_mm = _sd_mm
            break
    if spiral is None:
        # ไม่มีขนาดเหล็กปลอกใดผ่านเลย — ใช้ขนาดใหญ่สุดที่มีแล้วแจ้งเตือน (ต้องขยายเสา/ลดระยะหุ้ม/เพิ่มเกรด)
        spiral_bar_dia_used_mm = spiral_candidates[-1]
        spiral = _spiral_design(inp.fc_ksc, fyt, inp.diameter_cm, inp.cover_cm, spiral_bar_dia_used_mm / 10.0,
                                bar_area_cm2(spiral_bar_dia_used_mm), inp.spiral_pitch_use_cm)
    spiral_dia_auto_upsized = (spiral_bar_dia_used_mm != inp.spiral_bar_dia_mm)

    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    spiral_bar_type = GS_STEEL_BAR_TYPE[inp.spiral_steel_type]

    pu_unstable = False
    if slenderness.is_short:
        slenderness.delta_ns = 1.0
        slenderness.cm_factor = CM_FACTOR
        slenderness.mu_design_kgm = inp.mu_kgm
    else:
        ec_ksc, ig_cm4, ei_tm2, pc_kg, delta_ns, pu_exceeds = _moment_magnification(
            inp.diameter_cm, inp.Lu_m, inp.fc_ksc, inp.beta_dns, inp.pu_kg, inp.mu_kgm)
        slenderness.ec_ksc = ec_ksc
        slenderness.ig_cm4 = ig_cm4
        slenderness.ei_tm2 = ei_tm2
        slenderness.pc_ton = pc_kg / 1000.0
        slenderness.cm_factor = CM_FACTOR
        slenderness.pu_exceeds_075pc = pu_exceeds
        if pu_exceeds:
            pu_unstable = True
            slenderness.delta_ns = 0.0
            slenderness.mu_design_kgm = inp.mu_kgm
        else:
            slenderness.delta_ns = delta_ns
            slenderness.mu_design_kgm = inp.mu_kgm * delta_ns
    mu_design = slenderness.mu_design_kgm

    # ออกแบบเหล็กยืนแบบหนังสือ DRMK (ผู้ใช้เลือก 2026-07-12): ใช้จำนวนเส้น "น้อยที่สุด" ก่อน
    # (เริ่ม 6 เส้นตามข้อกำหนดเสาปลอกเกลียว) แล้วเลือกขนาดเหล็กยืนเล็กที่สุดที่ยังพอ (ไม่เล็กกว่าที่
    # ผู้ใช้เลือก) ให้ As ≥ 1%Ag (และ ≤ 8%) + กำลังพอ → ได้ผลทรงเดียวกับหนังสือ เช่น 6-DB16
    # (แทนที่จะคงเส้นเล็กแล้วเพิ่มจำนวนจนได้ 9-DB12 ที่ดูแน่นเกินจำเป็น)
    spiral_used_cm = spiral_bar_dia_used_mm / 10.0
    main_candidates_mm = [d for d in COLUMN_BAR_DIAMETERS_MM if d >= inp.main_bar_dia_mm] or list(COLUMN_BAR_DIAMETERS_MM)

    chosen = None
    for n_bars in range(MIN_BARS_SPIRAL, MAX_BARS_TRY + 1):
        for md_mm in main_candidates_mm:
            md_cm = md_mm / 10.0
            area = bar_area_cm2(md_mm)
            as_total = n_bars * area
            if as_total < as_min:
                continue                       # ยังไม่ถึง 1% -> ลองเส้นใหญ่ขึ้น
            if as_total > as_max:
                continue                       # เกิน 8% -> ข้าม (เส้นเล็ก/จำนวนน้อยกว่าดีกว่า)
            r_bar_md = R - inp.cover_cm - spiral_used_cm - md_cm / 2.0
            if n_bars > _max_bars_circular(r_bar_md, md_cm):
                continue                       # ใส่ไม่พอในวง
            bar_points = _build_bar_points(inp.diameter_cm, md_cm, spiral_used_cm, n_bars, inp.cover_cm)
            points, po, phi_pn_max = _build_interaction_diagram(
                inp.diameter_cm, inp.fc_ksc, fy, beta1, bar_points, area)
            if inp.pu_kg > phi_pn_max:
                continue
            phi_mn_cap = _capacity_mn_at_pu(points, inp.pu_kg)
            if phi_mn_cap >= mu_design:
                chosen = (n_bars, md_mm, area, bar_points, points, po, phi_pn_max, phi_mn_cap)
                break
        if chosen is not None:
            break

    if chosen is None:
        capacity_fail = True
        md_mm = main_candidates_mm[-1]
        md_cm = md_mm / 10.0
        area = bar_area_cm2(md_mm)
        r_bar_md = R - inp.cover_cm - spiral_used_cm - md_cm / 2.0
        n_bars = max(MIN_BARS_SPIRAL, min(MAX_BARS_TRY, _max_bars_circular(r_bar_md, md_cm)))
        while n_bars > MIN_BARS_SPIRAL and n_bars * area > as_max:
            n_bars -= 1
        main_bar_dia_used_mm = md_mm
        bar_points = _build_bar_points(inp.diameter_cm, md_cm, spiral_used_cm, n_bars, inp.cover_cm)
        points, po, phi_pn_max = _build_interaction_diagram(
            inp.diameter_cm, inp.fc_ksc, fy, beta1, bar_points, area)
        phi_mn_cap = _capacity_mn_at_pu(points, inp.pu_kg)
        as_provided = n_bars * area
    else:
        n_bars, main_bar_dia_used_mm, area, bar_points, points, po, phi_pn_max, phi_mn_cap = chosen
        as_provided = n_bars * area
        capacity_fail = False
    main_dia_auto_upsized = (main_bar_dia_used_mm != inp.main_bar_dia_mm)

    warnings = []
    if capacity_fail:
        warnings.append("⚠️ ไม่สามารถออกแบบเหล็กเสริมให้เพียงพอได้ภายในขนาดหน้าตัดนี้ (แม้ใช้ rho สูงสุด 8%) "
                         "กรุณาขยายขนาดเสาหรือเพิ่ม f'c")
    elif main_dia_auto_upsized:
        warnings.append(f"ℹ️ ปรับขนาดเหล็กยืนอัตโนมัติจาก DB{inp.main_bar_dia_mm:.0f} → DB{main_bar_dia_used_mm:.0f} "
                         f"(ออกแบบแบบหนังสือ: ใช้ {n_bars} เส้นให้ได้เหล็กขั้นต่ำ 1% แทนการเพิ่มจำนวนเส้นเล็กจำนวนมาก)")
    if pu_unstable:
        warnings.append("⚠️ เสาไม่เสถียร (Pu ≥ 0.75Pc ตาม ACI 318 6.6.4.5.2) — ไม่สามารถคำนวณตัวขยายโมเมนต์ได้ "
                         "กรุณาขยายขนาดหน้าตัดหรือลดความยาวช่วงเสาที่ไม่มีค้ำยัน (Lu)")
    elif not slenderness.is_short:
        warnings.append(f"⚠️ เสาชะลูด (kLu/r > 22) — โปรแกรมขยายโมเมนต์ให้อัตโนมัติแล้ว (δns={slenderness.delta_ns:.2f}, "
                         f"Mu,design={mu_design:,.0f} kg-m.) ตามวิธี ACI 318 6.6.4.5")
    if not spiral.feasible:
        warnings.append("⚠️ แม้ใช้เหล็กปลอกเกลียวเส้นใหญ่สุดที่มี ก็ยังทำ ρs,min (ACI 318 25.7.3) ไม่ได้สำหรับ "
                         f"เสาขนาดนี้ (s_max={spiral.s_max_cm:.2f} < s_min={spiral.s_min_code_cm:.2f} ซม.) "
                         "กรุณาขยายขนาดเสา ลดระยะหุ้มคอนกรีต หรือใช้เหล็กปลอกเกรดสูงขึ้น")
    else:
        if spiral_dia_auto_upsized:
            warnings.append(f"ℹ️ ปรับขนาดเหล็กปลอกเกลียวอัตโนมัติจาก {inp.spiral_bar_dia_mm:.0f} → {spiral_bar_dia_used_mm:.0f} มม. "
                             "(ขนาดที่เลือกเล็กเกินไป ทำ ρs,min ไม่ได้แม้เรียงถี่สุด)")
        if spiral.auto_adjusted:
            warnings.append(f"ℹ️ ปรับระยะห่างเหล็กปลอกเกลียวอัตโนมัติเป็น {spiral.s_use_cm:.1f} ซม. "
                             f"(ให้อยู่ในช่วง {spiral.s_min_code_cm:.2f}–{spiral.s_max_cm:.2f} ซม. ตาม ACI 318 25.7.3)")
    design_fail_reason = " ".join(warnings)
    design_ok = (not capacity_fail) and spiral.spiral_ok and (not pu_unstable)

    rho_g = as_provided / ag if ag > 0 else 0.0
    utilization = (mu_design / phi_mn_cap) if phi_mn_cap > 0 else (0.0 if mu_design <= 0 else 999.0)
    utilization = min(utilization, 999.0)   # กันค่ามหาศาลตอน phi_mn_cap ~ 0 (เคสกำลังไม่พอ/เสาไม่เสถียร)

    reinf_label = f"{n_bars}-{main_bar_type}{main_bar_dia_used_mm:.0f} (กระจายรอบวง)"
    reinf_label_spiral = f"{spiral_bar_type}{spiral_bar_dia_used_mm:.0f}@{spiral.s_use_cm:.1f}cm. Spiral"

    return ColumnSpiralResult(
        ag_cm2=ag, as_min_cm2=as_min, as_max_cm2=as_max,
        n_bars=n_bars, as_provided_cm2=as_provided,
        rho_g=rho_g, bar_points=bar_points, po_kg=po, phi_pn_max_kg=phi_pn_max,
        interaction_points=points, phi_mn_capacity_at_pu_kgm=phi_mn_cap, utilization=utilization,
        design_ok=design_ok,
        design_fail_reason=design_fail_reason,
        slenderness=slenderness, spiral=spiral,
        main_bar_type=main_bar_type, spiral_bar_type=spiral_bar_type,
        reinf_label=reinf_label, reinf_label_spiral=reinf_label_spiral,
        spiral_bar_dia_used_mm=spiral_bar_dia_used_mm,
        spiral_dia_auto_upsized=spiral_dia_auto_upsized,
        main_bar_dia_used_mm=main_bar_dia_used_mm,
        main_dia_auto_upsized=main_dia_auto_upsized,
    )
