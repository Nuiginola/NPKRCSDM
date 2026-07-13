"""
Schematic detail drawing for Slab-on-Ground reinforcement/joint,
generated dynamically from the actual design inputs (thickness, bar
size/spacing) so the drawing in the printed report matches the numbers.

Geometry is reverse-engineered directly from the user's own reference
Excel file ("Detail Slabonground.xlsx", an XY-scatter chart built from
raw coordinate series) so every line, tick mark and label position
matches the reference drawing exactly: wall on the LEFT with a keyed
joint (vertical drop -> shelf -> diagonal taper back to the slab
soffit), blue dimension lines with perpendicular tick marks (not
arrowheads), a blue elbow leader for "Mastic Joint Sealer" to an orange
sealer strip, a black reinforcement line with a hooked end + tick-dots
and TWO SEPARATE "RB{dia}@{spacing}" call-outs (elbow leaders, spacing
shown in metres e.g. "0.2"), Lean/Sand fill layers below the slab
labelled in blue, a green "Ground Slab" caption, and a red dashed
cut-off line on the right (slab continues beyond the drawing). No
outer frame border.

Rendered with matplotlib -> PNG bytes (embeddable in Streamlit and in the
printable HTML report as a base64 data URI).
"""

import io
import math
import base64
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.ticker import FuncFormatter

LINE_COLOR = "black"
DIM_COLOR = "#0000CC"
JOINT_FILL = "#D98A2B"
DIVIDER_COLOR = "#D98A2B"
CAPTION_COLOR = "#1a7a1a"


def _fmt_m(x_m: float) -> str:
    """Structural-dimension format: metres, minimum 2 decimals, e.g.
    0.10 -> '0.10', 0.125 -> '0.125' (matches the reference drawing)."""
    s = f"{x_m:.3f}"
    if s.endswith("0"):
        s = s[:-1]
    return s


def _fmt_frac_m(x_m: float) -> str:
    """Negative-steel cut-off length format: metres, rounded HALF-UP to 2
    decimals then fully trimmed, e.g. 0.8333 -> '0.83', 0.625 -> '0.63',
    1.0 -> '1' (matches the reference drawing's '0.83 (L/3)' / '0.63 (L/4)'
    / '1 (L/3)' label style). Half-up rounding (not Python's banker's
    rounding) is used deliberately so 0.625 reads as 0.63, matching Excel's
    own rounding convention and the reference numbers exactly."""
    import math
    rounded = math.floor(x_m * 100.0 + 0.5) / 100.0
    s = f"{rounded:.2f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _fmt_spacing_m(x_m: float) -> str:
    """Rebar-spacing format: metres, fully trimmed, e.g. 0.20 -> '0.2'."""
    s = f"{x_m:.3f}".rstrip("0").rstrip(".")
    return s if s else "0"


def _dim_v(ax, x, y0, y1, tick_half=0.04):
    """Vertical dimension line at x, from y0 to y1, with short
    perpendicular tick marks at both ends (matches reference style)."""
    ax.plot([x, x], [y0, y1], color=DIM_COLOR, linewidth=1.0)
    ax.plot([x - tick_half, x + tick_half], [y0, y0], color=DIM_COLOR, linewidth=1.0)
    ax.plot([x - tick_half, x + tick_half], [y1, y1], color=DIM_COLOR, linewidth=1.0)


def _dim_h(ax, y, x0, x1, tick_half=0.04):
    """Horizontal dimension line at y, from x0 to x1, with short
    perpendicular tick marks at both ends (matches reference style)."""
    ax.plot([x0, x1], [y, y], color=DIM_COLOR, linewidth=1.0)
    ax.plot([x0, x0], [y - tick_half, y + tick_half], color=DIM_COLOR, linewidth=1.0)
    ax.plot([x1, x1], [y - tick_half, y + tick_half], color=DIM_COLOR, linewidth=1.0)


def draw_gs_detail_png(t_cm: float, bar_dia_mm: float, bar_spacing_cm: float,
                        sand_cm: float = 10.0, lean_cm: float = 5.0) -> bytes:
    """
    Draw a schematic cross-section of a slab-on-ground keyed joint at a
    wall, matching the user's reference Excel drawing exactly. Returns
    PNG image bytes.
    """
    t_m = t_cm / 100.0
    bar_spacing_m = bar_spacing_cm / 100.0
    sand_m = sand_cm / 100.0
    lean_m = lean_cm / 100.0

    # --- fixed schematic constants, taken directly from the reference
    #     Excel coordinate data (Detail Slabonground.xlsx) ---
    wall_w = 0.20
    wall_h = 0.50          # wall depicted depth is fixed, independent of t
    key_depth = 0.10
    joint_w = 0.015
    seg_w = 0.10
    slab_len = 1.75

    key_bot_y = -(t_m + key_depth)

    # --- x layout, left -> right: wall | joint | keyed step | flat slab | cut-off ---
    wall_left = 0.0
    wall_right = wall_left + wall_w
    wall_bot_y = -wall_h
    x_a = wall_right + joint_w       # key's outer (vertical) face
    x_b = x_a + seg_w                # end of shelf at key_bot_y
    x_c = x_b + seg_w                # end of diagonal taper, back at -t_m
    slab_end = x_c + slab_len        # cut-off point

    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=150)

    # --- Wall outline, no fill, no label ---
    ax.add_patch(patches.Rectangle(
        (wall_left, wall_bot_y), wall_w, (0 - wall_bot_y),
        fill=False, edgecolor=LINE_COLOR, linewidth=1.4))

    # --- Mastic joint sealer gap (filled strip, spans full key depth) ---
    ax.add_patch(patches.Rectangle((wall_right, key_bot_y), joint_w, (0 - key_bot_y),
                                    facecolor=JOINT_FILL, edgecolor=LINE_COLOR, linewidth=0.6))
    joint_cx = wall_right + joint_w / 2
    mastic_y = 0.34
    ax.plot([joint_cx, joint_cx, joint_cx + 0.09], [0, mastic_y, mastic_y],
            color=DIM_COLOR, linewidth=1.0)
    ax.annotate("", xy=(joint_cx, 0.012), xytext=(joint_cx, 0.05),
                arrowprops=dict(arrowstyle="-|>", lw=1.0, color=DIM_COLOR, mutation_scale=10))
    ax.text(joint_cx + 0.10, mastic_y, "Mastic Joint Sealer", fontsize=9, ha="left", va="center", color="black")

    # --- Slab top line (flat, from the joint all the way to the cut-off) ---
    ax.plot([x_a, slab_end], [0, 0], color=LINE_COLOR, linewidth=1.4)

    # --- Keyed notch (vertical drop -> shelf -> diagonal taper) + flat soffit ---
    ax.plot([x_a, x_a, x_b, x_c, slab_end],
            [0, key_bot_y, key_bot_y, -t_m, -t_m],
            color=LINE_COLOR, linewidth=1.4)

    # --- Reinforcement: black line with a hooked end + tick-dots, 2 call-outs ---
    rebar_y = -0.04
    hook_x = x_a + 0.03
    hook_bot_y = rebar_y - 0.155
    ax.plot([hook_x, slab_end], [rebar_y, rebar_y], color=LINE_COLOR, linewidth=1.1)
    ax.plot([hook_x, hook_x, hook_x + 0.05], [rebar_y, hook_bot_y, hook_bot_y],
            color=LINE_COLOR, linewidth=1.1)

    dot_y = rebar_y - 0.015
    n_ticks = max(int(slab_len / max(bar_spacing_m, 0.05)), 1)
    xs = [hook_x + 0.015 + i * bar_spacing_m for i in range(n_ticks)]
    xs = [x for x in xs if x < slab_end - 0.05]
    for x in xs:
        ax.add_patch(patches.Circle((x, dot_y), 0.008, color=LINE_COLOR, zorder=5))

    label = f"RB{bar_dia_mm:.0f}@{_fmt_spacing_m(bar_spacing_m)}"
    idx_a = min(2, len(xs) - 1) if xs else 0
    idx_b = min(idx_a + 1, len(xs) - 1) if xs else 0
    callout_y_a, callout_y_b = 0.24, 0.13
    if xs:
        x_dot_a = xs[idx_a]
        ax.annotate("", xy=(x_dot_a, dot_y), xytext=(x_dot_a, callout_y_a),
                    arrowprops=dict(arrowstyle="-|>", lw=1.0, color=LINE_COLOR,
                                     mutation_scale=10, shrinkA=0, shrinkB=0))
        ax.plot([x_dot_a, x_dot_a + 0.10], [callout_y_a, callout_y_a], color=LINE_COLOR, linewidth=1.0)
        ax.text(x_dot_a + 0.11, callout_y_a, label, fontsize=9.5, ha="left", va="center", color="black")

        if idx_b != idx_a:
            x_dot_b = xs[idx_b]
            ax.annotate("", xy=(x_dot_b, dot_y), xytext=(x_dot_b, callout_y_b),
                        arrowprops=dict(arrowstyle="-|>", lw=1.0, color=LINE_COLOR,
                                         mutation_scale=10, shrinkA=0, shrinkB=0))
            ax.plot([x_dot_b, x_dot_b + 0.10], [callout_y_b, callout_y_b], color=LINE_COLOR, linewidth=1.0)
            ax.text(x_dot_b + 0.11, callout_y_b, label, fontsize=9.5, ha="left", va="center", color="black")

    # --- Lean / Sand fill layers below the slab, labelled in blue ---
    fill_x0, fill_x1 = wall_right, slab_end
    lean_top_y = -t_m
    lean_bot_y = lean_top_y - lean_m
    sand_bot_y = lean_bot_y - sand_m
    divider_x0 = x_b + seg_w * 0.5

    ax.plot([divider_x0, fill_x1], [lean_bot_y, lean_bot_y], color=DIVIDER_COLOR, linewidth=1.0)
    ax.plot([fill_x0, fill_x1], [sand_bot_y, sand_bot_y], color="#999999", linewidth=0.8)

    ax.text(fill_x1 + 0.04, (lean_top_y + lean_bot_y) / 2, f"Lean {_fmt_m(lean_m)} m.",
            fontsize=8.5, va="center", ha="left", color=DIM_COLOR)
    ax.text(fill_x1 + 0.04, (lean_bot_y + sand_bot_y) / 2, f"Sand {_fmt_m(sand_m)} m.",
            fontsize=8.5, va="center", ha="left", color=DIM_COLOR)

    # --- Red dashed cut-off line (slab continues beyond drawing, to the right) ---
    cutoff_bottom = sand_bot_y - 0.05
    ax.plot([slab_end, slab_end], [0.05, cutoff_bottom], color="red",
            linewidth=1.0, linestyle=(0, (5, 3)))

    # --- Vertical dimension stack (blue, tick marks): t_m then key_depth ---
    dim_x = wall_left - 0.13
    _dim_v(ax, dim_x, 0, -t_m)
    ax.text(dim_x - 0.05, -t_m / 2, _fmt_m(t_m), fontsize=8.5, va="center", ha="right", color=DIM_COLOR)
    _dim_v(ax, dim_x, -t_m, key_bot_y)
    ax.text(dim_x - 0.05, -t_m - key_depth / 2, _fmt_m(key_depth), fontsize=8.5, va="center", ha="right", color=DIM_COLOR)

    # --- Horizontal dimension row below the wall (blue, tick marks): two key segments ---
    dim_y = wall_bot_y - 0.05
    _dim_h(ax, dim_y, x_a, x_b)
    ax.text((x_a + x_b) / 2 - 0.012, dim_y - 0.03, _fmt_m(seg_w), fontsize=7, ha="center", va="top", color=DIM_COLOR)
    _dim_h(ax, dim_y, x_b, x_c)
    ax.text((x_b + x_c) / 2 + 0.012, dim_y - 0.03, _fmt_m(seg_w), fontsize=7, ha="center", va="top", color=DIM_COLOR)

    # --- Green "Ground Slab" caption, centred below the drawing ---
    ax.text((x_a + slab_end) / 2, cutoff_bottom - 0.10, "Ground Slab",
            fontsize=12, ha="center", va="center", color=CAPTION_COLOR, fontweight="bold")

    ax.set_xlim(dim_x - 0.10, slab_end + 0.95)
    ax.set_ylim(cutoff_bottom - 0.20, 0.40)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def png_to_data_uri(png_bytes: bytes) -> str:
    b64 = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64}"


# ===========================================================================
# One-way Slab (พื้นทางเดียว) — detail drawings
#
# Geometry reverse-engineered the same way as the Ground Slab drawing: from
# the user's own reference file "One way Slab.xlsx", sheet "Drawing OW"
# (cross-section, chart6.xml) and sheet "One way Slab" charts 1-2 (plan
# view). Both are XY-scatter charts built from raw coordinate cells, read
# via openpyxl. Fixed schematic constants below (beam size, hook/embedment
# lengths, cut-off distance, drawn clear-span width) are taken directly
# from that source and kept independent of the real span S — same
# "schematic, not-to-scale, real values shown via labels" convention the
# reference itself uses (e.g. its own dimension line for clear span is
# labelled "1.50" even though the drawn line is a fixed 2.0m-equivalent
# width). Only the slab-thickness line, bar-count/spacing dots, and all
# text labels are driven by the real design values.
# ===========================================================================

OW_BEAM_W = 0.20
OW_BEAM_H = 0.40
OW_DRAWN_SPAN = 2.0          # schematic drawn clear span (not to scale vs real S)
OW_EMBED_BOT = 0.14          # main (bottom) bar embedment past beam face
OW_EMBED_TOP = 0.17          # top (negative-moment) bar embedment past beam face
OW_HOOK_DEPTH = 0.25         # top bar hook depth into the beam (from y=-0.03)
OW_CUTOFF_X = 0.5            # schematic drawn negative-moment bar cut-off distance
OW_TOP_BAR_Y = -0.03
OW_TOP_DOT_Y = -0.045
OW_COVER = 0.03


def _ow_elbow_leader(ax, x0, y0, y1, x1, label, color=LINE_COLOR, fontsize=9.5, ha="left",
                      fontproperties=None, linewidth=1.0, bbox=None):
    """Elbow leader: vertical segment (x0,y0)->(x0,y1) then horizontal to
    (x1,y1), label at the horizontal end — same convention as the Ground
    Slab callouts, confirmed against the One-way Slab reference leaders.
    fontproperties: pass THAI_FONT explicitly when label contains Thai text
    (e.g. the stair rebar-detail callouts) — defaults to None (matplotlib's
    default DejaVu Sans) to leave all existing English/numeric-label callers
    unaffected. linewidth: defaults to 1.0 (unchanged for existing callers) —
    stair callouts pass a bolder value to match the reference image's line weight.
    bbox: optional matplotlib text bbox dict (e.g. a highlight-color background) —
    defaults to None (no box) for all existing callers; used by the stair module
    to mark which callout values come from calculation vs. from stair-size input,
    per the reference "(6) แบบรายละเอียด" annotation style."""
    ax.plot([x0, x0], [y0, y1], color=color, linewidth=linewidth)
    ax.plot([x0, x1], [y1, y1], color=color, linewidth=linewidth)
    ax.text(x1 + (0.02 if ha == "left" else -0.02), y1, label, fontsize=fontsize,
             ha=ha, va="center", color="black", fontproperties=fontproperties, bbox=bbox)


def draw_ow_section_png(t_cm: float, main_bar_dia_mm: float, main_bar_spacing_cm: float,
                         temp_bar_dia_mm: float, temp_bar_spacing_cm: float,
                         S_m: float, end1_active: bool, end2_active: bool,
                         main_bar_type: str = "DB", temp_bar_type: str = "RB") -> bytes:
    """
    Cross-section at the slab supports (two beams, one each side) — used
    for Simply Supported / One End Continuous / Both Ends Continuous.
    end1_active / end2_active: whether negative-moment top steel is drawn
    at that end (per the selected continuity case).
    """
    t_m = t_cm / 100.0
    main_label = f"{main_bar_type}{main_bar_dia_mm:.0f}@{main_bar_spacing_cm:.0f}"
    temp_label = f"{temp_bar_type}{temp_bar_dia_mm:.0f}@{temp_bar_spacing_cm:.0f}"
    cutoff_len_m = S_m / 3.0

    span = OW_DRAWN_SPAN
    beam1_L, beam1_R = -OW_BEAM_W, 0.0
    beam2_L, beam2_R = span, span + OW_BEAM_W
    bottom_bar_y = -(t_m - OW_COVER)
    bottom_dot_y = bottom_bar_y + 0.015

    fig, ax = plt.subplots(figsize=(9.5, 4.6), dpi=150)

    # --- beams ---
    ax.add_patch(patches.Rectangle((beam1_L, -OW_BEAM_H), OW_BEAM_W, OW_BEAM_H,
                                    fill=False, edgecolor=LINE_COLOR, linewidth=1.4))
    ax.add_patch(patches.Rectangle((beam2_L, -OW_BEAM_H), OW_BEAM_W, OW_BEAM_H,
                                    fill=False, edgecolor=LINE_COLOR, linewidth=1.4))

    # --- slab top / bottom ---
    ax.plot([beam1_R, beam2_L], [0, 0], color=LINE_COLOR, linewidth=1.4)
    ax.plot([beam1_R, beam2_L], [-t_m, -t_m], color=LINE_COLOR, linewidth=1.4)

    # --- break marks near mid-span ---
    mid = span / 2.0
    ax.plot([mid - 0.015, mid - 0.015], [0.05, -t_m - 0.15], color=LINE_COLOR, linewidth=0.9)
    ax.plot([mid + 0.015, mid + 0.015], [0.05, -t_m - 0.15], color=LINE_COLOR, linewidth=0.9)

    # --- main (bottom / positive-moment) steel: full length + end ticks ---
    x0, x1 = beam1_R - OW_EMBED_BOT, beam2_L + OW_EMBED_BOT
    ax.plot([x0, x1], [bottom_bar_y, bottom_bar_y], color=LINE_COLOR, linewidth=1.1)
    ax.plot([x0, x0], [bottom_bar_y, bottom_bar_y + 0.04], color=LINE_COLOR, linewidth=1.1)
    ax.plot([x1, x1], [bottom_bar_y, bottom_bar_y + 0.04], color=LINE_COLOR, linewidth=1.1)

    # --- bottom distribution-bar dots (across full drawn width) ---
    spacing_m = max(temp_bar_spacing_cm / 100.0, 0.05)
    n = max(int(span / spacing_m), 1)
    bot_dot_xs = [i * spacing_m for i in range(n + 1) if i * spacing_m <= span]
    for x in bot_dot_xs:
        ax.add_patch(patches.Circle((x, bottom_dot_y), 0.008, color=LINE_COLOR, zorder=5))

    # --- top (negative-moment) steel + top dots, per active end ---
    # Leader anchors are taken from the ACTUAL drawn coordinates (bar-line
    # midpoint, and a real dot x from the same list used to draw the dots)
    # so the callout always points at a real feature, never a guessed offset.
    def draw_top_end(face_x, direction, dot_xs_source):
        # direction: +1 = extends to the RIGHT of face_x (left support),
        #            -1 = extends to the LEFT of face_x (right support)
        hook_x = face_x - direction * OW_EMBED_TOP
        cutoff_x = face_x + direction * OW_CUTOFF_X
        ax.plot([hook_x, cutoff_x], [OW_TOP_BAR_Y, OW_TOP_BAR_Y], color=LINE_COLOR, linewidth=1.1)
        ax.plot([hook_x, hook_x], [OW_TOP_BAR_Y, -OW_HOOK_DEPTH], color=LINE_COLOR, linewidth=1.1)
        # dots near this end only (within ~0.45m of the beam face)
        near_dots = sorted([x for x in dot_xs_source if abs(x - face_x) <= 0.45])
        for x in near_dots:
            ax.add_patch(patches.Circle((x, OW_TOP_DOT_Y), 0.008, color=LINE_COLOR, zorder=5))
        bar_anchor_x = (hook_x + cutoff_x) / 2.0                          # guaranteed on the bar line
        dot_anchor_x = near_dots[len(near_dots) // 2] if near_dots else None   # a real dot, if any
        return bar_anchor_x, dot_anchor_x

    if end1_active:
        bar_anchor_x, dot_anchor_x = draw_top_end(beam1_R, +1, bot_dot_xs)
        _ow_elbow_leader(ax, bar_anchor_x, OW_TOP_BAR_Y, 0.20, bar_anchor_x + 0.10, main_label, ha="left")
        if dot_anchor_x is not None:
            _ow_elbow_leader(ax, dot_anchor_x, OW_TOP_DOT_Y, 0.105, dot_anchor_x + 0.10, temp_label, ha="left")
    if end2_active:
        bar_anchor_x, dot_anchor_x = draw_top_end(beam2_L, -1, bot_dot_xs)
        _ow_elbow_leader(ax, bar_anchor_x, OW_TOP_BAR_Y, 0.20, bar_anchor_x + 0.10, main_label, ha="left")
        if dot_anchor_x is not None:
            _ow_elbow_leader(ax, dot_anchor_x, OW_TOP_DOT_Y, 0.105, dot_anchor_x + 0.10, temp_label, ha="left")

    # --- bottom callouts (main + temp), once near mid-left of drawn slab ---
    bottom_bar_anchor_x = mid - 0.5                    # on the continuous bottom bar line
    dot_candidates = [x for x in bot_dot_xs if x < mid - 0.05]   # keep clear of the break marks
    bottom_dot_anchor_x = min(dot_candidates, key=lambda x: abs(x - bottom_bar_anchor_x)) if dot_candidates else None
    _ow_elbow_leader(ax, bottom_bar_anchor_x, bottom_bar_y, bottom_bar_y - 0.23, bottom_bar_anchor_x + 0.20,
                      main_label, ha="left")
    if bottom_dot_anchor_x is not None:
        _ow_elbow_leader(ax, bottom_dot_anchor_x, bottom_dot_y, bottom_dot_y - 0.15, bottom_dot_anchor_x + 0.20,
                          temp_label, ha="left")

    # --- dimension: slab thickness t (left of beam1) ---
    dim_x = beam1_L - 0.13
    _dim_v(ax, dim_x, 0, -t_m)
    ax.text(dim_x - 0.05, -t_m / 2, f"t={_fmt_m(t_m)}", fontsize=8.5, va="center", ha="right", color=DIM_COLOR)

    # --- dimension: negative-moment cut-off length, each active end (closest row) ---
    cdim_y = -OW_BEAM_H - 0.10
    if end1_active:
        _dim_h(ax, cdim_y, beam1_R, beam1_R + OW_CUTOFF_X)
        ax.text(beam1_R + OW_CUTOFF_X / 2, cdim_y - 0.03, f"{_fmt_m(cutoff_len_m)} (S/3)",
                fontsize=7, ha="center", va="top", color=DIM_COLOR)
    if end2_active:
        _dim_h(ax, cdim_y, beam2_L - OW_CUTOFF_X, beam2_L)
        ax.text(beam2_L - OW_CUTOFF_X / 2, cdim_y - 0.03, f"{_fmt_m(cutoff_len_m)} (S/3)",
                fontsize=7, ha="center", va="top", color=DIM_COLOR)

    # --- dimension: clear span S (below the cut-off row) ---
    dim_y = -OW_BEAM_H - 0.24
    _dim_h(ax, dim_y, beam1_R, beam2_L)
    ax.text(mid, dim_y - 0.05, f"S = {_fmt_m(S_m)} m.", fontsize=9, ha="center", va="top", color=DIM_COLOR)

    ax.text(mid, dim_y - 0.20, "One Way Slab", fontsize=12, ha="center", va="center",
            color=CAPTION_COLOR, fontweight="bold")

    ax.set_xlim(dim_x - 0.10, span + OW_BEAM_W + 0.95)
    ax.set_ylim(dim_y - 0.32, 0.42)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ===========================================================================
# Cantilever Slab (พื้นยื่น, module 1.4) — detail drawings
#
# Geometry reverse-engineered from the user's reference "Cantiliver Slab.xlsx"
# (sheet "Calculation CS" chart2 = cross-section, sheet "Cantiliver Slab"
# chart1 = plan) via zipfile/ElementTree, same technique as every other
# module. Beam size (0.20x0.40), top-bar embedment-past-face (0.17), cover
# (0.03) are IDENTICAL to the OW_* constants reused everywhere else — only
# the hook depth is measured slightly differently here (see below).
#
# Key finding that made the ORIGINAL (pre-2026-07, speculative) cantilever
# section function wrong: a cantilever only has ONE reinforcement mat — TOP
# — for BOTH the main (flexural, negative-moment) bar and the secondary/
# temperature bar (shown as crossing dots). There is no separate bottom bar
# at all (tension is entirely on top at the fixed support; the reference
# drawing confirms this — the secondary-bar dots sit at y=-0.045, right next
# to the main bar's y=-0.03, not near the slab soffit). The corrected
# functions below replace the old (now-deleted) draw_ow_cantilever_section_png.
# ===========================================================================

CANT_DRAWN_SPAN = 1.0   # schematic drawn projection length (not to scale vs real S)


def draw_cant_section_png(S_m: float, t_cm: float,
                           main_bar_dia_mm: float, main_bar_spacing_cm: float, main_bar_type: str,
                           temp_bar_dia_mm: float, temp_bar_spacing_cm: float, temp_bar_type: str) -> bytes:
    """
    Cantilever slab cross-section: one fixed support (beam) on the left,
    slab projecting out to a free (solid) edge on the right. Top steel
    (both main + secondary/temperature, both in the SAME top mat) runs the
    full projection length from the fixed end, hooked down into the beam,
    stopping just short of the free tip (cover clearance only — confirmed
    "top_end_x = tip - cover" from the reference chart). No bottom bar.
    """
    t_m = t_cm / 100.0
    main_label = f"{main_bar_type}{main_bar_dia_mm:.0f}@{main_bar_spacing_cm:.0f}"
    temp_label = f"{temp_bar_type}{temp_bar_dia_mm:.0f}@{temp_bar_spacing_cm:.0f}"

    span = CANT_DRAWN_SPAN
    beam_L, beam_R = -OW_BEAM_W, 0.0
    tip_x = span

    fig, ax = plt.subplots(figsize=(8.5, 4.4), dpi=150)

    # --- beam (fixed support, left only — free tip has no beam) ---
    ax.add_patch(patches.Rectangle((beam_L, -OW_BEAM_H), OW_BEAM_W, OW_BEAM_H,
                                    fill=False, edgecolor=LINE_COLOR, linewidth=1.4))

    # --- slab top / bottom / free edge (solid — slab genuinely ends here) ---
    ax.plot([beam_R, tip_x], [0, 0], color=LINE_COLOR, linewidth=1.4)
    ax.plot([beam_R, tip_x], [-t_m, -t_m], color=LINE_COLOR, linewidth=1.4)
    ax.plot([tip_x, tip_x], [0, -t_m], color=LINE_COLOR, linewidth=1.4)

    # --- top steel (main, negative-moment) — hooked into beam, full length to (tip - cover) ---
    hook_x = beam_R - OW_EMBED_TOP
    top_end_x = tip_x - OW_COVER
    ax.plot([hook_x, top_end_x], [OW_TOP_BAR_Y, OW_TOP_BAR_Y], color=LINE_COLOR, linewidth=1.1)
    ax.plot([hook_x, hook_x], [OW_TOP_BAR_Y, OW_TOP_BAR_Y - OW_HOOK_DEPTH], color=LINE_COLOR, linewidth=1.1)
    # end tick at the tip (confirmed small vertical tick in the reference, "เหล็กบนขวา")
    ax.plot([top_end_x, top_end_x], [OW_TOP_BAR_Y, OW_TOP_BAR_Y - 0.04], color=LINE_COLOR, linewidth=1.1)

    # --- secondary/temperature steel, seen end-on as dots — SAME top mat, not bottom ---
    spacing_m = max(temp_bar_spacing_cm / 100.0, 0.05)
    n = max(int(span / spacing_m), 1)
    dot_xs = [i * spacing_m for i in range(n + 1) if i * spacing_m <= span - OW_COVER]
    for x in dot_xs:
        ax.add_patch(patches.Circle((x, OW_TOP_DOT_Y), 0.008, color=LINE_COLOR, zorder=5))

    bar_anchor_x = (hook_x + top_end_x) / 2.0
    dot_anchor_x = dot_xs[len(dot_xs) // 2] if dot_xs else None
    _ow_elbow_leader(ax, bar_anchor_x, OW_TOP_BAR_Y, 0.20, bar_anchor_x + 0.10, main_label, ha="left")
    if dot_anchor_x is not None:
        _ow_elbow_leader(ax, dot_anchor_x, OW_TOP_DOT_Y, 0.105, dot_anchor_x + 0.10, temp_label, ha="left")

    # --- dimension: slab thickness t (near the free tip — no beam on the right to clash with) ---
    dim_x = tip_x + 0.15
    _dim_v(ax, dim_x, 0, -t_m)
    ax.text(dim_x + 0.05, -t_m / 2, f"t={_fmt_m(t_m)}", fontsize=8.5, va="center", ha="left", color=DIM_COLOR)

    # --- dimension: cantilever projection S ---
    dim_y = -OW_BEAM_H - 0.15
    _dim_h(ax, dim_y, beam_R, tip_x)
    ax.text((beam_R + tip_x) / 2, dim_y - 0.05, f"S = {_fmt_m(S_m)} m. (Cantilever)", fontsize=9,
            ha="center", va="top", color=DIM_COLOR)

    ax.text((beam_R + tip_x) / 2, dim_y - 0.20, "Cantilever Slab — Section", fontsize=11.5,
            ha="center", va="center", color=CAPTION_COLOR, fontweight="bold")

    ax.set_xlim(beam_L - 0.15, dim_x + 0.65)
    ax.set_ylim(dim_y - 0.32, 0.35)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_cant_plan_png(S_m: float,
                        main_bar_dia_mm: float, main_bar_spacing_cm: float, main_bar_type: str,
                        temp_bar_dia_mm: float, temp_bar_spacing_cm: float, temp_bar_type: str) -> bytes:
    """
    Plan-view rebar layout for a cantilever slab strip — reverse-engineered
    from chart1 on the "Cantiliver Slab" sheet: a support wall/beam strip
    along the TOP edge, slab projecting DOWN (S direction, drawn vertically)
    to a free edge at the bottom. Main bar (top, negative-moment) runs in
    the S direction (drawn as vertical representative lines); secondary/
    temperature bar runs parallel to the wall (drawn as a horizontal
    representative line). The wall-parallel extent is schematic only (this
    app designs a per-metre-width strip — there is no real "L" input), shown
    with a "repeats along the wall" note instead of a fabricated dimension.
    """
    main_label = f"{main_bar_type}{main_bar_dia_mm:.0f}@{main_bar_spacing_cm:.0f}"
    temp_label = f"{temp_bar_type}{temp_bar_dia_mm:.0f}@{temp_bar_spacing_cm:.0f}"

    W = 2.0    # drawn width along the wall (schematic, repeats)
    H = 1.2    # drawn projection depth (S direction)
    WALL_T = 0.15

    fig, ax = plt.subplots(figsize=(8.0, 6.4), dpi=150)

    # --- support wall/beam strip along the top edge ---
    ax.add_patch(patches.Rectangle((-0.1, H), W + 0.2, WALL_T, facecolor="#dddddd",
                                    edgecolor=LINE_COLOR, linewidth=1.2, hatch="////"))
    ax.text(W / 2.0, H + WALL_T + 0.10, "Wall / Beam (Fixed Support)", fontsize=8.5,
            ha="center", va="bottom", color="black")

    # --- slab outline (free tip at the bottom, solid line — genuinely ends there) ---
    ax.add_patch(patches.Rectangle((0, 0), W, H, fill=False, edgecolor=LINE_COLOR, linewidth=1.6))

    # --- main bar (top mat, runs in S direction) — a FEW representative vertical lines only
    # (typical-bar-shown convention, same as the One-way/Two-way plans — NOT a literal
    # spacing-accurate grid, which got too cluttered on the first render at real spacing) ---
    xs = [W * f for f in (0.25, 0.5, 0.75)]
    for x in xs:
        ax.plot([x, x], [0, H], color=LINE_COLOR, linewidth=1.1, zorder=4)
    label_x = xs[1]
    ax.annotate(main_label, xy=(label_x, H * 0.65), xytext=(label_x + 0.35, H * 0.65),
                fontsize=9, ha="left", va="center", color="black",
                arrowprops=dict(arrowstyle="-", color=LINE_COLOR, linewidth=0.9))

    # --- secondary/temperature bar (parallel to wall) — one representative horizontal line ---
    temp_y = H * 0.25
    ax.plot([0, W], [temp_y, temp_y], color=LINE_COLOR, linewidth=1.1, linestyle=(0, (5, 3)), zorder=4)
    ax.annotate(temp_label, xy=(W * 0.25, temp_y), xytext=(W * 0.25, temp_y - 0.18),
                fontsize=9, ha="center", va="top", color="black",
                arrowprops=dict(arrowstyle="-", color=LINE_COLOR, linewidth=0.9))

    # --- dimension: S (vertical, left side, real value) ---
    dim_x = -0.45
    _dim_v(ax, dim_x, H, 0)
    ax.text(dim_x - 0.05, H / 2, f"S = {_fmt_m(S_m)} m.", fontsize=9.5, va="center", ha="right",
            color=DIM_COLOR, rotation=90)

    ax.text(W / 2.0, -0.30, "(repeats along the wall, per 1 m. width strip)", fontsize=8,
            ha="center", va="top", color="#666666", style="italic")

    ax.text(W / 2.0, H + WALL_T + 0.40, "Cantilever Slab — Reinforcement Plan", fontsize=12.5,
            ha="center", va="center", color=CAPTION_COLOR, fontweight="bold")

    ax.set_xlim(dim_x - 0.35, W + 0.35)
    ax.set_ylim(-0.55, H + WALL_T + 0.65)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_ow_plan_png(main_bar_dia_mm: float, main_bar_spacing_cm: float,
                      temp_bar_dia_mm: float, temp_bar_spacing_cm: float,
                      S_m: float, L_m: float, end1_active: bool, end2_active: bool,
                      main_bar_type: str = "DB", temp_bar_type: str = "RB") -> bytes:
    """
    Plan-view (top-view) rebar layout — reverse-engineered from charts 1-2
    on the "One way Slab" sheet. Slab panel drawn schematically 2.0 x 1.5
    (S runs vertically, L runs horizontally — matches the reference, which
    also keeps this fixed regardless of the real S/L, labelling the real
    values via dimension lines instead). One representative main bar
    (vertical, spans S) and one representative distribution/temperature
    bar (horizontal, spans L) are drawn — standard "typical bar shown,
    repeat at spacing" convention, since drawing every individual bar at
    an arbitrary spacing is impractical.
    """
    main_label = f"{main_bar_type}{main_bar_dia_mm:.0f}@{main_bar_spacing_cm:.0f}"
    temp_label = f"{temp_bar_type}{temp_bar_dia_mm:.0f}@{temp_bar_spacing_cm:.0f}"

    W, H = 2.0, 1.5   # drawn plan width (~L direction) / height (~S direction)

    fig, ax = plt.subplots(figsize=(8.5, 6.0), dpi=150)

    # inner slab edge + outer (beam centreline) edge
    ax.add_patch(patches.Rectangle((0, 0), W, H, fill=False, edgecolor=LINE_COLOR, linewidth=1.4))
    ax.add_patch(patches.Rectangle((-0.1, -0.1), W + 0.2, H + 0.2, fill=False,
                                    edgecolor="#888888", linewidth=0.8, linestyle=(0, (4, 3))))

    # outer reference lines (frame)
    ax.plot([-0.1, W + 0.1], [H + 0.15, H + 0.15], color="#bbbbbb", linewidth=0.7)
    ax.plot([-0.1, W + 0.1], [-0.15, -0.15], color="#bbbbbb", linewidth=0.7)

    mid_x = W / 2.0

    # representative main bar (vertical, spans S) — embeds past each active edge
    top_y = H + (0.10 if end2_active else 0.02)
    bot_y = -(0.10 if end1_active else 0.02)
    ax.plot([mid_x, mid_x], [bot_y, top_y], color=LINE_COLOR, linewidth=1.3)

    # representative distribution/temperature bar (horizontal, spans L)
    mid_y = H / 2.0
    ax.plot([-0.1, W + 0.1], [mid_y, mid_y], color=LINE_COLOR, linewidth=1.1)

    # negative-moment top-steel bands near active edges, with their own cut-off line
    if end1_active:
        ax.plot([-0.1, W + 0.1], [0.10, 0.10], color=LINE_COLOR, linewidth=1.1)
        ax.plot([-0.1, W + 0.1], [0.20, 0.20], color="#999999", linewidth=0.7)
        _ow_elbow_leader(ax, mid_x - 0.35, 0.10, -0.35, mid_x - 0.25, main_label, ha="left")
        _ow_elbow_leader(ax, mid_x - 0.35, mid_y, mid_y - 0.30, mid_x - 0.25, temp_label, ha="left")
    if end2_active:
        ax.plot([-0.1, W + 0.1], [H - 0.10, H - 0.10], color=LINE_COLOR, linewidth=1.1)
        ax.plot([-0.1, W + 0.1], [H - 0.20, H - 0.20], color="#999999", linewidth=0.7)
        _ow_elbow_leader(ax, mid_x + 0.35, H - 0.10, H + 0.35, mid_x + 0.25, main_label, ha="right")

    # labels for the representative bars themselves
    ax.text(mid_x + 0.06, mid_y + 0.35, main_label, fontsize=9.5, ha="left", va="center", color="black")
    ax.text(mid_x + 0.55, mid_y + 0.06, temp_label, fontsize=9.5, ha="left", va="bottom", color="black")

    # dimension: S (vertical, left side) and L (horizontal, bottom)
    dim_x = -0.45
    _dim_v(ax, dim_x, 0, H)
    ax.text(dim_x - 0.05, H / 2, f"S = {_fmt_m(S_m)} m.", fontsize=9, va="center", ha="right",
            color=DIM_COLOR, rotation=90)

    dim_y = -0.45
    _dim_h(ax, dim_y, 0, W)
    ax.text(mid_x, dim_y - 0.05, f"L = {_fmt_m(L_m)} m.", fontsize=9, ha="center", va="top", color=DIM_COLOR)

    ax.text(mid_x, H + 0.45, "One Way Slab — Reinforcement Plan", fontsize=11.5, ha="center",
            va="center", color=CAPTION_COLOR, fontweight="bold")

    ax.set_xlim(dim_x - 0.35, W + 0.9)
    ax.set_ylim(dim_y - 0.30, H + 0.65)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ===========================================================================
# Two-way Slab (พื้นสองทาง) — detail drawings
#
# Geometry reverse-engineered from the user's reference "Two way Slab.xlsx",
# sheet "Drawing TW" (cross-sections: chart7.xml = short-direction cut,
# chart8.xml = long-direction cut — both XY-scatter charts, read via
# zipfile/ElementTree the same way as the One-way Slab charts) and sheet
# "Two way Slab" charts 3-4 (plan view: chart3 = top-steel layer at all 4
# edges, chart4 = bottom-mesh layer, both directions). Confirmed the
# schematic constants (beam size 0.20x0.40, top-bar embedment-past-face
# 0.17, hook depth 0.25, cover 0.03, drawn span 2.0, drawn cut-off extent
# 0.5) are IDENTICAL to the One-way Slab drawing's OW_* constants — reused
# directly rather than re-declared.
#
# One thing the reference workbook could NOT tell us: which specific edges
# are continuous vs discontinuous for cases other than its own one worked
# example (short direction: one continuous end + one discontinuous end
# with reduced/minimum top steel at span/4 instead of span/3; long
# direction: both ends continuous at span/3 — matches the confirmed
# CASE2 moment coefficients exactly, where Con- and Disc- are both active
# for the short direction but only Con- is active for the long direction).
# So continuity per end here is driven by the REAL selected case's
# DirectionPositionResult.active flags (Con-/Disc- position), not hardcoded
# from the reference example — see draw_tw_section_png's end1_state/
# end2_state parameters ("continuous" / "discontinuous" / "none").
# "none" (no top steel at all) is used when BOTH edges of a direction are
# discontinuous (e.g. CASE5) — the standard ACI 318-63 coefficient table
# gives a genuinely zero negative-moment coefficient there, confirmed by
# the con-=0 pattern already documented in modules/two_way_slab.py.
# ===========================================================================


def _tw_cutoff_label(direction_label: str, span_m: float, state: str):
    """Embedment-length label for the negative-steel cut-off dimension:
    span/3 at a continuous edge (full design negative moment), span/4 at a
    discontinuous edge (ACI 318-63 minimum/nominal top steel provision —
    confirmed against the reference drawing's own '0.83 (L/3)' / '0.63
    (L/4)' pair, where 'L' in the source is just a generic per-cut span
    label, not the panel's long side — relabelled here using this app's
    own S/L terminology for the direction actually being cut)."""
    if state == "continuous":
        return f"{_fmt_frac_m(span_m / 3.0)} ({direction_label}/3)"
    if state == "discontinuous":
        return f"{_fmt_frac_m(span_m / 4.0)} ({direction_label}/4)"
    return None


def draw_tw_section_png(direction_label: str, span_m: float, t_cm: float,
                         bar_dia_mm: float, bar_spacing_cm: float, bar_type: str,
                         cross_bar_dia_mm: float, cross_bar_spacing_cm: float, cross_bar_type: str,
                         end1_state: str = "continuous", end2_state: str = "continuous") -> bytes:
    """
    Two-way slab cross-section cut along ONE direction (call once for the
    short-direction cut with span_m=S, once for the long-direction cut with
    span_m=L). This direction's own bars are drawn as continuous top/bottom
    lines (top steel only where end*_state != "none"); the CROSSING
    direction's bars are seen end-on and drawn as dots (same convention as
    the One-way Slab section's main-bar/temp-bar split).

    end1_state / end2_state: "continuous" (full negative steel, span/3
    embedment), "discontinuous" (minimum top steel per ACI 318-63, span/4
    embedment), or "none" (no top steel — both edges of this direction are
    discontinuous, con-=0 per the moment-coefficient table).
    """
    t_m = t_cm / 100.0
    main_label = f"{bar_type}{bar_dia_mm:.0f}@{bar_spacing_cm:.0f}"
    cross_label = f"{cross_bar_type}{cross_bar_dia_mm:.0f}@{cross_bar_spacing_cm:.0f}"

    span = OW_DRAWN_SPAN
    beam1_L, beam1_R = -OW_BEAM_W, 0.0
    beam2_L, beam2_R = span, span + OW_BEAM_W
    bottom_bar_y = -(t_m - OW_COVER)
    bottom_dot_y = bottom_bar_y + 0.015

    fig, ax = plt.subplots(figsize=(9.5, 4.6), dpi=150)

    # --- beams ---
    ax.add_patch(patches.Rectangle((beam1_L, -OW_BEAM_H), OW_BEAM_W, OW_BEAM_H,
                                    fill=False, edgecolor=LINE_COLOR, linewidth=1.4))
    ax.add_patch(patches.Rectangle((beam2_L, -OW_BEAM_H), OW_BEAM_W, OW_BEAM_H,
                                    fill=False, edgecolor=LINE_COLOR, linewidth=1.4))

    # --- slab top / bottom ---
    ax.plot([beam1_R, beam2_L], [0, 0], color=LINE_COLOR, linewidth=1.4)
    ax.plot([beam1_R, beam2_L], [-t_m, -t_m], color=LINE_COLOR, linewidth=1.4)

    # --- break marks near mid-span ---
    mid = span / 2.0
    ax.plot([mid - 0.015, mid - 0.015], [0.05, -t_m - 0.15], color=LINE_COLOR, linewidth=0.9)
    ax.plot([mid + 0.015, mid + 0.015], [0.05, -t_m - 0.15], color=LINE_COLOR, linewidth=0.9)

    # --- this direction's positive-moment (bottom) steel: full length + end ticks ---
    x0, x1 = beam1_R - OW_EMBED_BOT, beam2_L + OW_EMBED_BOT
    ax.plot([x0, x1], [bottom_bar_y, bottom_bar_y], color=LINE_COLOR, linewidth=1.1)
    ax.plot([x0, x0], [bottom_bar_y, bottom_bar_y + 0.04], color=LINE_COLOR, linewidth=1.1)
    ax.plot([x1, x1], [bottom_bar_y, bottom_bar_y + 0.04], color=LINE_COLOR, linewidth=1.1)

    # --- crossing-direction bars, seen end-on as dots (full drawn width) ---
    spacing_m = max(cross_bar_spacing_cm / 100.0, 0.05)
    n = max(int(span / spacing_m), 1)
    bot_dot_xs = [i * spacing_m for i in range(n + 1) if i * spacing_m <= span]
    for x in bot_dot_xs:
        ax.add_patch(patches.Circle((x, bottom_dot_y), 0.008, color=LINE_COLOR, zorder=5))

    def draw_top_end(face_x, direction, dot_xs_source):
        hook_x = face_x - direction * OW_EMBED_TOP
        cutoff_x = face_x + direction * OW_CUTOFF_X
        ax.plot([hook_x, cutoff_x], [OW_TOP_BAR_Y, OW_TOP_BAR_Y], color=LINE_COLOR, linewidth=1.1)
        ax.plot([hook_x, hook_x], [OW_TOP_BAR_Y, -OW_HOOK_DEPTH], color=LINE_COLOR, linewidth=1.1)
        near_dots = sorted([x for x in dot_xs_source if abs(x - face_x) <= 0.45])
        for x in near_dots:
            ax.add_patch(patches.Circle((x, OW_TOP_DOT_Y), 0.008, color=LINE_COLOR, zorder=5))
        bar_anchor_x = (hook_x + cutoff_x) / 2.0
        dot_anchor_x = near_dots[len(near_dots) // 2] if near_dots else None
        return bar_anchor_x, dot_anchor_x

    cdim_y = -OW_BEAM_H - 0.10
    if end1_state != "none":
        bar_anchor_x, dot_anchor_x = draw_top_end(beam1_R, +1, bot_dot_xs)
        _ow_elbow_leader(ax, bar_anchor_x, OW_TOP_BAR_Y, 0.20, bar_anchor_x + 0.10, main_label, ha="left")
        if dot_anchor_x is not None:
            _ow_elbow_leader(ax, dot_anchor_x, OW_TOP_DOT_Y, 0.105, dot_anchor_x + 0.10, cross_label, ha="left")
        _dim_h(ax, cdim_y, beam1_R, beam1_R + OW_CUTOFF_X)
        lbl1 = _tw_cutoff_label(direction_label, span_m, end1_state)
        ax.text(beam1_R + OW_CUTOFF_X / 2, cdim_y - 0.03, lbl1, fontsize=7, ha="center", va="top", color=DIM_COLOR)
    if end2_state != "none":
        bar_anchor_x, dot_anchor_x = draw_top_end(beam2_L, -1, bot_dot_xs)
        _ow_elbow_leader(ax, bar_anchor_x, OW_TOP_BAR_Y, 0.20, bar_anchor_x + 0.10, main_label, ha="left")
        if dot_anchor_x is not None:
            _ow_elbow_leader(ax, dot_anchor_x, OW_TOP_DOT_Y, 0.105, dot_anchor_x + 0.10, cross_label, ha="left")
        _dim_h(ax, cdim_y, beam2_L - OW_CUTOFF_X, beam2_L)
        lbl2 = _tw_cutoff_label(direction_label, span_m, end2_state)
        ax.text(beam2_L - OW_CUTOFF_X / 2, cdim_y - 0.03, lbl2, fontsize=7, ha="center", va="top", color=DIM_COLOR)

    # --- bottom callouts (this direction's bar + crossing bar), once near mid-left ---
    bottom_bar_anchor_x = mid - 0.5
    dot_candidates = [x for x in bot_dot_xs if x < mid - 0.05]
    bottom_dot_anchor_x = min(dot_candidates, key=lambda x: abs(x - bottom_bar_anchor_x)) if dot_candidates else None
    _ow_elbow_leader(ax, bottom_bar_anchor_x, bottom_bar_y, bottom_bar_y - 0.23, bottom_bar_anchor_x + 0.20,
                      main_label, ha="left")
    if bottom_dot_anchor_x is not None:
        _ow_elbow_leader(ax, bottom_dot_anchor_x, bottom_dot_y, bottom_dot_y - 0.15, bottom_dot_anchor_x + 0.20,
                          cross_label, ha="left")

    # --- dimension: slab thickness t (left of beam1) ---
    dim_x = beam1_L - 0.13
    _dim_v(ax, dim_x, 0, -t_m)
    ax.text(dim_x - 0.05, -t_m / 2, f"t={_fmt_m(t_m)}", fontsize=8.5, va="center", ha="right", color=DIM_COLOR)

    # --- dimension: clear span (below the cut-off row) ---
    dim_y = -OW_BEAM_H - 0.24
    _dim_h(ax, dim_y, beam1_R, beam2_L)
    ax.text(mid, dim_y - 0.05, f"{direction_label} = {_fmt_m(span_m)} m.", fontsize=9,
            ha="center", va="top", color=DIM_COLOR)

    ax.text(mid, dim_y - 0.20, f"Two Way Slab — {direction_label} Direction Section", fontsize=11.5,
            ha="center", va="center", color=CAPTION_COLOR, fontweight="bold")

    ax.set_xlim(dim_x - 0.10, span + OW_BEAM_W + 0.95)
    ax.set_ylim(dim_y - 0.32, 0.42)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_tw_plan_png(S_m: float, L_m: float,
                      short_bar_dia_mm: float, short_bar_spacing_cm: float, short_bar_type: str,
                      long_bar_dia_mm: float, long_bar_spacing_cm: float, long_bar_type: str,
                      s_end1_state: str = "continuous", s_end2_state: str = "continuous",
                      l_end1_state: str = "continuous", l_end2_state: str = "continuous") -> bytes:
    """
    Plan-view rebar layout for a two-way slab panel, split into two
    side-by-side diagrams — "Top Bars" (negative-moment steel, banded
    inward from each active edge by span/3 or span/4 per that end's real
    continuity state) and "Bottom Bars" (positive-moment mesh, continuous
    across the whole panel) — matching the reference software's split-panel
    "Slab Diagram" layout (2026-07 feedback: user asked for this same
    layout style instead of one combined plan). S is drawn vertically, L
    horizontally: top/bottom edges are the short-direction (S) end
    supports, left/right edges are the long-direction (L) end supports —
    same convention as draw_tw_section_png and the rest of this module.
    """
    short_label = f"{short_bar_type}{short_bar_dia_mm:.0f}@{short_bar_spacing_cm:.0f}"
    long_label = f"{long_bar_type}{long_bar_dia_mm:.0f}@{long_bar_spacing_cm:.0f}"

    W, H = 2.2, 1.6   # drawn plan width (~L direction) / height (~S direction)
    BAND_CONT = 0.34   # drawn band depth, continuous edge (full negative steel)
    BAND_DISC = 0.20   # drawn band depth, discontinuous edge (minimum top steel)
    BAND_FILL = "#f4d9a0"
    mid_x, mid_y = W / 2.0, H / 2.0

    fig, (axT, axB) = plt.subplots(1, 2, figsize=(15.5, 7.8), dpi=150)

    # --- highlight ขอบด้านที่ต่อเนื่อง (fixed/continuous edge) — ผู้ใช้ขอเพิ่ม 2026-07-12 ---
    # เส้นหนาสีเขียวเข้มเยื้องออกนอกกรอบเล็กน้อยที่ขอบซึ่งต่อเนื่อง (ขอบบน=s_end2, ขอบล่าง=s_end1,
    # ขอบขวา=l_end2, ขอบซ้าย=l_end1 — ตามระบบพิกัดเดียวกับ s_band/l_band)
    HL_COLOR = "#2E7D32"
    HL_OFF = 0.055

    def _hl_continuous_edges(ax):
        drew = False
        if s_end2_state == "continuous":          # ขอบบน (แนวราบ)
            ax.plot([0, W], [H + HL_OFF, H + HL_OFF], color=HL_COLOR, linewidth=5.0,
                    solid_capstyle="butt", zorder=7); drew = True
        if s_end1_state == "continuous":          # ขอบล่าง
            ax.plot([0, W], [-HL_OFF, -HL_OFF], color=HL_COLOR, linewidth=5.0,
                    solid_capstyle="butt", zorder=7); drew = True
        if l_end2_state == "continuous":          # ขอบขวา (แนวตั้ง)
            ax.plot([W + HL_OFF, W + HL_OFF], [0, H], color=HL_COLOR, linewidth=5.0,
                    solid_capstyle="butt", zorder=7); drew = True
        if l_end1_state == "continuous":          # ขอบซ้าย
            ax.plot([-HL_OFF, -HL_OFF], [0, H], color=HL_COLOR, linewidth=5.0,
                    solid_capstyle="butt", zorder=7); drew = True
        return drew

    # ===================== LEFT PANEL: Top Bars =====================
    ax = axT
    ax.add_patch(patches.Rectangle((0, 0), W, H, fill=False, edgecolor=LINE_COLOR, linewidth=1.6, zorder=3))
    _hl_continuous_edges(axT)

    def bar_ticks_h(y0, depth, from_top):
        # short vertical tick marks inside a top/bottom band -> S-direction bars
        y_edge = H if from_top else 0.0
        y_in = y0 if from_top else y0 + depth
        for f in (0.12, 0.28, 0.44, 0.56, 0.72, 0.88):
            x = W * f
            ax.plot([x, x], [y_edge, y_in], color=LINE_COLOR, linewidth=0.9, zorder=4)

    def bar_ticks_v(x0, depth, from_right):
        # short horizontal tick marks inside a left/right band -> L-direction bars
        x_edge = W if from_right else 0.0
        x_in = x0 if from_right else x0 + depth
        for f in (0.15, 0.35, 0.5, 0.65, 0.85):
            y = H * f
            ax.plot([x_edge, x_in], [y, y], color=LINE_COLOR, linewidth=0.9, zorder=4)

    def s_band(from_top, state):
        if state == "none":
            return
        depth = BAND_CONT if state == "continuous" else BAND_DISC
        y0 = (H - depth) if from_top else 0.0
        ax.add_patch(patches.Rectangle((0, y0), W, depth, facecolor=BAND_FILL,
                                        edgecolor=LINE_COLOR, linewidth=1.0, zorder=2))
        bar_ticks_h(y0, depth, from_top)
        dim_x = W * 0.16
        y_a, y_b = (H, y0) if from_top else (0, y0 + depth)
        _dim_v(ax, dim_x, y_a, y_b, tick_half=0.035)
        lbl = _tw_cutoff_label("S", S_m, state)
        ax.text(dim_x + 0.07, (y_a + y_b) / 2, lbl, fontsize=8, ha="left", va="center", color=DIM_COLOR)
        cap = "Cont." if state == "continuous" else "Disc. (min.)"
        text_y = (H + 0.12) if from_top else -0.12
        ax.text(mid_x, text_y, f"{short_label}  —  {cap}", fontsize=9, ha="center",
                va="bottom" if from_top else "top", color="black", fontweight="bold")

    def l_band(from_right, state):
        if state == "none":
            return
        depth = BAND_CONT if state == "continuous" else BAND_DISC
        x0 = (W - depth) if from_right else 0.0
        ax.add_patch(patches.Rectangle((x0, 0), depth, H, facecolor=BAND_FILL,
                                        edgecolor=LINE_COLOR, linewidth=1.0, zorder=2))
        bar_ticks_v(x0, depth, from_right)
        dim_y = mid_y
        x_a, x_b = (W, x0) if from_right else (0, x0 + depth)
        _dim_h(ax, dim_y, x_a, x_b, tick_half=0.035)
        lbl = _tw_cutoff_label("L", L_m, state)
        ax.text((x_a + x_b) / 2, dim_y + 0.06, lbl, fontsize=8, ha="center", va="bottom", color=DIM_COLOR)
        cap = "Cont." if state == "continuous" else "Disc. (min.)"
        text_x = (W + 0.12) if from_right else -0.12
        ax.text(text_x, mid_y, f"{long_label}  —  {cap}", fontsize=9,
                ha="left" if from_right else "right", va="center", color="black",
                fontweight="bold", rotation=90)

    s_band(True, s_end2_state)
    s_band(False, s_end1_state)
    l_band(True, l_end2_state)
    l_band(False, l_end1_state)

    if all(st == "none" for st in (s_end1_state, s_end2_state, l_end1_state, l_end2_state)):
        ax.text(mid_x, mid_y, "No top steel\n(all edges discontinuous)", fontsize=10.5, ha="center",
                va="center", color="#999999", style="italic")

    ax.set_title("Top Bars", fontsize=13, fontweight="bold", color=CAPTION_COLOR, pad=16)
    ax.set_xlim(-0.85, W + 0.85)
    ax.set_ylim(-0.70, H + 0.55)
    ax.set_aspect("equal")
    ax.axis("off")

    # ===================== RIGHT PANEL: Bottom Bars =====================
    ax = axB
    ax.add_patch(patches.Rectangle((0, 0), W, H, fill=False, edgecolor=LINE_COLOR, linewidth=1.6, zorder=3))
    _hl_continuous_edges(axB)

    n_v = 7   # S-direction bottom bars (vertical lines), continuous full height
    for i in range(1, n_v):
        x = W * i / n_v
        ax.plot([x, x], [0, H], color=LINE_COLOR, linewidth=0.8, linestyle=(0, (5, 3)), zorder=2)
    n_h = 5   # L-direction bottom bars (horizontal lines), continuous full width
    for i in range(1, n_h):
        y = H * i / n_h
        ax.plot([0, W], [y, y], color=LINE_COLOR, linewidth=0.8, linestyle=(0, (5, 3)), zorder=2)

    ax.text(W * 2 / n_v + 0.05, H * 0.94, f"{short_label}\n(Bottom)", fontsize=8.5, ha="left", va="top",
            color="black")
    ax.text(W * 0.62, H * 2 / n_h + 0.05, f"{long_label} (Bottom)", fontsize=8.5, ha="center", va="bottom",
            color="black")

    dim_x = -0.55
    _dim_v(ax, dim_x, 0, H)
    ax.text(dim_x - 0.06, mid_y, f"S = {_fmt_m(S_m)} m.", fontsize=9.5, va="center", ha="right",
            color=DIM_COLOR, rotation=90)

    dim_y = -0.30
    _dim_h(ax, dim_y, 0, W)
    ax.text(mid_x, dim_y - 0.10, f"L = {_fmt_m(L_m)} m.", fontsize=9.5, ha="center", va="top", color=DIM_COLOR)

    ax.set_title("Bottom Bars", fontsize=13, fontweight="bold", color=CAPTION_COLOR, pad=16)
    ax.set_xlim(-0.85, W + 0.5)
    ax.set_ylim(-0.65, H + 0.4)
    ax.set_aspect("equal")
    ax.axis("off")

    fig.suptitle("Two Way Slab — Reinforcement Plan", fontsize=14.5, fontweight="bold",
                 color=CAPTION_COLOR, y=0.99)

    # คำอธิบายสัญลักษณ์เส้นไฮไลท์ขอบต่อเนื่อง (ถ้ามีขอบต่อเนื่องอย่างน้อย 1 ขอบ)
    if any(st == "continuous" for st in (s_end1_state, s_end2_state, l_end1_state, l_end2_state)):
        fig.legend([plt.Line2D([0], [0], color=HL_COLOR, linewidth=5.0)],
                   ["Continuous / fixed edge (top steel embedment = L/3)"],
                   loc="lower center", bbox_to_anchor=(0.5, 0.005), fontsize=9.5, frameon=False)

    buf = io.BytesIO()
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ============================================================================
# Module 3.1 — คานช่วงเดียว (Single-span Beam): SFD/BMD chart + cross-section
# ============================================================================

def _signed_tick_fmt(x, pos):
    """Axis tick formatter that shows an explicit +/- sign (Thai engineering-
    drawing convention: magnitudes on SFD/BMD are always labelled with sign,
    not just implied by position). Zero is shown as plain '0'."""
    if abs(x) < 1e-6:
        return "0"
    return f"{x:+,.0f}"


def draw_beam_sfd_bmd_png(x_arr: list, v_arr: list, m_arr: list, L_m: float,
                           vu_max_kg: float, mu_max_kg_m: float, mu_max_x_m: float) -> bytes:
    """Shear Force Diagram (SFD) + Bending Moment Diagram (BMD), stacked
    vertically, from the (x, V, M) arrays computed in modules.beam_single_span
    (factored/Wu-based — design diagrams, not service-load diagrams). Units:
    V in kg, M in kg-m, x in m. English-only text (no Thai glyphs in
    matplotlib figures — this sandbox has no Thai font installed).

    Sign convention: Thai engineering-drawing style — positive (sagging)
    moment is plotted ABOVE the zero line (i.e. the moment axis is NOT
    inverted), and both axes carry explicit +/- signed tick labels and
    signed value callouts. This matches how DRMK RC SDM and Thai textbooks
    draw SFD/BMD, as opposed to the "European" convention of plotting
    sagging moment below the line (hanging, like a deflected shape)."""
    fig, (ax_v, ax_m) = plt.subplots(2, 1, figsize=(9.5, 7.0), dpi=150)

    v_max, v_min = max(v_arr), min(v_arr)
    m_max, m_min = max(m_arr), min(m_arr)

    # --- SFD ---
    ax_v.plot(x_arr, v_arr, color="#1a5fb4", linewidth=1.6)
    ax_v.fill_between(x_arr, v_arr, 0, color="#1a5fb4", alpha=0.15)
    ax_v.axhline(0, color="black", linewidth=0.9)
    ax_v.set_title("Shear Force Diagram (SFD)", fontsize=11.5, fontweight="bold", color=CAPTION_COLOR)
    ax_v.set_ylabel("V (kg.)", fontsize=9.5)
    ax_v.grid(True, linewidth=0.4, alpha=0.5)
    ax_v.yaxis.set_major_formatter(FuncFormatter(_signed_tick_fmt))
    ax_v.annotate(f"V = {v_arr[0]:+,.0f} kg.",
                  xy=(x_arr[0], v_arr[0]), xytext=(12, 10 if v_arr[0] >= 0 else -18),
                  textcoords="offset points", fontsize=9, color="#1a5fb4", fontweight="bold")
    ax_v.annotate(f"V = {v_arr[-1]:+,.0f} kg.",
                  xy=(x_arr[-1], v_arr[-1]), xytext=(-12, 10 if v_arr[-1] >= 0 else -18),
                  textcoords="offset points", fontsize=9, color="#1a5fb4", fontweight="bold", ha="right")

    # --- BMD (Thai convention: positive/sagging moment plotted ABOVE the
    # zero line — NOT inverted — unlike the "European" hanging-diagram style) ---
    ax_m.plot(x_arr, m_arr, color="#c0392b", linewidth=1.6)
    ax_m.fill_between(x_arr, m_arr, 0, color="#c0392b", alpha=0.15)
    ax_m.axhline(0, color="black", linewidth=0.9)
    ax_m.set_title("Bending Moment Diagram (BMD)", fontsize=11.5, fontweight="bold", color=CAPTION_COLOR)
    ax_m.set_xlabel("Distance from left support, x (m.)", fontsize=9.5)
    ax_m.set_ylabel("M (kg-m.)", fontsize=9.5)
    ax_m.grid(True, linewidth=0.4, alpha=0.5)
    ax_m.yaxis.set_major_formatter(FuncFormatter(_signed_tick_fmt))
    ax_m.annotate(f"Mu,max = {mu_max_kg_m:+,.0f} kg-m.\n(at x={mu_max_x_m:.2f} m.)",
                  xy=(mu_max_x_m, mu_max_kg_m), xytext=(0, 16),
                  textcoords="offset points", fontsize=9, color="#c0392b", ha="center", fontweight="bold",
                  arrowprops=dict(arrowstyle="-", color="#c0392b", linewidth=0.8))
    if m_min < -1e-6:
        m_min_x = list(x_arr)[list(m_arr).index(m_min)]
        ax_m.annotate(f"M = {m_min:+,.0f} kg-m.",
                      xy=(m_min_x, m_min), xytext=(0, -16),
                      textcoords="offset points", fontsize=9, color="#c0392b", ha="center", fontweight="bold",
                      arrowprops=dict(arrowstyle="-", color="#c0392b", linewidth=0.8))

    # headroom so the +/- callouts (esp. the two-line Mu,max label) never
    # get clipped by the axes box or overlap the subplot title
    v_span = max(v_max - v_min, 1.0)
    ax_v.set_ylim(v_min - 0.18 * v_span, v_max + 0.18 * v_span)
    m_span = max(m_max - m_min, 1.0)
    ax_m.set_ylim(m_min - 0.20 * m_span, m_max + 0.40 * m_span)

    for ax in (ax_v, ax_m):
        ax.set_xlim(-L_m * 0.03, L_m * 1.03)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_beam_section_png(b_cm: float, h_cm: float,
                           bottom_layers, top_layers, main_bar_dia_mm: float, main_bar_type: str,
                           stirrup_dia_mm: float, stirrup_spacing_cm: float, stirrup_bar_type: str,
                           cover_cm: float = 3.0, torsion=None) -> bytes:
    """Beam cross-section: outer concrete outline, stirrup outline (rounded
    rectangle, inset by cover), top/bottom bars as rows of dots — รองรับหลาย
    ชั้น (bottom_layers/top_layers รับได้ทั้ง int เดี่ยว หรือ list ของจำนวนเส้นต่อชั้น
    เรียงจากชั้นใกล้ผิวรับแรงดึงสุดออกไป เช่น [6,4] = ชั้น 1 มี 6 เส้น ชั้น 2 มี 4 เส้น —
    ตำแหน่งชั้นสอดคล้องกับ modules.beam_single_span._layer_y_distances_cm).

    torsion : TorsionDesign หรือ None — ถ้าออกแบบรับแรงบิด (required=True) จะแสดง
    เหล็กปลอกปิดที่ระยะเรียงรับบิด (s_required) และเหล็กยืนรับบิด A_l กระจายที่ด้านข้าง
    ตามหลักการเสริมเหล็กรับแรงบิด (ตำรา SDM/ACI 318)."""
    _tor_on = bool(torsion is not None and getattr(torsion, "required", False))
    _TOR_COLOR = "#B45309"   # สีเหล็ก/ปลอกรับแรงบิด (amber) ให้ต่างจากเหล็กหลักสีดำ
    fig, ax = plt.subplots(figsize=(5.2, 6.2), dpi=150)

    b_m, h_m = b_cm / 100.0, h_cm / 100.0
    cover_m = cover_cm / 100.0
    stirrup_r_m = stirrup_dia_mm / 1000.0

    # concrete outline
    ax.add_patch(patches.Rectangle((0, 0), b_m, h_m, fill=False, edgecolor=LINE_COLOR, linewidth=1.8))

    # stirrup outline (rounded corners approximated with a slightly-inset rectangle)
    # เมื่อมีแรงบิดจะเป็น "ปลอกปิด" — เน้นสี/เส้นหนาขึ้นให้เห็นชัดว่าเป็นปลอกรับบิด
    inset = cover_m
    _stir_edge = _TOR_COLOR if _tor_on else "#555555"
    ax.add_patch(patches.FancyBboxPatch(
        (inset, inset), b_m - 2 * inset, h_m - 2 * inset,
        boxstyle="round,pad=0,rounding_size=0.015",
        fill=False, edgecolor=_stir_edge, linewidth=1.5 if _tor_on else 1.2))

    bar_r_m = main_bar_dia_mm / 2000.0
    edge = cover_m + stirrup_r_m
    layer_pitch_m = (main_bar_dia_mm / 10.0 + 2.5) / 100.0   # เท่ากับ LAYER_CLEAR_SPACING_CM ของ engine

    def _row(n: int, y: float):
        if n <= 0:
            return []
        if n == 1:
            xs = [b_m / 2.0]
        else:
            usable = b_m - 2.0 * (edge + bar_r_m)
            xs = [edge + bar_r_m + usable * i / (n - 1) for i in range(n)]
        for x in xs:
            ax.add_patch(patches.Circle((x, y), bar_r_m, facecolor="black", edgecolor="black", zorder=5))
        return xs

    def _norm_layers(layers):
        if isinstance(layers, (int, float)):
            return [int(layers)] if layers > 0 else []
        return [int(n) for n in layers if n > 0]

    bottom_layers = _norm_layers(bottom_layers)
    top_layers = _norm_layers(top_layers)

    y_bottom0 = edge + bar_r_m
    y_top0 = h_m - edge - bar_r_m
    xs_bot, y_bot_leader = [], y_bottom0
    for i, n in enumerate(bottom_layers):
        y = y_bottom0 + i * layer_pitch_m
        xs = _row(n, y)
        if xs:
            xs_bot, y_bot_leader = xs, y
    xs_top, y_top_leader = [], y_top0
    for i, n in enumerate(top_layers):
        y = y_top0 - i * layer_pitch_m
        xs = _row(n, y)
        if xs:
            xs_top, y_top_leader = xs, y

    total_bottom = sum(bottom_layers)
    total_top = sum(top_layers)

    def _bar_label(total: int, layers: list, side: str) -> str:
        base = f"{total}-{main_bar_type}{main_bar_dia_mm:.0f} ({side})"
        if len(layers) <= 1:
            return base
        # ขึ้นบรรทัดใหม่สำหรับรายละเอียดชั้น กันข้อความยาวชนเส้นบอกระยะ h ด้านขวา
        return base + f"\n({len(layers)} layers: {'+'.join(str(n) for n in layers)})"

    # --- labels / leaders ---
    if xs_bot:
        ax.annotate(_bar_label(total_bottom, bottom_layers, "Bottom"),
                    xy=(xs_bot[-1], y_bot_leader), xytext=(b_m + 0.06, y_bottom0),
                    fontsize=9, va="center", ha="left", color="black",
                    arrowprops=dict(arrowstyle="-", color=LINE_COLOR, linewidth=0.8))
    if xs_top:
        ax.annotate(_bar_label(total_top, top_layers, "Top"),
                    xy=(xs_top[-1], y_top_leader), xytext=(b_m + 0.06, y_top0),
                    fontsize=9, va="center", ha="left", color="black",
                    arrowprops=dict(arrowstyle="-", color=LINE_COLOR, linewidth=0.8))

    # --- เหล็กยืนรับแรงบิด A_l (ด้านข้าง) — กระจายรอบเส้นรอบรูป, ระยะเรียงตามยาว ≤ 30 cm ---
    if _tor_on:
        gap_cm = max((y_top_leader - y_bot_leader) * 100.0, 0.0)
        n_int = max(1, math.ceil(gap_cm / 30.0) - 1)   # จำนวนเหล็กข้างต่อหน้า (ให้ระยะ ≤ 30 ซม.)
        x_left = edge + bar_r_m
        x_right = b_m - edge - bar_r_m
        side_ys = [y_bot_leader + (y_top_leader - y_bot_leader) * (k / (n_int + 1))
                   for k in range(1, n_int + 1)]
        for yy in side_ys:
            for xx in (x_left, x_right):
                ax.add_patch(patches.Circle((xx, yy), bar_r_m, facecolor=_TOR_COLOR,
                                            edgecolor="black", linewidth=0.6, zorder=6))
        n_side_total = 2 * n_int
        al_lbl = f"{n_side_total}-{main_bar_type}{main_bar_dia_mm:.0f} (Al - Torsion)"
        ax.annotate(al_lbl, xy=(x_left, side_ys[len(side_ys) // 2]),
                    xytext=(-0.30, h_m * 0.30), fontsize=8.5, va="center", ha="right",
                    color=_TOR_COLOR,
                    arrowprops=dict(arrowstyle="-", color=_TOR_COLOR, linewidth=0.8))

    # --- ป้ายเหล็กปลอก: เมื่อมีแรงบิดใช้ปลอกปิดที่ระยะเรียงรับบิด (s_required) ---
    if _tor_on:
        _sdia = getattr(torsion, "stirrup_dia_mm", stirrup_dia_mm)
        _sreq = getattr(torsion, "s_required_cm", stirrup_spacing_cm)
        # เขียนป้ายเหล็กปลอกแบบมาตรฐานแบบก่อสร้าง: RBdia@spacing (ไม่ใส่จำนวนขานำหน้า
        # เพราะจำนวนขาเป็นค่าที่ใช้ตอนคำนวณพื้นที่เท่านั้น — เขียน "2-" จะอ่านผิดเป็น 2 ปลอก)
        _stir_txt = f"{stirrup_bar_type}{_sdia:.0f}@{_sreq:.0f}cm. (Closed - Torsion)"
    else:
        _stir_txt = f"{stirrup_bar_type}{stirrup_dia_mm:.0f}@{stirrup_spacing_cm:.0f}cm. (Stirrup)"
    ax.annotate(_stir_txt,
                xy=(inset, h_m / 2.0), xytext=(-0.30, h_m / 2.0),
                fontsize=9, va="center", ha="right", color=_stir_edge,
                arrowprops=dict(arrowstyle="-", color=_stir_edge, linewidth=0.8))

    # dimensions
    _dim_h_generic(ax, -0.14, 0, b_m, f"b = {b_cm:.0f} cm.")
    _dim_v_generic(ax, b_m + 0.55, 0, h_m, f"h = {h_cm:.0f} cm.")

    ax.text(b_m / 2.0, h_m + 0.10, "Beam Section", fontsize=12, fontweight="bold",
            ha="center", va="bottom", color=CAPTION_COLOR)

    ax.set_xlim(-0.55, b_m + 1.15)
    ax.set_ylim(-0.30, h_m + 0.30)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def _dim_h_generic(ax, y: float, x0: float, x1: float, label: str):
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", color=DIM_COLOR, linewidth=0.9))
    ax.text((x0 + x1) / 2.0, y - 0.05, label, fontsize=9, ha="center", va="top", color=DIM_COLOR)


def _dim_v_generic(ax, x: float, y0: float, y1: float, label: str):
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="<->", color=DIM_COLOR, linewidth=0.9))
    ax.text(x + 0.05, (y0 + y1) / 2.0, label, fontsize=9, ha="left", va="center",
            color=DIM_COLOR, rotation=90)


# ============================================================================
# Module 3.2 — คานต่อเนื่อง (Continuous Beam): combined SFD/BMD + elevation
# ============================================================================

def _support_shear_pairs(result):
    """คืน dict: support_index -> {"before": V หรือ None, "after": V หรือ None}
    คำนวณตรงจาก r_left_kg/r_right_kg ของแต่ละช่วง + vu_kg ของปลายยื่น (ไม่ query จาก
    อาร์เรย์ที่ sample มาเพื่อกัน sampling artifact) — sign convention ตรงกับที่ plot จริง
    ใน x_arr_full/v_arr_full (อนุพันธ์จากการวิเคราะห์ทิศทาง stitch ของ overhang):
    ปลายยื่นซ้าย v ที่จุดรองรับ = -vu_kg, ปลายยื่นขวา v ที่จุดรองรับ = +vu_kg,
    ช่วงคาน v หลังจุดรองรับซ้าย = +r_left_kg, v ก่อนจุดรองรับขวา = -r_right_kg"""
    N = len(result.spans)
    pairs = {i: {"before": None, "after": None} for i in range(N + 1)}
    if result.left_overhang is not None:
        pairs[0]["before"] = -result.left_overhang.vu_kg
    for i, sp in enumerate(result.spans):
        pairs[i]["after"] = sp.r_left_kg
        pairs[i + 1]["before"] = -sp.r_right_kg
    if result.right_overhang is not None:
        pairs[N]["after"] = result.right_overhang.vu_kg
    return pairs


def draw_continuous_beam_sfd_bmd_png(result) -> bytes:
    """Combined SFD/BMD across the full beam (รวม overhang) from
    ContinuousBeamResult.x_arr_full/v_arr_full/m_arr_full — สไตล์เดียวกับ
    draw_beam_sfd_bmd_png ของโมดูล 3.1 (signed ticks, sagging positive อยู่ด้านบน,
    signed value callouts) — เพิ่ม callout ตัวเลขค่า V ที่ปลายทั้งสองด้านของทุกช่วง/
    ปลายยื่น (จุดสูง/ต่ำสุดของแต่ละ segment) และค่า M ที่จุดรองรับทุกจุด + ค่า Mu+
    สูงสุดของทุกช่วง ตามคำขอผู้ใช้ให้แสดงตัวเลขเหมือนโมดูล 3.1"""
    x_arr = result.x_arr_full
    v_arr = result.v_arr_full
    m_arr = result.m_arr_full
    L_total = result.total_length_m
    x0 = x_arr[0]
    support_x = result.support_x_positions

    fig, (ax_v, ax_m) = plt.subplots(2, 1, figsize=(11.5, 7.8), dpi=150)

    v_max, v_min = max(v_arr), min(v_arr)
    m_max, m_min = max(m_arr), min(m_arr)

    # --- SFD ---
    ax_v.plot(x_arr, v_arr, color="#1a5fb4", linewidth=1.5)
    ax_v.fill_between(x_arr, v_arr, 0, color="#1a5fb4", alpha=0.15)
    ax_v.axhline(0, color="black", linewidth=0.9)
    ax_v.set_title("Shear Force Diagram (SFD) — Full Beam", fontsize=11.5, fontweight="bold", color=CAPTION_COLOR)
    ax_v.set_ylabel("V (kg.)", fontsize=9.5)
    ax_v.grid(True, linewidth=0.4, alpha=0.5)
    ax_v.yaxis.set_major_formatter(FuncFormatter(_signed_tick_fmt))

    shear_pairs = _support_shear_pairs(result)
    for i, sx in enumerate(support_x):
        v_before = shear_pairs[i]["before"]
        v_after = shear_pairs[i]["after"]
        if v_before is not None and abs(v_before) > 1e-6:
            ax_v.annotate(f"{v_before:+,.0f}", xy=(sx, v_before), xytext=(-4, 7 if v_before >= 0 else -13),
                          textcoords="offset points", fontsize=7.2, color="#1a5fb4", fontweight="bold", ha="right")
        if v_after is not None and abs(v_after) > 1e-6:
            ax_v.annotate(f"{v_after:+,.0f}", xy=(sx, v_after), xytext=(4, 7 if v_after >= 0 else -13),
                          textcoords="offset points", fontsize=7.2, color="#1a5fb4", fontweight="bold", ha="left")

    # --- BMD (Thai convention: sagging positive on top, ไม่ invert แกน) ---
    ax_m.plot(x_arr, m_arr, color="#c0392b", linewidth=1.5)
    ax_m.fill_between(x_arr, m_arr, 0, color="#c0392b", alpha=0.15)
    ax_m.axhline(0, color="black", linewidth=0.9)
    ax_m.set_title("Bending Moment Diagram (BMD) — Full Beam", fontsize=11.5, fontweight="bold", color=CAPTION_COLOR)
    ax_m.set_xlabel("Distance along beam, x (m.)", fontsize=9.5)
    ax_m.set_ylabel("M (kg-m.)", fontsize=9.5)
    ax_m.grid(True, linewidth=0.4, alpha=0.5)
    ax_m.yaxis.set_major_formatter(FuncFormatter(_signed_tick_fmt))

    for i, sx in enumerate(support_x):
        m_val = result.supports[i].moment_kgm
        if abs(m_val) > 1e-6:
            ax_m.annotate(f"{m_val:+,.0f}", xy=(sx, m_val), xytext=(0, -14 if m_val <= 0 else 10),
                          textcoords="offset points", fontsize=7.2, color="#c0392b", fontweight="bold", ha="center")
    for i, sp in enumerate(result.spans):
        x_peak = support_x[i] + sp.mu_pos_max_x_m
        ax_m.annotate(f"{sp.mu_pos_max_kgm:+,.0f}", xy=(x_peak, sp.mu_pos_max_kgm), xytext=(0, 9),
                      textcoords="offset points", fontsize=7.2, color="#c0392b", fontweight="bold", ha="center")

    v_span = max(v_max - v_min, 1.0)
    ax_v.set_ylim(v_min - 0.22 * v_span, v_max + 0.22 * v_span)
    m_span = max(m_max - m_min, 1.0)
    ax_m.set_ylim(m_min - 0.24 * m_span, m_max + 0.30 * m_span)

    x_pad = max(L_total * 0.03, 0.15)
    for ax in (ax_v, ax_m):
        ax.set_xlim(x0 - x_pad, x0 + L_total + x_pad)

    # --- support markers (dashed vertical line + Sn label) ---
    for i, sx in enumerate(result.support_x_positions):
        for ax in (ax_v, ax_m):
            ax.axvline(sx, color="#888888", linewidth=0.8, linestyle=(0, (4, 3)), zorder=1)
        y_top = ax_m.get_ylim()[1]
        ax_m.annotate(f"S{i}", xy=(sx, y_top), xytext=(0, -12), textcoords="offset points",
                      fontsize=8.5, ha="center", va="top", color="#555555", fontweight="bold")

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_continuous_beam_elevation_png(result) -> bytes:
    """รูปด้าน (schematic elevation) ของคานต่อเนื่อง: เส้นคาน (ช่วงปกติ=LINE_COLOR,
    ปลายยื่น=สีแดง #c0392b), จุดรองรับเป็นสามเหลี่ยม label S0..SN, เส้นบอกระยะใต้คาน
    แสดงความยาวแต่ละช่วง 'L{i}=...m.' และความยาวปลายยื่น 'OH-L=...m.' / 'OH-R=...m.'
    เพิ่ม (ตามคำขอผู้ใช้): สัญลักษณ์ Uniform Load (ลูกศรเรียงแถว + เส้นบน) พร้อมค่า
    'w=...kg/m.' ต่อช่วง/ปลายยื่น และสัญลักษณ์ Point Load (ลูกศรเดี่ยว) พร้อมค่า
    'P=...kg.' ที่ตำแหน่งจริง — ค่าที่แสดงเป็นค่า factored (Wu/Pu) ตรงกับที่ใช้วิเคราะห์
    SFD/BMD จริง (สอดคล้องกับตาราง 'ผังคาน' ในรายงานพิมพ์ที่แสดง Wu อยู่แล้ว)"""
    support_x = result.support_x_positions
    n_spans = len(result.spans)
    has_left = result.left_overhang is not None
    has_right = result.right_overhang is not None

    x_beam_start = support_x[0] - (result.left_overhang.length_m if has_left else 0.0)
    x_beam_end = support_x[-1] + (result.right_overhang.length_m if has_right else 0.0)
    L_total = x_beam_end - x_beam_start

    fig, ax = plt.subplots(figsize=(11.5, 3.5), dpi=150)

    # (ปรับตามคำขอผู้ใช้: ไม่ต้องทำสัญลักษณ์ UDL ใหญ่ แค่พอสื่อว่าเป็น uniform load —
    # ลดจำนวนลูกศรเหลือ 3 เส้น/ช่วง (คงที่ ไม่ขึ้นกับความยาวช่วง) และลดความสูงลูกศรลง
    # เพื่อลดพื้นที่ของผังคานโดยรวมด้วย (เผื่อพื้นที่หน้าปริ้นส์ให้รูปตัดคานชัดเจนขึ้น)
    udl_top = L_total * 0.055
    pl_top = L_total * 0.11
    n_udl_arrows = 3

    def _draw_udl(x0, x1, w_val):
        if x1 - x0 < 1e-9 or w_val <= 0:
            return
        ax.plot([x0, x1], [udl_top, udl_top], color="#1a5fb4", linewidth=1.0)
        n = max(2, n_udl_arrows)
        xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]
        for x in xs:
            ax.annotate("", xy=(x, L_total * 0.012), xytext=(x, udl_top),
                        arrowprops=dict(arrowstyle="-|>", color="#1a5fb4", linewidth=0.8))
        ax.text((x0 + x1) / 2.0, udl_top + L_total * 0.010, f"w = {w_val:,.0f} kg/m.",
                fontsize=7.5, ha="center", va="bottom", color="#1a5fb4", fontweight="bold")

    def _draw_point_load(x, p_val):
        if p_val <= 0:
            return
        ax.annotate("", xy=(x, L_total * 0.012), xytext=(x, pl_top),
                    arrowprops=dict(arrowstyle="-|>", color="#c0392b", linewidth=1.4))
        ax.text(x, pl_top + L_total * 0.012, f"P = {p_val:,.0f} kg.",
                fontsize=8, ha="center", va="bottom", color="#c0392b", fontweight="bold")

    if has_left:
        ov = result.left_overhang
        _draw_udl(x_beam_start, support_x[0], ov.wu_kg_m)
        for x_local, p in ov.pu_loads:
            _draw_point_load(support_x[0] - x_local, p)
    for i, sp in enumerate(result.spans):
        _draw_udl(support_x[i], support_x[i + 1], sp.wu_kg_m)
        for x_local, p in sp.pu_loads:
            _draw_point_load(support_x[i] + x_local, p)
    if has_right:
        ov = result.right_overhang
        _draw_udl(support_x[-1], x_beam_end, ov.wu_kg_m)
        for x_local, p in ov.pu_loads:
            _draw_point_load(support_x[-1] + x_local, p)

    # --- overhang lines (drawn first, red) ---
    if has_left:
        ax.plot([x_beam_start, support_x[0]], [0, 0], color="#c0392b", linewidth=2.2, solid_capstyle="butt")
    if has_right:
        ax.plot([support_x[-1], x_beam_end], [0, 0], color="#c0392b", linewidth=2.2, solid_capstyle="butt")

    # --- main span line (black) ---
    ax.plot([support_x[0], support_x[-1]], [0, 0], color=LINE_COLOR, linewidth=2.2, solid_capstyle="butt")

    # --- support triangles + labels ---
    tri_h = L_total * 0.028
    tri_w = L_total * 0.022
    for i, sx in enumerate(support_x):
        ax.add_patch(patches.Polygon(
            [(sx - tri_w, -tri_h), (sx + tri_w, -tri_h), (sx, 0)],
            closed=True, fill=False, edgecolor=LINE_COLOR, linewidth=1.2))
        ax.text(sx, -tri_h - L_total * 0.045, f"S{i}", fontsize=9, ha="center", va="top",
                color="#555555", fontweight="bold")

    # --- dimension line below ---
    dim_y = -tri_h - L_total * 0.13
    if has_left:
        _dim_h_generic(ax, dim_y, x_beam_start, support_x[0], f"OH-L={result.left_overhang.length_m:.2f}m.")
    for i in range(n_spans):
        _dim_h_generic(ax, dim_y, support_x[i], support_x[i + 1], f"L{i + 1}={result.spans[i].length_m:.2f}m.")
    if has_right:
        _dim_h_generic(ax, dim_y, support_x[-1], x_beam_end, f"OH-R={result.right_overhang.length_m:.2f}m.")

    ax.text((x_beam_start + x_beam_end) / 2.0, pl_top + L_total * 0.06, "Beam Elevation (with Loading)",
            fontsize=11.5, fontweight="bold", ha="center", va="bottom", color=CAPTION_COLOR)

    pad = max(L_total * 0.04, 0.15)
    ax.set_xlim(x_beam_start - pad, x_beam_end + pad)
    ax.set_ylim(dim_y - L_total * 0.12, pl_top + L_total * 0.10)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_cantilever_beam_elevation_png(inp, result) -> bytes:
    """รูปด้าน (schematic elevation) ของคานยื่น: จุดรองรับ/โคนคานวาดเป็นสัญลักษณ์ยึดแน่น
    (fixed support — กำแพง hatch แนวตั้ง ไม่ใช่สามเหลี่ยม pin เพราะเป็น fixed ไม่ใช่ปลายหมุน),
    เส้นคานจากโคนถึงปลายอิสระ, สัญลักษณ์ Uniform Load (ลูกศร 3 เส้น กระชับ ไม่ทำใหญ่ ตาม
    pattern ที่ปรับใน 3.2 รอบ feedback ที่ 3) + Point Load พร้อมค่า Wu/Pu (factored) กำกับ
    หน่วย, เส้นบอกระยะความยาวคานยื่น."""
    L = inp.L_m
    fig, ax = plt.subplots(figsize=(8.0, 3.3), dpi=150)

    udl_top = L * 0.16
    pl_top = L * 0.30
    n_udl_arrows = 3

    def _draw_udl(x0, x1, w_val):
        if x1 - x0 < 1e-9 or w_val <= 0:
            return
        ax.plot([x0, x1], [udl_top, udl_top], color="#1a5fb4", linewidth=1.0)
        n = max(2, n_udl_arrows)
        xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]
        for x in xs:
            ax.annotate("", xy=(x, L * 0.03), xytext=(x, udl_top),
                        arrowprops=dict(arrowstyle="-|>", color="#1a5fb4", linewidth=0.8))
        ax.text((x0 + x1) / 2.0, udl_top + L * 0.02, f"w = {w_val:,.0f} kg/m.",
                fontsize=8, ha="center", va="bottom", color="#1a5fb4", fontweight="bold")

    def _draw_point_load(x, p_val):
        if p_val <= 0:
            return
        ax.annotate("", xy=(x, L * 0.03), xytext=(x, pl_top),
                    arrowprops=dict(arrowstyle="-|>", color="#c0392b", linewidth=1.4))
        ax.text(x, pl_top + L * 0.02, f"P = {p_val:,.0f} kg.",
                fontsize=8, ha="center", va="bottom", color="#c0392b", fontweight="bold")

    _draw_udl(0.0, L, result.wu_kg_m)
    for x_local, p in result.pu_loads:
        _draw_point_load(x_local, p)

    # --- beam line ---
    ax.plot([0, L], [0, 0], color=LINE_COLOR, linewidth=2.2, solid_capstyle="butt")

    # --- fixed support symbol (hatched wall at x=0) ---
    wall_w = L * 0.035
    wall_h = L * 0.16
    ax.add_patch(patches.Rectangle((-wall_w, -wall_h / 2.0), wall_w, wall_h,
                                    facecolor="#dddddd", edgecolor=LINE_COLOR, linewidth=1.2, hatch="////"))
    ax.text(-wall_w * 1.3, 0, "Fixed", fontsize=8, ha="right", va="center", color="#555555", fontweight="bold")

    # --- free tip marker ---
    ax.plot([L], [0], marker="o", markersize=3.5, color=LINE_COLOR)

    # --- dimension line ---
    dim_y = -wall_h * 0.9
    _dim_h_generic(ax, dim_y, 0.0, L, f"L = {L:.2f} m.")

    ax.text(L / 2.0, pl_top + L * 0.08, "Cantilever Beam Elevation (with Loading)",
            fontsize=11, fontweight="bold", ha="center", va="bottom", color=CAPTION_COLOR)

    pad = max(L * 0.08, 0.15)
    ax.set_xlim(-wall_w * 2.2 - pad, L + pad)
    ax.set_ylim(dim_y - L * 0.10, pl_top + L * 0.16)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_cantilever_beam_sfd_bmd_png(result, L_m: float) -> bytes:
    """SFD/BMD ของคานยื่น สไตล์เดียวกับ draw_beam_sfd_bmd_png (3.1) — sagging บวกอยู่บน
    แบบไทย, signed tick + callout — แต่คานยื่นแท้ๆ ไม่มีโมเมนต์บวกเลย (hogging ตลอดความยาว)
    จึงข้าม annotation 'Mu,max บวก' ที่ไม่มีความหมาย ใช้แค่ callout ที่จุดรองรับ (M/V สูงสุด)
    และปลายอิสระ (M=V=0, บอกเป็น context ว่าจบที่ปลายยื่นจริง)."""
    x_arr, v_arr, m_arr = result.x_arr, result.v_arr, result.m_arr
    fig, (ax_v, ax_m) = plt.subplots(2, 1, figsize=(9.5, 7.0), dpi=150)

    v_max, v_min = max(v_arr), min(v_arr)
    m_max, m_min = max(m_arr), min(m_arr)

    # --- SFD ---
    ax_v.plot(x_arr, v_arr, color="#1a5fb4", linewidth=1.6)
    ax_v.fill_between(x_arr, v_arr, 0, color="#1a5fb4", alpha=0.15)
    ax_v.axhline(0, color="black", linewidth=0.9)
    ax_v.set_title("Shear Force Diagram (SFD)", fontsize=11.5, fontweight="bold", color=CAPTION_COLOR)
    ax_v.set_ylabel("V (kg.)", fontsize=9.5)
    ax_v.grid(True, linewidth=0.4, alpha=0.5)
    ax_v.yaxis.set_major_formatter(FuncFormatter(_signed_tick_fmt))
    ax_v.annotate(f"V = {v_arr[0]:+,.0f} kg.\n(at support)",
                  xy=(x_arr[0], v_arr[0]), xytext=(12, 10),
                  textcoords="offset points", fontsize=9, color="#1a5fb4", fontweight="bold")
    ax_v.annotate("V = 0\n(free tip)",
                  xy=(x_arr[-1], v_arr[-1]), xytext=(-12, 10),
                  textcoords="offset points", fontsize=9, color="#1a5fb4", fontweight="bold", ha="right")

    # --- BMD (Thai convention: positive/sagging above zero — คานยื่นแท้ๆ ไม่มีค่าบวกเลย) ---
    ax_m.plot(x_arr, m_arr, color="#c0392b", linewidth=1.6)
    ax_m.fill_between(x_arr, m_arr, 0, color="#c0392b", alpha=0.15)
    ax_m.axhline(0, color="black", linewidth=0.9)
    ax_m.set_title("Bending Moment Diagram (BMD)", fontsize=11.5, fontweight="bold", color=CAPTION_COLOR)
    ax_m.set_xlabel("Distance from support (fixed end), x (m.)", fontsize=9.5)
    ax_m.set_ylabel("M (kg-m.)", fontsize=9.5)
    ax_m.grid(True, linewidth=0.4, alpha=0.5)
    ax_m.yaxis.set_major_formatter(FuncFormatter(_signed_tick_fmt))
    ax_m.annotate(f"M = {m_arr[0]:+,.0f} kg-m.\n(at support)",
                  xy=(x_arr[0], m_arr[0]), xytext=(0, -16),
                  textcoords="offset points", fontsize=9, color="#c0392b", ha="left", fontweight="bold",
                  arrowprops=dict(arrowstyle="-", color="#c0392b", linewidth=0.8))
    ax_m.annotate("M = 0\n(free tip)",
                  xy=(x_arr[-1], m_arr[-1]), xytext=(0, 16),
                  textcoords="offset points", fontsize=9, color="#c0392b", ha="right", fontweight="bold")

    v_span = max(v_max - v_min, 1.0)
    ax_v.set_ylim(v_min - 0.18 * v_span, v_max + 0.18 * v_span)
    m_span = max(m_max - m_min, 1.0)
    ax_m.set_ylim(m_min - 0.30 * m_span, m_max + 0.22 * m_span)

    for ax in (ax_v, ax_m):
        ax.set_xlim(-L_m * 0.03, L_m * 1.03)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ============================================================================
# Module 4.1 — เสาสี่เหลี่ยม (Rectangular Tied Column): section + interaction diagram
# ============================================================================

def draw_column_section_png(b_cm: float, h_cm: float, bar_layers, main_bar_dia_mm: float,
                              main_bar_type: str, tie_dia_mm: float, tie_spacing_cm: float,
                              tie_bar_type: str, cover_cm: float = 4.0) -> bytes:
    """รูปตัดเสา: เส้นรอบคอนกรีต + เส้นปลอก (inset ตามระยะหุ้ม) + เหล็กหลักแต่ละชั้น (bar_layers
    คือ list ของ modules.column_tied.BarLayer: y_cm จากผิวล่าง, n_bars ที่ y นั้น) วางเป็นแถว
    ตามแนวนอน (แนว b) ที่แต่ละระดับ y — เหมือนกับ draw_beam_section_png แต่พลิกให้มีเหล็กทั้ง
    บนและล่างพร้อมกัน (สมมาตร) และมีชั้นข้างเพิ่มได้ (ny_side)."""
    # figsize/ dpi ใหญ่ขึ้น (เดิม 5.6/150) เพื่อให้รูปตัดเสาคมและใหญ่ขึ้นตามที่ผู้ใช้ขอ 2026-07-12
    # (ฟอนต์เป็นหน่วย point คงเดิม เมื่อ figure ใหญ่ขึ้น สัดส่วนช่องว่างจากป้ายข้อความจึงลดลง
    # ทำให้ตัวรูปเสาเต็มเฟรมมากขึ้น)
    fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=170)

    b_m, h_m = b_cm / 100.0, h_cm / 100.0
    cover_m = cover_cm / 100.0
    tie_r_m = tie_dia_mm / 1000.0
    bar_r_m = main_bar_dia_mm / 2000.0

    ax.add_patch(patches.Rectangle((0, 0), b_m, h_m, fill=False, edgecolor=LINE_COLOR, linewidth=1.8))
    inset = cover_m
    ax.add_patch(patches.FancyBboxPatch(
        (inset, inset), b_m - 2 * inset, h_m - 2 * inset,
        boxstyle="round,pad=0,rounding_size=0.015",
        fill=False, edgecolor="#555555", linewidth=1.2))

    edge = cover_m + tie_r_m
    for layer in bar_layers:
        y = layer.y_cm / 100.0
        n = layer.n_bars
        if n <= 0:
            continue
        if n == 1:
            xs = [b_m / 2.0]
        else:
            usable = b_m - 2.0 * (edge + bar_r_m)
            xs = [edge + bar_r_m + usable * i / (n - 1) for i in range(n)]
        for x in xs:
            ax.add_patch(patches.Circle((x, y), bar_r_m, facecolor="black", edgecolor="black", zorder=5))

    total_bars = sum(layer.n_bars for layer in bar_layers)
    # ระยะป้าย/เส้นชี้/เส้นบอกระยะสเกลตามขนาดเสา (s) — เดิมใช้ค่าคงที่ (เมตร) ทำให้เสาเล็กๆ
    # ถูกดันไปมุมซ้ายและมีช่องว่างเยอะจนรูปดูเล็ก (ผู้ใช้แจ้ง 2026-07-12) การผูกกับ s ทำให้
    # สัดส่วนรูปเสาต่อทั้งเฟรมคงที่ทุกขนาดเสา และเสาอยู่กึ่งกลางเฟรมมากขึ้น
    s = max(b_m, h_m)
    lead = 0.42 * s
    ax.annotate(f"{total_bars}-{main_bar_type}{main_bar_dia_mm:.0f}",
                xy=(b_m, h_m * 0.72), xytext=(b_m + lead, h_m + 0.20 * s),
                fontsize=11, va="center", ha="left", color="black", fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=LINE_COLOR, linewidth=0.8))
    ax.annotate(f"{tie_bar_type}{tie_dia_mm:.0f}@{tie_spacing_cm:.0f}cm. (Tie)",
                xy=(inset, h_m * 0.28), xytext=(-lead, -0.06 * s),
                fontsize=10.5, va="center", ha="right", color="#555555",
                arrowprops=dict(arrowstyle="-", color="#555555", linewidth=0.8))

    _dim_h_generic(ax, -0.20 * s, 0, b_m, f"b = {b_cm:.0f} cm.")
    _dim_v_generic(ax, b_m + 0.22 * s, 0, h_m, f"h = {h_cm:.0f} cm.")

    ax.text(b_m / 2.0, h_m + 0.20 * s, "Column Section", fontsize=13.5, fontweight="bold",
            ha="center", va="bottom", color=CAPTION_COLOR)

    ax.set_xlim(-lead - 0.55 * s, b_m + 0.22 * s + 0.55 * s)
    ax.set_ylim(-0.34 * s, h_m + 0.40 * s)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def _draw_column_thumbnail_inset(ax, b_cm: float, h_cm: float) -> None:
    """วาดรูปหน้าตัดเสาแบบย่อ/schematic มุมขวาบนของกราฟ P-M interaction diagram (สไตล์เดียวกับ
    ที่พบในซอฟต์แวร์ออกแบบเสา RC เชิงพาณิชย์ทั่วไป) — ไม่ใช่รูปตัดจริงแบบละเอียด (ดู
    draw_column_section_png สำหรับรูปตัดจริง) แค่กรอบ+จุดมุม 4 จุด+ลูกศร Mx+ป้ายขนาด เพื่อช่วยให้
    อ่านทิศทางแกนอ้างอิงของกราฟ (แกนไหนคือทิศทางที่ Mx กระทำ) ได้ง่ายขึ้นเวลาดูกราฟเดี่ยวๆ"""
    iax = ax.inset_axes([0.04, 0.68, 0.28, 0.28])
    w = 1.0
    h = (h_cm / b_cm) if b_cm > 0 else 1.0
    if h > 1.4:
        h = 1.4
        w = (b_cm / h_cm) * h if h_cm > 0 else 1.0
    iax.add_patch(patches.Rectangle((0, 0), w, h, fill=False, edgecolor=LINE_COLOR, linewidth=1.2))
    corner_r = min(w, h) * 0.05
    for cx, cy in [(0.08 * w, 0.08 * h), (0.92 * w, 0.08 * h),
                   (0.08 * w, 0.92 * h), (0.92 * w, 0.92 * h)]:
        iax.add_patch(patches.Circle((cx, cy), corner_r, facecolor="#1a5fb4", edgecolor="#1a5fb4", zorder=5))
    iax.annotate("", xy=(w * 0.85, h / 2.0), xytext=(w * 0.5, h / 2.0),
                 arrowprops=dict(arrowstyle="-|>", color="#b30000", linewidth=1.4))
    iax.text(w * 0.68, h / 2.0 + h * 0.10, "Mx", fontsize=8, color="#b30000",
             fontweight="bold", ha="center")
    iax.text(w / 2.0, -h * 0.16, f"{b_cm:.0f}×{h_cm:.0f} cm.", fontsize=7.5,
             ha="center", va="top", color=CAPTION_COLOR)
    iax.set_xlim(-0.08 * w, w * 1.08)
    iax.set_ylim(-0.30 * h, h * 1.10)
    iax.set_aspect("equal")
    iax.axis("off")


def draw_column_interaction_png(interaction_points, pu_kg: float, mu_kgm: float,
                                  phi_mn_capacity_kgm: float, mu_applied_kgm: float = None,
                                  b_cm: float = None, h_cm: float = None) -> bytes:
    """กราฟ P-M Interaction Diagram: เส้นกำลังออกแบบ (φPn, φMn) จาก modules.column_tied
    (interaction_points, เรียงตาม φPn น้อยไปมากแล้ว) + จุดแรงที่ต้องการ (Pu, Mu) — จุดสีเขียว
    ถ้าอยู่ในขอบเขต (ผ่าน), สีแดงถ้าเกิน (ไม่ผ่าน) เทียบจาก phi_Mn ที่ระดับ Pu เดียวกัน — มีเส้นประ
    ลากจากจุดกำเนิดไปยังจุดแรงที่ต้องการ (ช่วยให้เห็น eccentricity/สัดส่วนแรงชัดเจนขึ้น)

    mu_kgm: โมเมนต์ที่ใช้ตรวจกำลังจริง (=result.slenderness.mu_design_kgm — รวมผลขยายโมเมนต์
    จากความชะลูดแล้วถ้ามี) ใช้เป็นจุดที่พล็อต/ตัดสิน OK-NG
    mu_applied_kgm: โมเมนต์ดิบที่ผู้ใช้กรอกก่อนขยาย (ระบุเมื่อกรณีเสาชะลูด เพื่อแสดงหมายเหตุกำกับ)
    b_cm/h_cm: ขนาดหน้าตัดเสา — ถ้าระบุจะวาดรูปหน้าตัดย่อ (schematic) มุมขวาบนของกราฟด้วย"""
    fig, ax = plt.subplots(figsize=(6.2, 6.6), dpi=150)

    mn_vals = [p.phi_mn_kgm / 1000.0 for p in interaction_points]   # kg-m -> ton-m
    pn_vals = [p.phi_pn_kg / 1000.0 for p in interaction_points]     # kg -> ton

    ax.plot(mn_vals, pn_vals, color="#1a5fb4", linewidth=1.8, marker="", label="φPn - φMn (capacity)")
    ax.fill_betweenx(pn_vals, 0, mn_vals, color="#1a5fb4", alpha=0.08)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.axvline(0, color="black", linewidth=0.8)

    ok = mu_kgm <= phi_mn_capacity_kgm
    pt_color = "#0a7a0a" if ok else "#b30000"
    mu_ton_m = mu_kgm / 1000.0
    pu_ton = pu_kg / 1000.0

    ax.plot([0, mu_ton_m], [0, pu_ton], linestyle="--", color="#b30000", linewidth=1.2,
            zorder=4, label="eccentricity line")
    ax.plot([mu_ton_m], [pu_ton], marker="o", markersize=9,
            color=pt_color, zorder=6, label="Pu, Mu (demand)")

    label_note = f"(Mu={mu_ton_m:.2f}, Pu={pu_ton:.2f}) ton-m/ton\n{'✓ OK' if ok else '✗ NG'}"
    if mu_applied_kgm is not None and abs(mu_applied_kgm - mu_kgm) > 1e-6:
        label_note += f"\n(magnified from Mu={mu_applied_kgm/1000.0:.2f} ton-m.)"
    ax.annotate(label_note,
                xy=(mu_ton_m, pu_ton), xytext=(14, 10),
                textcoords="offset points", fontsize=9.5, color=pt_color, fontweight="bold")

    ax.set_title("P-M Interaction Diagram", fontsize=12, fontweight="bold", color=CAPTION_COLOR)
    ax.set_xlabel("φMn (ton-m.)", fontsize=10)
    ax.set_ylabel("φPn (ton)", fontsize=10)
    ax.grid(True, linewidth=0.4, alpha=0.5)
    ax.legend(fontsize=8.5, loc="upper right")

    m_max = max(mn_vals + [mu_ton_m * 1.15]) if mn_vals else 1.0
    p_min = min(pn_vals + [0.0])
    p_max = max(pn_vals + [pu_ton * 1.15])
    ax.set_xlim(-0.05 * m_max, m_max * 1.15)
    ax.set_ylim(p_min * 1.10 if p_min < 0 else -0.05 * p_max, p_max * 1.15)

    if b_cm and h_cm:
        _draw_column_thumbnail_inset(ax, b_cm, h_cm)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_column_circular_section_png(diameter_cm: float, bar_points, main_bar_dia_mm: float,
                                       main_bar_type: str, spiral_bar_dia_mm: float,
                                       spiral_pitch_cm: float, spiral_bar_type: str,
                                       cover_cm: float = 4.0) -> bytes:
    """รูปตัดเสากลม (module 4.2): วงกลมรอบคอนกรีต + วงกลมเหล็กปลอกเกลียว (inset ตามระยะหุ้ม) +
    เหล็กหลักกระจายรอบวงตามตำแหน่งจริงจาก modules.column_spiral.BarPoint (angle_deg, y_cm — คำนวณ
    พิกัด x จาก R + r_bar*cos(angle), y จาก y_cm โดยตรง เพื่อให้ตรงกับตำแหน่งจริงที่ใช้คำนวณ
    interaction diagram ทุกประการ ไม่ใช่แค่รูปประกอบ)."""
    # figsize/dpi ใหญ่ขึ้น (เดิม 5.6/150) + ระยะป้ายสเกลตามรัศมีเสา เพื่อให้รูปตัดเสาใหญ่และ
    # อยู่กึ่งกลางเฟรม (ผู้ใช้ขอ 2026-07-12 — แนวเดียวกับเสาสี่เหลี่ยม)
    fig, ax = plt.subplots(figsize=(7.2, 7.2), dpi=170)

    D_m = diameter_cm / 100.0
    R_m = D_m / 2.0
    cover_m = cover_cm / 100.0
    spiral_full_dia_m = spiral_bar_dia_mm / 1000.0   # เต็มเส้นผ่านศูนย์กลางเหล็กปลอกเกลียว (m.)
    bar_r_m = main_bar_dia_mm / 2000.0

    ax.add_patch(patches.Circle((0, 0), R_m, fill=False, edgecolor=LINE_COLOR, linewidth=1.8))
    spiral_R_m = R_m - cover_m
    ax.add_patch(patches.Circle((0, 0), spiral_R_m, fill=False, edgecolor="#555555", linewidth=1.2))

    # ตรงกับสูตร r_bar ใน modules.column_spiral._build_bar_points ทุกประการ (R - cover - spiral
    # เต็มเส้นผ่านศูนย์กลาง - รัศมีเหล็กหลัก) เพื่อให้ตำแหน่งเหล็กในรูปตรงกับตำแหน่งที่ใช้คำนวณจริง
    r_bar_m = R_m - cover_m - spiral_full_dia_m - bar_r_m
    for bp in bar_points:
        angle_rad = math.radians(bp.angle_deg)
        x = r_bar_m * math.cos(angle_rad)
        y = r_bar_m * math.sin(angle_rad)
        ax.add_patch(patches.Circle((x, y), bar_r_m, facecolor="black", edgecolor="black", zorder=5))

    n_bars = len(bar_points)
    # ระยะป้าย/เส้นชี้สเกลตามรัศมีเสา s (เดิมค่าคงที่หน่วยเมตร ทำให้เสาเล็กมีช่องว่างมาก)
    s = R_m
    lead = 0.48 * s
    ax.annotate(f"{n_bars}-{main_bar_type}{main_bar_dia_mm:.0f} (around)",
                xy=(R_m * 0.92, R_m * 0.39), xytext=(R_m + lead, R_m * 0.42),
                fontsize=11, va="center", ha="left", color="black", fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=LINE_COLOR, linewidth=0.8))
    ax.annotate(f"{spiral_bar_type}{spiral_bar_dia_mm:.0f}@{spiral_pitch_cm:.1f}cm. Spiral",
                xy=(-spiral_R_m * 0.71, spiral_R_m * 0.71), xytext=(-R_m - lead, R_m * 0.62),
                fontsize=10.5, va="center", ha="right", color="#555555",
                arrowprops=dict(arrowstyle="-", color="#555555", linewidth=0.8))

    _dim_h_generic(ax, -R_m - 0.22 * s, -R_m, R_m, f"D = {diameter_cm:.0f} cm.")

    ax.text(0, R_m + 0.22 * s, "Column Section (Circular)", fontsize=13.5, fontweight="bold",
            ha="center", va="bottom", color=CAPTION_COLOR)

    ax.set_xlim(-R_m - lead - 0.60 * s, R_m + lead + 0.60 * s)
    ax.set_ylim(-R_m - 0.42 * s, R_m + 0.45 * s)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ============================================================================
# Module 5.1 — ฐานรากแผ่เดี่ยว (Isolated Spread Footing): plan + section
# ============================================================================

def draw_footing_plan_png(B_cm: float, column_b_cm: float, column_h_cm: float,
                           main_bar_dia_mm: float, main_bar_type: str,
                           n_bars_x: int, n_bars_y: int) -> bytes:
    """แปลนฐานราก: เส้นรอบรูปฐานราก B×B + เสาตรงกลาง (เส้นประ, ซ่อนอยู่ใต้ฐานราก) + เหล็กเสริม
    2 ทิศทางแบบนับจำนวนเส้น (n_bars_x/n_bars_y ตรงกับ FootingFlexure.n_bars_use — เปลี่ยนจากเดิม
    ที่วาดตามระยะห่าง เพราะไฟล์อ้างอิง SDM Plus_Footing_Bearing Pu.xlsx ออกแบบเหล็กเสริมเป็นแบบ
    นับจำนวนเส้นรวมทั้งแถบ ไม่ใช่ระยะห่างต่อเมตร — จำกัดจำนวนเส้นที่วาดไว้ไม่เกิน ~20 เส้น/ทิศทาง
    เพื่อไม่ให้รูปรกถ้าจำนวนเส้นจริงเยอะมาก แต่ตัวเลขที่กำกับป้ายชื่อยังเป็นจำนวนจริงเสมอ)."""
    fig, ax = plt.subplots(figsize=(6.0, 6.0), dpi=150)

    B_m = B_cm / 100.0
    col_b_m, col_h_m = column_b_cm / 100.0, column_h_cm / 100.0

    ax.add_patch(patches.Rectangle((0, 0), B_m, B_m, fill=False, edgecolor=LINE_COLOR, linewidth=1.8, zorder=3))

    def _grid_lines(n_bars, vertical: bool):
        n = min(max(int(n_bars), 1), 20)
        step = B_m / (n + 1)
        for i in range(1, n + 1):
            p = i * step
            if vertical:
                ax.plot([p, p], [0, B_m], color=LINE_COLOR, linewidth=0.8,
                        linestyle=(0, (5, 3)), zorder=2)
            else:
                ax.plot([0, B_m], [p, p], color=LINE_COLOR, linewidth=0.8,
                        linestyle=(0, (5, 3)), zorder=2)

    _grid_lines(n_bars_x, vertical=True)     # เหล็กทิศทาง X วางตามแนวตั้ง (เส้นขนานแกน Y)
    _grid_lines(n_bars_y, vertical=False)    # เหล็กทิศทาง Y วางตามแนวนอน (เส้นขนานแกน X)

    col_x0, col_y0 = (B_m - col_b_m) / 2.0, (B_m - col_h_m) / 2.0
    ax.add_patch(patches.Rectangle((col_x0, col_y0), col_b_m, col_h_m, fill=True,
                                    facecolor="#dddddd", edgecolor=LINE_COLOR, linewidth=1.4, zorder=4))
    ax.text(B_m / 2.0, B_m / 2.0, "Column\n(above)", fontsize=8.5, ha="center", va="center",
            color="#555555", zorder=5)

    ax.text(B_m / 2.0, -0.22, f"{n_bars_x}-{main_bar_type}{main_bar_dia_mm:.0f} (X-dir)",
            fontsize=9, ha="center", va="top", color="black")
    ax.text(B_m + 0.10, B_m / 2.0, f"{n_bars_y}-{main_bar_type}{main_bar_dia_mm:.0f} (Y-dir)",
            fontsize=9, ha="left", va="center", color="black", rotation=90)

    _dim_h_generic(ax, -0.42, 0, B_m, f"B = {B_cm:.0f} cm.")

    ax.text(B_m / 2.0, B_m + 0.12, "Footing Plan", fontsize=12, fontweight="bold",
            ha="center", va="bottom", color=CAPTION_COLOR)

    ax.set_xlim(-0.55, B_m + 1.0)
    ax.set_ylim(-0.65, B_m + 0.35)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_footing_section_png(B_cm: float, t_cm: float, column_b_cm: float, cover_cm: float,
                              main_bar_dia_mm: float, main_bar_type: str,
                              d_x_cm: float, d_y_cm: float,
                              n_bars_x: int = None, n_bars_y: int = None,
                              q_kg_m2: float = None) -> bytes:
    """รูปตัดฐานราก (ตัดผ่านแนวเสา) — วาดตามเลย์เอาต์ของไฟล์อ้างอิง
    SDM Plus_Footing_Bearing Pu.xlsx ชีท "Drawing FB" (แกะพิกัดจาก xl/charts/chart8.xml
    ซึ่งเป็น Excel XY-Scatter Chart ไม่ใช่รูปภาพฝัง) โดยตรง: เส้นระดับดิน (GL) เป็นแถบทึบ
    หนาพาดเต็มความกว้าง (เสาลากผ่านทับด้านบน), เหล็กเสริมหลัก 2 ชั้นมีป้ายชี้แยกทิศ X/Y
    คนละเส้น (เส้นชี้หักมุม ขึ้นแล้วเลี้ยวขวา) ไม่ใช่ป้ายรวมเส้นเดียว, เส้นบอกระยะ (t, cover,
    Lean, Sand) วางเรียงเป็นชุดเดียวกันทางซ้าย — ชั้นทรายรองพื้น/คอนกรีตหยาบ/เส้นระดับดิน
    เป็นค่ามาตรฐานงานก่อสร้างทั่วไป ไม่ใช่ผลคำนวณของโมดูลนี้ (อยู่นอกขอบเขตวิศวกรรมที่ตรวจสอบ
    ใช้ประกอบภาพให้ครบธรรมเนียมรูปตัดเหมือนไฟล์อ้างอิงเท่านั้น) **หมายเหตุ**: ไฟล์อ้างอิงไม่ได้
    วาดเหล็กทาบ/เหล็กหนวดกุ้ง (dowel bar) ในรูปตัดนี้เลย (ค่า Dowel Length เป็นแค่ตัวเลขในชีท
    Calculation FB เท่านั้น) — โมดูลนี้จึงไม่วาด dowel เช่นกัน (ผลตรวจสอบ dowel ยังคงแสดงเป็น
    ตารางในรายงาน/หน้าเว็บตามปกติ). n_bars_x/n_bars_y เป็น optional (None = ใช้ป้ายรวมแบบเดิม
    เผื่อเรียกจากที่อื่นที่ยังไม่มีข้อมูลจำนวนเหล็กแยกทิศ)."""
    fig, ax = plt.subplots(figsize=(6.6, 6.4), dpi=150)

    B_m, t_m = B_cm / 100.0, t_cm / 100.0
    cover_m = cover_cm / 100.0
    col_b_m = column_b_cm / 100.0
    bar_r_m = main_bar_dia_mm / 2000.0

    # ชั้นทรายรองพื้น (Sand) + คอนกรีตหยาบ (Lean) ใต้ฐานราก — ค่ามาตรฐานงานก่อสร้างทั่วไป
    # ตรงกับตัวอย่างในไฟล์อ้างอิง (Lean 0.05 m., Sand 0.10 m.) ยื่นกว้างกว่าฐานรากข้างละ 0.10 m.
    lean_m, sand_m, overhang_m = 0.05, 0.10, 0.10
    ax.add_patch(patches.Rectangle((-overhang_m, -lean_m), B_m + 2 * overhang_m, lean_m,
                                    fill=True, facecolor="#ece6d8", edgecolor=LINE_COLOR, linewidth=1.0, zorder=1))
    ax.add_patch(patches.Rectangle((-overhang_m, -lean_m - sand_m), B_m + 2 * overhang_m, sand_m,
                                    fill=True, facecolor="#f2ead2", edgecolor=LINE_COLOR, linewidth=1.0, zorder=1))
    ax.text(B_m + overhang_m + 0.06, -lean_m / 2.0, "Lean 0.05 m.", fontsize=7.5,
            va="center", ha="left", color="#555555")
    ax.text(B_m + overhang_m + 0.06, -lean_m - sand_m / 2.0, "Sand 0.10 m.", fontsize=7.5,
            va="center", ha="left", color="#555555")

    # เส้นระดับดิน (Ground Level, GL) — แถบทึบหนาพาดเต็มความกว้าง (เสาลากผ่านทับด้านบน,
    # zorder สูงกว่า) ระยะจากก้นฐานราก (founding level) ถึง GL ใช้ค่าต่ำสุดตามกฎกระทรวง
    # กำหนดสิ่งปลูกสร้างฯ พ.ศ. 2566 = 1.50 ม. (ค่ามาตรฐานบังคับ ไม่ใช่ผลคำนวณของโมดูลนี้
    # แต่เป็นข้อกำหนดขั้นต่ำที่ต้องแสดงให้ถูกต้อง)
    FOUNDING_DEPTH_M = 1.50
    gl_y = FOUNDING_DEPTH_M
    ax.plot([-overhang_m, B_m + overhang_m], [gl_y, gl_y], color="#8a6a3a", linewidth=6,
            solid_capstyle="butt", zorder=4)
    ax.text(-overhang_m, gl_y + 0.05, "GL", fontsize=9, ha="left", va="bottom",
            color="#8a6a3a", fontweight="bold")
    depth_dim_x = -overhang_m - 0.95
    _dim_v_generic(ax, depth_dim_x, 0, gl_y, f"D={FOUNDING_DEPTH_M:.2f}m. (min.)")

    # ตอเสา + เส้น "break line" ปิดบนกว้างกว่าเสาจริง (สัญลักษณ์บอกว่าเสาต่อขึ้นไปอีก) —
    # วาดทับแถบ GL (zorder สูงกว่า) เหมือนไฟล์อ้างอิง
    col_x0 = (B_m - col_b_m) / 2.0
    break_y = gl_y + 0.35 * t_m
    ax.plot([col_x0, col_x0], [t_m, break_y], color=LINE_COLOR, linewidth=1.6, zorder=6)
    ax.plot([col_x0 + col_b_m, col_x0 + col_b_m], [t_m, break_y], color=LINE_COLOR, linewidth=1.6,
            zorder=6)
    break_half_w = col_b_m * 0.75
    ax.plot([B_m / 2.0 - break_half_w, B_m / 2.0 + break_half_w], [break_y, break_y],
            color=LINE_COLOR, linewidth=1.6, zorder=6)
    # ลายขีดทแยง (hatch) สัญลักษณ์ break line ที่ปลายบนของเสา บอกว่าตัดรูปไว้ตรงนี้ เสาจริงต่อขึ้นไปอีก
    hatch_h = 0.06
    n_hatch = 5
    for i in range(n_hatch):
        hx0 = col_x0 + i * col_b_m / n_hatch
        hx1 = col_x0 + (i + 1) * col_b_m / n_hatch
        ax.plot([hx0, hx1], [break_y, break_y + hatch_h], color=LINE_COLOR, linewidth=1.0, zorder=6)
    ax.text(B_m / 2.0, break_y + hatch_h + 0.06, "Column (continues above)", fontsize=8, ha="center",
            va="bottom", color="#555555")

    # เส้นรอบรูปฐานราก (วาดหลังชั้นดิน/GL เพื่อให้ทับอยู่ด้านบน)
    ax.add_patch(patches.Rectangle((0, 0), B_m, t_m, fill=True, facecolor="white",
                                    edgecolor=LINE_COLOR, linewidth=1.8, zorder=5))

    # เหล็กเสริมหลัก — คำนวณความสูงจริงตาม d_x/d_y ก่อน (ต้องรู้ตำแหน่งเหล็กเสริมฐานรากก่อน
    # จึงจะวางปลายเหล็กเสา/dowel ให้อยู่เหนือชั้นเหล็กเสริม ไม่ทับซ้อนกับจุด/เส้นเหล็กฐานราก)
    # ไม่ใช่จุดแถวเดียวซ้อนป้าย 2 ทิศแบบเดิม ซึ่งผิดหลักวิศวกรรม เพราะเหล็ก X และ Y ของฐานราก
    # สองทางวางคนละชั้นจริง ชั้นที่ตั้งฉากกันไม่สามารถอยู่ระดับเดียวกันได้ — ใช้ y = t - d แปลง
    # จากระยะ d ที่ส่งเข้ามาโดยตรง เพื่อให้ตำแหน่งวาดตรงกับผลคำนวณจริง ไม่ใช่ค่าสมมติ)
    y_x = max(t_m - d_x_cm / 100.0, bar_r_m)
    y_y = max(t_m - d_y_cm / 100.0, bar_r_m)
    # ระยะห่างจริงระหว่าง 2 ชั้นคือ ~1 เส้นผ่านศูนย์กลางเหล็ก (สองชั้นตั้งฉากวางซ้อนชิดกัน) —
    # ให้จุดวงกลมเหล็กแกน Y ชิดขอบด้านในของเส้นเหล็กแกน X พอดี (สัมผัสกัน ไม่ลอยห่าง) โดยยังคง
    # ลำดับชั้นบน-ล่างตามค่า d จริง
    min_gap = bar_r_m * 2.0
    if abs(y_y - y_x) < min_gap:
        if y_y >= y_x:
            y_y = y_x + min_gap
        else:
            y_y = y_x - min_gap

    # เหล็กเสาที่ลากยาวลงมาฝังในฐานราก (column bar / dowel) — เส้นประสีเขียว 2 เส้น ตามหลักการ
    # ต้องแสดงในรูปตัด (เหล็กเสายึดต่อเนื่องลงไปในฐานราก ไม่ใช่แค่ตัวเลข Dowel Length ในตาราง)
    # ปลายล่างหักฉากออกด้านข้าง โดยวางไว้ "เหนือ" ชั้นเหล็กเสริมฐานรากทั้งสองทิศ (y_x, y_y) เสมอ
    # กันไม่ให้จุด/เส้นหักฉากไปทับซ้อนกับจุดเหล็กฐานรากเหมือนตัวอย่างที่ผิดก่อนหน้านี้
    REBAR_LINE_COLOR = "#1f7a1f"
    dowel_top_y = break_y - hatch_h - 0.06
    dowel_bottom_y = max(y_x, y_y) + bar_r_m * 4.0
    dowel_hook_len = B_m / 4.0
    for frac, hook_dir in ((0.25, -1.0), (0.75, 1.0)):
        dx_ = col_x0 + frac * col_b_m
        ax.plot([dx_, dx_], [dowel_top_y, dowel_bottom_y], color=REBAR_LINE_COLOR, linewidth=1.4,
                linestyle=(0, (5, 3)), zorder=6.5)
        # ปลายล่างหักฉากออกด้านข้าง (มาตรฐาน hook end) ตามตัวอย่างอ้างอิง
        ax.plot([dx_, dx_ + hook_dir * dowel_hook_len], [dowel_bottom_y, dowel_bottom_y],
                color=REBAR_LINE_COLOR, linewidth=1.4, linestyle=(0, (5, 3)), zorder=6.5)

    # ทิศ Y ถูกตัดขวางในรูปตัดนี้ (มองเห็นหน้าตัดเหล็ก) -> วาดเป็นจุดกลม
    n_bars = min(max(int(B_cm / 12.0), 4), 16)
    xs = [cover_m + bar_r_m + i * (B_m - 2 * (cover_m + bar_r_m)) / (n_bars - 1) for i in range(n_bars)]
    for x in xs:
        ax.add_patch(patches.Circle((x, y_y), bar_r_m, facecolor="black", edgecolor="black", zorder=7))

    # ทิศ X วิ่งขนานไปกับแนวตัด (มองเห็นความยาวเต็มเส้น) -> ต้องวาดเป็นเส้นยาวต่อเนื่อง ไม่ใช่จุด
    # สีดำ (LINE_COLOR) ตรงตามหลักเขียนแบบ — สีเขียวสงวนไว้เฉพาะเหล็กเสา/dowel เท่านั้น
    x_bar_0, x_bar_1 = cover_m + bar_r_m, B_m - cover_m - bar_r_m
    ax.plot([x_bar_0, x_bar_1], [y_x, y_x], color=LINE_COLOR, linewidth=1.8,
            linestyle="-", zorder=7)
    # ปลายเหล็กแกน X หักฉากขึ้น 90 องศา (มาตรฐาน hook end) ตามตัวอย่างอ้างอิง — หักขึ้นสูงเกือบเต็ม
    # ความลึกฐานราก (เหลือระยะหุ้ม/รัศมีเหล็กกันชนขอบบน)
    hook_top_y = t_m - cover_m - bar_r_m
    ax.plot([x_bar_0, x_bar_0], [y_x, hook_top_y], color=LINE_COLOR, linewidth=1.8, zorder=7)
    ax.plot([x_bar_1, x_bar_1], [y_x, hook_top_y], color=LINE_COLOR, linewidth=1.8, zorder=7)

    label_x = f"{n_bars_x}-{main_bar_type}{main_bar_dia_mm:.0f} (X-dir)" if n_bars_x else \
        f"{main_bar_type}{main_bar_dia_mm:.0f} (X-dir)"
    label_y = f"{n_bars_y}-{main_bar_type}{main_bar_dia_mm:.0f} (Y-dir)" if n_bars_y else \
        f"{main_bar_type}{main_bar_dia_mm:.0f} (Y-dir)"

    i_mid = max(0, len(xs) - 4)
    for (sx, label, y_row, y_text, bend_x, color) in [
        (x_bar_1, label_x, y_x, t_m * 0.34, B_m - cover_m * 0.5, LINE_COLOR),
        (xs[i_mid], label_y, y_y, t_m * 0.70, B_m - cover_m * 1.6, "#1a4fa0"),
    ]:
        ax.plot([sx, bend_x], [y_row, y_row], color=color, linewidth=1.0, zorder=7)
        ax.plot([bend_x, bend_x], [y_row, y_text], color=color, linewidth=1.0, zorder=7)
        ax.plot([bend_x, B_m + 0.08], [y_text, y_text], color=color, linewidth=1.0, zorder=7)
        ax.text(B_m + 0.10, y_text, label, fontsize=8, ha="left", va="center", color=color)

    ax.text(0.02, t_m * 0.95, f"dx={d_x_cm:.1f}cm.\ndy={d_y_cm:.1f}cm.",
            fontsize=7.5, ha="left", va="top", color="#555555")

    # cover — เส้นชี้ (leader) พร้อมลูกศรวัดระยะจริง จากขอบฐานรากไปยังป้ายข้อความ ตรงกับไฟล์อ้างอิง
    # วางไว้ทางขวาล่าง (ใต้ป้าย Lean/Sand) กัน ไม่ให้ไปทับกับชุดเส้นบอกระยะ t/L+S ทางซ้าย
    ax.annotate(f"cover = {cover_cm:.1f} cm.", xy=(B_m - cover_m, y_x),
                xytext=(B_m + overhang_m + 0.06, -lean_m - sand_m - 0.07),
                fontsize=7.5, color=DIM_COLOR, ha="left", va="center",
                arrowprops=dict(arrowstyle="->", color=DIM_COLOR, linewidth=0.9))

    # ชุดเส้นบอกระยะทางซ้าย: t (ความหนาฐานราก) และ Lean+Sand (รวมเป็นเส้นเดียว กันป้ายทับกัน
    # เพราะสองชั้นนี้บางมาก) เรียงต่อกันในแนวเดียว
    dim_x = -overhang_m - 0.30
    _dim_v_generic(ax, dim_x, 0, t_m, f"t={t_cm:.0f}cm.")
    _dim_v_generic(ax, dim_x - 0.35, -lean_m - sand_m, 0, f"L+S={(lean_m+sand_m)*100:.0f}cm.")

    b_dim_y = -lean_m - sand_m - 0.10
    _dim_h_generic(ax, b_dim_y, 0, B_m, f"B = {B_cm:.0f} cm.")

    # ลูกศรแรงดันดินใต้ฐานราก (bearing pressure) ชี้ขึ้นเข้าฐานราก ตรงกับไฟล์อ้างอิง (ซีรีส์ "แรงดัน")
    # วาดเฉพาะเมื่อมีค่า q ส่งเข้ามา (ไม่ใส่ตัวเลขสมมติถ้าโมดูลไม่ได้ส่งมาให้)
    if q_kg_m2 is not None:
        arrow_y0, arrow_y1 = -lean_m - 0.035, -lean_m
        for frac in (-0.35, -0.12, 0.12, 0.35):
            ax_ = B_m / 2.0 + frac * B_m
            ax.annotate("", xy=(ax_, arrow_y1), xytext=(ax_, arrow_y0),
                        arrowprops=dict(arrowstyle="->", color="#8a6a3a", linewidth=1.1))
        ax.text(B_m / 2.0, -lean_m - 0.09, f"q = {q_kg_m2:,.0f} kg/sq.m.", fontsize=7.5,
                ha="center", va="top", color="#8a6a3a")

    ax.text(B_m / 2.0, break_y + 0.28, "Footing Section", fontsize=12, fontweight="bold",
            ha="center", va="bottom", color=CAPTION_COLOR)

    ax.set_xlim(-1.85, B_m + 1.70)
    ax.set_ylim(b_dim_y - 0.18, break_y + 0.50)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ===========================================================================
# Straight-Run Stair (บันไดช่วงตรง, module 2.1) — reinforcement detail drawings
#
# 2026-07-10 (รอบที่ 3 ของโมดูลนี้): ผู้ใช้ส่งภาพหน้า "(6) แบบรายละเอียด" จากเอกสารอ้างอิง
# (ALL_SDM_BasicBOOK_DRMK.pdf ส่วนบันได) และขอให้ "คัดลอกการเสริมเหล็กแบบนี้เลย 100%" — ทำ
# ตามด้วยการวาดรูปขึ้นใหม่ทั้งหมดด้วยโค้ด matplotlib ของตัวเอง (ไม่ใช่การคัดลอก/ฝังภาพต้นฉบับ)
# ให้ได้ "ผลลัพธ์ที่ตรงกับภาพตัวอย่างมากที่สุด" ทั้งโครงสร้าง/สัดส่วน/สี/ป้ายกำกับ — ธรรมเนียม
# การเขียนแบบวิศวกรรม (เส้นบอกระยะ, เส้นชี้แบบหักมุม, จุดหน้าตัดเหล็ก ฯลฯ) เป็นความรู้มาตรฐาน
# ทั่วไปของวงการ ไม่ใช่ทรัพย์สินทางปัญญาเฉพาะของโปรแกรมใดโปรแกรมหนึ่ง จึงทำได้โดยไม่ขัดกับ
# กติกาเดิมของโปรเจกต์ที่ห้าม decompile/คัดลอกโค้ดหรือสูตรคำนวณของโปรแกรมอ้างอิงโดยตรง —
# ตัวเลข/สูตรที่แสดงในรูปยังคงเป็นค่าที่คำนวณจริงจากอินพุตของผู้ใช้เสมอ ไม่ใช่ค่าตัวอย่างจากภาพ
#
# แบ่งเป็น 2 รูปตามภาพตัวอย่าง (ผังบนไม่มีเหล็กเสริม, รูปขยายล่างมีเหล็กเสริมครบ):
#   1) draw_stair_section_png    — รูปด้านข้าง (elevation): เรขาคณิต + เส้นบอกระยะ L/H/θ/t
#      เท่านั้น ไม่มีเหล็กเสริม (ตรงตามภาพตัวอย่างที่ผังบนไม่มีเหล็กเสริมเช่นกัน)
#   2) draw_stair_rebar_detail_png — รูปขยาย (zoom) แสดงเหล็กเสริมครบ 4 ชนิด: เหล็กเสริมหลัก
#      (main, สีน้ำเงิน), เหล็กเสริมกันร้าว (distribution, จุดเขียว), เหล็กมุม (corner, เขียว),
#      เหล็กยึดขึ้น (tie-up, เขียว) — ป้ายกำกับ/เส้นชี้สีแดงตามภาพตัวอย่าง
#
# ข้อจำกัดที่ลดรูปเหมือนเดิม: ระยะตั้งฉากกับแนวลาดของ t และ cover วาดเป็นระยะแนวดิ่งแทน
# (ความคลาดเคลื่อนน้อยมากที่ความชันบันไดทั่วไป 30-40°, เป็นภาพประกอบรายการคำนวณ ไม่ใช่แบบ
# ก่อสร้าง) — เหล็กมุม/เหล็กยึดขึ้น เป็นเหล็กเสริมพิเศษ (constructive) ไม่มีการคำนวณออกแบบแยก
# ในโมดูลนี้ ใช้ขนาด/ระยะห่างเดียวกับเหล็กเสริมกันร้าว ตามธรรมเนียมงานบันไดทั่วไป (ตรงกับภาพ
# ตัวอย่างที่ก็ใช้ RB12 ขนาดเดียวกับเหล็กเสริมกันร้าวสำหรับเหล็กมุม/เหล็กยึดขึ้นเช่นกัน)
#
# ความต่อเนื่อง: ตั้งแต่รอบนี้บันไดช่วงตรงออกแบบเป็น "ไม่ต่อเนื่อง" (Simply Supported) เพียง
# กรณีเดียวเสมอ (ผู้ใช้สั่งตัดตัวเลือก ONE/BOTH ออกจาก UI ทั้งหมด) — รูปด้านข้างจึงไม่ต้องมี
# โค้งเหล็กลบ/ฝังเข้าคานที่ปลายอีกต่อไป (เดิมมีไว้รองรับกรณีต่อเนื่อง)
# ===========================================================================

import os as _os
import matplotlib.font_manager as _fm

_THAI_FONT_DIR = _os.path.join(_os.path.dirname(__file__), "fonts")
try:
    THAI_FONT = _fm.FontProperties(fname=_os.path.join(_THAI_FONT_DIR, "NotoSansThai-Regular.ttf"))
    THAI_FONT_BOLD = _fm.FontProperties(fname=_os.path.join(_THAI_FONT_DIR, "NotoSansThai-Bold.ttf"))
except Exception:
    # ป้องกันไว้เผื่อไฟล์ฟอนต์ไม่ครบ/หาไม่เจอ (เช่น ยังไม่ได้ sync ไฟล์ฟอนต์ขึ้นเครื่อง) —
    # matplotlib จะ fallback ไปใช้ฟอนต์ default ของระบบแทน (ข้อความไทยอาจกลายเป็น tofu
    # บนเครื่องที่ไม่มีฟอนต์ไทยติดตั้งไว้ แต่โปรแกรมจะไม่ crash)
    THAI_FONT = None
    THAI_FONT_BOLD = None

STAIR_BEAM_W = 0.20
STAIR_BEAM_H = 0.40
STAIR_COVER = 0.03
# ระยะหุ้ม "ผิวขั้นบันได" (nose cover) สำหรับเหล็กมุม/เหล็กยึดขึ้นในรูปขยายรายละเอียด — ใช้ค่า
# จริงตามภาพตัวอย่าง (2 ซม.) ไม่ใช่ค่าขยายเกินจริงแบบรอบก่อนหน้าอีกต่อไป (รอบนี้ปรับสัดส่วน/
# ระดับการซูมของรูปให้ระยะ 2 ซม. นี้มองเห็นชัดเจนได้โดยไม่ต้องขยายค่าตัวเลข)
STAIR_NOSE_COVER = 0.02

STAIR_MAIN_COLOR = "#1a4fd6"        # เหล็กเสริมหลัก (main bar, DB) — น้ำเงิน ตามภาพตัวอย่าง
STAIR_SECONDARY_COLOR = "#1a9c4a"   # เหล็กเสริมกันร้าว/เหล็กมุม/เหล็กยึดขึ้น (RB) — เขียว
STAIR_CALLOUT_COLOR = "#cc2222"     # เส้นชี้ + ข้อความป้ายกำกับเหล็กเสริมทั้งหมด — แดง

# --- "แบบรายละเอียด" (detail drawing) ล็อกรูปทรง/สัดส่วนเป็นมาตรฐานตายตัวเสมอ ---
# ตามคำสั่งผู้ใช้ (2026-07-11, อ้างอิงภาพ "(6) แบบรายละเอียด" ของโปรแกรมอ้างอิง): ขนาดบันไดจริง
# ที่ผู้ใช้กรอก (L/B/H/n) ใช้ "เพื่อการคำนวณเท่านั้น" ห้ามเอาไปกำหนดรูปทรง/สัดส่วนของรูปวาดแบบ
# รายละเอียด — รูปวาด (ทั้งรูปตัดข้างใหญ่ elevation และรูปขยายจุดเหล็กเสริม) จึงใช้ชุดตัวเลข
# "มาตรฐาน" ชุดเดียวกันเสมอสำหรับกำหนดรูปทรง/สัดส่วนที่วาดจริง (จำนวนขั้น+ขนาดขั้น+ความหนา waist
# ล็อกทั้งหมด ตามที่ผู้ใช้ยืนยันผ่าน AskUserQuestion) ไม่ว่าผู้ใช้จะกรอกขนาดบันไดจริงเท่าไหร่ก็ตาม
# รูปจะหน้าตาเหมือนเดิมทุกครั้ง — ใช้ค่าเดียวกับค่าเริ่มต้นของแอป (n_riser=10, R=17cm, G=25cm,
# t=15cm) เป็นชุด "มาตรฐาน" อ้างอิงเดียว ส่วนตัวเลขจริงที่ผู้ใช้กรอก/คำนวณได้ยังคงแสดงเป็น
# ป้ายกำกับ (label) บนรูปมาตรฐานนี้ตามปกติ (ไม่ใช่ตัวเลขปลอม)
STAIR_STD_N_RISER = 10
STAIR_STD_RISE_M = 0.17
STAIR_STD_GOING_M = 0.25
STAIR_STD_T_M = 0.15

# กล่องไฮไลต์สีหลังตัวเลขบนรูป แยกที่มาของค่า 2 กลุ่ม ตามภาพตัวอย่างที่ผู้ใช้ส่งมา:
# สีแดง = ค่าที่ได้จาก "การคำนวณ" ทางวิศวกรรม (มุมลาด θ, ระยะลูกตั้ง/ลูกนอนต่อขั้นในรูปขยาย,
#         ระยะห่างเหล็กเสริม) — สีเหลือง = ตัวเลขที่มาจาก "ขนาดบันได" ที่ผู้ใช้กรอกโดยตรง (สูตร
#         H = n×ลูกตั้ง, L = (n-1)×ลูกนอน)
STAIR_HL_CALC_BBOX = dict(boxstyle="round,pad=0.28", facecolor="#ff9e9e", edgecolor="none")
STAIR_HL_SIZE_BBOX = dict(boxstyle="round,pad=0.28", facecolor="#fff176", edgecolor="none")

# 2026-07-11 (รอบแปด, แก้ตามภาพจริงที่ผู้ใช้ยืนยัน): หัวข้อ "(6) แบบรายละเอียด" ใช้สีน้ำเงินกรม
# ท่า (navy) ตรงตามภาพอ้างอิง — เดิมใช้ CAPTION_COLOR (เขียว) ซึ่งไม่ตรง
STAIR_TITLE_COLOR = "#1E3853"


def _stair_dim_h(ax, y, x0, x1, tick_half=0.035, color=LINE_COLOR, linewidth=0.9):
    """เส้นบอกระยะแนวนอน พร้อมขีดตั้งฉากปลายทั้งสองข้าง (สีดำ ตามภาพตัวอย่าง — ต่างจาก
    _dim_h ของโมดูลอื่นที่ใช้สีน้ำเงิน DIM_COLOR)."""
    ax.plot([x0, x1], [y, y], color=color, linewidth=linewidth)
    ax.plot([x0, x0], [y - tick_half, y + tick_half], color=color, linewidth=linewidth)
    ax.plot([x1, x1], [y - tick_half, y + tick_half], color=color, linewidth=linewidth)


def _stair_dim_v(ax, x, y0, y1, tick_half=0.035, color=LINE_COLOR, linewidth=0.9):
    """เส้นบอกระยะแนวตั้ง พร้อมขีดตั้งฉากปลายทั้งสองข้าง (สีดำ)."""
    ax.plot([x, x], [y0, y1], color=color, linewidth=linewidth)
    ax.plot([x - tick_half, x + tick_half], [y0, y0], color=color, linewidth=linewidth)
    ax.plot([x - tick_half, x + tick_half], [y1, y1], color=color, linewidth=linewidth)


def _stair_leader_split(ax, x0, y0, y1, x1, value_text, label_text, color=STAIR_CALLOUT_COLOR,
                         fontsize=11, ha="left", fontproperties=None, linewidth=1.6,
                         value_bbox=None):
    """Elbow leader (เหมือน _ow_elbow_leader) แต่แยกข้อความเป็น 2 บรรทัดอิสระตามภาพอ้างอิงจริงที่
    ผู้ใช้ยืนยัน (2026-07-11 รอบแปด): บรรทัดค่า (value_text — ตัวเลข/รหัสเหล็กที่เป็นผลคำนวณ) มี
    กล่องไฮไลต์ value_bbox อยู่ "เหนือ" จุดหักมุมของเส้นชี้ ส่วนบรรทัดป้ายชื่อ (label_text — คำอธิบาย
    ว่าเป็นเหล็กชนิดไหน) เป็นตัวหนังสือเปล่า ไม่มีกล่องสี อยู่ "ใต้" จุดหักมุม — ต่างจาก
    _ow_elbow_leader เดิมที่ไฮไลต์ทั้งก้อนข้อความ 2 บรรทัดรวมกัน (ผู้ใช้ยืนยันว่าไม่ตรงกับภาพ
    อ้างอิง ต้องไฮไลต์เฉพาะค่าตัวเลขเท่านั้น ไม่ไฮไลต์ป้ายชื่อ)"""
    ax.plot([x0, x0], [y0, y1], color=color, linewidth=linewidth)
    ax.plot([x0, x1], [y1, y1], color=color, linewidth=linewidth)
    tx = x1 + (0.02 if ha == "left" else -0.02)
    ax.text(tx, y1 + 0.02, value_text, fontsize=fontsize, ha=ha, va="bottom", color="black",
            fontproperties=fontproperties, bbox=value_bbox)
    ax.text(tx, y1 - 0.02, label_text, fontsize=fontsize, ha=ha, va="top", color=color,
            fontproperties=fontproperties)


def draw_stair_section_png(n_riser: int, rise_cm: float, going_cm: float, t_cm: float,
                            S_m: float) -> bytes:
    """
    รูปด้านข้าง (elevation) ของบันไดช่วงตรง 1 ช่วงเต็ม — "แบบรายละเอียด" ล็อกรูปทรง/สัดส่วนเป็น
    มาตรฐานตายตัวเสมอ (STAIR_STD_N_RISER/RISE_M/GOING_M/T_M, ดูคอมเมนต์ตรงจุดประกาศค่าคงที่
    ด้านบนของไฟล์) — ขนาดบันไดจริง (n_riser/rise_cm/going_cm/t_cm/S_m ที่รับเข้ามา) ใช้แค่คำนวณ
    ตัวเลขในป้ายกำกับ (label) เท่านั้น ไม่ได้เอาไปกำหนดรูปทรง/สัดส่วนที่วาดจริงอีกต่อไป (เปลี่ยน
    ตามคำสั่งผู้ใช้ 2026-07-11 — เดิมวาดตามขนาดจริงทุกจุด) ป้ายกำกับมีเส้นบอกระยะ L (ความยาว
    ทั้งหมด), H (ความสูงระหว่างชั้น), θ (มุมลาด), t (ความหนา waist) พร้อมกล่องไฮไลต์สีแยกที่มา:
    สีเหลือง = ค่าจากขนาดบันได (H, L), สีแดง = ค่าจากการคำนวณ (θ) — ไม่มีเหล็กเสริม (ดูเหล็กเสริม
    ทั้งหมดในรูปขยายรายละเอียด draw_stair_rebar_detail_png แยกต่างหาก)
    """
    import math

    # --- ค่าจริงสำหรับ "ป้ายกำกับ" เท่านั้น (ไม่ใช้กำหนดรูปทรงที่วาด) ---
    real_rise_m = rise_cm / 100.0
    real_going_m = going_cm / 100.0
    real_total_rise = n_riser * real_rise_m
    real_slope = (real_total_rise / S_m) if S_m > 0 else 0.0
    real_theta_deg = math.degrees(math.atan(real_slope)) if S_m > 0 else 0.0

    # --- ค่ามาตรฐานสำหรับ "วาดรูปทรง" จริง (ล็อกตายตัว ไม่ขึ้นกับ input) ---
    n_riser_d = STAIR_STD_N_RISER
    rise_m = STAIR_STD_RISE_M
    going_m = STAIR_STD_GOING_M
    t_m = STAIR_STD_T_M
    total_rise = n_riser_d * rise_m
    S_m_d = (n_riser_d - 1) * going_m
    slope = total_rise / S_m_d
    theta_deg = math.degrees(math.atan(slope))

    fig, ax = plt.subplots(figsize=(9.2, 7.4), dpi=150)

    # --- ทิศทางบันได: สูงซ้ายบน ลาดลงขวาล่าง ตรงตามภาพอ้างอิงจริงที่ผู้ใช้ยืนยัน (2026-07-11
    # รอบแปด — เดิมกลับด้าน: ต่ำซ้ายล่าง สูงขวาบน) — สูตร/เรขาคณิตทั้งหมดด้านล่างยังคงคำนวณใน
    # กรอบพิกัดเดิม (ต่ำที่ x=0, สูงที่ x=S_m_d) ทุกจุดเหมือนเดิมทุกประการ (ลดความเสี่ยงบั๊กใหม่
    # เพราะสูตรผ่านการทดสอบหลายรอบมาแล้ว) แล้วค่อย "สะท้อนแนวนอน" ตำแหน่ง x ทุกจุดตอนวาดจริง
    # ผ่านฟังก์ชัน mx(x) = S_m_d - x เพียงจุดเดียว (y ไม่เปลี่ยน) — ยกเว้นส่วนโค้ง θ (patches.Arc)
    # ที่ต้องพลิกมุม theta1/theta2 ด้วย เพราะเป็นรูปทรงที่นิยามด้วยมุมกวาด ไม่ใช่จุดพิกัดตรงๆ ---
    def mx(px):
        return S_m_d - px

    # --- ผนัง/คานรองรับหัว-ท้ายช่วง (มิเรอร์แล้ว: คานสูงอยู่ซ้าย (x เดิม -BEAM_W..0), คานต่ำอยู่ขวา
    # (x เดิม S_m_d..S_m_d+BEAM_W) — ตำแหน่ง x ของกล่องคานทั้งสองสมมาตรกันเองอยู่แล้ว การมิเรอร์จึง
    # เท่ากับแค่ "สลับค่า y" ระหว่างสองกล่อง โดย x คงตำแหน่งเดิม ไม่ต้องผ่าน mx() ---
    ax.add_patch(patches.Rectangle((-STAIR_BEAM_W, total_rise - STAIR_BEAM_H), STAIR_BEAM_W, STAIR_BEAM_H,
                                    fill=True, facecolor="#e2e2f0", edgecolor=LINE_COLOR, linewidth=1.8))
    ax.add_patch(patches.Rectangle((S_m_d, -STAIR_BEAM_H), STAIR_BEAM_W, STAIR_BEAM_H,
                                    fill=True, facecolor="#e2e2f0", edgecolor=LINE_COLOR, linewidth=1.8))

    # --- เส้นประแนวเอียง (nosing line สมมติ, ใต้ผิวขั้นบันไดจริงลงมาเป็นระยะ t) ---
    ax.plot([mx(0), mx(S_m_d)], [0, total_rise], color=LINE_COLOR, linewidth=1.6, linestyle=(0, (6, 3)))

    # --- โครงร่างขั้นบันได (สัดส่วนมาตรฐาน ล็อกตายตัว) — คำนวณในกรอบพิกัดเดิมก่อน แล้วมิเรอร์ x
    # ทีเดียวหลังสร้างครบ (ลดความเสี่ยงพลาดจุดใดจุดหนึ่งระหว่างวนลูป) ---
    pts = [(0.0, t_m)]
    cx, cy = 0.0, t_m
    for i in range(n_riser_d):
        cy += rise_m
        pts.append((cx, cy))
        if i < n_riser_d - 1:
            cx += going_m
            pts.append((cx, cy))
    pts = [(mx(px), py) for (px, py) in pts]

    # --- ทึบสีตัวเนื้อคอนกรีต (waist+ขั้นบันได) เหมือนภาพตัวอย่างที่ผู้ใช้อ้างอิง 100%
    # (ภาพตัวอย่างระบายสีทึบทั้งตัวบันได ไม่ใช่แค่เส้นขอบ) — ขอบเขตของรูปทึบคือพื้นที่ระหว่าง
    # เส้นประ (แนวศูนย์กลาง/ท้องบันได) กับโครงร่างขั้นบันได ปิดขอบด้วย patches.Polygon เดียวกับ
    # สีเดียวกับคานรองรับหัว-ท้ายช่วง (#e2e2f0) ให้ดูเป็นชิ้นเดียวกันต่อเนื่องกับคาน ---
    fill_verts = [(mx(0.0), 0.0)] + pts + [(mx(S_m_d), total_rise)]
    ax.add_patch(patches.Polygon(fill_verts, closed=True, facecolor="#e2e2f0",
                                  edgecolor="none", zorder=0.5))

    xs, ys = zip(*pts)
    ax.plot(xs, ys, color=LINE_COLOR, linewidth=2.4)
    ax.plot([mx(0), mx(0)], [0, t_m], color=LINE_COLOR, linewidth=2.4)
    ax.plot([mx(S_m_d), mx(S_m_d)], [cy, total_rise], color=LINE_COLOR, linewidth=2.4)

    # --- callout "t = xx cm" — ป้ายอยู่ "ใกล้ชิด" จุดที่ชี้ ไม่ลากไกลไปพื้นที่ว่างด้านล่างสุด
    # ตำแหน่งเลือกจาก "กึ่งกลางลูกนอน" ของขั้นที่เลือก (ไม่ใช่ริมขั้นใกล้ลูกตั้ง) เพื่อให้มีเนื้อที่
    # ทึบ (ลิ่มระหว่างเส้นประท้องบันไดกับผิวขั้นบันได) กว้างพอรอบจุดชี้เสมอ — ระยะสูงของป้าย
    # คำนวณจากตำแหน่งผิวขั้นบันไดจริง ณ ขั้นนั้น (ไม่ใช่ offset ตายตัว) จึงไม่มีทางไปทับเส้นขอบ
    # ขั้นบันได — ตัวเลขในป้ายแสดง t_cm จริงที่ผู้ใช้กรอก/คำนวณได้ (แม้รูปทรงที่วาดจะเป็นมาตรฐาน) ---
    call_i = min(max(n_riser_d // 3, 0), max(n_riser_d - 1, 0))  # 0-based tread index, clamped in range
    x_left = call_i * going_m
    x_right = min(x_left + going_m, S_m_d)
    call_x = x_left + (x_right - x_left) * 0.3
    y_nose = t_m + slope * call_x
    y_line = slope * call_x
    outline_y = t_m + (call_i + 1) * rise_m  # ผิวขั้นบันได (เนื้อทึบด้านบน) ตรงขั้นที่เลือก
    # ป้ายอยู่ "เหนือ" ผิวขั้นบันได (พื้นที่ว่างเปิดโล่งเสมอ เพราะไม่มีสิ่งใดวาดเหนือเส้นขอบขั้น
    # บันได) แทนที่จะพยายามหลบอยู่ในลิ่มเนื้อทึบที่แคบ — ระยะห่างจากเส้นขอบคำนวณเป็นสัดส่วนของ
    # rise_m เสมอ ลูกศรลากผ่านเนื้อทึบลงไปยังเส้นประท้องบันได — ตำแหน่ง x คำนวณในกรอบพิกัดเดิม
    # (unmirrored) แล้วค่อยผ่าน mx() ตอนส่งเข้า annotate เท่านั้น (y ไม่ต้องมิเรอร์) ---
    t_text_x = x_left + (x_right - x_left) * 0.5
    t_text_y = outline_y + rise_m * 0.85
    # หมายเหตุ (2026-07-11 รอบสิบ): t เป็นป้ายบอกระยะสไตล์ dimension-callout (ลูกศรชี้จุดเดียว
    # ไม่มีกรอบไฮไลต์) ตรงตามภาพอ้างอิงจริงที่ผู้ใช้ยืนยัน — รอบเก้าใส่กล่องเหลืองผิดไป (ตีความ
    # กติกาสีเกินจริง) ภาพจริงยืนยันชัดเจนว่า t ไม่มีกล่องสี ต่างจาก H/L ที่เป็นค่าสูตรคำนวณ (มีกล่อง) ---
    ax.annotate(f"t = {t_cm:.0f} cm.", xy=(mx(call_x), (y_nose + y_line) / 2.0),
                xytext=(mx(t_text_x), t_text_y),
                fontsize=10.5, fontproperties=THAI_FONT, color=LINE_COLOR, ha="center", va="bottom",
                arrowprops=dict(arrowstyle="->", color=LINE_COLOR, linewidth=1.2))

    # --- θ มุมลาด — ส่วนโค้งเล็ก ๆ ใกล้ฐานรองรับด้านสูง (ซ้ายบน หลังมิเรอร์) พร้อมป้ายกำกับติดกับ
    # ส่วนโค้ง (ส่วนโค้งเองวาดตามสัดส่วนมาตรฐานที่ล็อกไว้ ให้เข้ากับรูปทรง — ตัวเลขในป้ายแสดงมุม θ
    # จริงที่คำนวณได้จาก S_m/n_riser/rise_cm จริงที่ผู้ใช้กรอก ไม่ใช่มุมของรูปทรงมาตรฐานที่วาด) —
    # ตำแหน่งศูนย์กลางส่วนโค้ง/เส้นอ้างอิง/ป้าย คำนวณในกรอบพิกัดเดิม (unmirrored, อิงจาก S_m_d
    # เหมือนเดิมทุกสูตร) แล้วมิเรอร์ x ตอนวาดจริงเท่านั้น — ยกเว้น patches.Arc ที่นิยามรูปทรงด้วย
    # มุมกวาด (theta1/theta2) ไม่ใช่จุดพิกัด จึงต้องพลิกมุมด้วย (สะท้อนแนวตั้ง: มุม φ กลายเป็น
    # 180°-φ) — เดิม theta1=0,theta2=theta_deg (กวาดจากแนวนอนขึ้นไปหาเส้นลาด) กลายเป็น
    # theta1=180-theta_deg, theta2=180 (กวาดจากเส้นลาดที่มิเรอร์แล้วไปหาแนวนอนที่ชี้ซ้าย) ---
    arc_cx = max(S_m_d - going_m * 1.6, S_m_d * 0.5)
    arc_cy = slope * arc_cx
    arc_r = min(going_m, rise_m) * 0.5
    ax.plot([mx(arc_cx), mx(arc_cx + arc_r * 1.15)], [arc_cy, arc_cy],
            color=LINE_COLOR, linewidth=1.0)
    ax.add_patch(patches.Arc((mx(arc_cx), arc_cy), arc_r * 1.7, arc_r * 1.7, angle=0,
                              theta1=180 - theta_deg, theta2=180, color=LINE_COLOR, linewidth=1.1))
    # หมายเหตุ: สัญลักษณ์ theta (θ) เป็นอักษรกรีก ไม่มีอยู่ใน glyph set ของฟอนต์ไทย
    # Noto Sans Thai ที่ bundle มา — ข้อความนี้ไม่มีอักษรไทยปน จึงปล่อยให้ใช้ฟอนต์
    # default (DejaVu Sans) ซึ่งมี glyph ของ theta/degree ครบ แทนที่จะบังคับ THAI_FONT — ตำแหน่ง
    # ป้าย (label_x/label_y) คำนวณในกรอบพิกัดเดิมด้วยสูตรตั้งฉากเดิมทุกประการ (ผ่านการทดสอบแล้ว
    # ว่าไม่ชนเส้นไม่ว่ามุมลาดจะเป็นเท่าไหร่) แล้วมิเรอร์เฉพาะ x ตอนวาดจริง — กล่องไฮไลต์สีแดง =
    # ค่าจากการคำนวณ ---
    theta_rad = math.radians(theta_deg)
    perp_dist = min(going_m, rise_m) * 1.3
    label_x = arc_cx + math.sin(theta_rad) * perp_dist
    label_y = arc_cy - math.cos(theta_rad) * perp_dist
    ax.text(mx(label_x), label_y, f"θ = {real_theta_deg:.2f}°",
            fontsize=10.5, ha="center", va="top", color="black", bbox=STAIR_HL_CALC_BBOX)

    # --- เส้นบอกระยะ L (ใต้รูป) — เส้นบอกระยะวาดตามความกว้างของรูปทรงมาตรฐาน (S_m_d, สมมาตรกับ
    # ตัวเองภายใต้การมิเรอร์ x จึงไม่ต้องเปลี่ยนตำแหน่งเส้น/จุดกึ่งกลาง) — แยกข้อความเป็น 2 บรรทัด
    # อิสระตามภาพอ้างอิงจริงที่ผู้ใช้ยืนยัน (2026-07-11 รอบแปด): บรรทัดสูตร "L = (n-1) x ลูกนอน"
    # เป็นตัวหนังสือเปล่า ไม่มีกล่องสี, บรรทัดค่า "(n-1) x G = S_m" มีกล่องไฮไลต์สีเหลือง (ค่าจาก
    # ขนาดบันได) — เดิมไฮไลต์ทั้ง 2 บรรทัดรวมกันเป็นกล่องเดียว ไม่ตรงกับภาพอ้างอิง ---
    dim_y = -STAIR_BEAM_H - 0.30
    _stair_dim_h(ax, dim_y, 0, S_m_d, linewidth=1.4)
    ax.text(S_m_d / 2.0, dim_y - 0.08, "L = (n-1) x ลูกนอน",
            fontsize=11.5, fontproperties=THAI_FONT, ha="center", va="top", color="black")
    ax.text(S_m_d / 2.0, dim_y - 0.34, f"({n_riser}-1) x {_fmt_m(real_going_m)} = {_fmt_m(S_m)} m.",
            fontsize=11.5, fontproperties=THAI_FONT, ha="center", va="top", color="black",
            bbox=STAIR_HL_SIZE_BBOX)

    # --- เส้นบอกระยะ H — ย้ายไปฝั่งขวา (ชิดคานรองรับต่ำที่ย้ายมาอยู่ขวาหลังมิเรอร์ทิศทาง) ตามภาพ
    # อ้างอิงจริงที่ผู้ใช้ยืนยัน (2026-07-11 รอบเก้า — รอบแปดวางผิดไว้ที่ฝั่งซ้าย ไม่ตรงกับภาพ) ---
    h_dim_x = S_m_d + STAIR_BEAM_W + 0.32
    _stair_dim_v(ax, h_dim_x, 0, total_rise, linewidth=1.4)
    ax.text(h_dim_x + 0.12, total_rise / 2.0 + 0.55, "H = n x ลูกตั้ง",
            fontsize=11.5, fontproperties=THAI_FONT, ha="left", va="center", color="black",
            rotation=90)
    ax.text(h_dim_x + 0.12, total_rise / 2.0 - 0.10,
            f"{n_riser} x {_fmt_m(real_rise_m)} = {_fmt_m(real_total_rise)} m.",
            fontsize=11.5, fontproperties=THAI_FONT, ha="left", va="center", color="black",
            rotation=90, bbox=STAIR_HL_SIZE_BBOX)

    # --- หัวข้อ "(6) แบบรายละเอียด" — จุดเดียว (เดิมซ้ำกับ st.subheader ของหน้า Streamlit ที่
    # เอาออกไปแล้ว) วางไว้มุมซ้ายบนของรูป สีน้ำเงินกรมท่า ตรงตามภาพอ้างอิงจริงที่ผู้ใช้ยืนยัน
    # (2026-07-11 รอบแปด — เดิมอยู่กึ่งกลางใต้รูป สีเขียว) ---
    ax.text(-STAIR_BEAM_W - 0.15, total_rise + STAIR_BEAM_H + 0.55, "(6) แบบรายละเอียด",
            fontsize=16, fontproperties=THAI_FONT_BOLD, ha="left", va="bottom",
            color=STAIR_TITLE_COLOR)

    # --- บีบขอบเขตรูปให้แคบลง (เดิมเผื่อขอบกว้างเกินไป) ให้ตัวบันไดเต็มเฟรมมากขึ้น — ขอบขวาขยับตาม
    # h_dim_x ที่ย้ายไปฝั่งขวาแล้ว (รอบเก้า) ---
    ax.set_xlim(-STAIR_BEAM_W - 0.20, h_dim_x + 0.75)
    ax.set_ylim(dim_y - 0.55, total_rise + STAIR_BEAM_H + 0.85)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_stair_u_shape_elevation_png(n_riser_per_flight: int, rise_cm: float, going_cm: float,
                                      t_cm: float, flight_S_m: float, landing_length_m: float) -> bytes:
    """
    รูปด้านข้าง (elevation) ของบันไดหักกลับ (U-Shape, โมดูล 2.2) — แบบ "คลี่" (developed
    elevation) แสดงช่วงล่าง (flight 1) เอียงขึ้น ต่อด้วยชานพัก (landing, แนวราบ) แล้วช่วงบน
    (flight 2) เอียงขึ้นต่อในทิศทางเดียวกันจนถึงพื้นชั้นบน — ทั้งสองช่วงมีเรขาคณิตเหมือนกัน
    ทุกประการ (rise_cm/going_cm/n_riser_per_flight ค่าเดียวกันทั้งคู่ ตามข้อตกลงกับผู้ใช้ว่า
    บันไดหักกลับบังคับให้ทั้งสองช่วงเท่ากันเสมอ) — ไม่มีเหล็กเสริม (ดูรูปขยายรายละเอียดแยกใน
    draw_stair_u_shape_rebar_detail_png) — ใช้ระบบพิกัด/ธรรมเนียมการวาดเดียวกับ
    draw_stair_section_png (โมดูล 2.1) ทุกประการ เพียงต่อขยายด้วยชานพักตรงกลาง
    """
    import math

    rise_m = rise_cm / 100.0
    going_m = going_cm / 100.0
    t_m = t_cm / 100.0
    total_rise_flight = n_riser_per_flight * rise_m
    total_rise = 2.0 * total_rise_flight
    slope = (total_rise_flight / flight_S_m) if flight_S_m > 0 else 0.0
    theta_deg = math.degrees(math.atan(slope)) if flight_S_m > 0 else 0.0
    x_land0 = flight_S_m
    x_land1 = flight_S_m + landing_length_m
    x_end = x_land1 + flight_S_m  # = total_horizontal_length_m ของโมดูล (2xflight_S_m+landing)

    fig, ax = plt.subplots(figsize=(11.5, 7.6), dpi=150)

    # --- ผนัง/คานรองรับหัว-ท้ายช่วง (เหมือน 2.1 — ไม่วาดคาน/ผนังรองรับชานพักเพิ่ม เพราะอยู่
    # นอกขอบเขตโมดูลนี้ ดูหมายเหตุใน modules/stair_u_shape.py) ---
    ax.add_patch(patches.Rectangle((-STAIR_BEAM_W, -STAIR_BEAM_H), STAIR_BEAM_W, STAIR_BEAM_H,
                                    fill=True, facecolor="#e2e2f0", edgecolor=LINE_COLOR, linewidth=1.8))
    ax.add_patch(patches.Rectangle((x_end, total_rise - STAIR_BEAM_H), STAIR_BEAM_W, STAIR_BEAM_H,
                                    fill=True, facecolor="#e2e2f0", edgecolor=LINE_COLOR, linewidth=1.8))

    # --- เส้นประแนวเอียง/แนวราบ (nosing line สมมติ) — 3 ช่วงต่อกัน: ลาดขึ้น (flight1) /
    # ราบ (landing) / ลาดขึ้น (flight2) ---
    ax.plot([0, flight_S_m], [0, total_rise_flight], color=LINE_COLOR, linewidth=1.6, linestyle=(0, (6, 3)))
    ax.plot([x_land0, x_land1], [total_rise_flight, total_rise_flight], color=LINE_COLOR,
            linewidth=1.6, linestyle=(0, (6, 3)))
    ax.plot([x_land1, x_end], [total_rise_flight, total_rise], color=LINE_COLOR,
            linewidth=1.6, linestyle=(0, (6, 3)))

    # --- โครงร่างขั้นบันไดช่วงล่าง (flight1) ---
    pts1 = [(0.0, t_m)]
    cx, cy = 0.0, t_m
    for i in range(n_riser_per_flight):
        cy += rise_m
        pts1.append((cx, cy))
        if i < n_riser_per_flight - 1:
            cx += going_m
            pts1.append((cx, cy))
    land_top_y = cy  # = t_m + total_rise_flight — ผิวชานพัก (ต่อเนื่องจากขั้นบนสุดของ flight1)

    # --- ชานพัก (แนวราบ) ---
    pts_landing = [(x_land0, land_top_y), (x_land1, land_top_y)]

    # --- โครงร่างขั้นบันไดช่วงบน (flight2) — เริ่มจากผิวชานพัก ต่อเนื่องกันสนิท ---
    pts2 = [(x_land1, land_top_y)]
    cx2, cy2 = x_land1, land_top_y
    for i in range(n_riser_per_flight):
        cy2 += rise_m
        pts2.append((cx2, cy2))
        if i < n_riser_per_flight - 1:
            cx2 += going_m
            pts2.append((cx2, cy2))

    all_pts = pts1 + pts_landing[1:] + pts2[1:]

    # --- ทึบสีตัวเนื้อคอนกรีต ตลอดทั้งช่วงล่าง+ชานพัก+ช่วงบน (ปิดขอบกลับไปยังเส้นประที่จุดเริ่ม/
    # จุดจบ เหมือนหลักการเดียวกับ draw_stair_section_png) ---
    fill_verts = [(0.0, 0.0)] + all_pts + [(x_end, total_rise)]
    ax.add_patch(patches.Polygon(fill_verts, closed=True, facecolor="#e2e2f0",
                                  edgecolor="none", zorder=0.5))

    xs, ys = zip(*all_pts)
    ax.plot(xs, ys, color=LINE_COLOR, linewidth=2.4)
    ax.plot([0, 0], [0, t_m], color=LINE_COLOR, linewidth=2.4)
    ax.plot([x_end, x_end], [cy2, total_rise], color=LINE_COLOR, linewidth=2.4)

    # --- ป้าย "ชานพัก (Landing)" กำกับพื้นที่แนวราบตรงกลาง ---
    ax.text((x_land0 + x_land1) / 2.0, land_top_y + rise_m * 0.55, "ชานพัก (Landing)",
            fontsize=11, fontproperties=THAI_FONT, ha="center", va="bottom", color=LINE_COLOR)

    # --- callout "t = xx cm" — ใช้ตำแหน่งขั้นในช่วงล่าง (flight1) เป็นตัวแทน (ทั้งสองช่วง
    # เหมือนกันทุกประการ ไม่ต้องกำกับซ้ำสองจุด) — ตรรกะ/สัดส่วนเดียวกับ draw_stair_section_png ---
    call_i = min(max(n_riser_per_flight // 3, 0), max(n_riser_per_flight - 1, 0))
    x_left = call_i * going_m
    x_right = min(x_left + going_m, flight_S_m)
    call_x = x_left + (x_right - x_left) * 0.3
    y_nose = t_m + slope * call_x
    y_line = slope * call_x
    outline_y = t_m + (call_i + 1) * rise_m
    t_text_x = x_left + (x_right - x_left) * 0.5
    t_text_y = outline_y + rise_m * 0.85
    ax.annotate(f"t = {t_cm:.0f} cm.", xy=(call_x, (y_nose + y_line) / 2.0),
                xytext=(t_text_x, t_text_y),
                fontsize=10.5, fontproperties=THAI_FONT, color=LINE_COLOR, ha="center", va="bottom",
                arrowprops=dict(arrowstyle="->", color=LINE_COLOR, linewidth=1.2))

    # --- θ มุมลาด — ใกล้ปลายช่วงบน (flight2, ก่อนถึงคานรองรับบนสุด) เหมือนตรรกะ/สัดส่วน
    # เดียวกับ draw_stair_section_png ---
    arc_cx = max(x_end - going_m * 1.6, x_land1 + flight_S_m * 0.5)
    arc_cy = total_rise_flight + slope * (arc_cx - x_land1)
    arc_r = min(going_m, rise_m) * 0.5
    ax.plot([arc_cx, arc_cx + arc_r * 1.15], [arc_cy, arc_cy], color=LINE_COLOR, linewidth=1.0)
    ax.add_patch(patches.Arc((arc_cx, arc_cy), arc_r * 1.7, arc_r * 1.7, angle=0,
                              theta1=0, theta2=theta_deg, color=LINE_COLOR, linewidth=1.1))
    # หมายเหตุ: ตั้งฉากจริงกับทิศทางเส้น (cosθ, sinθ) คือ (sinθ, -cosθ) เท่านั้น — ดูคำอธิบาย
    # เต็มใน draw_stair_section_png (จุดเดียวกันที่แก้ไปพร้อมกัน)
    theta_rad = math.radians(theta_deg)
    perp_dist = min(going_m, rise_m) * 1.3
    label_x = arc_cx + math.sin(theta_rad) * perp_dist
    label_y = arc_cy - math.cos(theta_rad) * perp_dist
    ax.text(label_x, label_y, f"θ = {theta_deg:.2f}°",
            fontsize=10.5, ha="center", va="top", color=LINE_COLOR)

    # --- เส้นบอกระยะ L1 / ชานพัก / L2 (ใต้รูป แถวเดียวกัน ต่อกัน) ---
    dim_y = -STAIR_BEAM_H - 0.30
    _stair_dim_h(ax, dim_y, 0, flight_S_m, linewidth=1.4)
    _stair_dim_h(ax, dim_y, x_land0, x_land1, linewidth=1.4)
    _stair_dim_h(ax, dim_y, x_land1, x_end, linewidth=1.4)
    ax.text(flight_S_m / 2.0, dim_y - 0.10,
            f"L1 = (n/2-1) x ลูกนอน\n({n_riser_per_flight}-1) x {_fmt_m(going_m)} = {_fmt_m(flight_S_m)} m.",
            fontsize=10.5, fontproperties=THAI_FONT, ha="center", va="top", color=LINE_COLOR)
    ax.text((x_land0 + x_land1) / 2.0, dim_y - 0.10,
            f"ชานพัก\n{_fmt_m(landing_length_m)} m.",
            fontsize=10.5, fontproperties=THAI_FONT, ha="center", va="top", color=LINE_COLOR)
    ax.text((x_land1 + x_end) / 2.0, dim_y - 0.10,
            f"L2 = (n/2-1) x ลูกนอน\n{_fmt_m(flight_S_m)} m.",
            fontsize=10.5, fontproperties=THAI_FONT, ha="center", va="top", color=LINE_COLOR)

    # --- เส้นบอกระยะ H รวม (ขวาของรูป) ---
    h_dim_x = x_end + STAIR_BEAM_W + 0.32
    _stair_dim_v(ax, h_dim_x, 0, total_rise, linewidth=1.4)
    ax.text(h_dim_x + 0.12, total_rise / 2.0,
            f"H = 2 x (n/2) x ลูกตั้ง\n2 x {n_riser_per_flight} x {_fmt_m(rise_m)} = {_fmt_m(total_rise)} m.",
            fontsize=10.5, fontproperties=THAI_FONT, ha="left", va="center", color=LINE_COLOR,
            rotation=90)

    ax.text(x_end / 2.0, dim_y - 0.70, "(6) แบบรายละเอียด — บันไดหักกลับ (U-Shape)",
            fontsize=15, fontproperties=THAI_FONT_BOLD, ha="center", va="center",
            color=CAPTION_COLOR)

    ax.set_xlim(-STAIR_BEAM_W - 0.20, h_dim_x + 0.60)
    ax.set_ylim(dim_y - 0.70, total_rise + t_m + 0.35)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_stair_rebar_detail_png(rise_cm: float, going_cm: float, t_cm: float,
                                 main_bar_dia_mm: float, main_bar_spacing_cm: float,
                                 temp_bar_dia_mm: float, temp_bar_spacing_cm: float,
                                 main_bar_type: str = "DB", temp_bar_type: str = "RB") -> bytes:
    """
    รูปขยาย (zoom) หน่วยซ้ำทั่วไปของขั้นบันได (3 ลูกตั้ง/2 ลูกนอน) แสดงเหล็กเสริมครบ 4 ชนิด
    ตรงตามภาพตัวอย่างที่ผู้ใช้อ้างอิง: เหล็กเสริมหลัก (สีน้ำเงิน), เหล็กเสริมกันร้าว/เหล็กมุม/
    เหล็กยึดขึ้น (สีเขียว), เส้นชี้/ป้ายกำกับ (สีแดง) — "แบบรายละเอียด" ล็อกรูปทรง/สัดส่วนที่วาด
    เป็นมาตรฐานตายตัวเสมอ (STAIR_STD_RISE_M/GOING_M/T_M) ไม่ขึ้นกับ rise_cm/going_cm/t_cm ที่รับ
    เข้ามา (เปลี่ยนตามคำสั่งผู้ใช้ 2026-07-11) — ตัวเลข rise_cm/going_cm/ระยะห่างเหล็กที่รับเข้ามา
    ใช้แสดงเป็นป้ายกำกับ (label) ค่าจริงบนรูปทรงมาตรฐานนี้เท่านั้น พร้อมกล่องไฮไลต์สีแดง (ค่าจาก
    การคำนวณ: ระยะ R/G ต่อขั้น, ระยะห่างเหล็กเสริม)
    """
    # --- ค่ามาตรฐานสำหรับ "วาดรูปทรง" จริง (ล็อกตายตัว ไม่ขึ้นกับ input) ---
    rise_m = STAIR_STD_RISE_M
    going_m = STAIR_STD_GOING_M
    t_m = STAIR_STD_T_M
    slope = (rise_m / going_m) if going_m > 0 else 0.0
    # --- ป้ายกำกับแสดงค่าจริงที่รับเข้ามาเสมอ (ไม่ใช่ค่ามาตรฐานที่ใช้วาด) ---
    main_label = f"{main_bar_type}{main_bar_dia_mm:.0f} @ {main_bar_spacing_cm:.0f} cm."
    temp_label = f"{temp_bar_type}{temp_bar_dia_mm:.0f} @ {temp_bar_spacing_cm:.0f} cm."
    corner_label = f"{temp_bar_type}{temp_bar_dia_mm:.0f}"

    N_STEPS = 3  # 3 ลูกตั้ง / 2 ลูกนอน — ซูมเข้าใกล้กว่ารอบก่อนหน้า ให้เห็นระยะ cover ชัดเจน

    def y_bar(x):
        return STAIR_COVER + slope * x

    def zigzag(x0, y0, n):
        pts = [(x0, y0)]
        cx, cy = x0, y0
        for i in range(n):
            cy += rise_m
            pts.append((cx, cy))
            if i < n - 1:
                cx += going_m
                pts.append((cx, cy))
        return pts

    outline = zigzag(0.0, t_m, N_STEPS)
    corner_pts = zigzag(STAIR_NOSE_COVER, t_m - STAIR_NOSE_COVER, N_STEPS)
    S_local = (N_STEPS - 1) * going_m
    top_rise_local = N_STEPS * rise_m

    fig, ax = plt.subplots(figsize=(10.5, 8.2), dpi=170)

    # --- ท้องบันได (soffit) เลยขอบทั้งสองข้างเล็กน้อย ---
    ext = going_m * 0.30
    ax.plot([-ext, S_local + ext], [-slope * ext, top_rise_local + slope * ext],
            color=LINE_COLOR, linewidth=2.2)

    # --- ทึบสีตัวเนื้อคอนกรีต เหมือนภาพตัวอย่างที่ผู้ใช้อ้างอิง 100% (ภาพตัวอย่างระบายสีทึบ
    # ทั้งตัวบันไดในรูปขยายด้วยเช่นกัน ไม่ใช่แค่รูปตัดข้างใหญ่) — ขอบเขตพื้นที่ทึบคือระหว่างเส้น
    # ท้องบันได (แนวลาดจริง, y=slope*x) กับโครงร่างขั้นบันได (offset ขึ้นเป็นระยะ t) — จุดปิด
    # รูปหลายเหลี่ยมด้านขวาต้องอยู่ "บนเส้นท้องบันไดจริง" ที่ x=S_local คือ (S_local, slope*S_local)
    # ไม่ใช่ (S_local, top_rise_local) แบบเดิม (top_rise_local = N_STEPS*rise_m สูงกว่าเส้นท้อง
    # บันไดจริงที่ x นี้อยู่ 1 ค่า rise_m เต็มๆ เพราะลูกตั้งขั้นสุดท้ายเป็นเส้นดิ่ง ไม่ใช่เส้นลาด —
    # ค่าเดิมทำให้เกิดช่องว่างสีขาวเป็นรูปสามเหลี่ยมเล็กๆ ที่มุมขวาบนของพื้นที่ทึบ ตรวจพบระหว่าง
    # พัฒนาโมดูล 2.2 ที่ต้องต่อขยายรูปทรงนี้ จึงแก้ไขจุดนี้ในโมดูล 2.1 ไปพร้อมกัน) ---
    fill_verts = [(0.0, 0.0)] + outline + [(S_local, slope * S_local)]
    ax.add_patch(patches.Polygon(fill_verts, closed=True, facecolor="#e2e2f0",
                                  edgecolor="none", zorder=0.5))

    # --- โครงร่างขั้นบันได (ผิวจริง) — เส้นหนาขึ้นชัดเจน ตามน้ำหนักเส้นของภาพตัวอย่าง ---
    xs, ys = zip(*outline)
    ax.plot(xs, ys, color=LINE_COLOR, linewidth=3.0)

    # --- เหล็กเสริมหลัก (main bar, DB) — เส้นสีน้ำเงิน ตามแนวท้องบันได + cover — หนาขึ้นชัดเจน ---
    x0, x1 = -ext * 0.6, S_local + ext * 0.6
    ax.plot([x0, x1], [y_bar(x0), y_bar(x1)], color=STAIR_MAIN_COLOR, linewidth=4.0,
            solid_capstyle="round")

    # --- เหล็กเสริมกันร้าว (distribution bar, RB) — จุดวงกลมสีเขียว ตามแนวเหล็กหลัก — จุดใหญ่ขึ้น
    # ชัดเจน (เดิมเล็กเกินไปจนดูไม่มีน้ำหนัก) ---
    spacing_m = max(temp_bar_spacing_cm / 100.0, 0.05)
    n_dots = int((x1 - x0) / spacing_m) + 2
    dot_xs = [x0 + i * spacing_m for i in range(n_dots) if x0 + i * spacing_m <= x1]
    for x in dot_xs:
        ax.add_patch(patches.Circle((x, y_bar(x) + 0.014), 0.022,
                                     facecolor=STAIR_SECONDARY_COLOR, edgecolor="none",
                                     zorder=5))

    # --- เหล็กมุม + เหล็กยึดขึ้น (corner bar + tie-up bar, RB) — เป็นเหล็กดัดเส้นเดียวต่อเนื่อง
    # วิ่งตามรูปทรงซิกแซกของขั้นบันได offset เข้าด้านในเป็นระยะ cover (ไม่ใช่เหล็กแยกชิ้นที่ไม่มี
    # ที่มา) — ช่วง "แนวดิ่ง" (ขนานลูกตั้ง) = เหล็กยึดขึ้น, ช่วง "แนวราบ" ที่มุมหักเข้าใต้จมูกขั้น
    # = เหล็กมุม — วาดเส้นหนา + จุดใหญ่ชัดเจนทุกจุดหักมุม ให้เห็นเป็นเส้นเหล็กแยกจากเส้นขอบคอนกรีต
    # ชัดเจน (จุดสีเขียวใหญ่กว่าเดิมเกือบเท่าตัว, เส้นหนาเกือบเท่าเหล็กหลัก) ---
    cxs, cys = zip(*corner_pts)
    ax.plot(cxs, cys, color=STAIR_SECONDARY_COLOR, linewidth=3.2, solid_joinstyle="round")
    for cx_, cy_ in corner_pts:
        ax.add_patch(patches.Circle((cx_, cy_), 0.020,
                                     facecolor=STAIR_SECONDARY_COLOR, edgecolor="none",
                                     zorder=6))

    # --- จุดยึด/ตำแหน่งป้ายกำกับซ้าย-ขวา คำนวณล่วงหน้า (ใช้กำหนดตำแหน่งเส้นบอกระยะ R
    # ให้อยู่คนละฝั่ง/คนละแนวกับ callout ทั้งสองกลุ่ม ป้องกันการทับซ้อน) ---
    label_x_left = x0 - 0.05
    label_x_right = S_local + ext * 0.6 + 0.55

    # --- เส้นบอกระยะ G (ลูกนอน) และ "2 cm" (ระยะหุ้มเหล็กมุม) แถวเดียวกัน ติดกัน ด้านบนของ
    # รูป ตรงตามภาพตัวอย่าง (ข้อความ cover ชิดขวาของขีดตัวเองแทนวางกึ่งกลางช่วงแคบ ๆ กันทับกัน) ---
    top_y = top_rise_local + 0.40
    # หมายเหตุ (2026-07-11 รอบสิบ): G (ลูกนอน) เป็นป้ายบอกระยะสไตล์ dimension-line (มีขีดหัวท้าย
    # เหมือนไม้บรรทัด) ไม่ใช่กรอบไฮไลต์ ตรงตามภาพอ้างอิงจริงที่ผู้ใช้ยืนยัน — รอบเก้าใส่กล่องเหลือง
    # ผิดไป (ตีความกติกาสีเกินจริง) ภาพจริงยืนยันว่าตัวเลข dimension-line ทั้งหมด (G, R, t) ไม่มี
    # กรอบสี ต่างจากป้าย leader-callout (θ, H/L สูตร, รหัสเหล็ก) ที่มีกรอบ ---
    g_x0, g_x1 = going_m, 2 * going_m
    _stair_dim_h(ax, top_y, g_x0, g_x1, linewidth=1.4)
    ax.text((g_x0 + g_x1) / 2.0, top_y + 0.05, f"{going_cm:.1f} cm.", fontsize=12,
            fontproperties=THAI_FONT, ha="center", va="bottom", color=LINE_COLOR)

    cov_x0, cov_x1 = 2 * going_m, 2 * going_m + STAIR_NOSE_COVER
    _stair_dim_h(ax, top_y, cov_x0, cov_x1, tick_half=0.02, linewidth=1.4)
    ax.text(cov_x1 + 0.05, top_y + 0.05, f"{STAIR_NOSE_COVER * 100:.0f} cm.", fontsize=11,
            fontproperties=THAI_FONT, ha="left", va="bottom", color=LINE_COLOR)

    # --- เส้นบอกระยะ R (ลูกตั้งบนสุด) แนวตั้ง ชิดขวาของรูปทรงจริง (ตรงตามภาพตัวอย่าง) —
    # วางให้อยู่ "เหนือ" ระดับ callout ขวาบนเสมอ (คำนวณจาก corner/tie anchor จริงด้านล่าง
    # ก่อน แล้วเว้นระยะเผื่อ) ป้องกันเส้นบอกระยะตัดผ่านเส้นชี้สีแดง ---
    r_x = corner_pts[-1][0] + going_m * 0.22
    r_y0 = corner_pts[-2][1]
    r_y1 = corner_pts[-1][1]

    # --- callout ซ้ายล่าง: เหล็กเสริมหลัก + เหล็กเสริมกันร้าว (เส้นชี้/ข้อความสีแดง หนาขึ้นชัดเจน) ---
    # ตำแหน่ง "ปลายป้าย" (จุดวางข้อความ) ใช้ระบบเรียงแถวตายตัวจากเรขาคณิตเสมอ (stack_gap คำนวณ
    # จาก rise_m/going_m จริง) แทนการค้นหา "จุดที่ใกล้ที่สุด" แล้วบวกค่าคงที่หน่วยเมตรตายตัวแบบเดิม
    # (ของเดิม: main_anchor[1]-0.36 กับ y_bar(dist_dot_x)-0.62 — ระยะห่างระหว่างป้ายทั้งสองจึงขึ้น
    # อยู่กับตำแหน่ง dist_dot_x ที่หาได้ ซึ่งไม่แน่นอน ทำให้ป้ายไปทับกันได้เมื่อ rise/going/ระยะห่าง
    # เหล็กเปลี่ยนไป — บั๊กที่ยืนยันแล้วจากภาพจริงของผู้ใช้ด้วยค่าเริ่มต้นของแอป) ระบบใหม่นี้รับประกัน
    # ว่าป้ายเหล็กเสริมหลักกับป้ายเหล็กเสริมกันร้าวจะห่างกันอย่างน้อย stack_gap เสมอ ไม่ว่าค่า
    # input จะเป็นเท่าไหร่ก็ตาม เพราะกำหนดจากตำแหน่งคงที่ ไม่ใช่จากผลการค้นหาจุด ---
    stack_gap = max(rise_m, going_m) * 1.1
    main_label_y = -stack_gap
    dist_label_y = -stack_gap * 2.2

    # --- ป้ายกำกับเหล็กเสริมทั้ง 4 ชนิดแยกบรรทัดค่า (ไฮไลต์แดง) ออกจากบรรทัดป้ายชื่อ (ตัวหนังสือ
    # เปล่า) ตามภาพอ้างอิงจริงที่ผู้ใช้ยืนยัน (2026-07-11 รอบแปด) ผ่าน _stair_leader_split — เดิม
    # ไฮไลต์ทั้งก้อนข้อความ 2 บรรทัด (main/temp) หรือไม่ไฮไลต์เลย (corner/tie-up) ไม่ตรงกับภาพ
    # อ้างอิงที่ไฮไลต์เฉพาะรหัสเหล็ก/ระยะห่างเท่านั้น ---
    main_anchor_x = x0 + 0.20
    main_anchor = (main_anchor_x, y_bar(main_anchor_x))
    _stair_leader_split(ax, main_anchor[0], main_anchor[1], main_label_y, label_x_left,
                         main_label, "เหล็กเสริมหลัก", color=STAIR_CALLOUT_COLOR, fontsize=11,
                         ha="right", fontproperties=THAI_FONT, linewidth=1.6,
                         value_bbox=STAIR_HL_CALC_BBOX)

    dist_dot_x = min(dot_xs, key=lambda x: abs(x - going_m * 0.75)) if dot_xs else main_anchor_x
    _stair_leader_split(ax, dist_dot_x, y_bar(dist_dot_x) + 0.014, dist_label_y, label_x_left,
                         temp_label, "เหล็กเสริมกันร้าว", color=STAIR_CALLOUT_COLOR, fontsize=11,
                         ha="right", fontproperties=THAI_FONT, linewidth=1.6,
                         value_bbox=STAIR_HL_CALC_BBOX)
    dist_leader_end_y = dist_label_y

    # --- callout ขวาบน: เหล็กมุม + เหล็กยึดขึ้น — ชี้ไปยัง "เส้นเดียวกัน" ที่วาดไว้ข้างต้นจริง
    # คนละช่วง (มุมหักเข้า = เหล็กมุม, ช่วงแนวดิ่ง = เหล็กยึดขึ้น) ไม่ใช่เส้นแยกที่ไม่มีที่มา ---
    corner_anchor = corner_pts[-2]  # จุดหักมุมบนสุด (ปลายช่วงแนวราบ ต่อกับช่วงแนวดิ่งสุดท้าย)
    corner_y1 = r_y0 - rise_m * 0.55  # ต่ำกว่าแนว R ให้ชัดว่าคนละเส้น ไม่ชนกัน
    _stair_leader_split(ax, corner_anchor[0], corner_anchor[1], corner_y1, label_x_right,
                         corner_label, "เหล็กมุม", color=STAIR_CALLOUT_COLOR, fontsize=11,
                         ha="left", fontproperties=THAI_FONT, linewidth=1.6,
                         value_bbox=STAIR_HL_CALC_BBOX)

    tie_mid = ((corner_pts[-2][0] + corner_pts[-1][0]) / 2.0,
               (corner_pts[-2][1] + corner_pts[-1][1]) / 2.0)
    tie_y1 = r_y1 + rise_m * 0.35  # เหนือแนว R แต่ต่ำกว่าแถวมิติ G/cover ด้านบนชัดเจน ไม่ชนกัน
    _stair_leader_split(ax, tie_mid[0], tie_mid[1], tie_y1, label_x_right,
                         temp_label, "เหล็กยึดขึ้น", color=STAIR_CALLOUT_COLOR, fontsize=11,
                         ha="left", fontproperties=THAI_FONT, linewidth=1.6,
                         value_bbox=STAIR_HL_CALC_BBOX)

    # --- วาดเส้นบอกระยะ R หลังกำหนด corner_y1/tie_y1 แล้ว เพื่อยืนยันช่วง y ไม่ทับ callout ---
    # หมายเหตุ (2026-07-11 รอบสิบ): R (ลูกตั้ง) เป็นป้าย dimension-line เช่นเดียวกับ G — ไม่มีกรอบสี
    # ตรงตามภาพอ้างอิงจริง (รอบเก้าใส่กล่องเหลืองผิดไป) ---
    _stair_dim_v(ax, r_x, r_y0, r_y1, linewidth=1.4)
    ax.text(r_x + 0.05, (r_y0 + r_y1) / 2.0, f"{rise_cm:.1f} cm.", fontsize=12,
            fontproperties=THAI_FONT, ha="left", va="center", color=LINE_COLOR)

    # --- คำอธิบายภาพ: วางต่ำกว่าปลายเส้นชี้ทุกเส้นอย่างชัดเจน (ต่ำกว่าจุดต่ำสุดของ callout
    # ซ้ายล่างอีก 0.25 ม.) ป้องกันไม่ให้ทับกับเส้นชี้หรือข้อความ label ---
    caption_y = dist_leader_end_y - 0.28
    ax.text((label_x_left + label_x_right) / 2.0, caption_y, "แบบรายละเอียดการเสริมเหล็ก",
            fontsize=15, fontproperties=THAI_FONT_BOLD, ha="center", va="center",
            color=CAPTION_COLOR)

    # --- ขอบเขตรูป: บีบระยะขอบให้แคบลงมาก (เดิมเผื่อขอบกว้างเกินไปจนตัวรูปเล็ก จมอยู่ใน
    # พื้นที่ว่าง) ให้ตัวบันได+ป้ายกำกับเต็มเฟรมใกล้เคียงภาพตัวอย่างมากขึ้น ---
    ax.set_xlim(label_x_left - 0.85, label_x_right + 0.85)
    ax.set_ylim(caption_y - 0.12, top_y + 0.15)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_stair_u_shape_rebar_detail_png(rise_cm: float, going_cm: float, t_cm: float,
                                         main_bar_dia_mm: float, main_bar_spacing_cm: float,
                                         temp_bar_dia_mm: float, temp_bar_spacing_cm: float,
                                         main_bar_type: str = "DB", temp_bar_type: str = "RB") -> bytes:
    """
    รูปขยาย (zoom) จุดต่อชานพัก-ช่วงบันได ของโมดูล 2.2 (U-Shape) — แสดงเหล็กเสริมหลัก/เหล็กเสริม
    กันร้าววิ่ง "ต่อเนื่องเป็นเส้นเดียว" จากชานพัก (แนวราบ ด้านซ้าย) เข้าสู่ช่วงบันได (แนวลาด
    ด้านขวา) ตรงตามขอบเขตที่ยืนยันกับผู้ใช้ผ่าน AskUserQuestion (2026-07-10): ชานพักออกแบบ
    แบบง่าย — ต่อเนื่องจากบันได ไม่มีการคำนวณ Mu/As แยก ไม่มีเหล็กชุดใหม่/ระยะห่างใหม่สำหรับ
    ชานพักโดยเฉพาะ (ดู modules/stair_u_shape.py ข้อ 2) — รวมเหล็กมุม/เหล็กยึดขึ้นของช่วงบันได
    (รูปแบบ/สัดส่วนเดียวกับ draw_stair_rebar_detail_png โมดูล 2.1 ทุกประการ)

    เนื่องจากทั้งสองช่วง (บน/ล่าง) ถูกบังคับให้เหมือนกันทุกประการ (ข้อ 1 ในไฟล์เดียวกัน) รูป
    เดียวนี้จึงใช้แทนจุดต่อได้ทั้งสองจุด (ชานพัก-ช่วงล่าง และ ชานพัก-ช่วงบน) ไม่ต้องวาดซ้ำสองรูป

    สัญลักษณ์เส้นตัด (break line, ซิกแซกที่ขอบซ้ายของชานพัก) เป็นธรรมเนียมงานเขียนแบบวิศวกรรม
    ทั่วไป (ใช้แสดงว่าองค์อาคารต่อยาวออกไปอีก ไม่ได้แสดงเต็มความยาวจริงในรูปขยายนี้) — ไม่ใช่การ
    เลียนแบบโปรแกรมอ้างอิงใดๆ
    """
    rise_m = rise_cm / 100.0
    going_m = going_cm / 100.0
    t_m = t_cm / 100.0
    slope = (rise_m / going_m) if going_m > 0 else 0.0
    main_label = f"{main_bar_type}{main_bar_dia_mm:.0f} @ {main_bar_spacing_cm:.0f} cm."
    temp_label = f"{temp_bar_type}{temp_bar_dia_mm:.0f} @ {temp_bar_spacing_cm:.0f} cm."
    corner_label = f"{temp_bar_type}{temp_bar_dia_mm:.0f}"

    N_STEPS = 3  # จำนวนขั้นที่แสดงในรูปขยาย — เท่ากับ draw_stair_rebar_detail_png (2.1)
    landing_zoom_m = going_m * 1.6  # ความยาวชานพักที่แสดงในรูปขยาย (ตัดด้วยสัญลักษณ์ break)

    def zigzag(x0, y0, n):
        pts = [(x0, y0)]
        cx, cy = x0, y0
        for i in range(n):
            cy += rise_m
            pts.append((cx, cy))
            if i < n - 1:
                cx += going_m
                pts.append((cx, cy))
        return pts

    # --- โครงร่างขั้นบันได (flight) เริ่มต่อจากขอบชานพัก (x=landing_zoom_m) ---
    flight_outline = zigzag(landing_zoom_m, t_m, N_STEPS)
    corner_pts = zigzag(landing_zoom_m + STAIR_NOSE_COVER, t_m - STAIR_NOSE_COVER, N_STEPS)
    S_local = landing_zoom_m + (N_STEPS - 1) * going_m
    top_rise_local = t_m + N_STEPS * rise_m

    # --- โครงร่างผิวบน: ชานพัก (แนวราบ) ต่อเนื่องเข้ากับขั้นบันได ---
    outline = [(0.0, t_m), (landing_zoom_m, t_m)] + flight_outline[1:]

    def y_bar(x):
        # เหล็กเสริมหลัก/กันร้าว: แนวราบตลอดชานพัก แล้วลาดตามช่วงบันได — เส้นเดียวต่อเนื่อง
        # (ตรงตามขอบเขต: ไม่มีเหล็กชุดใหม่/ไม่มีจุดตัดที่ชานพัก)
        if x <= landing_zoom_m:
            return STAIR_COVER
        return STAIR_COVER + slope * (x - landing_zoom_m)

    def y_soffit(x):
        if x <= landing_zoom_m:
            return 0.0
        return slope * (x - landing_zoom_m)

    fig, ax = plt.subplots(figsize=(11.8, 8.2), dpi=170)

    # --- ท้องบันได/ชานพัก (soffit) เลยขอบขวาเล็กน้อย ---
    ext = going_m * 0.30
    soffit_x_end = S_local + ext
    ax.plot([0.0, landing_zoom_m, soffit_x_end],
            [0.0, 0.0, y_soffit(soffit_x_end)],
            color=LINE_COLOR, linewidth=2.2)

    # --- พื้นที่ทึบคอนกรีต — ปิดขอบขวาไปยังเส้นท้องบันไดจริง (สอดคล้องกับการแก้ไขบั๊กช่องว่าง
    # สามเหลี่ยมที่พบใน draw_stair_rebar_detail_png — ใช้หลักการเดียวกัน) ---
    fill_verts = [(0.0, 0.0)] + outline + [(S_local, y_soffit(S_local))]
    ax.add_patch(patches.Polygon(fill_verts, closed=True, facecolor="#e2e2f0",
                                  edgecolor="none", zorder=0.5))

    # --- โครงร่างผิวบน (ชานพัก+ขั้นบันได) — เส้นหนา ---
    xs, ys = zip(*outline)
    ax.plot(xs, ys, color=LINE_COLOR, linewidth=3.0)

    # --- สัญลักษณ์เส้นตัด (break line) ที่ขอบซ้ายสุดของชานพัก ---
    break_y0, break_y1 = -0.06, t_m + 0.06
    zig_n = 5
    zig_amp = 0.035
    bx = [(zig_amp if i % 2 == 1 else -zig_amp) for i in range(zig_n + 1)]
    by = [break_y0 + (break_y1 - break_y0) * i / zig_n for i in range(zig_n + 1)]
    ax.plot(bx, by, color=LINE_COLOR, linewidth=1.6)

    # --- เหล็กเสริมหลัก (main bar) — เส้นเดียวต่อเนื่องจากชานพักเข้าช่วงบันได ---
    x0, x1 = -0.02, S_local + ext * 0.6
    ax.plot([x0, landing_zoom_m, x1], [y_bar(x0), y_bar(landing_zoom_m), y_bar(x1)],
            color=STAIR_MAIN_COLOR, linewidth=4.0, solid_capstyle="round", solid_joinstyle="round")

    # --- เหล็กเสริมกันร้าว (distribution bar) — จุดวงกลมสีเขียว ต่อเนื่องตลอดชานพัก+ช่วงบันได ---
    spacing_m = max(temp_bar_spacing_cm / 100.0, 0.05)
    n_dots = int((x1 - x0) / spacing_m) + 2
    dot_xs = [x0 + i * spacing_m for i in range(n_dots) if x0 + i * spacing_m <= x1]
    for x in dot_xs:
        ax.add_patch(patches.Circle((x, y_bar(x) + 0.014), 0.022,
                                     facecolor=STAIR_SECONDARY_COLOR, edgecolor="none", zorder=5))

    # --- เหล็กมุม + เหล็กยึดขึ้น (เฉพาะช่วงบันได — รูปแบบเดียวกับโมดูล 2.1 ทุกประการ) ---
    cxs, cys = zip(*corner_pts)
    ax.plot(cxs, cys, color=STAIR_SECONDARY_COLOR, linewidth=3.2, solid_joinstyle="round")
    for cx_, cy_ in corner_pts:
        ax.add_patch(patches.Circle((cx_, cy_), 0.020, facecolor=STAIR_SECONDARY_COLOR,
                                     edgecolor="none", zorder=6))

    # --- ป้าย "ชานพัก (Landing)" กำกับพื้นที่แนวราบ — วางเหนือผิวชานพักเล็กน้อย ---
    ax.text(landing_zoom_m / 2.0, t_m + 0.10, "ชานพัก (Landing)\nเหล็กต่อเนื่องจากบันได",
            fontsize=9.5, fontproperties=THAI_FONT, ha="center", va="bottom", color=LINE_COLOR)

    # --- จุดยึด/ตำแหน่งป้ายกำกับซ้าย-ขวา (เหมือนหลักการ 2.1) ---
    label_x_left = x0 - 0.05
    label_x_right = S_local + ext * 0.6 + 0.55

    # --- เส้นบอกระยะ G (ลูกนอน) และ cover ที่จมูกขั้น — แถวบนของรูป (shift ตาม landing_zoom_m) ---
    top_y = top_rise_local + 0.40
    g_x0, g_x1 = landing_zoom_m + going_m, landing_zoom_m + 2 * going_m
    _stair_dim_h(ax, top_y, g_x0, g_x1, linewidth=1.4)
    ax.text((g_x0 + g_x1) / 2.0, top_y + 0.05, f"{going_cm:.1f} cm.", fontsize=12,
            fontproperties=THAI_FONT, ha="center", va="bottom", color=LINE_COLOR)

    cov_x0, cov_x1 = g_x1, g_x1 + STAIR_NOSE_COVER
    _stair_dim_h(ax, top_y, cov_x0, cov_x1, tick_half=0.02, linewidth=1.4)
    ax.text(cov_x1 + 0.05, top_y + 0.05, f"{STAIR_NOSE_COVER * 100:.0f} cm.", fontsize=11,
            fontproperties=THAI_FONT, ha="left", va="bottom", color=LINE_COLOR)

    # --- เส้นบอกระยะ R (ลูกตั้งบนสุด) แนวตั้ง ชิดขวาของรูปทรงจริง ---
    r_x = corner_pts[-1][0] + going_m * 0.22
    r_y0 = corner_pts[-2][1]
    r_y1 = corner_pts[-1][1]

    # --- callout ซ้ายล่าง: เหล็กเสริมหลัก + เหล็กเสริมกันร้าว — จุดยึดอยู่บนชานพัก (แสดงว่าเหล็ก
    # ชุดนี้เริ่มต่อเนื่องมาจากชานพักแล้ว) — ระบบเรียงแถวตายตัวจากเรขาคณิตเดียวกับโมดูล 2.1
    # (stack_gap คำนวณจาก rise_m/going_m จริง ป้องกันป้ายทับกันไม่ว่า input จะเป็นเท่าไหร่) ---
    stack_gap = max(rise_m, going_m) * 1.1
    main_label_y = -stack_gap
    dist_label_y = -stack_gap * 2.2

    main_anchor_x = min(x0 + 0.20, landing_zoom_m * 0.85)
    main_anchor = (main_anchor_x, y_bar(main_anchor_x))
    _ow_elbow_leader(ax, main_anchor[0], main_anchor[1], main_label_y, label_x_left,
                      f"{main_label}\nเหล็กเสริมหลัก (ต่อเนื่องจากชานพัก)",
                      color=STAIR_CALLOUT_COLOR, fontsize=10.5, ha="right",
                      fontproperties=THAI_FONT, linewidth=1.6)

    dist_target_x = landing_zoom_m * 0.5
    dist_dot_x = min(dot_xs, key=lambda x: abs(x - dist_target_x)) if dot_xs else main_anchor_x
    _ow_elbow_leader(ax, dist_dot_x, y_bar(dist_dot_x) + 0.014, dist_label_y,
                      label_x_left, f"{temp_label}\nเหล็กเสริมกันร้าว",
                      color=STAIR_CALLOUT_COLOR, fontsize=10.5, ha="right", fontproperties=THAI_FONT,
                      linewidth=1.6)
    dist_leader_end_y = dist_label_y

    # --- callout ขวาบน: เหล็กมุม + เหล็กยึดขึ้น (ช่วงบันได — เหมือนโมดูล 2.1 ทุกประการ) ---
    corner_anchor = corner_pts[-2]
    corner_y1 = r_y0 - rise_m * 0.55
    _ow_elbow_leader(ax, corner_anchor[0], corner_anchor[1], corner_y1,
                      label_x_right, f"เหล็กมุม {corner_label}",
                      color=STAIR_CALLOUT_COLOR, fontsize=11, ha="left", fontproperties=THAI_FONT,
                      linewidth=1.6)

    tie_mid = ((corner_pts[-2][0] + corner_pts[-1][0]) / 2.0,
               (corner_pts[-2][1] + corner_pts[-1][1]) / 2.0)
    tie_y1 = r_y1 + rise_m * 0.35
    _ow_elbow_leader(ax, tie_mid[0], tie_mid[1], tie_y1, label_x_right,
                      f"เหล็กยึดขึ้น {temp_label}",
                      color=STAIR_CALLOUT_COLOR, fontsize=11, ha="left", fontproperties=THAI_FONT,
                      linewidth=1.6)

    # --- เส้นบอกระยะ R หลังกำหนด corner_y1/tie_y1 แล้ว เพื่อยืนยันช่วง y ไม่ทับ callout ---
    _stair_dim_v(ax, r_x, r_y0, r_y1, linewidth=1.4)
    ax.text(r_x + 0.05, (r_y0 + r_y1) / 2.0, f"{rise_cm:.1f} cm.", fontsize=12,
            fontproperties=THAI_FONT, ha="left", va="center", color=LINE_COLOR)

    # --- คำอธิบายภาพ ---
    caption_y = dist_leader_end_y - 0.28
    ax.text((label_x_left + label_x_right) / 2.0, caption_y,
            "แบบรายละเอียดการเสริมเหล็ก — จุดต่อชานพัก (ใช้ได้ทั้งจุดต่อบน-ล่าง เนื่องจากทั้งสองช่วงเหมือนกัน)",
            fontsize=12.5, fontproperties=THAI_FONT_BOLD, ha="center", va="center",
            color=CAPTION_COLOR)

    # --- ขอบเขตรูป ---
    ax.set_xlim(label_x_left - 0.85, label_x_right + 0.85)
    ax.set_ylim(caption_y - 0.12, top_y + 0.15)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


# ============================================================================
# Module 5.2 — ฐานรากเสาเข็ม (Pile Cap): แปลน + รูปตัด
# ============================================================================

def draw_pile_cap_plan_png(A_cm: float, B_cm: float, column_b_cm: float, column_h_cm: float,
                            pile_size_cm: float, pile_positions_cm: list,
                            main_bar_dia_mm: float, main_bar_type: str,
                            n_bars_1: int, n_bars_2: int, d_cm: float = None) -> bytes:
    """แปลนฐานรากเสาเข็ม — เขียนใหม่ 2026-07-12 ให้เหมือนแบบขยายไฟล์อ้างอิง SDM Plus (chart1):
    เส้นรอบรูปฐานราก A×B (ดำ) + เสาเป็นสี่เหลี่ยมสีเขียวมีกากบาท (X) + หน้าตัดวิกฤตแรงเฉือนทะลุ
    (เส้นประแดง รอบเสา ห่างออก d/2) + เสาเข็มเป็นวงกลมมีเครื่องหมายบวกที่ศูนย์กลาง (ดำ) +
    เส้นบอกระยะ A/B และระยะเสาเข็ม (น้ำเงิน) — เหล็กเสริมแสดงรายละเอียดในรูปตัด, แปลนบอกจำนวน
    เส้นแต่ละทิศเป็นป้ายกำกับ (ตามธรรมเนียมไฟล์อ้างอิงที่แปลนเป็นผังจัดวาง ไม่ใช่ผังเหล็ก)."""
    GREEN = "#008000"
    RED = "#D00000"

    fig, ax = plt.subplots(figsize=(7.4, 7.0), dpi=160)

    A_m, B_m = A_cm / 100.0, B_cm / 100.0
    col_b_m, col_h_m = column_b_cm / 100.0, column_h_cm / 100.0
    pile_r_m = (pile_size_cm / 100.0) / 2.0
    x0, y0 = -A_m / 2.0, -B_m / 2.0
    x1, y1 = A_m / 2.0, B_m / 2.0

    # --- ฐานราก ---
    ax.add_patch(patches.Rectangle((x0, y0), A_m, B_m, fill=False, edgecolor=LINE_COLOR,
                                    linewidth=1.9, zorder=3))

    # --- เสาเข็ม (วงกลมเส้นประ = อยู่ใต้ฐานราก + เครื่องหมายบวกศูนย์กลาง) ---
    for (px_cm, py_cm) in pile_positions_cm:
        px_m, py_m = px_cm / 100.0, py_cm / 100.0
        ax.add_patch(patches.Circle((px_m, py_m), pile_r_m, fill=True, facecolor="#ededed",
                                     edgecolor=LINE_COLOR, linewidth=1.3, linestyle=(0, (4, 2)), zorder=4))
        r = pile_r_m * 0.55
        ax.plot([px_m - r, px_m + r], [py_m, py_m], color=LINE_COLOR, linewidth=1.0, zorder=5)
        ax.plot([px_m, px_m], [py_m - r, py_m + r], color=LINE_COLOR, linewidth=1.0, zorder=5)

    # --- หน้าตัดวิกฤตแรงเฉือนทะลุที่ผิวเสา (เส้นประแดง ห่างจากผิวเสา d/2 รอบด้าน) ---
    if d_cm:
        hx = col_b_m / 2.0 + (d_cm / 100.0) / 2.0
        hy = col_h_m / 2.0 + (d_cm / 100.0) / 2.0
        ax.add_patch(patches.Rectangle((-hx, -hy), 2 * hx, 2 * hy, fill=False, edgecolor=RED,
                                        linewidth=1.3, linestyle=(0, (5, 3)), zorder=6))
        ax.text(hx, hy + 0.015, "critical section (d/2)", fontsize=7.5, ha="right", va="bottom",
                color=RED, zorder=6)

    # --- เสา (สี่เหลี่ยมเขียวมีกากบาท X) ---
    ax.add_patch(patches.Rectangle((-col_b_m / 2.0, -col_h_m / 2.0), col_b_m, col_h_m, fill=False,
                                    edgecolor=GREEN, linewidth=1.9, zorder=7))
    ax.plot([-col_b_m / 2.0, col_b_m / 2.0], [-col_h_m / 2.0, col_h_m / 2.0], color=GREEN, linewidth=1.2, zorder=7)
    ax.plot([-col_b_m / 2.0, col_b_m / 2.0], [col_h_m / 2.0, -col_h_m / 2.0], color=GREEN, linewidth=1.2, zorder=7)

    # --- เหล็กเสริม 2 ทิศ: ลูกศรเขียวบอกช่วงกระจายเหล็ก + ป้ายจำนวน+ขนาด (เท่านั้น) ตามรูปอ้างอิง
    #     ล่าง = เหล็กกระจายตามแนว A (n_bars_2 เส้น วิ่ง // B) ; ขวา = เหล็ก // A (n_bars_1 เส้น) ---
    gy = y0 + 0.06
    ax.annotate("", xy=(x0 + 0.03, gy), xytext=(x1 - 0.03, gy),
                arrowprops=dict(arrowstyle="<->", color=GREEN, linewidth=1.6))
    ax.text(0, y0 - 0.16, f"{n_bars_2}{main_bar_type}{main_bar_dia_mm:.0f}",
            fontsize=10, ha="center", va="top", color="black", fontweight="bold")
    gx = x1 - 0.06
    ax.annotate("", xy=(gx, y0 + 0.03), xytext=(gx, y1 - 0.03),
                arrowprops=dict(arrowstyle="<->", color=GREEN, linewidth=1.6))
    ax.text(x1 + 0.16, 0, f"{n_bars_1}{main_bar_type}{main_bar_dia_mm:.0f}",
            fontsize=10, ha="left", va="center", color="black", fontweight="bold", rotation=90)

    # --- เส้นบอกระยะรวม A (ล่าง), B (ซ้าย) ---
    _dim_h_generic(ax, y0 - 0.34, x0, x1, f"A = {A_cm:.0f} cm.")
    _dim_v_generic(ax, x0 - 0.16, y0, y1, f"B = {B_cm:.0f} cm.")

    # --- เส้นบอกระยะย่อยด้านบน: ขอบ-เสาเข็ม-ศูนย์กลาง (ระยะขอบ/ระยะห่างเสาเข็ม) ---
    xs_p = sorted(set(round(px_cm / 100.0, 4) for (px_cm, _) in pile_positions_cm))
    bounds = sorted(set([x0] + xs_p + ([0.0] if 0.0 not in xs_p else []) + [x1]))
    ytop = y1 + 0.12
    ax.plot([bounds[0], bounds[-1]], [ytop, ytop], color=DIM_COLOR, linewidth=0.9, zorder=6)
    for bx in bounds:
        ax.plot([bx, bx], [ytop - 0.02, ytop + 0.02], color=DIM_COLOR, linewidth=0.9, zorder=6)
    for i in range(len(bounds) - 1):
        seg = (bounds[i + 1] - bounds[i]) * 100.0
        if seg < 1.0:
            continue
        ax.annotate("", xy=(bounds[i], ytop), xytext=(bounds[i + 1], ytop),
                    arrowprops=dict(arrowstyle="<->", color=DIM_COLOR, linewidth=0.8))
        ax.text((bounds[i] + bounds[i + 1]) / 2.0, ytop + 0.03, f"{seg:.0f}", fontsize=7.5,
                ha="center", va="bottom", color=DIM_COLOR)

    ax.text(0, ytop + 0.16, "Pile Cap Plan", fontsize=12.5, fontweight="bold",
            ha="center", va="bottom", color=CAPTION_COLOR)

    ax.set_xlim(x0 - 0.55, x1 + 1.0)
    ax.set_ylim(y0 - 0.55, ytop + 0.42)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()


def draw_pile_cap_section_png(A_cm: float, t_cm: float, column_b_cm: float, cover_cm: float,
                               pile_size_cm: float, c_dist_cm: float, n_piles_shown: int,
                               main_bar_dia_mm: float, main_bar_type: str,
                               d1_cm: float, d2_cm: float,
                               pile_safe_load_ton: float = None,
                               n_bars_1: int = 0, n_bars_2: int = 0,
                               pile_shape_label: str = None) -> bytes:
    """รูปตัดฐานรากเสาเข็ม (ตัดผ่านแนวเสา ตามแนวเรียงเสาเข็มทิศทาง#1) — ตามธรรมเนียมเดียวกับ
    draw_footing_section_png ของโมดูล 5.1 (ชั้นทราย/เลียน/GL/break line ที่หัวเสา) เพิ่มเสาเข็ม
    เป็นแท่งสี่เหลี่ยมยื่นลงมาใต้ฐานราก ที่ตำแหน่งจริงตาม c_dist_cm (ระยะศูนย์เสาเข็มริมจาก
    กึ่งกลาง) — n_piles_shown ใช้กำหนดว่าจะวาดเสาเข็มกี่ต้นในรูปตัดนี้ (2 = ซ้าย/ขวา, 3 =
    ซ้าย/กลาง/ขวา, มุมมองตัดผ่านแนวเรียงเดียวจึงไม่ต้องมีค่าอื่น — เสาเข็มแถวหลัง กรณี 4 ต้น
    จะซ้อนทับกับต้นหน้าในมุมมองนี้พอดี เพราะฐานรากจัตุรัส สมมาตร 2 ทิศเท่ากัน)."""
    # เขียนใหม่ 2026-07-12 ให้เหมือนแบบขยายไฟล์อ้างอิง "SDM Plus_Footing_*Pile Pu.xlsx"
    # (chart4: รูปตัด+เหล็กเสริมเต็มรูปแบบ) — วาดเป็นแบบวิศวกรรมโครงสร้างสะอาดๆ ไม่ใช่รูป GL/ดินถม
    # องค์ประกอบ: ฐานราก + ตอม่อ/เสา (break+hatch) + เสาเข็มฝังหัวเข้าฐานราก + เหล็กล่างหลักงอปลาย
    # (ตะขอ) + เหล็กทิศตั้งฉากเห็นหัวตัด (จุด) + เหล็ก dowel เสา (เขียว) + เส้นบอกระยะ (น้ำเงิน)
    GREEN = "#008000"
    DIMC = DIM_COLOR   # น้ำเงิน #0000CC

    fig, ax = plt.subplots(figsize=(9.6, 6.0), dpi=160)

    A_m, t_m = A_cm / 100.0, t_cm / 100.0
    col_b_m = column_b_cm / 100.0
    pile_w_m = pile_size_cm / 100.0
    c_dist_m = c_dist_cm / 100.0
    cover_m = cover_cm / 100.0
    bar_r_m = main_bar_dia_mm / 2000.0

    x0, x1 = -A_m / 2.0, A_m / 2.0

    if n_piles_shown == 1:
        pile_xs = [0.0]
    elif n_piles_shown == 3:
        pile_xs = [-c_dist_m, 0.0, c_dist_m]
    else:   # 2 หรือ 4 ต้น -> ตัดผ่านแถวเดียว 2 ต้น
        pile_xs = [-c_dist_m, c_dist_m]

    pile_len = max(0.45, 0.30 * A_m)          # ความยาวเสาเข็มที่วาด (schematic)
    embed = min(0.06, 0.4 * t_m)              # หัวเสาเข็มฝังเข้าใต้ฐานรากเล็กน้อย

    MAG = "#C000C0"      # ชมพู/ม่วง — ตะขอ & ป้าย Dowel (ตามรูปอ้างอิง)
    DOT = "#8B0000"      # แดงเข้ม — เหล็กทิศตั้งฉากเห็นหัวตัด
    ORANGE = "#E08A2B"
    lean_h, sand_h = 0.05, 0.10   # ชั้นคอนกรีตหยาบ (Lean) + ทราย (schematic, เมตร)

    # --- ชั้นทราย + คอนกรีตหยาบ (Lean) ใต้ฐานราก (ตามรูปอ้างอิง) ---
    ax.add_patch(patches.Rectangle((x0, -lean_h - sand_h), A_m, sand_h, fill=True,
                                    facecolor="#efe1bf", edgecolor="none", zorder=1))
    ax.plot([x0, x1], [-lean_h, -lean_h], color=ORANGE, linewidth=2.2, zorder=2)
    ax.text(x1 + 0.06, -lean_h + 0.008, "Lean 0.05 m.", fontsize=8, ha="left", va="center", color=ORANGE)
    ax.text(x1 + 0.06, -lean_h - sand_h * 0.5, "Sand 0.10 m.", fontsize=8, ha="left", va="center", color="#b8860b")

    # --- เสาเข็ม (เส้นประ = อยู่ใต้ฐานราก) ---
    for px in pile_xs:
        ax.add_patch(patches.Rectangle((px - pile_w_m / 2.0, -pile_len), pile_w_m, pile_len + embed,
                                        fill=True, facecolor="white", edgecolor=LINE_COLOR,
                                        linewidth=1.2, linestyle=(0, (5, 3)), zorder=4))

    # --- ฐานราก (Pile Cap) ---
    ax.add_patch(patches.Rectangle((x0, 0), A_m, t_m, fill=True, facecolor="white",
                                    edgecolor=LINE_COLOR, linewidth=1.9, zorder=5))

    # --- เสา/ตอม่อด้านบน (ปลายบนเส้นประ = ต่อขึ้นไป) ---
    stub_h = max(0.34, 0.95 * t_m)
    cxl, cxr = -col_b_m / 2.0, col_b_m / 2.0
    top = t_m + stub_h
    ax.plot([cxl, cxl], [t_m, top], color=LINE_COLOR, linewidth=1.7, zorder=6)
    ax.plot([cxr, cxr], [t_m, top], color=LINE_COLOR, linewidth=1.7, zorder=6)
    ax.plot([cxl, cxr], [top, top], color=LINE_COLOR, linewidth=1.0, linestyle=(0, (4, 3)), zorder=6)
    ax.text(cxr + 0.04, top - 0.02, "Column", fontsize=8.5, ha="left", va="top", color="#555555")

    # --- เหล็กรัดรอบ 1RB9 (Around) — วาดเป็นกรอบเหล็กปลอกสี่เหลี่ยม (tie loop) ระยะหุ้ม cover ---
    y_bar = cover_m
    y_hook = t_m - cover_m
    bxl, bxr = x0 + cover_m, x1 - cover_m
    ax.add_patch(patches.Rectangle((bxl, y_bar), bxr - bxl, y_hook - y_bar, fill=False,
                                    edgecolor=LINE_COLOR, linewidth=1.3, zorder=7))

    # --- เหล็กเสริมหลัก (เส้นประเขียว) ที่ท้องฐานราก + ตะขอปลายงอขึ้น (ชมพู) ---
    yb = y_bar + 0.012
    ax.plot([bxl + 0.008, bxr - 0.008], [yb, yb], color=GREEN, linewidth=2.2, zorder=8,
            linestyle=(0, (6, 3)))
    for hx in (bxl + 0.008, bxr - 0.008):
        ax.plot([hx, hx], [yb, y_hook - 0.006], color=MAG, linewidth=2.0, zorder=9)

    # --- เหล็กทิศตั้งฉาก เห็นหัวตัด (จุดแดงเข้ม) ---
    y_dot = yb + 0.020
    n_dots = min(max(int(A_m / 0.16), 5), 14)
    for i in range(n_dots):
        px = bxl + (i + 0.5) * (bxr - bxl) / n_dots
        ax.add_patch(patches.Circle((px, y_dot), 0.008, facecolor=DOT, edgecolor=DOT, zorder=8))

    # --- เหล็ก dowel เสา (เส้นประเขียว) หักฉากออกด้านข้าง + ตะขอชมพู + ป้าย "Dowel" ---
    dow_off = max(col_b_m / 2.0 - 0.035, 0.02)
    lap = min(0.16, 0.4 * (x1 - cxr) if x1 > cxr else 0.12)
    for sx in (-1.0, 1.0):
        dx = sx * dow_off
        ax.plot([dx, dx], [top - 0.06, y_bar + 0.05], color=GREEN, linewidth=1.8, zorder=9,
                linestyle=(0, (6, 3)))
        ax.plot([dx, dx + sx * lap], [y_bar + 0.05, y_bar + 0.05], color=GREEN, linewidth=1.8,
                zorder=9, linestyle=(0, (6, 3)))
        ax.plot([dx + sx * lap, dx + sx * lap], [y_bar + 0.05, y_bar + 0.10], color=MAG,
                linewidth=1.6, zorder=9)
        ax.text(dx + sx * 0.02, (top + t_m) / 2.0 + 0.03, "Dowel", fontsize=8, ha="center",
                va="center", color=MAG, fontweight="bold")   # ป้าย "Dowel" ที่ dowel แต่ละต้น

    # --- ป้ายเหล็ก (จำนวน + ขนาด เท่านั้น ตามที่ผู้ใช้สั่ง) ---
    lx = x1 + 0.16
    lbl1 = f"{n_bars_1}{main_bar_type}{main_bar_dia_mm:.0f}" if n_bars_1 else f"{main_bar_type}{main_bar_dia_mm:.0f}"
    lbl2 = f"{n_bars_2}{main_bar_type}{main_bar_dia_mm:.0f}" if n_bars_2 else f"{main_bar_type}{main_bar_dia_mm:.0f}"
    ax.annotate("1RB9 (Around)", xy=(bxr, y_hook), xytext=(lx, y_hook + 0.11),
                fontsize=8.5, ha="left", va="center", color="black",
                arrowprops=dict(arrowstyle="-", color=LINE_COLOR, linewidth=0.8))
    ax.annotate(lbl1, xy=(bxr - 0.02, yb), xytext=(lx, yb + 0.02),
                fontsize=9.5, ha="left", va="center", color="black", fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=LINE_COLOR, linewidth=0.8))
    ax.annotate(lbl2, xy=(bxr - 0.07, y_dot), xytext=(lx, yb - 0.09),
                fontsize=9.5, ha="left", va="center", color="black", fontweight="bold",
                arrowprops=dict(arrowstyle="-", color=LINE_COLOR, linewidth=0.8))

    # --- เส้นบอกระยะ (น้ำเงิน) ---
    # โซ่ระยะแนวตั้งด้านซ้าย: T (ฐานราก) + Lean + Sand ตามรูปอ้างอิง
    _dim_v_generic(ax, x0 - 0.16, 0, t_m, f"T={t_cm:.0f}")
    _dim_v_generic(ax, x0 - 0.16, -lean_h, 0.0, f"{lean_h*100:.0f}")
    _dim_v_generic(ax, x0 - 0.16, -lean_h - sand_h, -lean_h, f"{sand_h*100:.0f}")
    # ระยะหุ้มคอนกรีต (cover) มุมบนซ้ายในฐานราก
    _dim_h_generic(ax, y_hook + 0.02, x0, bxl, f"{cover_cm:.1f}")
    if len(pile_xs) >= 2:
        _dim_h_generic(ax, -lean_h - sand_h - 0.13, pile_xs[0], pile_xs[-1],
                       f"pile spacing = {2 * c_dist_cm:.0f} cm.")
    _dim_h_generic(ax, -pile_len - 0.14, x0, x1, f"A={A_cm:.0f} cm.")

    # --- หมายเหตุเสาเข็ม (มุมล่างขวา ตามรูป) ---
    _shape = pile_shape_label or "Pile"
    note = f"{n_piles_shown} {_shape}"
    if pile_safe_load_ton is not None:
        note += f"\nS.L >= {pile_safe_load_ton:.0f} t/pile"
    ax.text(x1 + 0.06, -pile_len + 0.04, note, fontsize=8.5, ha="left", va="bottom", color="#333333")

    ax.text(0, top + 0.16, "SECTION", fontsize=12.5, fontweight="bold",
            ha="center", va="bottom", color=CAPTION_COLOR)

    ax.set_xlim(x0 - 0.55, x1 + 1.35)
    ax.set_ylim(-pile_len - 0.40, top + 0.42)
    ax.set_aspect("equal")
    ax.axis("off")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    return buf.getvalue()
