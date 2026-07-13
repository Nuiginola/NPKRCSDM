"""
Module 5.2 — ฐานเสาเข็ม (Pile Cap)

ขอบเขต: ฐานเสาเข็มรองรับเสาต้นเดียวรับแรงตามแนวแกน (concentric axial load) เท่านั้น —
รองรับจำนวนเสาเข็ม 1 ต้น (กึ่งกลางเสาตรงๆ), 2, 3 (เรียงแถวเดียว "3a"), และ 4 ต้น (จัดเรียง 2x2)
เท่านั้นในเวอร์ชันนี้ (ตัดสินใจร่วมกับผู้ใช้ผ่าน AskUserQuestion เมื่อ 2026-07 — ไฟล์อ้างอิงมีให้
ทั้งหมด 6 แบบ 1-6 ต้น แต่ผู้ใช้เลือกให้ทำเฉพาะ 2-4 ต้นในรอบแรก เพราะเป็นรูปแบบที่พบบ่อยที่สุดใน
บ้านพักอาศัยขนาดเล็ก-กลาง ส่วน 5-6 ต้นสามารถเพิ่มภายหลังได้ถ้าจำเป็นจริง — เพิ่มกรณี 1 ต้นภายหลัง
ตามคำขอผู้ใช้ 2026-07-11 ดูรายละเอียดที่ `_pile_geometry`)

ที่มา/ยืนยันสูตร: ไฟล์อ้างอิง 3 ไฟล์ (โฟลเดอร์ SDM+beta) — "SDM Plus_Footing_2Pile Pu.xlsx",
"SDM Plus_Footing_3a Pile Pu.xlsx", "SDM Plus_Footing_4Pile Pu.xlsx" — ตรวจสอบทุกสูตรหลัก
ทีละ cell (helper block ซ่อน ALT2:ALX49 ของแต่ละไฟล์ + hidden geometry block ZK/ZL,
"printable report" block D/T/W/Z คอลัมน์ rows 17-45, และตาราง pile catalog ANM:ANW) จนครบ
ทุกสูตรที่ใช้จริงในการคำนวณ (ไม่ใช่แค่ดูตัวอย่างตัวเลขผิวเผิน) — ตัวอย่างตัวเลขที่ยืนยัน
(ใช้ค่าเรขาคณิต A/B/d จากไฟล์ตรงๆ ไม่ผ่านสูตรระยะขอบ/ระยะห่างอย่างง่ายที่ทำให้เรขาคณิตต่างจาก
ไฟล์ ดูหมายเหตุด้านล่าง — ยืนยันเฉพาะสูตรโมเมนต์/แรงเฉือน/เหล็กเสริมว่าตรงกับไฟล์ทุกจุด):
  - 2 ต้น: fc'=150, fy=3000, a1=b1=30cm, D(เสาเข็ม)=22cm (ANO13 "22x22"), A=1.175m, B=0.5m,
    C(ระยะศูนย์เสาเข็มถึงกลางฐานราก)=0.3375m, T=30cm, d1=21.7cm, Wu=43,197.875kg -> pile load=
    21,598.94kg, Mu=4,049.8 kg-m — แรงเฉือนทางเดียวไม่เข้าเงื่อนไขตรวจสอบในตัวอย่างนี้ (หน้าตัด
    วิกฤต d+a1/2=0.367m > C=0.3375m คือพ้นตำแหน่งเสาเข็มริมไปแล้ว ไฟล์แสดงผลเป็น "-"), Vu(column
    punching)=43,197.88kg, fvVc=23,945.84kg (NOT ผ่าน — ตัวอย่างจากไฟล์เอง), bo(punching เสาเข็ม
    เดี่ยว)=4×(22+21.7)=174.8cm, fvVc(pile punching)=41,857.34kg, As#1=7.526 cm², As#2(min)=
    11.10 cm² (7-DB16 ใช้จริง), Lbd=29.55cm, Ld=95cm
  - 4 ต้น: fc'=150, fy=3000, a1=b1=30cm, D=18cm (ANO11 "18x18"), A=B=0.95m, C=0.275m, T=35cm,
    d1=26.7cm, d2=25.1cm, Wu=65,184.9375kg -> pile load=16,296.23kg, Mu(ทิศ1)=2×pile load×X1
    =4,074.06 kg-m (X1=C-a1/2=0.125m), Vu(beam)=2×pile load=32,592.46kg, Vu(column punching)
    =4×pile load=65,184.92kg (นับเสาเข็มทุกต้น), bo(punching เสาเข็มเดี่ยว)=4×(18+26.7)=178.8cm,
    fvVc(pile punching)=52,680.42kg, As#1=11.92 cm² (ใช้ rho_min เพราะ rreq<rho_min),
    As#2(เต็มรูปแบบ ไม่ใช่ min เฉยๆ, คำนวณด้วย d2)=11.21 cm² (ยืนยันจาก AB31/AB35 ของ "printable
    report" block — ตรงกับ As#1 โดยบังเอิญเกือบเท่ากันเพราะทั้งคู่ถูก rho_min ครอบเหมือนกัน)
  - 3 ต้น (3a, เรียงแถวเดียว): fc'=150, fy=3000, a1=b1=30cm, D=18cm (ANO12 "18x18"), A=1.5m,
    B=0.4m, C=0.55m (ระยะเต็ม ไม่ใช่ครึ่งหนึ่งเหมือน 2/4 ต้น เพราะเสาเข็มริมอยู่ห่างจากศูนย์กลาง
    1 ระยะห่างเต็ม), T=50cm, d1=41.7cm, d2=40.1cm, Wu=61,438kg -> pile load=20,479.33kg,
    Mu=pile load×X1=8,191.73 kg-m (X1=C-a1/2=0.4m, ไม่คูณ 2 เหมือน 2 ต้น เพราะมีแค่เสาเข็มริม
    1 ต้นต่อด้านที่พ้นหน้าตัดวิกฤต), Vu(column punching)=2×pile load=40,958.66kg (นับเฉพาะ 2 ต้น
    ริม ไม่นับต้นกลางที่อยู่ตรงตำแหน่งเสาพอดี), bo(punching เสาเข็มเดี่ยว)=4×(18+41.7)=238.8cm,
    As#1=7.84 cm², As#2(min เท่านั้น)=28.27 cm² (16-DB16), Lbd=29.55cm, Ld=127.5cm
  หมายเหตุ bo (เส้นรอบรูปวิกฤตรอบเสาเข็มเดี่ยว): ตารางเสาเข็มในไฟล์มีทั้งสูตรวงกลม π×(D+d)
  (แถวเสาเข็ม Hp ทรงกลม) และสูตรสี่เหลี่ยมจัตุรัส 4×(D+d) (แถวเสาเข็มอัดแรงสี่เหลี่ยม เช่น
  "18x18"/"22x22") — ตัวอย่างที่ยืนยันทั้ง 3 ไฟล์ใช้แถวเสาเข็มสี่เหลี่ยมทั้งหมด (4×(D+d))
  โมดูลนี้จึงเลือกสูตรสี่เหลี่ยมเป็นค่าเริ่มต้น (ดูรายละเอียดที่ฟังก์ชัน _pile_punching_shear)
  ทั้งหมดคำนวณซ้ำได้ตรงกับสูตรในไฟล์ต้นฉบับ 100% เมื่อป้อนค่าเรขาคณิต A/B/C/d เดียวกัน (ยกเว้น
  ผลต่างเล็กน้อย <1% จากการที่ไฟล์ ROUND(14/fy,4)=0.0047 แต่โมดูลนี้ใช้ rho_min แบบไม่ปัดเศษ
  0.046667% ตรงกับ common.design_params.compute_rho_min ที่ทุกโมดูลอื่นใช้อยู่แล้ว รวมถึง
  โมดูล 5.1 — ดู test คู่กับไฟล์นี้)

การลดความซับซ้อนของเรขาคณิตฐานราก (ตำแหน่ง/ขนาดเสาเข็ม) — จุดที่ต่างจากไฟล์อ้างอิงโดยตั้งใจ
(เหมือนหลักการเดียวกับที่โมดูล 5.1 แทนที่ตารางแรงแบกทานดินด้วย qa_net_kg_m2 กรอกตรง):
  ไฟล์อ้างอิงใช้ตาราง VLOOKUP ผลิตภัณฑ์เสาเข็มมาตรฐาน ~60 แถว (คอลัมน์ ANM:ANW) เพื่อดึงค่า
  "ระยะขอบฐานรากถึงศูนย์เสาเข็มริม" (ANV, หัวตาราง "1-1.5D") และ "ระยะห่างศูนย์กลางเสาเข็ม c/c"
  (ANW, หัวตาราง "3D") ซึ่งจากการตรวจสอบค่าจริงในตาราง พบว่า ANV ≈ 1.0-1.2×ขนาดเสาเข็มจริง (ANU,
  ไม่ใช่เต็ม 1.5D ตามหัวตาราง) และ ANW ≈ 2.67-3.0×ANV (แถวท้ายตาราง/ขนาดใหญ่ใช้สูตรตรง ANW=ANV×3)
  — โมดูลนี้ตัดตารางค้นหา 60 แถวออก แทนที่ด้วยการกรอกขนาดเสาเข็ม (pile_size_cm, D) และกำลังรับ
  น้ำหนักปลอดภัยต่อต้น (pile_safe_load_ton) โดยตรง แล้วคำนวณระยะขอบ/ระยะห่างจากกฎมาตรฐานทั่วไป
  ที่ใช้กันแพร่หลายในงานฐานรากเสาเข็ม (PILE_EDGE_MARGIN_FACTOR=1.5×D, PILE_SPACING_FACTOR=3.0×D)
  — ค่านี้ ≥ ค่าจริงในตารางของไฟล์เสมอ (อนุรักษ์นิยมกว่า/ฐานรากใหญ่กว่าเล็กน้อย ปลอดภัยกว่า)
  ดังนั้นขนาดฐานราก A/B ที่คำนวณได้จากโมดูลนี้จะไม่ตรงเป๊ะกับตัวอย่างในไฟล์ (ซึ่งใช้ค่าตาราง
  เฉพาะผลิตภัณฑ์) แต่สูตรโมเมนต์/แรงเฉือน/เหล็กเสริมทั้งหมด (เมื่อป้อนเรขาคณิตเดียวกัน) ตรงกับ
  ไฟล์ทุกจุดตามที่ยืนยันไว้ข้างต้น

รูปแบบเรขาคณิตของแต่ละจำนวนเสาเข็ม (ยืนยันจากไฟล์ ZK/ZL block, สูตร ZL9/ZL10/ZL11):
  - 2 ต้น: เสาเข็มเรียงเป็นเส้นตรง 1 แถว ห่างกัน spacing เต็ม ห่างจากศูนย์กลางฐานรากข้างละครึ่ง
    (C=spacing/2) A=spacing+2×margin, B=2×margin (ฐานรากแคบสุดเท่าที่จำเป็นในทิศทางตั้งฉาก)
    ทิศทางตั้งฉาก (#2) ไม่มีโมเมนต์จริง (เสาเข็มไม่มีต้นไหนอยู่นอกหน้าตัดวิกฤตในทิศนี้) —
    ใส่เหล็กเสริมขั้นต่ำ (rho_min) เท่านั้น
  - 3 ต้น (3a): เสาเข็มเรียงเป็นเส้นตรง 1 แถวเช่นกัน แต่มีต้นกลางอยู่ตรงตำแหน่งเสาพอดี (ไม่ใช่รูป
    สามเหลี่ยม) + ต้นริม 2 ต้นห่างจากศูนย์กลางเต็ม 1 ระยะห่าง (C=spacing เต็ม ไม่ใช่ครึ่งหนึ่ง)
    A=2×spacing+2×margin, B=2×margin — พฤติกรรมด้านโมเมนต์/แรงเฉือนทางเดียวเหมือน 2 ต้นทุก
    ประการ (ไม่คูณ 2 เพราะมีแค่ต้นริม 1 ต้นต่อด้านที่พ้นหน้าตัดวิกฤต) ทิศทางตั้งฉาก (#2) เหล็ก
    ขั้นต่ำเท่านั้นเหมือน 2 ต้น — แต่แรงเฉือนทะลุที่ผิวเสา (column punching) นับเฉพาะ 2 ต้นริม
    (ต้นกลางถือว่าถ่ายน้ำหนักตรงเข้าเสาโดยไม่ต้อง "เจาะทะลุ" ผ่านหน้าตัดวิกฤต)
  - 4 ต้น: เสาเข็มจัดเรียง 2x2 (ตาราง) ฐานรากเป็นรูปสี่เหลี่ยมจัตุรัสเสมอ (A=B, กำหนดจากระยะห่าง
    เสาเข็มล้วนๆ ไม่ขึ้นกับสัดส่วนเสา แม้เสาจะเป็นสี่เหลี่ยมผืนผ้า) ทั้ง 2 ทิศทางมีโมเมนต์จริง
    (มี 2 ต้นอยู่นอกหน้าตัดวิกฤตทุกทิศทาง จึงคูณ 2 ทั้ง Mu และ Vu) แต่ละทิศทางใช้ขนาดเสาด้าน
    ของตัวเอง (a1 ทิศทาง#1, b1 ทิศทาง#2) หาแขนโมเมนต์ แต่ใช้ตำแหน่งเสาเข็มเดียวกัน (C เท่ากัน
    ทั้ง 2 ทิศทาง เพราะฐานรากเป็นจัตุรัส) — แรงเฉือนทะลุที่ผิวเสานับเสาเข็มทุกต้น (4 ต้น)

ขอบเขตที่ตัดออก/สมมติฐาน (เหมือนหลักการเดียวกับโมดูล 5.1 เท่าที่เกี่ยวข้อง):
  - **โมเมนต์ที่ฐานราก**: ไม่รองรับ — เฉพาะแรงตามแนวแกน (Pd, Pl) เท่านั้น
  - **ตำแหน่งเสา (punching)**: เสาใน (interior column) เสมอ เหมือนโมดูล 5.1
  - **แรงเฉือนทางเดียว (beam shear) ตรวจทิศทางเดียว**: ตรงกับไฟล์อ้างอิงทุกไฟล์ — แม้กรณี 4 ต้น
    ที่มีโมเมนต์จริงทั้ง 2 ทิศทาง ไฟล์อ้างอิงก็ตรวจแรงเฉือนทางเดียวแค่ทิศทาง#1 (ตามแนว a1) เท่านั้น
    ไม่มีชุดตรวจแยกทิศทาง#2 เลย (ช่องผลลัพธ์ "Beam Shear" ในไฟล์มีแค่ชุดเดียว) — เป็นข้อจำกัดที่
    มีอยู่แล้วในเครื่องมือต้นฉบับ ไม่ใช่จุดที่ตัดออกเพิ่มเติมในโมดูลนี้ (กรณีเสาเป็นสี่เหลี่ยมผืนผ้า
    ที่ b1 ต่างจาก a1 มาก ควรตรวจสอบเพิ่มเติมด้วยมือ)
  - **แรงเฉือนทะลุตรวจ 2 แบบ (ไม่ใช่ 3 แบบเต็มรูปแบบ ACI)**: เหมือนโมดูล 5.1 — Vc1 (ค่าคงที่
    0.27) และ Vc2 (ค่าคงที่ 1.06) เท่านั้น ไม่มีสูตรที่ 3 (αs*d/bo+2)
  - **น้ำหนักตัวเองฐานราก/ดินถมด้านบน (Ws, Wf) รวมอยู่ใน Wu ที่ออกแบบจริง**: ต่างจากโมดูล 5.1
    ที่ไม่รวม (เพราะฐานรากแผ่ถ่ายน้ำหนักส่วนนี้ลงดินโดยตรงไม่ผ่านหน้าตัด) — ฐานเสาเข็มต้องถ่าย
    น้ำหนักทุกส่วน (รวมน้ำหนักตัวเอง+ดินถมด้านบน) ลงเสาเข็มทั้งหมด จึงต้องรวมเป็นส่วนหนึ่งของ
    น้ำหนักที่กระจายลงเสาเข็ม (ตรงกับไฟล์อ้างอิง cell W25: Wu=1.4×(Ws+Wf+PD)+1.7×PL) — น้ำหนัก
    ตัวเองคอนกรีต hardcode 2400 kg/m³ (ไม่ผูกกับ f'c ที่ผู้ใช้กรอก ตรงกับไฟล์อ้างอิง cell ALX8)
    ดินถมใช้หน่วยน้ำหนักดินเริ่มต้น 1.4 ton/m³ และความลึกฝังฐานราก (F.I. depth) เริ่มต้น 1.0 m
    ตรงกับค่าเริ่มต้นในไฟล์ (W17=1.4, W18=1) — ผู้ใช้ปรับได้
  - **การรวมชุดผสมแรง (load combination)**: ไฟล์อ้างอิงมีตัวเลือกหลายชุด (DL, LL, DL+LL,
    1.4DL+1.7LL, 1.7DL+2.0LL) — โมดูลนี้ใช้เฉพาะ Wu=1.4(Ws+Wf+PD)+1.7PL (ชุด "1.4DL+1.7LL")
    เสมอ ให้สอดคล้องกับทุกโมดูลอื่นในโปรเจกต์นี้ (ไม่เปิดให้เลือกชุดอื่นเหมือนไฟล์ต้นฉบับ)
  - **ขนาด/ชนิดเหล็กฝัง (dowel)**: สมมติใช้ขนาดเดียวกับเหล็กเสริมหลักของฐานราก เหมือนโมดูล 5.1

หลักการออกแบบอัตโนมัติ (auto-design เหมือนทุกโมดูลก่อนหน้า):
  1. คำนวณเรขาคณิตฐานราก (A, B, ตำแหน่งเสาเข็ม) จากขนาดเสาเข็ม+จำนวนเสาเข็มเพียงครั้งเดียว
     (ไม่ขึ้นกับความหนา T)
  2. ไล่ลองความหนา T จากน้อยไปมาก (FOOTING_THICKNESS_CM_OPTIONS ชุดเดียวกับโมดูล 5.1) คำนวณ
     Ws/Wf/Wu ใหม่ทุกครั้ง (เพราะขึ้นกับ T) จนกว่าจะผ่านแรงเฉือนทางเดียว + แรงเฉือนทะลุที่ผิวเสา
     + แรงเฉือนทะลุรอบเสาเข็มเดี่ยวทั้งหมด (ต่างจากไฟล์อ้างอิงที่ให้ผู้ใช้กรอก T เองแล้วรายงาน
     OK/NOT — และต่างจากไฟล์อ้างอิงที่คำนวณ Wf จาก T ที่ผู้ใช้กรอกเริ่มต้นเพียงครั้งเดียวไม่ได้
     lag ตาม T สุดท้าย โมดูลนี้คำนวณ Ws/Wf ใหม่ทุกรอบการไล่ลอง T ให้สอดคล้องกันเองเสมอ)
  3. ออกแบบเหล็กเสริม 2 ทิศทาง (ทิศทาง#1 ออกแบบจริงเสมอ, ทิศทาง#2 ออกแบบจริงเฉพาะ 4 ต้น
     มิฉะนั้นใส่ขั้นต่ำ) แล้วปัดจำนวนเหล็กขึ้น (ROUNDUP)
  4. ตรวจสอบความยาวฝังเหล็กทาบ/เหล็กหนวดกุ้ง (dowel) เหมือนโมดูล 5.1
  5. ตรวจสอบน้ำหนักบรรทุกต่อต้นเทียบกับกำลังรับน้ำหนักปลอดภัยที่ผู้ใช้กรอก (ระดับ Service,
     ไม่คูณตัวคูณ — ตรงกับไฟล์อ้างอิง cell AC27)
"""

import math
from dataclasses import dataclass

from common.design_params import PHI_B, PHI_V, compute_beta1, compute_rho_b, compute_rho_max, compute_rho_min
from modules.slab_on_ground import GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2
from modules.stair_straight import CONCRETE_UNIT_WEIGHT_KG_M3
from modules.footing_spread import (
    DEFAULT_FOOTING_COVER_CM, FOOTING_THICKNESS_CM_OPTIONS,
    PUNCHING_COEFF_1, PUNCHING_COEFF_2, DOWEL_LBD_MIN_CM, FOOTING_EDGE_MARGIN_MIN_CM,
)

PILE_COUNT_OPTIONS = [1, 2, 3, 4]

PILE_EDGE_MARGIN_FACTOR = 1.5   # ระยะขอบฐานรากถึงศูนย์เสาเข็มริม = 1.5xD (ดูหมายเหตุด้านบน)
PILE_SPACING_FACTOR = 3.0       # ระยะห่างศูนย์กลางเสาเข็ม c/c = 3xD

# รูปทรงเสาเข็ม (2026-07-11, เพิ่มตามคำขอผู้ใช้) — มีผลต่อสูตรเส้นรอบรูปวิกฤตของแรงเฉือนทะลุ
# รอบเสาเข็มเดี่ยวเท่านั้น (_pile_punching_shear) ไม่มีผลต่อสูตรอื่น (เรขาคณิตฐานราก/โมเมนต์/
# แรงเฉือนทางเดียว/แรงเฉือนทะลุที่ผิวเสา ใช้ค่า D เป็นมิติเดียวกันทุกรูปทรง) — แบ่ง 2 กลุ่ม:
#   "กลุ่มสี่เหลี่ยม" (square, square_hollow) ใช้เส้นรอบรูปสี่เหลี่ยมจัตุรัสสมมูล 4×(D+d) —
#   สูตรที่ยืนยันตรงกับไฟล์อ้างอิง 100% สำหรับเสาเข็มคอนกรีตอัดแรงหน้าตัดสี่เหลี่ยมจัตุรัสจริง
#   (ดู docstring ด้านบน)
#   "กลุ่มวงกลม/ไม่ทราบรูปทรงแน่ชัด" (round, round_hollow, hex_hollow, i_beam) ใช้เส้นรอบรูป
#   วงกลม π×(D+d) — เป็นสูตรที่แม่นยำสำหรับเสาเข็มกลม (round/round_hollow) โดยตรง และเป็นค่า
#   ประมาณฝั่งปลอดภัย (conservative) สำหรับรูปทรงที่ไม่มีสูตรมาตรฐานเฉพาะ (หกเหลี่ยม/ตัวไอ) —
#   เหตุผล: เมื่อกำหนดมิติกว้าง D เท่ากัน เส้นรอบรูปวงกลม π×D จะน้อยกว่าเส้นรอบรูปสี่เหลี่ยมจัตุรัส
#   4×D เสมอ (π<4) ทำให้ผลลัพธ์ bo/Vc ต่ำกว่า → เข้มงวดกว่า/ปลอดภัยกว่าเมื่อไม่แน่ใจรูปทรงจริง
#   (ตรงข้ามกับที่อาจเข้าใจผิดว่าใช้สูตรสี่เหลี่ยมแทนรูปทรงไม่ทราบแน่ชัดจะปลอดภัยกว่า — ที่จริง
#   สูตรสี่เหลี่ยมให้ค่า bo/Vc **สูงกว่า** จึงไม่ conservative สำหรับรูปทรงที่ไม่ใช่สี่เหลี่ยมจริง)
#   — ผู้ใช้ควรตรวจสอบกับผู้ผลิตเสาเข็มจริงอีกครั้งสำหรับรูปทรงหกเหลี่ยม/ตัวไอโดยเฉพาะ
PILE_SHAPES = {
    "square": "สี่เหลี่ยมตัน (Square Solid)",
    "square_hollow": "สี่เหลี่ยมกลวง (Square Spun)",
    "round": "กลมตัน (Round Solid)",
    "round_hollow": "กลมกลวง (Round Spun)",
    "hex_hollow": "หกเหลี่ยมกลวง (Hexagon Spun)",
    "i_beam": "ตัวไอ (I-Section)",
}
PILE_SHAPE_SQUARE_FAMILY = {"square", "square_hollow"}   # ใช้สูตรสี่เหลี่ยมจัตุรัส 4×(D+d) (สูตรตรงจากไฟล์อ้างอิง)
DEFAULT_PILE_SHAPE = "square"

SOIL_UNIT_WEIGHT_DEFAULT_TON_M3 = 1.4     # ไฟล์อ้างอิง W17=1.4 t/cu.m.
FOOTING_INVERT_DEPTH_DEFAULT_M = 1.0      # ไฟล์อ้างอิง W18=1 m. (F.I. depth)


@dataclass
class PileCapInput:
    fc_ksc: float
    main_steel_type: str
    n_piles: int              # 1, 2, 3, หรือ 4
    column_b_cm: float        # a1 -- ขนาดเสาด้านที่ขนานแนวเรียงเสาเข็ม (ทิศทาง#1)
    column_h_cm: float        # b1 -- ขนาดเสาด้านตั้งฉาก (ทิศทาง#2, มีผลเฉพาะกรณี 4 ต้น)
    pile_size_cm: float        # D -- ขนาด/เส้นผ่านศูนย์กลางเสาเข็ม
    pile_safe_load_ton: float  # กำลังรับน้ำหนักปลอดภัยต่อต้น (Service)
    pd_kg: float
    pl_kg: float
    main_bar_dia_mm: float
    soil_unit_weight_ton_m3: float = SOIL_UNIT_WEIGHT_DEFAULT_TON_M3
    footing_invert_depth_m: float = FOOTING_INVERT_DEPTH_DEFAULT_M
    cover_cm: float = DEFAULT_FOOTING_COVER_CM
    pile_shape: str = DEFAULT_PILE_SHAPE   # key ของ PILE_SHAPES — มีผลต่อสูตรแรงเฉือนทะลุรอบเสาเข็มเดี่ยวเท่านั้น


@dataclass
class PileGeometry:
    n_piles: int
    edge_margin_cm: float
    spacing_cm: float
    A_cm: float                 # ความยาวฐานรากตามแนวเรียงเสาเข็ม (ทิศทาง#1)
    B_cm: float                 # ความกว้างฐานรากตั้งฉาก (ทิศทาง#2)
    pile_positions_cm: list     # [(x_cm, y_cm), ...] เทียบกับศูนย์กลางฐานราก
    c_dist_cm: float            # ระยะจากศูนย์กลางฐานรากถึงศูนย์เสาเข็มริม (แนวทิศทาง#1)
    n_outer_piles: int          # จำนวนเสาเข็มที่พ้นหน้าตัดวิกฤตต่อด้าน (ตัวคูณ Mu/Vu ทิศทาง#1)
    n_piles_column_punch: int   # จำนวนเสาเข็มที่นับรวมในแรงเฉือนทะลุที่ผิวเสา


@dataclass
class PileLoadServiceCheck:
    service_load_per_pile_ton: float
    safe_load_ton: float
    capacity_ok: bool


@dataclass
class OneWayShearCheckPC:
    applicable: bool     # False = หน้าตัดวิกฤตพ้นตำแหน่งเสาเข็มริม ไม่ต้องตรวจ (ตรงกับไฟล์ "-")
    vu_kg: float
    vc_kg: float
    phi_vc_kg: float
    shear_ok: bool


@dataclass
class ColumnPunchingShearCheckPC:
    bo_cm: float
    fallback_perimeter_used: bool
    beta_c: float
    vu_kg: float
    vc1_kg: float
    vc2_kg: float
    vc_kg: float
    phi_vc_kg: float
    shear_ok: bool


@dataclass
class PilePunchingShearCheck:
    bo_pile_cm: float
    vu_kg: float
    vc_kg: float
    phi_vc_kg: float
    shear_ok: bool


@dataclass
class PileCapFlexure:
    direction: str
    full_design: bool
    arm_cm: float
    mu_kgm: float
    d_cm: float
    width_cm: float
    ru_ksc: float
    rreq: float
    rho_min: float
    rho_used: float
    over_reinforced: bool
    as_req_cm2: float
    n_bars_req: int
    n_bars_use: int
    as_provided_cm2: float
    reinf_ok: bool


@dataclass
class DowelCheckPC:
    lbd_cm: float
    ld_avail_cm: float
    dowel_ok: bool


@dataclass
class PileCapResult:
    geometry: PileGeometry
    ws_kg: float
    wf_kg: float
    pnet_service_kg: float
    pile_load_service: PileLoadServiceCheck
    wu_kg: float
    pile_load_factored_kg: float
    t_cm: float
    d1_cm: float
    d2_cm: float
    beam_shear: OneWayShearCheckPC
    column_punching: ColumnPunchingShearCheckPC
    pile_punching: PilePunchingShearCheck
    flex_1: PileCapFlexure
    flex_2: PileCapFlexure
    dowel: DowelCheckPC
    main_bar_type: str
    reinf_label_1: str
    reinf_label_2: str
    design_ok: bool
    design_fail_reason: str
    thickness_search_exhausted: bool


def _pile_geometry(n_piles: int, column_b_cm: float, column_h_cm: float, pile_size_cm: float) -> PileGeometry:
    margin = PILE_EDGE_MARGIN_FACTOR * pile_size_cm
    spacing = PILE_SPACING_FACTOR * pile_size_cm

    if n_piles == 1:
        # เสาเข็ม 1 ต้น อยู่กึ่งกลางเสาตรงๆ (ไม่มีระยะยื่น/แถว) — เพิ่มตามคำขอผู้ใช้ 2026-07-11
        # (ตอบ AskUserQuestion: "เสาเข็มอยู่กึ่งกลางเสาตรงๆ") ฐานรากเป็นจัตุรัส กำหนดขนาดจาก
        # ระยะขอบรอบเสาเข็มเพียงอย่างเดียว (ไม่มี spacing เพราะไม่มีเสาเข็มต้นที่สอง) —
        # ผลข้างเคียงที่ตั้งใจ: c_dist_cm=0 ทำให้ _one_way_shear_pc คืน applicable=False เสมอ
        # (ไม่มีเสาเข็มต้นไหนพ้นหน้าตัดวิกฤต ตรงตามหลักวิศวกรรม — ไม่มีแรงเฉือนทางเดียวที่ต้อง
        # ตรวจสำหรับฐานรากเสาเข็มเดี่ยวศูนย์กลางตรงกับเสา) และ n_outer=0 ทำให้ Mu ทิศทาง#1=0
        # (ไม่มีโมเมนต์จริง ใส่เหล็กเสริมขั้นต่ำทั้ง 2 ทิศทางโดยอัตโนมัติผ่านสูตร _flexure_pc เดิม
        # ไม่ต้องเพิ่มเงื่อนไขพิเศษ)
        A_cm = 2.0 * margin
        B_cm = 2.0 * margin
        c_dist = 0.0
        positions = [(0.0, 0.0)]
        n_outer = 0
        n_column_punch = 1
    elif n_piles == 2:
        A_cm = spacing + 2.0 * margin
        B_cm = 2.0 * margin
        c_dist = spacing / 2.0
        positions = [(-c_dist, 0.0), (c_dist, 0.0)]
        n_outer = 1
        n_column_punch = 2   # ทุกต้น (ไม่มีต้นกลาง)
    elif n_piles == 3:
        A_cm = 2.0 * spacing + 2.0 * margin
        B_cm = 2.0 * margin
        c_dist = spacing
        positions = [(-c_dist, 0.0), (0.0, 0.0), (c_dist, 0.0)]
        n_outer = 1
        n_column_punch = 2   # เฉพาะ 2 ต้นริม (ไม่นับต้นกลางที่อยู่ตรงตำแหน่งเสา)
    elif n_piles == 4:
        A_cm = spacing + 2.0 * margin
        B_cm = A_cm           # ฐานรากจัตุรัสเสมอ
        c_dist = spacing / 2.0
        positions = [(-c_dist, -c_dist), (-c_dist, c_dist), (c_dist, -c_dist), (c_dist, c_dist)]
        n_outer = 2
        n_column_punch = 4   # ทุกต้น
    else:
        raise ValueError(f"จำนวนเสาเข็มไม่รองรับ: {n_piles} (รองรับเฉพาะ 1, 2, 3, 4)")

    # กันกรณีเรขาคณิตคำนวณได้เล็กกว่าขนาดเสา (เสาใหญ่/เสาเข็มเล็ก)
    A_cm = max(A_cm, column_b_cm + 2.0 * FOOTING_EDGE_MARGIN_MIN_CM)
    B_cm = max(B_cm, column_h_cm + 2.0 * FOOTING_EDGE_MARGIN_MIN_CM) if n_piles != 4 else max(A_cm, column_h_cm + 2.0 * FOOTING_EDGE_MARGIN_MIN_CM)
    if n_piles == 4:
        A_cm = B_cm = max(A_cm, B_cm)

    return PileGeometry(
        n_piles=n_piles, edge_margin_cm=margin, spacing_cm=spacing,
        A_cm=A_cm, B_cm=B_cm, pile_positions_cm=positions, c_dist_cm=c_dist,
        n_outer_piles=n_outer, n_piles_column_punch=n_column_punch,
    )


def _one_way_shear_pc(d1_cm: float, B_cm: float, column_b_cm: float, c_dist_cm: float,
                       n_outer: int, pile_load_kg: float, fc_ksc: float) -> OneWayShearCheckPC:
    """แรงเฉือนทางเดียวที่หน้าตัดระยะ d จากผิวเสา (ทิศทาง#1 เท่านั้น ตรงกับไฟล์อ้างอิงทุกไฟล์ —
    ดูหมายเหตุขอบเขตด้านบนของไฟล์). ตรวจเฉพาะกรณีหน้าตัดวิกฤตยังไม่พ้นตำแหน่งเสาเข็มริม
    (ตรงกับเงื่อนไข IF(ZL22<ZL11,...,"-") ของไฟล์อ้างอิง)."""
    critical_section_cm = d1_cm + column_b_cm / 2.0
    applicable = critical_section_cm < c_dist_cm
    if not applicable:
        return OneWayShearCheckPC(applicable=False, vu_kg=0.0, vc_kg=0.0, phi_vc_kg=0.0, shear_ok=True)

    vu = n_outer * pile_load_kg
    vc = 0.53 * math.sqrt(fc_ksc) * B_cm * d1_cm
    phi_vc = PHI_V * vc
    return OneWayShearCheckPC(applicable=True, vu_kg=vu, vc_kg=vc, phi_vc_kg=phi_vc, shear_ok=(vu <= phi_vc))


def _column_punching_shear_pc(column_b_cm: float, column_h_cm: float, d1_cm: float,
                               B_cm: float, n_piles_column_punch: int, pile_load_kg: float,
                               fc_ksc: float) -> ColumnPunchingShearCheckPC:
    """แรงเฉือนทะลุที่ผิวเสา — เส้นรอบรูปวิกฤตมาตรฐาน 4 ด้าน เหมือนโมดูล 5.1 แต่มีสูตรสำรอง
    (fallback) กรณีเส้นรอบรูปมาตรฐานกว้างเกินตัวฐานรากเอง (พบเฉพาะฐานเสาเข็มที่ B แคบ เช่น
    2/3 ต้น) ตรงกับไฟล์อ้างอิง cell ALX34: IF(b1+d < B, เส้นรอบรูปมาตรฐาน, B×2)."""
    bo_standard = 2.0 * (column_b_cm + d1_cm) + 2.0 * (column_h_cm + d1_cm)
    fallback = (column_h_cm + d1_cm) >= B_cm
    bo = (B_cm * 2.0) if fallback else bo_standard

    beta_c = max(column_b_cm, column_h_cm) / min(column_b_cm, column_h_cm) if min(column_b_cm, column_h_cm) > 0 else 1.0
    vu = n_piles_column_punch * pile_load_kg

    vc1 = PUNCHING_COEFF_1 * (2.0 + 4.0 / beta_c) * math.sqrt(fc_ksc) * bo * d1_cm
    vc2 = PUNCHING_COEFF_2 * math.sqrt(fc_ksc) * bo * d1_cm
    vc = min(vc1, vc2)
    phi_vc = PHI_V * vc

    return ColumnPunchingShearCheckPC(
        bo_cm=bo, fallback_perimeter_used=fallback, beta_c=beta_c, vu_kg=vu,
        vc1_kg=vc1, vc2_kg=vc2, vc_kg=vc, phi_vc_kg=phi_vc, shear_ok=(vu <= phi_vc),
    )


def _pile_punching_shear(pile_size_cm: float, d1_cm: float, pile_load_kg: float,
                          fc_ksc: float, pile_shape: str = DEFAULT_PILE_SHAPE) -> PilePunchingShearCheck:
    """แรงเฉือนทะลุ (punching) รอบเสาเข็มเดี่ยว — เส้นรอบรูปวิกฤตขึ้นกับรูปทรงเสาเข็ม (pile_shape,
    เพิ่มตามคำขอผู้ใช้ 2026-07-11 — ก่อนหน้านี้ hardcode สูตรสี่เหลี่ยมเสมอ):
      - รูปทรง "กลุ่มสี่เหลี่ยม" (square, square_hollow) ใช้เส้นรอบรูปสี่เหลี่ยมจัตุรัสสมมูล
        4×(ขนาดเสาเข็ม+d) — ตรงกับไฟล์อ้างอิง cell ANP ของแถวตารางที่ใช้จริงในทั้ง 3 ตัวอย่าง
        (เสาเข็มคอนกรีตอัดแรงหน้าตัดสี่เหลี่ยมจัตุรัส เช่น "22x22", "18x18")
      - รูปทรงอื่น (round, round_hollow, hex_hollow, i_beam) ใช้เส้นรอบรูปวงกลมจริง
        π×(ขนาดเสาเข็ม+d) — สูตรที่แม่นยำสำหรับเสาเข็มกลมโดยตรง และเป็นค่าประมาณฝั่งปลอดภัย
        (conservative, bo/Vc ต่ำกว่าสูตรสี่เหลี่ยมเสมอเพราะ π<4) สำหรับรูปทรงที่ไม่มีสูตร
        มาตรฐานเฉพาะ (ดู PILE_SHAPES/PILE_SHAPE_SQUARE_FAMILY ด้านบนของไฟล์) ดู ALX44:
        fvVc = φv×1.06×√f'c×bo×d — สูตรเดียว ไม่ใช้ min ของ 2 สูตรเหมือนแรงเฉือนทะลุที่ผิวเสา —
        ตรวจครั้งเดียวแทนเสาเข็มทุกต้น (เพราะทุกต้นรับแรงปฏิกิริยาเท่ากันโดยสมมาตร)."""
    if pile_shape in PILE_SHAPE_SQUARE_FAMILY:
        bo_pile = 4.0 * (pile_size_cm + d1_cm)
    else:
        bo_pile = math.pi * (pile_size_cm + d1_cm)
    vc = PUNCHING_COEFF_2 * math.sqrt(fc_ksc) * bo_pile * d1_cm
    phi_vc = PHI_V * vc
    return PilePunchingShearCheck(bo_pile_cm=bo_pile, vu_kg=pile_load_kg, vc_kg=vc,
                                   phi_vc_kg=phi_vc, shear_ok=(pile_load_kg <= phi_vc))


def _flexure_pc(direction: str, full_design: bool, mu_kgm: float, d_cm: float, width_cm: float,
                 fc_ksc: float, fy_ksc: float, rho_min: float, rho_max: float,
                 bar_area: float) -> PileCapFlexure:
    """ออกแบบเหล็กเสริม — ต่างจากโมดูล 5.1 ตรงที่ Mu ที่นี่เป็นโมเมนต์รวมจริงของทั้งหน้าตัดกว้าง
    width_cm อยู่แล้ว (มาจากแรงเสาเข็มที่เป็นจุด ไม่ใช่หน่วยแรงแบกทานที่กระจายสม่ำเสมอแบบฐานรากแผ่)
    จึงไม่ต้องคูณ/หารด้วยความกว้างซ้ำแบบโมดูล 5.1 (ตรงกับไฟล์อ้างอิง cell ALX45/ALX47 ที่ใช้
    Mu รวมและ width รวมตรงๆ ในสูตรเดียวกัน)."""
    if not full_design:
        rho_used = rho_min
        as_req = rho_used * width_cm * d_cm
        n_bars_req = max(1, math.ceil(as_req / bar_area))
        n_bars_use = n_bars_req
        as_provided = n_bars_use * bar_area
        return PileCapFlexure(
            direction=direction, full_design=False, arm_cm=0.0, mu_kgm=0.0, d_cm=d_cm,
            width_cm=width_cm, ru_ksc=0.0, rreq=0.0, rho_min=rho_min, rho_used=rho_used,
            over_reinforced=False, as_req_cm2=as_req, n_bars_req=n_bars_req, n_bars_use=n_bars_use,
            as_provided_cm2=as_provided, reinf_ok=(as_provided >= as_req),
        )

    ru = (mu_kgm * 100.0) / (PHI_B * width_cm * d_cm ** 2) if d_cm > 0 and width_cm > 0 else 999.0
    under_sqrt = 1.0 - (2.0 * ru) / (0.85 * fc_ksc)
    over_reinforced = under_sqrt < 0
    if over_reinforced:
        rreq = rho_max
    else:
        rreq = 0.85 * (fc_ksc / fy_ksc) * (1.0 - math.sqrt(under_sqrt))

    rho_used = max(rreq, rho_min)
    over_reinforced = over_reinforced or (rho_used > rho_max)
    as_req = rho_used * width_cm * d_cm

    n_bars_req = max(1, math.ceil(as_req / bar_area))
    n_bars_use = n_bars_req
    as_provided = n_bars_use * bar_area
    reinf_ok = (as_provided >= as_req) and (not over_reinforced)

    return PileCapFlexure(
        direction=direction, full_design=True, arm_cm=0.0, mu_kgm=mu_kgm, d_cm=d_cm, width_cm=width_cm,
        ru_ksc=ru, rreq=rreq, rho_min=rho_min, rho_used=rho_used, over_reinforced=over_reinforced,
        as_req_cm2=as_req, n_bars_req=n_bars_req, n_bars_use=n_bars_use, as_provided_cm2=as_provided,
        reinf_ok=reinf_ok,
    )


def _dowel_check_pc(fc_ksc: float, fy_ksc: float, bar_area: float, A_cm: float,
                     cover_cm: float, column_b_cm: float) -> DowelCheckPC:
    """ตรงกับโมดูล 5.1 (_dowel_check) — ใช้ระยะฝังที่มีจริง = A (ด้านยาวตามแนวเรียงเสาเข็ม
    ซึ่ง >= B เสมอโดยโครงสร้าง) - cover - a1/2 ตรงกับไฟล์อ้างอิง cell ALX49
    (MAX(ZL9:ZM10)*100 = A เสมอในทางปฏิบัติ)."""
    lbd = max(0.06 * bar_area * fy_ksc / math.sqrt(fc_ksc), DOWEL_LBD_MIN_CM)
    ld_avail = A_cm - cover_cm - (column_b_cm / 2.0)
    return DowelCheckPC(lbd_cm=lbd, ld_avail_cm=ld_avail, dowel_ok=(ld_avail >= lbd))


def calculate(inp: PileCapInput) -> PileCapResult:
    fy = GS_STEEL_FY_KSC[inp.main_steel_type]
    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    rho_min = compute_rho_min(fy)
    beta1 = compute_beta1(inp.fc_ksc)
    rho_b = compute_rho_b(inp.fc_ksc, fy, beta1)
    rho_max = compute_rho_max(rho_b)
    bar_area = bar_area_cm2(inp.main_bar_dia_mm)
    bar_dia_cm = inp.main_bar_dia_mm / 10.0

    geometry = _pile_geometry(inp.n_piles, inp.column_b_cm, inp.column_h_cm, inp.pile_size_cm)
    A_m = geometry.A_cm / 100.0
    B_m = geometry.B_cm / 100.0
    area_m2 = A_m * B_m

    chosen = None
    thickness_search_exhausted = True
    for t_cm in FOOTING_THICKNESS_CM_OPTIONS:
        d1 = t_cm - inp.cover_cm - bar_dia_cm / 2.0
        d2 = d1 - bar_dia_cm
        if d1 <= 0 or d2 <= 0:
            continue

        ws = max(0.0, area_m2 * (inp.footing_invert_depth_m - t_cm / 100.0) * inp.soil_unit_weight_ton_m3 * 1000.0)
        wf = area_m2 * (t_cm / 100.0) * CONCRETE_UNIT_WEIGHT_KG_M3
        wu = 1.4 * (ws + wf + inp.pd_kg) + 1.7 * inp.pl_kg
        pile_load_factored = wu / inp.n_piles

        beam_shear = _one_way_shear_pc(d1, geometry.B_cm, inp.column_b_cm, geometry.c_dist_cm,
                                        geometry.n_outer_piles, pile_load_factored, inp.fc_ksc)
        column_punching = _column_punching_shear_pc(inp.column_b_cm, inp.column_h_cm, d1, geometry.B_cm,
                                                      geometry.n_piles_column_punch, pile_load_factored, inp.fc_ksc)
        pile_punching = _pile_punching_shear(inp.pile_size_cm, d1, pile_load_factored, inp.fc_ksc, inp.pile_shape)

        if beam_shear.shear_ok and column_punching.shear_ok and pile_punching.shear_ok:
            chosen = (t_cm, d1, d2, ws, wf, wu, pile_load_factored, beam_shear, column_punching, pile_punching)
            thickness_search_exhausted = False
            break

    if chosen is None:
        t_cm = FOOTING_THICKNESS_CM_OPTIONS[-1]
        d1 = max(t_cm - inp.cover_cm - bar_dia_cm / 2.0, 1.0)
        d2 = max(d1 - bar_dia_cm, 1.0)
        ws = max(0.0, area_m2 * (inp.footing_invert_depth_m - t_cm / 100.0) * inp.soil_unit_weight_ton_m3 * 1000.0)
        wf = area_m2 * (t_cm / 100.0) * CONCRETE_UNIT_WEIGHT_KG_M3
        wu = 1.4 * (ws + wf + inp.pd_kg) + 1.7 * inp.pl_kg
        pile_load_factored = wu / inp.n_piles
        beam_shear = _one_way_shear_pc(d1, geometry.B_cm, inp.column_b_cm, geometry.c_dist_cm,
                                        geometry.n_outer_piles, pile_load_factored, inp.fc_ksc)
        column_punching = _column_punching_shear_pc(inp.column_b_cm, inp.column_h_cm, d1, geometry.B_cm,
                                                      geometry.n_piles_column_punch, pile_load_factored, inp.fc_ksc)
        pile_punching = _pile_punching_shear(inp.pile_size_cm, d1, pile_load_factored, inp.fc_ksc, inp.pile_shape)
    else:
        t_cm, d1, d2, ws, wf, wu, pile_load_factored, beam_shear, column_punching, pile_punching = chosen

    pnet_service = ws + wf + inp.pd_kg + inp.pl_kg
    service_load_per_pile_ton = (pnet_service / inp.n_piles) / 1000.0
    pile_load_service = PileLoadServiceCheck(
        service_load_per_pile_ton=service_load_per_pile_ton, safe_load_ton=inp.pile_safe_load_ton,
        capacity_ok=(inp.pile_safe_load_ton >= service_load_per_pile_ton),
    )

    # --- ทิศทาง#1 (ตามแนวเรียงเสาเข็ม, ออกแบบจริงเสมอ) ---
    x1_arm_cm = geometry.c_dist_cm - inp.column_b_cm / 2.0
    mu1 = geometry.n_outer_piles * pile_load_factored * (x1_arm_cm / 100.0)
    flex_1 = _flexure_pc("1", True, mu1, d1, geometry.B_cm, inp.fc_ksc, fy, rho_min, rho_max, bar_area)
    flex_1.arm_cm = x1_arm_cm

    # --- ทิศทาง#2 (ตั้งฉาก, ออกแบบจริงเฉพาะ 4 ต้น มิฉะนั้นใส่เหล็กขั้นต่ำ) ---
    full_design_2 = (inp.n_piles == 4)
    if full_design_2:
        x2_arm_cm = geometry.c_dist_cm - inp.column_h_cm / 2.0
        mu2 = geometry.n_outer_piles * pile_load_factored * (x2_arm_cm / 100.0)
        flex_2 = _flexure_pc("2", True, mu2, d2, geometry.A_cm, inp.fc_ksc, fy, rho_min, rho_max, bar_area)
        flex_2.arm_cm = x2_arm_cm
    else:
        flex_2 = _flexure_pc("2", False, 0.0, d2, geometry.A_cm, inp.fc_ksc, fy, rho_min, rho_max, bar_area)

    reinf_label_1 = f"{flex_1.n_bars_use}-{main_bar_type}{inp.main_bar_dia_mm:.0f}"
    reinf_label_2 = f"{flex_2.n_bars_use}-{main_bar_type}{inp.main_bar_dia_mm:.0f}"

    dowel = _dowel_check_pc(inp.fc_ksc, fy, bar_area, geometry.A_cm, inp.cover_cm, inp.column_b_cm)

    warnings = []
    if thickness_search_exhausted:
        warnings.append("⚠️ ไม่พบความหนาที่ผ่านแรงเฉือนทุกกรณีภายในช่วงที่ลอง (สูงสุด "
                         f"{FOOTING_THICKNESS_CM_OPTIONS[-1]:.0f} ซม.) กรุณาเพิ่มจำนวน/ขนาดเสาเข็ม หรือเพิ่ม f'c")
    if beam_shear.applicable and not beam_shear.shear_ok:
        warnings.append("⚠️ แรงเฉือนทางเดียว (beam shear) ไม่ผ่าน")
    if not column_punching.shear_ok:
        warnings.append("⚠️ แรงเฉือนทะลุที่ผิวเสา (column punching shear) ไม่ผ่าน")
    if not pile_punching.shear_ok:
        warnings.append("⚠️ แรงเฉือนทะลุรอบเสาเข็ม (pile punching shear) ไม่ผ่าน")
    if not flex_1.reinf_ok:
        warnings.append("⚠️ เหล็กเสริมทิศทาง#1 ไม่เพียงพอ")
    if not flex_2.reinf_ok:
        warnings.append("⚠️ เหล็กเสริมทิศทาง#2 ไม่เพียงพอ")
    if not dowel.dowel_ok:
        warnings.append("⚠️ ความยาวฝังเหล็กทาบ/เหล็กหนวดกุ้ง (dowel) ไม่เพียงพอ — กรุณาขยายขนาดฐานราก")
    if not pile_load_service.capacity_ok:
        warnings.append("⚠️ น้ำหนักบรรทุกต่อต้นเกินกำลังรับน้ำหนักปลอดภัยที่กรอกไว้ — กรุณาเพิ่มจำนวน/ขนาดเสาเข็ม")

    design_ok = (
        (not beam_shear.applicable or beam_shear.shear_ok) and column_punching.shear_ok and pile_punching.shear_ok
        and flex_1.reinf_ok and flex_2.reinf_ok and dowel.dowel_ok and pile_load_service.capacity_ok
        and not thickness_search_exhausted
    )
    design_fail_reason = " ".join(warnings)

    return PileCapResult(
        geometry=geometry, ws_kg=ws, wf_kg=wf, pnet_service_kg=pnet_service,
        pile_load_service=pile_load_service, wu_kg=wu, pile_load_factored_kg=pile_load_factored,
        t_cm=t_cm, d1_cm=d1, d2_cm=d2, beam_shear=beam_shear, column_punching=column_punching,
        pile_punching=pile_punching, flex_1=flex_1, flex_2=flex_2, dowel=dowel,
        main_bar_type=main_bar_type, reinf_label_1=reinf_label_1, reinf_label_2=reinf_label_2,
        design_ok=design_ok, design_fail_reason=design_fail_reason,
        thickness_search_exhausted=thickness_search_exhausted,
    )
