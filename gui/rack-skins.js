/* Frentes vectoriales genéricos de equipos en la elevación del rack. */
const rackSkinBase = { render, details: rackOccupantDetails };
let rackSkinsVisible = true;
try {
  const saved = JSON.parse(
    localStorage.getItem("lanrack.skins.preferences") || "{}",
  );
  if (saved.schemaVersion === 1) {
    if (typeof saved.visible === "boolean") rackSkinsVisible = saved.visible;
  }
} catch {}
function rackSkinStore() {
  localStorage.setItem(
    "lanrack.skins.preferences",
    JSON.stringify({
      schemaVersion: 1,
      visible: rackSkinsVisible,
    }),
  );
}
// Resize the existing rows, without rebuilding forms, focus or inventory.
// Tall racks scroll at the minimum readable size instead of hiding units.
function rackFitElevation() {
  if (state.launcher !== "lanrack" || rackMode !== "rack") return;
  const canvas = $("#canvas"),
    elevation = canvas.querySelector(".rack-elevation"),
    header = canvas.querySelector(".rack-detail-header"),
    rack = state.records.find((r) => r.id === selected);
  if (!elevation || !header || !rack?.units) return;
  const style = getComputedStyle(elevation),
    horizontal = parseFloat(style.paddingLeft) + parseFloat(style.paddingRight),
    vertical =
      parseFloat(style.paddingTop) +
      parseFloat(style.paddingBottom) +
      parseFloat(style.borderTopWidth) +
      parseFloat(style.borderBottomWidth),
    gap = parseFloat(style.rowGap),
    available = canvas.clientHeight - header.offsetHeight - 8 - vertical,
    byHeight = (available - (rack.units - 1) * gap) / rack.units,
    byWidth = ((elevation.clientWidth - horizontal - 65) * 88) / 1200 + 6,
    height = Math.floor(Math.max(30, Math.min(84, byHeight, byWidth)));
  elevation.style.setProperty("--rack-unit-height", height + "px");
}
const rackSizeObserver = new ResizeObserver(rackFitElevation);
const rackSkinKinds = [
  ["auto", "Automático según inventario"],
  ["switch", "Switch"],
  ["panel", "Panel de conexiones"],
  ["server", "Servidor"],
  ["ups", "SAI / UPS"],
  ["router", "Router / cortafuegos"],
  ["shelf", "Bandeja"],
  ["blank", "Panel ciego"],
];
function rackAutoSkin(r) {
  const data = r.data || {},
    type = data.type || r.type || "";
  const entries = Object.entries(data.ports || {}),
    fiber = entries.filter(([, p]) =>
      /fiber|sfp/i.test([p.kind, p.connector, p.type].join(" ")),
    );
  const kind = /switch/.test(type)
    ? "switch"
    : /panel/.test(type)
      ? "panel"
      : /server/.test(type)
        ? "server"
        : /ups|sai/.test(type)
          ? "ups"
          : /router|gateway|firewall/.test(type)
            ? "router"
            : "shelf";
  return {
    kind,
    rj45: entries.length - fiber.length,
    sfp: fiber.length,
    units: r.span || 1,
    rackmount: !/switch/.test(type) || entries.length >= 12,
  };
}
function rackSkinOf(r) {
  const saved = r.data?.rackAppearance;
  return !saved || saved.kind === "auto"
    ? { ...rackAutoSkin(r), units: saved?.units || r.span || 1 }
    : saved;
}
function rackFace(r, override) {
  const p =
      override?.kind === "auto"
        ? { ...rackAutoSkin(r), units: override.units }
        : override || rackSkinOf(r),
    units = p.units || 1,
    h = 88 * units;
  const ports = Object.entries(r.data?.ports || {}),
    fiber = ports.filter(([, v]) =>
      /fiber|sfp/i.test([v.kind, v.connector, v.type].join(" ")),
    ),
    copper = ports.filter((e) => !fiber.includes(e));
  const used = new Set(r.connectedPorts || []),
    name = r.name || r.id;
  const title = `${name} · ${r.id} · ${units} U · Frente genérico ${p.kind} · ${p.rj45} RJ45 + ${p.sfp} SFP`;
  const label = name.length > 33 ? name.slice(0, 30) + "…" : name;
  let body = `<rect class="skin-chassis" x="${p.rackmount ? 18 : 200}" y="5" width="${p.rackmount ? 1164 : 800}" height="${h - 12}" rx="5"/>`;
  if (p.rackmount)
    for (const x of [5, 1184])
      body += `<rect class="skin-ear" x="${x}" y="1" width="12" height="${h - 4}" rx="3"/><circle class="skin-bolt" cx="${x + 6}" cy="15" r="3"/><circle class="skin-bolt" cx="${x + 6}" cy="${h - 16}" r="3"/>`;
  else
    body += `<path class="skin-tray" d="M5 ${h - 8} H1195 M12 ${h - 18} V${h - 4} M1188 ${h - 18} V${h - 4}"/>`;
  const textX = p.rackmount ? 38 : 220;
  body += `<text class="skin-device-name" x="${textX}" y="25">${esc(label)}</text><text class="skin-device-id" x="${textX}" y="42">${esc(r.id)} · ${esc(rackSkinKinds.find((k) => k[0] === p.kind)?.[1] || p.kind)}</text>`;
  if (["switch", "panel", "router"].includes(p.kind)) {
    const columns = Math.max(1, Math.ceil(p.rj45 / 2)),
      area = p.rj45 > 24 ? 650 : 390,
      cell = Math.min(31, area / columns),
      size = Math.max(9, cell - 5),
      right = p.rackmount ? 1040 : 925,
      start = right - columns * cell;
    for (let i = 0; i < p.rj45; i++) {
      const col = Math.floor(i / 2),
        row = i % 2,
        x = start + col * cell,
        y = 15 + row * 33;
      const port = copper[i],
        active = port && used.has(port[0]);
      body += `<g class="skin-port ${active ? "connected" : ""}" data-skin-port="${esc(port?.[0] || "")}" data-connector="rj45"><title>${esc(port ? port[0] + (active ? " · Conectado" : " · Sin conexión registrada") : "RJ45 " + (i + 1) + " · Representación sin puerto asociado")}</title><rect x="${x}" y="${y}" width="${size}" height="21" rx="1"/><path d="M${x + size * 0.25} ${y + 3} H${x + size * 0.75} M${x + size * 0.3} ${y + 6} H${x + size * 0.7}"/><text x="${x + size / 2}" y="${y + 29}">${i + 1}</text></g>`;
    }
    const sfpStart = p.rackmount ? 1065 : 945,
      cols = Math.max(1, Math.ceil(p.sfp / 2)),
      sfpCell = Math.min(38, (p.rackmount ? 100 : 48) / cols);
    for (let i = 0; i < p.sfp; i++) {
      const x = sfpStart + Math.floor(i / 2) * sfpCell,
        y = 15 + (i % 2) * 33,
        port = fiber[i];
      body += `<g class="skin-port skin-sfp ${port && used.has(port[0]) ? "connected" : ""}" data-connector="sfp"><title>${esc(port ? port[0] : "SFP " + (i + 1) + " · Representación sin puerto asociado")}</title><rect x="${x}" y="${y}" width="${Math.max(7, sfpCell - 4)}" height="20" rx="1"/><text x="${x + sfpCell / 2 - 2}" y="${y + 29}">S${i + 1}</text></g>`;
    }
    body += `<circle class="skin-power" cx="${textX + 5}" cy="62" r="3"/><text class="skin-device-id" x="${textX + 17}" y="65">${p.rj45} RJ45${p.sfp ? " + " + p.sfp + " SFP" : ""}</text>`;
  } else if (p.kind === "server") {
    const rows = Math.min(4, units),
      cols = 6,
      bayH = Math.max(18, (h - 22) / rows);
    for (let i = 0; i < rows * cols; i++) {
      const x = 440 + (i % cols) * 115,
        y = 12 + Math.floor(i / cols) * bayH;
      body += `<g class="skin-drive"><rect x="${x}" y="${y}" width="102" height="${bayH - 5}" rx="3"/><path d="M${x + 9} ${y + 7} V${y + bayH - 12}"/><circle cx="${x + 87}" cy="${y + 9}" r="2"/></g>`;
    }
  } else if (p.kind === "ups") {
    body += `<rect class="skin-display" x="455" y="${h * 0.25}" width="200" height="${h * 0.45}" rx="6"/><text class="skin-display-text" x="555" y="${h * 0.5}">SAI / UPS</text><text class="skin-device-id" x="555" y="${h * 0.5 + 18}" text-anchor="middle">Sin telemetría</text>`;
    for (let i = 0; i < 16; i++)
      body += `<path class="skin-vent" d="M${740 + i * 23} ${h * 0.2} V${h * 0.8}"/>`;
  } else if (p.kind === "shelf") {
    for (let i = 0; i < 24; i++)
      body += `<path class="skin-vent" d="M${440 + i * 28} ${h * 0.45} V${h * 0.8}"/>`;
  } else body += `<path class="skin-vent" d="M440 ${h * 0.55} H1120"/>`;
  return `<svg class="rack-face skin-${p.kind}" viewBox="0 0 1200 ${h}" preserveAspectRatio="none" focusable="false" role="img" aria-label="${esc(title)}"><title>${esc(title)}</title>${body}</svg>`;
}
function rackSkinElevation(rack) {
  const occupied = new Map(),
    conflicts = new Set();
  for (const r of rack.occupants) {
    if (!r.unit) continue;
    for (
      let u = Number(r.unit);
      u < Number(r.unit) + (r.span || 1) && u <= rack.units;
      u++
    ) {
      if (occupied.has(u)) conflicts.add(u);
      else occupied.set(u, r);
    }
  }
  const rendered = new Set();
  let html = "";
  for (let u = rack.units; u >= 1; u--) {
    const r = occupied.get(u);
    if (r && rendered.has(r.id)) continue;
    if (r) {
      rendered.add(r.id);
      const span = r.span || 1;
      const label = `${r.name || r.id} · ${r.id} · ${span} U`;
      html += `<button class="rack-skin-unit occupied" data-rack-occupant="${esc(r.id)}" style="--rack-span:${span}" title="${esc(label)}" aria-label="${esc(label)}"><span class="rack-u-label">${span > 1 ? `${Number(r.unit) + span - 1}–${r.unit}` : r.unit} U</span><span class="rack-skin-face">${rackFace(r)}<span class="rack-skin-caption">${esc(r.name || r.id)}</span></span></button>`;
    } else
      html += `<button class="rack-skin-unit rack-skin-empty" disabled><span class="rack-u-label">${u} U</span><span>Libre</span></button>`;
  }
  if (conflicts.size)
    html =
      '<p class="error">Hay posiciones solapadas en el inventario: ' +
      [...conflicts].sort((a, b) => b - a).join(", ") +
      " U. Revisa sus ubicaciones en LANWIRE.</p>" +
      html;
  return html;
}
function rackSkinEditor(r) {
  const current = r.data?.rackAppearance || {
      schemaVersion: 1,
      ...rackAutoSkin(r),
      kind: "auto",
    },
    values = { ...current };
  const preview = document.createElement("div");
  preview.className = "rack-skin-preview";
  const note = document.createElement("p");
  note.className = "muted";
  note.textContent =
    "Frentes genéricos. La apariencia no crea puertos ni cambia conexiones. La altura ocupa unidades desde la posición inicial hacia arriba; se validará el espacio disponible.";
  const profiles = state.skinProfiles || [];
  const fields = [
    field("Plantilla", "preset", "custom", "text", [
      ["custom", "Personalizado"],
      ...profiles.map((p) => [p.id, p.name]),
    ]),
    field("Tipo de frente", "kind", values.kind, "text", rackSkinKinds),
    field("Puertos RJ45 (representación)", "rj45", values.rj45, "number"),
    field("Puertos SFP / SFP+ (representación)", "sfp", values.sfp, "number"),
    field("Altura ocupada (U)", "units", values.units, "number"),
    field("Formato", "rackmount", String(values.rackmount), "text", [
      ["true", "Montaje en rack"],
      ["false", "Sobremesa sobre bandeja"],
    ]),
  ];
  const controls = document.createElement("div");
  controls.className = "rack-skin-controls";
  controls.append(...fields);
  showForm(
    "Frente visual · " + (r.name || r.id),
    [preview, note, controls],
    () => call("rack_appearance", state.organizationRevision, r.id, read()),
  );
  function read() {
    return {
      kind: controls.querySelector("[name=kind]").value,
      rj45: Number(controls.querySelector("[name=rj45]").value),
      sfp: Number(controls.querySelector("[name=sfp]").value),
      units: Number(controls.querySelector("[name=units]").value),
      rackmount: controls.querySelector("[name=rackmount]").value === "true",
    };
  }
  function paint() {
    const v = read();
    if (v.kind === "auto") {
      const auto = rackAutoSkin(r);
      for (const key of ["rj45", "sfp", "rackmount"])
        controls.querySelector(`[name=${key}]`).value = String(auto[key]);
    }
    controls.querySelector("[name=rackmount]").disabled = v.kind === "auto";
    preview.innerHTML = rackFace(r, {
      ...v,
      rj45: Math.max(0, Math.min(96, v.rj45 || 0)),
      sfp: Math.max(0, Math.min(32, v.sfp || 0)),
      units: Math.max(1, Math.min(52, v.units || 1)),
    });
    for (const k of ["rj45", "sfp"])
      controls.querySelector(`[name=${k}]`).disabled = v.kind === "auto";
  }
  controls.querySelector("[name=preset]").onchange = (e) => {
    const p = profiles.find((p) => p.id === e.target.value);
    if (!p) return;
    for (const k of ["kind", "rj45", "sfp", "units", "rackmount"])
      controls.querySelector(`[name=${k}]`).value = String(p[k]);
    paint();
  };
  for (const key of ["rj45", "sfp", "units"]) {
    const input = controls.querySelector(`[name=${key}]`);
    input.min = key === "units" ? 1 : 0;
    input.max = key === "rj45" ? 96 : key === "sfp" ? 32 : 52;
    input.step = 1;
  }
  controls.addEventListener("input", paint);
  controls.addEventListener("change", paint);
  paint();
}
rackOccupantDetails = function (r) {
  rackSkinBase.details(r);
  const panel = document.querySelector("#detail-fields .wire-tab-panel");
  if (!panel) return;
  const front = document.createElement("div");
  front.className = "rack-skin-preview";
  front.innerHTML = rackFace(r);
  panel.prepend(
    front,
    wireAction("Personalizar frente", () => {
      $("#detail").close();
      rackSkinEditor(r);
    }),
  );
};
render = function () {
  rackSizeObserver.disconnect();
  rackSkinBase.render();
  if (state.launcher !== "lanrack" || rackMode !== "rack") return;
  const chosen = state.records.find((r) => r.id === selected),
    elevation = document.querySelector(".rack-elevation");
  if (!chosen || !elevation) return;
  const toggle = document.createElement("button");
  toggle.id = "rack-skins-toggle";
  toggle.textContent = rackSkinsVisible
    ? "Ver unidades simples"
    : "Ver frentes de equipos";
  toggle.onclick = () => {
    rackSkinsVisible = !rackSkinsVisible;
    rackSkinStore();
    render();
  };
  $("#rack-back").after(toggle);
  rackSizeObserver.observe($("#canvas"));
  rackSizeObserver.observe(document.querySelector(".rack-detail-header"));
  rackFitElevation();
  if (!rackSkinsVisible) return;
  elevation.classList.add("rack-skinned");
  elevation.innerHTML = rackSkinElevation(chosen);
  elevation
    .querySelectorAll("[data-rack-occupant]")
    .forEach(
      (b) =>
        (b.onclick = () =>
          rackOccupantDetails(
            chosen.occupants.find((r) => r.id === b.dataset.rackOccupant),
          )),
    );
};
