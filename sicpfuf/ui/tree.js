/* A bounded projection of a recorded heap. It never evaluates the program. */
(function () {
  "use strict";
  const NS = "http://www.w3.org/2000/svg", MAX_NODES = 320, MAX_DEPTH = 48;
  const empty = value => value && value.kind !== "ref" && value.display === "None";
  const text = value => value ? value.objectId || value.display || value.name || "(unassigned)" : "(missing)";

  function roots(store) {
    if (!store) return [];
    const heap = new Map(store.heap.map(item => [item.id, item])), options = new Map();
    const frames = [...store.frames].sort((a, b) => Number(b.id === store.activeFrameId) - Number(a.id === store.activeFrameId));
    for (const frame of frames) for (const binding of frame.bindings) {
      const value = binding.value, item = heap.get(value.objectId);
      if ((!item || item.kind === "function") && !empty(value)) continue;
      const id = item ? item.id : `empty:${frame.id}:${binding.name}`;
      const label = `${frame.id === "Global" ? "Global" : frame.id} · ${binding.name}`;
      if (options.has(id)) options.get(id).label += ` / ${label}`;
      else options.set(id, { id, value, label: label + (item ? ` → ${id}` : " → ∅") });
    }
    for (const item of store.heap) if (item.kind !== "function" && !options.has(item.id)) {
      options.set(item.id, { id: item.id, value: { kind: "ref", objectId: item.id },
        label: `${item.id} · ${item.elements.length} slots${item.isGarbage ? " · unreachable" : ""}` });
    }
    return [...options.values()];
  }

  function project(store, value, format) {
    const heap = new Map(store.heap.map(item => [item.id, item]));
    const incoming = new Map(), expanded = new Map(), nodes = [], notes = new Set();
    let scans = 6000;
    const count = value => { if (value.kind === "ref") incoming.set(value.objectId, (incoming.get(value.objectId) || 0) + 1); };
    for (const item of store.heap) for (const child of item.elements || []) count(child);
    for (const frame of store.frames) for (const binding of frame.bindings) count(binding.value);

    function make(label, caption, objectId, kind = "value") {
      if (nodes.length >= MAX_NODES) {
        notes.add(`Showing at most ${MAX_NODES} nodes. Select a smaller subtree to explore more.`);
        return null;
      }
      const node = { id: "tree-" + nodes.length, label, caption, objectId, kind, children: [], dead: Boolean(heap.get(objectId)?.isGarbage) };
      nodes.push(node);
      return node;
    }

    function sequence(value) {
      const cells = [], seen = new Set();
      while (!empty(value)) {
        if (--scans < 0) return null;
        const item = value.kind === "ref" && heap.get(value.objectId);
        if (!item || item.kind !== "list" || item.elements.length !== 2 || seen.has(item.id)) return null;
        seen.add(item.id);
        cells.push(item);
        value = item.elements[1];
      }
      return cells;
    }

    function visit(value, ancestors, depth) {
      if (!value || value.kind !== "ref") {
        const invalid = format === "binary" && !empty(value);
        if (invalid) notes.add("Binary mode expects llist(entry, left, right), with None for empty subtrees.");
        return make(empty(value) ? "∅" : text(value), empty(value) ? "empty llist" : invalid ? "invalid subtree" : "", null, invalid ? "invalid" : "value");
      }
      const id = value.objectId, item = heap.get(id);
      if (!item) return make(id, "unavailable", id, "reference");
      if (expanded.has(id)) {
        const kind = ancestors.has(id) ? "cycle" : "shared";
        const node = make("↪ " + id, kind + " reference", id, "reference");
        if (node) node.target = expanded.get(id).id;
        notes.add("Shared nodes and cycles link to their original node.");
        return node;
      }
      if (depth >= MAX_DEPTH || scans < 0) {
        notes.add("Large branches are abbreviated. Select a smaller subtree to continue.");
        return make(id, "… inspect subtree", id, "omitted");
      }
      const node = make(item.kind === "function" ? "function" : "llist", id, id, "object");
      if (!node) return null;
      node.dead = Boolean(item.isGarbage);
      expanded.set(id, node);
      if (item.kind === "function") return node;
      const path = new Set(ancestors); path.add(id);
      const cells = sequence(value);
      function child(value, label) {
        const next = visit(value, path, depth + 1);
        if (next) node.children.push({ node: next, label });
        return Boolean(next);
      }
      if (format === "binary") {
        if (!cells || cells.length !== 3) {
          node.label = id; node.caption = "expected 3-item llist"; node.kind = "invalid";
          notes.add("Binary mode expects llist(entry, left, right), with None for empty subtrees.");
        } else {
          node.label = text(cells[0].elements[0]); node.caption = id + " · binary node";
          if (cells[0].elements[0].kind === "ref") child(cells[0].elements[0], "entry");
          child(cells[1].elements[0], "left"); child(cells[2].elements[0], "right");
        }
      } else if (cells) {
        for (let i = 0; i < cells.length; i++) {
          if (i > 0 && (incoming.get(cells[i].id) || 0) > 1) {
            child({ kind: "ref", objectId: cells[i].id }, "tail");
            notes.add("Shared tails are shown explicitly instead of being copied.");
            break;
          }
          if (!child(cells[i].elements[0], String(i))) break;
        }
      } else {
        node.label = item.elements.length === 2 ? "pair" : "list";
        notes.add("Non-llist pairs and arrays show their slots explicitly.");
        for (let i = 0; i < item.elements.length; i++) {
          if (!child(item.elements[i], item.elements.length === 2 ? (i === 0 ? "head" : "tail") : String(i))) break;
        }
      }
      return node;
    }
    return { root: visit(value, new Set(), 0), nodes, notes };
  }

  function draw(store, value, format = "llist") {
    const graph = project(store, value, format);
    function element(tag, attributes = {}, content) {
      const node = document.createElementNS(NS, tag);
      for (const [key, value] of Object.entries(attributes)) node.setAttribute(key, String(value));
      if (content !== undefined) node.textContent = content;
      return node;
    }
    function measure(node) {
      node.width = Math.max(76, Math.min(220, Math.max(Array.from(node.label).length * 8, node.caption.length * 6) + 28));
      node.span = Math.max(node.width, node.children.reduce((sum, child) => sum + measure(child.node), 0) + Math.max(0, node.children.length - 1) * 24);
      return node.span;
    }
    let bottom = 0;
    function place(node, left, depth) {
      node.x = left + (node.span - node.width) / 2; node.y = 28 + depth * 104;
      bottom = Math.max(bottom, node.y + 56);
      const total = node.children.reduce((sum, child) => sum + child.node.span, 0) + Math.max(0, node.children.length - 1) * 24;
      let offset = left + (node.span - total) / 2;
      for (const child of node.children) { place(child.node, offset, depth + 1); offset += child.node.span + 24; }
    }
    const width = measure(graph.root) + 56;
    place(graph.root, 28, 0);
    const svg = element("svg", { viewBox: `0 0 ${width} ${bottom + 48}`, width, height: bottom + 48, class: "tree-diagram", role: "group", "aria-label": "Tree view" });
    const definitions = element("defs"), marker = element("marker", { id: "tree-arrow", viewBox: "0 0 10 10", refX: 9, refY: 5, markerWidth: 6, markerHeight: 6, orient: "auto" });
    marker.append(element("path", { d: "M0,0 L10,5 L0,10 Z" })); definitions.append(marker); svg.append(definitions);
    const links = element("g"), boxes = element("g"), byId = new Map(graph.nodes.map(node => [node.id, node]));
    for (const node of graph.nodes) {
      for (const child of node.children) {
        const next = child.node, x = node.x + node.width / 2, y = node.y + 56;
        const tx = next.x + next.width / 2, ty = next.y;
        links.append(element("path", { class: "line tree-link", d: `M${x},${y} C${x},${y + 24} ${tx},${ty - 24} ${tx},${ty}`, "data-source": node.objectId || node.id, "data-target": next.objectId || next.id, "marker-end": "url(#tree-arrow)" }));
        links.append(element("text", { class: "small tree-edge-label", x: tx + 9, y: ty - 12 }, child.label));
      }
      if (node.target) {
        const target = byId.get(node.target), x = node.x + node.width, y = node.y + 28;
        const tx = target.x + target.width, ty = target.y + 28, bend = Math.max(x, tx) + 18;
        links.append(element("path", { class: "line tree-reference", d: `M${x},${y} C${bend},${y} ${bend},${ty} ${tx},${ty}`, "data-source": node.objectId, "data-target": target.objectId, "data-tree-reference": node.caption, "marker-end": "url(#tree-arrow)" }));
      }
      const attributes = { "data-tree-node": node.id, "data-node-id": node.objectId || node.id,
        "data-bounds": `${node.x},${node.y},${node.width},56`, class: `tree-node tree-${node.kind}${node.dead ? " unreachable" : ""}` };
      if (node.objectId) Object.assign(attributes, { "data-object": node.objectId, tabindex: 0, role: "button", "aria-label": `Inspect ${node.objectId}: ${node.label}` });
      const group = element("g", attributes);
      group.append(element("title", {}, node.label + (node.caption ? " · " + node.caption : "")));
      group.append(element("rect", { class: "box", x: node.x, y: node.y, width: node.width, height: 56, rx: 10 }));
      const label = Array.from(node.label);
      group.append(element("text", { x: node.x + node.width / 2, y: node.y + (node.caption ? 23 : 34), "text-anchor": "middle" }, label.length > 24 ? label.slice(0, 23).join("") + "…" : node.label));
      if (node.caption) group.append(element("text", { class: "small", x: node.x + node.width / 2, y: node.y + 43, "text-anchor": "middle" }, node.caption));
      boxes.append(group);
    }
    svg.append(links, boxes);
    return { svg, note: [...graph.notes].join(" ") };
  }
  window.sicpfufTree = { roots, draw };
})();
