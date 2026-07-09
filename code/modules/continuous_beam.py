"""
Module 3.2 — คานต่อเนื่อง (Continuous Beam)

Scope: คานต่อเนื่องหลายช่วง (2-10 ช่วง) รองรับปลายยื่น (overhang) ซ้าย/ขวาได้ ตามที่ผู้ใช้
ยืนยันขอบเขต (AskUserQuestion): (1) รวม overhang ไว้ในเวอร์ชันแรกเลย (2) จุดแรงกระทำสูงสุด
5 จุด/ช่วง (มากกว่าไฟล์ต้นฉบับ) (3) จำนวนช่วงคานสูงสุด 10 ช่วง (จำกัดน้อยกว่าไฟล์ต้นฉบับซึ่ง
รองรับถึง 20 ช่วง)

อ้างอิง/ที่มา: "SDM Plus_Beam_Analysis.xlsx" (โฟลเดอร์ SDM+beta) — วิเคราะห์โครงสร้างด้วยวิธี
Three Moment Equation (Clapeyron's Theorem) ยืนยันจากชีท Input Data cell ABN14 ที่มี label
สูตรตรงๆ ว่า "MA*L1+2MB(L1+L2)+MC*L2 = -L0-R0" และคอลัมน์สัมประสิทธิ์/RHS (AAW/ABA/ABE,
ABJ/ABN) ที่ยืนยันรูปแบบเทอม w*L^3/4 (UDL) และ P*b*(L^2-b^2)/L (point load) — ไฟล์แก้ระบบ
สมการด้วย MINVERSE/MMULT ในตัวเอง (โมดูลนี้ reimplement ด้วย numpy.linalg.solve) ไม่มีการ
อ้างอิงถึง E, I ที่ไหนเลยในไฟล์ต้นฉบับ = สมมติ EI คงที่ตลอดคาน (ใช้ b x h ค่าเดียวทั้งคาน
รวม overhang ด้วย) — สอดคล้องกับสมมติฐานมาตรฐานของ Three Moment Equation แบบไม่คิด
differential settlement/EI变.

สูตร Three Moment Equation (สำหรับช่วง i ยาว L_i รับ UDL w_i และจุดแรง P ที่ระยะ a จาก
ปลายซ้าย/ b จากปลายขวา ของช่วงนั้น):
    M_(i-1)*L_i + 2*M_i*(L_i+L_(i+1)) + M_(i+1)*L_(i+1) = -(6*A_i*abar_i/L_i + 6*A_(i+1)*bbar_(i+1)/L_(i+1))
    เทอม UDL (ทั้งสองด้าน สมมาตร): w*L^3/4
    เทอมจุดแรง (วัดจากซ้าย): P*a*(L^2-a^2)/L
    เทอมจุดแรง (วัดจากขวา):  P*b*(L^2-b^2)/L

ปลายยื่น (overhang) ถือเป็น "known boundary moment" ที่ปลายคาน (ไม่ใช่ unknown เพิ่มใน
ระบบสมการ) — โมเมนต์ที่ฐานรองรับของปลายยื่น = -(w*L0^2/2 + sum(P*d)) (d = ระยะจากจุดรองรับ
ถึงแรงจุดบนปลายยื่น) แทนค่าเป็นค่าที่ทราบแล้วในสมการ Three Moment Equation ตัวแรก/ตัวสุดท้าย
ของระบบ

หลังแก้ระบบสมการได้ M ที่จุดรองรับภายในทุกจุดแล้ว, ปฏิกิริยาที่แท้จริงของแต่ละช่วงคำนวณจาก:
    R_left_actual  = R0_left  + (M_right - M_left)/L
    R_right_actual = R0_right + (M_left  - M_right)/L
(R0 = ปฏิกิริยาแบบ simple-span/determinate ของช่วงนั้น, M_left/M_right = โมเมนต์จริงที่จุด
รองรับซ้าย/ขวาของช่วงนั้น ซึ่งอาจเป็นลบ (hogging) ได้) — สูตรนี้ยืนยันตรงกับรูปแบบสูตรใน
ไฟล์ต้นฉบับ (cell AEI12 มีรูปแบบ (...-M_left+M_right)/L)

ยืนยันความถูกต้องของ engine นี้ด้วยการเทียบกับผลลัพธ์ปิดรูป (closed-form) จากตำรามาตรฐาน
สำหรับคานต่อเนื่อง 2 ช่วงเท่ากันรับ UDL สม่ำเสมอ: M ที่จุดรองรับกลาง = -wL^2/8, โมเมนต์บวก
กลางช่วง = 9wL^2/128 ที่ x=0.375L — ทั้งสองค่าตรงกับผลจาก engine นี้ (ตรวจสอบใน test สคริปต์
แยกก่อน integrate เข้าโมดูลนี้)

หน่วยแรง/โมเมนต์: kg, kg-m ตลอดทั้งไฟล์ (สอดคล้องกับโมดูล 3.1)
น้ำหนักบรรทุก: Wu = 1.4(DL_line+DL_selfweight) + 1.7(LL_line) ตามกฎกระทรวง พ.ศ. 2566
(เหมือนโมดูล 3.1) น้ำหนักหน้าตัดคาน (self-weight) คำนวณจาก b_cm, h_cm ค่าเดียวใช้ตลอดทั้งคาน
(รวมช่วงยื่นด้วย) ตามสมมติฐาน "หน้าตัดเดียวกันทั้งคาน" ของ Three Moment Equation

การออกแบบเหล็กเสริม/เหล็กปลอก ใช้สูตรเดียวกับโมดูล 3.1 ทุกประการ (_flexure_design,
_stirrup_design, _max_bars_single_layer — import มาใช้ซ้ำโดยตรง ไม่ copy-paste สูตร) เพื่อกัน
บั๊กจากการพิมพ์สูตรซ้ำ:
  - เหล็กล่าง (บวก): ออกแบบจาก Mu บวกสูงสุดในแต่ละช่วง (mu_pos_max_kgm)
  - เหล็กบน (ลบ): ออกแบบจาก |M| ที่จุดรองรับแต่ละจุด (is_nominal_only=True ถ้า M≈0 คือ
    จุดรองรับริมที่ไม่มี overhang — เหมือน logic เหล็กบนของโมดูล 3.1)
  - เหล็กปลอก: ตรวจสอบทีละช่วง/ปลายยื่น จาก Vu governing ของตำแหน่งนั้น ใช้ระยะห่างที่ผู้ใช้
    เลือกค่าเดียวทั้งคาน (global spacing) ตามที่ผู้ใช้ยืนยันขอบเขต
"""

import math
from dataclasses import dataclass, field

import numpy as np

from common.design_params import (
    compute_beta1, compute_rho_b, compute_rho_min, compute_rho_max, PHI_B, PHI_V,
)
from modules.slab_on_ground import (
    GS_STEEL_FY_KSC, GS_STEEL_BAR_TYPE, bar_area_cm2, CONCRETE_UNIT_WEIGHT_KG_M3,
)
from modules.beam_single_span import (
    PointLoad, FlexureDesign, StirrupDesign,
    _flexure_design, _stirrup_design, _max_bars_single_layer,
    COVER_CM, BEAM_WIDTH_CM_OPTIONS, BEAM_DEPTH_CM_OPTIONS,
    BAR_DIAMETERS_MM, STIRRUP_DIAMETERS_MM, DEFAULT_STIRRUP_LEGS,
)

MAX_SPANS = 10
MIN_SPANS = 2
MAX_POINT_LOADS_PER_SPAN = 5


@dataclass
class SpanInput:
    length_m: float
    line_load_dl_kg_m: float
    line_load_ll_kg_m: float
    point_loads: list = field(default_factory=list)   # list[PointLoad], x_m จากปลายซ้ายของช่วงนี้


@dataclass
class OverhangInput:
    length_m: float
    line_load_dl_kg_m: float
    line_load_ll_kg_m: float
    point_loads: list = field(default_factory=list)   # list[PointLoad], x_m จากจุดรองรับ (root)


@dataclass
class ContinuousBeamInput:
    fc_ksc: float
    main_steel_type: str
    stirrup_steel_type: str
    b_cm: float
    h_cm: float
    spans: list                          # list[SpanInput], ความยาว >= MIN_SPANS
    left_overhang: object = None         # OverhangInput หรือ None
    right_overhang: object = None
    main_bar_dia_mm: float = 16.0
    stirrup_bar_dia_mm: float = 9.0
    stirrup_legs: int = DEFAULT_STIRRUP_LEGS
    stirrup_spacing_use_cm: float = 15.0


@dataclass
class SpanResult:
    length_m: float
    self_weight_kg_m: float
    wu_kg_m: float
    pu_loads: list
    m_left_kgm: float
    m_right_kgm: float
    r_left_kg: float
    r_right_kg: float
    mu_pos_max_kgm: float
    mu_pos_max_x_m: float
    vu_max_kg: float
    x_arr: list
    v_arr: list
    m_arr: list
    bottom: FlexureDesign
    stirrup: StirrupDesign


@dataclass
class SupportResult:
    index: int
    moment_kgm: float
    reaction_kg: float
    is_exterior: bool
    has_overhang: bool
    top: FlexureDesign


@dataclass
class OverhangResult:
    length_m: float
    wu_kg_m: float
    pu_loads: list
    end_moment_kgm: float
    vu_kg: float
    top: FlexureDesign
    stirrup: StirrupDesign
    x_arr: list
    v_arr: list
    m_arr: list


@dataclass
class ContinuousBeamResult:
    spans: list
    supports: list
    left_overhang: object
    right_overhang: object
    beta1: float
    rho_b: float
    rho_min: float
    rho_max: float
    main_bar_type: str
    stirrup_bar_type: str
    total_length_m: float
    x_arr_full: list
    v_arr_full: list
    m_arr_full: list
    support_x_positions: list
    nominal_bars: FlexureDesign          # เหล็กยึดเหล็กปลอกขั้นต่ำ (hanger) — ใช้เป็นเหล็กบนกลางช่วง/เหล็กล่างที่จุดรองรับในรูปตัดรายละเอียด
    governing_span_index: int             # ช่วงที่มีเหล็กล่างมากสุด — ใช้เป็นรูปตัด "กลางคาน" ตัวแทน
    governing_support_index: int          # จุดรองรับที่มี |M| มากสุด — ใช้เป็นรูปตัด "หัวเสา/จุดรองรับ" ตัวแทน


def _simple_span_terms(L: float, w: float, pu_loads: list):
    """ปฏิกิริยาแบบ simple-span (determinate) + เทอม Three Moment Equation (RHS)
    ของช่วงหนึ่ง — pu_loads: list[(x_m, pu_kg)] วัดจากปลายซ้ายของช่วงนี้"""
    sum_pu = sum(p for _, p in pu_loads)
    moment_about_right = w * L * (L / 2.0) + sum(p * (L - x) for x, p in pu_loads)
    r0_left = moment_about_right / L if L > 0 else 0.0
    r0_right = w * L + sum_pu - r0_left

    term_L = w * L ** 3 / 4.0
    term_R = w * L ** 3 / 4.0
    for x, p in pu_loads:
        a = x
        b = L - x
        term_L += p * a * (L ** 2 - a ** 2) / L
        term_R += p * b * (L ** 2 - b ** 2) / L

    return r0_left, r0_right, term_L, term_R


def _overhang_end_moment_and_load(L0: float, wu: float, pu_loads: list):
    """โมเมนต์ที่จุดรองรับ (ราก) ของปลายยื่น (hogging = ลบ ตาม sign convention ของโมดูลนี้ ที่
    โมเมนต์บวก=sagging) + แรงรวมทั้งหมดบนปลายยื่น (= ปฏิกิริยาที่จุดรองรับต้องรับ)
    pu_loads: list[(x_m, pu_kg)] วัดจากจุดรองรับ (0) ถึงปลายยื่น (L0)"""
    end_moment = -(wu * L0 ** 2 / 2.0 + sum(p * x for x, p in pu_loads))
    total_load = wu * L0 + sum(p for _, p in pu_loads)
    return end_moment, total_load


def _overhang_local_arrays(L0: float, wu: float, pu_loads: list, n_samples: int = 40):
    """x_s วัดจากจุดรองรับ (0) ถึงปลายยื่น (L0) — ใช้ sign convention เดียวกับ shear_at/
    moment_at ของช่วงคาน (V = แรงขึ้นสุทธิจากด้าน 'ราก' ถึงจุดตัด): ที่ x_s=0 (จุดรองรับ)
    V=total_load (สูงสุด), M=end_moment (ค่าลบ/hogging) และที่ x_s=L0 (ปลายยื่นอิสระ) V=0, M=0"""
    def v_at(x_s, include_load_at_x=True):
        v = wu * (L0 - x_s)
        for xi, p in pu_loads:
            if (xi > x_s) or (include_load_at_x and abs(xi - x_s) < 1e-9):
                v += p
        return v

    def m_at(x_s):
        m = -(wu * (L0 - x_s) ** 2 / 2.0)
        for xi, p in pu_loads:
            if xi >= x_s:
                m -= p * (xi - x_s)
        return m

    load_xs = [x for x, _ in pu_loads]
    xs = sorted(set([i * L0 / n_samples for i in range(n_samples + 1)] + load_xs + [0.0, L0]))
    x_arr, v_arr, m_arr = [], [], []
    for x in xs:
        x_arr.append(x)
        v_arr.append(v_at(x, include_load_at_x=False))
        m_arr.append(m_at(x))
        for xi, p in pu_loads:
            if abs(xi - x) < 1e-9:
                x_arr.append(x)
                v_arr.append(v_at(x, include_load_at_x=True))
                m_arr.append(m_at(x))
    return x_arr, v_arr, m_arr


def _critical_points_and_max_pos_moment(L, w, pu_loads, m_left, r_left):
    """หาจุดวิกฤต (V=0) ในแต่ละ segment ระหว่างแรงจุด แล้วคืนค่าโมเมนต์บวกสูงสุด + ตำแหน่ง
    m_left = โมเมนต์จริงที่ปลายซ้ายช่วง (จาก Three Moment Equation, อาจติดลบ), r_left =
    ปฏิกิริยาซ้ายที่แก้ไขแล้ว (actual, ไม่ใช่ r0)"""
    def shear_at(x, include_load_at_x=True):
        v = r_left - w * x
        for xi, p in pu_loads:
            if (xi < x) or (include_load_at_x and abs(xi - x) < 1e-9):
                v -= p
        return v

    def moment_at(x):
        m = m_left + r_left * x - w * x ** 2 / 2.0
        for xi, p in pu_loads:
            if xi <= x:
                m -= p * (x - xi)
        return m

    boundaries = sorted(set([0.0] + [x for x, _ in pu_loads] + [L]))
    critical_x = set(boundaries)
    for i in range(len(boundaries) - 1):
        x_start, x_end = boundaries[i], boundaries[i + 1]
        v_start = shear_at(x_start, include_load_at_x=True)
        if w > 0:
            x_star = x_start + v_start / w
            if x_start <= x_star <= x_end:
                critical_x.add(x_star)

    mu_max = -1e18
    mu_max_x = 0.0
    for x in critical_x:
        m = moment_at(x)
        if m > mu_max:
            mu_max = m
            mu_max_x = x
    mu_max = max(mu_max, 0.0)

    return mu_max, mu_max_x, critical_x, shear_at, moment_at


def calculate(inp: ContinuousBeamInput) -> ContinuousBeamResult:
    fy_main = GS_STEEL_FY_KSC[inp.main_steel_type]
    fy_stirrup = GS_STEEL_FY_KSC[inp.stirrup_steel_type]

    b_m = inp.b_cm / 100.0
    h_m = inp.h_cm / 100.0
    self_weight = CONCRETE_UNIT_WEIGHT_KG_M3 * b_m * h_m   # kg/m — หน้าตัดเดียวกันทั้งคาน

    N = len(inp.spans)
    lengths = [s.length_m for s in inp.spans]
    wu_list = []
    pu_lists = []
    for s in inp.spans:
        wd_total = s.line_load_dl_kg_m + self_weight
        wu = 1.4 * wd_total + 1.7 * s.line_load_ll_kg_m
        wu_list.append(wu)
        pts = sorted(s.point_loads, key=lambda p: p.x_m)
        pu_lists.append([(p.x_m, 1.4 * p.p_dl_kg + 1.7 * p.p_ll_kg) for p in pts])

    r0_left_list, r0_right_list, term_L_list, term_R_list = [], [], [], []
    for L, w, pu in zip(lengths, wu_list, pu_lists):
        r0l, r0r, tl, tr = _simple_span_terms(L, w, pu)
        r0_left_list.append(r0l)
        r0_right_list.append(r0r)
        term_L_list.append(tl)
        term_R_list.append(tr)

    # --- โมเมนต์ที่ขอบเขต (known boundary) จาก overhang (ถ้ามี) ---
    left_ov = inp.left_overhang
    right_ov = inp.right_overhang

    if left_ov is not None:
        wd_ov_l = left_ov.line_load_dl_kg_m + self_weight
        wu_ov_l = 1.4 * wd_ov_l + 1.7 * left_ov.line_load_ll_kg_m
        pts_ov_l = sorted(left_ov.point_loads, key=lambda p: p.x_m)
        pu_ov_l = [(p.x_m, 1.4 * p.p_dl_kg + 1.7 * p.p_ll_kg) for p in pts_ov_l]
        m0_known, total_load_l = _overhang_end_moment_and_load(left_ov.length_m, wu_ov_l, pu_ov_l)
    else:
        wu_ov_l, pu_ov_l = 0.0, []
        m0_known, total_load_l = 0.0, 0.0

    if right_ov is not None:
        wd_ov_r = right_ov.line_load_dl_kg_m + self_weight
        wu_ov_r = 1.4 * wd_ov_r + 1.7 * right_ov.line_load_ll_kg_m
        pts_ov_r = sorted(right_ov.point_loads, key=lambda p: p.x_m)
        pu_ov_r = [(p.x_m, 1.4 * p.p_dl_kg + 1.7 * p.p_ll_kg) for p in pts_ov_r]
        mN_known, total_load_r = _overhang_end_moment_and_load(right_ov.length_m, wu_ov_r, pu_ov_r)
    else:
        wu_ov_r, pu_ov_r = 0.0, []
        mN_known, total_load_r = 0.0, 0.0

    # --- แก้ระบบสมการ Three Moment Equation หาโมเมนต์ที่จุดรองรับภายใน (unknowns) ---
    n_unknown = N - 1
    M = [0.0] * (N + 1)   # M[0..N] ที่จุดรองรับ 0..N (0=ซ้ายสุด, N=ขวาสุด)
    M[0] = m0_known
    M[N] = mN_known

    if n_unknown > 0:
        A = np.zeros((n_unknown, n_unknown))
        rhs = np.zeros(n_unknown)
        for row in range(n_unknown):
            i = row + 1                      # support index (1..N-1)
            L_i = lengths[i - 1]              # ช่วงทางซ้ายของ support i
            L_ip1 = lengths[i]                # ช่วงทางขวาของ support i
            A[row, row] = 2.0 * (L_i + L_ip1)
            rhs_val = -(term_R_list[i - 1] + term_L_list[i])
            if i - 1 >= 1:
                A[row, row - 1] = L_i
            else:
                rhs_val -= M[0] * L_i
            if i + 1 <= N - 1:
                A[row, (i + 1) - 1] = L_ip1
            else:
                rhs_val -= M[N] * L_ip1
            rhs[row] = rhs_val
        M_unknown = np.linalg.solve(A, rhs)
        for k in range(n_unknown):
            M[k + 1] = float(M_unknown[k])

    # --- ปฏิกิริยาจริงแต่ละช่วง + โมเมนต์บวกสูงสุด + array สำหรับกราฟ (local, 0..L) ---
    span_results = []
    for i in range(N):
        L = lengths[i]
        w = wu_list[i]
        pu = pu_lists[i]
        m_left = M[i]
        m_right = M[i + 1]
        r_left = r0_left_list[i] + (m_right - m_left) / L
        r_right = r0_right_list[i] + (m_left - m_right) / L

        mu_pos_max, mu_pos_max_x, critical_x, shear_at, moment_at = _critical_points_and_max_pos_moment(
            L, w, pu, m_left, r_left
        )
        vu_max = max(abs(r_left), abs(r_right))

        n_samples = 80
        xs = sorted(set([j * L / n_samples for j in range(n_samples + 1)] + list(critical_x)))
        x_arr, v_arr, m_arr = [], [], []
        for x in xs:
            x_arr.append(x)
            v_arr.append(shear_at(x, include_load_at_x=False))
            m_arr.append(moment_at(x))
            for xi, p in pu:
                if abs(xi - x) < 1e-9:
                    x_arr.append(x)
                    v_arr.append(shear_at(x, include_load_at_x=True))
                    m_arr.append(moment_at(x))

        span_results.append(dict(
            length_m=L, self_weight_kg_m=self_weight, wu_kg_m=w, pu_loads=pu,
            m_left_kgm=m_left, m_right_kgm=m_right, r_left_kg=r_left, r_right_kg=r_right,
            mu_pos_max_kgm=mu_pos_max, mu_pos_max_x_m=mu_pos_max_x, vu_max_kg=vu_max,
            x_arr=x_arr, v_arr=v_arr, m_arr=m_arr,
        ))

    # --- คุณสมบัติหน้าตัด/เหล็ก (ใช้ร่วมกันทั้งคาน — หน้าตัดเดียว) ---
    beta1 = compute_beta1(inp.fc_ksc)
    rho_b = compute_rho_b(inp.fc_ksc, fy_main, beta1)
    rho_min = compute_rho_min(fy_main)
    rho_max = compute_rho_max(rho_b)
    main_bar_type = GS_STEEL_BAR_TYPE[inp.main_steel_type]
    stirrup_bar_type = GS_STEEL_BAR_TYPE[inp.stirrup_steel_type]

    spans_out = []
    for sr in span_results:
        bottom = _flexure_design(
            sr["mu_pos_max_kgm"], inp.b_cm, inp.h_cm, inp.fc_ksc, fy_main,
            inp.main_bar_dia_mm, inp.stirrup_bar_dia_mm,
            beta1, rho_b, rho_min, rho_max, is_nominal_only=False,
        )
        stirrup = _stirrup_design(
            sr["vu_max_kg"], inp.b_cm, bottom.d_cm, inp.fc_ksc, fy_stirrup,
            inp.stirrup_legs, inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm,
        )
        spans_out.append(SpanResult(
            length_m=sr["length_m"], self_weight_kg_m=sr["self_weight_kg_m"],
            wu_kg_m=sr["wu_kg_m"], pu_loads=sr["pu_loads"],
            m_left_kgm=sr["m_left_kgm"], m_right_kgm=sr["m_right_kgm"],
            r_left_kg=sr["r_left_kg"], r_right_kg=sr["r_right_kg"],
            mu_pos_max_kgm=sr["mu_pos_max_kgm"], mu_pos_max_x_m=sr["mu_pos_max_x_m"],
            vu_max_kg=sr["vu_max_kg"], x_arr=sr["x_arr"], v_arr=sr["v_arr"], m_arr=sr["m_arr"],
            bottom=bottom, stirrup=stirrup,
        ))

    # --- จุดรองรับ: โมเมนต์ + ปฏิกิริยา (bookkeeping) + เหล็กบน ---
    supports_out = []
    for i in range(N + 1):
        m_i = M[i]
        if i == 0:
            reaction = spans_out[0].r_left_kg + total_load_l
            has_ov = left_ov is not None
            is_ext = True
        elif i == N:
            reaction = spans_out[N - 1].r_right_kg + total_load_r
            has_ov = right_ov is not None
            is_ext = True
        else:
            reaction = spans_out[i - 1].r_right_kg + spans_out[i].r_left_kg
            has_ov = False
            is_ext = False

        is_nominal = abs(m_i) < 1e-6
        top = _flexure_design(
            abs(m_i), inp.b_cm, inp.h_cm, inp.fc_ksc, fy_main,
            inp.main_bar_dia_mm, inp.stirrup_bar_dia_mm,
            beta1, rho_b, rho_min, rho_max, is_nominal_only=is_nominal,
        )
        supports_out.append(SupportResult(
            index=i, moment_kgm=m_i, reaction_kg=reaction,
            is_exterior=is_ext, has_overhang=has_ov, top=top,
        ))

    # --- ปลายยื่น: เหล็กบน + เหล็กปลอก + array สำหรับกราฟ ---
    left_ov_out = None
    if left_ov is not None:
        x_arr_l, v_arr_l, m_arr_l = _overhang_local_arrays(left_ov.length_m, wu_ov_l, pu_ov_l)
        top_l = _flexure_design(
            abs(m0_known), inp.b_cm, inp.h_cm, inp.fc_ksc, fy_main,
            inp.main_bar_dia_mm, inp.stirrup_bar_dia_mm,
            beta1, rho_b, rho_min, rho_max, is_nominal_only=False,
        )
        stirrup_l = _stirrup_design(
            total_load_l, inp.b_cm, top_l.d_cm, inp.fc_ksc, fy_stirrup,
            inp.stirrup_legs, inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm,
        )
        left_ov_out = OverhangResult(
            length_m=left_ov.length_m, wu_kg_m=wu_ov_l, pu_loads=pu_ov_l,
            end_moment_kgm=m0_known, vu_kg=total_load_l, top=top_l, stirrup=stirrup_l,
            x_arr=x_arr_l, v_arr=v_arr_l, m_arr=m_arr_l,
        )

    right_ov_out = None
    if right_ov is not None:
        x_arr_r, v_arr_r, m_arr_r = _overhang_local_arrays(right_ov.length_m, wu_ov_r, pu_ov_r)
        top_r = _flexure_design(
            abs(mN_known), inp.b_cm, inp.h_cm, inp.fc_ksc, fy_main,
            inp.main_bar_dia_mm, inp.stirrup_bar_dia_mm,
            beta1, rho_b, rho_min, rho_max, is_nominal_only=False,
        )
        stirrup_r = _stirrup_design(
            total_load_r, inp.b_cm, top_r.d_cm, inp.fc_ksc, fy_stirrup,
            inp.stirrup_legs, inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm,
        )
        right_ov_out = OverhangResult(
            length_m=right_ov.length_m, wu_kg_m=wu_ov_r, pu_loads=pu_ov_r,
            end_moment_kgm=mN_known, vu_kg=total_load_r, top=top_r, stirrup=stirrup_r,
            x_arr=x_arr_r, v_arr=v_arr_r, m_arr=m_arr_r,
        )

    # --- ตำแหน่ง global ของแต่ละจุดรองรับ (s0=0 คือจุดรองรับซ้ายสุดของ "คานหลัก" เสมอ) ---
    support_x = [0.0]
    for L in lengths:
        support_x.append(support_x[-1] + L)
    total_length = support_x[-1]
    if left_ov is not None:
        total_length += left_ov.length_m
    if right_ov is not None:
        total_length += right_ov.length_m

    # --- รวม array เต็มคาน (รวม overhang) เป็นพิกัด global เดียว ---
    x_full, v_full, m_full = [], [], []
    if left_ov_out is not None:
        s0 = support_x[0]
        for xs, vs, ms in zip(left_ov_out.x_arr, left_ov_out.v_arr, left_ov_out.m_arr):
            x_full.append(s0 - xs)
            v_full.append(-vs)
            m_full.append(ms)

    for i, sp in enumerate(spans_out):
        s_i = support_x[i]
        for xs, vs, ms in zip(sp.x_arr, sp.v_arr, sp.m_arr):
            x_full.append(s_i + xs)
            v_full.append(vs)
            m_full.append(ms)

    if right_ov_out is not None:
        sN = support_x[N]
        for xs, vs, ms in zip(right_ov_out.x_arr, right_ov_out.v_arr, right_ov_out.m_arr):
            x_full.append(sN + xs)
            v_full.append(vs)
            m_full.append(ms)

    order = sorted(range(len(x_full)), key=lambda k: x_full[k])
    x_full = [x_full[k] for k in order]
    v_full = [v_full[k] for k in order]
    m_full = [m_full[k] for k in order]

    # --- เหล็กยึดเหล็กปลอกขั้นต่ำ (nominal/hanger) — ใช้เป็นเหล็กบนกลางช่วง/เหล็กล่างที่จุดรองรับ
    # ในรูปตัดรายละเอียด (ค่าเดียวกันทุกตำแหน่ง เพราะขึ้นกับ b/เหล็กปลอกเท่านั้น ไม่ขึ้นกับโมเมนต์) ---
    nominal_bars = _flexure_design(
        0.0, inp.b_cm, inp.h_cm, inp.fc_ksc, fy_main,
        inp.main_bar_dia_mm, inp.stirrup_bar_dia_mm,
        beta1, rho_b, rho_min, rho_max, is_nominal_only=True,
    )
    governing_span_index = max(range(N), key=lambda i: spans_out[i].bottom.n_bars_use)
    governing_support_index = max(range(N + 1), key=lambda i: abs(supports_out[i].moment_kgm))

    return ContinuousBeamResult(
        spans=spans_out, supports=supports_out,
        left_overhang=left_ov_out, right_overhang=right_ov_out,
        beta1=beta1, rho_b=rho_b, rho_min=rho_min, rho_max=rho_max,
        main_bar_type=main_bar_type, stirrup_bar_type=stirrup_bar_type,
        total_length_m=total_length,
        x_arr_full=x_full, v_arr_full=v_full, m_arr_full=m_full,
        support_x_positions=support_x,
        nominal_bars=nominal_bars,
        governing_span_index=governing_span_index,
        governing_support_index=governing_support_index,
    )
