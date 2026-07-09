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


def _ow_elbow_leader(ax, x0, y0, y1, x1, label, color=LINE_COLOR, fontsize=9.5, ha="left"):
    """Elbow leader: vertical segment (x0,y0)->(x0,y1) then horizontal to
    (x1,y1), label at the horizontal end — same convention as the Ground
    Slab callouts, confirmed against the One-way Slab reference leaders."""
    ax.plot([x0, x0], [y0, y1], color=color, linewidth=1.0)
    ax.plot([x0, x1], [y1, y1], color=color, linewidth=1.0)
    ax.text(x1 + (0.02 if ha == "left" else -0.02), y1, label, fontsize=fontsize,
             ha=ha, va="center", color="black")


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

    # ===================== LEFT PANEL: Top Bars =====================
    ax = axT
    ax.add_patch(patches.Rectangle((0, 0), W, H, fill=False, edgecolor=LINE_COLOR, linewidth=1.6, zorder=3))

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
                           cover_cm: float = 3.0) -> bytes:
    """Beam cross-section: outer concrete outline, stirrup outline (rounded
    rectangle, inset by cover), top/bottom bars as rows of dots — รองรับหลาย
    ชั้น (bottom_layers/top_layers รับได้ทั้ง int เดี่ยว หรือ list ของจำนวนเส้นต่อชั้น
    เรียงจากชั้นใกล้ผิวรับแรงดึงสุดออกไป เช่น [6,4] = ชั้น 1 มี 6 เส้น ชั้น 2 มี 4 เส้น —
    ตำแหน่งชั้นสอดคล้องกับ modules.beam_single_span._layer_y_distances_cm)."""
    fig, ax = plt.subplots(figsize=(5.2, 6.2), dpi=150)

    b_m, h_m = b_cm / 100.0, h_cm / 100.0
    cover_m = cover_cm / 100.0
    stirrup_r_m = stirrup_dia_mm / 1000.0

    # concrete outline
    ax.add_patch(patches.Rectangle((0, 0), b_m, h_m, fill=False, edgecolor=LINE_COLOR, linewidth=1.8))

    # stirrup outline (rounded corners approximated with a slightly-inset rectangle)
    inset = cover_m
    ax.add_patch(patches.FancyBboxPatch(
        (inset, inset), b_m - 2 * inset, h_m - 2 * inset,
        boxstyle="round,pad=0,rounding_size=0.015",
        fill=False, edgecolor="#555555", linewidth=1.2))

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

    ax.annotate(f"{stirrup_bar_type}{stirrup_dia_mm:.0f}@{stirrup_spacing_cm:.0f}cm. (Stirrup)",
                xy=(inset, h_m / 2.0), xytext=(-0.30, h_m / 2.0),
                fontsize=9, va="center", ha="right", color="#555555",
                arrowprops=dict(arrowstyle="-", color="#555555", linewidth=0.8))

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
