"use strict";

// LANMON owns activity, operational logs and the reviewable diagnostic workflow.
(() => {
  let page = "network",
    paused = false,
    reading = false,
    rows = [],
    session = "",
    allProjects = false;
  function sessionOptions(result, selected) {
    const metadata=new Map((result.sessionDetails||[]).map(item=>[item.id,item]));
    const zone=Intl.DateTimeFormat().resolvedOptions().timeZone;
    const formatter=new Intl.DateTimeFormat(window.LanctlI18n.code,{day:"2-digit",month:"2-digit",year:"numeric",hour:"2-digit",minute:"2-digit",second:"2-digit",hourCycle:"h23"});
    const items=(result.sessions||[]).map(id=>{
      const info=metadata.get(id)||{};
      const valid=value=>typeof value==="number"&&Number.isFinite(value)&&value>0;
      const real=valid(info.started),timestamp=real?info.started:valid(info.firstRecord)?info.firstRecord:null;
      const date=timestamp===null?null:new Date(timestamp*1000);
      const label=date&&!Number.isNaN(date.getTime())?formatter.format(date)+" · "+zone+(real?"":window.LanctlI18n.t("LANCTL.UI.FRAGMENT.FIRST_RETAINED_RECORD")):window.LanctlI18n.t("LANCTL.UI.FRAGMENT.UNKNOWN_DATE")+id;
      return {id,timestamp,label};
    }).sort((a,b)=>(b.timestamp??-Infinity)-(a.timestamp??-Infinity)||a.id.localeCompare(b.id));
    const counts=new Map();
    for(const item of items)counts.set(item.label,(counts.get(item.label)||0)+1);
    const options=[new Option(window.LanctlI18n.t("LANCTL.UI.VIEW.ALL_PROJECT_SESSIONS"),"")];
    for(const item of items){
      let label=item.label;
      if(counts.get(label)>1){
        let length=8;
        while(length<item.id.length&&items.some(other=>other.id!==item.id&&other.label===label&&other.id.slice(0,length)===item.id.slice(0,length)))length++;
        label+=" · "+item.id.slice(0,length);
      }
      const option=new Option(label,item.id);option.title=window.LanctlI18n.t("LANCTL.UI.FRAGMENT.SESSION_ID")+item.id;options.push(option);
    }
    // Keep an already selected session even if it leaves the retained window.
    if(selected&&!items.some(item=>item.id===selected))options.push(new Option(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.UNKNOWN_DATE")+selected,selected));
    return options;
  }
  const baseRender = render;
  function navigation() {
    $("#views").innerHTML = [
      ["network", window.LanctlI18n.t("LANCTL.UI.VIEW.MONITORING_67BC1FA5")],
      ["activity", window.LanctlI18n.t("LANCTL.UI.TEXT.ACTIVITY")],
      ["logs", window.LanctlI18n.t("LANCTL.UI.TEXT.LOGS")],
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
      page === "logs" ? window.LanctlI18n.t("LANCTL.UI.VIEW.OPERATIONAL_LOGS") : window.LanctlI18n.t("LANCTL.UI.VIEW.INTERFACE_ACTIVITY");
    $("#subtitle").textContent =
      page === "logs"
        ? window.LanctlI18n.t("LANCTL.UI.FRAGMENT.INCREMENTAL_LANCTL_LOG_PAUSING_STOPS_UPDATES_TO_THIS_VIEW")
        : window.LanctlI18n.t("LANCTL.UI.VIEW.MESSAGES_WITH_SOURCE_PROJECT_AND_SESSION_MONITORING_HISTORY_IS_KEPT_SEPARATE");
    $("#tools").innerHTML =
      "<button type=\"button\" data-monitor-report><span data-i18n=\"LANCTL.UI.HTML.PREPARE_REPORT\">Preparar reporte</span></button>";
    $("#commands").replaceChildren();
    $("#selection").textContent =
      "LANMON · " + (page === "logs" ? window.LanctlI18n.t("LANCTL.UI.TEXT.LOGS") : window.LanctlI18n.t("LANCTL.UI.TEXT.ACTIVITY"));
    if (!$("#monitor-evidence")) {
      $("#canvas").innerHTML =
        `<section class="monitor-evidence"><div class="monitor-filters"><label><span data-i18n="LANCTL.INVENTORY.MANUAL.SEARCH">Buscar</span><input type="search" id="monitor-query" placeholder="Mensaje, origen…" data-i18n-placeholder="LANCTL.UI.HTML.MESSAGE_SOURCE"></label><label><span data-i18n="LANCTL.UI.TEXT.LEVEL">Nivel</span><select id="monitor-level"><option value="0" data-i18n="LANCTL.UI.TEXT.ALL">Todos</option><option value="40" data-i18n="LANCTL.UI.HTML.ERRORS">Errores</option><option value="30" data-i18n="LANCTL.UI.HTML.WARNINGS_AND_ERRORS">Advertencias y errores</option></select></label><label id="monitor-session-label"><span data-i18n="LANCTL.UI.TEXT.SESSION">Sesión</span><select id="monitor-session"><option value="" data-i18n="LANCTL.UI.VIEW.ALL_PROJECT_SESSIONS">Todas las sesiones del proyecto</option></select></label><label class="check" id="monitor-projects-label"><input type="checkbox" id="monitor-all-projects"> <span data-i18n="LANCTL.UI.HTML.ALL_PROJECTS">Todos los proyectos</span></label><button type="button" id="monitor-pause"><span data-i18n="LANCTL.UI.TEXT.PAUSE">Pausar</span></button></div><p id="monitor-evidence-status" role="status"></p><div id="monitor-evidence" tabindex="0" aria-label="Registros de LANMON" data-i18n-aria-label="LANCTL.UI.HTML.LANMON_LOGS"></div></section>`;
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
        $("#monitor-pause").textContent = paused ? window.LanctlI18n.t("LANCTL.UI.WORD.RESUME") : window.LanctlI18n.t("LANCTL.UI.TEXT.PAUSE");
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
    window.LanctlI18n.bindText($("#monitor-evidence-status"),"LANCTL.UI.WEB.VALUE0_RECORDS_MAXIMUM_500_VALUE1",{value0:(visible.length),value1:(paused ? window.LanctlI18n.t("LANCTL.UI.FRAGMENT.PAUSED") : "")});
    const host = $("#monitor-evidence"),
      fragment = document.createDocumentFragment();
    for (const row of visible) {
      const article = document.createElement("article"),
        meta = document.createElement("small"),
        text = document.createElement("pre");
      meta.textContent = [
        row.created,
        row.launcher || row.source,
        row.project || row.file,
        row.level ? window.LanctlI18n.t("LANCTL.UI.FRAGMENT.LEVEL") + row.level : "",
      ]
        .filter(Boolean)
        .join(" · ");
      text.textContent = row.message;
      article.append(meta, text);
      if(row.session){
        const details=document.createElement("details"),summary=document.createElement("summary"),identifier=document.createElement("code");
        window.LanctlI18n.bindText(summary,"LANCTL.UI.VIEW.SESSION_IDENTIFIER");identifier.textContent=row.session;
        details.append(summary,identifier);article.append(details);
      }
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
        select.replaceChildren(...sessionOptions(result,session));
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
  window.LanctlI18n.bindAttribute(report, "aria-label", "LANCTL.UI.TEXT.PREPARE_REPORT_IN_LANMON");
  report.innerHTML = `<form><h2><span data-i18n="LANCTL.UI.HTML.PREPARE_REPORT">Preparar reporte</span></h2><p><span data-i18n="LANCTL.UI.HTML.REVIEW_DATA_BEFORE_OPENING_GITHUB_THE_ISSUE_IS_PUBLISHED_FROM_THE_BROWSER_WHEN_YOU_SUBMIT_IT">Revisa los datos antes de abrir GitHub. La incidencia se publica desde el navegador cuando tú la envíes.</span></p><label><span data-i18n="LANCTL.UI.HTML.SOURCE_SESSION">Sesión de origen</span><select name="reportSession"><option value="" data-i18n="LANCTL.UI.VIEW.ALL_PROJECT_SESSIONS">Todas las sesiones del proyecto</option></select></label><label><span data-i18n="LANCTL.INVENTORY.MANUAL.DESCRIPTION">Descripción</span><textarea name="description" rows="3" required></textarea></label><label><span data-i18n="LANCTL.UI.HTML.STEPS_TO_REPRODUCE">Pasos para reproducir</span><textarea name="steps" rows="3"></textarea></label><label><span data-i18n="LANCTL.UI.HTML.EXPECTED_RESULT">Resultado esperado</span><textarea name="expected" rows="2"></textarea></label><fieldset><legend><span data-i18n="LANCTL.UI.HTML.DATA_TO_INCLUDE">Datos que se incluirán</span></legend><label><input type="checkbox" name="includeErrors" checked> <span data-i18n="LANCTL.UI.HTML.ERRORS_FROM_THE_SELECTED_SESSION">Errores de la sesión seleccionada</span></label><label><input type="checkbox" name="includeActivity"> <span data-i18n="LANCTL.UI.HTML.ACTIVITY_FROM_THE_SELECTED_SESSION">Actividad de la sesión seleccionada</span></label><label><input type="checkbox" name="includeLogs"> <span data-i18n="LANCTL.UI.HTML.LATEST_OPERATIONAL_LOG_ENTRIES_UP_TO_100">Últimos registros operativos (hasta 100)</span></label><label><input type="checkbox" name="includePlugins"> <span data-i18n="LANCTL.UI.HTML.PLUGIN_IDENTIFIERS_AND_VERSIONS">Identificadores y versiones de plugins</span></label><label><input type="checkbox" name="anonymize" checked> <span data-i18n="LANCTL.UI.HTML.ANONYMIZE_PATHS_ADDRESSES_AND_PRIVATE_DATA">Anonimizar rutas, direcciones y datos privados</span></label></fieldset><p><span data-i18n="LANCTL.UI.HTML.CREDENTIALS_ARE_ALWAYS_EXCLUDED_THE_COMPLETE_PROJECT_IS_NOT_ATTACHED">Las credenciales se excluyen siempre. No se adjunta el proyecto completo.</span></p><p class="report-state" role="status"></p><div class="report-preview-toolbar" hidden><span><span data-i18n="LANCTL.UI.HTML.PREVIEW">Vista previa</span></span><button type="button" data-report="copy" aria-label="Copiar todo el reporte al portapapeles" disabled data-i18n-aria-label="LANCTL.UI.HTML.COPY_THE_ENTIRE_REPORT_TO_CLIPBOARD"><span data-i18n="LANCTL.UI.HEADING.COPY">COPY</span></button></div><pre class="report-preview" tabindex="0" aria-label="Vista previa del reporte" hidden data-i18n-aria-label="LANCTL.UI.HTML.REPORT_PREVIEW"></pre><div class="actions"><button type="button" data-report="close"><span data-i18n="LANCTL.UI.TEXT.CLOSE">Cerrar</span></button><button type="button" data-report="export" disabled><span data-i18n="LANCTL.UI.HTML.EXPORT_DIAGNOSTICS">Exportar diagnóstico</span></button><button type="button" data-report="github" disabled><span data-i18n="LANCTL.UI.HTML.OPEN_GITHUB_FORM">Abrir formulario en GitHub</span></button><button type="submit" class="primary"><span data-i18n="LANCTL.UI.HTML.PREVIEW">Vista previa</span></button></div></form>`;
  document.body.append(report);
  let prepared = false;
  function invalidate() {
    prepared = false;
    report
      .querySelectorAll('[data-report="export"],[data-report="github"],[data-report="copy"]')
      .forEach((b) => (b.disabled = true));
    report.querySelector(".report-preview").hidden = true;
    report.querySelector(".report-preview-toolbar").hidden = true;
  }
  report.addEventListener("input", invalidate);
  report.querySelector('[data-report="close"]').onclick = () => report.close();
  report.querySelector('[data-report="copy"]').onclick = async () => {
    if (!prepared) return;
    const text = report.querySelector(".report-preview").textContent;
    let copied = false;
    try {
      await navigator.clipboard.writeText(text);
      copied = true;
    } catch {
      // Some desktop webviews do not expose the Clipboard API.
      const input = document.createElement("textarea"),
        focused = document.activeElement;
      input.value = text;
      input.readOnly = true;
      input.style.cssText = "position:fixed;opacity:0;pointer-events:none";
      report.append(input);
      try {
        input.select();
        copied = document.execCommand("copy");
      } catch {
        copied = false;
      } finally {
        input.remove();
        focused?.focus({ preventScroll: true });
      }
    }
    report.querySelector(".report-state").textContent = copied
      ? window.LanctlI18n.t("LANCTL.UI.VIEW.FULL_REPORT_COPIED_TO_CLIPBOARD")
      : window.LanctlI18n.t("LANCTL.UI.VIEW.COULD_NOT_COPY_SELECT_THE_PREVIEW_TEXT_AND_PRESS_CTRL_C");
  };
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
      report.querySelector(".report-preview-toolbar").hidden = false;
      prepared = true;
      report
        .querySelectorAll('[data-report="export"],[data-report="github"],[data-report="copy"]')
        .forEach((b) => (b.disabled = false));
      window.LanctlI18n.bindText(report.querySelector(".report-state"),"LANCTL.UI.VIEW.DRAFT_PREPARED_CHECK_THE_PREVIEW_BEFORE_CONTINUING");
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
          ? window.LanctlI18n.t("LANCTL.UI.VIEW.EXPORT_CANCELLED")
          : result.path
            ? window.LanctlI18n.t("LANCTL.UI.FRAGMENT.DIAGNOSTICS_EXPORTED") + result.path
            : result.opened
              ? window.LanctlI18n.t("LANCTL.UI.VIEW.FORM_OPENED_FOR_YOUR_REVIEW")
              : window.LanctlI18n.t("LANCTL.UI.VIEW.COULD_NOT_OPEN_THE_BROWSER");
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
        select.replaceChildren(...sessionOptions(evidence,session));
        select.value = session;
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
