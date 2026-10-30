"use strict";

// Dimensions are edited in LANRACK and validated against the shared physical inventory.
(() => {
  const base = { render, details: rackShowDetails, metric: rackMetric };
  const validHeight = (r) =>
    Number.isInteger(r.units) && r.units >= 4 && r.units <= 52;
  rackMetric = (r) =>
    `${base.metric(r)} · ${r.widthInches ? r.widthInches + window.LanctlI18n.html("LANCTL.UI.FRAGMENT.MOUNTING_WIDTH") : window.LanctlI18n.html("LANCTL.UI.VIEW.WIDTH_PENDING")}${r.dimensions?.needsReview ? window.LanctlI18n.html("LANCTL.UI.FRAGMENT.REVIEW_DIMENSIONS") : ""}`;
  function dimensionFields(r) {
    const height = field(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.HEIGHT_4_52_U"), "units", r?.units ?? 42, "number");
    const input = height.querySelector("input");
    input.min = 4;
    input.max = 52;
    input.step = 1;
    input.required = true;
    const width = field(
      window.LanctlI18n.t("LANCTL.UI.VIEW.MOUNTING_WIDTH_INCHES"),
      "widthInches",
      r?.widthInches ?? (r ? "" : 19),
      "text",
      [
        ["", window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_WIDTH")],
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
      window.LanctlI18n.t("LANCTL.UI.VIEW.EQUIPMENT_AND_CONNECTIONS_WILL_BE_PRESERVED_THE_HEIGHT_CANNOT_LEAVE_EQUIPMENT_OUTSIDE_THE_RACK");
    showForm(
      window.LanctlI18n.t("LANCTL.UI.FRAGMENT.DIMENSIONS") + r.name,
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
      window.LanctlI18n.t("LANCTL.UI.VIEW.NEW_RACK_CABINET"),
      [
        field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.NAME"), "name"),
        field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.DESCRIPTION"), "description", "", "textarea"),
        field(window.LanctlI18n.t("LANCTL.UI.VIEW.IDENTIFIER_PREFIX"), "prefix", "RK"),
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
        wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.EDIT_DIMENSIONS"), () => {
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
      window.LanctlI18n.bindText(title,"LANCTL.UI.VIEW.DIMENSIONS_PENDING_REVIEW");
      const note = document.createElement("p");
      note.textContent = (rack.dimensions?.warnings || []).join(". ");
      section.append(
        title,
        note,
        wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.CORRECT_DIMENSIONS"), () => edit(rack)),
      );
      $("#canvas").replaceChildren(section);
    }
    $("#tools").append(wireAction(window.LanctlI18n.t("LANCTL.UI.TEXT.NEW_RACK"), create));
    const chosen = state.records.find((r) => r.id === selected);
    if (chosen)
      $("#commands").append(
        wireAction(window.LanctlI18n.t("LANCTL.UI.VIEW.EDIT_DIMENSIONS"), () => edit(chosen)),
      );
  };
})();
