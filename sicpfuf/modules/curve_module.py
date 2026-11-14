"""
sicpfuf/modules/curve_module.py —  from curve import make_point, draw_connected, ...

A CURVE IS A FUNCTION. It takes a number t between 0 and 1 and returns a POINT:

    def unit_circle(t):
        return make_point(math_cos(2 * math_pi * t), math_sin(2 * math_pi * t))

    draw_connected(200)(unit_circle)

t is "how far along the curve are we": the curve starts at C(0) and ends at C(1).
draw_connected(n) asks the curve for n + 1 points (t = 0, 1/n, 2/n, ..., 1) and
joins them with straight lines.

Because a curve must take exactly ONE argument, a "curve with settings" is a
function that RETURNS a curve, and a "curve transformation" is a function that
takes a curve and returns a curve:

    translate(0.5, 0.5, 0)(unit_circle)        rotate_around_origin(math_pi / 2)(arc)

Functions that take and return functions: the same idea as make_adder.

    draw_connected(n)                          the window is the unit square 0..1 by 0..1
    draw_connected_full_view(n)                stretch the curve to fill the window
    draw_connected_full_view_proportional(n)   fit the curve in the window, keep its shape
    draw_points...(n)                          the same three, but only the points
"""

import math

from ..errors import SicpError
from ..values import Closure, Builtin, type_name, a
from .rune_module import save_figure

NAMES = (
    "make_point", "make_3D_point", "make_color_point", "make_3D_color_point",
    "x_of", "y_of", "z_of", "r_of", "g_of", "b_of",
    "unit_circle", "unit_line", "unit_line_at", "arc",
    "invert", "translate", "scale", "scale_proportional", "rotate_around_origin", "rotate_around_origin_3D",
    "put_in_standard_position", "connect_rigidly", "connect_ends",
    "draw_connected", "draw_connected_full_view", "draw_connected_full_view_proportional",
    "draw_points", "draw_points_full_view", "draw_points_full_view_proportional",
    "draw_3D_connected", "draw_3D_connected_full_view", "draw_3D_connected_full_view_proportional",
    "draw_3D_points", "draw_3D_points_full_view", "draw_3D_points_full_view_proportional",
)


class Point:
    __slots__ = ("x", "y", "z", "colour")

    def __init__(self, x, y, z=0.0, colour=(0.0, 0.0, 0.0)):
        self.x, self.y, self.z, self.colour = x, y, z, colour

    def __repr__(self):
        return "<Point>"


def place(points, mode):
    """Map curve coordinates into the unit window, according to the drawing mode."""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    if mode == "none" or not points:
        return [(x, y) for x, y in zip(xs, ys)]
    lo_x, hi_x, lo_y, hi_y = min(xs), max(xs), min(ys), max(ys)
    span_x, span_y = (hi_x - lo_x) or 1.0, (hi_y - lo_y) or 1.0
    margin = 0.1
    if mode == "fit":                               # one scale for both directions: the shape is kept
        span = max(span_x, span_y)
        off_x, off_y = (span - span_x) / 2, (span - span_y) / 2
        return [(margin + (1 - 2 * margin) * (x - lo_x + off_x) / span,
                 margin + (1 - 2 * margin) * (y - lo_y + off_y) / span) for x, y in zip(xs, ys)]
    return [(margin + (1 - 2 * margin) * (x - lo_x) / span_x,
             margin + (1 - 2 * margin) * (y - lo_y) / span_y) for x, y in zip(xs, ys)]


def to_svg(placed, colours, lines, size=512):
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">',
           f'<rect width="{size}" height="{size}" fill="#ffffff" stroke="#cccccc"/>']
    px = [(x * size, (1 - y) * size) for x, y in placed]
    rgb = lambda c: f"rgb({round(c[0] * 255)},{round(c[1] * 255)},{round(c[2] * 255)})"
    if lines and len(set(colours)) <= 1:
        path = " ".join(f"{x:.2f},{y:.2f}" for x, y in px)
        out.append(f'<polyline points="{path}" fill="none" stroke="{rgb(colours[0]) if colours else "black"}" '
                   f'stroke-width="2" stroke-linejoin="round"/>')
    elif lines:
        for i in range(len(px) - 1):
            out.append(f'<line x1="{px[i][0]:.2f}" y1="{px[i][1]:.2f}" x2="{px[i + 1][0]:.2f}" '
                       f'y2="{px[i + 1][1]:.2f}" stroke="{rgb(colours[i])}" stroke-width="2"/>')
    else:
        for (x, y), c in zip(px, colours):
            out.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="2" fill="{rgb(c)}"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def to_text(placed, lines, width=56):
    """Text preview: a grid of dots, two (upper/lower) per character."""
    grid = [[False] * width for _ in range(width)]

    def dot(x, y):
        col, row = int(x * (width - 1) + 0.5), int((1 - y) * (width - 1) + 0.5)
        if 0 <= col < width and 0 <= row < width:
            grid[row][col] = True

    for i, (x, y) in enumerate(placed):
        dot(x, y)
        if lines and i + 1 < len(placed):
            x2, y2 = placed[i + 1]
            n = int(max(abs(x2 - x), abs(y2 - y)) * width * 1.5) + 1
            if n < 4000:
                for k in range(1, n):
                    dot(x + (x2 - x) * k / n, y + (y2 - y) * k / n)
    out = ["┌" + "─" * width + "┐"]
    for row in range(0, width, 2):
        out.append("│" + "".join("█" if u and l else "▀" if u else "▄" if l else " "
                                 for u, l in zip(grid[row], grid[row + 1])) + "│")
    out.append("└" + "─" * width + "┘")
    return "\n".join(out)


def make(interp):
    from ..lib import builtin

    def number(fname, x, pname):
        if type(x) is not int and type(x) is not float:
            raise SicpError("TypeError", f"{fname} expects a number as {pname}, but got {a(type_name(x))}")
        return x

    def point(fname, p):
        if type(p) is not Point:
            raise SicpError("TypeError", f"{fname} expects a point, but got {a(type_name(p))}")
        return p

    def curve(fname, c):
        if type(c) is not Closure and type(c) is not Builtin:
            raise SicpError("TypeError", f"{fname} expects a curve (a function from a number to a point), "
                            f"but got {a(type_name(c))}")
        return c

    def at(c, t):
        """The point of curve c at t."""
        p = interp.apply(c, [t])
        if type(p) is not Point:
            raise SicpError("TypeError", f"a curve must return a point (use make_point), but this one "
                            f"returned {a(type_name(p))}")
        return p

    def as_curve(name, fn):
        return builtin(name, lambda t: fn(number(name, t, "t")), 1)

    def transformer(name, fn):
        """A curve transformation: takes a curve, returns the curve with fn applied to each point."""
        def transform(c):
            curve(name, c)
            return as_curve("curve", lambda t: fn(at(c, t), t))
        return builtin(name, transform, 1)

    # ------------------------------------------------------------ points
    def make_point(x, y):
        return Point(number("make_point", x, "x"), number("make_point", y, "y"))

    def make_3D_point(x, y, z):
        return Point(number("make_3D_point", x, "x"), number("make_3D_point", y, "y"), number("make_3D_point", z, "z"))

    def colour(fname, r, g, b):
        return tuple(min(max(number(fname, v, n), 0), 255) / 255 for v, n in ((r, "r"), (g, "g"), (b, "b")))

    def make_color_point(x, y, r, g, b):
        return Point(number("make_color_point", x, "x"), number("make_color_point", y, "y"), 0.0,
                     colour("make_color_point", r, g, b))

    def make_3D_color_point(x, y, z, r, g, b):
        return Point(number("make_3D_color_point", x, "x"), number("make_3D_color_point", y, "y"),
                     number("make_3D_color_point", z, "z"), colour("make_3D_color_point", r, g, b))

    # ------------------------------------------------------------ transformations
    def translate(x0, y0, z0):
        for v, n in ((x0, "x0"), (y0, "y0"), (z0, "z0")):
            number("translate", v, n)
        return transformer("translate", lambda p, t: Point(x0 + p.x, y0 + p.y, z0 + p.z, p.colour))

    def scale(x, y, z):
        for v, n in ((x, "x"), (y, "y"), (z, "z")):
            number("scale", v, n)
        return transformer("scale", lambda p, t: Point(x * p.x, y * p.y, z * p.z, p.colour))

    def scale_proportional(s):
        number("scale_proportional", s, "s")
        return transformer("scale_proportional", lambda p, t: Point(s * p.x, s * p.y, s * p.z, p.colour))

    def rotate_around_origin(angle):
        number("rotate_around_origin", angle, "a")
        c, s = math.cos(angle), math.sin(angle)
        return transformer("rotate_around_origin",
                           lambda p, t: Point(c * p.x - s * p.y, s * p.x + c * p.y, p.z, p.colour))

    def rotate_around_origin_3D(ax, by, cz):
        cx, sx, cy, sy = math.cos(ax), math.sin(ax), math.cos(by), math.sin(by)
        c3, s3 = math.cos(cz), math.sin(cz)
        m = ((c3 * cy, c3 * sy * sx - s3 * cx, c3 * sy * cx + s3 * sx),
             (s3 * cy, s3 * sy * sx + c3 * cx, s3 * sy * cx - c3 * sx),
             (-sy, cy * sx, cy * cx))
        return transformer("rotate_around_origin_3D", lambda p, t: Point(
            m[0][0] * p.x + m[0][1] * p.y + m[0][2] * p.z, m[1][0] * p.x + m[1][1] * p.y + m[1][2] * p.z,
            m[2][0] * p.x + m[2][1] * p.y + m[2][2] * p.z, p.colour))

    def invert(c):
        curve("invert", c)
        return as_curve("curve", lambda t: at(c, 1 - t))

    def connect_rigidly(c1, c2):
        curve("connect_rigidly", c1)
        curve("connect_rigidly", c2)
        return as_curve("curve", lambda t: at(c1, 2 * t) if t < 1 / 2 else at(c2, 2 * t - 1))

    def connect_ends(c1, c2):
        end, start = at(curve("connect_ends", c1), 1), at(curve("connect_ends", c2), 0)
        moved = translate(end.x - start.x, end.y - start.y, end.z - start.z).fn(c2)
        return connect_rigidly(c1, moved)

    def put_in_standard_position(c):
        start = at(curve("put_in_standard_position", c), 0)
        at_origin = translate(-start.x, -start.y, 0).fn(c)
        end = at(at_origin, 1)
        on_axis = rotate_around_origin(-math.atan2(end.y, end.x)).fn(at_origin)
        length = at(on_axis, 1).x
        if length == 0 or math.isinf(length) or math.isnan(length):
            raise SicpError("ValueError", "put_in_standard_position: the curve starts and ends at the same point")
        return scale_proportional(1 / length).fn(on_axis)

    # ------------------------------------------------------------ drawing
    def drawer(name, mode, lines, three_d):
        def make_renderer(n):
            if type(n) is not int or n < 1:
                raise SicpError("TypeError", f"{name}(n) expects a positive integer number of segments")

            def render(interp_, node, c):
                curve(name, c)
                points = [at(c, i / n) for i in range(n + 1)]
                flat = [(p.x + 0.35 * p.z, p.y + 0.35 * p.z) if three_d else (p.x, p.y) for p in points]
                placed = place(flat, mode)
                interp_.write(to_text(placed, lines) + "\n")
                path = save_figure(interp_, "curve", "svg", to_svg(placed, [p.colour for p in points], lines))
                if path:
                    interp_.write(f"[saved {path}]\n")
                return None
            return builtin("renderer", render, 1, -1, True)
        return builtin(name, make_renderer, 1)

    module = {
        "make_point": builtin("make_point", make_point, 2),
        "make_3D_point": builtin("make_3D_point", make_3D_point, 3),
        "make_color_point": builtin("make_color_point", make_color_point, 5),
        "make_3D_color_point": builtin("make_3D_color_point", make_3D_color_point, 6),
        "x_of": builtin("x_of", lambda p: point("x_of", p).x, 1),
        "y_of": builtin("y_of", lambda p: point("y_of", p).y, 1),
        "z_of": builtin("z_of", lambda p: point("z_of", p).z, 1),
        "r_of": builtin("r_of", lambda p: math.floor(point("r_of", p).colour[0] * 255), 1),
        "g_of": builtin("g_of", lambda p: math.floor(point("g_of", p).colour[1] * 255), 1),
        "b_of": builtin("b_of", lambda p: math.floor(point("b_of", p).colour[2] * 255), 1),
        "unit_circle": as_curve("unit_circle", lambda t: Point(math.cos(2 * math.pi * t), math.sin(2 * math.pi * t))),
        "unit_line": as_curve("unit_line", lambda t: Point(t, 0)),
        "unit_line_at": builtin("unit_line_at", lambda y: as_curve("curve", lambda t: Point(t, number("unit_line_at", y, "y"))), 1),
        "arc": as_curve("arc", lambda t: Point(math.sin(math.pi * t), math.cos(math.pi * t))),
        "invert": builtin("invert", invert, 1),
        "translate": builtin("translate", translate, 3),
        "scale": builtin("scale", scale, 3),
        "scale_proportional": builtin("scale_proportional", scale_proportional, 1),
        "rotate_around_origin": builtin("rotate_around_origin", rotate_around_origin, 1),
        "rotate_around_origin_3D": builtin("rotate_around_origin_3D", rotate_around_origin_3D, 3),
        "put_in_standard_position": builtin("put_in_standard_position", put_in_standard_position, 1),
        "connect_rigidly": builtin("connect_rigidly", connect_rigidly, 2),
        "connect_ends": builtin("connect_ends", connect_ends, 2),
    }
    for dims in ("", "3D_"):
        for kind, lines in (("connected", True), ("points", False)):
            for suffix, mode in (("", "none"), ("_full_view", "stretch"), ("_full_view_proportional", "fit")):
                name = f"draw_{dims}{kind}{suffix}"
                module[name] = drawer(name, mode, lines, bool(dims))
    return module
