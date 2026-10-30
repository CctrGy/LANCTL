/* LANWIRE workspace: independent list and interactive topology, real RPC operations. */
const wireBase = { render, refresh, records, fullDetails, settings, wireEdit };
const wireNames = ()=>({
  "device.switch": window.LanctlI18n.t("LANCTL.UI.VIEW.NETWORK_SWITCH"),
  "device.router": window.LanctlI18n.t("LANCTL.UI.WORD.ROUTER"),
  "device.pc": window.LanctlI18n.t("LANCTL.UI.WORD.COMPUTER"),
  "device.server": window.LanctlI18n.t("LANCTL.UI.EXTENSION.SERVER"),
  "device.outlet": window.LanctlI18n.t("LANCTL.UI.VIEW.NETWORK_OUTLET"),
  "device.panel": window.LanctlI18n.t("LANCTL.UI.VIEW.PATCH_PANEL"),
  panel: window.LanctlI18n.t("LANCTL.UI.VIEW.PATCH_PANEL"),
  wire: window.LanctlI18n.t("LANCTL.UI.WORD.CABLE"),
  rack: window.LanctlI18n.t("LANCTL.UI.WORD.RACK"),
  "external.supply": window.LanctlI18n.t("LANCTL.UI.VIEW.PROVIDER_SUPPLY"),
  "wire.copper": window.LanctlI18n.t("LANCTL.UI.TEXT.COPPER_CABLE"),
  "wire.fiber": window.LanctlI18n.t("LANCTL.UI.TEXT.FIBER_CABLE"),
  "wire.dac": window.LanctlI18n.t("LANCTL.UI.VIEW.DAC_CABLE"),
  element: window.LanctlI18n.t("LANCTL.UI.TEXT.ELEMENT"),
  "device.gateway": window.LanctlI18n.t("LANCTL.UI.TEXT.GATEWAY"),
  "device.workstation": window.LanctlI18n.t("LANCTL.UI.VIEW.WORKSTATION"),
  "connection.rj45": "RJ45",
  "connection.fiber": window.LanctlI18n.t("LANCTL.UI.VIEW.OPTICAL_FIBER"),
  "connection.dac": "DAC",
  "connection.unknown": window.LanctlI18n.t("LANCTL.UI.VIEW.UNSPECIFIED"),
});
function wireName(v) {
  return (
    wireNames()[v] ||
    String(v || window.LanctlI18n.t("LANCTL.UI.TEXT.ELEMENT"))
      .replace(/^device\./, "")
      .replace(/[._]/g, " ")
  );
}
const wireModes = ()=>([
  ["wired", window.LanctlI18n.t("LANCTL.UI.WORD.CABLE")],
  ["wifi", "Wi-Fi"],
  ["mixed", window.LanctlI18n.t("LANCTL.UI.VIEW.WIRED_AND_WI_FI")],
]);
function wireReadPrefs() {
  try {
    const saved = JSON.parse(
      localStorage.getItem("lanwire.gui.preferences") || "{}",
    );
    if (saved.schemaVersion !== 1) return {};
    return {
      ...saved,
      view: ["map", "list"].includes(saved.view) ? saved.view : "map",
      depth:
        Number.isInteger(saved.depth) && saved.depth >= 1 && saved.depth <= 10
          ? saved.depth
          : 1,
      columns: Array.isArray(saved.columns)
        ? saved.columns
        : ["id", "type", "connections", "rack", "mode"],
    };
  } catch {
    return {};
  }
}
let wirePrefs = {
  schemaVersion: 1,
  depth: 1,
  labels: true,
  minimap: false,
  view: "map",
  columns: ["id", "type", "connections", "rack", "mode"],
  ...wireReadPrefs(),
};
view = wirePrefs.view;
let wireFilter = {
    kind: "",
    prefix: "",
    group: "",
    rack: "",
    mode: "",
    status: "",
    medium: "",
  },
  wireSort = { key: "name", direction: 1 };
let camera = { x: 40, y: 40, z: 1 },
  wirePositions = {},
  wireFocus = null,
  wireHidden = new Set(),
  wireHistory = [],
  wireHistoryIndex = -1,
  wireDragging = false,
  wireGraph = null,
  wireInitialized = false;
function wireStore() {
  localStorage.setItem("lanwire.gui.preferences", JSON.stringify(wirePrefs));
}
function wirePositionKey() {
  return "lanwire.layout." + state.storage;
}
function wireLoadPositions() {
  try {
    const saved = JSON.parse(localStorage.getItem(wirePositionKey()) || "{}");
    wirePositions = saved.schemaVersion === 1 ? saved.positions || {} : {};
  } catch {
    wirePositions = {};
  }
}
function wireSavePositions() {
  localStorage.setItem(
    wirePositionKey(),
    JSON.stringify({ schemaVersion: 1, positions: wirePositions }),
  );
}
function wireConnections(r) {
  return physicalInventory().filter(
    (w) =>
      w.data.type === "wire" &&
      (w.data.endpoints || []).some((e) => e.device === r.id),
  );
}
function wireFree(r) {
  return Object.keys(r.data.ports || {}).some(
    (p) =>
      !wireConnections(r).some((w) =>
        w.data.endpoints.some((e) => e.device === r.id && e.port === p),
      ),
  );
}
records = function () {
  if (state.launcher !== "lanwire") return wireBase.records();
  const query = $("#search").value.trim().toLocaleLowerCase(),
    type = $("#filter").value;
  let rows = state.records.filter((r) => {
    const d = r.data,
      f = wireFilter;
    return (
      (!type || d.type === type) &&
      (!query ||
        [
          r.id,
          r.prefix,
          d.name,
          d.alias,
          d.description,
          d.ip,
          ...(r.filterGroups || []),
          wireName(d.type),
        ]
          .join(" ")
          .toLocaleLowerCase()
          .includes(query)) &&
      (!f.kind || (f.kind === "wires") === (d.type === "wire")) &&
      (!f.prefix || r.prefix === f.prefix) &&
      (!f.group || (r.filterGroups || d.groups || []).includes(f.group)) &&
      (!f.rack || view === "map" || physicalRackOf(r) === f.rack) &&
      (!f.mode || (d.connectionMode || "wired") === f.mode) &&
      (!f.medium ||
        d.kind === f.medium ||
        Object.values(d.ports || {}).some((p) => p.kind === f.medium)) &&
      (!f.status ||
        (f.status === "free"
          ? wireFree(r)
          : f.status === "connected"
            ? d.type === "wire"
              ? d.endpoints?.length
              : wireConnections(r).length
            : !(d.type === "wire"
                ? d.endpoints?.length
                : wireConnections(r).length)))
    );
  });
  const value = (r) =>
    wireSort.key === "name"
      ? labelOf(r)
      : wireSort.key === "type"
        ? wireName(r.data.type)
        : r.id;
  return rows.sort(
    (a, b) =>
      String(value(a)).localeCompare(String(value(b)), "es", {
        numeric: true,
      }) * wireSort.direction,
  );
};
refresh = async function () {
  if (wireDragging) return;
  await wireBase.refresh();
  if (state.launcher !== "lanwire") return;
  for (const o of $("#filter").options) {
    if (o.value) {
      const identifier = o.value;
      o.value = identifier;
      o.textContent = wireName(identifier);
    }
  }
  if (!wireInitialized) {
    wireInitialized = true;
    document.body.classList.add("wire-app");
    const more = document.createElement("button");
    more.id = "wire-filters";
    window.LanctlI18n.bindText(more,"LANCTL.UI.WORD.FILTERS");
    more.onclick = wireFilters;
    $("#filter").after(more);
    const clear = document.createElement("button");
    window.LanctlI18n.bindText(clear,"LANCTL.UI.WORD.CLEAR");
    clear.onclick = wireClearFilters;
    more.after(clear);
    const active = document.createElement("span");
    active.id = "wire-active-filters";
    $(".filterbar").after(active);
  }
  $("#wire-active-filters").textContent =
    Object.values(wireFilter).filter(Boolean).length +
    window.LanctlI18n.t("LANCTL.UI.FRAGMENT.ADDITIONAL_FILTERS_SHARED_PHYSICAL_STORE");
};
renderWire = function (rows, r) {
  if (!wireInitialized) wireLoadPositions();
  if (view === "list") {
    const cols = {
      id: [window.LanctlI18n.t("LANCTL.UI.HTML.IDENTIFIER"), (x) => x.id],
      type: [window.LanctlI18n.t("LANCTL.UI.TEXT.TYPE"), (x) => wireName(x.data.type)],
      connections: [
        window.LanctlI18n.t("LANCTL.UI.TEXT.CONNECTIONS"),
        (x) =>
          x.data.type === "wire"
            ? (x.data.endpoints || [])
                .map((e) => e.device + " · " + e.port)
                .join(" ↔ ")
            : wireConnections(x)
                .map((w) => w.id)
                .join(", "),
      ],
      rack: [
        window.LanctlI18n.t("LANCTL.UI.VIEW.RACK_UNIT"),
        (x) =>
          physicalPlacementLabel(x),
      ],
      mode: [
        window.LanctlI18n.t("LANCTL.UI.TEXT.CONNECTION"),
        (x) =>
          wireModes().find(
            (m) => m[0] === (x.data.connectionMode || "wired"),
          )?.[1],
      ],
      alias: [window.LanctlI18n.t("LANCTL.UI.WORD.ALIAS"), (x) => x.data.alias],
      group: [
        window.LanctlI18n.t("LANCTL.UI.TEXT.GROUPS"),
        (x) => (x.filterGroups || x.data.groups || []).join(", "),
      ],
    };
    const visible = wirePrefs.columns.filter((k) => cols[k]);
    $("#canvas").innerHTML =
      "<div class=\"wire-list-tools\"><button id=\"wire-columns\"><span data-i18n=\"LANCTL.UI.TEXT.COLUMNS\">Columnas</span></button><label><span data-i18n=\"LANCTL.UI.HTML.SORT\">Ordenar</span> <select id=\"wire-sort\"><option value=\"name\" data-i18n=\"LANCTL.INVENTORY.MANUAL.NAME\">Nombre</option><option value=\"id\" data-i18n=\"LANCTL.UI.HTML.IDENTIFIER\">Identificador</option><option value=\"type\" data-i18n=\"LANCTL.UI.TEXT.TYPE\">Tipo</option></select></label><button id=\"wire-direction\">" +
      (wireSort.direction === 1 ? window.LanctlI18n.html("LANCTL.UI.FRAGMENT.ASCENDING") : window.LanctlI18n.html("LANCTL.UI.FRAGMENT.DESCENDING")) +
      "</button></div>" +
      table([window.LanctlI18n.t("LANCTL.UI.TEXT.ELEMENT"), ...visible.map((k) => cols[k][0])], rows, (x) => [
        labelOf(x),
        ...visible.map((k) => cols[k][1](x)),
      ]);
    $("#wire-columns").onclick = wireColumns;
    $("#wire-sort").value = wireSort.key;
    $("#wire-sort").onchange = (e) => {
      wireSort.key = e.target.value;
      render();
    };
    $("#wire-direction").onclick = () => {
      wireSort.direction *= -1;
      render();
    };
    wireResizeColumns();
    return;
  }
  wireRenderTopology(rows);
};
render = function () {
  wireBase.render();
  if (state.launcher !== "lanwire") return;
  wirePrefs.view = view;
  wireStore();
  if (!state.records.length && !$("#wire-board")) return;
};
function wireClearFilters() {
  wireFilter = {
    kind: "",
    prefix: "",
    group: "",
    rack: "",
    mode: "",
    status: "",
    medium: "",
  };
  $("#search").value = "";
  $("#filter").value = "";
  wireHidden.clear();
  render();
}
function wireFilters() {
  const opts = (key, label, values) =>
    field(label, key, wireFilter[key], "text", [["", window.LanctlI18n.t("LANCTL.UI.TEXT.ALL")], ...values]);
  const unique = (values) =>
    [...new Set(values.filter(Boolean))].map((v) => [v, v]);
  showForm(
    window.LanctlI18n.t("LANCTL.UI.VIEW.ELEMENT_FILTERS"),
    [
      opts("kind", window.LanctlI18n.t("LANCTL.UI.WORD.SHOW"), [
        ["elements", window.LanctlI18n.t("LANCTL.UI.VIEW.EQUIPMENT_AND_INFRASTRUCTURE")],
        ["wires", window.LanctlI18n.t("LANCTL.UI.TEXT.CABLES")],
      ]),
      opts("prefix", window.LanctlI18n.t("LANCTL.UI.WORD.PREFIX"), unique(state.records.map((r) => r.prefix))),
      opts(
        "group",
        window.LanctlI18n.t("LANCTL.UI.TEXT.GROUP"),
        unique(
          state.records.flatMap((r) => r.filterGroups || r.data.groups || []),
        ).map(([v]) => [
          v,
          {
            WIRE: window.LanctlI18n.t("LANCTL.UI.TEXT.CABLES"),
            SWITCHS: window.LanctlI18n.t("LANCTL.UI.VIEW.DISTRIBUTION_EQUIPMENT"),
            PC: window.LanctlI18n.t("LANCTL.UI.VIEW.COMPUTERS_AND_SERVERS"),
          }[v] || v,
        ]),
      ),
      opts(
        "rack",
        window.LanctlI18n.t("LANCTL.UI.WORD.RACK"),
        state.records
          .filter((r) => r.data.type === "rack")
          .map((r) => [r.id, labelOf(r)]),
      ),
      opts("mode", window.LanctlI18n.t("LANCTL.UI.VIEW.CONNECTION_TYPE"), wireModes()),
      opts("status", window.LanctlI18n.t("LANCTL.UI.WORD.AVAILABILITY"), [
        ["connected", window.LanctlI18n.t("LANCTL.UI.WORD.CONNECTED")],
        ["disconnected", window.LanctlI18n.t("LANCTL.UI.TEXT.NOT_CONNECTED")],
        ["free", window.LanctlI18n.t("LANCTL.UI.VIEW.WITH_FREE_PORTS")],
      ]),
      opts("medium", window.LanctlI18n.t("LANCTL.UI.WORD.MEDIUM"), [
        ["wire.copper", window.LanctlI18n.t("LANCTL.UI.WORD.COPPER")],
        ["wire.fiber", window.LanctlI18n.t("LANCTL.UI.WORD.FIBER")],
        ["wire.dac", "DAC"],
      ]),
    ],
    async (values) => {
      wireFilter = values;
    },
  );
}
function wireColumns() {
  const note = document.createElement("p");
  window.LanctlI18n.bindText(note,"LANCTL.UI.VIEW.IDENTIFIER_TYPE_CONNECTIONS_RACK_CONNECTION_ALIAS_AND_GROUPS");
  const box = document.createElement("div");
  for (const [key, label] of [
    ["id", window.LanctlI18n.t("LANCTL.UI.HTML.IDENTIFIER")],
    ["type", window.LanctlI18n.t("LANCTL.UI.TEXT.TYPE")],
    ["connections", window.LanctlI18n.t("LANCTL.UI.TEXT.CONNECTIONS")],
    ["rack", window.LanctlI18n.t("LANCTL.UI.WORD.RACK")],
    ["mode", window.LanctlI18n.t("LANCTL.UI.TEXT.CONNECTION")],
    ["alias", window.LanctlI18n.t("LANCTL.UI.WORD.ALIAS")],
    ["group", window.LanctlI18n.t("LANCTL.UI.TEXT.GROUPS")],
  ]) {
    const f = field(label, key, "", "checkbox");
    f.querySelector("input").checked = wirePrefs.columns.includes(key);
    box.append(f);
  }
  showForm(window.LanctlI18n.t("LANCTL.UI.VIEW.LIST_COLUMNS"), [note, box], async (v) => {
    wirePrefs.columns = Object.keys(v);
    wireStore();
  });
}
function wireEdges() {
  return state.records
    .filter((r) => r.data.type === "wire")
    .map((w) => {
      const ends = [
        ...(w.data.source
          ? [{ device: w.data.source, port: window.LanctlI18n.t("LANCTL.UI.WORD.PROVIDER") }]
          : []),
        ...(w.data.endpoints || []),
      ];
      return { wire: w, a: ends[0], b: ends[1] };
    });
}
function wireNeighborhood(id, depth) {
  const found = new Set([id]);
  for (let i = 0; i < depth; i++) {
    const before = new Set(found);
    for (const e of wireEdges())
      if (
        before.has(e.a?.device) ||
        before.has(e.b?.device) ||
        before.has(e.wire.id)
      ) {
        found.add(e.wire.id);
        if (e.a) found.add(e.a.device);
        if (e.b) found.add(e.b.device);
      }
  }
  return found;
}
function wireLayout(nodes) {
  const levels = new Map(),
    seen = new Set(),
    adj = new Map(nodes.map((n) => [n.id, []]));
  for (const e of wireEdges())
    if (adj.has(e.a?.device) && adj.has(e.b?.device)) {
      adj.get(e.a.device).push(e.b.device);
      adj.get(e.b.device).push(e.a.device);
    }
  const roots = [...nodes].sort(
    (a, b) => (adj.get(b.id)?.length || 0) - (adj.get(a.id)?.length || 0),
  );
  let offset = 0,
    rowY = 0,
    rowHeight = 0;
  for (const root of roots) {
    if (seen.has(root.id)) continue;
    const queue = [[root.id, 0]],
      width = new Map(),
      component = new Map();
    while (queue.length) {
      const [id, level] = queue.shift();
      if (seen.has(id)) continue;
      seen.add(id);
      const col = width.get(level) || 0;
      width.set(level, col + 1);
      component.set(id, { x: col * 235, y: level * 170 });
      for (const next of adj.get(id) || [])
        if (!seen.has(next)) queue.push([next, level + 1]);
    }
    const componentWidth = Math.max(1, ...width.values()) * 235;
    const componentHeight = width.size * 170;
    if (offset && offset + componentWidth > 1200) {
      offset = 0;
      rowY += rowHeight + 70;
      rowHeight = 0;
    }
    for (const [id, p] of component)
      levels.set(id, { x: offset + p.x, y: rowY + p.y });
    offset += componentWidth + 70;
    rowHeight = Math.max(rowHeight, componentHeight);
  }
  return levels;
}
function wireRenderTopology(rows) {
  let allowed = new Set(rows.map((r) => r.id));
  // A matching cable needs its endpoint equipment as visual context, even
  // when the type filter or search matches only the cable itself.
  for (const edge of wireEdges()) {
    if (allowed.has(edge.wire.id)) {
      if (edge.a) allowed.add(edge.a.device);
      if (edge.b) allowed.add(edge.b.device);
    }
  }
  if (wireFocus) {
    const neighborhood = wireNeighborhood(wireFocus, Number(wirePrefs.depth));
    allowed = new Set([...allowed].filter((id) => neighborhood.has(id)));
  }
  const nodes = state.records.filter(
    (r) =>
      r.data.type !== "wire" &&
      r.data.type !== "rack" &&
      allowed.has(r.id) &&
      !wireHidden.has(r.id) &&
      (wirePrefs.showWifi || r.data.connectionMode !== "wifi"),
  );
  const automatic = wireLayout(nodes);
  for (const n of nodes)
    if (!wirePositions[n.id]) wirePositions[n.id] = automatic.get(n.id);
  wireGraph = {
    nodes,
    edges: wireEdges().filter(
      (e) =>
        allowed.has(e.wire.id) ||
        (allowed.has(e.a?.device) && allowed.has(e.b?.device)),
    ),
  };
  $("#canvas").innerHTML =
    "<section class=\"wire-topology\"><div class=\"wire-navigation\"><button data-nav=\"back\" title=\"Vista anterior\" data-i18n-title=\"LANCTL.UI.HTML.PREVIOUS_VIEW\">←</button><button data-nav=\"forward\" title=\"Vista siguiente\" data-i18n-title=\"LANCTL.UI.HTML.NEXT_VIEW\">→</button><button data-nav=\"out\" aria-label=\"Alejar\" data-i18n-aria-label=\"LANCTL.UI.HTML.ZOOM_OUT\">−</button><button id=\"wire-zoom\" data-nav=\"reset\">100 %</button><button data-nav=\"in\" aria-label=\"Acercar\" data-i18n-aria-label=\"LANCTL.UI.HTML.ZOOM_IN\">+</button><button data-nav=\"fit\"><span data-i18n=\"LANCTL.UI.HTML.VIEW_ALL\">Ver todo</span></button><button data-nav=\"center\"><span data-i18n=\"LANCTL.UI.HTML.CENTER_SELECTION\">Centrar selección</span></button><button data-nav=\"focus\"><span data-i18n=\"LANCTL.UI.VIEW.VIEW_CONNECTIONS\">Ver conexiones</span></button><label><span data-i18n=\"LANCTL.UI.HTML.LEVELS\">Niveles</span> <select id=\"wire-depth\"><option>1</option><option>2</option><option>3</option><option>5</option><option>10</option></select></label><button data-nav=\"all\"><span data-i18n=\"LANCTL.UI.HTML.COMPLETE_TOPOLOGY\">Topología completa</span></button><button data-nav=\"layout\"><span data-i18n=\"LANCTL.UI.HTML.REORGANIZE\">Reorganizar</span></button><button data-nav=\"mini\"><span data-i18n=\"LANCTL.UI.HTML.MINIMAP\">Minimapa</span></button></div><div id=\"wire-board\" tabindex=\"0\" aria-label=\"Lienzo de topología. Arrastra el fondo para desplazarte; usa la rueda para ampliar.\" data-i18n-aria-label=\"LANCTL.UI.HTML.TOPOLOGY_CANVAS_DRAG_THE_BACKGROUND_TO_PAN_USE_THE_WHEEL_TO_ZOOM\"><div id=\"wire-world\"><svg id=\"wire-lines\"></svg>" +
    nodes
      .map(
        (n) =>
          `<button class="wire-node ${n.id === selected ? "selected" : ""}" data-node="${esc(n.id)}"><strong>${esc(labelOf(n))}</strong><small>${esc(n.id)} · ${esc(wireName(n.data.type))}</small><span class="wire-ports" ${wirePrefs.showPorts === false ? "hidden" : ""}>${wireOrderedPorts(
            n,
          )
            .map(
              (p) =>
                `<span data-port="${esc(p)}" class="${wireConnections(n).some((w) => (w.data.endpoints || []).some((e) => e.device === n.id && e.port === p)) ? "occupied" : "free"}" title="${esc(p)}">▣ ${esc(p)}</span>`,
            )
            .join("")}</span></button>`,
      )
      .join("") +
    "</div><svg id=\"wire-minimap\" aria-label=\"Minimapa\" data-i18n-aria-label=\"LANCTL.UI.HTML.MINIMAP\"></svg><div class=\"wire-hint\"><span data-i18n=\"LANCTL.UI.HTML.DRAG_MOVE_WHEEL_ZOOM_DOUBLE_CLICK_DETAILS_RIGHT_CLICK_ACTIONS\">Arrastrar: mover · Rueda: zoom · Doble clic: detalles · Clic derecho: acciones</span>" +
    (wireFocus ? window.LanctlI18n.html("LANCTL.UI.FRAGMENT.FOCUS") + esc(wireFocus) : "") +
    "</div></div></section>";
  $("#wire-depth").value = wirePrefs.depth;
  $("#wire-depth").onchange = (e) => {
    wirePrefs.depth = Number(e.target.value);
    wireStore();
    render();
    wireFit();
  };
  $("#wire-board").onwheel = (e) => {
    e.preventDefault();
    const rect = e.currentTarget.getBoundingClientRect();
    wireZoom(
      Math.exp(-e.deltaY * 0.001),
      e.clientX - rect.left,
      e.clientY - rect.top,
    );
  };
  $("#wire-board").onpointerdown = wirePointer;
  $("#wire-board").ondblclick = (e) => {
    const node = e.target.closest("[data-node]");
    if (node) {
      clearTimeout(clickTimer);
      selected = node.dataset.node;
      fullDetails(state.records.find((r) => r.id === selected));
    }
  };
  $("#wire-board").oncontextmenu = (e) => {
    e.preventDefault();
    const n = e.target.closest("[data-node]");
    if (n) {
      selected = n.dataset.node;
      wireContext(state.records.find((r) => r.id === selected));
    }
  };
  $("#wire-board").onkeydown = (e) => {
    if (
      [
        "ArrowLeft",
        "ArrowRight",
        "ArrowUp",
        "ArrowDown",
        "+",
        window.LanctlI18n.t("LANCTL.COMMON.VALUE.NONE"),
        "Home",
      ].includes(e.key)
    )
      e.preventDefault();
    if (e.key === "+") wireZoom(1.2);
    else if (e.key === "-") wireZoom(1 / 1.2);
    else if (e.key === "Home") wireFit();
    else {
      camera.x += e.key === "ArrowLeft" ? 40 : e.key === "ArrowRight" ? -40 : 0;
      camera.y += e.key === "ArrowUp" ? 40 : e.key === "ArrowDown" ? -40 : 0;
      wirePaint();
    }
  };
  wirePaint();
}
function wirePaint() {
  if (!$("#wire-world") || !wireGraph) return;
  $("#wire-world").style.transform =
    `translate(${camera.x}px,${camera.y}px) scale(${camera.z})`;
  for (const n of wireGraph.nodes) {
    const el = document.querySelector('[data-node="' + CSS.escape(n.id) + '"]'),
      p = wirePositions[n.id];
    el.style.left = p.x + "px";
    el.style.top = p.y + "px";
    el.classList.toggle("selected", n.id === selected);
    el.classList.toggle("no-labels", !wirePrefs.labels);
  }
  const visible = new Set(wireGraph.nodes.map((n) => n.id)),
    near = wireNeighborhood(selected, 1);
  $("#wire-lines").innerHTML = wireGraph.edges
    .filter((e) => visible.has(e.a?.device) || visible.has(e.b?.device))
    .map((original) => {
      const e = visible.has(original.a?.device)
        ? original
        : { ...original, a: original.b, b: original.a };
      const a = wireAnchor(e.a),
        b = visible.has(e.b?.device)
          ? wireAnchor(e.b)
          : { x: a.x + 220, y: a.y + 120 };
      return `<g data-cable="${esc(e.wire.id)}" class="${near.has(e.wire.id) ? "highlight" : ""}"><path d="M${a.x} ${a.y} C${a.x} ${(a.y + b.y) / 2},${b.x} ${(a.y + b.y) / 2},${b.x} ${b.y}"/><text x="${(a.x + b.x) / 2}" y="${(a.y + b.y) / 2}">${wirePrefs.labels ? esc(e.wire.id + " · " + e.a.port + " ↔ " + (e.b?.port || window.LanctlI18n.t("LANCTL.UI.TEXT.NOT_CONNECTED"))) : ""}</text></g>`;
    })
    .join("");
  $("#wire-lines").onclick = (e) => {
    const cable = e.target.closest("[data-cable]");
    if (cable) {
      selected = cable.dataset.cable;
      fullDetails(state.records.find((r) => r.id === selected));
    }
  };
  $("#wire-zoom").textContent = Math.round(camera.z * 100) + " %";
  wireMini();
  wireNavAvailability();
}
function wireNavAvailability() {
  const back = document.querySelector('[data-nav="back"]');
  const forward = document.querySelector('[data-nav="forward"]');
  if (back) back.disabled = wireHistoryIndex <= 0;
  if (forward) forward.disabled = wireHistoryIndex >= wireHistory.length - 1;
}
function wireAnchor(endpoint) {
  const node = document.querySelector(
    `[data-node="${CSS.escape(endpoint.device)}"]`,
  );
  const port = node?.querySelector(
    `[data-port="${CSS.escape(endpoint.port || "")}"]`,
  );
  if (port && wirePrefs.showPorts !== false) {
    const rect = port.getBoundingClientRect(),
      board = $("#wire-board").getBoundingClientRect();
    return {
      x: (rect.x + rect.width / 2 - board.x - camera.x) / camera.z,
      y: (rect.y + rect.height / 2 - board.y - camera.y) / camera.z,
    };
  }
  const position = wirePositions[endpoint.device];
  return { x: position.x + 95, y: position.y + 45 };
}
function wireZoom(factor, x, y) {
  const board = $("#wire-board");
  if (!board) return;
  x ??= board.clientWidth / 2;
  y ??= board.clientHeight / 2;
  const z = Math.max(0.02, Math.min(3, camera.z * factor));
  camera.x = x - ((x - camera.x) * z) / camera.z;
  camera.y = y - ((y - camera.y) * z) / camera.z;
  camera.z = z;
  wirePaint();
}
function wireBounds() {
  const ps = wireGraph.nodes.map((n) => wirePositions[n.id]);
  return {
    x: Math.min(0, ...ps.map((p) => p.x)),
    y: Math.min(0, ...ps.map((p) => p.y)),
    right: Math.max(200, ...ps.map((p) => p.x + 190)),
    bottom: Math.max(100, ...ps.map((p) => p.y + 100)),
  };
}
function wireFit() {
  if (!$("#wire-board") || !wireGraph) return;
  const b = wireBounds(),
    el = $("#wire-board");
  camera.z = Math.max(
    0.02,
    Math.min(
      1.5,
      (el.clientWidth - 80) / (b.right - b.x),
      (el.clientHeight - 80) / (b.bottom - b.y),
    ),
  );
  camera.x = (el.clientWidth - (b.right - b.x) * camera.z) / 2 - b.x * camera.z;
  camera.y =
    (el.clientHeight - (b.bottom - b.y) * camera.z) / 2 - b.y * camera.z;
  wirePaint();
}
function wireCenter() {
  let p = wirePositions[selected];
  const el = $("#wire-board");
  if (!p) {
    const edge = wireEdges().find((e) => e.wire.id === selected);
    const points = [edge?.a, edge?.b]
      .filter((e) => e && wirePositions[e.device])
      .map((e) => wirePositions[e.device]);
    if (points.length)
      p = {
        x: points.reduce((sum, p) => sum + p.x, 0) / points.length,
        y: points.reduce((sum, p) => sum + p.y, 0) / points.length,
      };
  }
  if (!p || !el) {
    message(window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_A_VISIBLE_DEVICE_TO_CENTER_IT"));
    return;
  }
  camera.x = el.clientWidth / 2 - (p.x + 95) * camera.z;
  camera.y = el.clientHeight / 2 - (p.y + 45) * camera.z;
  wirePaint();
}
function wireRemember() {
  wireHistory = wireHistory.slice(0, wireHistoryIndex + 1);
  wireHistory.push({ camera: { ...camera }, focus: wireFocus, selected });
  wireHistoryIndex = wireHistory.length - 1;
  wireNavAvailability();
}
function wireNavigate(action) {
  if (action === "back" || action === "forward") {
    const next = wireHistoryIndex + (action === "back" ? -1 : 1);
    if (next < 0 || next >= wireHistory.length) return;
    wireHistoryIndex = next;
    const h = wireHistory[next];
    camera = { ...h.camera };
    wireFocus = h.focus;
    selected = h.selected;
    render();
    return;
  }
  if (!wireHistory.length) wireRemember();
  if (action === "in") wireZoom(1.25);
  if (action === "out") wireZoom(0.8);
  if (action === "reset") {
    wireZoom(1 / camera.z);
  }
  if (action === "fit") wireFit();
  if (action === "center") wireCenter();
  if (action === "focus") {
    wireFocus = selected;
    wireHidden.clear();
    render();
    wireFit();
  }
  if (action === "all") {
    wireFocus = null;
    wireHidden.clear();
    render();
    wireFit();
  }
  if (action === "layout") {
    wirePositions = {};
    render();
    wireFit();
    wireSavePositions();
  }
  if (action === "mini") {
    wirePrefs.minimap = !wirePrefs.minimap;
    wireStore();
    wirePaint();
  }
  wireRemember();
}
function wireMini() {
  const mini = $("#wire-minimap");
  if (!mini) return;
  mini.style.display = wirePrefs.minimap ? "block" : "none";
  const b = wireBounds(),
    w = b.right - b.x + 80,
    h = b.bottom - b.y + 80;
  mini.setAttribute("viewBox", `${b.x - 40} ${b.y - 40} ${w} ${h}`);
  mini.innerHTML =
    wireGraph.nodes
      .map((n) => {
        const p = wirePositions[n.id];
        return `<rect x="${p.x}" y="${p.y}" width="${physicalSize(n).w}" height="${physicalSize(n).h}"/>`;
      })
      .join("") +
    `<rect class="viewport" x="${-camera.x / camera.z}" y="${-camera.y / camera.z}" width="${$("#wire-board").clientWidth / camera.z}" height="${$("#wire-board").clientHeight / camera.z}"/>`;
  mini.onclick = (e) => {
    const r = mini.getBoundingClientRect(),
      scale = Math.min(r.width / w, r.height / h),
      ox = (r.width - w * scale) / 2,
      oy = (r.height - h * scale) / 2;
    camera.x =
      $("#wire-board").clientWidth / 2 -
      ((e.clientX - r.left - ox) / scale + b.x - 40) * camera.z;
    camera.y =
      $("#wire-board").clientHeight / 2 -
      ((e.clientY - r.top - oy) / scale + b.y - 40) * camera.z;
    wirePaint();
  };
}
function wirePointer(e) {
  if (e.button !== 0 || e.target.closest("#wire-minimap")) return;
  if (e.target.closest("[data-cable]") && !physicalNodeAt(e)) return;
  const node = e.target.closest("[data-node]") || physicalNodeAt(e);
  const start = {
    x: e.clientX,
    y: e.clientY,
    c: { ...camera },
    p: node ? { ...wirePositions[node.dataset.node] } : null,
  };
  let moved = false;
  wireDragging = true;
  const board = e.currentTarget;
  (node || board).setPointerCapture(e.pointerId);
  const move = (ev) => {
    const dx = ev.clientX - start.x,
      dy = ev.clientY - start.y;
    moved ||= Math.abs(dx) + Math.abs(dy) > 4;
    if (node) {
      wirePositions[node.dataset.node] = {
        x: start.p.x + dx / camera.z,
        y: start.p.y + dy / camera.z,
      };
    } else {
      camera.x = start.c.x + dx;
      camera.y = start.c.y + dy;
    }
    wirePaint();
  };
  const up = () => {
    wireDragging = false;
    board.removeEventListener("pointermove", move);
    board.removeEventListener("pointerup", up);
    if (node) {
      selected = node.dataset.node;
      document
        .querySelectorAll("[data-node]")
        .forEach((n) =>
          n.classList.toggle("selected", n.dataset.node === selected),
        );
      $("#selection").textContent = labelOf(
        state.records.find((r) => r.id === selected),
      );
      if (moved) wireSavePositions();
      else {
        clearTimeout(clickTimer);
        clickTimer = setTimeout(render, 260);
      }
    }
    if (moved) wireRemember();
  };
  board.addEventListener("pointermove", move);
  board.addEventListener("pointerup", up, { once: true });
  board.addEventListener("pointercancel", up, { once: true });
}
function wireContext(r) {
  const box = document.createElement("div");
  for (const [label, fn] of [
    [window.LanctlI18n.t("LANCTL.UI.TEXT.VIEW_AND_EDIT_DATA"), () => fullDetails(r)],
    [window.LanctlI18n.t("LANCTL.UI.WORD.CENTER"), () => wireCenterFromDetails(r)],
    [
      window.LanctlI18n.t("LANCTL.UI.VIEW.VIEW_CONNECTIONS"),
      () => {
        wireFocus = r.id;
        view = "map";
        render();
        wireFit();
      },
    ],
    [
      window.LanctlI18n.t("LANCTL.UI.VIEW.COLLAPSE_THIS_BRANCH"),
      () => {
        for (const id of wireNeighborhood(r.id, Number(wirePrefs.depth)))
          if (id !== r.id) wireHidden.add(id);
        render();
      },
    ],
    [
      window.LanctlI18n.t("LANCTL.UI.VIEW.EXPAND_BRANCHES"),
      () => {
        wireHidden.clear();
        wirePrefs.depth = Math.min(10, Number(wirePrefs.depth) + 1);
        render();
        wireFit();
      },
    ],
  ]) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.onclick = async () => {
      await dismiss();
      if (!$("#detail").open) fn();
    };
    box.append(b);
  }
  showForm(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.ACTIONS") + labelOf(r), [box]);
}
async function wireCenterFromDetails(r) {
  await dismiss();
  if ($("#detail").open) return;
  view = "map";
  selected = r.id;
  const filtered =
    !records().some((x) => x.id === r.id) ||
    (r.data.connectionMode === "wifi" && !wirePrefs.showWifi);
  if (
    filtered &&
    !(await appDecision(
      window.LanctlI18n.t("LANCTL.UI.VIEW.FILTERS_HIDE_THIS_ELEMENT_CLEAR_THEM_TO_SHOW_IT"),
    ))
  )
    return;
  if (filtered) {
    wireClearFilters();
    wirePrefs.showWifi = true;
  }
  wireFocus = null;
  wireHidden.clear();
  render();
  if (r.data.type === "wire") {
    wireFocus = r.id;
    render();
    wireFit();
  } else wireCenter();
  wireRemember();
}
function wireTabs(sections) {
  const container = document.createElement("div"),
    nav = document.createElement("nav");
  nav.className = "wire-tabs";
  container.append(nav);
  sections.forEach(([label, nodes], index) => {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = label;
    b.setAttribute("role", "tab");
    const panel = document.createElement("section");
    panel.className = "wire-tab-panel";
    panel.hidden = index !== 0;
    panel.append(...nodes);
    b.classList.toggle("active", index === 0);
    b.onclick = () => {
      container
        .querySelectorAll(".wire-tab-panel")
        .forEach((p) => (p.hidden = p !== panel));
      nav.querySelectorAll("button").forEach((x) => {
        x.classList.toggle("active", x === b);
        x.setAttribute("aria-selected", x === b);
      });
    };
    nav.append(b);
    container.append(panel);
  });
  return container;
}
function wireAction(label, fn) {
  const b = document.createElement("button");
  b.type = "button";
  b.textContent = label;
  b.onclick = () =>
    Promise.resolve(fn()).catch(
      (e) => ($("#detail-error").textContent = e.message),
    );
  return b;
}
fullDetails = function (r) {
  if (!["lanwire", "lanrack"].includes(state.launcher)) return wireBase.fullDetails(r);
  const d = r.data;
  const identity = document.createElement("p");
  identity.textContent = r.id + " · " + wireName(d.type);
  const general = [
    identity,
    field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.NAME"), "name", d.name),
    field(window.LanctlI18n.t("LANCTL.UI.WORD.ALIAS"), "alias", d.alias),
    field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.DESCRIPTION"), "description", d.description, "textarea"),
    field(
      window.LanctlI18n.t("LANCTL.UI.TEXT.CONNECTION"),
      "connectionMode",
      d.connectionMode || "wired",
      "text",
      wireModes(),
    ),
  ];
  const location = physicalLocationFields(r);
  const ports = document.createElement("div");
  for (const [p, value] of Object.entries(d.ports || {})) {
    const row = document.createElement("div");
    row.className = "wire-port-row";
    const text = document.createElement("span");
    text.textContent =
      p +
      " · " +
      wireName(value.kind) +
      " · " +
      (value.connector || "") +
      " · " +
      (wireConnections(r).find((w) =>
        w.data.endpoints.some((e) => e.device === r.id && e.port === p),
      )?.id || window.LanctlI18n.t("LANCTL.UI.HTML.FREE"));
    row.append(
      text,
      field(window.LanctlI18n.t("LANCTL.UI.WORD.MEDIUM"), "port_kind_" + p, value.kind || "wire.copper", "text", [
        ["wire.copper", window.LanctlI18n.t("LANCTL.UI.WORD.COPPER")],
        ["wire.fiber", window.LanctlI18n.t("LANCTL.UI.WORD.FIBER")],
        ["wire.dac", "DAC"],
        ["connection.rj45", "RJ45"],
        ["connection.fiber", window.LanctlI18n.t("LANCTL.UI.VIEW.OPTICAL_FIBER")],
        ["connection.dac", window.LanctlI18n.t("LANCTL.UI.VIEW.DAC_CONNECTOR")],
        ["connection.unknown", window.LanctlI18n.t("LANCTL.UI.VIEW.UNSPECIFIED")],
      ]),
      field("PoE", "port_poe_" + p, String(!!value.poe), "text", [
        ["false", window.LanctlI18n.t("LANCTL.UI.TEXT.NO")],
        ["true", window.LanctlI18n.t("LANCTL.UI.TEXT.YES")],
      ]),
      wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.EDIT_PORT"), () =>
        wireOpenAfterSave(() => wirePort(r, p)),
      ),
      wireAction(window.LanctlI18n.t("LANCTL.UI.TEXT.CONNECTIONS"), () =>
        wireOpenAfterSave(() => wirePortConnections(r, p)),
      ),
    );
    ports.append(row);
  }
  if (!ports.childNodes.length)
    window.LanctlI18n.bindText(ports,"LANCTL.UI.VIEW.THIS_ELEMENT_HAS_NO_PORTS");
  const connections = document.createElement("div");
  for (const w of d.type === "wire" ? [r] : wireConnections(r)) {
    const p = document.createElement("p");
    p.textContent =
      labelOf(w) +
      " · " +
      (w.data.endpoints || [])
        .map((e) => e.device + " · " + e.port)
        .join(" ↔ ");
    connections.append(
      p,
      wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.EDIT_CONNECTION"), () =>
        wireOpenAfterSave(() => wireConnect(w)),
      ),
    );
  }
  if (!connections.childNodes.length)
    window.LanctlI18n.bindText(connections,"LANCTL.UI.VIEW.NO_STORED_CONNECTIONS");
  const technical = document.createElement("dl");
  const technicalFields = [
    field(
      window.LanctlI18n.t("LANCTL.UI.VIEW.GROUPS_COMMA_SEPARATED"),
      "groups",
      (d.groups || []).join(", "),
    ),
    field(window.LanctlI18n.t("LANCTL.UI.TEXT.IP_ADDRESS"), "ip", d.ip),
    field(
      window.LanctlI18n.t("LANCTL.UI.VIEW.SPEEDS_COMMA_SEPARATED"),
      "speeds",
      (d.speeds || []).join(", "),
    ),
  ];
  if (d.type === "wire")
    technicalFields.push(
      field(window.LanctlI18n.t("LANCTL.UI.VIEW.CABLE_MEDIUM"), "kind", d.kind || "wire.copper", "text", [
        ["wire.copper", window.LanctlI18n.t("LANCTL.UI.WORD.COPPER")],
        ["wire.fiber", window.LanctlI18n.t("LANCTL.UI.WORD.FIBER")],
        ["wire.dac", "DAC"],
      ]),
    );
  if (d.type === "rack") technicalFields.push(
    field(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.RACK_HEIGHT_4_52_U"), "units", d.units ?? d.size_units, "number"),
    field(window.LanctlI18n.t("LANCTL.UI.VIEW.MOUNTING_WIDTH_INCHES"), "widthInches", d.rackDimensions?.widthInches || "", "text", [["", window.LanctlI18n.t("LANCTL.UI.TEXT.SELECT")], [10, "10″"], [19, "19″"], [21, "21″"], [23, "23″"]]),
  );
  for (const [k, v] of Object.entries({
    ...d,
    created_at: r.created_at,
    updated_at: r.updated_at,
  })) {
    if (
      [
        "ports",
        "endpoints",
        "name",
        "alias",
        "description",
        "location",
      ].includes(k)
    )
      continue;
    const dt = document.createElement("dt"),
      dd = document.createElement("dd");
    dt.textContent = wireTechnicalName(k);
    dd.textContent =
      typeof v === "object" ? JSON.stringify(v) : String(v ?? "—");
    technical.append(dt, dd);
  }
  const raw = document.createElement("textarea");
  raw.readOnly = true;
  raw.rows = 15;
  raw.value = JSON.stringify(r, null, 2);
  raw.setAttribute("aria-label", window.LanctlI18n.t("LANCTL.UI.VIEW.JSON_RECORD"));
  const copy = wireAction(window.LanctlI18n.t("LANCTL.UI.TEXT.COPY_JSON"), async () => {
    try {
      await navigator.clipboard.writeText(raw.value);
      message(window.LanctlI18n.t("LANCTL.UI.VIEW.JSON_COPIED"));
    } catch {
      raw.focus();
      raw.select();
      if (!document.execCommand("copy"))
        throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_THE_TEXT_AND_PRESS_CTRL_C"));
    }
  });
  const center = wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.CENTER_IN_TOPOLOGY"), () =>
    wireCenterFromDetails(r),
  );
  showForm(
    window.LanctlI18n.t("LANCTL.UI.FRAGMENT.DETAILS") + labelOf(r),
    [
      ...(state.launcher === "lanwire" ? [center] : []),
      wireTabs([
        [window.LanctlI18n.t("LANCTL.UI.TEXT.GENERAL"), general],
        [window.LanctlI18n.t("LANCTL.UI.TEXT.LOCATION"), location],
        [window.LanctlI18n.t("LANCTL.UI.TEXT.PORTS"), [ports]],
        [window.LanctlI18n.t("LANCTL.UI.TEXT.CONNECTIONS"), [connections]],
        [window.LanctlI18n.t("LANCTL.UI.VIEW.TECHNICAL_DATA"), [...technicalFields, technical]],
        ["JSON", [copy, raw]],
      ]),
    ],
    (v) =>
      call("wire_update", r.id, r.revision, {
        name: v.name,
        alias: v.alias,
        description: v.description,
        connectionMode: v.connectionMode,
        ...physicalLocationValues(v, r),
        groups: v.groups
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean),
        ip: v.ip,
        speeds: v.speeds
          .split(",")
          .map((x) => x.trim())
          .filter(Boolean),
        ...(v.kind ? { kind: v.kind } : {}),
        ...(v.units && (Number(v.units) !== (d.units ?? d.size_units) || String(v.widthInches) !== String(d.rackDimensions?.widthInches || "")) ? { units: Number(v.units), widthInches: Number(v.widthInches) } : {}),
        portChanges: Object.fromEntries(
          Object.keys(d.ports || {}).map((p) => [
            p,
            { kind: v["port_kind_" + p], poe: v["port_poe_" + p] === "true" },
          ]),
        ),
      }),
  );
};
wireEdit = function (r) {
  if (state.launcher === "lanwire") return fullDetails(r);
  return wireBase.wireEdit(r);
};
async function wireOpenAfterSave(fn) {
  if (formOriginal !== JSON.stringify([...new FormData($("#detail-form"))])) {
    message(
      window.LanctlI18n.t("LANCTL.UI.VIEW.SAVE_OR_CANCEL_CHANGES_BEFORE_EDITING_PORTS_OR_CONNECTIONS"),
    );
    window.LanctlI18n.bindText($("#detail-error"),"LANCTL.UI.VIEW.SAVE_ELEMENT_CHANGES_FIRST");
    return;
  }
  await dismiss();
  if (!$("#detail").open) fn();
}
wirePort = function (r, p) {
  const ports = Object.keys(r.data.ports || {});
  p = p || ports[0];
  const fields = [
    field(
      window.LanctlI18n.t("LANCTL.UI.TEXT.PORT"),
      "port",
      p,
      "text",
      ports.map((x) => [x, x]),
    ),
    field(window.LanctlI18n.t("LANCTL.UI.TEXT.NEW_NAME"), "name", p),
    field(window.LanctlI18n.t("LANCTL.UI.TEXT.POSITION"), "position", ports.indexOf(p) + 1, "number"),
  ];
  fields[0].querySelector("select").onchange = (e) => {
    fields[1].querySelector("input").value = e.target.value;
    fields[2].querySelector("input").value = ports.indexOf(e.target.value) + 1;
  };
  showForm(window.LanctlI18n.t("LANCTL.UI.VIEW.RENAME_OR_REORDER_PORT"), fields, (v) =>
    call("wire_port", r.id, r.revision, v.port, v.name, Number(v.position)),
  );
};
function wirePortConnections(r, p) {
  const existing = wireConnections(r).find((w) =>
    w.data.endpoints.some((e) => e.device === r.id && e.port === p),
  );
  if (existing) {
    wireConnect(existing);
    return;
  }
  const cables = physicalInventory().filter(
    (w) => w.data.type === "wire" && (w.data.endpoints || []).length < 2,
  );
  showForm(
    window.LanctlI18n.t("LANCTL.UI.FRAGMENT.CONNECT_PORT") + r.id + " · " + p,
    [
      field(
        window.LanctlI18n.t("LANCTL.UI.VIEW.AVAILABLE_CABLE"),
        "wire",
        cables[0]?.id || "",
        "text",
        cables.map((w) => [w.id, labelOf(w)]),
      ),
    ],
    async (v) => {
      const w = physicalInventory().find((x) => x.id === v.wire);
      if (!w) throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.CREATE_A_CABLE_WITH_A_FREE_ENDPOINT_FIRST"));
      await call("wire_connect", w.id, w.revision, [
        ...(w.data.endpoints || []),
        { device: r.id, port: p },
      ]);
    },
  );
}
async function wireProjects() {
  const payload = await call("projects");
  showForm(
    window.LanctlI18n.t("LANCTL.UI.VIEW.CHANGE_PROJECT"),
    [
      field(
        window.LanctlI18n.t("LANCTL.UI.TEXT.PROJECT"),
        "project",
        state.project,
        "text",
        payload.projects.map((p) => [p.path, p.name]),
      ),
      wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.OPEN_VLF_FILE"), async () => {
        const result = await call("select_project_file");
        if (result.path)
          $("#detail-fields select").add(
            new Option(result.path, result.path, true, true),
          );
      }),
      Object.assign(document.createElement("p"), {
        textContent:
          window.LanctlI18n.t("LANCTL.UI.VIEW.THE_PROJECT_DEFINES_THE_SUITE_CONTEXT_PHYSICAL_LANWIRE_ELEMENTS_BELONG_TO_THE_SHARED_STORE_SHOW"),
      }),
    ],
    async (v) => {
      if (!v.project) throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_A_PROJECT"));
      if ((await call("project_state")).dirty) {
        if (
          !(await appDecision(
            window.LanctlI18n.t("LANCTL.UI.VIEW.THERE_ARE_PENDING_CHANGES_SAVE_THEM_BEFORE_SWITCHING_PROJECTS"),
          ))
        )
          throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.CHANGE_CANCELLED_THE_CURRENT_PROJECT_IS_PRESERVED"));
        await call("save_project");
      }
      await call("use_project", v.project);
      wireFocus = null;
      wirePositions = {};
      selected = null;
    },
  );
}
function wireTechnicalName(path) {
  const names = {
    type: window.LanctlI18n.t("LANCTL.UI.TEXT.TYPE"),
    subtype: window.LanctlI18n.t("LANCTL.UI.WORD.VARIANT"),
    kind: window.LanctlI18n.t("LANCTL.UI.WORD.MEDIUM"),
    groups: window.LanctlI18n.t("LANCTL.UI.TEXT.GROUPS"),
    ip: window.LanctlI18n.t("LANCTL.UI.TEXT.IP_ADDRESS"),
    speeds: window.LanctlI18n.t("LANCTL.UI.WORD.SPEEDS"),
    units: window.LanctlI18n.t("LANCTL.UI.VIEW.HEIGHT_IN_UNITS"),
    connectionMode: window.LanctlI18n.t("LANCTL.UI.VIEW.CONNECTION_TYPE"),
    created_at: window.LanctlI18n.t("LANCTL.UI.VIEW.CREATION_DATE"),
    updated_at: window.LanctlI18n.t("LANCTL.UI.VIEW.LAST_MODIFICATION"),
    portCount: window.LanctlI18n.t("LANCTL.UI.VIEW.NUMBER_OF_PORTS"),
    portNaming: window.LanctlI18n.t("LANCTL.UI.VIEW.PORT_NAMES"),
    portTemplate: window.LanctlI18n.t("LANCTL.UI.VIEW.PORT_TEMPLATE"),
    lanipDevice: window.LanctlI18n.t("LANCTL.UI.VIEW.LINKED_LANIP_DEVICE"),
    schemaVersion: window.LanctlI18n.t("LANCTL.UI.VIEW.FORMAT_VERSION"),
    active: window.LanctlI18n.t("LANCTL.UI.TEXT.ACTIVE"),
    directory: window.LanctlI18n.t("LANCTL.UI.WORD.FOLDER"),
    database: window.LanctlI18n.t("LANCTL.UI.VIEW.DATABASE"),
    devices: window.LanctlI18n.t("LANCTL.UI.TEXT.EQUIPMENT"),
    groups: window.LanctlI18n.t("LANCTL.UI.TEXT.GROUPS"),
    physical: window.LanctlI18n.t("LANCTL.UI.VIEW.PHYSICAL_INVENTORY"),
    saveMode: window.LanctlI18n.t("LANCTL.UI.TEXT.SAVE_MODE"),
    saveIntervalMinutes: window.LanctlI18n.t("LANCTL.UI.TEXT.SAVE_INTERVAL_MINUTES"),
    networkDatabase: window.LanctlI18n.t("LANCTL.UI.TEXT.NETWORK_INVENTORY"),
    networkGroups: window.LanctlI18n.t("LANCTL.UI.VIEW.NETWORK_GROUPS"),
    databaseLog: window.LanctlI18n.t("LANCTL.UI.VIEW.DATABASE_LOG"),
    credentials: window.LanctlI18n.t("LANCTL.UI.VIEW.CREDENTIAL_STORE"),
    iconsDirectory: window.LanctlI18n.t("LANCTL.UI.VIEW.ICON_FOLDER"),
    workspace: window.LanctlI18n.t("LANCTL.UI.VIEW.WORKSPACE"),
    project: window.LanctlI18n.t("LANCTL.UI.TEXT.PROJECT"),
    projectId: window.LanctlI18n.t("LANCTL.UI.VIEW.PROJECT_IDENTIFIER"),
    contentHash: window.LanctlI18n.t("LANCTL.UI.VIEW.CONTENT_FINGERPRINT"),
    metadata: window.LanctlI18n.t("LANCTL.UI.WORD.METADATA"),
    monitor: window.LanctlI18n.t("LANCTL.UI.WORD.MONITOR"),
    monitoring: window.LanctlI18n.t("LANCTL.UI.VIEW.MONITORING_67BC1FA5"),
    runtime: window.LanctlI18n.t("LANCTL.UI.VIEW.RUNTIME"),
    incidents: window.LanctlI18n.t("LANCTL.UI.TEXT.INCIDENTS"),
    lock: window.LanctlI18n.t("LANCTL.UI.WORD.LOCK"),
    profiles: window.LanctlI18n.t("LANCTL.UI.WORD.PROFILES"),
    assignments: window.LanctlI18n.t("LANCTL.UI.WORD.ASSIGNMENTS"),
    databases: window.LanctlI18n.t("LANCTL.UI.VIEW.DATABASES"),
    storage: window.LanctlI18n.t("LANCTL.UI.WORD.STORAGE"),
    projects: window.LanctlI18n.t("LANCTL.UI.TEXT.PROJECT"),
  };
  return path
    .split(".")
    .map(
      (k) =>
        names[k] || k.replace(/([a-z])([A-Z])/g, "$1 $2").replaceAll("_", " "),
    )
    .join(" › ");
}
settings = async function () {
  if (state.launcher !== "lanwire") return wireBase.settings();
  const payload = await call("settings");
  const general = [
      field(window.LanctlI18n.t("LANCTL.UI.VIEW.INITIAL_VIEW"), "pref_view", wirePrefs.view, "text", [
        ["map", window.LanctlI18n.t("LANCTL.UI.TEXT.TOPOLOGY")],
        ["list", window.LanctlI18n.t("LANCTL.UI.TEXT.LIST")],
      ]),
    ],
    list = [
      field(window.LanctlI18n.t("LANCTL.UI.VIEW.SORT_BY"), "pref_sort", wireSort.key, "text", [
        ["name", window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.NAME")],
        ["id", window.LanctlI18n.t("LANCTL.UI.HTML.IDENTIFIER")],
        ["type", window.LanctlI18n.t("LANCTL.UI.TEXT.TYPE")],
      ]),
    ],
    topology = [
      field(
        window.LanctlI18n.t("LANCTL.UI.VIEW.SHOW_NAMES_AND_LABELS"),
        "pref_labels",
        String(wirePrefs.labels),
        "text",
        [
          ["true", window.LanctlI18n.t("LANCTL.UI.TEXT.YES")],
          ["false", window.LanctlI18n.t("LANCTL.UI.TEXT.NO")],
        ],
      ),
      field(
        window.LanctlI18n.t("LANCTL.UI.VIEW.SHOW_WI_FI_LINKS"),
        "pref_showWifi",
        String(!!wirePrefs.showWifi),
        "text",
        [
          ["false", window.LanctlI18n.t("LANCTL.UI.TEXT.NO")],
          ["true", window.LanctlI18n.t("LANCTL.UI.TEXT.YES")],
        ],
      ),
      field(
        window.LanctlI18n.t("LANCTL.UI.VIEW.SHOW_MINIMAP"),
        "pref_minimap",
        String(wirePrefs.minimap),
        "text",
        [
          ["true", window.LanctlI18n.t("LANCTL.UI.TEXT.YES")],
          ["false", window.LanctlI18n.t("LANCTL.UI.TEXT.NO")],
        ],
      ),
      field(window.LanctlI18n.t("LANCTL.UI.VIEW.CONNECTION_LEVELS"), "pref_depth", wirePrefs.depth, "number"),
    ];
  const connectionsSettings = [
    field(
      window.LanctlI18n.t("LANCTL.UI.VIEW.DEFAULT_CONNECTION_FOR_NEW_ELEMENTS"),
      "pref_connectionMode",
      wirePrefs.connectionMode || "wired",
      "text",
      wireModes(),
    ),
    field(
      window.LanctlI18n.t("LANCTL.UI.VIEW.SHOW_PORTS_ON_CANVAS"),
      "pref_showPorts",
      String(wirePrefs.showPorts !== false),
      "text",
      [
        ["true", window.LanctlI18n.t("LANCTL.UI.TEXT.YES")],
        ["false", window.LanctlI18n.t("LANCTL.UI.TEXT.NO")],
      ],
    ),
  ];
  const sections = [
      [window.LanctlI18n.t("LANCTL.UI.TEXT.GENERAL"), general],
      [window.LanctlI18n.t("LANCTL.UI.VIEW.PORTS_AND_CONNECTIONS"), connectionsSettings],
      [window.LanctlI18n.t("LANCTL.UI.VIEW.LIST_AND_SEARCH"), list],
      [window.LanctlI18n.t("LANCTL.UI.TEXT.TOPOLOGY"), topology],
    ],
    entries = new Map();
  for (const category of ["storage", "projects", "logging"]) {
    const nodes = [];
    for (const e of payload.entries.filter((e) => e.category === category)) {
      const object = e.value === null || typeof e.value === "object",
        boolean = typeof e.value === "boolean";
      const f = field(
        wireTechnicalName(e.path),
        "setting_" + e.path,
        object ? JSON.stringify(e.value, null, 2) : String(e.value),
        object ? "textarea" : typeof e.value === "number" ? "number" : "text",
        boolean
          ? [
              ["true", window.LanctlI18n.t("LANCTL.UI.TEXT.ENABLED")],
              ["false", window.LanctlI18n.t("LANCTL.UI.TEXT.DISABLED")],
            ]
          : null,
      );
      const input = f.querySelector("input,select,textarea");
      input.disabled = !!e.readOnly;
      const note = document.createElement("small");
      note.textContent =
        e.readOnly ||
        window.LanctlI18n.t("LANCTL.UI.VIEW.SHARED_SUITE_SETTING_PATHS_APPLY_WHEN_REOPENING_THE_INTERFACE");
      f.append(note);
      if (!e.readOnly && /directory$/i.test(e.path)) {
        f.append(
          wireAction(window.LanctlI18n.t("LANCTL.UI.TEXT.CHOOSE_FOLDER"), async () => {
            const selected = await call("select_project_directory");
            if (selected.path) input.value = selected.path;
          }),
        );
      }
      nodes.push(f);
      entries.set("setting_" + e.path, e);
    }
    sections.push([
      category === "storage"
        ? window.LanctlI18n.t("LANCTL.UI.WORD.STORAGE")
        : category === "projects"
          ? window.LanctlI18n.t("LANCTL.UI.TEXT.PROJECT")
          : window.LanctlI18n.t("LANCTL.UI.TEXT.ADVANCED"),
      nodes,
    ]);
  }
  const search = field(window.LanctlI18n.t("LANCTL.UI.TEXT.SEARCH_SETTINGS"), "settings_search");
  const tabs = wireTabs(sections);
  search.querySelector("input").oninput = (e) => {
    const q = e.target.value.toLocaleLowerCase();
    tabs.querySelectorAll(".wire-tab-panel").forEach((p) => {
      p.hidden = !!q ? false : p !== tabs.querySelector(".wire-tab-panel");
      p.querySelectorAll("label").forEach(
        (l) =>
          (l.hidden = !!q && !l.textContent.toLocaleLowerCase().includes(q)),
      );
    });
  };
  const reset = wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.RESTORE_VISUAL_PREFERENCES"), () => {
    for (const [name, val] of Object.entries({
      pref_view: "map",
      pref_sort: "name",
      pref_labels: "true",
      pref_showWifi: "false",
      pref_minimap: "false",
      pref_depth: 1,
      pref_connectionMode: "wired",
      pref_showPorts: "true",
    }))
      tabs.querySelector(`[name="${name}"]`).value = val;
  });
  showForm(
    window.LanctlI18n.t("LANCTL.UI.VIEW.LANWIRE_SETTINGS"),
    [search, reset, tabs],
    async (values) => {
      const depth = Number(values.pref_depth);
      if (!Number.isInteger(depth) || depth < 1 || depth > 10)
        throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.LEVELS_MUST_BE_BETWEEN_1_AND_10"));
      for (const [key, e] of entries) {
        if (e.readOnly || !(key in values)) continue;
        const raw = values[key],
          value =
            typeof e.value === "boolean"
              ? raw === "true"
              : typeof e.value === "number"
                ? Number(raw)
                : e.value === null || typeof e.value === "object"
                  ? JSON.parse(raw)
                  : raw;
        if (JSON.stringify(value) !== JSON.stringify(e.value))
          await call("save_setting", e.path, value);
      }
      wirePrefs = {
        ...wirePrefs,
        view: values.pref_view,
        depth,
        labels: values.pref_labels === "true",
        showWifi: values.pref_showWifi === "true",
        minimap: values.pref_minimap === "true",
        connectionMode: values.pref_connectionMode,
        showPorts: values.pref_showPorts === "true",
      };
      wireSort.key = values.pref_sort;
      view = wirePrefs.view;
      wireStore();
    },
  );
};
document.addEventListener("click", (e) => {
  const b = e.target.closest("[data-nav]");
  if (b) wireNavigate(b.dataset.nav);
});
let wireLastSize = "";
new ResizeObserver(() => {
  if (state.launcher === "lanwire" && view === "map" && $("#wire-board")) {
    const size =
      $("#wire-board").clientWidth + ":" + $("#wire-board").clientHeight;
    if (size !== wireLastSize) {
      wireLastSize = size;
      wireFit();
    } else wirePaint();
  }
}).observe($("#canvas"));
wireNew = function (initialKind = "switch.24ports") {
  const choices = [
    ["switch.5ports", window.LanctlI18n.t("LANCTL.UI.VIEW.SWITCH_5_PORTS"), "SW"],
    ["switch.12ports", window.LanctlI18n.t("LANCTL.UI.VIEW.SWITCH_12_PORTS"), "SW"],
    ["switch.24ports", window.LanctlI18n.t("LANCTL.UI.VIEW.SWITCH_24_PORTS"), "SW"],
    ["switch.48ports", window.LanctlI18n.t("LANCTL.UI.VIEW.SWITCH_48_PORTS"), "SW"],
    ["router.gateway", window.LanctlI18n.t("LANCTL.UI.WORD.ROUTER"), "RT"],
    ["pc.1port", window.LanctlI18n.t("LANCTL.UI.VIEW.COMPUTER_1_PORT"), "PC"],
    ["pc.2ports", window.LanctlI18n.t("LANCTL.UI.VIEW.COMPUTER_2_PORTS"), "PC"],
    ["server.2ports", window.LanctlI18n.t("LANCTL.UI.VIEW.SERVER_2_PORTS"), "SR"],
    ["tray", window.LanctlI18n.t("LANCTL.UI.VIEW.DEVICE_TRAY"), "TR"],
    ["router.otg", "OTG", "OT"],
    ["panel", window.LanctlI18n.t("LANCTL.UI.VIEW.PATCH_PANEL_24_PORTS"), "PN"],
    ["outlet", window.LanctlI18n.t("LANCTL.UI.VIEW.NETWORK_OUTLET_WALL_AND_ROOM"), "PX"],
    ["wire.copper", window.LanctlI18n.t("LANCTL.UI.TEXT.COPPER_CABLE"), "WL"],
    ["wire.fiber", window.LanctlI18n.t("LANCTL.UI.TEXT.FIBER_CABLE"), "FB"],
    ["wire.dac", window.LanctlI18n.t("LANCTL.UI.VIEW.DAC_CABLE"), "WL"],
    ["rack", window.LanctlI18n.t("LANCTL.UI.WORD.RACK"), "RK"],
  ];
  const fields = [
    field(
      window.LanctlI18n.t("LANCTL.UI.TEXT.TYPE"),
      "kind",
      initialKind,
      "text",
      choices.map(([v, l]) => [v, l]),
    ),
    field(window.LanctlI18n.t("LANCTL.UI.VIEW.IDENTIFIER_PREFIX"), "prefix", "SW"),
    field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.NAME"), "name"),
    field(window.LanctlI18n.t("LANCTL.UI.WORD.ALIAS"), "alias"),
    field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.DESCRIPTION"), "description", "", "textarea"),
    field(
      window.LanctlI18n.t("LANCTL.UI.VIEW.CONNECTION_TYPE"),
      "connectionMode",
      wirePrefs.connectionMode || "wired",
      "text",
      wireModes(),
    ),
    field(window.LanctlI18n.t("LANCTL.UI.VIEW.RACK_HEIGHT_UNITS"), "units", 42, "number"),
    field(window.LanctlI18n.t("LANCTL.UI.VIEW.MOUNTING_WIDTH_INCHES"), "widthInches", 19, "text", [
      [10, "10″"],
      [19, "19″"],
      [21, "21″"],
      [23, "23″"],
    ]),
  ];
  const heightField = fields.at(-2), widthField = fields.at(-1);
  const height = heightField.querySelector("input");
  const endpoints = [["", window.LanctlI18n.t("LANCTL.UI.TEXT.NOT_CONNECTED")], ...physicalInventory().flatMap(r => Object.keys(r.data.ports || {}).map(port => [JSON.stringify({device: r.id, port}), `${r.data.name || r.id} · ${port}`]))];
  const endFields = [field(window.LanctlI18n.t("LANCTL.UI.VIEW.ENDPOINT_A"), "endpointA", "", "text", endpoints), field(window.LanctlI18n.t("LANCTL.UI.VIEW.ENDPOINT_B"), "endpointB", "", "text", endpoints)];
  fields.push(...endFields);
  height.min = 4;
  height.max = 52;
  height.step = 1;
  const change = () => {
    const kind = fields[0].querySelector("select").value;
    fields[1].querySelector("input").value = choices.find(
      (x) => x[0] === kind,
    )[2];
    widthField.hidden = heightField.hidden = kind !== "rack";
    height.disabled = widthField.querySelector("select").disabled = kind !== "rack";
    const cable = kind.startsWith("wire.");
    endFields.forEach(f => { f.hidden = !cable; f.querySelector("select").disabled = !cable; });
    fields[5].hidden = cable || kind === "rack";
    height.required = kind === "rack";
  };
  fields[0].querySelector("select").onchange = change;
  change();
  showForm(initialKind.startsWith("wire.") ? window.LanctlI18n.t("LANCTL.UI.TEXT.NEW_CABLE") : initialKind === "rack" ? window.LanctlI18n.t("LANCTL.UI.TEXT.NEW_RACK") : window.LanctlI18n.t("LANCTL.UI.TEXT.NEW_PHYSICAL_ELEMENT"), fields, async (values) => {
    const { units, widthInches, endpointA, endpointB, ...data } = values;
    const result = await call("wire_create", {
      ...data,
      ...(values.kind.startsWith("wire.") ? {connectionMode: "wired", endpoints: [endpointA, endpointB].filter(Boolean).map(v => JSON.parse(v))} : {}),
      ...(values.kind === "rack"
        ? { units: Number(units), widthInches: Number(widthInches) }
        : {}),
    });
    if (state.launcher !== "lanrack" || values.kind === "rack") selected = result.id;
    if (state.launcher === "lanwire") {
      wireClearFilters(); physicalRack = ""; physicalCpd = ""; wireFocus = null;
      // Cables without both endpoints remain inspectable in the inventory list.
      view = values.kind.startsWith("wire.") ? "list" : view;
      if (values.kind === "rack") physicalLevel = "outside";
      selected = result.id;
    }
  });
};
function wireResizeColumns() {
  document.querySelectorAll("#canvas th").forEach((th) => {
    const key = th.textContent;
    const saved = wirePrefs.widths?.[key];
    if (saved) th.style.width = saved + "px";
    const grip = document.createElement("span");
    grip.className = "wire-column-grip";
    grip.title = window.LanctlI18n.t("LANCTL.UI.VIEW.DRAG_TO_CHANGE_WIDTH");
    th.append(grip);
    grip.onpointerdown = (e) => {
      e.preventDefault();
      e.stopPropagation();
      const start = e.clientX,
        width = th.getBoundingClientRect().width;
      grip.setPointerCapture(e.pointerId);
      grip.onpointermove = (ev) => {
        th.style.width = Math.max(90, width + ev.clientX - start) + "px";
      };
      grip.onpointerup = () => {
        wirePrefs.widths = {
          ...wirePrefs.widths,
          [key]: th.getBoundingClientRect().width,
        };
        wireStore();
        grip.onpointermove = null;
      };
    };
  });
}
