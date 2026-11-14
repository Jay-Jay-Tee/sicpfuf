"""
sicpfuf/modules/rune_module.py —  from rune import show, heart, stack, beside, ...

A RUNE is a picture that lives in a square. You never draw lines yourself:
you start from a few PRIMITIVE runes (heart, sail, rcross, nova, corner, ...)
and build bigger pictures with functions that take runes and return runes:

    stack(a, b)               a on top of b            beside(a, b)       a left of b
    quarter_turn_right(a)     turn a by 90 degrees     stack_frac(1/3, a, b)   a gets the top third
    stackn(n, a)   make_cross(a)   overlay(a, b)   red(a)   scale(1/2, a)   rotate(angle, a)

    show(stack(heart, beside(sail, sail)))

A rune is a VALUE, like a number: you can name it, pass it to a function and
return it from a function. That is why runes are such a good playground for
functional abstraction, recursion and higher-order functions.

HOW IT IS BUILT. A primitive rune is a list of triangles inside the square
-1 <= x, y <= 1. Every other rune is a small tree: "these sub-runes, moved by
this transformation, in this colour". show() walks the tree, collects all the
triangles, and draws them: as text in the terminal, and as an SVG picture file
when sicpfuf runs with  --out FOLDER.
"""

import math
import random

from ..errors import SicpError
from ..values import type_name, a

NAMES = (
    "show", "anaglyph", "hollusion",
    "square", "blank", "rcross", "sail", "triangle", "corner", "nova", "circle", "heart", "pentagram", "ribbon",
    "scale_independent", "scale", "translate", "rotate", "stack_frac", "stack", "stackn",
    "quarter_turn_right", "quarter_turn_left", "turn_upside_down", "beside_frac", "beside",
    "flip_vert", "flip_horiz", "make_cross", "overlay_frac", "overlay", "color",
    "black", "blue", "brown", "green", "indigo", "red", "pink", "orange", "purple", "white", "yellow",
    "random_color",
)

COLOURS = {"black": "#000000", "blue": "#2196F3", "brown": "#795548", "green": "#4CAF50",
           "indigo": "#3F51B5", "orange": "#FF9800", "pink": "#E91E63", "purple": "#AA00FF",
           "red": "#F44336", "white": "#FFFFFF", "yellow": "#FFEB3B"}

IDENTITY = (1.0, 0.0, 0.0, 1.0, 0.0, 0.0)


class Rune:
    """Either a primitive (triangles) or a group of sub-runes with a transformation."""
    __slots__ = ("triangles", "subs", "matrix", "colour", "depth")

    def __init__(self, triangles=(), subs=(), matrix=IDENTITY, colour=None, depth=(1.0, 0.0)):
        self.triangles = triangles      # ((x1, y1), (x2, y2), (x3, y3)), ...
        self.subs = subs
        self.matrix = matrix            # (a, b, c, d, e, f):  x' = a*x + c*y + e,  y' = b*x + d*y + f
        self.colour = colour            # (r, g, b), each 0..1, or None for "not coloured here"
        self.depth = depth              # (scale, shift) of the z-coordinate: used by overlay

    def __repr__(self):
        return "<Rune>"


def compose(m, n):
    """The transformation "first n, then m"."""
    a1, b1, c1, d1, e1, f1 = m
    a2, b2, c2, d2, e2, f2 = n
    return (a1 * a2 + c1 * b2, b1 * a2 + d1 * b2, a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1)


def flatten(rune):
    """Walk the tree: returns [(z, colour, triangles in final position)], back to front."""
    out = []

    def walk(r, matrix, colour, zs, zb):
        matrix = compose(matrix, r.matrix)
        if colour is None:                          # the OUTERMOST colour wins
            colour = r.colour
        zs, zb = zs * r.depth[0], zs * r.depth[1] + zb
        if r.triangles:
            a_, b_, c_, d_, e_, f_ = matrix
            moved = [tuple((a_ * x + c_ * y + e_, b_ * x + d_ * y + f_) for x, y in tri) for tri in r.triangles]
            out.append((zb, colour or (0.0, 0.0, 0.0), moved))
        for sub in r.subs:
            walk(sub, matrix, colour, zs, zb)

    walk(rune, IDENTITY, None, 1.0, 0.0)
    out.sort(key=lambda item: item[0])              # (a stable sort: equal depths keep their order)
    return out


# ------------------------------------------------------------------ the primitive runes
def fan(points, centre):
    return tuple((points[i], points[i + 1], centre) for i in range(len(points) - 1))


def primitives():
    tris = lambda *numbers: tuple(tuple((numbers[i + 2 * k], numbers[i + 2 * k + 1]) for k in range(3))
                                  for i in range(0, len(numbers), 6))
    circle_points = [(math.cos(2 * math.pi * i / 60), math.sin(2 * math.pi * i / 60)) for i in range(61)]
    root2 = math.sqrt(2)
    r = 4 / (2 + 3 * root2)
    sx = 1 / (r * (1 + root2 / 2))
    right = [((math.cos(math.pi * (-1 / 4 + i / 100)) * r + r / root2) * sx,
              math.sin(math.pi * (-1 / 4 + i / 100)) * r + 1 - r) for i in range(101)]
    left = [((math.cos(math.pi * (1 / 4 + i / 100)) * r - r / root2) * sx,
             math.sin(math.pi * (1 / 4 + i / 100)) * r + 1 - r) for i in range(102)]
    v1, v2 = math.sin(math.pi / 10), math.cos(math.pi / 10)
    w1, w2 = math.sin(3 * math.pi / 10), math.cos(3 * math.pi / 10)
    star = [(v2, v1), (w2, -w1), (-w2, -w1), (-v2, v1), (0.0, 1.0)]
    spiral, i = [], 0.0
    while i < 30:
        x, y = (i / 30) * math.cos(i), (i / 30) * math.sin(i)
        spiral.append((x, y))
        spiral.append((abs(math.cos(i) / -30) + x, abs(math.sin(i) / -30) + y))
        i += 0.1
    return {
        "square": Rune(tris(-1, 1, -1, -1, 1, -1, 1, -1, -1, 1, 1, 1)),
        "blank": Rune(),
        "rcross": Rune(tris(-.5, .5, -.5, -.5, .5, -.5, -1, 1, -.5, .5, 1, 1, -.5, .5, 1, 1, .5, .5,
                            1, 1, .5, .5, 1, -1, .5, .5, 1, -1, .5, -.5)),
        "sail": Rune(tris(.5, -1, 0, -1, 0, 1)),
        "triangle": Rune(tris(1, -1, 0, -1, 0, 1)),
        "corner": Rune(tris(1, 0, 1, 1, 0, 1)),
        "nova": Rune(tris(0, 1, -.5, 0, 0, .5, -.5, 0, 0, .5, 1, 0)),
        "circle": Rune(fan(circle_points, (0.0, 0.0))),
        "heart": Rune(fan(right, (0.0, -1.0)) + fan(left, (0.0, -1.0))),
        "pentagram": Rune(tuple(((0.0, 0.0), star[k], star[(k + 2) % 5]) for k in range(5))),
        "ribbon": Rune(tuple((spiral[k], spiral[k + 1], spiral[k + 2]) for k in range(len(spiral) - 2))),
    }


# ------------------------------------------------------------------ drawing
def to_svg(rune, size=512):
    """The rune as an SVG picture (text). x, y in -1..1 with y UP become pixels with y DOWN."""
    half = size / 2
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}" width="{size}" height="{size}">',
           f'<rect width="{size}" height="{size}" fill="#ffffff"/>']
    for _, (red, green, blue), triangles in flatten(rune):
        fill = f"rgb({round(red * 255)},{round(green * 255)},{round(blue * 255)})"
        path = "".join("M" + "L".join(f"{(x + 1) * half:.2f},{(1 - y) * half:.2f}" for x, y in tri) + "Z"
                       for tri in triangles)
        out.append(f'<path d="{path}" fill="{fill}" stroke="{fill}" stroke-width="0.4"/>')
    out.append("</svg>")
    return "\n".join(out) + "\n"


def to_text(rune, width=48):
    """The rune as text: a grid of `width` x `width` dots, two dots (upper/lower) per character."""
    grid = [[False] * width for _ in range(width)]
    for _, colour, triangles in flatten(rune):
        ink = min(colour) < 0.9                     # white paint ERASES (useful with overlay)
        for (x1, y1), (x2, y2), (x3, y3) in triangles:
            # to grid coordinates: column 0 is x = -1, row 0 is y = +1
            ax, ay = (x1 + 1) / 2 * width, (1 - y1) / 2 * width
            bx, by = (x2 + 1) / 2 * width, (1 - y2) / 2 * width
            cx, cy = (x3 + 1) / 2 * width, (1 - y3) / 2 * width
            area = (bx - ax) * (cy - ay) - (by - ay) * (cx - ax)
            if area == 0:
                continue
            for row in range(max(0, int(min(ay, by, cy))), min(width, int(max(ay, by, cy)) + 1)):
                py = row + 0.5
                for col in range(max(0, int(min(ax, bx, cx))), min(width, int(max(ax, bx, cx)) + 1)):
                    px = col + 0.5
                    w1 = ((bx - ax) * (py - ay) - (by - ay) * (px - ax)) / area
                    w2 = ((cx - bx) * (py - by) - (cy - by) * (px - bx)) / area
                    w3 = ((ax - cx) * (py - cy) - (ay - cy) * (px - cx)) / area
                    if w1 >= 0 and w2 >= 0 and w3 >= 0:
                        grid[row][col] = ink
    lines = ["┌" + "─" * width + "┐"]
    for row in range(0, width, 2):
        upper, lower = grid[row], grid[row + 1] if row + 1 < width else [False] * width
        lines.append("│" + "".join("█" if u and l else "▀" if u else "▄" if l else " "
                                   for u, l in zip(upper, lower)) + "│")
    lines.append("└" + "─" * width + "┘")
    return "\n".join(lines)


def save_figure(interp, kind, extension, data, binary=False):
    """Write a picture or sound into the --out folder (if there is one). Returns the file name or None."""
    import os
    folder = getattr(interp, "out_dir", None)
    if not folder:
        return None
    counts = interp.modules.setdefault("__figures__", {})
    counts[kind] = counts.get(kind, 0) + 1
    os.makedirs(folder, exist_ok=True)
    stem = getattr(interp, "out_stem", None)
    name = f"{stem + '-' if stem else ''}{kind}-{counts[kind]}.{extension}"
    path = os.path.join(folder, name)
    with open(path, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as f:
        f.write(data)
    return name


# ------------------------------------------------------------------ the module
def make(interp):
    from ..lib import builtin

    def need_rune(fname, x, pname="rune"):
        if type(x) is not Rune:
            raise SicpError("TypeError", f"{fname} expects a rune as {pname}, but got {a(type_name(x))}")

    def need_number(fname, x, pname):
        if type(x) is not int and type(x) is not float:
            raise SicpError("TypeError", f"{fname} expects a number as {pname}, but got {a(type_name(x))}")

    def need_fraction(fname, x, pname):
        need_number(fname, x, pname)
        if not 0 <= x <= 1:
            raise SicpError("ValueError", f"{fname} expects {pname} to be between 0 and 1, but got {x}")

    def scale_independent(ratio_x, ratio_y, rune):
        need_number("scale_independent", ratio_x, "ratio_x")
        need_number("scale_independent", ratio_y, "ratio_y")
        need_rune("scale_independent", rune)
        return Rune(subs=(rune,), matrix=(ratio_x, 0.0, 0.0, ratio_y, 0.0, 0.0))

    def scale(ratio, rune):
        need_number("scale", ratio, "ratio")
        need_rune("scale", rune)
        return scale_independent(ratio, ratio, rune)

    def translate(x, y, rune):
        need_number("translate", x, "x")
        need_number("translate", y, "y")
        need_rune("translate", rune)
        return Rune(subs=(rune,), matrix=(1.0, 0.0, 0.0, 1.0, x, -y))      # +y moves DOWN the screen

    def rotate(rad, rune):
        need_number("rotate", rad, "rad")
        need_rune("rotate", rune)
        c, s = math.cos(rad), math.sin(rad)
        return Rune(subs=(rune,), matrix=(c, s, -s, c, 0.0, 0.0))          # anticlockwise

    def stack_frac(frac, rune1, rune2):
        need_fraction("stack_frac", frac, "frac")
        need_rune("stack_frac", rune1, "rune1")
        need_rune("stack_frac", rune2, "rune2")
        upper = translate(0, -(1 - frac), scale_independent(1, frac, rune1))
        lower = translate(0, frac, scale_independent(1, 1 - frac, rune2))
        return Rune(subs=(upper, lower))

    def stack(rune1, rune2):
        need_rune("stack", rune1, "rune1")
        need_rune("stack", rune2, "rune2")
        return stack_frac(1 / 2, rune1, rune2)

    def stackn(n, rune):
        need_number("stackn", n, "n")
        need_rune("stackn", rune)
        result = rune
        for k in range(2, int(n) + 1):              # stack_frac(1 / k, rune, <k - 1 runes>)
            result = stack_frac(1 / k, rune, result)
        return result

    def quarter_turn_right(rune):
        need_rune("quarter_turn_right", rune)
        return rotate(-math.pi / 2, rune)

    def quarter_turn_left(rune):
        need_rune("quarter_turn_left", rune)
        return rotate(math.pi / 2, rune)

    def turn_upside_down(rune):
        need_rune("turn_upside_down", rune)
        return rotate(math.pi, rune)

    def beside_frac(frac, rune1, rune2):
        need_fraction("beside_frac", frac, "frac")
        need_rune("beside_frac", rune1, "rune1")
        need_rune("beside_frac", rune2, "rune2")
        left = translate(-(1 - frac), 0, scale_independent(frac, 1, rune1))
        right = translate(frac, 0, scale_independent(1 - frac, 1, rune2))
        return Rune(subs=(left, right))

    def beside(rune1, rune2):
        need_rune("beside", rune1, "rune1")
        need_rune("beside", rune2, "rune2")
        return beside_frac(1 / 2, rune1, rune2)

    def flip_vert(rune):
        need_rune("flip_vert", rune)
        return scale_independent(1, -1, rune)

    def flip_horiz(rune):
        need_rune("flip_horiz", rune)
        return scale_independent(-1, 1, rune)

    def make_cross(rune):
        need_rune("make_cross", rune)
        return stack(beside(quarter_turn_right(rune), rotate(math.pi, rune)),
                     beside(rune, rotate(math.pi / 2, rune)))

    def overlay_frac(frac, rune1, rune2):
        need_fraction("overlay_frac", frac, "frac")
        need_rune("overlay_frac", rune1, "rune1")
        need_rune("overlay_frac", rune2, "rune2")
        frac = min(max(frac, 0.000001), 0.999999)
        front = Rune(subs=(rune1,), depth=(frac, 0.0))                     # rune1 is IN FRONT
        back = Rune(subs=(rune2,), depth=(1 - frac, -frac))
        return Rune(subs=(front, back))

    def overlay(rune1, rune2):
        need_rune("overlay", rune1, "rune1")
        need_rune("overlay", rune2, "rune2")
        return overlay_frac(1 / 2, rune1, rune2)

    def color(rune, r, g, b):
        need_rune("color", rune)
        for value, name in ((r, "r"), (g, "g"), (b, "b")):
            need_fraction("color", value, name)
        return Rune(subs=(rune,), colour=(float(r), float(g), float(b)))

    def named_colour(name, code):
        rgb = tuple(int(code[i:i + 2], 16) / 255 for i in (1, 3, 5))

        def paint(rune):
            need_rune(name, rune)
            return Rune(subs=(rune,), colour=rgb)
        return paint

    def random_color(rune):
        need_rune("random_color", rune)
        code = COLOURS[random.choice(["blue", "brown", "green", "indigo", "orange", "pink", "purple", "red", "yellow"])]
        return Rune(subs=(rune,), colour=tuple(int(code[i:i + 2], 16) / 255 for i in (1, 3, 5)))

    def show(interp_, node, rune):
        """Display the rune. Returns the rune, so show(...) can sit inside an expression."""
        need_rune("show", rune)
        interp_.write(to_text(rune) + "\n")
        path = save_figure(interp_, "rune", "svg", to_svg(rune))
        if path:
            interp_.write(f"[saved {path}]\n")
        return rune

    module = dict(primitives())
    for name, fn, count in (
            ("scale_independent", scale_independent, 3), ("scale", scale, 2), ("translate", translate, 3),
            ("rotate", rotate, 2), ("stack_frac", stack_frac, 3), ("stack", stack, 2), ("stackn", stackn, 2),
            ("quarter_turn_right", quarter_turn_right, 1), ("quarter_turn_left", quarter_turn_left, 1),
            ("turn_upside_down", turn_upside_down, 1), ("beside_frac", beside_frac, 3), ("beside", beside, 2),
            ("flip_vert", flip_vert, 1), ("flip_horiz", flip_horiz, 1), ("make_cross", make_cross, 1),
            ("overlay_frac", overlay_frac, 3), ("overlay", overlay, 2), ("color", color, 4),
            ("random_color", random_color, 1)):
        module[name] = builtin(name, fn, count)
    for name, code in COLOURS.items():
        module[name] = builtin(name, named_colour(name, code), 1)
    for name in ("show", "anaglyph", "hollusion"):          # (3D glasses not included: all three just show)
        module[name] = builtin(name, show, 1, -1, True)
    return module
