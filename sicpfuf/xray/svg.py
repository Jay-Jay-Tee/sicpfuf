"""
sicpfuf/xray/svg.py — the same diagrams as boxpointer.py and envdiagram.py, as PICTURES.

When sicpfuf runs with  --out FOLDER,  draw_data(x) and show_env() also save an
SVG file each, drawn the way you would draw it by hand in an exam:

  box-and-pointer   a pair is a box with two halves; a slash in the tail half means None;
                    tails point right, heads point down
  environment       frames are boxes of  name: value  lines; an arrow leaves each frame
                    for its ENCLOSING environment; a function object is two circles:
                    the left one points at its code (parameters and body), the right one
                    at the environment it was created in
"""

from ..values import Closure, Builtin, short, show_atom
from .boxpointer import atom_text

CELL_H, CELL_MIN, CHAR_W, GAP_X, GAP_Y = 30, 34, 8.4, 34, 44
STYLE = ('<style>text{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:14px;fill:#1a1a1a}'
         '.small{font-size:12px;fill:#444}.box{fill:#fff;stroke:#1a1a1a;stroke-width:1.5}'
         '.frame{fill:#f3f6f6;stroke:#1a1a1a;stroke-width:1.5}.line{stroke:#1a1a1a;stroke-width:1.5;fill:none}'
         '.dot{fill:#1a1a1a}</style>'
         '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
         'orient="auto-start-reverse"><path d="M0,0L10,5L0,10z" fill="#1a1a1a"/></marker></defs>')


def esc(text):
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def document(width, height, parts):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" '
            f'width="{width:.0f}" height="{height:.0f}">{STYLE}'
            f'<rect width="{width:.0f}" height="{height:.0f}" fill="#ffffff"/>' + "".join(parts) + "</svg>\n")


# ====================================================================== box-and-pointer
class BoxDrawing:
    def __init__(self):
        self.parts = []
        self.arrows = []
        self.where = {}             # id(list) → (x, y) of its box, once it is placed
        self.count = 0

    def cell_width(self, text):
        return max(CELL_MIN, len(text) * CHAR_W + 14)

    def place(self, v, x, y):
        """Draw the box of v at (x, y). Returns (width, height) of everything drawn for it."""
        self.where[id(v)] = (x, y)
        self.count += 1
        is_pair = len(v) == 2
        texts, widths, kids = [], [], []
        for i, item in enumerate(v):
            pointer = type(item) is list
            text = "" if pointer or (is_pair and item is None) else atom_text(item)
            texts.append(text)
            widths.append(self.cell_width(text))
            kids.append(item if pointer else None)
        if not v:
            widths = [14]
        # children that hang BELOW (every list-valued slot, except the tail of a pair)
        height = CELL_H
        cx = x
        slot_x = []
        below_extent = 0
        for i, item in enumerate(v):
            slot_x.append(cx)
            if kids[i] is not None and not (is_pair and i == 1):
                target = self.where.get(id(item))
                if target is None and self.count < 300:
                    w, h = self.place(item, cx, y + CELL_H + GAP_Y)
                    self.arrows.append(("down", cx + widths[i] / 2, y + CELL_H / 2, y + CELL_H + GAP_Y))
                    height = max(height, CELL_H + GAP_Y + h)
                    if is_pair:
                        below_extent = w
                    else:
                        widths[i] = max(widths[i], w + 10)
                elif target is not None:
                    self.arrows.append(("curve", cx + widths[i] / 2, y + CELL_H / 2, target[0] + 8, target[1]))
            cx += widths[i]
        own = sum(widths)
        # the box itself
        cx = x
        for i in range(max(1, len(v))):
            w = widths[i]
            self.parts.append(f'<rect class="box" x="{cx:.1f}" y="{y:.1f}" width="{w:.1f}" height="{CELL_H}"/>')
            if v:
                if kids[i] is not None:
                    self.parts.append(f'<circle class="dot" cx="{cx + w / 2:.1f}" cy="{y + CELL_H / 2:.1f}" r="3.5"/>')
                elif is_pair and v[i] is None:
                    self.parts.append(f'<line class="line" x1="{cx:.1f}" y1="{y + CELL_H:.1f}" '
                                      f'x2="{cx + w:.1f}" y2="{y:.1f}"/>')
                else:
                    self.parts.append(f'<text x="{cx + w / 2:.1f}" y="{y + CELL_H / 2 + 5:.1f}" '
                                      f'text-anchor="middle">{esc(texts[i])}</text>')
            cx += w
        width = max(own, below_extent)
        # the tail of a pair goes to the RIGHT
        if is_pair and kids[1] is not None:
            start_x = x + widths[0] + widths[1] / 2
            target = self.where.get(id(v[1]))
            if target is None and self.count < 300:
                tx = x + width + GAP_X
                w, h = self.place(v[1], tx, y)
                self.arrows.append(("right", start_x, y + CELL_H / 2, tx))
                width = tx - x + w
                height = max(height, h)
            elif target is not None:
                self.arrows.append(("curve", start_x, y + CELL_H / 2, target[0] + 8, target[1]))
        return width, height

    def finish(self, width, height):
        top = 0
        for a in self.arrows:
            if a[0] == "right":
                _, x1, y1, x2 = a
                self.parts.append(f'<line class="line" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2 - 2:.1f}" y2="{y1:.1f}" '
                                  f'marker-end="url(#arrow)"/>')
            elif a[0] == "down":
                _, x1, y1, y2 = a
                self.parts.append(f'<line class="line" x1="{x1:.1f}" y1="{y1:.1f}" x2="{x1:.1f}" y2="{y2 - 2:.1f}" '
                                  f'marker-end="url(#arrow)"/>')
            else:                                   # back to a box that is already drawn (sharing, cycles)
                _, x1, y1, x2, y2 = a
                lift = min(y1, y2) - 34
                top = min(top, lift)
                self.parts.append(f'<path class="line" d="M{x1:.1f},{y1:.1f} C{x1:.1f},{lift:.1f} {x2:.1f},{lift:.1f} '
                                  f'{x2:.1f},{y2 - 2:.1f}" marker-end="url(#arrow)"/>')
        return top


def box_pointer(value):
    """The box-and-pointer diagram of `value` as SVG text."""
    if type(value) is not list:
        text = atom_text(value)
        return document(len(text) * CHAR_W + 30, 40, [f'<text x="15" y="25">{esc(text)}</text>'])
    d = BoxDrawing()
    pad = 44
    width, height = d.place(value, pad, pad)
    d.finish(width, height)
    return document(width + 2 * pad, height + 2 * pad, d.parts)


# ====================================================================== environment diagram
LINE_H, FRAME_X, PAD = 22, 96, 10


def environment(snapshot, label=None, interactive=False):
    """The environment diagram of an envdiagram.Snapshot as SVG text.

    Layout: frames in a column on the left, in the order they were made. Each function
    object sits to the right of the frame it was created in, so that its environment
    arrow is short. Enclosing-environment arrows run down the left margin.
    """
    from .envdiagram import real_frame
    parts, y = [], 16
    if label is not None:
        parts.append(f'<text class="small" x="12" y="18">{esc(str(label))}</text>')
        y = 34
    frames = sorted(snapshot.frames.values(), key=lambda e: e.serial)
    rows = []                           # (env, [(name, text, closure or None)])
    for env in frames:
        names = list(env.vars)
        if env.scope is not None:
            names += sorted(n for n in env.scope.local_names if n not in env.vars)
        lines = []
        for name in names:
            if name not in env.vars:
                lines.append((name, "", None))                     # unassigned: nothing after the colon
            else:
                v = env.vars[name]
                is_fn = type(v) is Closure and not v.prelude
                lines.append((name, "" if is_fn else short_text(snapshot.value_text(v), 44), v if is_fn else None))
        rows.append((env, lines))
    frame_w = max([150] + [(len(n) + len(t) + 2) * CHAR_W + 2 * PAD + 14 for _, ls in rows for n, t, _ in ls])
    right = FRAME_X + frame_w
    fn_x = right + 120
    position, dots = {}, {}             # id(env) → (top, height);  closure serial → [(x, y, env)]
    for env, lines in rows:
        if interactive:
            key = "global env" if env.kind == "program" else f"E{env.serial}"
            dead = id(env) in getattr(snapshot, "unreachable_frames", ())
            state = ' class="unreachable" data-reachable="false"' if dead else ' data-reachable="true"'
            parts.append(f'<g data-frame="{key}"{state} tabindex="0" role="button" aria-label="Inspect {key}{" (unreachable)" if dead else ""}">')
        if env.kind == "program":
            title, call = "global env", ""
        else:
            title = f"E{env.serial}"
            saved = env.args or []
            call = f"{env.name}({', '.join(saved) if snapshot.interp.diagrams else ', '.join(short(a_, 14) for a_ in saved)})"
        parts.append(f'<text x="{FRAME_X}" y="{y + 14}" font-weight="bold">{title}</text>')
        if call:
            room = int((frame_w + 90) / (CHAR_W * 0.86)) - len(title) - 2     # stop before the function column
            parts.append(f'<text class="small" x="{FRAME_X + (len(title) + 1.5) * CHAR_W:.0f}" y="{y + 14}">'
                         f'{esc(short_text(call, max(12, room)))}</text>')
        y += 20
        h = max(1, len(lines)) * LINE_H + 2 * PAD
        position[id(env)] = (y, h)
        parts.append(f'<rect class="frame" x="{FRAME_X}" y="{y}" width="{frame_w:.0f}" height="{h}" rx="7"/>')
        if interactive and env is snapshot.current:
            parts.append(f'<rect x="{FRAME_X}" y="{y}" width="{frame_w:.0f}" height="{h}" rx="7" '
                         'fill="none" stroke="#008577" stroke-width="4" pointer-events="none"/>')
        for i, (name, text, closure) in enumerate(lines):
            ty = y + PAD + i * LINE_H + 16
            parts.append(f'<text x="{FRAME_X + PAD}" y="{ty}">{esc(name + ": " + text)}</text>')
            if closure is not None:
                dot_x = FRAME_X + PAD + (len(name) + 2) * CHAR_W + 6
                parts.append(f'<circle class="dot" cx="{dot_x:.1f}" cy="{ty - 5}" r="3.5"/>')
                dots.setdefault(closure.serial, []).append((dot_x, ty - 5, env))
        if interactive:
            parts.append("</g>")
        y += h + 22
    bottom = y
    # enclosing-environment arrows, in lanes down the left margin
    arrivals = {}
    for k, (env, _) in enumerate(rows):
        if env.kind == "program":
            continue
        parent = real_frame(env.parent)
        if parent is None or id(parent) not in position:
            continue
        ey, eh = position[id(env)]
        py, ph = position[id(parent)]
        j = arrivals.get(id(parent), 0)
        arrivals[id(parent)] = j + 1
        land = max(py + 8, py + ph - 9 - 7 * j)
        lane = FRAME_X - 14 - 11 * (j % 7)
        dead = interactive and id(env) in getattr(snapshot, "unreachable_frames", ())
        parts.append(f'<path class="line{" unreachable" if dead else ""}" d="M{FRAME_X},{ey + 12} H{lane} V{land} H{FRAME_X - 2}" '
                     f'marker-end="url(#arrow)"/>')
    # function objects: beside the frame they were created in
    placed = []
    for serial, f in snapshot.functions.items():
        home = real_frame(f.env)
        mine = dots.get(serial, [])
        at_home = [d for d in mine if d[2] is home]
        if at_home:
            anchor = at_home[0][1]
        elif home is not None and id(home) in position:     # no name for it there: below the named ones
            anchor = position[id(home)][0] + position[id(home)][1] - 8
        else:
            anchor = mine[0][1] if mine else 40
        placed.append((anchor, serial, f, home, mine))
    placed.sort(key=lambda item: (item[0], item[1]))
    fy = 0
    for anchor, serial, f, home, mine in placed:
        fy = max(anchor, fy + 78) if fy else max(anchor, 40)
        cx = fn_x
        if interactive:
            dead = serial in getattr(snapshot, "unreachable_functions", ())
            state = ' class="unreachable" data-reachable="false"' if dead else ' data-reachable="true"'
            parts.append(f'<g data-function="fn#{serial}"{state} tabindex="0" role="button" aria-label="Inspect function {serial}{" (unreachable)" if dead else ""}">')
        parts.append(f'<circle class="box" cx="{cx}" cy="{fy}" r="11"/><circle class="box" cx="{cx + 22}" cy="{fy}" r="11"/>'
                     f'<circle class="dot" cx="{cx}" cy="{fy}" r="3"/><circle class="dot" cx="{cx + 22}" cy="{fy}" r="3"/>')
        params = ", ".join(f.params + (["*" + f.vararg] if f.vararg else []))
        parts.append(f'<line class="line" x1="{cx}" y1="{fy}" x2="{cx}" y2="{fy + 22}" marker-end="url(#arrow)"/>')
        parts.append(f'<text class="small" x="{cx - 9}" y="{fy + 37}">parameters: {esc(params)}</text>')
        parts.append(f'<text class="small" x="{cx - 9}" y="{fy + 52}">body: {esc(short_text(snapshot.source(f.node.line), 44))}</text>')
        for dx, dy, _ in mine:                      # a binding → the function object
            mid = (right + cx) / 2
            parts.append(f'<path class="line" d="M{dx:.1f},{dy} C{mid:.0f},{dy} {mid:.0f},{fy} {cx - 13},{fy}" '
                         f'marker-end="url(#arrow)"/>')
        if home is not None and id(home) in position:           # right circle → its environment
            hy, hh = position[id(home)]
            ty = min(max(fy - 15, hy + 7), hy + hh - 7)
            parts.append(f'<path class="line" d="M{cx + 22},{fy} C{cx + 22},{fy - 44} {right + 70:.0f},{ty} '
                         f'{right + 2:.0f},{ty}" marker-end="url(#arrow)"/>')
        if interactive:
            parts.append("</g>")
    width = fn_x + 350 if snapshot.functions else right + 40
    return document(width, max(bottom, fy + 64) + 6, parts)


def short_text(text, width):
    return text if len(text) <= width else text[:width - 3] + "..."
