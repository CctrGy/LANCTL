"use strict";

// Native logical views reuse bounded RPCs; derived observations remain read-only.
(() => {
  const base = { details: fullDetails, access: accessForm, records, render };
  let request = 0, retained = null;
  const context = () => JSON.stringify(state.projectContext);
  const filterState = () => [context(), $("#search").value, $("#filter").value].join("\n");
  function keepSelection(id) {
    selected = id;
    retained = { id, filter: filterState() };
  }
  function scopedCall(expected, method, ...args) {
    if (context() !== expected) return Promise.reject(new Error(window.LanctlI18n.t("LANCTL.UI.VIEW.THE_PROJECT_CHANGED_RELOAD_THE_RECORD")));
    return call(method, ...args);
  }
  function note(text) {
    return Object.assign(document.createElement("p"), { textContent: text });
  }
  records = function () {
    const rows = base.records();
    if (!["lanaccess", "lanmon"].includes(state.launcher)) return rows;
    if (!retained || retained.filter !== filterState() || selected !== retained.id) {
      retained = null;
      return rows;
    }
    const row = state.records.find(r => idOf(r) === retained.id);
    return row && !rows.some(r => idOf(r) === retained.id) ? [...rows, row] : rows;
  };
  render = function () {
    base.render();
    if ($("#canvas [data-id]") && retained && retained.filter === filterState() &&
        !base.records().some(r => idOf(r) === retained.id)) {
      const message = note(window.LanctlI18n.t("LANCTL.UI.VIEW.THE_ELEMENT_YOU_JUST_EDITED_REMAINS_VISIBLE_EVEN_IF_IT_NO_LONGER_MATCHES_THE_FILTER"));
      message.className = "muted record-editor-retained";
      $("#canvas").prepend(message);
    }
  };

  function credentialEditor(r) {
    if (state.locked) return message(window.LanctlI18n.t("LANCTL.UI.VIEW.UNLOCK_THE_STORE_BEFORE_EDITING"), true);
    const expected = context(), username = field(window.LanctlI18n.t("LANCTL.UI.TEXT.USERNAME"), "username", r.username);
    username.querySelector("input").required = true;
    const change = field(window.LanctlI18n.t("LANCTL.UI.VIEW.CHANGE_PASSWORD"), "rotate", "", "checkbox");
    change.className = "record-secret-toggle";
    const password = field(window.LanctlI18n.t("LANCTL.UI.VIEW.NEW_PASSWORD"), "password", "", "password");
    const confirmation = field(window.LanctlI18n.t("LANCTL.UI.TEXT.REPEAT_PASSWORD"), "confirmation", "", "password");
    const toggle = change.querySelector("input"), inputs = [
      password.querySelector("input"), confirmation.querySelector("input")
    ];
    function visibility() {
      password.hidden = confirmation.hidden = !toggle.checked;
      for (const input of inputs) {
        input.disabled = !toggle.checked;
        input.required = toggle.checked;
        if (!toggle.checked) input.value = "";
      }
    }
    toggle.onchange = visibility;
    visibility();
    showForm(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.CREDENTIAL") + r.element, [
      note(`${r.element} · ${r.protocol.toUpperCase()} · ${r.credentialId}`),
      note(window.LanctlI18n.t("LANCTL.UI.VIEW.THE_DEVICE_AND_PROTOCOL_IDENTIFY_THIS_CREDENTIAL_THE_CURRENT_PASSWORD_REMAINS_HIDDEN_AND_IS_PRE")),
      username, change, password, confirmation
    ], async values => {
      const changes = { username: values.username };
      if (toggle.checked) {
        changes.password = values.password;
        changes.confirmation = values.confirmation;
      }
      await scopedCall(expected, "access_update", r.credentialId, r.revision, changes);
      keepSelection(r.credentialId);
    });
  }
  accessForm = function (r = null) {
    return r ? credentialEditor(r) : base.access();
  };

  async function monitorEditor(r) {
    const token = ++request, expected = context(), loading = note(window.LanctlI18n.t("LANCTL.UI.VIEW.LOADING_SAVED_DATA"));
    showForm(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.DEVICE_05DBAF67") + r.name, [loading]);
    try {
      let record = (await scopedCall(expected, "monitor_device", r.id)).device;
      if (token !== request || !loading.isConnected || !$("#detail").open || context() !== expected) return;
      const fields = [
        field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.NAME"), "name", record.editable.name),
        field(window.LanctlI18n.t("LANCTL.UI.WORD.ALIAS"), "alias", record.editable.alias),
        field(window.LanctlI18n.t("LANCTL.UI.TEXT.IP_ADDRESS"), "ip", record.editable.ip),
        field(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.DESCRIPTION"), "description", record.editable.description, "textarea")
      ];
      const observations = note( window.LanctlI18n.t("LANCTL.UI.WEB.OBSERVATIONS",{value0:(r.presence),value1:(r.health),value2:(r.latency == null ? window.LanctlI18n.t("LANCTL.UI.TEXT.NO_MEASUREMENT") : r.latency + " ms")}));
      const groups = document.createElement("div");
      function changedFields() {
        return Object.fromEntries(fields.map(f => f.querySelector("input,textarea"))
          .filter(input => input.value !== record.editable[input.name])
          .map(input => [input.name, input.value]));
      }
      function paintGroups() {
        groups.replaceChildren(note(window.LanctlI18n.t("LANCTL.UI.VIEW.MEMBERSHIP_CHANGES_APPLY_WITH_ADD_OR_REMOVE_PROTECTED_GROUPS_ARE_READ_ONLY")));
        const available = record.groupCatalog.filter(g => g.editable && !record.groups.includes(g.name));
        const choice = field(window.LanctlI18n.t("LANCTL.UI.VIEW.ADD_TO_A_GROUP"), "group", available[0]?.name || "", "text",
          available.map(g => [g.name, g.name]));
        const add = wireAction(window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.ADD"), () => changeGroup("add", choice.querySelector("select").value));
        add.disabled = !available.length;
        groups.append(choice, add);
        for (const name of record.groups) {
          const row = document.createElement("div"); row.className = "row";
          const editable = record.groupCatalog.find(g => g.name === name)?.editable === true;
          row.append(note(name + (editable ? "" : window.LanctlI18n.t("LANCTL.UI.FRAGMENT.PROTECTED"))));
          if (editable) row.append(wireAction(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.REMOVE_FROM") + name, () => changeGroup("remove", name)));
          groups.append(row);
        }
      }
      let changingGroup = false;
      async function changeGroup(action, name) {
        if (changingGroup) return;
        if (Object.keys(changedFields()).length) {
          window.LanctlI18n.bindText($("#detail-error"),"LANCTL.UI.VIEW.SAVE_OR_DISCARD_EDITED_DATA_BEFORE_CHANGING_GROUPS");
          return;
        }
        changingGroup = true;
        $("#submit").disabled = true;
        try {
          record = (await scopedCall(expected, "monitor_group", r.id, record.revision, action, name)).device;
          if (!groups.isConnected || !$("#detail").open || token !== request) return;
          paintGroups();
          $("#detail-error").textContent = "";
          formOriginal = JSON.stringify([...new FormData($("#detail-form"))]);
          window.launcherDataChanged = true;
        } catch (error) {
          if (groups.isConnected) $("#detail-error").textContent = error.message;
        } finally {
          changingGroup = false;
          if (groups.isConnected) $("#submit").disabled = false;
        }
      }
      paintGroups();
      showForm(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.DEVICE_05DBAF67") + r.name, [
        wireTabs([
          [window.LanctlI18n.t("LANCTL.UI.WORD.DATA"), [note(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.IDENTITY") + r.id), ...fields]],
          [window.LanctlI18n.t("LANCTL.UI.TEXT.GROUPS"), [groups]],
          [window.LanctlI18n.t("LANCTL.UI.WORD.NOTES"), [observations, note(window.LanctlI18n.t("LANCTL.UI.VIEW.MEASUREMENTS_STATE_AND_EVENTS_ARE_PRODUCED_BY_THE_MONITOR_THEY_ARE_NOT_EDITED_MANUALLY"))]]
        ])
      ], async () => {
        if (changingGroup) throw Error(window.LanctlI18n.t("LANCTL.UI.VIEW.WAIT_FOR_THE_GROUP_CHANGE_TO_FINISH"));
        await scopedCall(expected, "monitor_update", r.id, record.revision, changedFields());
        keepSelection(r.id);
      });
    } catch (error) {
      if (token === request && loading.isConnected && $("#detail").open) $("#detail-error").textContent = error.message;
    }
  }
  fullDetails = function (r) {
    if (!r) return;
    if (state.launcher === "lanaccess") return credentialEditor(r);
    if (state.launcher === "lanmon") return monitorEditor(r);
    return base.details(r);
  };
})();
