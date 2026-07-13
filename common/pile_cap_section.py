"""
common/pile_cap_section.py
==========================
Reusable, fully-parametric RC **Pile Cap SECTION** drawing component (SVG).

Architecture (NOT "trace the picture"):
        Input parameters  ->  Geometry Engine  ->  Coordinates  ->  Draw
Every coordinate is computed by the geometry engine (`build_geometry`) from
engineering inputs in millimetres, in a world coordinate system (mm, y-up,
x centred on the column axis).  One global scale (pixels_per_mm) maps world ->
SVG.  There are NO hardcoded object coordinates and NO magic numbers in the
geometry — the only literals are line weights / font heights (drafting style).

Reinforcement is drawn from real detailing rules:
  * bottom bars: equally spaced from  width, side-cover, bar count
  * closed stirrup: offset by the cover from ALL faces (encloses every bar)
  * dowels: start inside the column (at column bars), run DOWN to the bottom-bar
    level, then bend and lap ALONG the bottom bars (bend at the same level as the
    main steel), with a hook
Output: responsive SVG; export to SVG / PDF / PNG (PDF & PNG need `cairosvg`).
"""

from dataclasses import dataclass, field
from typing import List, Optional


# ======================================================================
# INPUT PARAMETERS  (all lengths in millimetres)
# ======================================================================
@dataclass
class PileCap:
    width_mm: float
    thickness_mm: float


@dataclass
class Pedestal:
    width_mm: float
    height_mm: float


@dataclass
class Column:
    width_mm: float
    depth_mm: float = 0.0
    projection_mm: float = 0.0     # 0 -> auto = 1.3 * cap thickness


@dataclass
class Piles:
    count: int                     # 2, 3, 4 or 6
    diameter_mm: float
    spacing_mm: float
    length_mm: float = 0.0         # 0 -> auto = max(3*dia, 1.5*T)


@dataclass
class Cover:
    bottom_mm: float
    side_mm: float
    top_mm: float


@dataclass
class BottomReinf:
    bar_dia_mm: float
    num_bars: int
    spacing_mm: float = 0.0


@dataclass
class TopReinf:
    bar_dia_mm: float
    num_bars: int


@dataclass
class Dowel:
    bar_dia_mm: float
    development_length_mm: float
    hook_length_mm: float


@dataclass
class Stirrups:
    dia_mm: float
    spacing_mm: float = 0.0


@dataclass
class FoundationLayers:
    lean_thickness_mm: float
    sand_thickness_mm: float


@dataclass
class Texts:
    bottom_callout: str = ""
    top_callout: str = ""
    around_callout: str = ""
    pile_desc: str = ""
    safe_load: str = ""
    title: str = "SECTION"


@dataclass
class PileCapSectionParams:
    pile_cap: PileCap
    pedestal: Pedestal
    column: Column
    piles: Piles
    cover: Cover
    bottom_reinf: BottomReinf
    top_reinf: TopReinf
    dowel: Dowel
    stirrups: Stirrups
    layers: FoundationLayers
    texts: Texts = field(default_factory=Texts)


# ======================================================================
# STYLE
# ======================================================================
COLORS = {
    "concrete": "#000000", "dim": "#0000CC", "rebar": "#008000",
    "center": "#9A9A9A", "soil": "#E08A2B", "bottom_bar": "#B00000",
    "hook": "#C000C0", "text": "#111111", "title": "#0A7A0A",
}
LW = {"concrete": 6.0, "pedestal": 5.0, "rebar": 3.5, "stirrup": 3.0,
      "dim": 2.0, "center": 1.8, "soil": 3.0, "hook": 3.2}
FONT = {"label": 40.0, "dim": 30.0, "title": 60.0, "small": 28.0}


def _m(mm: float) -> str:
    """Format a millimetre length as metres (engineering label)."""
    return f"{mm/1000.0:.3f}"


# ======================================================================
# LOW-LEVEL SVG CANVAS  (world mm, y-up -> SVG user units)
# ======================================================================
def _f(v: float) -> str:
    return f"{v:.2f}"


class Canvas:
    def __init__(self, xmin, xmax, ymin, ymax, scale=1.0):
        self.xmin, self.xmax, self.ymin, self.ymax = xmin, xmax, ymin, ymax
        self.scale = scale
        self._el: List[str] = []

    def X(self, x): return (x - self.xmin) * self.scale
    def Y(self, y): return (self.ymax - y) * self.scale

    def _w(self, key): return (LW.get(key, key) if isinstance(key, str) else key) * self.scale

    def line(self, x1, y1, x2, y2, color, w, dash=None):
        d = f' stroke-dasharray="{_f(dash[0]*self.scale)},{_f(dash[1]*self.scale)}"' if dash else ""
        self._el.append(f'<line x1="{_f(self.X(x1))}" y1="{_f(self.Y(y1))}" x2="{_f(self.X(x2))}" '
                        f'y2="{_f(self.Y(y2))}" stroke="{color}" stroke-width="{_f(self._w(w))}"{d} '
                        f'stroke-linecap="round"/>')

    def rect(self, x, y, w_mm, h_mm, color, w, fill="none", dash=None):
        d = f' stroke-dasharray="{_f(dash[0]*self.scale)},{_f(dash[1]*self.scale)}"' if dash else ""
        self._el.append(f'<rect x="{_f(self.X(x))}" y="{_f(self.Y(y+h_mm))}" '
                        f'width="{_f(w_mm*self.scale)}" height="{_f(h_mm*self.scale)}" fill="{fill}" '
                        f'stroke="{color}" stroke-width="{_f(self._w(w))}"{d}/>')

    def circle(self, x, y, r_mm, color, w, fill="none"):
        self._el.append(f'<circle cx="{_f(self.X(x))}" cy="{_f(self.Y(y))}" r="{_f(r_mm*self.scale)}" '
                        f'fill="{fill}" stroke="{color}" stroke-width="{_f(self._w(w))}"/>')

    def polyline(self, pts, color, w, dash=None, fill="none"):
        d = f' stroke-dasharray="{_f(dash[0]*self.scale)},{_f(dash[1]*self.scale)}"' if dash else ""
        s = " ".join(f"{_f(self.X(px))},{_f(self.Y(py))}" for px, py in pts)
        self._el.append(f'<polyline points="{s}" fill="{fill}" stroke="{color}" '
                        f'stroke-width="{_f(self._w(w))}"{d} stroke-linejoin="round" stroke-linecap="round"/>')

    def text(self, x, y, s, color, font_mm, anchor="middle", weight="normal", rotate=0.0,
             dx=0.0, dy=0.0):
        px, py = self.X(x) + dx * self.scale, self.Y(y) + dy * self.scale
        tr = f' transform="rotate({_f(rotate)} {_f(px)} {_f(py)})"' if rotate else ""
        s = s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self._el.append(f'<text x="{_f(px)}" y="{_f(py)}" fill="{color}" font-family="Arial, sans-serif" '
                        f'font-size="{_f(font_mm*self.scale)}" font-weight="{weight}" text-anchor="{anchor}" '
                        f'dominant-baseline="middle"{tr}>{s}</text>')

    def svg(self):
        w, h = (self.xmax - self.xmin) * self.scale, (self.ymax - self.ymin) * self.scale
        return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {_f(w)} {_f(h)}" width="100%" '
                f'preserveAspectRatio="xMidYMid meet">\n'
                f'<rect x="0" y="0" width="{_f(w)}" height="{_f(h)}" fill="white"/>\n'
                + "\n".join(self._el) + "\n</svg>")


# ======================================================================
# GEOMETRY ENGINE
# ======================================================================
@dataclass
class Geometry:
    W: float; T: float
    cap_top: float; cap_bottom: float
    has_ped: bool; ped_l: float; ped_r: float; ped_top: float
    col_l: float; col_r: float; col_bottom: float; col_top: float
    lean_bottom: float; sand_bottom: float
    pile_xs: List[float]; pile_w: float; pile_top: float; pile_bottom: float
    stir_l: float; stir_r: float; stir_b: float; stir_t: float; stir_dia: float
    bot_y: float; top_y: float; bot_xs: List[float]
    dowel_xs: List[float]
    side_cover: float; bottom_cover: float; top_cover: float


def _pile_positions(count: int, spacing: float) -> List[float]:
    """Section-cut pile x-positions, symmetric about the centre line, from spacing."""
    if count <= 1:
        return [0.0]
    if count in (2, 4):                      # one row of two
        return [-spacing / 2.0, spacing / 2.0]
    return [-spacing, 0.0, spacing]          # 3 (inline) or 6 (row of three)


def build_geometry(p: PileCapSectionParams) -> Geometry:
    pc, pd, col, pl, cv = p.pile_cap, p.pedestal, p.column, p.piles, p.cover
    W, T = pc.width_mm, pc.thickness_mm
    cap_top, cap_bottom = 0.0, -T

    has_ped = pd.height_mm > 0.0
    ped_top = cap_top + (pd.height_mm if has_ped else 0.0)
    ped_hw = (pd.width_mm if has_ped else col.width_mm) / 2.0
    ped_l, ped_r = -ped_hw, ped_hw

    col_bottom = ped_top
    col_proj = col.projection_mm or 1.0 * T
    col_top = col_bottom + col_proj
    col_l, col_r = -col.width_mm / 2.0, col.width_mm / 2.0

    lean_bottom = cap_bottom - p.layers.lean_thickness_mm
    sand_bottom = lean_bottom - p.layers.sand_thickness_mm

    pile_xs = _pile_positions(pl.count, pl.spacing_mm)
    pile_w = pl.diameter_mm
    # display stub: pass through lean + sand and a little below (template style, not full length)
    pile_len = pl.length_mm or (p.layers.lean_thickness_mm + p.layers.sand_thickness_mm + 0.85 * T)
    pile_top = cap_bottom + min(0.35 * T, 0.5 * pl.diameter_mm)     # small embed into cap
    pile_bottom = cap_bottom - pile_len

    # closed stirrup: offset by the cover from every cap face (encloses all bars)
    sd = p.stirrups.dia_mm
    stir_l, stir_r = -W / 2.0 + cv.side_mm, W / 2.0 - cv.side_mm
    stir_b, stir_t = cap_bottom + cv.bottom_mm, cap_top - cv.top_mm

    # bar centroid levels (inside the stirrup)
    bd = p.bottom_reinf.bar_dia_mm
    td = p.top_reinf.bar_dia_mm
    bot_y = stir_b + sd + bd / 2.0
    top_y = stir_t - sd - td / 2.0

    # bottom bars: equally spaced across the clear width inside the stirrup
    n = max(int(p.bottom_reinf.num_bars), 1)
    inner_l = stir_l + sd + bd / 2.0
    inner_r = stir_r - sd - bd / 2.0
    bot_xs = [0.0] if n == 1 else [inner_l + (inner_r - inner_l) * i / (n - 1) for i in range(n)]

    # dowels: at the column bars (inside the column by its cover), symmetric
    dcov = cv.side_mm
    dxo = max(col.width_mm / 2.0 - dcov, 0.05 * col.width_mm)
    dowel_xs = [-dxo, dxo]

    return Geometry(W, T, cap_top, cap_bottom, has_ped, ped_l, ped_r, ped_top,
                    col_l, col_r, col_bottom, col_top, lean_bottom, sand_bottom,
                    pile_xs, pile_w, pile_top, pile_bottom,
                    stir_l, stir_r, stir_b, stir_t, sd, bot_y, top_y, bot_xs, dowel_xs,
                    cv.side_mm, cv.bottom_mm, cv.top_mm)


# ======================================================================
# VALIDATION  (STEP 4 — "if validation fails DO NOT RENDER")
# ======================================================================
class GeometryError(Exception):
    """Raised when the computed geometry violates an engineering rule."""


def validateGeometry(g: Geometry, p: PileCapSectionParams) -> List[str]:
    """Return a list of rule violations.  Empty list => geometry is valid."""
    e: List[str] = []
    eps = 1e-6

    # 1) all steel inside the concrete cap
    for x in g.bot_xs:
        if not (-g.W / 2.0 - eps <= x <= g.W / 2.0 + eps):
            e.append(f"bottom bar x={x:.0f}mm is outside the cap width")
    if not (g.cap_bottom < g.bot_y < g.cap_top):
        e.append("bottom-bar level is not inside the cap")
    if p.top_reinf.num_bars > 0 and not (g.cap_bottom < g.top_y < g.cap_top):
        e.append("top-bar level is not inside the cap")

    # 2) cover satisfied on every face
    if g.bot_y - g.cap_bottom < g.bottom_cover - eps:
        e.append("bottom cover is violated")
    if g.cap_top - g.top_y < g.top_cover - eps and p.top_reinf.num_bars > 0:
        e.append("top cover is violated")
    if g.bot_xs:
        if min(g.bot_xs) - (-g.W / 2.0) < g.side_cover - eps:
            e.append("side cover is violated (left)")
        if (g.W / 2.0) - max(g.bot_xs) < g.side_cover - eps:
            e.append("side cover is violated (right)")

    # 3) closed stirrup must enclose every bar
    if g.bot_xs and not (g.stir_l - eps <= min(g.bot_xs) and max(g.bot_xs) <= g.stir_r + eps):
        e.append("stirrup does not enclose the bottom bars (horizontal)")
    if not (g.stir_b - eps <= g.bot_y <= g.stir_t + eps):
        e.append("stirrup does not enclose the bottom bars (vertical)")

    # 4) dowel must reach the bottom steel: it starts high in the column and runs DOWN to
    #    g.bot_y, so the column top must sit above the bottom-bar level
    if not (g.col_top > g.bot_y):
        e.append("dowel cannot reach the bottom steel (column top not above bar level)")

    # 5) column & pedestal centred on the axis; cap >= pedestal >= column
    if abs(g.col_l + g.col_r) > 1e-3:
        e.append("column is not centred on the axis")
    if g.has_ped:
        if abs(g.ped_l + g.ped_r) > 1e-3:
            e.append("pedestal is not centred on the axis")
        if (g.ped_r - g.ped_l) < (g.col_r - g.col_l) - eps:
            e.append("pedestal is narrower than the column")
        if g.W < (g.ped_r - g.ped_l) - eps:
            e.append("pile cap is narrower than the pedestal")

    # 6) piles: symmetric about the axis and under the cap
    if g.pile_xs:
        if abs(sum(g.pile_xs)) > 1e-3:
            e.append("piles are not symmetric about the centre line")
        for x in g.pile_xs:
            if x - g.pile_w / 2.0 < -g.W / 2.0 - eps or x + g.pile_w / 2.0 > g.W / 2.0 + eps:
                e.append(f"pile at x={x:.0f}mm extends beyond the cap width")

    # 7) foundation layers ordered top->down
    if not (g.sand_bottom < g.lean_bottom < g.cap_bottom < g.cap_top):
        e.append("foundation layer ordering is invalid")

    return e


# ======================================================================
# DRAW FUNCTIONS  (each object; order set in render())
# ======================================================================
def drawSandLayer(cv, g, p):
    cv.rect(-g.W / 2.0, g.sand_bottom, g.W, g.lean_bottom - g.sand_bottom,
            COLORS["soil"], "soil", fill="#f3e6c6")
    cv.line(-g.W / 2.0, g.lean_bottom, g.W / 2.0, g.lean_bottom, COLORS["soil"], "soil")


def drawLeanConcrete(cv, g, p):
    cv.line(-g.W / 2.0, g.cap_bottom, g.W / 2.0, g.cap_bottom, COLORS["soil"], "soil")


def drawPiles(cv, g, p):
    for x in g.pile_xs:
        cv.rect(x - g.pile_w / 2.0, g.pile_bottom, g.pile_w, g.pile_top - g.pile_bottom,
                COLORS["concrete"], "pedestal", fill="white", dash=(26, 16))


def drawPileCap(cv, g, p):
    cv.rect(-g.W / 2.0, g.cap_bottom, g.W, g.T, COLORS["concrete"], "concrete", fill="white")


def drawPedestal(cv, g, p):
    if not g.has_ped:
        return
    cv.rect(g.ped_l, g.cap_top, g.ped_r - g.ped_l, g.ped_top - g.cap_top,
            COLORS["concrete"], "pedestal", fill="white")
    cv.line(g.ped_l, g.cap_top, g.ped_r, g.cap_top, "white", LW["pedestal"] * 0.9)  # merge with cap


def drawColumn(cv, g, p):
    cv.line(g.col_l, g.col_bottom, g.col_l, g.col_top, COLORS["concrete"], "pedestal")
    cv.line(g.col_r, g.col_bottom, g.col_r, g.col_top, COLORS["concrete"], "pedestal")
    cv.line(g.col_l, g.col_top, g.col_r, g.col_top, COLORS["concrete"], "center", dash=(22, 16))
    cv.line(g.col_l, g.col_bottom, g.col_r, g.col_bottom, "white", LW["pedestal"] * 0.9)  # merge


def drawCenterLine(cv, g, p):
    cv.line(0, g.col_top + 0.10 * (g.col_top - g.col_bottom), 0, g.pile_bottom - 0.05 * g.T,
            COLORS["center"], "center", dash=(42, 12, 8, 12))


def drawStirrups(cv, g, p):
    # closed perimeter tie enclosing all bars (= "1RB9 Around"), equal cover all round
    cv.rect(g.stir_l, g.stir_b, g.stir_r - g.stir_l, g.stir_t - g.stir_b,
            COLORS["concrete"], "stirrup", fill="none")


def drawBottomBars(cv, g, p):
    # perpendicular (into-page) bottom bars seen in section -> equally spaced red dots
    r = max(p.bottom_reinf.bar_dia_mm / 2.0, 0.004 * g.W)
    for x in g.bot_xs:
        cv.circle(x, g.bot_y, r, COLORS["bottom_bar"], 1.2, fill=COLORS["bottom_bar"])
    # in-plane bottom bar (green) with standard hooks turned up at both ends
    hook_up = min(g.stir_t, g.bot_y + p.dowel.hook_length_mm)
    cv.polyline([(g.bot_xs[0] if len(g.bot_xs) > 1 else g.stir_l + g.stir_dia, hook_up),
                 (g.bot_xs[0] if len(g.bot_xs) > 1 else g.stir_l + g.stir_dia, g.bot_y),
                 (g.bot_xs[-1] if len(g.bot_xs) > 1 else g.stir_r - g.stir_dia, g.bot_y),
                 (g.bot_xs[-1] if len(g.bot_xs) > 1 else g.stir_r - g.stir_dia, hook_up)],
                COLORS["rebar"], "rebar", dash=(30, 16))


def drawTopBars(cv, g, p):
    if p.top_reinf.num_bars <= 0:
        return
    cv.line(g.stir_l + g.stir_dia, g.top_y, g.stir_r - g.stir_dia, g.top_y,
            COLORS["rebar"], "rebar", dash=(30, 16))


def drawDowels(cv, g, p):
    # dowels: embedded in the column, DOWN to the bottom-bar level, then bent and
    # lapped ALONG the bottom bars (bend at the same level as the main steel) + hook up
    ld = min(p.dowel.development_length_mm, (g.stir_r - g.stir_dia) - max(g.dowel_xs))
    hk = min(p.dowel.hook_length_mm, 0.8 * (g.stir_t - g.bot_y))
    top_anchor = g.col_bottom + 0.75 * (g.col_top - g.col_bottom)   # up inside the column
    for x in g.dowel_xs:
        s = 1.0 if x >= 0 else -1.0
        cv.polyline([(x, top_anchor), (x, g.bot_y), (x + s * ld, g.bot_y)],
                    COLORS["rebar"], "rebar")
        cv.line(x + s * ld, g.bot_y, x + s * ld, g.bot_y + hk, COLORS["hook"], "hook")
    xl = min(g.dowel_xs)
    cv.text(xl - 0.03 * g.W, (g.cap_top + g.col_bottom) / 2.0 + 0.30 * (g.col_top - g.col_bottom),
            "Dowel", COLORS["hook"], FONT["small"], weight="bold", anchor="end")


# ----- dimension primitives (blue, architectural tick) -----
def _tick(cv, x, y, color):
    t = 0.014 * (cv.xmax - cv.xmin)
    cv.line(x - t, y - t, x + t, y + t, color, "dim")


def _ext(cv, x1, y1, x2, y2, color):
    cv.line(x1, y1, x2, y2, color, "dim")


def _dim_h(cv, x1, x2, y, text, color=None, text_dy=None):
    color = color or COLORS["dim"]
    cv.line(x1, y, x2, y, color, "dim")
    _tick(cv, x1, y, color); _tick(cv, x2, y, color)
    dy = text_dy if text_dy is not None else -1.0 * FONT["dim"]
    cv.text((x1 + x2) / 2.0, y, text, color, FONT["dim"], anchor="middle", dy=dy * cv.scale)


def _dim_v(cv, x, y1, y2, text, color=None):
    color = color or COLORS["dim"]
    cv.line(x, y1, x, y2, color, "dim")
    _tick(cv, x, y1, color); _tick(cv, x, y2, color)
    cv.text(x, (y1 + y2) / 2.0, text, color, FONT["dim"], anchor="middle", rotate=-90,
            dx=-1.0 * FONT["dim"])


def drawDimensions(cv, g, p):
    W, T = g.W, g.T
    L = W / 2.0
    # ---- left vertical chain (nested): T + pedestal on inner gutter, overall on outer ----
    #      lean & sand are short segments -> labelled as text on the right (no tiny dims here,
    #      so nothing overlaps in this gutter)
    gx1 = -L - 0.09 * W
    gx2 = -L - 0.22 * W
    for yy in (g.col_top, g.ped_top, g.cap_top, g.cap_bottom, g.lean_bottom, g.sand_bottom):
        _ext(cv, -L, yy, gx2 - 0.02 * W, yy, COLORS["center"])
    _dim_v(cv, gx1, g.cap_bottom, g.cap_top, _m(T))                       # pile-cap thickness
    if g.has_ped:
        _dim_v(cv, gx1, g.cap_top, g.ped_top, _m(g.ped_top - g.cap_top))  # pedestal height
    _dim_v(cv, gx2, g.sand_bottom, g.col_top, _m(g.col_top - g.sand_bottom))          # overall height

    # ---- top horizontal: column width + pedestal width ----
    _ext(cv, g.col_l, g.col_top, g.col_l, g.col_top + 0.10 * W, COLORS["center"])
    _ext(cv, g.col_r, g.col_top, g.col_r, g.col_top + 0.10 * W, COLORS["center"])
    _dim_h(cv, g.col_l, g.col_r, g.col_top + 0.09 * W, _m(g.col_r - g.col_l))
    if g.has_ped:
        _dim_h(cv, g.ped_l, g.ped_r, g.col_top + 0.09 * W - 0.055 * W, _m(g.ped_r - g.ped_l),
               text_dy=1.1 * FONT["dim"])

    # ---- covers (bottom-left corner): side cover + bottom cover ----
    _dim_h(cv, -L, g.stir_l, g.cap_top + 0.10 * T, _m(g.side_cover))
    _dim_v(cv, g.stir_l - 0.02 * W, g.cap_bottom, g.bot_y, _m(g.bottom_cover))

    # ---- bottom horizontals: pile diameter, pile spacing, overall width ----
    yb1 = g.pile_bottom - 0.10 * T
    yb2 = g.pile_bottom - 0.35 * T
    yb3 = g.pile_bottom - 0.62 * T
    px = g.pile_xs[0]
    _dim_h(cv, px - g.pile_w / 2.0, px + g.pile_w / 2.0, yb1, _m(g.pile_w))
    if len(g.pile_xs) >= 2:
        _dim_h(cv, g.pile_xs[0], g.pile_xs[-1], yb2, _m(g.pile_xs[-1] - g.pile_xs[0]))
    _dim_h(cv, -L, L, yb3, f"A = {_m(W)} m.")


def drawTexts(cv, g, p):
    t, W = p.texts, g.W
    lx = W / 2.0 + 0.05 * W
    if t.around_callout:
        cv.line(g.stir_r, g.stir_t, lx, g.stir_t + 0.10 * g.T, COLORS["concrete"], "dim")
        cv.text(lx, g.stir_t + 0.10 * g.T, t.around_callout, COLORS["text"], FONT["label"], anchor="start")
    if t.top_callout:
        cv.line(g.stir_r - g.stir_dia, g.top_y, lx, g.top_y, COLORS["concrete"], "dim")
        cv.text(lx, g.top_y, t.top_callout, COLORS["text"], FONT["label"], anchor="start", weight="bold")
    if t.bottom_callout:
        cv.line(g.stir_r - g.stir_dia, g.bot_y, lx, g.bot_y, COLORS["concrete"], "dim")
        cv.text(lx, g.bot_y, t.bottom_callout, COLORS["text"], FONT["label"], anchor="start", weight="bold")
    cv.text(lx, g.cap_bottom - 0.5 * p.layers.lean_thickness_mm,
            f"Lean {_m(p.layers.lean_thickness_mm)} m.", COLORS["soil"], FONT["small"], anchor="start")
    cv.text(lx, g.lean_bottom - 0.5 * p.layers.sand_thickness_mm,
            f"Sand {_m(p.layers.sand_thickness_mm)} m.", COLORS["soil"], FONT["small"], anchor="start")
    yb = g.pile_bottom + 0.35 * (g.cap_bottom - g.pile_bottom)
    if t.pile_desc:
        cv.text(lx, yb, t.pile_desc, COLORS["text"], FONT["small"], anchor="start")
    if t.safe_load:
        cv.text(lx, yb - FONT["small"] * 1.3, t.safe_load, COLORS["text"], FONT["small"], anchor="start")
    cv.text(0, g.pile_bottom - 0.95 * g.T, t.title, COLORS["title"], FONT["title"],
            anchor="middle", weight="bold")


# ======================================================================
# RENDER
# ======================================================================
def render(p: PileCapSectionParams, scale: float = 0.35, validate: bool = True) -> str:
    # STEP 1 read params -> STEP 2/3 build model & coordinates
    g = build_geometry(p)
    # STEP 4 validate -> if it fails DO NOT RENDER, raise the validation error
    if validate:
        errs = validateGeometry(g, p)
        if errs:
            raise GeometryError("การตรวจสอบเรขาคณิตไม่ผ่าน:\n- " + "\n- ".join(errs))
    # STEP 5 render
    W, T = g.W, g.T
    xmin = -W / 2.0 - 0.32 * W
    xmax = W / 2.0 + 0.55 * W
    ymax = g.col_top + 0.16 * (g.col_top - g.col_bottom)
    ymin = g.pile_bottom - 1.15 * T
    cv = Canvas(xmin, xmax, ymin, ymax, scale=scale)

    drawSandLayer(cv, g, p)
    drawPiles(cv, g, p)
    drawLeanConcrete(cv, g, p)
    drawPileCap(cv, g, p)
    drawPedestal(cv, g, p)
    drawColumn(cv, g, p)
    drawCenterLine(cv, g, p)
    drawStirrups(cv, g, p)
    drawTopBars(cv, g, p)
    drawBottomBars(cv, g, p)
    drawDowels(cv, g, p)
    drawDimensions(cv, g, p)
    drawTexts(cv, g, p)
    return cv.svg()


# ---- export helpers -------------------------------------------------
def _error_card_svg(msg: str, scale: float = 0.35) -> str:
    """Fallback drawing used when validateGeometry() fails — shows the reason."""
    cv = Canvas(0, 1600, 0, 900, scale=scale)
    cv._el.append('<rect x="0" y="0" width="%s" height="%s" fill="#fff5f5" stroke="#B00000" '
                  'stroke-width="6"/>' % (_f(1600 * scale), _f(900 * scale)))
    cv.text(800, 780, "ตรวจสอบเรขาคณิตไม่ผ่าน — ไม่วาดรูป", "#B00000", 60, weight="bold")
    for i, ln in enumerate(msg.splitlines()):
        cv.text(120, 660 - i * 70, ln, "#7A0000", 38, anchor="start")
    return cv.svg()


def render_safe(p: PileCapSectionParams, scale: float = 0.35):
    """Return (svg, errors).  On failure returns an error-card SVG instead of raising."""
    g = build_geometry(p)
    errs = validateGeometry(g, p)
    if errs:
        return _error_card_svg("การตรวจสอบเรขาคณิตไม่ผ่าน:\n" + "\n".join(errs), scale), errs
    return render(p, scale=scale, validate=False), []


def to_svg(p, path=None, scale=0.35):
    svg, _ = render_safe(p, scale=scale)
    if path:
        open(path, "w", encoding="utf-8").write(svg)
    return svg


def to_pdf(p, path, scale=0.35):
    try:
        import cairosvg
    except Exception:
        return False
    svg, _ = render_safe(p, scale=scale)
    cairosvg.svg2pdf(bytestring=svg.encode("utf-8"), write_to=path)
    return True


def to_png_bytes(p, scale=0.35, output_width=None):
    try:
        import cairosvg
    except Exception:
        return None
    svg, _ = render_safe(p, scale=scale)
    kw = {"output_width": output_width} if output_width else {}
    return cairosvg.svg2png(bytestring=svg.encode("utf-8"), **kw)


# ======================================================================
# MATPLOTLIB RENDERER  (same geometry engine + validation, no cairosvg dep)
#   -> used by the app so the drawing renders even where Cairo is absent.
#   World coords are millimetres, y-up (matplotlib native — no flip needed).
# ======================================================================
_MPL_LW = {"concrete": 2.4, "pedestal": 1.9, "rebar": 1.5, "stirrup": 1.25,
           "dim": 0.8, "center": 0.8, "soil": 1.1, "hook": 1.35}
_MPL_FS = {"label": 12.5, "dim": 10.0, "title": 18.0, "small": 9.5}


def _mpl_tick(ax, x, y, span, color):
    t = 0.012 * span
    ax.plot([x - t, x + t], [y - t, y + t], color=color, lw=_MPL_LW["dim"], solid_capstyle="round")


def _mpl_dim_h(ax, x1, x2, y, text, span, color, dy):
    ax.plot([x1, x2], [y, y], color=color, lw=_MPL_LW["dim"])
    _mpl_tick(ax, x1, y, span, color); _mpl_tick(ax, x2, y, span, color)
    ax.text((x1 + x2) / 2.0, y + dy, text, color=color, fontsize=_MPL_FS["dim"],
            ha="center", va="bottom")


def _mpl_dim_v(ax, x, y1, y2, text, span, color):
    ax.plot([x, x], [y1, y2], color=color, lw=_MPL_LW["dim"])
    _mpl_tick(ax, x, y1, span, color); _mpl_tick(ax, x, y2, span, color)
    ax.text(x - 0.012 * span, (y1 + y2) / 2.0, text, color=color, fontsize=_MPL_FS["dim"],
            ha="center", va="center", rotation=90)


def render_png_mpl(p: PileCapSectionParams, dpi: int = 200):
    """Render the section with matplotlib from the geometry engine. Returns PNG bytes.
    If validateGeometry() fails, returns an error card instead of the drawing."""
    import io
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle, Circle

    g = build_geometry(p)
    errs = validateGeometry(g, p)

    W, T = g.W, g.T
    xmin, xmax = -W / 2.0 - 0.32 * W, W / 2.0 + 0.58 * W
    ymax = g.col_top + 0.16 * (g.col_top - g.col_bottom)
    ymin = g.pile_bottom - 1.20 * T
    xspan = xmax - xmin

    fig_w = 11.0
    fig_h = fig_w * (ymax - ymin) / xspan
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=dpi)
    ax.set_xlim(xmin, xmax); ax.set_ylim(ymin, ymax)
    ax.set_aspect("equal"); ax.axis("off")

    if errs:                                   # STEP4 failed -> DO NOT draw the section
        ax.text(0.5, 0.62, "ตรวจสอบเรขาคณิตไม่ผ่าน — ไม่วาดรูป", transform=ax.transAxes,
                ha="center", color=COLORS["bottom_bar"], fontsize=_MPL_FS["title"], fontweight="bold")
        for i, ln in enumerate(errs):
            ax.text(0.5, 0.5 - i * 0.05, ln, transform=ax.transAxes, ha="center",
                    color="#7A0000", fontsize=_MPL_FS["small"])
        buf = io.BytesIO(); fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
        plt.close(fig); return buf.getvalue()

    C = COLORS

    # ---- sand + lean ----
    ax.add_patch(Rectangle((-W / 2.0, g.sand_bottom), W, g.lean_bottom - g.sand_bottom,
                           facecolor="#f3e6c6", edgecolor=C["soil"], lw=_MPL_LW["soil"]))
    ax.plot([-W / 2.0, W / 2.0], [g.lean_bottom, g.lean_bottom], color=C["soil"], lw=_MPL_LW["soil"])
    ax.plot([-W / 2.0, W / 2.0], [g.cap_bottom, g.cap_bottom], color=C["soil"], lw=_MPL_LW["soil"])

    # ---- piles (solid stub outline, template style) ----
    for x in g.pile_xs:
        ax.add_patch(Rectangle((x - g.pile_w / 2.0, g.pile_bottom), g.pile_w,
                               g.pile_top - g.pile_bottom, fill=False, edgecolor=C["concrete"],
                               lw=_MPL_LW["stirrup"]))

    # ---- pile cap / pedestal / column (Column -> Pedestal -> Pile Cap) ----
    ax.add_patch(Rectangle((-W / 2.0, g.cap_bottom), W, T, fill=False,
                           edgecolor=C["concrete"], lw=_MPL_LW["concrete"]))
    if g.has_ped:
        ax.add_patch(Rectangle((g.ped_l, g.cap_top), g.ped_r - g.ped_l, g.ped_top - g.cap_top,
                               fill=False, edgecolor=C["concrete"], lw=_MPL_LW["pedestal"]))
        ax.plot([g.ped_l, g.ped_r], [g.cap_top, g.cap_top], color="white", lw=_MPL_LW["pedestal"])
    ax.plot([g.col_l, g.col_l], [g.col_bottom, g.col_top], color=C["concrete"], lw=_MPL_LW["pedestal"])
    ax.plot([g.col_r, g.col_r], [g.col_bottom, g.col_top], color=C["concrete"], lw=_MPL_LW["pedestal"])
    ax.plot([g.col_l, g.col_r], [g.col_top, g.col_top], color=C["center"], lw=_MPL_LW["center"],
            linestyle=(0, (6, 4)))
    ax.plot([g.col_l, g.col_r], [g.col_bottom, g.col_bottom], color="white", lw=_MPL_LW["pedestal"])

    # ---- centre line (dash-dot through everything) ----
    ax.plot([0, 0], [g.col_top + 0.10 * (g.col_top - g.col_bottom), g.pile_bottom - 0.05 * T],
            color=C["center"], lw=_MPL_LW["center"], linestyle=(0, (10, 3, 2, 3)))

    # ---- closed stirrup (1RB9 Around) + tie marker at a corner ----
    ax.add_patch(Rectangle((g.stir_l, g.stir_b), g.stir_r - g.stir_l, g.stir_t - g.stir_b,
                           fill=False, edgecolor=C["concrete"], lw=_MPL_LW["stirrup"]))
    _mk = 0.012 * W
    ax.add_patch(Rectangle((g.stir_l - _mk / 2.0, g.stir_b - _mk / 2.0), _mk, _mk,
                           facecolor=C["concrete"], edgecolor=C["concrete"]))

    # ---- top bar ----
    if p.top_reinf.num_bars > 0:
        ax.plot([g.stir_l + g.stir_dia, g.stir_r - g.stir_dia], [g.top_y, g.top_y],
                color=C["rebar"], lw=_MPL_LW["rebar"], linestyle=(0, (7, 4)))

    # ---- bottom bars: equally-spaced dots + in-plane bar with end hooks ----
    r = max(p.bottom_reinf.bar_dia_mm / 2.0, 0.004 * W)
    for x in g.bot_xs:
        ax.add_patch(Circle((x, g.bot_y), r, facecolor=C["bottom_bar"], edgecolor=C["bottom_bar"]))
    hook_up = min(g.stir_t, g.bot_y + p.dowel.hook_length_mm)
    bx0 = g.bot_xs[0] if len(g.bot_xs) > 1 else g.stir_l + g.stir_dia
    bx1 = g.bot_xs[-1] if len(g.bot_xs) > 1 else g.stir_r - g.stir_dia
    ax.plot([bx0, bx0, bx1, bx1], [hook_up, g.bot_y, g.bot_y, hook_up],
            color=C["rebar"], lw=_MPL_LW["rebar"], linestyle=(0, (7, 4)))

    # ---- dowels (template): green dashed vertical bars up inside the column and down to the
    #      bottom mat, with a cluster of magenta hook "staples" standing on the bottom steel.
    top_anchor = g.col_bottom + 0.80 * (g.col_top - g.col_bottom)   # up inside the column
    hh = 0.42 * (g.stir_t - g.bot_y)                                # hook height above bottom bar
    foot = 0.018 * W
    zone = g.stir_t - g.bot_y
    for x in g.dowel_xs:
        # green dashed dowel/column-bar line
        ax.plot([x, x], [top_anchor, g.bot_y], color=C["rebar"], lw=_MPL_LW["rebar"], linestyle=(0, (7, 4)))
        # two magenta hook staples flanking the dowel line, feet bending toward it
        for hx in (x - foot, x + foot):
            s = 1.0 if hx < x else -1.0
            ax.plot([hx, hx, hx + s * foot * 0.6], [g.bot_y, g.bot_y + hh, g.bot_y + hh],
                    color=C["hook"], lw=_MPL_LW["hook"])
    # "Dowel" labels: one centred for a single pile, otherwise one over each cluster
    if p.piles.count <= 1:
        ax.text(0, g.bot_y + 0.62 * zone, "Dowel", color=C["hook"], fontsize=_MPL_FS["small"],
                ha="center", va="center", fontweight="bold")
    else:
        for x in g.dowel_xs:
            lx_d = x * 0.62 + (0.16 * g.stir_r if x >= 0 else -0.16 * g.stir_r)
            ax.text(lx_d, g.bot_y + 0.62 * zone, "Dowel", color=C["hook"], fontsize=_MPL_FS["small"],
                    ha="center", va="center", fontweight="bold")

    # ---- dimensions ----
    L = W / 2.0
    gx1, gx2 = -L - 0.09 * W, -L - 0.22 * W
    for yy in (g.col_top, g.ped_top, g.cap_top, g.cap_bottom, g.lean_bottom, g.sand_bottom):
        ax.plot([-L, gx2 - 0.02 * W], [yy, yy], color=C["center"], lw=_MPL_LW["center"])
    _mpl_dim_v(ax, gx1, g.cap_bottom, g.cap_top, _m(T), xspan, C["dim"])
    if g.has_ped:
        _mpl_dim_v(ax, gx1, g.cap_top, g.ped_top, _m(g.ped_top - g.cap_top), xspan, C["dim"])
    _mpl_dim_v(ax, gx2, g.sand_bottom, g.col_top, _m(g.col_top - g.sand_bottom), xspan, C["dim"])
    # top: column width + pedestal width
    ax.plot([g.col_l, g.col_l], [g.col_top, g.col_top + 0.10 * W], color=C["center"], lw=_MPL_LW["center"])
    ax.plot([g.col_r, g.col_r], [g.col_top, g.col_top + 0.10 * W], color=C["center"], lw=_MPL_LW["center"])
    _mpl_dim_h(ax, g.col_l, g.col_r, g.col_top + 0.09 * W, _m(g.col_r - g.col_l), xspan, C["dim"],
               0.012 * xspan)
    if g.has_ped:
        _mpl_dim_h(ax, g.ped_l, g.ped_r, g.col_top + 0.035 * W, _m(g.ped_r - g.ped_l), xspan, C["dim"],
                   -0.028 * xspan)
    # covers
    _mpl_dim_h(ax, -L, g.stir_l, g.cap_top + 0.10 * T, _m(g.side_cover), xspan, C["dim"], 0.010 * xspan)
    _mpl_dim_v(ax, g.stir_l - 0.02 * W, g.cap_bottom, g.bot_y, _m(g.bottom_cover), xspan, C["dim"])
    # bottom: pile diameter, pile spacing, overall width
    yb1, yb2, yb3 = g.pile_bottom - 0.10 * T, g.pile_bottom - 0.40 * T, g.pile_bottom - 0.72 * T
    px = g.pile_xs[0]
    _mpl_dim_h(ax, px - g.pile_w / 2.0, px + g.pile_w / 2.0, yb1, _m(g.pile_w), xspan, C["dim"], 0.008 * xspan)
    if len(g.pile_xs) >= 2:
        _mpl_dim_h(ax, g.pile_xs[0], g.pile_xs[-1], yb2, _m(g.pile_xs[-1] - g.pile_xs[0]), xspan,
                   C["dim"], 0.008 * xspan)
    _mpl_dim_h(ax, -L, L, yb3, f"A = {_m(W)} m.", xspan, C["dim"], 0.008 * xspan)

    # ---- callouts / texts ----
    t = p.texts
    lx = W / 2.0 + 0.04 * W
    if t.around_callout:
        ax.plot([g.stir_r, lx], [g.stir_t, g.stir_t + 0.10 * T], color=C["concrete"], lw=_MPL_LW["dim"])
        ax.text(lx, g.stir_t + 0.10 * T, t.around_callout, color=C["text"], fontsize=_MPL_FS["label"],
                ha="left", va="center")
    if t.top_callout:
        ax.plot([g.stir_r - g.stir_dia, lx], [g.top_y, g.top_y], color=C["concrete"], lw=_MPL_LW["dim"])
        ax.text(lx, g.top_y, t.top_callout, color=C["text"], fontsize=_MPL_FS["label"], ha="left",
                va="center", fontweight="bold")
    if t.bottom_callout:
        ax.plot([g.stir_r - g.stir_dia, lx], [g.bot_y, g.bot_y], color=C["concrete"], lw=_MPL_LW["dim"])
        ax.text(lx, g.bot_y, t.bottom_callout, color=C["text"], fontsize=_MPL_FS["label"], ha="left",
                va="center", fontweight="bold")
    ax.text(lx, g.cap_bottom - 0.5 * p.layers.lean_thickness_mm,
            f"Lean {_m(p.layers.lean_thickness_mm)} m.", color=C["soil"], fontsize=_MPL_FS["small"], ha="left", va="center")
    ax.text(lx, g.lean_bottom - 0.5 * p.layers.sand_thickness_mm,
            f"Sand {_m(p.layers.sand_thickness_mm)} m.", color=C["soil"], fontsize=_MPL_FS["small"], ha="left", va="center")
    _stub = g.cap_bottom - g.pile_bottom
    if t.pile_desc:
        ax.text(lx, g.pile_bottom + 0.58 * _stub, t.pile_desc, color=C["text"],
                fontsize=_MPL_FS["small"], ha="left", va="center")
    if t.safe_load:
        ax.text(lx, g.pile_bottom + 0.30 * _stub, t.safe_load, color=C["text"],
                fontsize=_MPL_FS["small"], ha="left", va="center")
    ax.text(0, g.pile_bottom - 1.02 * T, t.title, color=C["title"], fontsize=_MPL_FS["title"],
            ha="center", va="center", fontweight="bold")

    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", facecolor="white")
    plt.close(fig)
    return buf.getvalue()


# ======================================================================
# ADAPTER for NPK RC SDM module 5.2
# ======================================================================
def params_from_pilecap_result(inp, result, *, pedestal_w_mm=None, pedestal_h_mm=0.0,
                               around_callout="1RB9 (Around)", pile_type_label=None):
    n1, n2 = result.flex_1.n_bars_use, result.flex_2.n_bars_use
    bottom_n, top_n = (n2, n1) if n2 >= n1 else (n1, n2)
    dia, bt = inp.main_bar_dia_mm, result.main_bar_type
    return PileCapSectionParams(
        pile_cap=PileCap(result.geometry.A_cm * 10.0, result.t_cm * 10.0),
        pedestal=Pedestal(pedestal_w_mm or (inp.column_b_cm * 10.0 + 100.0), pedestal_h_mm),
        column=Column(inp.column_b_cm * 10.0, inp.column_h_cm * 10.0),
        piles=Piles(inp.n_piles, inp.pile_size_cm * 10.0, result.geometry.spacing_cm * 10.0),
        cover=Cover(inp.cover_cm * 10.0, inp.cover_cm * 10.0, inp.cover_cm * 10.0),
        bottom_reinf=BottomReinf(dia, bottom_n),
        top_reinf=TopReinf(dia, top_n),
        dowel=Dowel(dia, result.dowel.lbd_cm * 10.0,
                    max(result.t_cm * 10.0 - 2 * inp.cover_cm * 10.0, 100.0)),
        stirrups=Stirrups(9.0),
        layers=FoundationLayers(50.0, 100.0),
        texts=Texts(f"{bottom_n}{bt}{dia:.0f}", f"{top_n}{bt}{dia:.0f}", around_callout,
                    f"{inp.n_piles} {pile_type_label}" if pile_type_label
                    else f"{inp.n_piles} Pile {inp.pile_size_cm:.0f}",
                    f"S.L >= {inp.pile_safe_load_ton:.0f} t/pile", "SECTION"),
    )


def example_2pile() -> PileCapSectionParams:
    """Reference example: 2 Pile I-22, cap 1180x300, column 300 on a 400x150 pedestal."""
    return PileCapSectionParams(
        pile_cap=PileCap(1180, 300),
        pedestal=Pedestal(400, 150),
        column=Column(300, 300, projection_mm=360),
        piles=Piles(2, 220, 675),
        cover=Cover(75, 75, 75),
        bottom_reinf=BottomReinf(16, 7),
        top_reinf=TopReinf(16, 4),
        dowel=Dowel(16, 300, 150),
        stirrups=Stirrups(9),
        layers=FoundationLayers(50, 100),
        texts=Texts("7DB16", "4DB16", "1RB9 (Around)", "2 Pile I-22", "S.L >= 15 t/pile", "SECTION"),
    )
