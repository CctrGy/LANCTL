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
    if (context() !== expected) return Promise.reject(new Error("El proyecto cambió. Recarga la ficha."));
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
      const message = note("Se mantiene visible el elemento que acabas de editar, aunque ya no coincida con el filtro.");
      message.className = "muted record-editor-retained";
      $("#canvas").prepend(message);
    }
  };

  function credentialEditor(r) {
    if (state.locked) return message("Desbloquea el almacén antes de editar.", true);
    const expected = context(), username = field("Usuario", "username", r.username);
    username.querySelector("input").required = true;
    const change = field("Cambiar contraseña", "rotate", "", "checkbox");
    change.className = "record-secret-toggle";
    const password = field("Nueva contraseña", "password", "", "password");
    const confirmation = field("Repetir contraseña", "confirmation", "", "password");
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
    showForm("Credencial · " + r.element, [
      note(`${r.element} · ${r.protocol.toUpperCase()} · ${r.credentialId}`),
      note("El equipo y el protocolo identifican esta credencial. La contraseña actual permanece oculta y se conserva salvo que elijas cambiarla."),
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
    const token = ++request, expected = context(), loading = note("Cargando datos guardados…");
    showForm("Equipo · " + r.name, [loading]);
    try {
      let record = (await scopedCall(expected, "monitor_device", r.id)).device;
      if (token !== request || !loading.isConnected || !$("#detail").open || context() !== expected) return;
      const fields = [
        field("Nombre", "name", record.editable.name),
        field("Alias", "alias", record.editable.alias),
        field("Dirección IP", "ip", record.editable.ip),
        field("Descripción", "description", record.editable.description, "textarea")
      ];
      const observations = note(`Presencia: ${r.presence} · Salud: ${r.health} · Latencia: ${r.latency == null ? "Sin medición" : r.latency + " ms"}`);
      const groups = document.createElement("div");
      function changedFields() {
        return Object.fromEntries(fields.map(f => f.querySelector("input,textarea"))
          .filter(input => input.value !== record.editable[input.name])
          .map(input => [input.name, input.value]));
      }
      function paintGroups() {
        groups.replaceChildren(note("Los cambios de pertenencia se aplican con Añadir o Retirar. Los grupos protegidos son de lectura."));
        const available = record.groupCatalog.filter(g => g.editable && !record.groups.includes(g.name));
        const choice = field("Añadir a un grupo", "group", available[0]?.name || "", "text",
          available.map(g => [g.name, g.name]));
        const add = wireAction("Añadir", () => changeGroup("add", choice.querySelector("select").value));
        add.disabled = !available.length;
        groups.append(choice, add);
        for (const name of record.groups) {
          const row = document.createElement("div"); row.className = "row";
          const editable = record.groupCatalog.find(g => g.name === name)?.editable === true;
          row.append(note(name + (editable ? "" : " · Protegido")));
          if (editable) row.append(wireAction("Retirar de " + name, () => changeGroup("remove", name)));
          groups.append(row);
        }
      }
      let changingGroup = false;
      async function changeGroup(action, name) {
        if (changingGroup) return;
        if (Object.keys(changedFields()).length) {
          $("#detail-error").textContent = "Guarda o descarta los datos editados antes de cambiar grupos.";
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
      showForm("Equipo · " + r.name, [
        wireTabs([
          ["Datos", [note("Identidad: " + r.id), ...fields]],
          ["Grupos", [groups]],
          ["Observaciones", [observations, note("Las mediciones, el estado y los eventos los produce el monitor; no se editan manualmente.")]]
        ])
      ], async () => {
        if (changingGroup) throw Error("Espera a que termine el cambio de grupo.");
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
