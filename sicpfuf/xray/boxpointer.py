"""
sicpfuf/xray/boxpointer.py — BOX-AND-POINTER diagrams, drawn with text.

    draw_data(llist(1, 2, 3))

    [1|•]-->[2|•]-->[3|/]

A pair is a box with two halves: the HEAD on the left, the TAIL on the right.
    * a number, string, boolean or function is written inside its half
    * •  means "this half points at another box": follow the arrow
    * /  in a tail means None, the empty linked list (the end of the line)

Tails go to the RIGHT, heads go DOWN:

    draw_data(llist(llist(1, 2), 3))          [•|•]----------->[3|/]
                                               |
                                               v
                                               [1|•]-->[2|/]

When the same box is reached twice (SHARING, or a cycle), it is drawn once
and given a label:

    xs = llist(1, 2)                          [•|•]-------------->#1
    draw_data(pair(xs, xs))                    |
                                               v
                                               #1=[1|•]-->[2|/]

A list with more (or fewer) than two items, such as [1, 2, 3], is one long
box with a slot per item.
"""

from ..values import Closure, Builtin, show_atom

MAX_BOXES = 400


def atom_text(v):
    if type(v) is Closure:
        return "ƒ" if v.name == "(anonymous)" else "ƒ " + v.name
    if type(v) is Builtin:
        return "ƒ " + v.name
    return show_atom(v)


class Diagram:
    def __init__(self, root):
        self.grid = {}                  # (row, col) → character
        self.labels = {}                # id(box) → label number, for boxes reached more than once
        self.drawn = set()              # ids of the boxes already on the canvas
        self.count = 0
        self.find_shared(root)

    def find_shared(self, root):
        """A first walk over the structure: which boxes are pointed at more than once?"""
        seen = set()
        stack = [root]
        while stack:
            v = stack.pop()
            if type(v) is not list:
                continue
            if id(v) in seen:
                if id(v) not in self.labels:
                    self.labels[id(v)] = len(self.labels) + 1
                continue
            seen.add(id(v))
            stack.extend(reversed(v))

    def put(self, row, col, text):
        for i, ch in enumerate(text):
            self.grid[(row, col + i)] = ch

    def box(self, v, row, col):
        """Draw the box of v with its top-left corner at (row, col).
        Returns (width, height) of everything that was drawn for it."""
        if id(v) in self.drawn:                     # seen before: just name it
            text = f"#{self.labels[id(v)]}"
            self.put(row, col, text)
            return len(text), 1
        self.drawn.add(id(v))
        self.count += 1
        if self.count > MAX_BOXES:
            self.put(row, col, "...")
            return 3, 1
        prefix = f"#{self.labels[id(v)]}=" if id(v) in self.labels else ""
        is_pair = len(v) == 2
        # 1. what is written in each slot, and which slots need an arrow going DOWN
        slots, down = [], []
        for i, item in enumerate(v):
            if is_pair and i == 1:                  # the TAIL of a pair: goes right, or is / for None
                slots.append("/" if item is None else "•" if type(item) is list else atom_text(item))
            elif type(item) is list:
                slots.append("•")
                down.append(i)
            else:
                slots.append(atom_text(item))
        # 2. draw what hangs below first, so we know how wide each slot must be
        widths = [len(text) for text in slots]
        height = 1
        slot_col = col + len(prefix) + 1
        starts = []
        for i, item in enumerate(v):
            starts.append(slot_col)
            if i in down:
                w, h = self.box(item, row + 3, slot_col)
                self.put(row + 1, slot_col, "|")
                self.put(row + 2, slot_col, "v")
                height = max(height, h + 3)
                if not is_pair or i == 0:
                    widths[i] = max(widths[i], w if not is_pair else 1)
                below_width = w
            slot_col += widths[i] + 1
        # 3. the box itself
        text = prefix + "[" + "|".join(slots[i].ljust(widths[i]) for i in range(len(v))) + "]"
        self.put(row, col, text)
        width = len(text)
        if is_pair and 0 in down:
            width = max(width, below_width + len(prefix) + 1)
        # 4. a pair's tail goes to the RIGHT
        if is_pair and type(v[1]) is list:
            arrow_to = col + width + 3
            self.put(row, col + len(text), "-" * (arrow_to - col - len(text) - 1) + ">")
            w, h = self.box(v[1], row, arrow_to)
            width = arrow_to - col + w
            height = max(height, h)
        return width, height

    def text(self):
        if not self.grid:
            return ""
        rows = max(r for r, _ in self.grid) + 1
        lines = []
        for r in range(rows):
            cols = [c for (rr, c) in self.grid if rr == r]
            line = [" "] * (max(cols) + 1 if cols else 0)
            for c in cols:
                line[c] = self.grid[(r, c)]
            lines.append("".join(line).rstrip())
        return "\n".join(lines)


def draw(value):
    """The box-and-pointer diagram of `value`, as text."""
    if type(value) is not list:
        return atom_text(value)
    d = Diagram(value)
    d.box(value, 0, 0)
    return d.text()
