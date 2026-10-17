/* Organización física compartida: CPD, racks y navegación de topología. */
let physicalLevel = "inside",
  physicalRack = "",
  physicalCpd = "",
  physicalBundles = true;
let physicalRegions = [],
  physicalOriginalEdges = [],
  physicalLabelBounds = [];
const physicalViews = new Map(),
  physicalSignatures = new Map();
wireNames["rack.summary"] = "Armario rack";
wirePositionKey = function () {
  return (
    "lanwire.layout.v2." +
    state.storage +
    ":" +
    physicalLevel +
    ":" +
    physicalRack +
    ":" +
    physicalCpd
  );
};
const physicalBase = {
  render,
  refresh,
  fullDetails,
  topology: wireRenderTopology,
  paint: wirePaint,
  pointer: wirePointer,
  bounds: wireBounds,
  center: wireCenterFromDetails,
};
function wireOrderedPorts(n) {
  const targets = new Map();
  for (const e of wireEdges()) {
    const local =
      e.a?.device === n.id ? e.a : e.b?.device === n.id ? e.b : null;
    const remote = local === e.a ? e.b : e.a;
    if (local)
      targets.set(local.port, wirePositions[remote?.device] || { x: 0, y: 0 });
  }
  return Object.keys(n.data.ports || {}).sort((a, b) => {
    const pa = n.data.ports[a],
      pb = n.data.ports[b],
      ta = targets.get(a),
      tb = targets.get(b);
    return (
      String(pa.kind || "").localeCompare(String(pb.kind || "")) ||
      Number(Boolean(tb)) - Number(Boolean(ta)) ||
      (ta && tb ? ta.x - tb.x || ta.y - tb.y : 0) ||
      a.localeCompare(b, "es", { numeric: true })
    );
  });
}
function physicalRackOf(r) {
  return ["rack", "rack.summary"].includes(r.data?.type)
    ? r.id
    : r.data?.location?.rack || "";
}
function physicalCpdOf(rack) {
  return state.records.find((r) => r.id === rack)?.data?.location?.cpd || "";
}
function physicalRoomName(id) {
  return state.cpds?.find((c) => c.id === id)?.name || "Sin CPD";
}
function physicalSize(n) {
  if (n.physicalSize) return n.physicalSize;
  const count = Object.keys(n.data.ports || {}).length;
  const cols = count > 24 ? 12 : count > 8 ? 8 : Math.max(1, count);
  return {
    w: count ? Math.max(240, cols * 43 + 28) : 240,
    h: 90 + Math.ceil(count / cols) * 29,
  };
}
// Fuerzas deterministas por componente: atracción de cables y separación de tarjetas.
function physicalPack(nodes, edges) {
  const sizes = new Map(nodes.map((n) => [n.id, physicalSize(n)]));
  const adjacency = new Map(nodes.map((n) => [n.id, new Set()]));
  for (const e of edges)
    if (
      adjacency.has(e.a?.device) &&
      adjacency.has(e.b?.device) &&
      e.a.device !== e.b.device
    ) {
      adjacency.get(e.a.device).add(e.b.device);
      adjacency.get(e.b.device).add(e.a.device);
    }
  const result = new Map(),
    seen = new Set();
  let offsetX = 0,
    offsetY = 0,
    rowH = 0;
  const connected = nodes
    .filter((n) => adjacency.get(n.id).size)
    .sort(
      (a, b) =>
        adjacency.get(b.id).size - adjacency.get(a.id).size ||
        a.id.localeCompare(b.id),
    );
  for (const root of connected) {
    if (seen.has(root.id)) continue;
    const ids = [],
      queue = [root.id];
    seen.add(root.id);
    while (queue.length) {
      const id = queue.shift();
      ids.push(id);
      for (const next of adjacency.get(id))
        if (!seen.has(next)) {
          seen.add(next);
          queue.push(next);
        }
    }
    const positions = ids.map((id, i) => ({
      id,
      x: i ? Math.cos(i * 2.39996) * Math.sqrt(i) * 220 : 0,
      y: i ? Math.sin(i * 2.39996) * Math.sqrt(i) * 220 : 0,
    }));
    const index = new Map(positions.map((p) => [p.id, p]));
    // El límite mantiene la interacción acotada incluso en instalaciones grandes.
    const iterations = ids.length > 200 ? 45 : 110;
    for (let step = 0; step < iterations; step++) {
      const forces = new Map(ids.map((id) => [id, { x: 0, y: 0 }]));
      for (let i = 0; i < positions.length; i++)
        for (let j = i + 1; j < positions.length; j++) {
          const a = positions[i],
            b = positions[j],
            sa = sizes.get(a.id),
            sb = sizes.get(b.id);
          let dx = b.x - a.x,
            dy = b.y - a.y;
          if (!dx && !dy) dx = 1;
          const overlapX = (sa.w + sb.w) / 2 + 80 - Math.abs(dx),
            overlapY = (sa.h + sb.h) / 2 + 85 - Math.abs(dy);
          if (overlapX > 0 && overlapY > 0) {
            const axis = overlapX < overlapY ? "x" : "y",
              delta = axis === "x" ? dx : dy;
            const f =
              (axis === "x" ? overlapX : overlapY) *
              0.32 *
              Math.sign(delta || 1);
            forces.get(a.id)[axis] -= f;
            forces.get(b.id)[axis] += f;
          }
        }
      for (const a of positions)
        for (const id of adjacency.get(a.id)) {
          const b = index.get(id),
            dx = b.x - a.x,
            dy = b.y - a.y,
            d = Math.hypot(dx, dy) || 1;
          const desired = (sizes.get(a.id).w + sizes.get(id).w) / 2 + 140;
          const f = (d - desired) * 0.025;
          forces.get(a.id).x += (dx / d) * f;
          forces.get(a.id).y += (dy / d) * f;
        }
      for (const p of positions) {
        const f = forces.get(p.id);
        p.x += Math.max(-32, Math.min(32, f.x));
        p.y += Math.max(-32, Math.min(32, f.y));
      }
    }
    // Separación final sin fuerzas de atracción para garantizar tarjetas no solapadas.
    for (let step = 0; step < Math.min(80, ids.length * 3); step++) {
      let changed = false;
      for (let i = 0; i < positions.length; i++)
        for (let j = i + 1; j < positions.length; j++) {
          const a = positions[i],
            b = positions[j],
            sa = sizes.get(a.id),
            sb = sizes.get(b.id),
            dx = b.x - a.x,
            dy = b.y - a.y;
          const ox = (sa.w + sb.w) / 2 + 55 - Math.abs(dx),
            oy = (sa.h + sb.h) / 2 + 70 - Math.abs(dy);
          if (ox > 0 && oy > 0) {
            changed = true;
            if (ox < oy) {
              const v = (ox / 2 + 0.1) * Math.sign(dx || 1);
              a.x -= v;
              b.x += v;
            } else {
              const v = (oy / 2 + 0.1) * Math.sign(dy || 1);
              a.y -= v;
              b.y += v;
            }
          }
        }
      if (!changed) break;
    }
    const minX = Math.min(...positions.map((p) => p.x - sizes.get(p.id).w / 2)),
      minY = Math.min(...positions.map((p) => p.y - sizes.get(p.id).h / 2));
    const width =
        Math.max(...positions.map((p) => p.x + sizes.get(p.id).w / 2)) - minX,
      height =
        Math.max(...positions.map((p) => p.y + sizes.get(p.id).h / 2)) - minY;
    if (offsetX && offsetX + width > 1800) {
      offsetX = 0;
      offsetY += rowH + 140;
      rowH = 0;
    }
    for (const p of positions)
      result.set(p.id, {
        x: offsetX + p.x - minX - sizes.get(p.id).w / 2,
        y: offsetY + p.y - minY - sizes.get(p.id).h / 2,
      });
    offsetX += width + 150;
    rowH = Math.max(rowH, height);
  }
  const empty = nodes.filter((n) => !seen.has(n.id));
  const top = offsetY + rowH + (connected.length ? 160 : 0);
  const maxW = Math.max(260, ...empty.map((n) => sizes.get(n.id).w + 50)),
    maxH = Math.max(150, ...empty.map((n) => sizes.get(n.id).h + 60));
  empty.forEach((n, i) =>
    result.set(n.id, { x: (i % 4) * maxW, y: top + Math.floor(i / 4) * maxH }),
  );
  return result;
}
wireLayout = function (nodes) {
  const edges = wireEdges();
  physicalRegions = [];
  const groupOfNode = (n) =>
    physicalLevel === "outside"
      ? n.data.location?.cpd || ""
      : physicalRackOf(n);
  const groups = new Map();
  for (const n of nodes) {
    const id = groupOfNode(n);
    if (!groups.has(id)) groups.set(id, []);
    groups.get(id).push(n);
  }
  const regions = [];
  for (const [id, items] of groups) {
    // Los enlaces salientes también influyen en la distribución local.
    const localIds = new Set(items.map((n) => n.id)),
      proxies = new Map();
    const localEdges = edges
      .filter((e) => localIds.has(e.a?.device) || localIds.has(e.b?.device))
      .map((e) => {
        const mapEnd = (end) => {
          if (!end || localIds.has(end.device)) return end;
          const remote = state.records.find((n) => n.id === end.device);
          const id = "@outside:" + (remote ? groupOfNode(remote) : end.device);
          if (!proxies.has(id))
            proxies.set(id, { id, data: {}, physicalSize: { w: 80, h: 65 } });
          return { ...end, device: id };
        };
        return { a: mapEnd(e.a), b: mapEnd(e.b) };
      });
    const local = physicalPack([...items, ...proxies.values()], localEdges);
    const w =
        Math.max(
          300,
          ...items.map((n) => local.get(n.id).x + physicalSize(n).w),
        ) + 80,
      h =
        Math.max(
          140,
          ...items.map((n) => local.get(n.id).y + physicalSize(n).h),
        ) + 100;
    regions.push({
      id,
      items,
      local,
      physicalSize: { w, h },
      data: {},
      label:
        physicalLevel === "outside"
          ? state.cpds?.find((c) => c.id === id)?.name || "Sin CPD"
          : id
            ? labelOf(state.records.find((r) => r.id === id) || { id })
            : "Equipos sin rack",
    });
  }
  const nodeGroups = new Map(nodes.map((n) => [n.id, groupOfNode(n)]));
  const links = edges
    .filter((e) => nodeGroups.has(e.a?.device) && nodeGroups.has(e.b?.device))
    .map((e) => ({
      a: { device: nodeGroups.get(e.a.device) },
      b: { device: nodeGroups.get(e.b.device) },
    }));
  const places = physicalPack(regions, links),
    result = new Map();
  for (const region of regions) {
    const p = places.get(region.id);
    physicalRegions.push({
      id: region.id,
      x: p.x,
      y: p.y,
      w: region.physicalSize.w,
      h: region.physicalSize.h,
      label: region.label,
    });
    for (const n of region.items) {
      const point = region.local.get(n.id);
      result.set(n.id, { x: p.x + 40 + point.x, y: p.y + 65 + point.y });
    }
  }
  return result;
};
function physicalSwitchLevel(level, rack = "") {
  const key = physicalLevel + ":" + physicalRack + ":" + physicalCpd;
  physicalViews.set(key, {
    positions: structuredClone(wirePositions),
    camera: { ...camera },
    focus: wireFocus,
  });
  wireSavePositions();
  physicalLevel = level;
  physicalRack = rack;
  wireFocus = null;
  wireHidden.clear();
  const saved = physicalViews.get(level + ":" + rack + ":" + physicalCpd);
  if (!saved) wireLoadPositions();
  wirePositions = saved?.positions || wirePositions;
  camera = saved?.camera || { x: 40, y: 40, z: 1 };
  wireFocus = saved?.focus || null;
  render();
  if (!saved) wireFit();
}
wireRenderTopology = function (rows) {
  physicalLabelBounds = [];
  physicalOriginalEdges = wireEdges();
  const scope = physicalLevel + ":" + physicalRack + ":" + physicalCpd;
  const signature = JSON.stringify(
    state.records.map((r) => [
      r.id,
      r.data.location,
      Object.keys(r.data.ports || {}),
      r.data.endpoints,
      r.data.source,
    ]),
  );
  if (
    physicalSignatures.has(scope) &&
    physicalSignatures.get(scope) !== signature
  )
    wirePositions = {};
  physicalSignatures.set(scope, signature);
  const original = state.records;
  const effectiveRack = physicalRack || wireFilter.rack;
  const rackAllowed = (id) =>
    (!effectiveRack || id === effectiveRack) &&
    (!physicalCpd ||
      (physicalCpd === "none"
        ? !physicalCpdOf(id)
        : physicalCpdOf(id) === physicalCpd));
  if (physicalLevel === "outside") {
    const allowedIds = new Set(rows.map((r) => r.id));
    const contextFiltered = Boolean(
      $("#search").value.trim() ||
      $("#filter").value ||
      Object.values(wireFilter).some(Boolean),
    );
    const eligible = new Set(rows.map(physicalRackOf));
    for (const edge of physicalOriginalEdges)
      if (allowedIds.has(edge.wire.id))
        for (const end of [edge.a, edge.b])
          if (end) {
            const r = original.find((r) => r.id === end.device);
            if (r) eligible.add(physicalRackOf(r));
          }
    const racks = original.filter(
      (r) =>
        r.data.type === "rack" &&
        rackAllowed(r.id) &&
        (!contextFiltered || eligible.has(r.id)),
    );
    const represented = new Set(racks.map((r) => r.id));
    const context = new Map();
    const visibleEdges = [];
    for (const e of physicalOriginalEdges) {
      const mapEnd = (end) => {
        if (!end) return null;
        const record = original.find((r) => r.id === end.device);
        const rack = record?.data.location?.rack;
        return {
          device: rack || end.device,
          port: record ? labelOf(record) + " · " + end.port : end.port,
        };
      };
      const a = mapEnd(e.a),
        b = mapEnd(e.b);
      if (!a && !b) continue;
      const touches = represented.has(a?.device) || represented.has(b?.device);
      const unassigned =
        (!physicalRack || physicalRack === "none") &&
        !physicalCpd &&
        [e.a, e.b].some(
          (end) =>
            end &&
            allowedIds.has(end.device) &&
            (physicalRack !== "none" ||
              !original.find((r) => r.id === end.device)?.data.location?.rack),
        );
      if (!touches && !unassigned) continue;
      if (a?.device === b?.device) continue;
      if (
        !allowedIds.has(e.wire.id) &&
        ![e.a, e.b].some((end) => end && allowedIds.has(end.device)) &&
        !racks.some((r) => allowedIds.has(r.id))
      )
        continue;
      for (const end of [a, b])
        if (end && !represented.has(end.device)) {
          const r = original.find((r) => r.id === end.device);
          if (r)
            context.set(r.id, {
              ...r,
              data: {
                ...r.data,
                ports: {},
                type: r.data.type === "rack" ? "rack.summary" : r.data.type,
              },
            });
        }
      visibleEdges.push({
        ...e,
        wire: {
          ...e.wire,
          data: {
            ...e.wire.data,
            source: undefined,
            endpoints: [a, b].filter(Boolean),
          },
        },
      });
    }
    const grouped = new Map();
    for (const e of visibleEdges) {
      const key = physicalBundles
        ? [e.wire.data.endpoints[0]?.device, e.wire.data.endpoints[1]?.device]
            .sort()
            .join("|")
        : e.wire.id;
      if (!grouped.has(key)) grouped.set(key, []);
      grouped.get(key).push(e);
    }
    const wires = [...grouped.values()].map((es) => ({
      ...es[0].wire,
      bundle: es.map((e) => e.wire.id),
    }));
    const nodes = [
      ...racks.map((r) => ({
        ...r,
        data: { ...r.data, type: "rack.summary", ports: {} },
      })),
      ...context.values(),
    ];
    state.records = [...nodes, ...wires];
    try {
      physicalBase.topology(state.records);
    } finally {
      state.records = original;
    }
  } else {
    let filtered = rows.filter(
      (r) =>
        r.data.type !== "rack" &&
        (!effectiveRack ||
          r.data.type === "wire" ||
          (effectiveRack === "none"
            ? !physicalRackOf(r)
            : physicalRackOf(r) === effectiveRack)) &&
        (!physicalCpd ||
          r.data.type === "wire" ||
          rackAllowed(physicalRackOf(r))),
    );
    if (effectiveRack || physicalCpd) {
      const ids = new Set(
        filtered.filter((r) => r.data.type !== "wire").map((r) => r.id),
      );
      filtered = filtered.filter(
        (r) =>
          r.data.type !== "wire" ||
          physicalOriginalEdges.some(
            (e) =>
              e.wire.id === r.id &&
              (ids.has(e.a?.device) || ids.has(e.b?.device)),
          ),
      );
    }
    // Los extremos externos se conservan como contexto, dentro de su rack real.
    physicalBase.topology(filtered);
  }
  const toolbar = $(".wire-navigation");
  const controls = document.createElement("div");
  controls.className = "physical-levels";
  controls.innerHTML = `<button data-level="inside" class="${physicalLevel === "inside" ? "active" : ""}">Interior de racks</button><button data-level="outside" class="${physicalLevel === "outside" ? "active" : ""}">Vista general de racks</button><label>CPD <select id="physical-cpd"><option value="">Todos los CPD</option><option value="none">Sin CPD</option>${(state.cpds || []).map((c) => `<option value="${esc(c.id)}">${esc(c.name)}</option>`).join("")}</select></label><label>Rack <select id="physical-rack"><option value="">Todos los racks</option><option value="none">Sin rack</option>${state.records
    .filter((r) => r.data.type === "rack")
    .map((r) => `<option value="${esc(r.id)}">${esc(labelOf(r))}</option>`)
    .join(
      "",
    )}</select></label><label><input id="physical-bundles" type="checkbox" ${physicalBundles ? "checked" : ""}> Agrupar enlaces</label>`;
  toolbar.before(controls);
  $("#physical-cpd").value = physicalCpd;
  $("#physical-rack").value = effectiveRack;
  controls
    .querySelectorAll("[data-level]")
    .forEach(
      (b) =>
        (b.onclick = () => physicalSwitchLevel(b.dataset.level, physicalRack)),
    );
  $("#physical-rack").onchange = (e) =>
    physicalSwitchLevel(physicalLevel, e.target.value);
  $("#physical-cpd").onchange = (e) => {
    physicalCpd = e.target.value;
    physicalSwitchLevel(physicalLevel, "");
  };
  $("#physical-bundles").onchange = (e) => {
    physicalBundles = e.target.checked;
    render();
  };
  $("#wire-board").ondblclick = (e) => {
    const el = e.target.closest("[data-node]") || physicalNodeAt(e);
    if (!el) return;
    clearTimeout(clickTimer);
    selected = el.dataset.node;
    const r = state.records.find((r) => r.id === selected);
    if (physicalLevel === "outside" && r?.data.type === "rack")
      physicalSwitchLevel("inside", r.id);
    else if (r) fullDetails(r);
  };
  for (const n of wireGraph.nodes) {
    const el = document.querySelector(`[data-node="${CSS.escape(n.id)}"]`);
    el.style.width = physicalSize(n).w + "px";
    el.style.minHeight = physicalSize(n).h + "px";
    const ports = el.querySelector(".wire-ports");
    if (ports)
      ports.style.gridTemplateColumns = `repeat(${Object.keys(n.data.ports || {}).length > 24 ? 12 : 8},minmax(0,1fr))`;
  }
  wirePaint();
};
wireBounds = function () {
  if (!wireGraph) return { x: 0, y: 0, right: 240, bottom: 100 };
  const rectangles = wireGraph.nodes.map((n) => {
    const p = wirePositions[n.id],
      s = physicalSize(n);
    return { x: p.x, y: p.y, right: p.x + s.w, bottom: p.y + s.h };
  });
  rectangles.push(
    ...physicalLabelBounds.map((r) => ({
      x: r.x,
      y: r.y,
      right: r.x + r.w,
      bottom: r.y + r.h,
    })),
  );
  rectangles.push(
    ...physicalRegions.map((r) => ({
      x: r.x,
      y: r.y,
      right: r.x + r.w,
      bottom: r.y + r.h,
    })),
  );
  return {
    x: Math.min(0, ...rectangles.map((r) => r.x)),
    y: Math.min(0, ...rectangles.map((r) => r.y)),
    right: Math.max(240, ...rectangles.map((r) => r.right)),
    bottom: Math.max(100, ...rectangles.map((r) => r.bottom)),
  };
};
wireAnchor = function (endpoint, toward) {
  const node = document.querySelector(
    `[data-node="${CSS.escape(endpoint.device)}"]`,
  );
  if (!node) return { x: 0, y: 0 };
  const port = node.querySelector(
      `[data-port="${CSS.escape(endpoint.port || "")}"]`,
    ),
    rect = (
      port && wirePrefs.showPorts !== false ? port : node
    ).getBoundingClientRect(),
    world = $("#wire-world").getBoundingClientRect();
  if ((!port || wirePrefs.showPorts === false) && toward) {
    const target = document.querySelector(
      `[data-node="${CSS.escape(toward.device)}"]`,
    );
    if (target) {
      const tr = target.getBoundingClientRect(),
        left = tr.left + tr.width / 2 < rect.left + rect.width / 2;
      return {
        x: ((left ? rect.left : rect.right) - world.left) / camera.z,
        y: (rect.top + rect.height * 0.65 - world.top) / camera.z,
      };
    }
  }
  return {
    x: (rect.left + rect.width / 2 - world.left) / camera.z,
    y: (rect.top + rect.height / 2 - world.top) / camera.z,
  };
};
wirePaint = function () {
  if (!wireGraph || !$("#wire-world")) return;
  // Las posiciones manuales permanecen dentro del contenedor de su rack.
  for (const n of wireGraph.nodes) {
    const region = physicalRegions.find(
      (r) =>
        r.id ===
        (physicalLevel === "outside"
          ? n.data.location?.cpd || ""
          : physicalRackOf(n)),
    );
    if (region && wirePositions[n.id]) {
      const p = wirePositions[n.id],
        s = physicalSize(n);
      p.x = Math.max(
        region.x + 25,
        Math.min(region.x + region.w - s.w - 25, p.x),
      );
      p.y = Math.max(
        region.y + 60,
        Math.min(region.y + region.h - s.h - 25, p.y),
      );
    }
  }
  physicalBase.paint();
  document.querySelectorAll(".physical-region").forEach((e) => e.remove());
  for (const region of physicalRegions) {
    const el = document.createElement("div");
    el.className = "physical-region";
    Object.assign(el.style, {
      left: region.x + "px",
      top: region.y + "px",
      width: region.w + "px",
      height: region.h + "px",
    });
    el.textContent =
      region.label +
      (physicalLevel === "inside"
        ? " · " + physicalRoomName(physicalCpdOf(region.id))
        : "");
    $("#wire-world").prepend(el);
  }
  const labels = [];
  $("#wire-lines").innerHTML = wireGraph.edges
    .filter((e) =>
      wireGraph.nodes.some((n) => n.id === e.a?.device || n.id === e.b?.device),
    )
    .map((e, i) => {
      const visible = (id) => wireGraph.nodes.some((n) => n.id === id);
      const first = visible(e.a?.device) ? e.a : e.b,
        second = first === e.a ? e.b : e.a;
      const a = wireAnchor(first, second),
        b =
          second && visible(second.device)
            ? wireAnchor(second, first)
            : { x: a.x + 240, y: a.y + 130 };
      const dx = b.x - a.x,
        dy = b.y - a.y,
        bend = Math.max(70, Math.abs(dx) * 0.28),
        parallel = ((i % 3) - 1) * 28;
      const path = `M${a.x} ${a.y} C${a.x + Math.sign(dx || 1) * bend} ${a.y + parallel},${b.x - Math.sign(dx || 1) * bend} ${b.y + parallel},${b.x} ${b.y}`;
      const bundle = e.wire.bundle || [e.wire.id],
        actual = state.records.find((r) => r.id === e.wire.id) || e.wire;
      const media = [
        ...new Set(
          bundle.map((id) =>
            wireName(
              state.records.find((r) => r.id === id)?.data.kind || "wire",
            ),
          ),
        ),
      ];
      const medium = media.join(" / ");
      const text =
        bundle.length > 1
          ? `${bundle.length} cables · ${medium}`
          : `${labelOf(actual)} · ${actual.id} · ${medium}`;
      const full = `${text} · ${first.device} ${first.port} ↔ ${second ? second.device + " " + second.port : "Sin conectar"}`;
      const caption =
        camera.z < 0.65
          ? bundle.length > 1
            ? bundle.length + " cables"
            : actual.id
          : text;
      const short = caption.length > 48 ? caption.slice(0, 45) + "…" : caption;
      const labelScale = 1 / Math.max(0.5, Math.min(1, camera.z));
      const width = Math.max(80, short.length * 6.8 + 18) * labelScale,
        height = 24 * labelScale;
      const midX = (a.x + b.x) / 2,
        midY = (a.y + b.y) / 2 + parallel * 0.75;
      let x = midX - width / 2,
        y = midY - height - 10;
      const obstacles = wireGraph.nodes.map((n) => {
        const p = wirePositions[n.id],
          s = physicalSize(n);
        return { x: p.x, y: p.y, w: s.w, h: s.h };
      });
      const collides = (x, y) =>
        [...labels, ...obstacles].some(
          (r) =>
            x < r.x + r.w + 8 &&
            x + width > r.x - 8 &&
            y < r.y + r.h + 8 &&
            y + height > r.y - 8,
        );
      for (let tries = 0; tries < 120 && collides(x, y); tries++) {
        const ring = Math.floor(tries / 8) + 1,
          angle = ((tries % 8) * Math.PI) / 4;
        x = midX - width / 2 + Math.cos(angle) * ring * 55;
        y = midY - height / 2 + Math.sin(angle) * ring * 40;
      }
      labels.push({ x, y, w: width, h: height });
      return `<g data-cable="${esc(e.wire.id)}" class="${selected === e.wire.id ? "highlight" : ""}"><title>${esc(full)}</title><path d="${path}"/><circle cx="${a.x}" cy="${a.y}" r="3"/><circle cx="${b.x}" cy="${b.y}" r="3"/>${wirePrefs.labels ? `<g class="physical-cable-label">${Math.hypot(x + width / 2 - midX, y + height / 2 - midY) > 40 ? `<line class="physical-label-leader" x1="${midX}" y1="${midY}" x2="${x + width / 2}" y2="${y + height / 2}"/>` : ""}<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="5"/><text style="font-size:${11 * labelScale}px" x="${x + 9 * labelScale}" y="${y + 16 * labelScale}">${esc(short)}</text></g>` : ""}</g>`;
    })
    .join("");
  physicalLabelBounds = labels;
  for (const label of document.querySelectorAll(
    "#wire-lines .physical-cable-label",
  )) {
    const group = label.parentElement;
    label.dataset.cable = group.dataset.cable;
    label.prepend(group.querySelector("title").cloneNode(true));
    $("#wire-lines").append(label);
  }
  $("#wire-lines").onclick = (e) => {
    const node = physicalNodeAt(e);
    if (node) {
      selected = node.dataset.node;
      clearTimeout(clickTimer);
      clickTimer = setTimeout(render, 260);
      return;
    }

    const el = e.target.closest("[data-cable]");
    if (!el) return;
    const edge = wireGraph.edges.find((x) => x.wire.id === el.dataset.cable);
    if (edge?.wire.bundle?.length > 1) {
      const section = document.createElement("div");
      for (const id of edge.wire.bundle) {
        const r = state.records.find((r) => r.id === id);
        section.append(
          wireAction(labelOf(r) + " · " + id, () => {
            $("#detail").close();
            fullDetails(r);
          }),
        );
      }
      showForm("Cables entre racks", [section]);
    } else {
      const r = state.records.find((r) => r.id === el.dataset.cable);
      if (r) fullDetails(r);
    }
  };
};
let rackMode = "rooms",
  rackCpd = "",
  rackChoice = "";
function rackMetric(r) {
  const used = new Set(r.occupants.map((o) => Number(o.unit)).filter(Boolean));
  return `${used.size} / ${r.units} U ocupadas · ${r.occupants.length} equipos`;
}
function rackRoomForm(room) {
  showForm(
    room ? "Editar CPD" : "Nuevo CPD",
    [
      field("Nombre", "name", room?.name),
      field("Descripción", "description", room?.description, "textarea"),
      field("Ubicación", "location", room?.location),
    ],
    async (values) => {
      await call(
        "rack_organization",
        state.organizationRevision,
        room ? "edit" : "create",
        { ...values, id: room?.id },
      );
    },
  );
}
function rackAssign(r) {
  showForm(
    "CPD de " + r.name,
    [
      field("Sala CPD", "id", r.location?.cpd || "", "text", [
        ["", "Sin CPD"],
        ...(state.cpds || []).map((c) => [c.id, c.name]),
      ]),
    ],
    (v) =>
      call("rack_organization", state.organizationRevision, "assign", {
        rack: r.id,
        id: v.id,
      }),
  );
}
function rackDeleteRoom(room) {
  showForm(
    "Eliminar CPD · " + room.name,
    [
      Object.assign(document.createElement("p"), {
        textContent:
          "Los armarios, sus equipos y cables se conservarán. Elige dónde dejar los armarios de esta sala.",
      }),
      field("Trasladar armarios a", "target", "", "text", [
        ["", "Sin CPD"],
        ...state.cpds
          .filter((c) => c.id !== room.id)
          .map((c) => [c.id, c.name]),
      ]),
    ],
    async (v) => {
      await call("rack_organization", state.organizationRevision, "delete", {
        id: room.id,
        target: v.target,
      });
      rackCpd = "";
    },
  );
}
function rackShowDetails(r) {
  const general = [
    Object.assign(document.createElement("p"), {
      textContent: r.name + " · " + r.id,
    }),
    Object.assign(document.createElement("p"), {
      textContent: r.description || "Sin descripción",
    }),
    Object.assign(document.createElement("p"), { textContent: rackMetric(r) }),
    wireAction("Cambiar CPD", () => {
      $("#detail").close();
      rackAssign(r);
    }),
  ];
  const items = document.createElement("div");
  for (const o of r.occupants)
    items.append(
      wireAction(`${o.name || o.id} · U${o.unit || "—"}`, () => {
        $("#detail").close();
        rackOccupantDetails(o);
      }),
    );
  const json = document.createElement("textarea");
  json.readOnly = true;
  json.rows = 16;
  json.value = JSON.stringify(r, null, 2);
  showForm("Rack · " + r.name, [
    wireTabs([
      ["Resumen", general],
      ["Equipos", [items]],
      [
        "JSON",
        [
          json,
          wireAction("Copiar JSON", async () => {
            try {
              await navigator.clipboard.writeText(json.value);
            } catch {
              json.select();
              document.execCommand("copy");
            }
          }),
        ],
      ],
    ]),
  ]);
}
render = function () {
  if (state.launcher !== "lanrack") {
    physicalBase.render();
    return;
  }
  document.body.classList.add("wire-app", "rack-app");
  const query = $("#search").value.toLocaleLowerCase().trim(),
    filter = $("#filter").value;
  if (filter !== rackCpd) rackCpd = filter;
  $("#title").textContent = "Salas CPD y armarios rack";
  $("#subtitle").textContent =
    "Organización física compartida con LANWIRE · equipos y conexiones conservados";
  $("#filter").innerHTML =
    '<option value="">Todos los CPD</option><option value="none">Sin CPD</option>' +
    (state.cpds || [])
      .map((c) => `<option value="${esc(c.id)}">${esc(c.name)}</option>`)
      .join("");
  $("#filter").value = rackCpd;
  const roomName = (id) => physicalRoomName(id);
  const rows = state.records.filter(
    (r) =>
      (!rackCpd ||
        (rackCpd === "none"
          ? !r.location?.cpd
          : r.location?.cpd === rackCpd)) &&
      (!query ||
        [r.name, r.id, r.description, roomName(r.location?.cpd)]
          .join(" ")
          .toLocaleLowerCase()
          .includes(query)),
  );
  selected = rows.some((r) => r.id === selected)
    ? selected
    : rows[0]?.id || null;
  const chosen = rows.find((r) => r.id === selected);
  $("#count").textContent =
    rows.length + " de " + state.records.length + " racks";
  $("#selection").textContent = chosen?.name || "Sin selección";
  $("#views").innerHTML = [
    ["rooms", "Vista de salas"],
    ["list", "Lista"],
    ["rack", "Detalle del rack"],
  ]
    .map(
      ([key, name]) =>
        `<button data-rack-mode="${key}" class="${rackMode === key ? "active" : ""}">${name}</button>`,
    )
    .join("");
  $("#tools").innerHTML =
    button("Actualizar", "refresh") +
    '<button id="rack-new-room" class="primary">Nuevo CPD</button>' +
    button("Abrir LANWIRE", "wire");
  $("#rack-new-room").onclick = () => rackRoomForm();
  $("#commands").innerHTML = chosen
    ? '<button id="rack-data">Ver datos</button><button id="rack-assign">Cambiar CPD</button>'
    : "";
  if (chosen) {
    $("#rack-data").onclick = () => rackShowDetails(chosen);
    $("#rack-assign").onclick = () => rackAssign(chosen);
  }
  if (rackMode === "list") {
    $("#canvas").innerHTML = table(
      ["ARMARIO", "ID", "CPD", "CAPACIDAD / OCUPACIÓN"],
      rows,
      (r) => [r.name, r.id, roomName(r.location?.cpd), rackMetric(r)],
    );
  } else if (rackMode === "rack" && chosen) {
    const occupancy = new Map(chosen.occupants.map((o) => [Number(o.unit), o]));
    $("#canvas").innerHTML =
      `<div class="rack-detail-layout"><section class="panel"><button id="rack-back">← Volver a la sala</button><h2>${esc(chosen.name)}</h2><p>${esc(roomName(chosen.location?.cpd))}</p><p>${esc(rackMetric(chosen))}</p><p>${esc(chosen.description)}</p></section><section class="rack-elevation">${Array.from(
        { length: chosen.units },
        (_, i) => chosen.units - i,
      )
        .map((u) => {
          const o = occupancy.get(u);
          return `<button ${o ? `data-rack-occupant="${esc(o.id)}"` : "disabled"} class="${o ? "occupied" : ""}"><span>${u} U</span> ${esc(o?.name || o?.id || "Libre")}</button>`;
        })
        .join("")}</section></div>`;
    $("#rack-back").onclick = () => {
      rackMode = "rooms";
      $("#filter").value = chosen.location?.cpd || "none";
      render();
    };
    document
      .querySelectorAll("[data-rack-occupant]")
      .forEach(
        (b) =>
          (b.onclick = () =>
            rackOccupantDetails(
              chosen.occupants.find((o) => o.id === b.dataset.rackOccupant),
            )),
      );
  } else {
    const rooms = (state.cpds || [])
      .filter((c) => !rackCpd || c.id === rackCpd)
      .filter(
        (c) =>
          !query ||
          c.name.toLocaleLowerCase().includes(query) ||
          rows.some((r) => r.location?.cpd === c.id),
      );
    const cards = [
      ...rooms,
      {
        id: "",
        name: "Sin CPD",
        description: "Armarios pendientes de asignación",
      },
    ].filter(
      (c) => !rackCpd || (rackCpd === "none" ? !c.id : c.id === rackCpd),
    );
    $("#canvas").innerHTML =
      '<div class="cpd-rooms">' +
      cards
        .map((c) => {
          const racks = rows.filter((r) => (r.location?.cpd || "") === c.id);
          if (!c.id && !racks.length) return "";
          return `<section class="panel cpd-room"><div class="row"><h2>${esc(c.name)}</h2>${c.id ? `<button data-cpd-edit="${esc(c.id)}">Editar CPD</button><button data-cpd-delete="${esc(c.id)}">Eliminar CPD</button>` : ""}</div><p>${esc(c.description || "")}</p><p>${esc(c.location || "")} · ${racks.length} armarios · ${racks.reduce((s, r) => s + r.units, 0)} U totales</p><div class="cpd-racks">${racks.map((r) => `<button data-rack-open="${esc(r.id)}" class="rack-cabinet"><strong>${esc(r.name)}</strong><small>${esc(r.id)} · ${esc(rackMetric(r))}</small><span aria-hidden="true">▤<br>▤<br>▤</span></button>`).join("") || '<p class="muted">CPD vacío. Usa «Cambiar CPD» en un rack para asignarlo.</p>'}</div></section>`;
        })
        .join("") +
      "</div>";
    document.querySelectorAll("[data-rack-open]").forEach(
      (b) =>
        (b.onclick = () => {
          selected = b.dataset.rackOpen;
          rackMode = "rack";
          render();
        }),
    );
    document
      .querySelectorAll("[data-cpd-edit]")
      .forEach(
        (b) =>
          (b.onclick = () =>
            rackRoomForm(state.cpds.find((c) => c.id === b.dataset.cpdEdit))),
      );
    document
      .querySelectorAll("[data-cpd-delete]")
      .forEach(
        (b) =>
          (b.onclick = () =>
            rackDeleteRoom(
              state.cpds.find((c) => c.id === b.dataset.cpdDelete),
            )),
      );
  }
  document.querySelectorAll("[data-rack-mode]").forEach(
    (b) =>
      (b.onclick = () => {
        rackMode = b.dataset.rackMode;
        render();
      }),
  );
};
fullDetails = function (r) {
  if (state.launcher === "lanrack" && r?.occupants) return rackShowDetails(r);
  return physicalBase.fullDetails(r);
};
refresh = async function () {
  const previous = $("#filter").value;
  await physicalBase.refresh();
  if (state.launcher === "lanrack") {
    $("#filter").value = previous;
    rackCpd = previous;
    render();
  }
};

wireCenterFromDetails = async function (r) {
  wireSavePositions();
  physicalLevel = r.data.type === "rack" ? "outside" : "inside";
  physicalRack =
    r.data.type === "rack"
      ? r.id
      : r.data.type === "wire"
        ? ""
        : physicalRackOf(r);
  physicalCpd = "";
  wirePositions = {};
  return physicalBase.center(r);
};

const physicalClearFilters = wireClearFilters;
wireClearFilters = function () {
  physicalRack = "";
  physicalCpd = "";
  wirePositions = {};
  physicalClearFilters();
};
function rackOccupantDetails(r) {
  const data = r.data || {};
  const summary = document.createElement("dl");
  for (const [name, value] of [
    ["Nombre", r.name || r.id],
    ["Identificador", r.id],
    ["Tipo", wireName(r.type)],
    ["Unidad", r.unit || "Sin asignar"],
    ["Descripción", r.description || "—"],
  ]) {
    const dt = document.createElement("dt"),
      dd = document.createElement("dd");
    dt.textContent = name;
    dd.textContent = String(value);
    summary.append(dt, dd);
  }
  const ports = document.createElement("div");
  for (const [id, p] of Object.entries(data.ports || {})) {
    const line = document.createElement("p");
    line.textContent =
      id + " · " + wireName(p.kind) + " · " + (p.connector || "");
    ports.append(line);
  }
  if (!ports.childNodes.length) ports.textContent = "Sin puertos registrados";
  const json = document.createElement("textarea");
  json.readOnly = true;
  json.rows = 16;
  json.value = JSON.stringify(r, null, 2);
  showForm("Equipo · " + (r.name || r.id), [
    wireTabs([
      ["Resumen", [summary]],
      ["Puertos", [ports]],
      ["JSON", [json]],
    ]),
  ]);
}

function physicalNodeAt(event) {
  return (
    [...document.querySelectorAll("[data-node]")].find((node) => {
      const r = node.getBoundingClientRect();
      return (
        event.clientX >= r.left &&
        event.clientX <= r.right &&
        event.clientY >= r.top &&
        event.clientY <= r.bottom
      );
    }) || null
  );
}
