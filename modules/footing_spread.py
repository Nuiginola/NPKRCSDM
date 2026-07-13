"""
Module 5.1 — ฐานรากแผ่เดี่ยว (Isolated Spread Footing)

ขอบเขต: ฐานรากแผ่รูปสี่เหลี่ยมจัตุรัส (square footing, B×B) รองรับเสาต้นเดียวรับแรงตาม
แนวแกน (concentric axial load) เท่านั้น — ยังไม่รองรับโมเมนต์ที่ถ่ายลงฐานราก (เช่น
เสาขอบอาคาร/เสามุมที่มักมี Mu ร่วมด้วย) และยังไม่รองรับฐานรากรูปสี่เหลี่ยมผืนผ้า (ขอบเขต
เดียวกับแนวทางที่ตัดขอบเขตไว้ในโมดูลเสา/คานก่อนหน้า — เพิ่มทีหลังได้ถ้าจำเป็นจริง)

ที่มา/ยืนยันสูตร: ไฟล์อ้างอิง "SDM Plus_Footing_Bearing Pu.xlsx" (โฟลเดอร์ SDM+beta) —
ตรวจสอบทุกสูตรหลัก (rho_min, โมเมนต์/Ru/rreq, แรงเฉือนทางเดียว, แรงเฉือนทะลุ, ความยาว
ฝังเหล็กทาบ/dowel) ทีละสูตรตรงกับ cell formula จริงในไฟล์ (ไม่ใช่แค่ดูตัวอย่างตัวเลข) —
ตัวอย่างตัวเลขที่ยืนยัน: a1=b1=20cm, fc'=150, fy=3000, A=B=1.4m, T=30cm, cover=7.5cm,
PD=10000kg, PL=5000kg -> Wu=27164.8kg, Pnet=13,859.6 kg/sq.m., d1=21.7cm, d2=20.9cm,
As#1=14.28 cm² (8-DB16), As#2=13.75 cm² (7-DB16, ใช้จริง 8), Vu(beam)=7,431.5kg,
fvVc(beam)=16,762.1kg, Vu(punching)=24,754.8kg, fvVc(punching)=39,941.7kg — ตัวเลขทั้งหมด
คำนวณซ้ำได้ตรงกับไฟล์ต้นฉบับ 100% (ดู test คู่กับไฟล์นี้)

หลักการออกแบบอัตโนมัติ (auto-design, ตามธรรมเนียมเดียวกับทุกโมดูลก่อนหน้า — ไม่ให้ผู้ใช้
ลองผิดลองถูกเอง — ต่างจากไฟล์อ้างอิงตรงที่ไฟล์ต้นฉบับให้ผู้ใช้กรอกความหนา T เองแล้วโปรแกรม
แค่ตรวจสอบ OK/NOT แต่โมดูลนี้ไล่ลองความหนาให้อัตโนมัติจนผ่านแทน ตามปรัชญาการออกแบบอัตโนมัติ
ที่ยึดมาตลอดทั้งโปรเจกต์):
  1. หาขนาดฐานราก B ที่ต้องการจากแรงบริการ (Pd+Pl, unfactored) หารด้วยหน่วยแรงแบกทานดิน
     สุทธิที่ยอมให้ (qa_net_kg_m2) แล้วปัดขึ้นเป็นขนาดกลม (ทวีคูณ 10 ซม.)
  2. ไล่ลองความหนา t จากน้อยไปมาก (FOOTING_THICKNESS_CM_OPTIONS — ตรงกับตารางความหนา
     มาตรฐาน 15-120 ซม. ทวีคูณ 5 ซม. ในไฟล์อ้างอิง cell OO9:OO30) จนกว่าจะผ่านทั้งแรงเฉือน
     ทางเดียว (one-way/beam shear) ทั้ง 2 ทิศทาง และแรงเฉือนทะลุ (two-way/punching shear)
  3. ออกแบบเหล็กเสริมทั้ง 2 ทิศทาง (เท่ากันโดยสมมาตรถ้าเสาเป็นสี่เหลี่ยมจัตุรัส ต่างกันเล็กน้อย
     ถ้าเสาเป็นสี่เหลี่ยมผืนผ้า) ด้วยวิธี moment ที่หน้าตัดวิกฤต=ผิวเสา (cantilever action) แล้ว
     ปัดจำนวนเหล็กขึ้น (ROUNDUP) ให้ As ที่ให้จริงพอดีตรงตามที่ต้องการ — เป็น "จำนวนเหล็ก
     กระจายสม่ำเสมอตลอดความกว้าง B" (เช่น "8-DB16") ตรงกับรูปแบบผลลัพธ์ของไฟล์อ้างอิง ไม่ใช่
     ระยะห่าง (spacing) แบบที่โมดูลพื้นทางเดียว/สองทางใช้ (ยืนยันจากไฟล์ว่าโมดูลฐานรากใช้
     รูปแบบ "จำนวนเหล็ก" แบบเดียวกับโมดูลเสา ไม่ใช่ระยะห่างแบบโมดูลพื้น)
  4. ตรวจสอบความยาวฝังเหล็กทาบ/เหล็กหนวดกุ้ง (dowel bar, จากเสาลงมาที่ฐานราก) ตามไฟล์
     อ้างอิง (ดูหัวข้อด้านล่าง)

สมมติฐาน/ขอบเขตที่ตัดออกในเวอร์ชันนี้:
  - **โมเมนต์ที่ฐานราก**: ไม่รองรับ — ออกแบบเฉพาะแรงตามแนวแกน (Pd, Pl) เท่านั้น
  - **รูปร่างฐานราก**: สี่เหลี่ยมจัตุรัสเท่านั้น (B×B) — ยังไม่รองรับฐานรากสี่เหลี่ยมผืนผ้า
  - **ตำแหน่งเสา (สำหรับแรงเฉือนทะลุ)**: สมมติเป็น "เสาใน" (interior column) เสมอ —
    ใช้เส้นรอบรูปวิกฤต 4 ด้านเต็ม (bo = 2(b+d)+2(h+d)) ตรงกับไฟล์อ้างอิง — ฐานรากเสาขอบ/
    เสามุมอาคาร (ซึ่งมีเส้นรอบรูปวิกฤตไม่ครบ 4 ด้าน และมักมีโมเมนต์ร่วมด้วย) ยังไม่รองรับใน
    เวอร์ชันนี้ (ไฟล์อ้างอิงเองก็เป็นแบบเสาในเช่นกัน ไม่มีตัวแปร αs/ตำแหน่งเสาให้เลือก)
  - **น้ำหนักฐานราก/ดินถมด้านบน**: ไม่รวมเป็นน้ำหนักที่ทำให้เกิดแรงเฉือน/โมเมนต์ภายในฐานราก
    (สมมติมาตรฐานทั่วไป: น้ำหนักส่วนนี้กระจายลงดินด้านล่างโดยตรง ไม่ผ่านหน้าตัดฐานราก จึง
    ไม่ก่อโมเมนต์/เฉือนภายใน) — ใช้เฉพาะหาขนาด B จากแรงบริการรวม Pd+Pl เทียบกับ qa_net
    ที่ผู้ใช้กรอก (สมมติว่า qa_net เป็นค่า "สุทธิ" ที่หักน้ำหนักส่วนนี้ออกแล้วจากผลทดสอบดิน) —
    ตรงกับไฟล์อ้างอิงที่แยก Ws (น้ำหนักดิน)/Wf (น้ำหนักฐานราก) ออกจากกันชัดเจน ใช้แค่ตอนหา
    ขนาด A0/ขนาดฐานราก ไม่ได้ใช้ตอนคำนวณ Pnet/Vu/Mu (ซึ่งใช้ Wu จาก PD/PL ของเสาเท่านั้น)
  - **การขยาย B ร่วมกับ t**: โปรแกรมหา B ครั้งเดียวจากแรงบริการ/qa_net ก่อน แล้วค่อยไล่ลอง
    เฉพาะ t ให้ผ่านแรงเฉือน — ยังไม่ทำ joint search ขยาย B ถ้า t สูงสุดที่ลองแล้วยังไม่พอ
    (กรณีนี้จะแจ้งเตือน NG ให้ผู้ใช้พิจารณาขยาย B/qa_net เอง)
  - **การตรวจสอบแรงแบกทานที่จุดต่อเสา-ฐานราก โดยตรง (bearing stress, ACI 318 22.8)**:
    ยังไม่ตรวจสอบแยกต่างหาก (ไฟล์อ้างอิงเองก็ไม่มีการตรวจสอบข้อนี้เช่นกัน — มีแค่ตรวจสอบ
    ความยาวฝังเหล็กทาบ/dowel ซึ่งเป็นคนละเรื่องกัน ดูหัวข้อด้านล่าง)
  - **ระยะหุ้มคอนกรีต (cover)**: ค่าเริ่มต้น 7.5 ซม. ตรงกับไฟล์อ้างอิง (H38=7.5) และตาม
    ACI 318 20.6.1.3.1 (คอนกรีตหล่อติดดินและสัมผัสดินถาวร ต้องการระยะหุ้มมากกว่าปกติ
    ต่างจากเสา 4.0 ซม. เพราะเสาไม่ได้หล่อติดดิน) — ผู้ใช้ปรับได้ตามสภาพหน้างานจริง
  - **เหล็กฝัง/เหล็กทาบ (dowel)**: สมมติใช้ขนาดเหล็กเดียวกับเหล็กเสริมหลักของฐานราก
    (main_bar_dia_mm/main_steel_type) ตรงกับไฟล์อ้างอิงที่ใช้ตัวแปร "Rebars" (W19) ตัวเดียว
    ทั้งฐานรากและ dowel ไม่ได้แยก input ขนาดเหล็กเสาต่างหาก — เป็นค่าประมาณที่สมเหตุสมผล
    เพราะเหล็กฝัง/ทาบจริงมักใช้ขนาดใกล้เคียงกับเหล็กหลักของฐานราก

สูตรหลักที่ใช้ (ยืนยันตรงกับไฟล์อ้างอิงทุกจุด เว้นแต่ระบุเป็นอย่างอื่น):
  - ขนาด B ต้องการ: B_req = sqrt((Pd+Pl)/qa_net)
  - หน่วยแรงแบกทานออกแบบ (factored, "Pnet" ในไฟล์ — ใช้คำนวณเฉือน/โมเมนต์):
    qu = Wu/B² = (1.4Pd+1.7Pl)/B²
  - ระยะประสิทธิผล 2 ชั้น (เหล็กชั้นแรกใกล้ผิวรับแรงดึงสุด d1=T-cover-db/2, ชั้นสองวางทับ
    ชั้นแรก d2=d1-db) — ตรงกับไฟล์ (NT27, NT45)
  - โมเมนต์ออกแบบ (คิดต่อแถบกว้าง 1 ม. คณิตศาสตร์เทียบเท่ากับที่ไฟล์คิดเป็นโมเมนต์รวมทั้ง
    แถบกว้าง B แล้วหาร B ออกใน Ru ภายหลัง — ยืนยันด้วยพีชคณิตว่าให้ผลเดียวกันทุกกรณี):
    Mu = qu*Lcant²/2 ที่หน้าตัดวิกฤต=ผิวเสา, Ru=Mu/(φb·100·d²),
    rreq=0.85(f'c/fy)(1-sqrt(1-2Ru/(0.85f'c)))
  - **เหล็กเสริมขั้นต่ำ: rho_min = 14/fy** (ไม่ใช่อัตราส่วนเหล็กกันร้าวจากอุณหภูมิที่เคยใช้ใน
    ร่างแรก — ไฟล์อ้างอิง cell NT21 ระบุชัดเจนว่า rmin=14/fy ตรงกับสูตรมาตรฐานของคาน/พื้น
    ทางเดียวในโปรเจกต์นี้เอง common.design_params.compute_rho_min ใช้สูตรเดียวกันอยู่แล้ว)
  - **เหล็กเสริมที่ต้องการ (จำนวนเหล็ก ไม่ใช่ระยะห่าง)**: As_req = max(rreq,rho_min)*B*d
    (ทั้งแถบกว้าง B ไม่ใช่ต่อเมตร), n_bars = ROUNDUP(As_req/Ab,0), As_provided = n_bars*Ab
    — กระจายสม่ำเสมอตลอดความกว้าง B (ตรงกับไฟล์ cell NT43/NT48, "Minimum/Using Rebars")
  - แรงเฉือนทางเดียว (one-way/beam shear ที่ระยะ d จากผิวเสา): Vc = 0.53*sqrt(f'c)*B*d
    (ตรงกับไฟล์ cell NT31 เป๊ะ — สูตรเดียวกับโมดูลคาน/พื้นทุกโมดูลในโปรเจกต์นี้ด้วย) —
    ตรวจทั้ง 2 ทิศทางแยกกัน (ใช้ d ของทิศทางนั้นๆ) เพราะโมดูลนี้รองรับเสารูปสี่เหลี่ยมผืนผ้า
    (ไฟล์อ้างอิงตรวจแค่ทิศทางเดียวเพราะตัวอย่างในไฟล์เป็นเสาสี่เหลี่ยมจัตุรัส a1=b1)
  - **แรงเฉือนทะลุ (two-way/punching shear)**: bo = 2(b+d)+2(h+d), βc = ด้านยาว/ด้านสั้น
    ของเสา, Vu = Wu - qu·(b+d)(h+d) — ทั้งหมดตรงกับไฟล์ (NT34/NT35/NT36) — Vc ใช้ 2 สูตร
    (ไม่ใช่ 3 แบบ ACI 318 เต็มรูปแบบ — ไฟล์อ้างอิงใช้แค่ 2 สมการนี้เท่านั้น):
      Vc1 = 0.27*(2+4/βc)*sqrt(f'c)*bo*d   (ตรงกับไฟล์ NT38 เป๊ะ, ค่าคงที่ 0.27 ไม่ใช่ 0.265
        ที่เคยประมาณเองในร่างแรกก่อนเจอไฟล์นี้)
      Vc2 = 1.06*sqrt(f'c)*bo*d              (ตรงกับไฟล์ NT39 เป๊ะ, ค่าเพดานทั่วไป)
      Vc,punching = min(Vc1,Vc2)
    ใช้ d เฉลี่ย (davg=(d1+d2)/2) แทนที่จะใช้ d1 อย่างเดียวแบบไฟล์ (ไฟล์ใช้ d1/NT27 ตัวเดียว
    ทั้งเส้นรอบรูปและ Vc เพราะไม่ได้แยก d ตามทิศทาง) — เลือกใช้ davg เพราะเป็นธรรมเนียมมาตรฐาน
    ตำราทั่วไปสำหรับแรงเฉือนทะลุ (bending 2 ทิศทางพร้อมกัน) และอนุรักษ์นิยมกว่าเล็กน้อย
    (davg < d1 เสมอ ทำให้ Vc คำนวณได้น้อยกว่าเล็กน้อย ปลอดภัยกว่า)
  - **ความยาวฝังเหล็กทาบ/dowel (ใหม่ — เพิ่มจากไฟล์อ้างอิง ไม่มีในร่างแรกของโมดูลนี้)**:
    Lbd (ความยาวฝังที่ต้องการขั้นต่ำ) = max(0.06*Ab*fy/sqrt(f'c), 30cm) — ตรงกับไฟล์ NT49
    (Ab = พื้นที่หน้าตัดเหล็กเสริมหลัก 1 เส้น, พื้นต่ำสุด 30 ซม. ตามไฟล์)
    Ld (ความยาวฝังที่มีพื้นที่ให้จริง) = B - cover - (max(b_col,h_col)/2) — ตรงกับไฟล์ NT50
    (ประมาณความยาวแนวราบที่มีให้เหล็กฝัง/ทาบจากผิวเสาถึงใกล้ขอบฐานราก) — ผ่านถ้า Ld>=Lbd
"""

import math
from dataclasses import dataclass

from common.design_params import PHI_B, PHI_V, compute_beta1, compute_rho_b, compute_rho_max, compute_rho_min
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2

DEFAULT_FOOTING_COVER_CM = 7.5     # ACI 318 20.6.1.3.1 / ไฟล์อ้างอิง H38: คอนกรีตหล่อติดดิน/สัมผัสดินถาวร
FOUNDING_DEPTH_DEFAULT_M = 1.50    # ระยะฝังฐานราก (พื้นดิน->ใต้ฐานราก) ค่าเริ่มต้นตามข้อกำหนด — ใช้กับรูปตัดเท่านั้น
FOOTING_SIZE_STEP_CM = 10.0         # ปัดขนาด B ขึ้นเป็นทวีคูณของค่านี้ (ความสะดวกก่อสร้าง)
FOOTING_SIZE_MIN_CM = 80.0
FOOTING_SIZE_MAX_CM = 500.0
FOOTING_EDGE_MARGIN_MIN_CM = 20.0   # ระยะขอบฐานรากถึงผิวเสาต่ำสุด (กันกรณี B คำนวณได้เล็กกว่าเสา)

# ตารางความหนามาตรฐาน — ตรงกับไฟล์อ้างอิง cell OO9:OO30 (15-120 ซม. ทวีคูณ 5 ซม.)
FOOTING_THICKNESS_CM_OPTIONS = [15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80, 85, 90, 95, 100, 105, 110, 115, 120]
FOOTING_BAR_DIAMETERS_MM = [10, 12, 16, 19, 20, 22, 25, 28]

PUNCHING_COEFF_1 = 0.27             # ไฟล์อ้างอิง NT38: fv*0.27*(2+4/βc)*sqrt(f'c)*bo*d
PUNCHING_COEFF_2 = 1.06             # ไฟล์อ้างอิง NT39: fv*1.06*sqrt(f'c)*bo*d
DOWEL_LBD_MIN_CM = 30.0             # ไฟล์อ้างอิง NY49: ความยาวฝังขั้นต่ำ 30 ซม.


@dataclass
class FootingSpreadInput:
    fc_ksc: float
    main_steel_type: str
    column_b_cm: float        # ขนาดเสาด้าน b (แนวแกน X)
    column_h_cm: float        # ขนาดเสาด้าน h (แนวแกน Y)
    pd_kg: float                # น้ำหนักบรรทุกคงที่จากเสา (DL, unfactored, service)
    pl_kg: float                # น้ำหนักบรรทุกจรจากเสา (LL, unfactored, service)
    qa_net_kg_m2: float         # หน่วยแรงแบกทานดินสุทธิที่ยอมให้ (net allowable soil bearing pressure)
    main_bar_dia_mm: float
    cover_cm: float = DEFAULT_FOOTING_COVER_CM
    founding_depth_m: float = FOUNDING_DEPTH_DEFAULT_M   # ระยะฝังรวม (สำหรับรูปตัด: ความสูงบน = ค่านี้ − ความหนา)


@dataclass
class OneWayShearCheck:
    direction: str
    cant_m: float
    d_cm: float
    vu_kg: float
    vc_kg: float
    phi_vc_kg: float
    shear_ok: bool


@dataclass
class PunchingShearCheck:
    bo_cm: float
    d_cm: float
    beta_c: float
    vu_kg: float
    vc1_kg: float
    vc2_kg: float
    vc_kg: float
    phi_vc_kg: float
    shear_ok: bool


@dataclass
class FootingFlexure:
    direction: str
    cant_m: float
    mu_kgm_per_m: float
    d_cm: float
    ru_ksc: float
    rreq: float
    rho_min: float
    rho_used: float
    over_reinforced: bool
    as_req_cm2: float          # As ต้องการรวมทั้งแถบกว้าง B (ไม่ใช่ต่อเมตร)
    n_bars_req: int
    n_bars_use: int
    as_provided_cm2: float     # As ที่ให้จริงรวมทั้งแถบกว้าง B
    reinf_ok: bool


@dataclass
class DowelCheck:
    lbd_cm: float       # ความยาวฝังที่ต้องการขั้นต่ำ
    ld_avail_cm: float  # ความยาวฝังที่มีพื้นที่ให้จริง
    dowel_ok: bool


@dataclass
class FootingSpreadResult:
    b_req_m: float
    B_cm: float
    area_m2: float
    q_actual_kg_m2: float
    bearing_ok: bool
    qu_factored_kg_m2: float
    t_cm: float
    d_x_cm: float
    d_y_cm: float
    shear_x: OneWayShearCheck
    shear_y: OneWayShearCheck
    punching: PunchingShearCheck
    flex_x: FootingFlexure
    flex_y: FootingFlexure
    dowel: DowelCheck
    main_bar_type: str
    reinf_label_x: str
    reinf_label_y: str
    design_ok: bool
    design_fail_reason: str
    thickness_search_exhausted: bool


def _round_up_to_step(value: float, step: float) -> float:
    return math.ceil(value / step) * step


def _effective_depths_cm(t_cm: float, cover_cm: float, bar_dia_mm: float) -> tuple:
    """ระยะประสิทธิผล d ของเหล็กเสริม 2 ชั้นตั้งฉากกัน (mat แบบ 2 ทิศทาง) — ชั้น X วางก่อน
    (ใกล้ผิวรับแรงดึงสุด, d มากกว่า) ชั้น Y วางทับชั้น X (d น้อยกว่าลงมา 1 เท่าของขนาดเหล็ก)
    ตรงกับไฟล์อ้างอิง SDM Plus_Footing_Bearing Pu.xlsx (cell NT27, NT45) เป๊ะ."""
    db_cm = bar_dia_mm / 10.0
    d_x = t_cm - cover_cm - db_cm / 2.0
    d_y = d_x - db_cm
    return d_x, d_y


def _one_way_shear(direction: str, cant_m: float, d_cm: float, B_cm: float,
                    qu_kg_cm2: float, fc_ksc: float) -> OneWayShearCheck:
    cant_cm = cant_m * 100.0
    vu = qu_kg_cm2 * B_cm * max(0.0, cant_cm - d_cm)
    vc = 0.53 * math.sqrt(fc_ksc) * B_cm * d_cm
    phi_vc = PHI_V * vc
    return OneWayShearCheck(
        direction=direction, cant_m=cant_m, d_cm=d_cm, vu_kg=vu, vc_kg=vc,
        phi_vc_kg=phi_vc, shear_ok=(vu <= phi_vc),
    )


def _punching_shear(b_col_cm: float, h_col_cm: float, d_cm: float, B_cm: float,
                     qu_kg_cm2: float, pu_col_kg: float, fc_ksc: float) -> PunchingShearCheck:
    bo = 2.0 * (b_col_cm + d_cm) + 2.0 * (h_col_cm + d_cm)
    beta_c = max(b_col_cm, h_col_cm) / min(b_col_cm, h_col_cm) if min(b_col_cm, h_col_cm) > 0 else 1.0
    vu = pu_col_kg - qu_kg_cm2 * (b_col_cm + d_cm) * (h_col_cm + d_cm)
    vu = max(vu, 0.0)

    vc1 = PUNCHING_COEFF_1 * (2.0 + 4.0 / beta_c) * math.sqrt(fc_ksc) * bo * d_cm
    vc2 = PUNCHING_COEFF_2 * math.sqrt(fc_ksc) * bo * d_cm
    vc = min(vc1, vc2)
    phi_vc = PHI_V * vc

    return PunchingShearCheck(
        bo_cm=bo, d_cm=d_cm, beta_c=beta_c, vu_kg=vu,
        vc1_kg=vc1, vc2_kg=vc2, vc_kg=vc, phi_vc_kg=phi_vc,
        shear_ok=(vu <= phi_vc),
    )


def _flexure_strip(direction: str, cant_m: float, qu_kg_m2: float, d_cm: float, B_cm: float,
                    fc_ksc: float, fy_ksc: float, rho_min: float, rho_max: float,
                    bar_dia_mm: float, bar_area: float) -> FootingFlexure:
    """ออกแบบเหล็กเสริมทิศทางเดียว — คิดโมเมนต์/Ru ต่อแถบกว้าง 1 ม. (คณิตศาสตร์เทียบเท่ากับ
    ที่ไฟล์อ้างอิงคิดเป็นโมเมนต์รวมทั้งแถบกว้าง B แล้วหาร B ออกใน Ru ภายหลัง) แต่ As ที่ต้องการ/
    จำนวนเหล็กคิดรวมทั้งแถบกว้าง B ตรงกับไฟล์ (ไม่ใช่ต่อเมตรแบบโมดูลพื้น)."""
    mu_kgm_per_m = qu_kg_m2 * cant_m ** 2 / 2.0
    ru = mu_kgm_per_m * 100.0 / (PHI_B * 100.0 * d_cm ** 2) if d_cm > 0 else 999.0

    under_sqrt = 1.0 - (2.0 * ru) / (0.85 * fc_ksc)
    over_reinforced = under_sqrt < 0
    if over_reinforced:
        rreq = rho_max
    else:
        rreq = 0.85 * (fc_ksc / fy_ksc) * (1.0 - math.sqrt(under_sqrt))

    rho_used = max(rreq, rho_min)
    over_reinforced = over_reinforced or (rho_used > rho_max)
    as_req_cm2_m = rho_used * 100.0 * d_cm
    as_req_cm2 = as_req_cm2_m * (B_cm / 100.0)   # As รวมทั้งแถบกว้าง B (cm²/m * m = cm²)

    n_bars_req = max(1, math.ceil(as_req_cm2 / bar_area))
    n_bars_use = n_bars_req
    as_provided_cm2 = n_bars_use * bar_area

    reinf_ok = (as_provided_cm2 >= as_req_cm2) and (not over_reinforced)

    return FootingFlexure(
        direction=direction, cant_m=cant_m, mu_kgm_per_m=mu_kgm_per_m, d_cm=d_cm,
        ru_ksc=ru, rreq=rreq, rho_min=rho_min, rho_used=rho_used, over_reinforced=over_reinforced,
        as_req_cm2=as_req_cm2, n_bars_req=n_bars_req, n_bars_use=n_bars_use,
        as_provided_cm2=as_provided_cm2, reinf_ok=reinf_ok,
    )


def _dowel_check(fc_ksc: float, fy_ksc: float, bar_area: float, B_cm: float,
                  cover_cm: float, column_b_cm: float, column_h_cm: float) -> DowelCheck:
    """ตรวจสอบความยาวฝังเหล็กทาบ/เหล็กหนวดกุ้ง (dowel bar) จากเสาลงฐานราก — ตรงกับไฟล์
    อ้างอิง SDM Plus_Footing_Bearing Pu.xlsx (cell NT49/NT50) — สมมติใช้ขนาดเหล็กเดียวกับ
    เหล็กเสริมหลักของฐานราก (ดูหมายเหตุขอบเขตด้านบนของไฟล์)."""
    lbd = max(0.06 * bar_area * fy_ksc / math.sqrt(fc_ksc), DOWEL_LBD_MIN_CM)
    ld_avail = B_cm - cover_cm - (max(column_b_cm, column_h_cm) / 2.0)
    return DowelCheck(lbd_cm=lbd, ld_avail_cm=ld_avail, dowel_ok=(ld_avail >= lbd))


def calculate(inp: FootingSpreadInput) -> FootingSpreadResult:
    fy = GS_STEEL_FY_KSC[inp.main_steel_type]
    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    rho_min = compute_rho_min(fy)
    beta1 = compute_beta1(inp.fc_ksc)
    rho_b = compute_rho_b(inp.fc_ksc, fy, beta1)
    rho_max = compute_rho_max(rho_b)
    bar_area = bar_area_cm2(inp.main_bar_dia_mm)

    # --- 1) หาขนาดฐานราก B จากแรงบริการ/qa_net ---
    service_load = inp.pd_kg + inp.pl_kg
    b_req_m = math.sqrt(service_load / inp.qa_net_kg_m2) if inp.qa_net_kg_m2 > 0 else FOOTING_SIZE_MAX_CM / 100.0
    B_cm = _round_up_to_step(b_req_m * 100.0, FOOTING_SIZE_STEP_CM)
    B_cm = max(B_cm, FOOTING_SIZE_MIN_CM, max(inp.column_b_cm, inp.column_h_cm) + 2.0 * FOOTING_EDGE_MARGIN_MIN_CM)
    B_cm = min(B_cm, FOOTING_SIZE_MAX_CM)
    B_m = B_cm / 100.0
    area_m2 = B_m ** 2
    q_actual = service_load / area_m2 if area_m2 > 0 else 0.0
    bearing_ok = q_actual <= inp.qa_net_kg_m2

    qu_factored_kg_m2 = (1.4 * inp.pd_kg + 1.7 * inp.pl_kg) / area_m2 if area_m2 > 0 else 0.0
    qu_kg_cm2 = qu_factored_kg_m2 / 10000.0
    pu_col_kg = 1.4 * inp.pd_kg + 1.7 * inp.pl_kg

    cant_x_m = max(0.0, (B_cm - inp.column_b_cm) / 2.0) / 100.0
    cant_y_m = max(0.0, (B_cm - inp.column_h_cm) / 2.0) / 100.0

    # --- 2) ไล่ลองความหนา t จนกว่าจะผ่านแรงเฉือนทุกกรณี ---
    chosen = None
    thickness_search_exhausted = True
    for t_cm in FOOTING_THICKNESS_CM_OPTIONS:
        d_x, d_y = _effective_depths_cm(t_cm, inp.cover_cm, inp.main_bar_dia_mm)
        if d_x <= 0 or d_y <= 0:
            continue
        shear_x = _one_way_shear("X", cant_x_m, d_x, B_cm, qu_kg_cm2, inp.fc_ksc)
        shear_y = _one_way_shear("Y", cant_y_m, d_y, B_cm, qu_kg_cm2, inp.fc_ksc)
        d_avg = (d_x + d_y) / 2.0
        punching = _punching_shear(inp.column_b_cm, inp.column_h_cm, d_avg, B_cm, qu_kg_cm2, pu_col_kg, inp.fc_ksc)
        if shear_x.shear_ok and shear_y.shear_ok and punching.shear_ok:
            chosen = (t_cm, d_x, d_y, shear_x, shear_y, punching)
            thickness_search_exhausted = False
            break

    if chosen is None:
        t_cm = FOOTING_THICKNESS_CM_OPTIONS[-1]
        d_x, d_y = _effective_depths_cm(t_cm, inp.cover_cm, inp.main_bar_dia_mm)
        d_x, d_y = max(d_x, 1.0), max(d_y, 1.0)
        shear_x = _one_way_shear("X", cant_x_m, d_x, B_cm, qu_kg_cm2, inp.fc_ksc)
        shear_y = _one_way_shear("Y", cant_y_m, d_y, B_cm, qu_kg_cm2, inp.fc_ksc)
        d_avg = (d_x + d_y) / 2.0
        punching = _punching_shear(inp.column_b_cm, inp.column_h_cm, d_avg, B_cm, qu_kg_cm2, pu_col_kg, inp.fc_ksc)
    else:
        t_cm, d_x, d_y, shear_x, shear_y, punching = chosen

    # --- 3) ออกแบบเหล็กเสริม 2 ทิศทาง (จำนวนเหล็กกระจายตลอดความกว้าง B) ---
    flex_x = _flexure_strip("X", cant_x_m, qu_factored_kg_m2, d_x, B_cm, inp.fc_ksc, fy, rho_min, rho_max,
                             inp.main_bar_dia_mm, bar_area)
    flex_y = _flexure_strip("Y", cant_y_m, qu_factored_kg_m2, d_y, B_cm, inp.fc_ksc, fy, rho_min, rho_max,
                             inp.main_bar_dia_mm, bar_area)

    reinf_label_x = f"{flex_x.n_bars_use}-{main_bar_type}{inp.main_bar_dia_mm:.0f}"
    reinf_label_y = f"{flex_y.n_bars_use}-{main_bar_type}{inp.main_bar_dia_mm:.0f}"

    # --- 4) ตรวจสอบความยาวฝังเหล็กทาบ/dowel ---
    dowel = _dowel_check(inp.fc_ksc, fy, bar_area, B_cm, inp.cover_cm, inp.column_b_cm, inp.column_h_cm)

    warnings = []
    if not bearing_ok:
        warnings.append("⚠️ หน่วยแรงแบกทานดินที่เกิดขึ้นจริงเกินค่าที่ยอมให้ (qa_net) — กรุณาขยายขนาดฐานรากหรือเพิ่ม qa_net")
    if thickness_search_exhausted:
        warnings.append("⚠️ ไม่พบความหนาที่ผ่านแรงเฉือนทุกกรณีภายในช่วงที่ลอง (สูงสุด "
                         f"{FOOTING_THICKNESS_CM_OPTIONS[-1]:.0f} ซม.) กรุณาขยายขนาดฐานราก (B) หรือเพิ่ม f'c")
    if not shear_x.shear_ok:
        warnings.append("⚠️ แรงเฉือนทางเดียวทิศทาง X ไม่ผ่าน")
    if not shear_y.shear_ok:
        warnings.append("⚠️ แรงเฉือนทางเดียวทิศทาง Y ไม่ผ่าน")
    if not punching.shear_ok:
        warnings.append("⚠️ แรงเฉือนทะลุ (punching shear) ไม่ผ่าน")
    if not flex_x.reinf_ok:
        warnings.append("⚠️ เหล็กเสริมทิศทาง X ไม่เพียงพอ")
    if not flex_y.reinf_ok:
        warnings.append("⚠️ เหล็กเสริมทิศทาง Y ไม่เพียงพอ")
    if not dowel.dowel_ok:
        warnings.append("⚠️ ความยาวฝังเหล็กทาบ/เหล็กหนวดกุ้ง (dowel) ไม่เพียงพอ — กรุณาขยายขนาดฐานราก")

    design_ok = (bearing_ok and shear_x.shear_ok and shear_y.shear_ok and punching.shear_ok
                 and flex_x.reinf_ok and flex_y.reinf_ok and dowel.dowel_ok)
    design_fail_reason = " ".join(warnings)

    return FootingSpreadResult(
        b_req_m=b_req_m, B_cm=B_cm, area_m2=area_m2, q_actual_kg_m2=q_actual, bearing_ok=bearing_ok,
        qu_factored_kg_m2=qu_factored_kg_m2, t_cm=t_cm, d_x_cm=d_x, d_y_cm=d_y,
        shear_x=shear_x, shear_y=shear_y, punching=punching, flex_x=flex_x, flex_y=flex_y, dowel=dowel,
        main_bar_type=main_bar_type, reinf_label_x=reinf_label_x, reinf_label_y=reinf_label_y,
        design_ok=design_ok, design_fail_reason=design_fail_reason,
        thickness_search_exhausted=thickness_search_exhausted,
    )
