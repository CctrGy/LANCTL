/* Shared placement forms. Rules and occupancy are enforced by Core/storage. */
function physicalInventory() {
  return state.launcher === "lanrack" ? state.elements || [] : state.records;
}

const physicalEditorContext = wireContext;
wireContext = function(r) {
  physicalEditorContext(r);
  if (r.data.type === "rack") $("#detail-fields").append(wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.VIEW_RACK_INTERIOR"), () => {
    $("#detail").close();
    physicalSwitchLevel("inside", r.id);
  }));
};
function physicalPlacementLabel(r) {
  const p = r.placement || {};
  if (p.needsReview) return window.LanctlI18n.t("LANCTL.UI.VIEW.LOCATION_PENDING_REVIEW");
  if (p.kind === "hosted") return window.LanctlI18n.t("LANCTL.UI.WEB.IN_TRAY_VALUE0_VALUE1_U_VALUE2",{value0:(p.tray),value1:(p.rack),value2:(p.unit)});
  if (p.kind === "inside") return `${p.rack} · U${p.unit} · ${r.data.rackAppearance?.units || 1} U`;
  if (p.kind === "environment") return window.LanctlI18n.t("LANCTL.UI.WEB.ENVIRONMENT_OF_VALUE0",{value0:(p.rack)});
  return window.LanctlI18n.t("LANCTL.UI.WORD.STANDALONE");
}
function physicalLocationFields(r) {
  if (state.launcher === "lanwire" && r.placement?.kind === "hosted") return [Object.assign(document.createElement("p"), {textContent: window.LanctlI18n.t("LANCTL.PHYSICAL.LOCATION.IN_LANRACK")})];
  if (["rack", "wire"].includes(r.data.type)) return [];
  const p = r.placement || {kind: "independent"}, location = r.data.location || {};
  const fields = [
    field(window.LanctlI18n.t("LANCTL.UI.VIEW.CLASSIFICATION"), "placement", p.needsReview ? "review" : p.kind, "text", [
      ["review", window.LanctlI18n.t("LANCTL.UI.VIEW.REVIEW_LOCATION")], ["inside", window.LanctlI18n.t("LANCTL.UI.VIEW.RACK_INTERIOR")],
      ["environment", window.LanctlI18n.t("LANCTL.UI.VIEW.RACK_ENVIRONMENT")], ["independent", window.LanctlI18n.t("LANCTL.UI.WORD.STANDALONE")],
      ["hosted", window.LanctlI18n.t("LANCTL.UI.VIEW.HOUSED_IN_A_TRAY")],
    ]),
    field(window.LanctlI18n.t("LANCTL.UI.WORD.RACK"), "rack", location.rack || "", "text", [["", window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_RACK")],
      ...physicalInventory().filter(x => x.data.type === "rack").map(x => [x.id, x.data.name || x.id])]),
    field(window.LanctlI18n.t("LANCTL.UI.VIEW.STARTING_UNIT"), "unit", location.unit || 1, "number"),
    field(window.LanctlI18n.t("LANCTL.UI.VIEW.OCCUPIED_HEIGHT_U"), "heightU", r.data.rackAppearance?.units || 1, "number"),
    field(window.LanctlI18n.t("LANCTL.UI.WORD.TRAY"), "tray", location.tray || "", "text", [["", window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_TRAY")],
      ...physicalInventory().filter(x => ["tray", "device.tray", "rack.raspberry-pi-panel"].includes(x.data.type) && x.id !== r.id && x.placement?.kind === "inside").map(x => [x.id, `${x.data.name || x.id} · ${physicalPlacementLabel(x)}`])]),
  ];
  for (const name of ["unit", "heightU"]) {
    const input = fields.find(f => f.querySelector(`[name=${name}]`)).querySelector("input");
    input.min = 1; input.max = 52; input.step = 1;
    if (name === "heightU" && r.data.type === "rack.raspberry-pi-panel") {input.value = 1;input.max = 1;input.readOnly = true;}
  }
  const update = () => {
    const mode = fields[0].querySelector("select").value;
    fields[1].hidden = !["inside", "environment", "review"].includes(mode);
    fields[2].hidden = !["inside", "review"].includes(mode);
    fields[3].hidden = mode === "hosted";
    fields[4].hidden = mode !== "hosted";
  };
  if (r.directMount === false) {
    const inside = fields[0].querySelector('option[value="inside"]');
    inside.disabled = true;
    inside.textContent += " · " + window.LanctlI18n.t("LANCTL.PHYSICAL.MOUNT.TRAY_REQUIRED");
  }
  if (state.launcher === "lanwire") fields[0].querySelector('option[value="hosted"]')?.remove();
  fields[0].querySelector("select").onchange = update;
  update();
  return fields;
}
function physicalLocationValues(v, r) {
  if (state.launcher === "lanwire" && r.placement?.kind === "hosted") return {};
  if (["rack", "wire"].includes(r.data.type)) return {};
  if (v.placement === "review") {
    if (v.rack !== (r.data.location?.rack || "") || Number(v.unit) !== (r.data.location?.unit || 1) || Number(v.heightU) !== (r.data.rackAppearance?.units || 1))
      throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_AN_EXPLICIT_CLASSIFICATION_TO_CORRECT_THE_LOCATION"));
    return {};
  }
  if (["inside", "environment"].includes(v.placement) && !v.rack) throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_A_RACK"));
  if (v.placement === "hosted" && !v.tray) throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_A_TRAY"));
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
  const note = Object.assign(document.createElement("p"), {textContent: window.LanctlI18n.t("LANCTL.UI.FRAGMENT.CURRENT") + physicalPlacementLabel(r)});
  const height = field(window.LanctlI18n.t("LANCTL.UI.VIEW.OCCUPIED_HEIGHT_U"), "heightU", r.data.rackAppearance?.units || 1, "number");
  const destination = field(window.LanctlI18n.t("LANCTL.UI.VIEW.AVAILABLE_DESTINATIONS"), "destination", "", "text", []);
  const input = height.querySelector("input"), select = destination.querySelector("select");
  input.min = 1; input.max = 52; input.step = 1; select.required = true;
  if (r.data.type === "rack.raspberry-pi-panel") {input.max = 1;input.readOnly = true;}
  let sequence = 0;
  async function load() {
    const current = ++sequence;
    select.disabled = true;
    try {
      const result = await call("rack_destinations", r.id, Number(input.value));
      if (sequence !== current || !$("#detail").open) return;
      select.replaceChildren(...result.destinations.map(d => new Option(`${d.rack} · U${d.unit}`, `${d.rack}|${d.unit}`)));
      if (!select.options.length) select.add(new Option(window.LanctlI18n.t("LANCTL.UI.VIEW.NO_AVAILABLE_SPACE"), ""));
      const old = `${r.placement?.rack}|${r.placement?.unit}`;
      if ([...select.options].some(o => o.value === old)) select.value = old;
      select.disabled = false;
      if (current === 1) formOriginal = JSON.stringify([...new FormData($("#detail-form"))]);
    } catch (e) { $("#detail-error").textContent = e.message; }
  }
  showForm(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.MOVE_ELEMENT") + (r.data.name || r.id), [note, height, destination], async v => {
    if (select.disabled || !v.destination) throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_AN_AVAILABLE_DESTINATION"));
    const [rack, unit] = v.destination.split("|");
    return call("rack_element", state.organizationRevision, "update", r.id, {rack, unit: Number(unit), in_rack: true, tray: null, heightU: Number(v.heightU)});
  });
  input.onchange = load;
  await load();
}

function physicalCreateInTray(r) {
  const context = JSON.stringify(state.projectContext), revision = state.organizationRevision;
  if (r.data.type === "rack.raspberry-pi-panel" && physicalInventory().filter(x => x.data.location?.tray === r.id).length >= 5)
    throw Error(window.LanctlI18n.t("LANCTL.RACK.PI_PANEL.FULL"));
  wireNew(r.data.type === "rack.raspberry-pi-panel" ? "raspberry-pi" : "router.gateway", {tray: r.id, rack: null, unit: 0, in_rack: false}, r.data.type);
  const submit = formSubmit;
  formSubmit = values => {
    if (context !== JSON.stringify(state.projectContext) || revision !== state.organizationRevision)
      throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.THE_PROJECT_CHANGED_RELOAD_THE_RECORD"));
    return submit(values);
  };
}
function physicalHostDevice(r) {
  const context = JSON.stringify(state.projectContext), revision = state.organizationRevision;
  const piPanel = r.data.type === "rack.raspberry-pi-panel";
  const count = physicalInventory().filter(x => x.data.location?.tray === r.id).length;
  const full = piPanel && count >= 5;
  const compatiblePi = x => {
    const ports = Object.values(x.data.ports || {});
    return ports.length === 1 && ["connection.rj45", "wire.copper"].includes(ports[0].kind) || !ports.length && ["element", "device.raspberry-pi"].includes(x.data.type || "element");
  };
  const available = physicalInventory().filter(x => !full && x.id !== r.id && !["rack", "wire", "tray", "device.tray", "rack.raspberry-pi-panel"].includes(x.data.type) && (piPanel ? compatiblePi(x) : x.directMount === false) && (x.data.rackAppearance?.units || 1) <= (r.data.rackAppearance?.units || 1) && x.data.location?.tray !== r.id);
  const selector = field(window.LanctlI18n.t("LANCTL.UI.TEXT.DEVICE_1C555EB7"), "device", available[0]?.id || "", "text", available.map(x => [x.id, `${x.data.name || x.id} · ${physicalPlacementLabel(x)}`]));
  const note = Object.assign(document.createElement("p"), {textContent: window.LanctlI18n.t(available.length ? "LANCTL.RACK.TRAY.EXISTING_HINT" : "LANCTL.RACK.TRAY.EMPTY")});
  if (piPanel) note.textContent = window.LanctlI18n.t("LANCTL.RACK.PI_PANEL.CAPACITY", {used:count}) + (full ? " · " + window.LanctlI18n.t("LANCTL.RACK.PI_PANEL.FULL") : "");
  note.dataset.trayHint = "";
  const create = wireAction(window.LanctlI18n.t("LANCTL.RACK.TRAY.CREATE_INSIDE"), () => wireOpenAfterSave(() => physicalCreateInTray(r)));
  create.dataset.trayCreate = r.id;
  create.disabled = full;
  function guard() {
    if (context !== JSON.stringify(state.projectContext) || revision !== state.organizationRevision)
      throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.THE_PROJECT_CHANGED_RELOAD_THE_RECORD"));
  }
  showForm(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.HOST_DEVICE_IN") + (r.data.name || r.id), [note, selector, create], async v => {
    guard();
    const child = available.find(x => x.id === v.device);
    if (!child) throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.NO_DEVICES_AVAILABLE"));
    if (child.placement?.kind !== "independent" && !await appDecision(window.LanctlI18n.t("LANCTL.RACK.UNIT.CONFIRM_MOVE", {element: child.id, origin: physicalPlacementLabel(child), destination: r.data.name || r.id})))
      throw Error(window.LanctlI18n.t("LANCTL.RACK.UNIT.CANCELLED"));
    guard();
    return call("rack_element", revision, "update", child.id, {tray: r.id});
  });
  if (!available.length) { selector.querySelector("select").disabled = true; $("#submit").hidden = true; }
}

rackOccupantDetails = function(item) {
  const r = physicalInventory().find(x => x.id === item.id);
  if (!r) return;
  fullDetails(r);
  if (r.data.type === "rack.raspberry-pi-panel") $("#detail-fields").append(Object.assign(document.createElement("p"), {textContent:window.LanctlI18n.t("LANCTL.RACK.PI_PANEL.CAPACITY",{used:physicalInventory().filter(x => x.data.location?.tray === r.id).length})}));
  const actions = document.createElement("div"); actions.className = "row";
  actions.append(wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.MOVE_ELEMENT"), () => wireOpenAfterSave(() => physicalMove(r))),
    wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.CUSTOMIZE_FRONT"), () => wireOpenAfterSave(() => rackSkinEditor(r))));
  if (["tray", "device.tray", "rack.raspberry-pi-panel"].includes(r.data.type) && r.placement?.kind === "inside") {
    actions.append(wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.HOUSE_DEVICE"), () => wireOpenAfterSave(() => {
      physicalHostDevice(r);
    })));
  }
  const children = physicalInventory().filter(x => x.data.location?.tray === r.id);
  for (const child of children) actions.append(wireAction(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.HOSTED") + (child.data.name || child.id), () => wireOpenAfterSave(() => rackOccupantDetails(child))));
  actions.append(wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.DELETE_ELEMENT"), async () => {
    if (await appDecision(window.LanctlI18n.t("LANCTL.UI.VIEW.DELETE_THIS_ELEMENT_HOUSED_DEVICES_MUST_BE_RELOCATED_FIRST"))) {
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
      wireAction(window.LanctlI18n.t("LANCTL.UI.TEXT.NEW_CABLE"), () => wireNew("wire.copper")),
      wireAction(window.LanctlI18n.t("LANCTL.UI.TEXT.NEW_RACK"), () => wireNew("rack")),
      wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.NEW_DATA_CENTER"), () => rackRoomForm()),
    );
    if (state.cpds?.length) $("#commands").append(wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.EDIT_DATA_CENTER"), () => {
      showForm(window.LanctlI18n.t("LANCTL.UI.VIEW.DATA_CENTER_ROOMS"), state.cpds.map(room => wireAction(room.name, () => rackRoomForm(room))));
    }));
    const rack = state.records.find(r => r.id === selected && r.data.type === "rack");
    if (rack) $("#commands").append(wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.CHANGE_DATA_CENTER"), () => rackAssign({id: rack.id, name: rack.data.name || rack.id, location: rack.data.location})));
    return;
  }
  if (state.launcher !== "lanrack") return;
  $("#tools").append(wireAction(window.LanctlI18n.t("LANCTL.UI.TEXT.NEW_DEVICE"), wireNew));
  const rack = state.records.find(x => x.id === selected);
  if (rack) $("#commands").append(wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.EDIT_DATA"), () => fullDetails(physicalInventory().find(x => x.id === rack.id))));
  if (rack && rackMode === "rack") {
    for (const item of rack.layout || []) {
      if (item.kind !== "tray" || item.idf) continue;
      $("#canvas").append(wireAction(window.LanctlI18n.t("LANCTL.UI.WEB.CONVERT_LEGACY_TRAY_U_VALUE0",{value0:(item.unit)}), async () => {
        await call("rack_element", state.organizationRevision, "import-tray", rack.id, {unit: item.unit});
        await refresh();
      }));
    }
  }
  const query = $("#search").value.toLocaleLowerCase();
  const items = physicalInventory().filter(x => !["rack", "wire"].includes(x.data.type) && (!query || JSON.stringify(x).toLocaleLowerCase().includes(query)));
  const groups = [
    [window.LanctlI18n.t("LANCTL.UI.VIEW.RACK_ENVIRONMENT"), items.filter(x => x.placement?.kind === "environment" && (rackMode !== "rack" || x.placement.rack === selected))],
    [window.LanctlI18n.t("LANCTL.UI.VIEW.DEVICES_HOUSED_IN_TRAYS"), items.filter(x => x.placement?.kind === "hosted" && !x.placement.needsReview && (rackMode !== "rack" || x.placement.rack === selected))],
    [window.LanctlI18n.t("LANCTL.UI.VIEW.STANDALONE_ELEMENTS"), items.filter(x => x.placement?.kind === "independent")],
    [window.LanctlI18n.t("LANCTL.UI.VIEW.LOCATIONS_PENDING_REVIEW"), items.filter(x => x.placement?.needsReview)],
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
  for (const tray of items.filter(x => ["tray", "device.tray", "rack.raspberry-pi-panel"].includes(x.data.type))) {
    const button = [...document.querySelectorAll("[data-rack-occupant]")].find(b => b.dataset.rackOccupant === tray.id);
    const children = items.filter(x => x.data.location?.tray === tray.id);
    if (button && children.length && !button.querySelector(".rack-face")) button.append(Object.assign(document.createElement("small"), {textContent: children.map(x => x.data.name || x.id).join(" · ")}));
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
