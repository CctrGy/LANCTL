/* Shared placement forms. Rules and occupancy are enforced by Core/storage. */
function physicalInventory() {
  return state.launcher === "lanrack" ? state.elements || [] : state.records;
}

const physicalEditorContext = wireContext;
wireContext = function(r) {
  physicalEditorContext(r);
  if (r.data.type === "rack") $("#detail-fields").append(wireAction("Ver interior del rack", () => {
    $("#detail").close();
    physicalSwitchLevel("inside", r.id);
  }));
};
function physicalPlacementLabel(r) {
  const p = r.placement || {};
  if (p.needsReview) return "Ubicación pendiente de revisión";
  if (p.kind === "hosted") return `En bandeja ${p.tray} · ${p.rack} · U${p.unit}`;
  if (p.kind === "inside") return `${p.rack} · U${p.unit} · ${r.data.rackAppearance?.units || 1} U`;
  if (p.kind === "environment") return `Entorno de ${p.rack}`;
  return "Independiente";
}
function physicalLocationFields(r) {
  if (["rack", "wire"].includes(r.data.type)) return [];
  const p = r.placement || {kind: "independent"}, location = r.data.location || {};
  const fields = [
    field("Clasificación", "placement", p.needsReview ? "review" : p.kind, "text", [
      ["review", "Revisar ubicación"], ["inside", "Interior del rack"],
      ["environment", "Entorno del rack"], ["independent", "Independiente"],
      ["hosted", "Alojado en bandeja"],
    ]),
    field("Rack", "rack", location.rack || "", "text", [["", "Seleccionar rack"],
      ...physicalInventory().filter(x => x.data.type === "rack").map(x => [x.id, x.data.name || x.id])]),
    field("Unidad inicial", "unit", location.unit || 1, "number"),
    field("Altura ocupada (U)", "heightU", r.data.rackAppearance?.units || 1, "number"),
    field("Bandeja", "tray", location.tray || "", "text", [["", "Seleccionar bandeja"],
      ...physicalInventory().filter(x => ["tray", "device.tray"].includes(x.data.type) && x.id !== r.id && x.placement?.kind === "inside").map(x => [x.id, `${x.data.name || x.id} · ${physicalPlacementLabel(x)}`])]),
  ];
  for (const name of ["unit", "heightU"]) {
    const input = fields.find(f => f.querySelector(`[name=${name}]`)).querySelector("input");
    input.min = 1; input.max = 52; input.step = 1;
  }
  const update = () => {
    const mode = fields[0].querySelector("select").value;
    fields[1].hidden = !["inside", "environment", "review"].includes(mode);
    fields[2].hidden = !["inside", "review"].includes(mode);
    fields[3].hidden = mode === "hosted";
    fields[4].hidden = mode !== "hosted";
  };
  fields[0].querySelector("select").onchange = update;
  update();
  return fields;
}
function physicalLocationValues(v, r) {
  if (["rack", "wire"].includes(r.data.type)) return {};
  if (v.placement === "review") {
    if (v.rack !== (r.data.location?.rack || "") || Number(v.unit) !== (r.data.location?.unit || 1) || Number(v.heightU) !== (r.data.rackAppearance?.units || 1))
      throw Error("Selecciona una clasificación explícita para corregir la ubicación.");
    return {};
  }
  if (["inside", "environment"].includes(v.placement) && !v.rack) throw Error("Selecciona un rack.");
  if (v.placement === "hosted" && !v.tray) throw Error("Selecciona una bandeja.");
  return {rack: ["inside", "environment"].includes(v.placement) ? v.rack : null,
    in_rack: v.placement === "inside", unit: v.placement === "inside" ? Number(v.unit) : 0,
    tray: v.placement === "hosted" ? v.tray : null, heightU: Number(v.heightU)};
}

// Keep the LANWIRE editor, including real ports and connections, in LANRACK.
const physicalEditorCall = call;
call = function(method, ...args) {
  if (state.launcher === "lanrack" && method.startsWith("wire_")) {
    const [id, revision, values, name, position] = args;
    const operation = method.slice(5);
    const payload = operation === "create" ? id : operation === "connect" ? {endpoints: values} : operation === "port" ? {port: values, name, position} : values || {};
    return physicalEditorCall("rack_element", state.organizationRevision, operation, operation === "create" ? "" : id, payload);
  }
  return physicalEditorCall(method, ...args);
};

async function physicalMove(r) {
  const note = Object.assign(document.createElement("p"), {textContent: "Actual: " + physicalPlacementLabel(r)});
  const height = field("Altura ocupada (U)", "heightU", r.data.rackAppearance?.units || 1, "number");
  const destination = field("Destinos disponibles", "destination", "", "text", []);
  const input = height.querySelector("input"), select = destination.querySelector("select");
  input.min = 1; input.max = 52; input.step = 1; select.required = true;
  let sequence = 0;
  async function load() {
    const current = ++sequence;
    select.disabled = true;
    try {
      const result = await call("rack_destinations", r.id, Number(input.value));
      if (sequence !== current || !$("#detail").open) return;
      select.replaceChildren(...result.destinations.map(d => new Option(`${d.rack} · U${d.unit}`, `${d.rack}|${d.unit}`)));
      if (!select.options.length) select.add(new Option("Sin espacio disponible", ""));
      const old = `${r.placement?.rack}|${r.placement?.unit}`;
      if ([...select.options].some(o => o.value === old)) select.value = old;
      select.disabled = false;
      if (current === 1) formOriginal = JSON.stringify([...new FormData($("#detail-form"))]);
    } catch (e) { $("#detail-error").textContent = e.message; }
  }
  showForm("Mover elemento · " + (r.data.name || r.id), [note, height, destination], async v => {
    if (select.disabled || !v.destination) throw Error("Selecciona un destino disponible.");
    const [rack, unit] = v.destination.split("|");
    return call("rack_element", state.organizationRevision, "update", r.id, {rack, unit: Number(unit), in_rack: true, tray: null, heightU: Number(v.heightU)});
  });
  input.onchange = load;
  await load();
}

rackOccupantDetails = function(item) {
  const r = physicalInventory().find(x => x.id === item.id);
  if (!r) return;
  fullDetails(r);
  const actions = document.createElement("div"); actions.className = "row";
  actions.append(wireAction("Mover elemento", () => wireOpenAfterSave(() => physicalMove(r))),
    wireAction("Personalizar frente", () => wireOpenAfterSave(() => rackSkinEditor(r))));
  if (["tray", "device.tray"].includes(r.data.type) && r.placement?.kind === "inside") {
    actions.append(wireAction("Alojar dispositivo", () => wireOpenAfterSave(() => {
      const available = physicalInventory().filter(x => !["rack", "wire", "tray", "device.tray"].includes(x.data.type) && x.data.location?.tray !== r.id);
      showForm("Alojar dispositivo en " + (r.data.name || r.id), [field("Dispositivo", "device", available[0]?.id || "", "text", available.map(x => [x.id, `${x.data.name || x.id} · ${physicalPlacementLabel(x)}`]))], v => {
        const child = available.find(x => x.id === v.device);
        if (!child) throw Error("No hay dispositivos disponibles.");
        return call("wire_update", child.id, child.revision, {tray: r.id});
      });
    })));
  }
  const children = physicalInventory().filter(x => x.data.location?.tray === r.id);
  for (const child of children) actions.append(wireAction("Alojado: " + (child.data.name || child.id), () => wireOpenAfterSave(() => rackOccupantDetails(child))));
  actions.append(wireAction("Eliminar elemento", async () => {
    if (await appDecision("¿Eliminar este elemento? Los dispositivos alojados deben reubicarse primero.")) {
      await call("wire_delete", r.id, r.revision); $("#detail").close(); await refresh();
    }
  }));
  $("#detail-fields").prepend(Object.assign(document.createElement("p"), {textContent: physicalPlacementLabel(r)}), actions);
};

const physicalEditorBaseRender = render;
render = function() {
  physicalEditorBaseRender();
  if (state.launcher === "lanwire") {
    $("#tools").append(
      wireAction("Nuevo cable", () => wireNew("wire.copper")),
      wireAction("Nuevo rack", () => wireNew("rack")),
      wireAction("Nuevo CPD", () => rackRoomForm()),
    );
    if (state.cpds?.length) $("#commands").append(wireAction("Editar CPD", () => {
      showForm("Salas CPD", state.cpds.map(room => wireAction(room.name, () => rackRoomForm(room))));
    }));
    const rack = state.records.find(r => r.id === selected && r.data.type === "rack");
    if (rack) $("#commands").append(wireAction("Cambiar CPD", () => rackAssign({id: rack.id, name: rack.data.name || rack.id, location: rack.data.location})));
    return;
  }
  if (state.launcher !== "lanrack") return;
  $("#tools").append(wireAction("Nuevo elemento", wireNew));
  const rack = state.records.find(x => x.id === selected);
  if (rack) $("#commands").append(wireAction("Editar datos", () => fullDetails(physicalInventory().find(x => x.id === rack.id))));
  if (rack && rackMode === "rack") {
    for (const item of rack.layout || []) {
      if (item.kind !== "tray" || item.idf) continue;
      $("#canvas").append(wireAction(`Convertir bandeja heredada · U${item.unit}`, async () => {
        await call("rack_element", state.organizationRevision, "import-tray", rack.id, {unit: item.unit});
        await refresh();
      }));
    }
  }
  const query = $("#search").value.toLocaleLowerCase();
  const items = physicalInventory().filter(x => !["rack", "wire"].includes(x.data.type) && (!query || JSON.stringify(x).toLocaleLowerCase().includes(query)));
  const groups = [
    ["Entorno del rack", items.filter(x => x.placement?.kind === "environment" && (rackMode !== "rack" || x.placement.rack === selected))],
    ["Dispositivos alojados en bandejas", items.filter(x => x.placement?.kind === "hosted" && !x.placement.needsReview && (rackMode !== "rack" || x.placement.rack === selected))],
    ["Elementos independientes", items.filter(x => x.placement?.kind === "independent")],
    ["Ubicaciones pendientes de revisión", items.filter(x => x.placement?.needsReview)],
  ];
  for (const [title, records] of groups) {
    if (!records.length) continue;
    const section = document.createElement("section"); section.className = "panel physical-elements";
    section.append(Object.assign(document.createElement("h2"), {textContent: title}));
    for (const r of records) {
      const b = wireAction(`${r.data.name || r.id} · ${r.id} · ${physicalPlacementLabel(r)}`, () => rackOccupantDetails(r));
      b.dataset.physicalElement = r.id; section.append(b);
    }
    $("#canvas").append(section);
  }
  for (const tray of items.filter(x => ["tray", "device.tray"].includes(x.data.type))) {
    const button = [...document.querySelectorAll("[data-rack-occupant]")].find(b => b.dataset.rackOccupant === tray.id);
    const children = items.filter(x => x.data.location?.tray === tray.id);
    if (button && children.length) button.append(Object.assign(document.createElement("small"), {textContent: children.map(x => x.data.name || x.id).join(" · ")}));
  }
};

const physicalEditorBaseRefresh = refresh;
refresh = async function() {
  const previous = state.projectContext && JSON.stringify(state.projectContext);
  await physicalEditorBaseRefresh();
  if (!previous || previous === JSON.stringify(state.projectContext)) return;
  if (state.launcher === "lanrack") {
    rackCpd = ""; $("#filter").value = "";
  } else if (state.launcher === "lanwire") {
    physicalRack = ""; physicalCpd = ""; wireFilter.rack = "";
    wireFocus = null; wireHidden.clear();
  }
  render();
};
