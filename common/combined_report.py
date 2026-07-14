"""
common/combined_report.py — รวมรายการคำนวณที่บันทึกไว้ทุกโมดูล (จาก
common.project_store) เป็นรายงาน HTML เดียว (หน้าปก + ทุกรายการเรียงตามลำดับหมวด)
สำหรับปุ่ม "ดาวน์โหลดข้อมูลทั้งหมด" ใน sidebar — คำนวณใหม่จาก input dict ที่บันทึกไว้
ทุกครั้งที่กด (ไม่ได้เก็บผลลัพธ์/รูปภาพไว้ ลดขนาด session_state) แล้วส่งต่อให้
common.pdf_export.html_to_pdf() แปลงเป็น PDF ไฟล์เดียวอีกที

แต่ละโมดูลมีฟังก์ชัน `_render_<module>(code, data) -> str` คืน HTML fragment ของ
รายการนั้น (เรียก calculate() + วาดรูปประกอบ + build_*_report_html() ซ้ำแบบเดียวกับ
ที่หน้าโมดูลนั้นทำตอนกด "คำนวณ" ทุกประการ — ต่างกันแค่ input มาจาก dict ที่บันทึกไว้
แทนที่จะมาจาก widget สดๆ)
"""

import streamlit as st

from common.project_store import MODULE_LABELS, get_items, total_item_count
from common.report import build_cover_page_html


def _page_break_wrap(title: str, body_html: str) -> str:
    return (
        f'<div style="page-break-before: always; padding-top: 8px;">'
        f'<h2 style="color:#1E3853; border-bottom:2px solid #1E3853; padding-bottom:6px;">{title}</h2>'
        f"{body_html}</div>"
    )


def _render_slab_on_ground(code: str, data: dict) -> str:
    from modules.slab_on_ground import SlabOnGroundInput, calculate as calc_sg
    from common.diagram import draw_gs_detail_png
    from common.report import build_gs_report_html

    inp = SlabOnGroundInput(**data)
    result = calc_sg(inp)
    project = {"slab_name": code, "project_name": "", "owner": "", "location": "", "engineer": ""}
    diagram_png = draw_gs_detail_png(inp.t_cm, inp.main_bar_dia_mm, inp.main_bar_spacing_cm)
    return build_gs_report_html(
        project, inp, result, diagram_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _render_one_way_slab(code: str, data: dict) -> str:
    from modules.one_way_slab import OneWaySlabInput, calculate as calc_ow
    from common.diagram import draw_ow_section_png, draw_ow_plan_png
    from common.report import build_ow_report_html

    inp = OneWaySlabInput(**data)
    result = calc_ow(inp)
    project = {"slab_name": code}
    end1_active = result.positions[0].active
    end2_active = result.positions[2].active
    section_png = draw_ow_section_png(
        inp.t_cm, inp.main_bar_dia_mm, inp.main_bar_spacing_cm,
        inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm, inp.S_m,
        end1_active, end2_active,
        main_bar_type=result.main_bar_type, temp_bar_type=result.temp_bar_type)
    plan_png = draw_ow_plan_png(
        inp.main_bar_dia_mm, inp.main_bar_spacing_cm,
        inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm,
        inp.S_m, inp.L_m, end1_active, end2_active,
        main_bar_type=result.main_bar_type, temp_bar_type=result.temp_bar_type)
    return build_ow_report_html(
        project, inp, result, section_png, plan_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _tw_end_states(positions):
    con_active = positions[0].active
    disc_active = positions[2].active
    if con_active and disc_active:
        return "continuous", "discontinuous"
    if con_active:
        return "continuous", "continuous"
    return "none", "none"


def _render_two_way_slab(code: str, data: dict) -> str:
    from modules.two_way_slab import TwoWaySlabInput, calculate as calc_tw
    from common.diagram import draw_tw_section_png, draw_tw_plan_png
    from common.report import build_tw_report_html

    inp = TwoWaySlabInput(**data)
    result = calc_tw(inp)
    project = {"slab_name": code}
    s_end1, s_end2 = _tw_end_states(result.short_positions)
    l_end1, l_end2 = _tw_end_states(result.long_positions)
    section_s_png = draw_tw_section_png(
        "S", inp.S_m, inp.t_cm,
        inp.short_bar_dia_mm, inp.short_bar_spacing_cm, result.short_bar_type,
        inp.long_bar_dia_mm, inp.long_bar_spacing_cm, result.long_bar_type,
        end1_state=s_end1, end2_state=s_end2)
    section_l_png = draw_tw_section_png(
        "L", inp.L_m, inp.t_cm,
        inp.long_bar_dia_mm, inp.long_bar_spacing_cm, result.long_bar_type,
        inp.short_bar_dia_mm, inp.short_bar_spacing_cm, result.short_bar_type,
        end1_state=l_end1, end2_state=l_end2)
    plan_png = draw_tw_plan_png(
        inp.S_m, inp.L_m,
        inp.short_bar_dia_mm, inp.short_bar_spacing_cm, result.short_bar_type,
        inp.long_bar_dia_mm, inp.long_bar_spacing_cm, result.long_bar_type,
        s_end1_state=s_end1, s_end2_state=s_end2,
        l_end1_state=l_end1, l_end2_state=l_end2)
    return build_tw_report_html(
        project, inp, result, section_s_png, section_l_png, plan_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _render_cantilever_slab(code: str, data: dict) -> str:
    from modules.cantilever_slab import CantileverSlabInput, calculate as calc_cant
    from common.diagram import draw_cant_section_png, draw_cant_plan_png
    from common.report import build_cant_report_html

    inp = CantileverSlabInput(**data)
    result = calc_cant(inp)
    project = {"slab_name": code}
    section_png = draw_cant_section_png(
        inp.S_m, inp.t_cm,
        inp.main_bar_dia_mm, inp.main_bar_spacing_cm, result.main_bar_type,
        inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm, result.temp_bar_type)
    plan_png = draw_cant_plan_png(
        inp.S_m,
        inp.main_bar_dia_mm, inp.main_bar_spacing_cm, result.main_bar_type,
        inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm, result.temp_bar_type)
    return build_cant_report_html(
        project, inp, result, section_png, plan_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _render_stair_straight(code: str, data: dict) -> str:
    from modules.stair_straight import StairStraightInput, calculate as calc_stair
    from common.diagram import draw_stair_section_png, draw_stair_rebar_detail_png
    from common.report import build_stair_report_html

    inp = StairStraightInput(**data)
    result = calc_stair(inp)
    project = {"stair_name": code}
    section_png = draw_stair_section_png(
        inp.n_riser, result.rise_cm, result.going_cm, inp.t_cm, result.S_m)
    detail_png = draw_stair_rebar_detail_png(
        result.rise_cm, result.going_cm, inp.t_cm,
        inp.main_bar_dia_mm, inp.main_bar_spacing_cm,
        inp.temp_bar_dia_mm, inp.temp_bar_spacing_cm,
        main_bar_type=result.main_bar_type, temp_bar_type=result.temp_bar_type)
    return build_stair_report_html(
        project, inp, result, section_png,
        detail_png=detail_png,
        project_info=st.session_state.get("project_info"),
        logo_bytes=st.session_state.get("project_logo_bytes"),
        logo_mime=st.session_state.get("project_logo_mime"),
    )


def _render_stair_u_shape(code: str, data: dict) -> str:
    from modules.stair_u_shape import StairUShapeInput, calculate as calc_stair_u
    from common.stair_detail import draw_stair_u_shape_detail_template_png
    from common.report import build_stair_u_shape_report_html

    inp = StairUShapeInput(**data)
    result = calc_stair_u(inp)
    project = {"stair_name": code}
    elevation_png = draw_stair_u_shape_detail_template_png(inp, result)
    return build_stair_u_shape_report_html(
        project, inp, result, elevation_png,
        detail_png=None,
        project_info=st.session_state.get("project_info"),
        logo_bytes=st.session_state.get("project_logo_bytes"),
        logo_mime=st.session_state.get("project_logo_mime"),
    )


def _rebuild_point_loads(raw_list):
    from modules.beam_single_span import PointLoad
    return [PointLoad(**pl) for pl in (raw_list or [])]


def _render_beam_single_span(code: str, data: dict) -> str:
    from modules.beam_single_span import BeamSingleSpanInput, calculate as calc_beam
    from common.diagram import draw_beam_sfd_bmd_png, draw_beam_section_png
    from common.report import build_beam_report_html

    data = dict(data)
    data["point_loads"] = _rebuild_point_loads(data.get("point_loads"))
    inp = BeamSingleSpanInput(**data)
    result = calc_beam(inp)
    project = {"beam_name": code}
    sfd_bmd_png = draw_beam_sfd_bmd_png(
        result.x_arr, result.v_arr, result.m_arr, inp.L_m,
        result.vu_max_kg, result.mu_max_kg_m, result.mu_max_x_m)
    section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, result.bottom.bars_per_layer, result.top.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    return build_beam_report_html(
        project, inp, result, sfd_bmd_png, section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _render_cantilever_beam(code: str, data: dict) -> str:
    from modules.cantilever_beam import CantileverBeamInput, calculate as calc_cant
    from common.diagram import (
        draw_cantilever_beam_elevation_png, draw_cantilever_beam_sfd_bmd_png, draw_beam_section_png,
    )
    from common.report import build_cantilever_beam_report_html

    data = dict(data)
    data["point_loads"] = _rebuild_point_loads(data.get("point_loads"))
    inp = CantileverBeamInput(**data)
    result = calc_cant(inp)
    project = {"beam_name": code}
    elevation_png = draw_cantilever_beam_elevation_png(inp, result)
    sfd_bmd_png = draw_cantilever_beam_sfd_bmd_png(result, inp.L_m)
    section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, result.bottom.bars_per_layer, result.top.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    return build_cantilever_beam_report_html(
        project, inp, result, elevation_png, sfd_bmd_png, section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _rebuild_span_or_overhang(raw: dict, cls):
    raw = dict(raw)
    raw["point_loads"] = _rebuild_point_loads(raw.get("point_loads"))
    return cls(**raw)


def _render_continuous_beam(code: str, data: dict) -> str:
    from modules.continuous_beam import ContinuousBeamInput, SpanInput, OverhangInput, calculate as calc_cbeam
    from modules.beam_single_span import reinf_label_with_layers  # noqa: F401 (parity import, unused here)
    from common.diagram import (
        draw_continuous_beam_sfd_bmd_png, draw_continuous_beam_elevation_png, draw_beam_section_png,
    )
    from common.report import build_continuous_beam_report_html

    data = dict(data)
    data["spans"] = [_rebuild_span_or_overhang(s, SpanInput) for s in (data.get("spans") or [])]
    data["left_overhang"] = (
        _rebuild_span_or_overhang(data["left_overhang"], OverhangInput) if data.get("left_overhang") else None
    )
    data["right_overhang"] = (
        _rebuild_span_or_overhang(data["right_overhang"], OverhangInput) if data.get("right_overhang") else None
    )
    inp = ContinuousBeamInput(**data)
    result = calc_cbeam(inp)
    project = {"beam_name": code}
    elevation_png = draw_continuous_beam_elevation_png(result)
    sfd_bmd_png = draw_continuous_beam_sfd_bmd_png(result)
    gsp_i = result.governing_span_index
    gsup_i = result.governing_support_index
    gsp = result.spans[gsp_i]
    gsup = result.supports[gsup_i]
    midspan_section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, gsp.bottom.bars_per_layer, result.nominal_bars.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    support_section_png = draw_beam_section_png(
        inp.b_cm, inp.h_cm, result.nominal_bars.bars_per_layer, gsup.top.bars_per_layer,
        inp.main_bar_dia_mm, result.main_bar_type,
        inp.stirrup_bar_dia_mm, inp.stirrup_spacing_use_cm, result.stirrup_bar_type)
    return build_continuous_beam_report_html(
        project, inp, result, elevation_png, sfd_bmd_png,
        midspan_section_png, support_section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _render_column_tied(code: str, data: dict) -> str:
    from modules.column_tied import ColumnTiedInput, calculate as calc_col
    from common.diagram import draw_column_section_png, draw_column_interaction_png
    from common.report import build_column_report_html

    inp = ColumnTiedInput(**data)
    result = calc_col(inp)
    project = {"column_name": code}
    section_png = draw_column_section_png(
        inp.b_cm, inp.h_cm, result.bar_layers, inp.main_bar_dia_mm, result.main_bar_type,
        inp.tie_bar_dia_mm, inp.tie_spacing_use_cm, result.tie_bar_type, inp.cover_cm)
    interaction_png = draw_column_interaction_png(
        result.interaction_points, inp.pu_kg, result.slenderness.mu_design_kgm,
        result.phi_mn_capacity_at_pu_kgm, mu_applied_kgm=inp.mu_kgm,
        b_cm=inp.b_cm, h_cm=inp.h_cm)
    return build_column_report_html(
        project, inp, result, section_png, interaction_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _render_column_spiral(code: str, data: dict) -> str:
    from modules.column_spiral import ColumnSpiralInput, calculate as calc_col
    from common.diagram import draw_column_circular_section_png, draw_column_interaction_png
    from common.report import build_column_spiral_report_html

    inp = ColumnSpiralInput(**data)
    result = calc_col(inp)
    project = {"column_name": code}
    section_png = draw_column_circular_section_png(
        inp.diameter_cm, result.bar_points, inp.main_bar_dia_mm, result.main_bar_type,
        inp.spiral_bar_dia_mm, inp.spiral_pitch_use_cm, result.spiral_bar_type, inp.cover_cm)
    interaction_png = draw_column_interaction_png(
        result.interaction_points, inp.pu_kg, result.slenderness.mu_design_kgm,
        result.phi_mn_capacity_at_pu_kgm, mu_applied_kgm=inp.mu_kgm)
    return build_column_spiral_report_html(
        project, inp, result, section_png, interaction_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _render_footing_spread(code: str, data: dict) -> str:
    from modules.footing_spread import FootingSpreadInput, calculate as calc_footing
    from common.diagram import draw_footing_plan_png, draw_footing_section_png
    from common.report import build_footing_report_html

    inp = FootingSpreadInput(**data)
    result = calc_footing(inp)
    project = {"footing_name": code}
    plan_png = draw_footing_plan_png(
        result.B_cm, inp.column_b_cm, inp.column_h_cm, inp.main_bar_dia_mm, result.main_bar_type,
        result.flex_x.n_bars_use, result.flex_y.n_bars_use)
    section_png = draw_footing_section_png(
        result.B_cm, result.t_cm, inp.column_b_cm, inp.cover_cm, inp.main_bar_dia_mm, result.main_bar_type,
        result.d_x_cm, result.d_y_cm, result.flex_x.n_bars_use, result.flex_y.n_bars_use,
        result.q_actual_kg_m2)
    return build_footing_report_html(
        project, inp, result, plan_png, section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


def _render_footing_pile_cap(code: str, data: dict) -> str:
    from modules.footing_pile_cap import PileCapInput, calculate as calc_pile_cap
    from common.diagram import draw_pile_cap_plan_png, draw_pile_cap_section_png
    from common.report import build_pile_cap_report_html

    inp = PileCapInput(**data)
    result = calc_pile_cap(inp)
    project = {"footing_name": code}
    plan_png = draw_pile_cap_plan_png(
        result.geometry.A_cm, result.geometry.B_cm, inp.column_b_cm, inp.column_h_cm,
        inp.pile_size_cm, result.geometry.pile_positions_cm,
        inp.main_bar_dia_mm, result.main_bar_type, result.flex_1.n_bars_use, result.flex_2.n_bars_use)
    section_png = draw_pile_cap_section_png(
        result.geometry.A_cm, result.t_cm, inp.column_b_cm, inp.cover_cm,
        inp.pile_size_cm, result.geometry.c_dist_cm, inp.n_piles,
        inp.main_bar_dia_mm, result.main_bar_type, result.d1_cm, result.d2_cm)
    return build_pile_cap_report_html(
        project, inp, result, plan_png, section_png,
        st.session_state.get("project_info"),
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
    )


_RENDERERS = {
    "slab_on_ground": _render_slab_on_ground,
    "one_way_slab": _render_one_way_slab,
    "two_way_slab": _render_two_way_slab,
    "cantilever_slab": _render_cantilever_slab,
    "stair_straight": _render_stair_straight,
    "stair_u_shape": _render_stair_u_shape,
    "beam_single_span": _render_beam_single_span,
    "continuous_beam": _render_continuous_beam,
    "cantilever_beam": _render_cantilever_beam,
    "column_tied": _render_column_tied,
    "column_spiral": _render_column_spiral,
    "footing_spread": _render_footing_spread,
    "footing_pile_cap": _render_footing_pile_cap,
}


def build_all_items_html():
    """สร้าง HTML รวมหน้าปก + ทุกรายการที่บันทึกไว้ (เรียงตามลำดับหมวดในเมนู) คืนค่า
    เป็น tuple (html, count, errors) — errors คือ list ของ (module_key, code, ข้อความ
    error) รายการที่คำนวณซ้ำไม่สำเร็จ (เช่น input dict เพี้ยน) จะถูกข้ามแต่ไม่ทำให้
    รายการอื่นพัง"""
    sections = []
    errors = []
    count = 0

    cover_html = build_cover_page_html(
        st.session_state.get("project_info") or {},
        st.session_state.get("project_logo_bytes"),
        st.session_state.get("project_logo_mime"),
        st.session_state.get("project_cover_image_bytes"),
        st.session_state.get("project_cover_image_mime"),
    )
    sections.append(cover_html)

    # หน้าพารามิเตอร์การออกแบบ — แนบทุกครั้งหลังหน้าปก (ตามคำขอผู้ใช้: ดาวน์โหลดทั้งโครงการ
    # ให้ได้ทั้งปก+พารามิเตอร์ในไฟล์เดียว ไม่ต้องไปสร้าง/ดาวน์โหลดแยก) — คำนวณสดจากค่าที่
    # ผู้ใช้ตั้งไว้ล่าสุด (session_state) เหมือนหน้า design_parameters ทุกประการ ห่อ try/except
    # กันไม่ให้พังทั้งไฟล์ถ้าเกิดข้อผิดพลาด (บันทึกไว้ใน errors แล้วข้ามไป)
    try:
        from common.design_params import (
            calculate as _calc_params,
            LOAD_SCHEDULE as _LOAD_SCHEDULE,
            LOAD_FACTOR_NOTE as _LOAD_FACTOR_NOTE,
            LOAD_SCHEDULE_SOURCE as _LOAD_SCHEDULE_SOURCE,
        )
        from common.report import build_design_params_report_html

        _fc = st.session_state.get("design_params_fc", 240.0)
        _sr = st.session_state.get("design_params_steel_sr", "SR24")
        _sd = st.session_state.get("design_params_steel_sd", "SD40")
        _params_html = build_design_params_report_html(
            _calc_params(_fc, _sr),
            _calc_params(_fc, _sd),
            st.session_state.get("project_info"),
            st.session_state.get("project_logo_bytes"),
            st.session_state.get("project_logo_mime"),
            load_schedule=_LOAD_SCHEDULE,
            load_factor_note=_LOAD_FACTOR_NOTE,
            load_schedule_source=_LOAD_SCHEDULE_SOURCE,
        )
        sections.append(f'<div style="page-break-before: always;">{_params_html}</div>')
    except Exception as e:  # noqa: BLE001
        errors.append(("design_parameters", "พารามิเตอร์การออกแบบ", str(e)))

    for module_key, label in MODULE_LABELS.items():
        items = get_items(module_key)
        if not items:
            continue
        renderer = _RENDERERS[module_key]
        for code, data in items.items():
            try:
                item_html = renderer(code, data)
            except Exception as e:
                errors.append((module_key, code, str(e)))
                continue
            sections.append(_page_break_wrap(f"{label} — {code}", item_html))
            count += 1

    combined = (
        '<div style="font-family: \'TH Sarabun New\', Arial, sans-serif;">'
        + "".join(sections)
        + "</div>"
    )
    return combined, count, errors


def _items_signature() -> tuple:
    """ลายเซ็นสั้นๆ ของรายการที่บันทึกไว้ทั้งหมด (โมดูล+รหัส) ใช้เช็คว่ารายการ
    เปลี่ยนไปจากตอนสร้างไฟล์รวมครั้งก่อนหรือไม่ โดยไม่ต้องคำนวณ/วาดรูปซ้ำทุก
    ครั้งที่ sidebar render (ซึ่งเกิดขึ้นทุกหน้า ทุก rerun) — คำนวณจริงเฉพาะตอนกด
    ปุ่มสร้างไฟล์เท่านั้น (ตามคำขอผู้ใช้ว่าห้ามดาวน์โหลด/สร้างไฟล์อัตโนมัติ)"""
    sig = []
    for module_key in MODULE_LABELS:
        for code in sorted(get_items(module_key).keys()):
            sig.append((module_key, code))
    return tuple(sig)


def render_combined_download_button() -> None:
    """ปุ่ม 'ดาวน์โหลดข้อมูลทั้งหมด' ใน sidebar — รวมทุกรายการที่บันทึกไว้เป็น PDF
    ไฟล์เดียว ทำงานแบบ 2 จังหวะเหมือน pdf_export.download_report_button() ทุก
    ประการ (ไม่สร้าง/แปลงไฟล์อัตโนมัติ ต้องกดปุ่มเองก่อนเสมอ) ต่างกันตรงที่ต้อง
    รวบรวม HTML จากทุกรายการก่อน (ขั้นตอนที่หนักกว่ารายงานเดี่ยว) จึงเลื่อนขั้นตอน
    นี้ไปทำตอนกดปุ่มครั้งแรกด้วยเช่นกัน (ไม่ใช่ตอน sidebar render ทุกครั้ง)"""
    from common.pdf_export import html_to_pdf

    cache_key = "_pdf_cache_all_items"
    sig_key = f"{cache_key}_sig"
    count = total_item_count()
    sig = _items_signature()

    if st.session_state.get(sig_key) != sig:
        st.session_state[cache_key] = None
        st.session_state[sig_key] = sig

    cached = st.session_state.get(cache_key)

    if cached is None:
        label = f"📥 ดาวน์โหลดข้อมูลทั้งหมด ({count} รายการ)"
        if st.button(label, key="dl_all_gen", use_container_width=True, disabled=(count == 0)):
            with st.spinner("กำลังรวบรวมรายการและสร้างไฟล์ PDF..."):
                combined_html, n, errors = build_all_items_html()
                pdf_bytes = html_to_pdf(combined_html) if combined_html else None
            st.session_state[cache_key] = pdf_bytes if pdf_bytes else b""
            st.session_state["_pdf_cache_all_items_html"] = combined_html
            st.session_state["_pdf_cache_all_items_errors"] = errors
            st.rerun()
        return

    errors = st.session_state.get("_pdf_cache_all_items_errors") or []
    if errors:
        st.caption(f"⚠️ ข้ามไป {len(errors)} รายการ (คำนวณซ้ำไม่สำเร็จ): "
                    + ", ".join(f"{code}" for _, code, _ in errors))

    from common.pdf_export import native_save_button
    if cached:
        native_save_button(
            "⬇️ บันทึกข้อมูลทั้งหมด (PDF)",
            cached,
            "npk_rc_sdm_รายการทั้งหมด.pdf",
            key="dl_all_pdf",
            mime="application/pdf",
            color="#2563EB",
        )
    else:
        html_fallback = st.session_state.get("_pdf_cache_all_items_html") or ""
        native_save_button(
            "⬇️ บันทึกข้อมูลทั้งหมด (HTML — เปิดแล้วกดพิมพ์ได้)",
            html_fallback,
            "npk_rc_sdm_รายการทั้งหมด.html",
            key="dl_all_html",
            mime="text/html",
            color="#2563EB",
        )
        st.caption("⚠️ ไม่พบ Microsoft Edge สำหรับแปลงเป็น PDF อัตโนมัติ — บันทึกเป็น HTML แทนชั่วคราว")
