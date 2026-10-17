"use strict";

// Dimensions are edited in LANRACK and validated against the shared physical inventory.
(() => {
  const base = { render, details: rackShowDetails, metric: rackMetric };
  const validHeight = (r) =>
    Number.isInteger(r.units) && r.units >= 4 && r.units <= 52;
  rackMetric = (r) =>
    `${base.metric(r)} · ${r.widthInches ? r.widthInches + "″ de montaje" : "Ancho pendiente"}${r.dimensions?.needsReview ? " · Revisar dimensiones" : ""}`;
  function dimensionFields(r) {
    const height = field("Altura (4–52 U)", "units", r?.units ?? 42, "number");
    const input = height.querySelector("input");
    input.min = 4;
    input.max = 52;
    input.step = 1;
    input.required = true;
    const width = field(
      "Ancho de montaje (pulgadas)",
      "widthInches",
      r?.widthInches ?? (r ? "" : 19),
      "text",
      [
        ["", "Seleccionar ancho"],
        [10, "10″"],
        [19, "19″"],
        [21, "21″"],
        [23, "23″"],
      ],
    );
    width.querySelector("select").required = true;
    return [height, width];
  }
  function edit(r) {
    const note = document.createElement("p");
    note.textContent =
      (r.dimensions?.warnings || []).join(". ") ||
      "Los equipos y sus conexiones se conservarán. La altura no puede dejar equipos fuera del rack.";
    showForm(
      "Dimensiones · " + r.name,
      [note, ...dimensionFields(r)],
      (values) =>
        call("rack_dimensions", state.organizationRevision, r.id, {
          units: Number(values.units),
          widthInches: Number(values.widthInches),
        }),
    );
  }
  function create() {
    showForm(
      "Nuevo armario rack",
      [
        field("Nombre", "name"),
        field("Descripción", "description", "", "textarea"),
        field("Prefijo del identificador", "prefix", "RK"),
        ...dimensionFields(),
      ],
      async (values) => {
        const result = await call("rack_create", {
          ...values,
          units: Number(values.units),
          widthInches: Number(values.widthInches),
        });
        selected = result.id;
      },
    );
  }
  rackShowDetails = function (r) {
    base.details(r);
    const summary = document.querySelector("#detail-fields .wire-tab-panel");
    if (summary)
      summary.append(
        wireAction("Editar dimensiones", () => {
          $("#detail").close();
          edit(r);
        }),
      );
  };
  render = function () {
    if (state.launcher !== "lanrack") return base.render();
    const rack = state.records.find((r) => r.id === selected),
      invalid = rack && !validHeight(rack),
      previous = rackMode;
    if (invalid && rackMode === "rack") rackMode = "list";
    base.render();
    rackMode = previous;
    if (invalid && previous === "rack") {
      const section = document.createElement("section");
      section.className = "panel";
      const title = document.createElement("h2");
      title.textContent = "Dimensiones pendientes de revisión";
      const note = document.createElement("p");
      note.textContent = (rack.dimensions?.warnings || []).join(". ");
      section.append(
        title,
        note,
        wireAction("Corregir dimensiones", () => edit(rack)),
      );
      $("#canvas").replaceChildren(section);
    }
    $("#tools").append(wireAction("Nuevo rack", create));
    const chosen = state.records.find((r) => r.id === selected);
    if (chosen)
      $("#commands").append(
        wireAction("Editar dimensiones", () => edit(chosen)),
      );
  };
})();
