/* Unit actions reuse the shared inventory transaction and project guard. */
let rackUnitMenuClose = () => {};
function rackUnitMenu(button, point = null) {
  rackUnitMenuClose();
  if (state.launcher !== "lanrack") return;
  const rack = button.dataset.rackId, unit = Number(button.dataset.rackUnit);
  const context = JSON.stringify(state.projectContext), revision = state.organizationRevision;
  const occupant = physicalInventory().find(r => r.id === button.dataset.rackOccupant);
  const t = key => window.LanctlI18n.t(key);
  function guard() {
    if (context !== JSON.stringify(state.projectContext) || revision !== state.organizationRevision)
      throw Error(t("LANCTL.UI.VIEW.THE_PROJECT_CHANGED_RELOAD_THE_RECORD"));
  }
  const action = (label, fn) => wireAction(label, async () => {
    try { guard(); rackUnitMenuClose(); await fn(); }
    catch (error) { message(error.message, true); }
  });
  const actions = [];
  if (occupant) {
    actions.push(action(t("LANCTL.RACK.UNIT.DETAILS"), () => {
      const pre = Object.assign(document.createElement("pre"), {textContent: JSON.stringify(occupant, null, 2)});
      showForm(occupant.data.name || occupant.id, [pre]);
    }), action(t("LANCTL.RACK.UNIT.EDIT"), () => fullDetails(occupant)));
    if (["tray", "device.tray"].includes(occupant.data.type)) {
      const house = action(t("LANCTL.RACK.TRAY.ADD_EXISTING"), () => physicalHostDevice(occupant));
      house.dataset.rackHouse = occupant.id;
      const create = action(t("LANCTL.RACK.TRAY.CREATE_INSIDE"), () => physicalCreateInTray(occupant));
      create.dataset.rackTrayCreate = occupant.id;
      actions.push(house, create);
    }
  } else {
    actions.push(action(t("LANCTL.RACK.UNIT.CREATE"), () => {
      wireNew("switch.24ports", {rack, unit, in_rack: true, tray: null});
      const submit = formSubmit;
      formSubmit = values => { guard(); return submit(values); };
    }));
  }
  const assign = action(t("LANCTL.RACK.UNIT.ASSIGN"), () => {
    const available = physicalInventory().filter(r => !["rack", "wire"].includes(r.data.type) && r.directMount !== false);
    const choices = available.map(r => [r.id, `${r.data.name || r.id} · ${r.id} · ${physicalPlacementLabel(r)}`]);
    showForm(t("LANCTL.RACK.UNIT.ASSIGN"), [field(t("LANCTL.UI.STATUS.ELEMENT"), "element", choices[0]?.[0] || "", "text", choices)], async values => {
      guard();
      const record = available.find(r => r.id === values.element);
      if (!record) throw Error(t("LANCTL.UI.VIEW.NO_DEVICES_AVAILABLE"));
      const destination = `${rack} · U${unit}`;
      if (record.placement?.kind !== "independent" && !await appDecision(
        window.LanctlI18n.t("LANCTL.RACK.UNIT.CONFIRM_MOVE", {element: record.id, origin: physicalPlacementLabel(record), destination})
      )) return Promise.reject(new Error(t("LANCTL.RACK.UNIT.CANCELLED")));
      guard();
      return call("rack_element", revision, "update", record.id, {rack, unit, in_rack: true, tray: null});
    });
  });
  assign.disabled = Boolean(occupant);
  if (occupant) assign.title = t("LANCTL.RACK.UNIT.OCCUPIED");
  actions.push(assign);
  const menu = document.createElement("div"), controller = new AbortController();
  menu.className = "rack-unit-context";
  menu.setAttribute("role", "menu");
  menu.setAttribute("aria-label", `${rack} · U${unit}`);
  const title = Object.assign(document.createElement("div"), {className: "rack-unit-context-title", textContent: `${rack} · U${unit}`});
  title.setAttribute("role", "presentation");
  menu.append(title, ...actions);
  actions.forEach(action => { action.setAttribute("role", "menuitem"); action.tabIndex = -1; });
  document.body.append(menu);
  const rect = button.getBoundingClientRect(), bounds = menu.getBoundingClientRect();
  const x = point ? point.x : rect.left, y = point ? point.y : rect.bottom;
  menu.style.left = Math.max(8, Math.min(x, innerWidth - bounds.width - 8)) + "px";
  menu.style.top = Math.max(8, Math.min(y, innerHeight - bounds.height - 8)) + "px";
  rackUnitMenuClose = () => {
    controller.abort(); menu.remove();
    if (button.isConnected) button.focus({preventScroll: true});
    rackUnitMenuClose = () => {};
  };
  const options = actions.filter(action => !action.disabled);
  options[0]?.focus({preventScroll: true});
  document.addEventListener("pointerdown", event => {
    if (!menu.contains(event.target)) rackUnitMenuClose();
  }, {capture: true, signal: controller.signal});
  document.addEventListener("keydown", event => {
    if (event.key === "Escape" || event.key === "Tab") {
      if (event.key === "Escape") event.preventDefault();
      rackUnitMenuClose();
    } else if (["ArrowDown", "ArrowUp", "Home", "End"].includes(event.key)) {
      event.preventDefault();
      const index = options.indexOf(document.activeElement);
      const next = event.key === "Home" ? 0 : event.key === "End" ? options.length - 1 : (index + (event.key === "ArrowDown" ? 1 : -1) + options.length) % options.length;
      options[next]?.focus();
    }
  }, {signal: controller.signal});
  window.addEventListener("resize", rackUnitMenuClose, {signal: controller.signal});
  const scrollPositions = new Map();
  for (let node = button.parentElement; node; node = node.parentElement) scrollPositions.set(node, [node.scrollLeft,node.scrollTop]);
  document.addEventListener("scroll", event => {
    const target = event.target === document ? document.scrollingElement : event.target;
    const original = scrollPositions.get(target);
    // A queued event from scrolling the unit into view must not dismiss a new menu.
    if (original && (target.scrollLeft !== original[0] || target.scrollTop !== original[1])) rackUnitMenuClose();
  }, {capture: true, signal: controller.signal});
}
document.addEventListener("contextmenu", event => {
  const button = event.target.closest("[data-rack-unit]");
  if (button && state.launcher === "lanrack") { event.preventDefault(); rackUnitMenu(button, {x: event.clientX, y: event.clientY}); }
});
document.addEventListener("keydown", event => {
  if (event.key !== "ContextMenu" && !(event.shiftKey && event.key === "F10")) return;
  const button = event.target.closest("[data-rack-unit]");
  if (button && state.launcher === "lanrack") { event.preventDefault(); rackUnitMenu(button); }
});
