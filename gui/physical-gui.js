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
wireNames["rack.summary"] = window.LanctlI18n.t("LANCTL.UI.VIEW.RACK_CABINET");
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
  if (r.data?.type === "external.fiber-entry") return "";
  return ["rack", "rack.summary"].includes(r.data?.type)
    ? r.id
    : r.placement?.rack || r.data?.location?.rack || "";
}
function physicalGroupOf(r) {
  if (r.data.type === "external.fiber-entry") return "@external:" + r.id;
  return physicalLevel === "outside" ? r.data.location?.cpd || "" : physicalRegionOf(r);
}
function physicalRegionOf(r) {
  const rack = physicalRackOf(r);
  if (r.placement?.kind === "environment") return rack + "::environment";
  if (r.placement?.kind === "hosted") return state.launcher === "lanwire" ? rack : rack + "::tray:" + r.placement.tray;
  if (r.placement?.needsReview) return "::review";
  return rack;
}
function physicalCpdOf(rack) {
  return state.records.find((r) => r.id === rack)?.data?.location?.cpd || "";
}
function physicalRoomName(id) {
  return state.cpds?.find((c) => c.id === id)?.name || window.LanctlI18n.t("LANCTL.UI.VIEW.NO_DATA_CENTER");
}
function physicalSize(n) {
  if (n.physicalSize) return n.physicalSize;
  if (n.data.type === "external.fiber-entry") return {w:160, h:150};
  const count = Object.keys(n.data.ports || {}).length;
  if (["device.outlet", "outlet"].includes(n.data.type) && count <= 2)
    return { w: 120, h: 64 };
  const cols = count > 24 ? 12 : count > 8 ? 8 : Math.max(1, count);
  return {
    w: count ? Math.max(240, cols * 43 + 28) : 240,
    h: 90 + Math.ceil(count / cols) * 29,
  };
}
// Deterministic layered layout: bounded sweeps, real card sizes, no storage edits.
function physicalPack(nodes, edges) {
  const byId = new Map(nodes.map(n => [n.id,n]));
  const sizes = new Map(nodes.map(n => [n.id,physicalSize(n)]));
  const adjacency = new Map(nodes.map(n => [n.id,new Set()]));
  for (const edge of edges) {
    const a=edge.a?.device,b=edge.b?.device;
    if (a!==b && adjacency.has(a) && adjacency.has(b)) {
      adjacency.get(a).add(b); adjacency.get(b).add(a);
    }
  }
  const priority = id => {
    const type=byId.get(id).data?.type || "";
    return type === "external.fiber-entry" ? 0 : /router|gateway/.test(type) ? 1 : 2;
  };
  const roots=[...byId.keys()].sort((a,b)=>priority(a)-priority(b) || adjacency.get(b).size-adjacency.get(a).size || a.localeCompare(b));
  const seen=new Set(), result=new Map();
  let offsetX=0,offsetY=0,rowHeight=0;
  for (const root of roots) {
    if (seen.has(root)) continue;
    const queue=[root], depth=new Map([[root,0]]), layers=[];
    seen.add(root);
    for (let cursor=0;cursor<queue.length;cursor++) {
      const id=queue[cursor], level=depth.get(id);
      (layers[level] ||= []).push(id);
      for (const next of [...adjacency.get(id)].sort()) if (!seen.has(next)) {
        seen.add(next); depth.set(next,level+1); queue.push(next);
      }
    }
    layers.forEach(layer=>layer.sort());
    // Barycentric ordering reduces crossings between adjacent levels, including cycles.
    const rank=new Map();
    const updateRank=layer=>layer.forEach((id,index)=>rank.set(id,(index+.5)/layer.length));
    layers.forEach(updateRank);
    for (let sweep=0;sweep<8;sweep++) {
      const indexes=Array.from({length:layers.length},(_,i)=>i);
      if (sweep%2) indexes.reverse();
      for (const level of indexes) {
        const layer=layers[level], centers=new Map();
        for (const id of layer) {
          let sum=0,count=0;
          for (const next of [...adjacency.get(id)].sort()) {
            if (depth.get(next) === level + (sweep%2 ? 1 : -1)) {sum+=rank.get(next);count++;}
          }
          centers.set(id,count ? sum/count : rank.get(id));
        }
        layer.sort((a,b)=>centers.get(a)-centers.get(b) || a.localeCompare(b));
        updateRank(layer);
      }
    }
    const widths=layers.map(layer=>layer.reduce((sum,id)=>sum+sizes.get(id).w,0)+Math.max(0,layer.length-1)*90);
    const width=Math.max(...widths), local=new Map();
    let height=0;
    for (const [level,layer] of layers.entries()) {
      let x=(width-widths[level])/2;
      const rowHeight=Math.max(...layer.map(id=>sizes.get(id).h));
      for (const id of layer) {
        local.set(id,{x,y:height}); x+=sizes.get(id).w+90;
      }
      height+=rowHeight+120;
    }
    height-=120;
    if (offsetX && offsetX+width>1800) {offsetX=0;offsetY+=rowHeight+150;rowHeight=0;}
    for (const [id,point] of local) result.set(id,{x:offsetX+point.x,y:offsetY+point.y});
    offsetX+=width+150;rowHeight=Math.max(rowHeight,height);
  }
  return result;
}
// Pure directional collision propagation; the selected region never moves its own nodes.
function physicalResizeRegions(regions, positions, members, selected, side, delta, sizes) {
  const boxes = structuredClone(regions), points = structuredClone(positions);
  const target = boxes.find(r=>r.id===selected), original = regions.find(r=>r.id===selected);
  if (!target || !["e","w","n","s"].includes(side) || !Number.isFinite(delta)) return {regions:boxes,positions:points};
  const inside = Object.keys(members).filter(id=>members[id]===selected && points[id]);
  const left = Math.min(original.x+original.w-160,...inside.map(id=>points[id].x-25));
  const top = Math.min(original.y+original.h-110,...inside.map(id=>points[id].y-60));
  const right = Math.max(original.x+160,...inside.map(id=>points[id].x+sizes[id].w+25));
  const bottom = Math.max(original.y+110,...inside.map(id=>points[id].y+sizes[id].h+25));
  if(side==="e") target.w=Math.max(right-target.x,original.w+delta);
  if(side==="s") target.h=Math.max(bottom-target.y,original.h+delta);
  if(side==="w") {target.x=Math.min(left,original.x+delta);target.w=original.x+original.w-target.x;}
  if(side==="n") {target.y=Math.min(top,original.y+delta);target.h=original.y+original.h-target.y;}
  const axis=side==="e"||side==="w" ? "x" : "y", extent=axis==="x" ? "w" : "h", other=axis==="x" ? "y" : "x", otherExtent=axis==="x" ? "h" : "w", direction=side==="e"||side==="s" ? 1 : -1;
  const growing=direction>0 ? target[extent]>original[extent] : target[axis]<original[axis];
  if(!growing) return {regions:boxes,positions:points};
  const initial=new Map(regions.map(r=>[r.id,r]));
  const ordered=boxes.slice().sort((a,b)=>direction*(initial.get(a.id)[axis]-initial.get(b.id)[axis]) || a.id.localeCompare(b.id));
  const moved=new Set([selected]), gap=40;
  for(let i=0;i<ordered.length;i++) {
    const source=ordered[i]; if(!moved.has(source.id)) continue;
    for(let j=i+1;j<ordered.length;j++) {
      const next=ordered[j]; if(next.id===selected) continue;
      const overlapsBand=source[other]<next[other]+next[otherExtent] && next[other]<source[other]+source[otherExtent];
      if(!overlapsBand) continue;
      const shift=direction>0 ? source[axis]+source[extent]+gap-next[axis] : source[axis]-gap-next[axis]-next[extent];
      if(direction*shift<=0) continue;
      next[axis]+=shift; moved.add(next.id);
    }
  }
  const boxIndex=new Map(boxes.map(r=>[r.id,r]));
  for(const [id,point] of Object.entries(points)) {
    const region=boxIndex.get(members[id]), start=initial.get(members[id]);
    if(region && start && region.id!==selected) {point.x+=region.x-start.x;point.y+=region.y-start.y;}
  }
  return {regions:boxes,positions:points};
}
wireLayout = function (nodes) {
  const edges = wireEdges();
  physicalRegions = [];
  const groupOfNode = physicalGroupOf;
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
          ? state.cpds?.find((c) => c.id === id)?.name || window.LanctlI18n.t("LANCTL.UI.VIEW.NO_DATA_CENTER")
          : id
            ? (id.includes("::environment") ? window.LanctlI18n.t("LANCTL.UI.FRAGMENT.ENVIRONMENT_FOR") + id.split("::")[0] : id.includes("::tray:") ? window.LanctlI18n.t("LANCTL.UI.FRAGMENT.TRAY") + id.split("::tray:")[1] : id === "::review" ? window.LanctlI18n.t("LANCTL.UI.VIEW.LOCATIONS_PENDING_REVIEW") : labelOf(state.records.find((r) => r.id === id) || { id }))
            : window.LanctlI18n.t("LANCTL.UI.VIEW.EQUIPMENT_WITHOUT_A_RACK"),
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
    const automatic = places.get(region.id), frame=wireRegionFrames[region.id];
    const p = frame || automatic;
    physicalRegions.push({
      id: region.id,
      x: p.x,
      y: p.y,
      w: frame?.w || region.physicalSize.w,
      h: frame?.h || region.physicalSize.h,
      label: region.label,
      external: region.id.startsWith("@external:"),
    });
    for (const n of region.items) {
      const point = region.local.get(n.id);
      result.set(n.id, { x: p.x + 40 + point.x, y: p.y + 65 + point.y });
    }
  }
  return result;
};
function physicalSwitchLevel(level, rack = "", cpd = physicalCpd) {
  const key = physicalLevel + ":" + physicalRack + ":" + physicalCpd;
  physicalViews.set(key, {
    positions: structuredClone(wirePositions),
    camera: { ...camera },
    regions: structuredClone(wireRegionFrames),
    focus: wireFocus,
  });
  wireSavePositions();
  physicalLevel = level;
  physicalRack = rack;
  physicalCpd = cpd;
  wireFocus = null;
  wireHidden.clear();
  const saved = physicalViews.get(level + ":" + rack + ":" + physicalCpd);
  if (!saved) wireLoadPositions();
  wirePositions = saved?.positions || wirePositions;
  wireRegionFrames = saved?.regions || wireRegionFrames;
  camera = saved?.camera || camera;
  wireFocus = saved?.focus || null;
  render();
  if (!saved && !state.diagramLayouts?.views?.[wireDiagramView()] && !wireDiagramUnsaved.has(wireDiagramKey())) wireFit();
}
wireRenderTopology = function (rows) {
  if (wireDiagramScope !== wireDiagramKey()) wireLoadPositions();
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
    wireLoadPositions();
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
    const context = new Map(rows.filter(r => r.data.type !== "wire" && r.data.type !== "rack" && !["inside", "hosted"].includes(r.placement?.kind) && (!effectiveRack || (effectiveRack === "none" ? !physicalRackOf(r) : physicalRackOf(r) === effectiveRack))).map(r => [r.id, r]));
    const visibleEdges = [];
    for (const e of physicalOriginalEdges) {
      const mapEnd = (end) => {
        if (!end) return null;
        const record = original.find((r) => r.id === end.device);
        const rack = record && !["environment", "independent", "review"].includes(record.placement?.kind) && physicalRackOf(record);
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
              !physicalRackOf(original.find((r) => r.id === end.device) || {})),
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
                ports: r.data.type === "external.fiber-entry" ? r.data.ports : {},
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
  controls.innerHTML = `<button data-level="inside" class="${physicalLevel === "inside" ? "active" : ""}">Interior de racks</button><button data-level="outside" class="${physicalLevel === "outside" ? "active" : ""}">Vista general de racks</button><label>CPD <select id="physical-cpd"><option value="" data-i18n="LANCTL.UI.HTML.ALL_DATA_CENTERS">Todos los CPD</option><option value="none" data-i18n="LANCTL.UI.VIEW.NO_DATA_CENTER">Sin CPD</option>${(state.cpds || []).map((c) => `<option value="${esc(c.id)}">${esc(c.name)}</option>`).join("")}</select></label><label>Rack <select id="physical-rack"><option value="" data-i18n="LANCTL.UI.HTML.ALL_RACKS">Todos los racks</option><option value="none" data-i18n="LANCTL.UI.TEXT.NO_RACK">Sin rack</option>${state.records
    .filter((r) => r.data.type === "rack")
    .map((r) => `<option value="${esc(r.id)}">${esc(labelOf(r))}</option>`)
    .join(
      "",
    )}</select></label><label><input id="physical-bundles" type="checkbox" ${physicalBundles ? "checked" : ""}> Agrupar enlaces</label>`;
  toolbar.before(controls);
  const labels = wireAction("", () => {
    wirePrefs.cableLabels = !(wirePrefs.cableLabels ?? wirePrefs.labels);
    wireStore();
    updateLabels();
    wirePaint();
  });
  function updateLabels() {
    const visible = wirePrefs.cableLabels ?? wirePrefs.labels;
    labels.textContent = visible ? window.LanctlI18n.t("LANCTL.UI.TEXT.HIDE_CABLE_NAMES") : window.LanctlI18n.t("LANCTL.UI.TEXT.SHOW_CABLE_NAMES");
    labels.setAttribute("aria-pressed", String(Boolean(visible)));
  }
  labels.id = "wire-cable-labels";
  updateLabels();
  toolbar.append(labels);
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
    physicalSwitchLevel(physicalLevel, "", e.target.value);
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
    if (r) fullDetails(r);
  };
  for (const n of wireGraph.nodes) {
    const el = document.querySelector(`[data-node="${CSS.escape(n.id)}"]`);
    el.style.width = physicalSize(n).w + "px";
    el.style.minHeight = physicalSize(n).h + "px";
    const compact = ["device.outlet", "outlet"].includes(n.data.type) && Object.keys(n.data.ports || {}).length <= 2;
    el.classList.toggle("physical-outlet", compact);
    if (compact) el.title = `${labelOf(n)} · ${n.id}`;
    const ports = el.querySelector(".wire-ports");
    if (ports)
      ports.style.gridTemplateColumns = `repeat(${compact ? 2 : Object.keys(n.data.ports || {}).length > 24 ? 12 : 8},minmax(0,1fr))`;
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
  // Expand visual containers around saved/manual coordinates; never clamp them away.
  for (const n of wireGraph.nodes) {
    const region = physicalRegions.find(r => r.id === physicalGroupOf(n));
    const point = wirePositions[n.id];
    if (region?.external && point) {
      Object.assign(region,{...point,...physicalSize(n)});
    } else if (region && point) {
      const size = physicalSize(n), right = Math.max(region.x+region.w,point.x+size.w+25), bottom = Math.max(region.y+region.h,point.y+size.h+25);
      region.x=Math.min(region.x,point.x-25);region.y=Math.min(region.y,point.y-60);
      region.w=right-region.x;region.h=bottom-region.y;
    }
  }
  // Older saved layouts may place the provider within a rack's environment.
  // Keep that boundary visibly external without changing inventory location data.
  const spaces=physicalRegions.filter(r=>!r.external);
  for (const region of physicalRegions.filter(r=>r.external)) {
    if (spaces.some(r=>region.x<r.x+r.w && r.x<region.x+region.w && region.y<r.y+r.h && r.y<region.y+region.h)) {
      region.x=Math.min(...spaces.map(r=>r.x))-region.w-60;
      const node=wireGraph.nodes.find(n=>physicalGroupOf(n)===region.id);
      if(node) wirePositions[node.id]={x:region.x,y:region.y};
    }
  }
  physicalBase.paint();
  document.querySelectorAll(".physical-region").forEach((e) => e.remove());
  for (const region of physicalRegions) {
    if (region.external) continue;
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
        ? " · " + physicalRoomName(physicalCpdOf(region.id.split("::")[0]))
        : "");
    for (const side of ["e","s","w","n"]) {
      const grip=document.createElement("button");grip.type="button";
      grip.className="physical-region-handle side-"+side;
      grip.dataset.regionId=region.id;grip.dataset.resizeSide=side;
      const directionKey={e:"LANCTL.DIAGRAM.DIRECTION.E",w:"LANCTL.DIAGRAM.DIRECTION.W",n:"LANCTL.DIAGRAM.DIRECTION.N",s:"LANCTL.DIAGRAM.DIRECTION.S"}[side];
      grip.setAttribute("aria-label",window.LanctlI18n.t("LANCTL.DIAGRAM.RESIZE",{region:region.label,direction:window.LanctlI18n.t(directionKey)}));
      grip.title=grip.getAttribute("aria-label");
      grip.style.setProperty("--grip",14/camera.z+"px");
      grip.onpointerdown=event=>physicalStartRegionResize(event,region.id,side);
      grip.onkeydown=event=>physicalKeyboardRegionResize(event,region.id,side);
      el.append(grip);
    }
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
          ?  window.LanctlI18n.t("LANCTL.UI.WEB.CABLE_BUNDLE",{value0:(bundle.length),value1:(medium)})
          : `${labelOf(actual)} · ${actual.id} · ${medium}`;
      const full = `${text} · ${first.device} ${first.port} ↔ ${second ? second.device + " " + second.port : window.LanctlI18n.html("LANCTL.UI.TEXT.NOT_CONNECTED")}`;
      const caption =
        camera.z < 0.65
          ? bundle.length > 1
            ? bundle.length + window.LanctlI18n.t("LANCTL.UI.FRAGMENT.CABLES")
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
      return `<g data-cable="${esc(e.wire.id)}" class="${selected === e.wire.id ? "highlight" : ""}"><title>${esc(full)}</title><path d="${path}"/><circle cx="${a.x}" cy="${a.y}" r="3"/><circle cx="${b.x}" cy="${b.y}" r="3"/>${(wirePrefs.cableLabels ?? wirePrefs.labels) ? `<g class="physical-cable-label">${Math.hypot(x + width / 2 - midX, y + height / 2 - midY) > 40 ? `<line class="physical-label-leader" x1="${midX}" y1="${midY}" x2="${x + width / 2}" y2="${y + height / 2}"/>` : ""}<rect x="${x}" y="${y}" width="${width}" height="${height}" rx="5"/><text style="font-size:${11 * labelScale}px" x="${x + 9 * labelScale}" y="${y + 16 * labelScale}">${esc(short)}</text></g>` : ""}</g>`;
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
      showForm(window.LanctlI18n.t("LANCTL.UI.VIEW.CABLES_BETWEEN_RACKS"), [section]);
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
  const used = new Set(
    r.occupants.flatMap((o) =>
      o.unit
        ? Array.from({ length: o.span || 1 }, (_, i) => Number(o.unit) + i)
        : [],
    ),
  );
  return  window.LanctlI18n.t("LANCTL.UI.WEB.RACK_OCCUPANCY",{value0:(used.size),value1:(r.units),value2:(r.occupants.length)});
}
function rackRoomForm(room) {
  showForm(
    room ? window.LanctlI18n.t("LANCTL.UI.VIEW.EDIT_DATA_CENTER") : window.LanctlI18n.t("LANCTL.UI.VIEW.NEW_DATA_CENTER"),
    [
      field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.NAME"), "name", room?.name),
      field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.DESCRIPTION"), "description", room?.description, "textarea"),
      field(window.LanctlI18n.t("LANCTL.UI.TEXT.LOCATION"), "location", room?.location),
    ],
    async (values) => {
      await call(
        state.launcher === "lanwire" ? "wire_organization" : "rack_organization",
        state.organizationRevision,
        room ? "edit" : "create",
        { ...values, id: room?.id },
      );
    },
  );
}
function rackAssign(r) {
  showForm(
    window.LanctlI18n.t("LANCTL.UI.FRAGMENT.DATA_CENTER_FOR") + r.name,
    [
      field(window.LanctlI18n.t("LANCTL.UI.VIEW.DATA_CENTER_ROOM"), "id", r.location?.cpd || "", "text", [
        ["", window.LanctlI18n.t("LANCTL.UI.VIEW.NO_DATA_CENTER")],
        ...(state.cpds || []).map((c) => [c.id, c.name]),
      ]),
    ],
    (v) =>
      call(state.launcher === "lanwire" ? "wire_organization" : "rack_organization", state.organizationRevision, "assign", {
        rack: r.id,
        id: v.id,
      }),
  );
}
function rackDeleteRoom(room) {
  showForm(
    window.LanctlI18n.t("LANCTL.UI.FRAGMENT.DELETE_DATA_CENTER") + room.name,
    [
      Object.assign(document.createElement("p"), {
        textContent:
          window.LanctlI18n.t("LANCTL.UI.VIEW.CABINETS_EQUIPMENT_AND_CABLES_WILL_BE_PRESERVED_CHOOSE_WHERE_TO_PLACE_THIS_ROOM_S_CABINETS"),
      }),
      field(window.LanctlI18n.t("LANCTL.UI.VIEW.MOVE_CABINETS_TO"), "target", "", "text", [
        ["", window.LanctlI18n.t("LANCTL.UI.VIEW.NO_DATA_CENTER")],
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
      textContent: r.description || window.LanctlI18n.t("LANCTL.UI.VIEW.NO_DESCRIPTION"),
    }),
    Object.assign(document.createElement("p"), { textContent: rackMetric(r) }),
    wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.CHANGE_DATA_CENTER"), () => {
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
  showForm(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.RACK") + r.name, [
    wireTabs([
      [window.LanctlI18n.t("LANCTL.UI.TEXT.SUMMARY"), general],
      [window.LanctlI18n.t("LANCTL.UI.TEXT.EQUIPMENT"), [items]],
      [
        "JSON",
        [
          json,
          wireAction(window.LanctlI18n.t("LANCTL.UI.TEXT.COPY_JSON"), async () => {
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
  window.LanctlI18n.bindText($("#title"),"LANCTL.UI.VIEW.DATA_CENTER_ROOMS_AND_RACK_CABINETS");
  window.LanctlI18n.bindText($("#subtitle"),"LANCTL.UI.VIEW.PHYSICAL_ORGANIZATION_SHARED_WITH_LANWIRE_EQUIPMENT_AND_CONNECTIONS_PRESERVED");
  $("#filter").innerHTML =
    "<option value=\"\" data-i18n=\"LANCTL.UI.HTML.ALL_DATA_CENTERS\">Todos los CPD</option><option value=\"none\" data-i18n=\"LANCTL.UI.VIEW.NO_DATA_CENTER\">Sin CPD</option>" +
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
    rows.length + window.LanctlI18n.t("LANCTL.UI.FRAGMENT.OF") + state.records.length + window.LanctlI18n.t("LANCTL.UI.FRAGMENT.RACKS");
  $("#selection").textContent = chosen?.name || window.LanctlI18n.t("LANCTL.UI.TEXT.NO_SELECTION");
  $("#views").innerHTML = [
    ["rooms", window.LanctlI18n.t("LANCTL.UI.VIEW.ROOM_VIEW")],
    ["list", window.LanctlI18n.t("LANCTL.UI.TEXT.LIST")],
    ["rack", window.LanctlI18n.t("LANCTL.UI.VIEW.RACK_DETAILS")],
  ]
    .map(
      ([key, name]) =>
        `<button data-rack-mode="${key}" class="${rackMode === key ? "active" : ""}">${name}</button>`,
    )
    .join("");
  $("#tools").innerHTML =
    button(window.LanctlI18n.t("LANCTL.UI.TEXT.REFRESH"), "refresh") +
    "<button id=\"rack-new-room\" class=\"primary\"><span data-i18n=\"LANCTL.UI.VIEW.NEW_DATA_CENTER\">Nuevo CPD</span></button>";
  $("#rack-new-room").onclick = () => rackRoomForm();
  $("#commands").innerHTML = chosen
    ? "<button id=\"rack-data\"><span data-i18n=\"LANCTL.UI.HTML.VIEW_DATA\">Ver datos</span></button><button id=\"rack-assign\"><span data-i18n=\"LANCTL.UI.VIEW.CHANGE_DATA_CENTER\">Cambiar CPD</span></button>"
    : "";
  if (chosen) {
    $("#rack-data").onclick = () => rackShowDetails(chosen);
    $("#rack-assign").onclick = () => rackAssign(chosen);
  }
  if (rackMode === "list") {
    $("#canvas").innerHTML = table(
      [window.LanctlI18n.t("LANCTL.UI.FRAGMENT.CABINET"), "ID", "CPD", "CAPACIDAD / OCUPACIÓN"],
      rows,
      (r) => [r.name, r.id, roomName(r.location?.cpd), rackMetric(r)],
    );
  } else if (rackMode === "rack" && chosen) {
    const occupancy = new Map(
      chosen.occupants.flatMap((o) =>
        o.unit
          ? Array.from({ length: o.span || 1 }, (_, i) => [
              Number(o.unit) + i,
              o,
            ])
          : [],
      ),
    );
    $("#canvas").innerHTML =
      `<div class="rack-detail-layout"><section class="rack-detail-header"><nav class="row" aria-label="Vista del rack" data-i18n-aria-label="LANCTL.UI.HTML.RACK_VIEW"><button id="rack-back"><span data-i18n="LANCTL.UI.TEXT.BACK_TO_ROOM">Volver a la sala</span></button></nav><div class="rack-summary"><h2>${esc(chosen.name)}</h2><p>${esc(roomName(chosen.location?.cpd))} · ${esc(rackMetric(chosen))}</p></div></section><section class="rack-elevation" aria-label="Unidades del rack" data-i18n-aria-label="LANCTL.UI.HTML.RACK_UNITS">${Array.from(
        { length: chosen.units },
        (_, i) => chosen.units - i,
      )
        .map((u) => {
          const o = occupancy.get(u);
          return `<button data-rack-unit="${u}" data-rack-id="${esc(chosen.id)}" ${o ? `data-rack-occupant="${esc(o.id)}"` : ""} class="${o ? "occupied" : ""}"><span>${u} U</span> ${esc(o?.name || o?.id || window.LanctlI18n.t("LANCTL.UI.HTML.FREE"))}</button>`;
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
        name: window.LanctlI18n.t("LANCTL.UI.VIEW.NO_DATA_CENTER"),
        description: window.LanctlI18n.t("LANCTL.UI.VIEW.CABINETS_PENDING_ASSIGNMENT"),
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
          return `<section class="panel cpd-room"><div class="row"><h2>${esc(c.name)}</h2>${c.id ? `<button data-cpd-edit="${esc(c.id)}">Editar CPD</button><button data-cpd-delete="${esc(c.id)}">Eliminar CPD</button>` : ""}</div><p>${esc(c.description || "")}</p><p>${esc(c.location || "")} · ${racks.length} armarios · ${racks.reduce((s, r) => s + r.units, 0)} U totales</p><div class="cpd-racks">${racks.map((r) => `<button data-rack-open="${esc(r.id)}" class="rack-cabinet"><strong>${esc(r.name)}</strong><small>${esc(r.id)} · ${esc(rackMetric(r))}</small><span aria-hidden="true">▤<br>▤<br>▤</span></button>`).join("") || "<p class=\"muted\"><span data-i18n=\"LANCTL.UI.HTML.EMPTY_DATA_CENTER_USE_CHANGE_DATA_CENTER_ON_A_RACK_TO_ASSIGN_IT\">CPD vacío. Usa «Cambiar CPD» en un rack para asignarlo.</span></p>"}</div></section>`;
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
    [window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.NAME"), r.name || r.id],
    [window.LanctlI18n.t("LANCTL.UI.HTML.IDENTIFIER"), r.id],
    [window.LanctlI18n.t("LANCTL.UI.TEXT.TYPE"), wireName(r.type)],
    [window.LanctlI18n.t("LANCTL.UI.WORD.UNIT"), r.unit || window.LanctlI18n.t("LANCTL.UI.VIEW.UNASSIGNED")],
    [window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.DESCRIPTION"), r.description || "—"],
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
  if (!ports.childNodes.length) window.LanctlI18n.bindText(ports,"LANCTL.UI.VIEW.NO_PORTS_RECORDED");
  const json = document.createElement("textarea");
  json.readOnly = true;
  json.rows = 16;
  json.value = JSON.stringify(r, null, 2);
  showForm(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.DEVICE_05DBAF67") + (r.name || r.id), [
    wireTabs([
      [window.LanctlI18n.t("LANCTL.UI.TEXT.SUMMARY"), [summary]],
      [window.LanctlI18n.t("LANCTL.UI.TEXT.PORTS"), [ports]],
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

let physicalRegionResizing=false;
function physicalResizeSnapshot() {
  return {regions:structuredClone(physicalRegions), positions:structuredClone(wirePositions), frames:structuredClone(wireRegionFrames),
    members:Object.fromEntries(wireGraph.nodes.map(n=>[n.id,physicalGroupOf(n)])),
    sizes:Object.fromEntries(wireGraph.nodes.map(n=>[n.id,physicalSize(n)]))};
}
function physicalApplyRegionResize(snapshot,id,side,delta) {
  const next=physicalResizeRegions(snapshot.regions,snapshot.positions,snapshot.members,id,side,delta,snapshot.sizes);
  physicalRegions=next.regions;wirePositions=next.positions;
  wireRegionFrames=Object.fromEntries(physicalRegions.map(r=>[r.id,{x:r.x,y:r.y,w:r.w,h:r.h}]));
  wirePaint();
}
function physicalKeyboardRegionResize(event,id,side) {
  const horizontal=side==="e"||side==="w";
  const direction=horizontal ? {ArrowLeft:-1,ArrowRight:1}[event.key] : {ArrowUp:-1,ArrowDown:1}[event.key];
  if(!direction) return;
  event.preventDefault();event.stopPropagation();
  physicalApplyRegionResize(physicalResizeSnapshot(),id,side,direction*(event.shiftKey?80:20));
  wireSavePositions();
  [...document.querySelectorAll('.physical-region-handle')].find(b=>b.dataset.regionId===id&&b.dataset.resizeSide===side)?.focus({preventScroll:true});
}
function physicalStartRegionResize(event,id,side) {
  if(event.button!==0||physicalRegionResizing) return;
  event.preventDefault();event.stopPropagation();physicalRegionResizing=true;
  const snapshot=physicalResizeSnapshot(), scope=wireDiagramKey(), zoom=camera.z;
  const origin=side==="e"||side==="w" ? event.clientX : event.clientY;
  const controller=new AbortController();let frame=null,latest=0;
  const valid=()=>wireDiagramKey()===scope;
  const finish=cancel=>{
    controller.abort();if(frame!==null) cancelAnimationFrame(frame);physicalRegionResizing=false;
    if(!valid()) return;
    if(cancel){physicalRegions=snapshot.regions;wirePositions=snapshot.positions;wireRegionFrames=snapshot.frames;wirePaint();}
    else {physicalApplyRegionResize(snapshot,id,side,latest);wireSavePositions();}
  };
  window.addEventListener('pointermove',move=>{
    if(move.pointerId!==event.pointerId) return;
    if(!valid()){finish(true);return;}
    latest=((side==="e"||side==="w" ? move.clientX : move.clientY)-origin)/zoom;
    if(frame===null) frame=requestAnimationFrame(()=>{frame=null;if(valid()) physicalApplyRegionResize(snapshot,id,side,latest);});
  },{signal:controller.signal});
  window.addEventListener('pointerup',up=>{if(up.pointerId===event.pointerId) finish(false);},{signal:controller.signal});
  window.addEventListener('pointercancel',()=>finish(true),{signal:controller.signal});
  window.addEventListener('blur',()=>finish(true),{signal:controller.signal});
  window.addEventListener('keydown',key=>{if(key.key==='Escape'){key.preventDefault();finish(true);}},{signal:controller.signal});
}
