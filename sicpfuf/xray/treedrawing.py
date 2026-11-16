"""Tree representations of values, for terminal output and --out SVG files.

Flatten proper llist spines into ordered children, keeping empty subtrees,
sharing, cycles and shared tails explicit. A binary representation is selected
deliberately: llist(entry, left, right) has no intrinsic binary-tree tag.
"""
from .boxpointer import atom_text

MAX_NODES = 400
MAX_DEPTH = 60
MAX_SCAN = 12000


class Node:
    def __init__(self, label):
        self.label = label
        self.children = []


class TreeDrawing:
    def __init__(self, value, mode='llist'):
        if mode not in ('llist', 'binary'):
            raise ValueError('draw_tree mode must be "llist" or "binary"')
        self.mode = mode
        self.references, self.labels, self.expanded = {}, {}, {}
        self.count = 0
        self.work = MAX_SCAN
        self.find_shared(value)
        self.root = self.build(value, set(), 0)

    def find_shared(self, root):
        todo, seen, remaining, incomplete = [root], set(), MAX_SCAN, False
        while todo and remaining > 0:
            value = todo.pop()
            if type(value) is not list:
                continue
            key = id(value)
            self.references[key] = self.references.get(key, 0) + 1
            if key in seen:
                continue
            seen.add(key)
            incomplete = incomplete or len(value) > remaining
            for child in reversed(value[:remaining]):
                remaining -= 1
                if type(child) is list:
                    todo.append(child)
        if todo or incomplete:
            # Unknown sharing must not be presented as independent copies.
            self.work = -1

    def tag(self, key):
        if key not in self.labels:
            self.labels[key] = '#' + str(len(self.labels) + 1)
        return self.labels[key]

    def node(self, label):
        if self.count >= MAX_NODES:
            return None
        self.count += 1
        return Node('… node limit' if self.count == MAX_NODES else label)

    def cells(self, value):
        cells, seen = [], set()
        while value is not None:
            self.work -= 1
            if self.work < 0 or type(value) is not list or len(value) != 2 or id(value) in seen:
                return None
            seen.add(id(value))
            cells.append(value)
            value = value[1]
        return cells

    def build(self, value, ancestors, depth):
        if self.count >= MAX_NODES:
            return None
        if value is None:
            return self.node('∅')
        if type(value) is not list:
            if self.mode == 'binary':
                raise ValueError('binary tree expects llist(entry, left, right) or None')
            label = atom_text(value)
            return self.node(label if len(label) <= 72 else label[:71] + '…')
        key = id(value)
        if key in self.expanded:
            tag = self.tag(key)
            original = self.expanded[key]
            if not original.label.endswith(' [' + tag + ']'):
                original.label += ' [' + tag + ']'
            return self.node('↪ ' + tag + (' (cycle)' if key in ancestors else ' (shared)'))
        if depth >= MAX_DEPTH or self.work < 0:
            return self.node('… depth/traversal limit')
        node = self.node('llist')
        if self.count == MAX_NODES:
            return node
        self.expanded[key] = node
        path = ancestors | {key}
        cells = self.cells(value)

        def child(value, label=''):
            item = self.build(value, path, depth + 1)
            if item is not None:
                node.children.append((label, item))
            return self.count < MAX_NODES

        if self.mode == 'binary':
            if cells is None or len(cells) != 3:
                raise ValueError('binary tree expects llist(entry, left, right) or None')
            entry = cells[0][0]
            if type(entry) is list:
                node.label = 'entry'
                # Entries can be data structures as well as scalar values.
                saved_mode = self.mode
                self.mode = 'llist'
                child(entry, 'value')
                self.mode = saved_mode
            else:
                node.label = atom_text(entry)
            child(cells[1][0], 'left')
            child(cells[2][0], 'right')
        elif cells is not None:
            for index, cell in enumerate(cells):
                if index and self.references.get(id(cell), 0) > 1:
                    child(cell, 'tail')
                    break
                if not child(cell[0]):
                    break
        else:
            node.label = 'pair' if len(value) == 2 else 'list'
            for index, item in enumerate(value):
                label = ('head' if index == 0 else 'tail') if len(value) == 2 else str(index)
                if not child(item, label):
                    break
        if self.references.get(key, 0) > 1:
            suffix = ' [' + self.tag(key) + ']'
            if not node.label.endswith(suffix):
                node.label += suffix
        return node

    def text(self):
        lines = [self.root.label]

        def walk(node, prefix):
            for index, (label, item) in enumerate(node.children):
                last = index == len(node.children) - 1
                lines.append(prefix + ('└── ' if last else '├── ') +
                             (label + ': ' if label else '') + item.label)
                walk(item, prefix + ('    ' if last else '│   '))
        walk(self.root, '')
        return '\n'.join(lines)

    def svg(self):
        from .svg import document, esc, short_text
        parts, links = [], []

        def measure(node):
            node.width = max(70, min(360, len(node.label) * 8.4 + 24))
            node.span = max(node.width, sum(measure(item) for _, item in node.children) +
                            max(0, len(node.children) - 1) * 26)
            return node.span

        bottom = [0]

        def place(node, left, depth):
            node.x = left + (node.span - node.width) / 2
            node.y = 24 + depth * 92
            bottom[0] = max(bottom[0], node.y + 40)
            width = sum(item.span for _, item in node.children) + max(0, len(node.children) - 1) * 26
            offset = left + (node.span - width) / 2
            for _, item in node.children:
                place(item, offset, depth + 1)
                offset += item.span + 26

        width = measure(self.root) + 48
        place(self.root, 24, 0)

        def paint(node):
            x, y = node.x + node.width / 2, node.y
            for label, item in node.children:
                tx, ty = item.x + item.width / 2, item.y
                links.append(f'<path class="line" d="M{x},{y + 40} C{x},{y + 62} {tx},{ty - 22} {tx},{ty}" marker-end="url(#arrow)"/>')
                if label:
                    links.append(f'<text class="small" x="{tx + 8}" y="{ty - 10}">{esc(label)}</text>')
                paint(item)
            parts.append(f'<g><title>{esc(node.label)}</title><rect class="box" x="{node.x}" y="{y}" width="{node.width}" height="40" rx="8"/>')
            parts.append(f'<text x="{x}" y="{y + 25}" text-anchor="middle">{esc(short_text(node.label, 39))}</text></g>')
        paint(self.root)
        return document(width, bottom[0] + 24, links + parts)


def draw(value, mode='llist'):
    return TreeDrawing(value, mode).text()
