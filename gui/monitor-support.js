"use strict";

// LANMON owns activity, operational logs and the reviewable diagnostic workflow.
(() => {
  let page = "network",
    paused = false,
    reading = false,
    rows = [],
    session = "",
    allProjects = false;
  const baseRender = render;
  function navigation() {
    $("#views").innerHTML = [
      ["network", "Monitorización"],
      ["activity", "Actividad"],
      ["logs", "Registros"],
    ]
      .map(
        ([id, label]) =>
          `<button type="button" data-monitor-page="${id}" class="${page === id ? "active" : ""}">${label}</button>`,
      )
      .join("");
  }
  render = function () {
    if (state.launcher !== "lanmon") return baseRender();
    if (page === "network") {
      baseRender();
      navigation();
      $("#workspace .filterbar").hidden = false;
      return;
    }
    navigation();
    $("#workspace .filterbar").hidden = true;
    $("#title").textContent =
      page === "logs" ? "Registros operativos" : "Actividad de las interfaces";
    $("#subtitle").textContent =
      page === "logs"
        ? "Registro incremental de LANCTL. La pausa detiene la actualización de esta vista."
        : "Mensajes con origen, proyecto y sesión. El historial de monitorización se mantiene separado.";
    $("#tools").innerHTML =
      '<button type="button" data-monitor-report>Preparar reporte</button>';
    $("#commands").replaceChildren();
    $("#selection").textContent =
      "LANMON · " + (page === "logs" ? "Registros" : "Actividad");
    if (!$("#monitor-evidence")) {
      $("#canvas").innerHTML =
        `<section class="monitor-evidence"><div class="monitor-filters"><label>Buscar<input type="search" id="monitor-query" placeholder="Mensaje, origen…"></label><label>Nivel<select id="monitor-level"><option value="0">Todos</option><option value="40">Errores</option><option value="30">Advertencias y errores</option></select></label><label id="monitor-session-label">Sesión<select id="monitor-session"><option value="">Todas las sesiones del proyecto</option></select></label><label class="check" id="monitor-projects-label"><input type="checkbox" id="monitor-all-projects"> Todos los proyectos</label><button type="button" id="monitor-pause">Pausar</button></div><p id="monitor-evidence-status" role="status"></p><div id="monitor-evidence" tabindex="0" aria-label="Registros de LANMON"></div></section>`;
      $("#monitor-query").oninput = paint;
      $("#monitor-level").onchange = paint;
      $("#monitor-session").onchange = (event) => {
        session = event.target.value;
        load();
      };
      $("#monitor-all-projects").checked = allProjects;
      $("#monitor-all-projects").onchange = (event) => {
        allProjects = event.target.checked;
        session = "";
        load();
      };
      $("#monitor-pause").onclick = () => {
        paused = !paused;
        $("#monitor-pause").textContent = paused ? "Reanudar" : "Pausar";
        if (!paused) load();
      };
    }
    $("#monitor-session-label").hidden = page === "logs";
    $("#monitor-projects-label").hidden = page === "logs";
    paint();
    load();
  };
  function paint() {
    if (!$("#monitor-evidence")) return;
    const query = $("#monitor-query").value.toLocaleLowerCase(),
      level = Number($("#monitor-level").value);
    const visible = rows.filter(
      (row) =>
        (!level || Number(row.level || 0) >= level) &&
        JSON.stringify(row).toLocaleLowerCase().includes(query),
    );
    $("#monitor-evidence-status").textContent =
      `${visible.length} registros · máximo 500${paused ? " · En pausa" : ""}`;
    const host = $("#monitor-evidence"),
      fragment = document.createDocumentFragment();
    for (const row of visible) {
      const article = document.createElement("article"),
        meta = document.createElement("small"),
        text = document.createElement("pre");
      meta.textContent = [
        row.created,
        row.launcher || row.source,
        row.session,
        row.project || row.file,
        row.level ? "Nivel " + row.level : "",
      ]
        .filter(Boolean)
        .join(" · ");
      text.textContent = row.message;
      article.append(meta, text);
      fragment.append(article);
    }
    host.replaceChildren(fragment);
  }
  async function load() {
    if (reading || paused || state.launcher !== "lanmon" || page === "network")
      return;
    reading = true;
    try {
      const result =
        page === "logs"
          ? await call("monitor_logs")
          : await call("monitor_activity", session || null, allProjects);
      rows = result.records;
      if (page === "activity" && $("#monitor-session")) {
        const select = $("#monitor-session");
        select.innerHTML =
          '<option value="">Todas las sesiones del proyecto</option>' +
          result.sessions
            .map((id) => `<option value="${esc(id)}">${esc(id)}</option>`)
            .join("");
        select.value = session;
      }
      paint();
    } catch (error) {
      if ($("#monitor-evidence-status"))
        $("#monitor-evidence-status").textContent = error.message;
    } finally {
      reading = false;
    }
  }
  const report = document.createElement("dialog");
  report.className = "support-dialog report-dialog";
  report.setAttribute("aria-label", "Preparar reporte en LANMON");
  report.innerHTML = `<form><h2>Preparar reporte</h2><p>Revisa los datos antes de abrir GitHub. La incidencia se publica desde el navegador cuando tú la envíes.</p><label>Sesión de origen<select name="reportSession"><option value="">Todas las sesiones del proyecto</option></select></label><label>Descripción<textarea name="description" rows="3" required></textarea></label><label>Pasos para reproducir<textarea name="steps" rows="3"></textarea></label><label>Resultado esperado<textarea name="expected" rows="2"></textarea></label><fieldset><legend>Datos que se incluirán</legend><label><input type="checkbox" name="includeErrors" checked> Errores de la sesión seleccionada</label><label><input type="checkbox" name="includeActivity"> Actividad de la sesión seleccionada</label><label><input type="checkbox" name="includeLogs"> Últimos registros operativos (hasta 100)</label><label><input type="checkbox" name="includePlugins"> Identificadores y versiones de plugins</label><label><input type="checkbox" name="anonymize" checked> Anonimizar rutas, direcciones y datos privados</label></fieldset><p>Las credenciales se excluyen siempre. No se adjunta el proyecto completo.</p><p class="report-state" role="status"></p><pre class="report-preview" tabindex="0" aria-label="Vista previa del reporte" hidden></pre><div class="actions"><button type="button" data-report="close">Cerrar</button><button type="button" data-report="export" disabled>Exportar diagnóstico</button><button type="button" data-report="github" disabled>Abrir formulario en GitHub</button><button type="submit" class="primary">Vista previa</button></div></form>`;
  document.body.append(report);
  let prepared = false;
  function invalidate() {
    prepared = false;
    report
      .querySelectorAll('[data-report="export"],[data-report="github"]')
      .forEach((b) => (b.disabled = true));
    report.querySelector(".report-preview").hidden = true;
  }
  report.addEventListener("input", invalidate);
  report.querySelector('[data-report="close"]').onclick = () => report.close();
  report.querySelector("form").onsubmit = async (event) => {
    event.preventDefault();
    const form = event.target,
      button = form.querySelector('[type="submit"]');
    button.disabled = true;
    try {
      const values = {
        session: form.elements.reportSession.value,
        description: form.elements.description.value,
        steps: form.elements.steps.value,
        expected: form.elements.expected.value,
      };
      for (const key of [
        "includeErrors",
        "includeActivity",
        "includeLogs",
        "includePlugins",
        "anonymize",
      ])
        values[key] = form.elements[key].checked;
      const result = await call("prepare_report", values);
      const preview = report.querySelector(".report-preview");
      preview.textContent = result.markdown;
      preview.hidden = false;
      prepared = true;
      report
        .querySelectorAll('[data-report="export"],[data-report="github"]')
        .forEach((b) => (b.disabled = false));
      report.querySelector(".report-state").textContent =
        "Borrador preparado. Comprueba la vista previa antes de continuar.";
    } catch (error) {
      report.querySelector(".report-state").textContent = error.message;
    } finally {
      button.disabled = false;
    }
  };
  for (const [action, method] of [
    ["export", "export_report"],
    ["github", "open_report_form"],
  ])
    report.querySelector(`[data-report="${action}"]`).onclick = async () => {
      if (!prepared) return;
      try {
        const result = await call(method);
        report.querySelector(".report-state").textContent = result.cancelled
          ? "Exportación cancelada."
          : result.path
            ? "Diagnóstico exportado: " + result.path
            : result.opened
              ? "Formulario abierto para tu revisión."
              : "No se ha podido abrir el navegador.";
      } catch (error) {
        report.querySelector(".report-state").textContent = error.message;
      }
    };
  window.openLanmonView = async function (next) {
    if (state.launcher !== "lanmon") return call("open_monitor", next);
    if (next === "report") {
      if (!report.open) {
        const evidence = await call("monitor_activity", null, false);
        const select = report.querySelector('[name="reportSession"]');
        select.innerHTML =
          '<option value="">Todas las sesiones del proyecto</option>' +
          evidence.sessions
            .map((id) => `<option value="${esc(id)}">${esc(id)}</option>`)
            .join("");
        select.value = evidence.sessions.includes(session) ? session : "";
        invalidate();
        report.showModal();
      }
      return;
    }
    page = next;
    rows = [];
    $("#canvas").replaceChildren();
    render();
  };
  document.addEventListener("click", (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    if (button.dataset.monitorPage) {
      page = button.dataset.monitorPage;
      rows = [];
      $("#canvas").replaceChildren();
      render();
    }
    if (button.hasAttribute("data-monitor-report"))
      window.openLanmonView("report");
  });
  window.addEventListener("pywebviewready", async () => {
    if (!window.pywebview?.api.monitor_view) return;
    try {
      const initial = await call("monitor_view");
      if (initial.view) {
        session = initial.sourceSession;
        const timer = setInterval(() => {
          if (state.launcher) {
            clearInterval(timer);
            window.openLanmonView(initial.view);
          }
        }, 100);
      }
    } catch (error) {
      console.warn(error.message);
    }
  });
  setInterval(load, 1500);
})();
