"""
common/torsion.py — การออกแบบรับแรงบิด (Torsion) ตามตำรา "การออกแบบคอนกรีตเสริมเหล็ก วิธีกำลัง (SDM)"
========================================================================================================
โดย ผศ.ดร.มงคล จิรวัชรเดช (มทส.) บทที่ 9 การบิด — อ้างอิง ACI 318-95 วิธีโครงถักสามมิติ (Space Truss)
หน่วย metric: kgf, cm, ksc (kg/cm²). ผู้ใช้กรอกแรงบิดประลัย Tu เอง (kg·m).

**φ (ตัวคูณลดกำลังสำหรับการบิด) = 0.85** ตามตำรา (สมการ 9.6/9.19) — ตรงกับ φ ของแรงเฉือนในโปรแกรม

สมการหลัก (อ้างอิงเลขสมการในตำรา):
  Acp = b·h , pcp = 2(b+h)                                          พื้นที่/เส้นรอบรูปหน้าตัดรวม
  Tcr = 1.1·√f'c·(Acp²/pcp)                        [9.5]  โมเมนต์บิดแตกร้าว (kg·cm)
  ไม่ต้องคิดแรงบิด ถ้า Tu ≤ φ·Tcr/4 = 0.275·φ·√f'c·(Acp²/pcp)   [9.6/9.20]
  Aoh = x₀·y₀ = (b−2c₁)(h−2c₁) , ph = 2(x₀+y₀) , Ao = 0.85·Aoh   [9.10/9.11]  c₁ = cover + d_stirrup/2
  ตรวจความพอเพียงหน้าตัด (หน้าตัดตัน):                            [9.17]
     √[(Vu/bwd)² + (Tu·ph/1.7Aoh²)²] ≤ φ·(Vc/bwd + 2.1√f'c)      ; Vc = 0.53√f'c·bw·d
  เหล็กปลอกรับบิด (θ=45°):  At/s = Tu/(2·φ·fyv·Ao)               [9.22]  (ต่อหนึ่งขา)
  เหล็กปลอกรับเฉือน:        Av/s = (Vu − φVc)/(φ·fyv·d)          [9.18]  (สองขา)
  เหล็กปลอกรวม:            (Av+2At)/s = Av/s + 2·(At/s)          [9.23]
  เหล็กปลอกขั้นต่ำ:         (Av+2At)/s ≥ 3.5·bw/fyv               [9.24]
  ระยะเรียงสูงสุด:          s_max = min(ph/8, 30 cm)
  เหล็กนอนรับบิด:          Al = (At/s)·ph·(fyv/fyl)               [9.25]
  เหล็กนอนขั้นต่ำ:         Al,min = 1.3√f'c·Acp/fyl − (At/s)·ph·(fyv/fyl)   [9.26]
                          โดยใช้ At/s ≥ 1.75·bw/fyv ในพจน์แรก

หมายเหตุสำคัญ: ระยะเรียงเหล็กปลอก **เป็นผลลัพธ์การออกแบบ** (โปรแกรมคำนวณให้) ไม่ใช่ค่าที่ผู้ใช้กรอกมา
เช็ค — ตรงตามตัวอย่างที่ 9.2 ในตำรา (คำนวณได้ DB12@18cm). การออกแบบ "ผ่าน" เมื่อหน้าตัดเพียงพอ
(สมการ 9.17) และมีระยะเรียงที่ก่อสร้างได้จริง
"""

import math
from dataclasses import dataclass

from modules.slab_on_ground import bar_area_cm2

PHI_TORSION = 0.85
MIN_PRACTICAL_SPACING_CM = 5.0   # ระยะเรียงเหล็กปลอกต่ำสุดที่ก่อสร้างได้จริง


@dataclass
class TorsionDesign:
    tu_kgm: float
    tu_kgcm: float
    acp_cm2: float
    pcp_cm: float
    tcr_kgcm: float
    tth_kgcm: float             # เกณฑ์ = φ·Tcr/4
    tth_kgm: float
    required: bool
    aoh_cm2: float
    ph_cm: float
    ao_cm2: float
    lhs_ksc: float              # หน่วยแรงร่วม (ซ้ายของสมการ 9.17)
    rhs_ksc: float              # φ(Vc/bwd + 2.1√f'c)
    section_ok: bool
    at_s: float                 # At/s ต่อขา (cm²/cm)
    av_s_shear: float           # Av/s จากแรงเฉือน (สองขา, cm²/cm)
    av2at_s_req: float          # (Av+2At)/s ที่ต้องการ (รวมขั้นต่ำแล้ว)
    av2at_s_min: float          # 3.5·bw/fyv
    s_max_cm: float             # min(ph/8, 30)
    stirrup_dia_mm: float
    stirrup_legs: int
    stirrup_area_2legs_cm2: float
    s_required_cm: float        # ระยะเรียงที่ต้องใช้ (ผลลัพธ์การออกแบบ)
    stirrup_ok: bool            # ออกแบบได้สำเร็จ (หน้าตัดพอ + ระยะก่อสร้างได้)
    al_cm2: float               # เหล็กนอนรับบิด
    al_min_cm2: float
    al_design_cm2: float
    al_per_face_cm2: float      # แบ่งรอบเส้นรอบรูป (÷4)


def design_beam_torsion(tu_kgm, vu_kg, b_cm, h_cm, d_cm, fc_ksc, fyv_ksc, fyl_ksc,
                        cover_cm, stirrup_dia_mm, stirrup_legs, vc_kg, av_shear_cm2=None,
                        stirrup_spacing_use_cm=None):
    """ออกแบบเหล็กรับแรงบิดของคานตามตำรา DRMK (ACI 318-95) — คืน TorsionDesign

    ระยะเรียงเหล็กปลอกเป็น "ผลลัพธ์การออกแบบ" (s_required_cm) โปรแกรมคำนวณให้เอง
    av_shear_cm2 / stirrup_spacing_use_cm รับไว้เพื่อความเข้ากันได้กับผู้เรียกเดิม (ไม่ได้ใช้)
    """
    phi = PHI_TORSION
    tu_kgcm = tu_kgm * 100.0
    sqrt_fc = math.sqrt(fc_ksc)

    acp = b_cm * h_cm
    pcp = 2.0 * (b_cm + h_cm)
    tcr = 1.1 * sqrt_fc * (acp ** 2) / pcp          # [9.5]
    tth = phi * tcr / 4.0                             # [9.6]
    required = tu_kgcm > tth

    c1 = cover_cm + stirrup_dia_mm / 10.0 / 2.0
    x0 = max(b_cm - 2.0 * c1, 1.0)
    y0 = max(h_cm - 2.0 * c1, 1.0)
    aoh = x0 * y0
    ph = 2.0 * (x0 + y0)
    ao = 0.85 * aoh                                   # [9.11]

    # ความพอเพียงหน้าตัด (สมการ 9.17)
    lhs = math.sqrt((vu_kg / (b_cm * d_cm)) ** 2 + (tu_kgcm * ph / (1.7 * aoh ** 2)) ** 2)
    rhs = phi * (vc_kg / (b_cm * d_cm) + 2.1 * sqrt_fc)
    section_ok = lhs <= rhs

    # เหล็กปลอกรับบิด (9.22) + รับเฉือน (9.18) + รวม (9.23)
    at_s = tu_kgcm / (2.0 * phi * fyv_ksc * ao) if required else 0.0        # ต่อขา
    vs_shear = max(0.0, vu_kg / phi - vc_kg)
    av_s_shear = vs_shear / (fyv_ksc * d_cm)                                 # สองขา
    av2at_s = av_s_shear + 2.0 * at_s
    av2at_s_min = 3.5 * b_cm / fyv_ksc                                       # [9.24]
    av2at_s_req = max(av2at_s, av2at_s_min)

    s_max = min(ph / 8.0, 30.0)
    stirrup_area_2legs = stirrup_legs * bar_area_cm2(stirrup_dia_mm)
    s_from_ratio = stirrup_area_2legs / av2at_s_req if av2at_s_req > 0 else 999.0
    s_required = min(s_from_ratio, s_max)
    stirrup_ok = required and section_ok and (s_required >= MIN_PRACTICAL_SPACING_CM)

    # เหล็กนอนรับบิด (9.25) + ขั้นต่ำ (9.26)
    al = at_s * ph * (fyv_ksc / fyl_ksc) if required else 0.0
    at_s_for_min = max(at_s, 1.75 * b_cm / fyv_ksc)
    al_min = (1.3 * sqrt_fc * acp / fyl_ksc) - at_s_for_min * ph * (fyv_ksc / fyl_ksc) if required else 0.0
    al_min = max(al_min, 0.0)
    al_design = max(al, al_min)
    al_per_face = al_design / 4.0

    return TorsionDesign(
        tu_kgm=tu_kgm, tu_kgcm=tu_kgcm, acp_cm2=acp, pcp_cm=pcp,
        tcr_kgcm=tcr, tth_kgcm=tth, tth_kgm=tth / 100.0, required=required,
        aoh_cm2=aoh, ph_cm=ph, ao_cm2=ao,
        lhs_ksc=lhs, rhs_ksc=rhs, section_ok=section_ok,
        at_s=at_s, av_s_shear=av_s_shear, av2at_s_req=av2at_s_req, av2at_s_min=av2at_s_min,
        s_max_cm=s_max, stirrup_dia_mm=stirrup_dia_mm, stirrup_legs=stirrup_legs,
        stirrup_area_2legs_cm2=stirrup_area_2legs, s_required_cm=s_required, stirrup_ok=stirrup_ok,
        al_cm2=al, al_min_cm2=al_min, al_design_cm2=al_design, al_per_face_cm2=al_per_face,
    )


def build_torsion_section(tor, stirrup_bar_type="RB"):
    """สร้าง section 'การออกแบบรับแรงบิด' สำหรับแผ่นคำนวณ (render_calc_sheet) — ใช้ร่วมทุกโมดูลคาน"""
    steps = [
        {"desc": "โมเมนต์บิดแตกร้าว (Cracking torque) และเกณฑ์พิจารณา",
         "formula": (f"T<sub>cr</sub> = 1.1√f'<sub>c</sub>·(A<sub>cp</sub>²/p<sub>cp</sub>) "
                     f"(A<sub>cp</sub> = {tor.acp_cm2:,.0f} cm², p<sub>cp</sub> = {tor.pcp_cm:.0f} cm)"),
         "result": f"T<sub>cr</sub> = {tor.tcr_kgcm/100:,.0f} kg·m → เกณฑ์ φT<sub>cr</sub>/4 = {tor.tth_kgm:,.0f} kg·m"},
        {"desc": "ตรวจว่าต้องออกแบบรับแรงบิดหรือไม่",
         "formula": f"T<sub>u</sub> = {tor.tu_kgm:,.0f} kg·m {'>' if tor.required else '≤'} เกณฑ์ {tor.tth_kgm:,.0f} kg·m",
         "result": "ต้องออกแบบรับแรงบิด" if tor.required else "ไม่ต้องออกแบบ (แรงบิดต่ำกว่าเกณฑ์) ✓"},
    ]
    if not tor.required:
        return {"title": "การออกแบบรับแรงบิด (Torsion — ตำรา SDM/ACI 318)", "steps": steps}
    stir_label = f"{tor.stirrup_legs}-{stirrup_bar_type}{tor.stirrup_dia_mm:.0f}@{tor.s_required_cm:.0f}cm"
    steps += [
        {"desc": "หน้าตัดกลวงเทียบเท่า (Space truss / ท่อผนังบาง)",
         "formula": "A<sub>oh</sub> = x₀·y₀ , p<sub>h</sub> = 2(x₀+y₀) , A<sub>o</sub> = 0.85A<sub>oh</sub>",
         "result": f"A<sub>oh</sub> = {tor.aoh_cm2:,.0f} cm² , p<sub>h</sub> = {tor.ph_cm:.0f} cm , A<sub>o</sub> = {tor.ao_cm2:,.0f} cm²"},
        {"desc": "ตรวจความพอเพียงของหน้าตัด (เฉือน+บิดร่วมกัน, สมการ 9.17)",
         "formula": "√[(V<sub>u</sub>/b<sub>w</sub>d)² + (T<sub>u</sub>p<sub>h</sub>/1.7A<sub>oh</sub>²)²] ≤ φ(V<sub>c</sub>/b<sub>w</sub>d + 2.1√f'<sub>c</sub>)",
         "sub": f"{tor.lhs_ksc:.3f} ≤ {tor.rhs_ksc:.3f} ksc",
         "result": "หน้าตัดเพียงพอ ✓" if tor.section_ok else "หน้าตัดเล็กเกินไป — ต้องขยายคาน ✗"},
        {"desc": "เหล็กปลอกรับแรงบิด A<sub>t</sub>/s (ต่อขา) และรับแรงเฉือน A<sub>v</sub>/s",
         "formula": (f"A<sub>t</sub>/s = T<sub>u</sub>/(2φf<sub>yv</sub>A<sub>o</sub>) = {tor.at_s:.4f} , "
                     f"A<sub>v</sub>/s = (V<sub>u</sub>−φV<sub>c</sub>)/(φf<sub>yv</sub>d) = {tor.av_s_shear:.4f}"),
         "result": f"(A<sub>v</sub>+2A<sub>t</sub>)/s = {tor.av2at_s_req:.4f} cm²/cm (≥ ขั้นต่ำ 3.5b/f<sub>yv</sub> = {tor.av2at_s_min:.4f})"},
        {"desc": "ระยะเรียงเหล็กปลอกที่ต้องใช้ (ผลลัพธ์การออกแบบ)",
         "formula": (f"s = A<sub>ปลอก 2 ขา</sub>/[(A<sub>v</sub>+2A<sub>t</sub>)/s] , "
                     f"s<sub>max</sub> = min(p<sub>h</sub>/8, 30) = {tor.s_max_cm:.1f} cm"),
         "result": f"ใช้เหล็กปลอกปิด {stir_label} → " + ("ผ่าน ✓" if tor.stirrup_ok else "ระยะแคบเกินไป — ควรเพิ่มขนาดเหล็กปลอก/ขยายคาน ✗")},
        {"desc": "เหล็กนอนรับแรงบิด A<sub>l</sub> (กระจายรอบเส้นรอบรูป)",
         "formula": (f"A<sub>l</sub> = (A<sub>t</sub>/s)·p<sub>h</sub>·(f<sub>yv</sub>/f<sub>yl</sub>) = {tor.al_cm2:.2f} cm² , "
                     f"A<sub>l,min</sub> = 1.3√f'<sub>c</sub>·A<sub>cp</sub>/f<sub>yl</sub> − ... = {tor.al_min_cm2:.2f} cm²"),
         "result": f"ใช้ A<sub>l</sub> = {tor.al_design_cm2:.2f} cm² (แบ่ง ≈ {tor.al_per_face_cm2:.2f} cm² ต่อด้าน เพิ่มเข้าเหล็กเดิม บน/ล่าง/ข้าง)"},
    ]
    return {"title": "การออกแบบรับแรงบิด (Torsion — ตำรา SDM/ACI 318, φ=0.85)", "steps": steps}
