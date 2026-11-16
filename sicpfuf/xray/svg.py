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


def reduction_environment(store, calls, functions):
    """Draw the reducer's actual heap, including aliases and cyclic lists.

    Every reference has one destination. Frames and heap cards have separate
    columns, so adding code text cannot enlarge a selection over another frame.
    """
    parts, edges, positions = [], [], {}
    frame_x, frame_w, heap_x, heap_w = 80, 260, 540, 340
    frame_y = heap_y = 184

    def group(attribute, key, dead, label):
        state = ' class="unreachable" data-reachable="false"' if dead else ' data-reachable="true"'
        parts.append(f'<g {attribute}="{key}"{state} tabindex="0" role="button" aria-label="{esc(label).replace(chr(34), "&quot;")}">')

    def value_text(value):
        return value.get('display', value.get('name', '(unassigned)'))

    # The protocol omits library internals. Show their enclosing environment
    # as a collapsed presentation frame, keeping it separate from user frames.
    positions['Builtins'] = (frame_x, 49, 440, 80)
    group('data-builtins', 'true', False, 'Inspect built-in and pre-declared names')
    parts.append(f'<text class="small" x="{frame_x}" y="38">Built-ins</text>')
    parts.append(f'<rect class="frame" x="{frame_x}" y="49" width="440" height="80" rx="5"/>')
    parts.append(f'<text class="small" x="{frame_x + 24}" y="94">:::pre-declared names:::</text>')
    parts.append('</g>')

    for frame in store['frames']:
        key = 'global env' if frame['id'] == 'Global' else frame['id']
        bindings = frame['bindings']
        width = 160 if not bindings else frame_w
        height = max(1, len(bindings)) * 25 + (59 if not bindings else 26)
        positions[frame['id']] = (frame_x, frame_y + 25, width, height)
        group('data-frame', key, frame['isGarbage'], 'Inspect ' + key)
        title = 'Global' if frame['id'] == 'Global' else key
        parts.append(f'<text x="{frame_x}" y="{frame_y + 14}" font-weight="bold">{esc(title)}</text>')
        if frame['id'] in calls and frame['id'] != 'Global':
            parts.append(f'<text class="small" x="{frame_x + 35}" y="{frame_y + 14}">{esc(short_text(calls[frame["id"]], 30))}</text>')
        top = frame_y + 25
        parts.append(f'<rect class="frame" x="{frame_x}" y="{top}" width="{width}" height="{height}" rx="7"/>')
        if frame['id'] == store['activeFrameId']:
            parts.append(f'<rect x="{frame_x}" y="{top}" width="{width}" height="{height}" rx="7" fill="none" stroke="#008577" stroke-width="4" pointer-events="none"/>')
        for index, binding in enumerate(bindings):
            y = top + 27 + index * 25
            value = binding['value']
            label = binding['name'] + ': '
            if value['kind'] == 'ref':
                x = frame_x + frame_w - 20
                edges.append((x, y - 5, value['objectId'], frame['isGarbage'], None))
                parts.append(f'<circle class="dot" cx="{x}" cy="{y - 5}" r="3.5"/>')
            else:
                label += value_text(value)
            parts.append(f'<text x="{frame_x + 12}" y="{y}">{esc(short_text(label, 27))}</text>')
        parts.append('</g>')
        frame_y += height + 58

    for item in store['heap']:
        function = item['kind'] == 'function'
        elements = item.get('elements', [])
        height = 108 if function else 48 + max(1, (len(elements) + 3) // 4) * 40
        positions[item['id']] = (heap_x, heap_y, heap_w, height)
        info = functions.get(item['id'])
        group('data-function' if function else 'data-object', info['id'] if function else item['id'],
              item['isGarbage'], 'Inspect ' + item['id'])
        label_x, label_y = (heap_x + 65, heap_y + 41) if function else (heap_x, heap_y + 13)
        parts.append(f'<text class="small" x="{label_x}" y="{label_y}">{esc(item["id"] + " · " + (item.get("name", "lambda") if function else "list"))}</text>')
        if function:
            cy = heap_y + 36
            for cx in (heap_x + 12, heap_x + 35):
                parts.append(f'<circle class="box" cx="{cx}" cy="{cy}" r="11"/><circle class="dot" cx="{cx}" cy="{cy}" r="3"/>')
            parts.append(f'<path class="line" d="M{heap_x + 12},{cy} V{cy + 18}" marker-end="url(#arrow)"/>')
            parts.append(f'<text class="small" x="{heap_x}" y="{cy + 34}">parameters: {esc(short_text(", ".join(item["params"]), 42))}</text>')
            code_lines = info['source'].splitlines()
            code = (code_lines[1].strip() if len(code_lines) > 1 else code_lines[0]) if code_lines else ''
            parts.append(f'<text class="small" x="{heap_x}" y="{cy + 51}">{esc(short_text(code, 42))}</text>')
            edges.append((heap_x + 35, cy, item['envId'], item['isGarbage'], None))
        else:
            if not elements:
                parts.append(f'<rect class="box" x="{heap_x}" y="{heap_y + 27}" width="40" height="32"/>')
                parts.append(f'<text class="small" x="{heap_x + 10}" y="{heap_y + 45}">[ ]</text>')
            for index, value in enumerate(elements):
                x, y = heap_x + index % 4 * 83, heap_y + 27 + index // 4 * 40
                parts.append(f'<rect class="box" x="{x}" y="{y}" width="83" height="32"/>')
                if value['kind'] == 'ref':
                    parts.append(f'<circle class="dot" cx="{x + 41}" cy="{y + 16}" r="3.5"/>')
                    edges.append((x + 41, y + 16, value['objectId'], item['isGarbage'], y + 36))
                elif len(elements) == 2 and value.get('display') == 'None':
                    parts.append(f'<path class="line" d="M{x},{y + 32} L{x + 83},{y}"/>')
                else:
                    parts.append(f'<text x="{x + 8}" y="{y + 21}">{esc(short_text(value_text(value), 8))}</text>')
        parts.append('</g>')
        heap_y += height + 26

    arrows = []
    for index, frame in enumerate(store['frames']):
        if frame['id'] == 'Global':
            x, y, width, _ = positions['Global']
            arrows.append(f'<path class="line" data-parent="Builtins" d="M{x + width / 2},{y} V129" marker-end="url(#arrow)" pointer-events="none"/>')
            continue
        if frame['parentId'] not in positions:
            continue
        x, y, _, _ = positions[frame['id']]
        px, py, _, ph = positions[frame['parentId']]
        lane = 64 - index % 5 * 10
        arrows.append(f'<path class="line{" unreachable" if frame["isGarbage"] else ""}" d="M{x},{y + 12} H{lane} V{py + ph - 10} H{px}" marker-end="url(#arrow)"/>')
    heap_kinds = {item['id']: item['kind'] for item in store['heap']}
    environment_arrivals = {}
    for index, (x, y, target, dead, departure) in enumerate(edges):
        if target not in positions:
            continue
        tx, ty, tw, th = positions[target]
        if target in heap_kinds:
            target_x = tx + (1 if heap_kinds[target] == 'function' else 0)
            destination_y = ty + (36 if heap_kinds[target] == 'function' else 43)
            if departure is not None:
                # Leave a list cell through its own bottom, cross the row gap,
                # then enter the actual first cell/circle of the target.
                lane = heap_x - 30 - index % 5 * 9
                path = f'M{x},{y} V{departure} H{lane} V{destination_y} H{target_x}'
            else:
                bend = (x + target_x) / 2
                path = f'M{x},{y} C{bend},{y} {bend},{destination_y} {target_x},{destination_y}'
        else:
            target_x = tx + tw
            arrival = environment_arrivals.get(target, 0)
            environment_arrivals[target] = arrival + 1
            destination_y = max(ty + 12, min(y, ty + th - 12) - 6 * (arrival % 5))
            lift = y - 52
            path = f'M{x},{y} C{x},{lift} {target_x + 70},{destination_y} {target_x},{destination_y}'
        kind = 'environment' if target not in heap_kinds else 'reference'
        arrows.append(f'<path class="line{" unreachable" if dead else ""}" data-edge-kind="{kind}" data-target="{target}" d="{path}" marker-end="url(#arrow)" pointer-events="none"/>')
    width = heap_x + heap_w + 80 if store['heap'] else frame_x + 440 + 40
    return document(width, max(frame_y, heap_y) + 12, parts + arrows)
