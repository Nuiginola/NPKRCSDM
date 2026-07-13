"""
Module 4.1 — เสาสี่เหลี่ยม (Rectangular Tied Column)

ขอบเขต: เสาเหลี่ยมมีปลอกเดี่ยว (tied column, ไม่ใช่เสาปลอกเกลียว/spiral) รับแรงตามแนวแกน
(Pu) ร่วมกับโมเมนต์ดัดทิศทางเดียว (uniaxial bending, Mu รอบแกนขนานกับด้าน b) — ยังไม่รองรับ
โมเมนต์สองทิศทาง (biaxial bending) ในเวอร์ชันนี้ (ขอบเขตเดียวกับหลักการที่ใช้ตัดขอบเขตของ
โมดูลคาน/พื้นก่อนหน้า — เพิ่มทีหลังได้ถ้าจำเป็นจริง)

หลักการออกแบบ: สร้าง P-M Interaction Diagram ของหน้าตัดเสาจริงด้วยวิธี strain compatibility
(Whitney stress block, ecu=0.003 ที่ผิวคอนกรีตรับแรงอัดสุด) แล้วตรวจสอบจุดแรงที่ต้องการ
(Pu, Mu) ว่าอยู่ในขอบเขตกำลังที่ออกแบบได้ (φPn, φMn) หรือไม่ — เป็นวิธีมาตรฐานตาม ACI 318 /
กฎกระทรวง พ.ศ. 2566 ที่ใช้กันทั่วไปในซอฟต์แวร์ออกแบบเสา RC เชิงพาณิชย์/วิชาการ (รวมถึง DRMK
RC SDM ที่โปรแกรมนี้อ้างอิงสไตล์) — ไม่ได้ใช้วิธีประมาณอย่างง่าย (เช่น เส้นตรงเชื่อม 2 จุด)
เพราะจะให้ผลอนุรักษ์นิยม/ไม่แม่นยำเกินไปสำหรับงานวิจัย

รูปแบบเหล็กเสริม: จัดเหล็กรอบขอบหน้าตัด (perimeter tie pattern) แบบสมมาตร — nx เส้นต่อแถว
บน/ล่าง (ตามแนว b, รวมเหล็กมุมแล้ว) + ny_side เส้นต่อด้านข้าง (ตามแนว h, ระหว่างแถวบน/ล่าง
ไม่นับเหล็กมุมซ้ำ) เป็นรูปแบบเดียวกับที่ซอฟต์แวร์ออกแบบเสาทั่วไปใช้รับ input (เช่น "จำนวนเหล็ก
ตามแนวแกน X" / "แนวแกน Y") — โปรแกรมออกแบบอัตโนมัติ (auto-design) ไล่ลองรูปแบบเหล็กจากน้อย
ไปมาก (เรียงตามปริมาณเหล็กรวม) จนกว่าจุด (Pu, Mu) จะอยู่ในขอบเขตกำลังที่ปลอดภัย เหมือนกับที่
โมดูลคาน/พื้นทำกับ As ที่ต้องการ (ไม่ใช่ให้ผู้ใช้ลองผิดลองถูกเอง)

สมมติฐาน/ขอบเขตที่ตัดออกในเวอร์ชันนี้ (ตามแนวทางเดียวกับที่บันทึกไว้ในโมดูลคาน 3.1):
  - **Biaxial bending**: ยังไม่รองรับ — คำนวณเฉพาะโมเมนต์ทิศทางเดียวรอบแกนขนาน b เท่านั้น
  - **ผลกระทบความชะลูด (slenderness / moment magnification)**: ตรวจสอบด้วยอัตราส่วน kLu/r
    เทียบกับเกณฑ์ 22 (ขีดจำกัดอนุรักษ์นิยมสำหรับเสาไม่มีค้ำยันด้านข้าง/unbraced ตาม
    ACI 318 6.2.5) — ถ้าเกินเกณฑ์นี้ โปรแกรม**ขยายโมเมนต์ (moment magnification) ให้อัตโนมัติ**
    ตามวิธี ACI 318 6.6.4.5 (nonsway/unbraced frame): EI = 0.4·Ec·Ig/(1+βdns), Pc = π²EI/(kLu)²,
    δns = Cm/(1-Pu/0.75Pc) (ไม่น้อยกว่า 1.0) แล้วใช้ Mu,design = δns·Mu ตรวจกำลังแทนค่า Mu ดิบ —
    k=1.0 คงที่ (สมมติเสาปลายหมุนทั้งสองด้าน/pinned-pinned อนุรักษ์นิยม), Cm=1.0 คงที่ (สมมติ
    มีแรงกระทำตามขวางระหว่างจุดรองรับ/เสาไม่มีค้ำยันด้านข้าง ตาม ACI 318 6.6.4.5.3(a) ตรงกับ
    สมมติฐาน unbraced เดียวกับที่ใช้กำหนด k=1.0), βdns ใช้ค่าอนุรักษ์นิยมเริ่มต้น 0.6 (ผู้ใช้ปรับ
    ได้ผ่าน input `beta_dns` เพราะโมดูลนี้ยังไม่แยกน้ำหนักบรรทุกคงค้าง(DL)/ชั่วคราว(LL) ออกจากกัน
    เป็น input คนละช่อง) — ถ้า Pu ≥ 0.75·Pc (เสาไม่เสถียรตาม ACI 318 6.6.4.5.2) ถือเป็นผลออกแบบ
    ไม่ผ่านทันที (blocking) ต้องขยายขนาดหน้าตัดหรือลดความยาวช่วงเสาที่ไม่มีค้ำยัน
  - **แรงเฉือน**: เสาบ้านพักอาศัยทั่วไปไม่ค่อยมีแรงเฉือนด้านข้างจากแผ่นดินไหว/ลมที่ต้อง
    ออกแบบเหล็กปลอกรับแรงเฉือนโดยเฉพาะ (ขอบเขตงานวิจัยนี้ตามกฎกระทรวง 2566 อาคารบ้านพัก
    อาศัย) — เหล็กปลอก (tie) ในโมดูลนี้ออกแบบตามข้อกำหนดระยะห่างมาตรฐาน (confinement/
    buckling restraint) เท่านั้น ไม่ได้ตรวจสอบกำลังรับแรงเฉือนแยกต่างหาก
  - **ระยะหุ้มคอนกรีต (cover)**: เป็นช่องกรอกที่ผู้ใช้ปรับเองได้ (`cover_cm`, ค่าเริ่มต้น 4.0 ซม. —
    มาตรฐานทั่วไปสำหรับเสาโครงสร้างหลัก มากกว่าคานที่ใช้ 3.0 ซม. เพราะเสาเป็นชิ้นส่วนรับแรงอัด
    หลักที่มักสัมผัสสภาพแวดล้อมมากกว่า แต่ผู้ใช้ปรับได้ตามสภาพหน้างานจริง)

สูตรหลักที่ใช้ (มาตรฐาน ACI 318 / ตรงกับค่าคงที่ที่มีอยู่แล้วใน common/design_params.py):
  - Po = 0.85*f'c*(Ag-Ast) + fy*Ast (กำลังอัดตามแนวแกนบริสุทธิ์)
  - φPn,max = 0.80*φc*Po (ตามข้อกำหนด ACI 318 22.4.2.1 สำหรับเสาปลอกเดี่ยว — ป้องกัน
    การออกแบบที่ไม่มี eccentricity ขั้นต่ำเลย)
  - Strain compatibility: εi = ecu*(c-di)/c ที่แต่ละชั้นเหล็ก, fs=clamp(Es*ε,-fy,fy)
  - φ แปรผันตาม net tensile strain εt ของเหล็กชั้นที่ไกลผิวรับแรงอัดสุด (ACI 318 21.2.2
    unified provisions): εt<=εy -> φ=φc(=0.70, compression-controlled, ตามที่ตั้งไว้ใน
    common/design_params.py PHI_C สำหรับโมดูลนี้โดยเฉพาะ), εt>=0.005 -> φ=φb(=0.90,
    tension-controlled), ระหว่างกลาง interpolate เชิงเส้น
"""

import math
from dataclasses import dataclass, field

from common.design_params import PHI_B, PHI_C, ES_KSC, compute_ec
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2, CONCRETE_UNIT_WEIGHT_KG_M3

DEFAULT_COVER_CM = 4.0           # ค่าเริ่มต้นระยะหุ้มคอนกรีตถึงเหล็กปลอก (ผู้ใช้ปรับได้ผ่าน input cover_cm)
ECU = 0.003                    # strain คอนกรีตสูงสุดที่ผิวรับแรงอัด (Whitney)
RHO_G_MIN = 0.01                # อัตราส่วนเหล็กเสริมตามแนวแกนขั้นต่ำ (ACI 318 / มาตรฐานทั่วไป 1%)
RHO_G_MAX = 0.08                # อัตราส่วนเหล็กเสริมตามแนวแกนสูงสุด (8%)
SLENDERNESS_LIMIT_KLU_R = 22.0   # เกณฑ์อนุรักษ์นิยมสำหรับเสาไม่มีค้ำยันด้านข้าง (unbraced)
K_FACTOR = 1.0                   # ตัวคูณความยาวประสิทธิผล (ปลายหมุนทั้งสองด้าน, อนุรักษ์นิยม)
PHI_PN_MAX_FACTOR = 0.80         # ตัวคูณจำกัด φPn,max ตาม ACI 318 22.4.2.1 (เสาปลอกเดี่ยว)
CM_FACTOR = 1.0                  # ACI 318 6.6.4.5.3(a): Cm=1.0 สำหรับเสาไม่มีค้ำยันด้านข้าง/มีแรงกระทำ
                                   # ตามขวางระหว่างจุดรองรับ (ตรงกับสมมติฐาน unbraced เดียวกับ K_FACTOR)
BETA_DNS_DEFAULT = 0.6            # ค่าอนุรักษ์นิยมเริ่มต้นของ βdns เมื่อไม่มีการแยกน้ำหนักบรรทุกคงค้าง
                                   # (DL)/ชั่วคราว(LL) เป็น input แยกกัน — ผู้ใช้ปรับได้ผ่าน input beta_dns
PC_SAFETY_FACTOR = 0.75           # ACI 318 6.6.4.5.2: Pu ต้องไม่เกิน 0.75*Pc มิฉะนั้นเสาไม่เสถียร

COLUMN_SIZE_CM_OPTIONS = [20, 25, 30, 35, 40, 45, 50, 60]
COLUMN_BAR_DIAMETERS_MM = [12, 16, 20, 22, 25, 28, 32]
TIE_DIAMETERS_MM = [6, 9, 10, 12]

MAX_NX_TRY = 8       # ขีดจำกัดจำนวนเหล็กต่อแถว (บน/ล่าง) สูงสุดที่ลองในลูปออกแบบอัตโนมัติ
MAX_NY_SIDE_TRY = 6   # ขีดจำกัดจำนวนเหล็กข้างต่อด้าน สูงสุดที่ลอง
N_C_STEPS = 70        # จำนวนจุดที่สุ่มบน interaction diagram (ความละเอียดของเส้นโค้ง)


@dataclass
class ColumnTiedInput:
    fc_ksc: float
    main_steel_type: str
    tie_steel_type: str
    b_cm: float          # ด้านตั้งฉากกับทิศทางโมเมนต์ดัด (bending axis ขนานด้านนี้)
    h_cm: float           # ด้านขนานกับทิศทางโมเมนต์ดัด (ทิศที่เหล็กรับแรงดึง/อัดสลับกัน)
    Lu_m: float            # ความสูงช่วงเสาที่ไม่มีค้ำยันด้านข้าง (unsupported length)
    pu_kg: float
    mu_kgm: float
    main_bar_dia_mm: float
    tie_bar_dia_mm: float
    tie_spacing_use_cm: float = 15.0
    cover_cm: float = DEFAULT_COVER_CM     # ระยะหุ้มคอนกรีตถึงเหล็กปลอก (ผู้ใช้ปรับเองได้)
    beta_dns: float = BETA_DNS_DEFAULT      # สัดส่วนน้ำหนักบรรทุกคงค้างต่อน้ำหนักบรรทุกออกแบบรวม
                                              # (ใช้คำนวณ moment magnification เมื่อเสาชะลูด)


@dataclass
class BarLayer:
    y_cm: float     # ระยะจากผิวล่างสุดของหน้าตัด (bottom fiber)
    n_bars: int


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
    # ฟิลด์ด้านล่างนี้มีค่าเฉพาะเมื่อ is_short=False (เสาชะลูด, คำนวณ moment magnification) —
    # ถ้า is_short=True จะเป็นค่าว่าง/ดีฟอลต์ (ไม่จำเป็นต้องขยายโมเมนต์ตาม ACI 318 6.2.5)
    ec_ksc: float = 0.0
    ig_cm4: float = 0.0
    ei_tm2: float = 0.0
    pc_ton: float = 0.0
    cm_factor: float = 1.0
    delta_ns: float = 1.0
    pu_exceeds_075pc: bool = False   # True = เสาไม่เสถียรตาม ACI 318 6.6.4.5.2 (Pu >= 0.75*Pc)
    mu_design_kgm: float = 0.0        # โมเมนต์ที่ใช้ตรวจกำลังจริง (=Mu*delta_ns ถ้าเสาชะลูด, มิฉะนั้น =Mu)


@dataclass
class TieDesign:
    s_max_16db_cm: float
    s_max_48dt_cm: float
    s_max_dim_cm: float
    s_max_cm: float
    s_use_cm: float
    tie_ok: bool


@dataclass
class ColumnTiedResult:
    ag_cm2: float
    as_min_cm2: float
    as_max_cm2: float
    nx_bars: int
    ny_side_bars: int
    n_bars_total: int
    as_provided_cm2: float
    rho_g: float
    bar_layers: list             # list[BarLayer]
    po_kg: float
    phi_pn_max_kg: float
    interaction_points: list      # list[InteractionPoint] เรียงตาม c จากน้อยไปมาก
    phi_mn_capacity_at_pu_kgm: float
    utilization: float             # Mu / phi_Mn_capacity_at_pu (<=1.0 ผ่าน)
    design_ok: bool
    design_fail_reason: str
    slenderness: SlendernessCheck
    tie: TieDesign
    main_bar_type: str
    tie_bar_type: str
    reinf_label: str
    reinf_label_tie: str


def _min_clear_spacing_cm(main_dia_cm: float) -> float:
    """ระยะห่างสุทธิขั้นต่ำระหว่างเหล็กเสริมตามแนวแกน (ACI 318 25.2.3 แบบง่าย): ไม่น้อยกว่า
    1.5 เท่าของขนาดเหล็ก หรือ 4 ซม. เลือกค่าที่มากกว่า (ไม่ได้พิจารณาขนาดมวลรวมหยาบสูงสุด
    เพราะไม่ได้เก็บเป็น input ของโปรแกรมนี้)."""
    return max(4.0, 1.5 * main_dia_cm)


def _max_bars_per_face(face_length_cm: float, main_dia_cm: float, tie_dia_cm: float,
                        cover_cm: float) -> int:
    """จำนวนเหล็กสูงสุดที่ใส่ได้ตามแนวขอบด้านหนึ่ง (รวมเหล็กมุมทั้ง 2 เส้น) ตามระยะหุ้ม/
    ขนาดปลอก/ระยะห่างสุทธิขั้นต่ำ — ใช้หลักการเดียวกับ modules.beam_single_span._max_bars_single_layer."""
    edge = cover_cm + tie_dia_cm + main_dia_cm / 2.0
    avail = face_length_cm - 2.0 * edge
    if avail < 0:
        return 0
    pitch = main_dia_cm + _min_clear_spacing_cm(main_dia_cm)
    n = int(math.floor(avail / pitch)) + 1
    return max(0, n)


def _build_bar_layers(b_cm: float, h_cm: float, main_dia_cm: float, tie_dia_cm: float,
                       nx: int, ny_side: int, cover_cm: float) -> list:
    """สร้างรายการชั้นเหล็ก (y จากผิวล่าง, จำนวนเส้นที่ y นั้น) — แถวบน/ล่างมี nx เส้น (รวม
    เหล็กมุม), เหล็กข้างมี ny_side เส้นต่อด้าน (2 ด้าน รวมเป็น 2 เส้นต่อระดับ) กระจายสม่ำเสมอ
    ระหว่างแถวบน/ล่าง (ไม่นับซ้ำเหล็กมุม)."""
    edge = cover_cm + tie_dia_cm + main_dia_cm / 2.0
    y_bottom = edge
    y_top = h_cm - edge
    layers = [BarLayer(y_cm=y_bottom, n_bars=nx), BarLayer(y_cm=y_top, n_bars=nx)]
    if ny_side > 0 and y_top > y_bottom:
        step = (y_top - y_bottom) / (ny_side + 1)
        for i in range(1, ny_side + 1):
            layers.append(BarLayer(y_cm=y_bottom + i * step, n_bars=2))
    return layers


def _po_kg(fc_ksc: float, fy_ksc: float, ag_cm2: float, ast_cm2: float) -> float:
    return 0.85 * fc_ksc * (ag_cm2 - ast_cm2) + fy_ksc * ast_cm2


def _phi_from_et(et: float, fy_ksc: float) -> float:
    ey = fy_ksc / ES_KSC
    if et <= ey:
        return PHI_C
    if et >= 0.005:
        return PHI_B
    return PHI_C + (et - ey) / (0.005 - ey) * (PHI_B - PHI_C)


def _build_interaction_diagram(b_cm: float, h_cm: float, fc_ksc: float, fy_ksc: float,
                                beta1: float, bar_layers: list, bar_area: float) -> list:
    """สร้าง P-M interaction diagram (ก่อน apply φ) ด้วยวิธี strain compatibility — สุ่มค่า
    ระยะแกนสะเทิน c (neutral axis depth จากผิวรับแรงอัดสุด สมมติผิวบน y=h_cm) ตั้งแต่ใกล้ 0
    (โมเมนต์ล้วน) ถึงค่ามาก (แรงอัดล้วน ประมาณ) — คืน list ของ InteractionPoint เรียงจาก c
    น้อยไปมาก (Pn น้อยไปมากตามไปด้วยโดยทั่วไป)."""
    d_t = h_cm - bar_layers[0].y_cm   # ระยะจากผิวรับแรงอัดสุด (y=h_cm) ถึงเหล็กชั้นไกลสุด (bottom row)
    ag = b_cm * h_cm
    ast = sum(layer.n_bars for layer in bar_layers) * bar_area
    po = _po_kg(fc_ksc, fy_ksc, ag, ast)
    phi_pn_max = PHI_PN_MAX_FACTOR * PHI_C * po

    c_values = []
    for i in range(N_C_STEPS):
        frac = i / (N_C_STEPS - 1)
        # ช่วงต้น (frac<0.6) ให้ความละเอียดสูงใกล้ 0-1.5h (โค้งมีความเปลี่ยนแปลงเร็ว),
        # ช่วงหลังกระจายห่างขึ้นถึง 6h (เข้าใกล้ Po แบบ asymptote)
        if frac <= 0.6:
            c = 0.02 * h_cm + (frac / 0.6) * (1.5 * h_cm - 0.02 * h_cm)
        else:
            c = 1.5 * h_cm + ((frac - 0.6) / 0.4) * (6.0 * h_cm - 1.5 * h_cm)
        c_values.append(c)

    points = []
    for c in c_values:
        a = min(beta1 * c, h_cm)
        cc_force = 0.85 * fc_ksc * a * b_cm
        cc_y = h_cm - a / 2.0

        pn = cc_force
        moment_sum = cc_force * (cc_y - h_cm / 2.0)
        et = None
        for layer in bar_layers:
            di = h_cm - layer.y_cm   # ระยะจากผิวรับแรงอัดสุดถึงชั้นเหล็กนี้
            strain = ECU * (c - di) / c
            fs = max(-fy_ksc, min(ES_KSC * strain, fy_ksc))
            area = layer.n_bars * bar_area
            force = area * fs
            if fs > 0 and di <= a:   # เหล็กรับแรงอัดที่อยู่ในช่วง stress block ต้องหักพื้นที่คอนกรีตที่ถูกแทนที่
                force -= area * 0.85 * fc_ksc
            pn += force
            moment_sum += force * (layer.y_cm - h_cm / 2.0)
            if abs(layer.y_cm - bar_layers[0].y_cm) < 1e-9:
                et = ECU * (di - c) / c   # net tensile strain ของชั้นไกลผิวรับแรงอัดสุด (bottom row)

        mn = abs(moment_sum) / 100.0   # kg-cm -> kg-m
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
    """Interpolate φMn ที่ φPn = pu_kg จากเส้น interaction diagram (เรียง Pn น้อยไปมากแล้ว)
    — นอก range ให้ clamp ที่ปลาย (pu ต่ำกว่าจุดต่ำสุด/สูงกว่าจุดสูงสุดของเส้นที่สร้างไว้)."""
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


def _slenderness_check(h_cm: float, Lu_m: float) -> SlendernessCheck:
    r_cm = 0.30 * h_cm   # รัศมีไจเรชันโดยประมาณสำหรับหน้าตัดสี่เหลี่ยม (ACI 318 6.2.5.1)
    klu_r = (K_FACTOR * Lu_m * 100.0) / r_cm if r_cm > 0 else 0.0
    return SlendernessCheck(r_cm=r_cm, klu_r=klu_r, is_short=(klu_r <= SLENDERNESS_LIMIT_KLU_R))


def _moment_magnification(b_cm: float, h_cm: float, Lu_m: float, fc_ksc: float, beta_dns: float,
                           pu_kg: float, mu_kgm: float) -> tuple:
    """ขยายโมเมนต์ (moment magnification) ตาม ACI 318 6.6.4.5 (nonsway/unbraced frame แบบง่าย)
    เรียกเฉพาะกรณีเสาชะลูด (kLu/r > 22) — ใช้ Ig หน้าตัดเต็ม (ไม่ลดตามรอยร้าว เพื่อความง่าย,
    เทียบเท่าสมมติฐานอนุรักษ์นิยม) รอบแกนที่มีโมเมนต์ดัด (ตั้งฉากกับ h ดังนั้น Ig=b*h^3/12)
    คืนค่า (ec_ksc, ig_cm4, ei_tm2, pc_kg, delta_ns_or_None, pu_exceeds_075pc)."""
    ec_ksc = compute_ec(fc_ksc)
    ig_cm4 = b_cm * (h_cm ** 3) / 12.0
    ei_kgcm2 = 0.4 * ec_ksc * ig_cm4 / (1.0 + beta_dns)
    ei_tm2 = ei_kgcm2 * 1e-7   # kg*cm^2 -> t*m^2 (1 kg*cm^2 = 1e-3 t * 1e-4 m^2 = 1e-7 t*m^2)

    klu_cm = K_FACTOR * Lu_m * 100.0
    pc_kg = (math.pi ** 2 * ei_kgcm2) / (klu_cm ** 2) if klu_cm > 0 else 0.0

    pu_exceeds_075pc = (pc_kg <= 0) or (pu_kg >= PC_SAFETY_FACTOR * pc_kg)
    if pu_exceeds_075pc:
        delta_ns = None   # เสาไม่เสถียร — คำนวณตัวขยายโมเมนต์ไม่ได้ (ดู design_ok ใน calculate())
    else:
        delta_ns = CM_FACTOR / (1.0 - pu_kg / (PC_SAFETY_FACTOR * pc_kg))
        delta_ns = max(delta_ns, 1.0)   # ACI 318 6.6.4.5.1: ถ้าคำนวณได้ < 1.0 ให้ใช้ 1.0

    return ec_ksc, ig_cm4, ei_tm2, pc_kg, delta_ns, pu_exceeds_075pc


def _tie_design(main_dia_cm: float, tie_dia_cm: float, b_cm: float, h_cm: float,
                 tie_spacing_use_cm: float) -> TieDesign:
    """ระยะห่างเหล็กปลอก (tie) สูงสุดตามข้อกำหนดยึดรั้งเหล็กเสริมหลัก (ป้องกันการโก่งเดาะ
    ของเหล็กหลัก, ไม่ใช่การออกแบบรับแรงเฉือน — ดูหมายเหตุขอบเขตด้านบนของไฟล์) มาตรฐาน
    ACI 318 25.7.2.1: s_max = min(16*db เหล็กหลัก, 48*db เหล็กปลอก, ด้านที่สั้นที่สุดของเสา)."""
    s_16db = 16.0 * main_dia_cm
    s_48dt = 48.0 * tie_dia_cm
    s_dim = min(b_cm, h_cm)
    s_max = min(s_16db, s_48dt, s_dim)
    return TieDesign(
        s_max_16db_cm=s_16db, s_max_48dt_cm=s_48dt, s_max_dim_cm=s_dim, s_max_cm=s_max,
        s_use_cm=tie_spacing_use_cm, tie_ok=(tie_spacing_use_cm <= s_max),
    )


def calculate(inp: ColumnTiedInput) -> ColumnTiedResult:
    from common.design_params import compute_beta1

    fy = GS_STEEL_FY_KSC[inp.main_steel_type]
    fy_tie = GS_STEEL_FY_KSC[inp.tie_steel_type]
    beta1 = compute_beta1(inp.fc_ksc)
    main_dia_cm = inp.main_bar_dia_mm / 10.0
    tie_dia_cm = inp.tie_bar_dia_mm / 10.0
    bar_area = bar_area_cm2(inp.main_bar_dia_mm)

    ag = inp.b_cm * inp.h_cm
    as_min = RHO_G_MIN * ag
    as_max = RHO_G_MAX * ag

    max_nx = min(MAX_NX_TRY, _max_bars_per_face(inp.b_cm, main_dia_cm, tie_dia_cm, inp.cover_cm))
    max_ny_total = _max_bars_per_face(inp.h_cm, main_dia_cm, tie_dia_cm, inp.cover_cm)
    max_ny_side = min(MAX_NY_SIDE_TRY, max(0, max_ny_total - 2))

    candidates = []
    for nx in range(2, max_nx + 1):
        for ny_side in range(0, max_ny_side + 1):
            n_total = 2 * nx + 2 * ny_side
            as_total = n_total * bar_area
            if as_total < as_min:
                continue
            candidates.append((as_total, nx, ny_side, n_total))
    candidates.sort(key=lambda t: t[0])

    slenderness = _slenderness_check(inp.h_cm, inp.Lu_m)
    tie = _tie_design(main_dia_cm, tie_dia_cm, inp.b_cm, inp.h_cm, inp.tie_spacing_use_cm)
    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    tie_bar_type = GS_STEEL_BAR_TYPE[inp.tie_steel_type]

    # ขยายโมเมนต์ (moment magnification) ถ้าเสาชะลูด — ดูหมายเหตุขอบเขตด้านบนของไฟล์
    pu_unstable = False
    if slenderness.is_short:
        slenderness.delta_ns = 1.0
        slenderness.cm_factor = CM_FACTOR
        slenderness.mu_design_kgm = inp.mu_kgm
    else:
        ec_ksc, ig_cm4, ei_tm2, pc_kg, delta_ns, pu_exceeds = _moment_magnification(
            inp.b_cm, inp.h_cm, inp.Lu_m, inp.fc_ksc, inp.beta_dns, inp.pu_kg, inp.mu_kgm)
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

    chosen = None
    for as_total, nx, ny_side, n_total in candidates:
        if as_total > as_max:
            break
        layers = _build_bar_layers(inp.b_cm, inp.h_cm, main_dia_cm, tie_dia_cm, nx, ny_side, inp.cover_cm)
        points, po, phi_pn_max = _build_interaction_diagram(
            inp.b_cm, inp.h_cm, inp.fc_ksc, fy, beta1, layers, bar_area)
        if inp.pu_kg > phi_pn_max:
            continue   # เกินกำลังอัดสูงสุดที่ยอมให้ — เพิ่มเหล็กก็ไม่ช่วย (ต้องขยายหน้าตัด) ข้ามไปลองชุดถัดไปเผื่อ Po เปลี่ยน
        phi_mn_cap = _capacity_mn_at_pu(points, inp.pu_kg)
        if phi_mn_cap >= mu_design:
            chosen = (as_total, nx, ny_side, n_total, layers, points, po, phi_pn_max, phi_mn_cap)
            break

    if chosen is None:
        # ไม่พบชุดเหล็กที่พอ (แม้ rho สูงสุด 8%) — ใช้ชุดที่มากสุดที่ลองได้ (หรือชุดขั้นต่ำถ้าไม่มี
        # candidate เลย) มาแสดงผลไว้อ้างอิง พร้อมข้อความ NG ชัดเจน ไม่ให้เข้าใจผิดว่าออกแบบผ่าน
        capacity_fail = True
        if candidates:
            as_total, nx, ny_side, n_total = candidates[-1]
        else:
            nx, ny_side, n_total, as_total = 2, 0, 4, 4 * bar_area
        layers = _build_bar_layers(inp.b_cm, inp.h_cm, main_dia_cm, tie_dia_cm, nx, ny_side, inp.cover_cm)
        points, po, phi_pn_max = _build_interaction_diagram(
            inp.b_cm, inp.h_cm, inp.fc_ksc, fy, beta1, layers, bar_area)
        phi_mn_cap = _capacity_mn_at_pu(points, inp.pu_kg)
        as_provided = sum(l.n_bars for l in layers) * bar_area
    else:
        as_total, nx, ny_side, n_total, layers, points, po, phi_pn_max, phi_mn_cap = chosen
        as_provided = sum(l.n_bars for l in layers) * bar_area
        capacity_fail = False

    warnings = []
    if capacity_fail:
        warnings.append("⚠️ ไม่สามารถออกแบบเหล็กเสริมให้เพียงพอได้ภายในขนาดหน้าตัดนี้ (แม้ใช้ rho สูงสุด 8%) "
                         "กรุณาขยายขนาดเสาหรือเพิ่ม f'c")
    if pu_unstable:
        warnings.append("⚠️ เสาไม่เสถียร (Pu ≥ 0.75Pc ตาม ACI 318 6.6.4.5.2) — ไม่สามารถคำนวณตัวขยายโมเมนต์ได้ "
                         "กรุณาขยายขนาดหน้าตัดหรือลดความยาวช่วงเสาที่ไม่มีค้ำยัน (Lu)")
    elif not slenderness.is_short:
        warnings.append(f"⚠️ เสาชะลูด (kLu/r > 22) — โปรแกรมขยายโมเมนต์ให้อัตโนมัติแล้ว (δns={slenderness.delta_ns:.2f}, "
                         f"Mu,design={mu_design:,.0f} kg-m.) ตามวิธี ACI 318 6.6.4.5")
    if not tie.tie_ok:
        warnings.append("⚠️ ระยะห่างเหล็กปลอกที่ใช้จริงเกินค่าสูงสุดตามมาตรฐาน")
    design_fail_reason = " ".join(warnings)
    # หมายเหตุ: กรณีเสาชะลูดแต่เสถียร (คำนวณ moment magnification ได้ปกติ) เป็นแค่ข้อความแจ้งให้ทราบ
    # ไม่ทำให้ design_ok=False เพราะได้ขยายโมเมนต์เข้าไปในการตรวจกำลังจริงแล้ว (mu_design) — ที่ทำให้
    # design_ok=False คือกรณีเสาไม่เสถียรจริง (pu_unstable, Pu>=0.75Pc) ซึ่งเป็นข้อกำหนดบังคับตาม ACI 318
    design_ok = (not capacity_fail) and tie.tie_ok and (not pu_unstable)

    rho_g = as_provided / ag if ag > 0 else 0.0
    utilization = (mu_design / phi_mn_cap) if phi_mn_cap > 0 else (0.0 if mu_design <= 0 else 999.0)

    reinf_label = f"{n_total}-{main_bar_type}{inp.main_bar_dia_mm:.0f} (แถวละ {nx}, ข้างละ {ny_side})"
    reinf_label_tie = f"{tie_bar_type}{inp.tie_bar_dia_mm:.0f}@{inp.tie_spacing_use_cm:.0f}cm."

    return ColumnTiedResult(
        ag_cm2=ag, as_min_cm2=as_min, as_max_cm2=as_max,
        nx_bars=nx, ny_side_bars=ny_side, n_bars_total=n_total, as_provided_cm2=as_provided,
        rho_g=rho_g, bar_layers=layers, po_kg=po, phi_pn_max_kg=phi_pn_max,
        interaction_points=points, phi_mn_capacity_at_pu_kgm=phi_mn_cap, utilization=utilization,
        design_ok=design_ok,
        design_fail_reason=design_fail_reason,
        slenderness=slenderness, tie=tie,
        main_bar_type=main_bar_type, tie_bar_type=tie_bar_type,
        reinf_label=reinf_label, reinf_label_tie=reinf_label_tie,
    )
