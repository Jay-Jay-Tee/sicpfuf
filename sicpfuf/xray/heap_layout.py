"""Deterministic box-and-pointer placement and obstacle-aware pointer routes.

Tail chains run to the right, nested heads hang below them. A shared object is
placed once and cycles link back to that same box. This is presentation only;
the reducer's heap order, identity and reachability are left untouched.
"""
import heapq
import math

CELL_WIDTH = 72
CELL_HEIGHT = 32
ROW_HEIGHT = 44
LABEL_HEIGHT = 24
GRID_X = 248
GRID_Y = 100


def object_size(item):
    count = max(1, len(item['elements']))
    return min(4, count) * CELL_WIDTH, LABEL_HEIGHT + math.ceil(count / 4) * ROW_HEIGHT - 12


def place_lists(store, left, top):
    objects = {item['id']: item for item in store['heap'] if item['kind'] != 'function'}
    positions, occupied = {}, set()
    roots_from_frames = [binding['value']['objectId']
                         for frame in store['frames'] for binding in frame['bindings']
                         if binding['value']['kind'] == 'ref']
    next_row = 0
    for dead in (False, True):
        members = [key for key, item in objects.items() if item['isGarbage'] == dead]
        member_set = set(members)
        incoming = {value['objectId'] for key in members for value in objects[key]['elements']
                    if value['kind'] == 'ref' and value['objectId'] in member_set}
        roots = sorted((key for key in members if key not in incoming),
                       key=lambda key: key not in roots_from_frames)
        roots += [key for key in roots_from_frames if key in members and key not in roots]
        roots += [key for key in members if key not in roots]
        for root in roots:
            if root in positions:
                continue
            pending = [(root, 0, next_row)]
            while pending:
                key, column, row = pending.pop()
                if key in positions or key not in objects or objects[key]['isGarbage'] != dead:
                    continue
                item = objects[key]
                width, height = object_size(item)
                columns = math.ceil((width + 24) / GRID_X)
                rows = math.ceil((height + 24) / GRID_Y)
                while any((c, r) in occupied for c in range(column, column + columns)
                          for r in range(row, row + rows)):
                    row += 1
                occupied.update((c, r) for c in range(column, column + columns)
                                for r in range(row, row + rows))
                positions[key] = (left + column * GRID_X, top + row * GRID_Y, width, height)
                children = [(i, value['objectId']) for i, value in enumerate(item['elements'])
                            if value['kind'] == 'ref' and value['objectId'] in objects]
                # Stack the head first so the tail gets placed first. Its
                # horizontal chain then reserves space before nested branches.
                for index, child in (children if len(item['elements']) == 2 else reversed(children)):
                    if len(item['elements']) == 2 and index == 1:
                        pending.append((child, column + columns, row))
                    else:
                        pending.append((child, column + index % 2, row + rows + index // 2))
            next_row = max((r for _, r in occupied), default=-1) + 2
    return positions


class PointerRouter:
    """Route along free horizontal/vertical corridors, sharing collision work.

    A* visits a sparse subset of the coordinate grid, rather than constructing
    an all-pairs graph. The same obstacles and segment cache serve every edge.
    """
    def __init__(self, boxes, ports):
        self.boxes = list(boxes)
        self.xs = sorted({p[0] for p in ports} |
                         {x - 14 for x, y, w, h in boxes} |
                         {x + w + 14 for x, y, w, h in boxes})
        self.ys = sorted({p[1] for p in ports} |
                         {y - 14 for x, y, w, h in boxes} |
                         {y + h + 14 for x, y, w, h in boxes})
        self.x_index = {value: i for i, value in enumerate(self.xs)}
        self.y_index = {value: i for i, value in enumerate(self.ys)}
        self.clear_cache = {}
        self.used_segments = set()

    def clear(self, a, b):
        key = tuple(sorted((a, b)))
        if key not in self.clear_cache:
            ax, ay = a
            bx, by = b
            self.clear_cache[key] = not any(
                (min(ax, bx) < x + w + 4 and max(ax, bx) > x - 4
                 and min(ay, by) < y + h + 4 and max(ay, by) > y - 4)
                for x, y, w, h in self.boxes)
        return self.clear_cache[key]

    def route(self, start, end):
        if start == end:
            return [start]
        first = (self.x_index[start[0]], self.y_index[start[1]], 0)
        goal = (self.x_index[end[0]], self.y_index[end[1]])
        queue, costs, previous = [(0, 0, first)], {first: 0}, {}
        while queue:
            _, cost, current = heapq.heappop(queue)
            if costs[current] != cost:
                continue
            ix, iy, direction = current
            if (ix, iy) == goal:
                result = []
                while True:
                    result.append((self.xs[current[0]], self.ys[current[1]]))
                    if current == first:
                        break
                    current = previous[current]
                result.reverse()
                self.used_segments.update(tuple(sorted((a, b))) for a, b in zip(result, result[1:]))
                # Remove intermediate points on a straight corridor.
                compact = []
                for point in result:
                    while len(compact) >= 2 and (
                        compact[-2][0] == compact[-1][0] == point[0] or
                        compact[-2][1] == compact[-1][1] == point[1]):
                        compact.pop()
                    compact.append(point)
                return compact
            point = (self.xs[ix], self.ys[iy])
            for nx, ny, turn in ((ix - 1, iy, 1), (ix + 1, iy, 1),
                                 (ix, iy - 1, 2), (ix, iy + 1, 2)):
                if not (0 <= nx < len(self.xs) and 0 <= ny < len(self.ys)):
                    continue
                other = (self.xs[nx], self.ys[ny])
                if not self.clear(point, other):
                    continue
                distance = abs(point[0] - other[0]) + abs(point[1] - other[1])
                candidate = cost + distance
                candidate += 16 if direction and direction != turn else 0
                if tuple(sorted((point, other))) in self.used_segments:
                    candidate += 12 + distance * .3
                state = (nx, ny, turn)
                if candidate >= costs.get(state, float('inf')):
                    continue
                costs[state], previous[state] = candidate, current
                estimate = abs(other[0] - end[0]) + abs(other[1] - end[1])
                heapq.heappush(queue, (candidate + estimate, candidate, state))
        # Ports are outside their nodes and the grid contains an outer margin.
        # Failure signals an invalid placement; never silently draw through a box.
        raise ValueError('No free pointer route between %r and %r' % (start, end))
