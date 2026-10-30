"use strict";

(() => {
  if (/^https?:$/.test(window.location.protocol)) return;
  const api = async (method, ...args) => {
    const result = await window.pywebview.api[method](...args);
    if (!result.ok) {
      throw Object.assign(
        new Error(result.error || window.LanctlI18n.t("LANCTL.UI.TEXT.COULD_NOT_COMPLETE_THE_OPERATION")),
        { errorDetails: result.errorDetails },
      );
    }
    return result;
  };
  const footer = document.querySelector("footer > div, footer > span");
  function footerButton(id, label, click) {
    const button = document.createElement("button");
    button.type = "button";
    button.id = id;
    if (label.startsWith("LANCTL.")) window.LanctlI18n.bindText(button, label);
    else button.textContent = label;
    button.hidden = true;
    button.onclick = () =>
      Promise.resolve(click()).catch((error) => message(error.message, true));
    footer?.append(button);
    window.addEventListener("pywebviewready", () => {
      button.hidden =
        id === "live-logs"
          ? !window.pywebview?.api.open_live_logs
          : !window.pywebview?.api.open_monitor;
    });
    return button;
  }
  const queue = [];
  let transmission = null;
  function flush() {
    if (transmission) return transmission;
    if (!window.pywebview?.api.record_activity) return Promise.resolve();
    transmission = (async () => {
      try {
        while (queue.length) {
          const item = queue[0];
          const result = await api(
            "record_activity",
            item.text,
            item.level,
            item.details,
          );
          if (result.loggingWarning) notify(result.loggingWarning);
          if (queue[0] === item) queue.shift();
        }
      } catch (error) {
        console.warn(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.ACTIVITY_PENDING_SUBMISSION_TO_LANMON"), error.message);
      }
    })().finally(() => {
      transmission = null;
    });
    return transmission;
  }
  const notice = document.createElement("dialog");
  notice.className = "support-dialog";
  notice.setAttribute("aria-labelledby", "support-error-title");
  notice.innerHTML = `<h2 id="support-error-title"><span data-i18n="LANCTL.UI.TEXT.THE_OPERATION_WAS_NOT_COMPLETED">No se ha completado la operación</span></h2><p class="support-error-summary"></p><details><summary><span data-i18n="LANCTL.UI.TEXT.VIEW_DETAILS">Ver detalles</span></summary><pre class="support-error-details"></pre></details><div class="actions"><button type="button" data-error="close"><span data-i18n="LANCTL.UI.TEXT.CLOSE">Cerrar</span></button><button type="button" class="primary" data-error="report"><span data-i18n="LANCTL.UI.TEXT.PREPARE_REPORT_IN_LANMON">Preparar reporte en LANMON</span></button></div>`;
  document.body.append(notice);
  let lastError = "",
    repeats = 0,
    lastTime = 0;
  notice.querySelector('[data-error="close"]').onclick = () => notice.close();
  notice.querySelector('[data-error="report"]').onclick = async () => {
    notice.close();
    try {
      await openMonitor("report");
    } catch (error) {
      message(error.message, true);
    }
  };
  function notify(text, details = null) {
    const repeated = text === lastError && Date.now() - lastTime < 60000;
    lastError = text;
    lastTime = Date.now();
    repeats = repeated ? repeats + 1 : 1;
    notice.querySelector(".support-error-summary").textContent =
      text.slice(0, 260) + (repeats > 1 ?  window.LanctlI18n.t("LANCTL.UI.WEB.REPEATED",{value0:(repeats)}) : "");
    notice.querySelector(".support-error-details").textContent =
      text +
      (details
        ? "\n\n" +
          [
            [window.LanctlI18n.t("LANCTL.UI.TEXT.SOURCE"), details.origin],
            [window.LanctlI18n.t("LANCTL.UI.VIEW.CODE"), details.code],
            ["ID", details.errorId],
          ]
            .filter(([, value]) => value)
            .map(([label, value]) => label + ": " + value)
            .join("\n")
        : "");
    if (!notice.open && !repeated) notice.showModal();
  }
  let handledError = "",
    handledAt = 0;
  function record(text, error, details = null) {
    queue.push({
      text: String(text).slice(0, 4096),
      level: error ? 43 : 20,
      details,
    });
    if (queue.length > 100) queue.shift();
    flush();
  }
  if (typeof call === "function") {
    const originalCall = call;
    call = async function (...args) {
      try {
        if (args[0] === "request_close") await flush();
        return await originalCall(...args);
      } catch (error) {
        handledError = error.message;
        handledAt = Date.now();
        record(error.message, true, error.errorDetails);
        notify(error.message, error.errorDetails);
        throw error;
      }
    };
  }
  if (typeof message === "function") {
    const original = message;
    message = function (text, error = false) {
      original(text, error);
      const alreadyHandled =
        error && String(text) === handledError && Date.now() - handledAt < 1000;
      if (text && !alreadyHandled) record(text, error);
      if (error && text && !alreadyHandled) notify(String(text));
    };
  }
  async function openMonitor(view) {
    await flush();
    if (queue.length)
      throw new Error(
        window.LanctlI18n.t("LANCTL.UI.VIEW.ACTIVITY_COULD_NOT_BE_PRESERVED_RETRY_BEFORE_OPENING_THE_REPORT"),
      );
    if (window.openLanmonView) return window.openLanmonView(view);
    return api("open_monitor", view);
  }
  footerButton("report-bug", window.LanctlI18n.t("LANCTL.UI.VIEW.REPORT_A_BUG"), () => openMonitor("report"));
  if (document.querySelector("#lanip-cli"))
    footerButton("live-logs", "LANCTL.UI.TEXT.LOGS", () => api("open_live_logs"));
  document.addEventListener(
    "click",
    (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      if (button.id === "activity") {
        event.stopImmediatePropagation();
        openMonitor("activity").catch((error) => message(error.message, true));
      }
      if (button.dataset.officialLink) {
        event.stopImmediatePropagation();
        api("open_official_link", button.dataset.officialLink)
          .then((result) => {
            if (!result.opened)
              message("No se pudo abrir el navegador. " + result.url, true);
          })
          .catch((error) => message(error.message, true));
      }
      if (button.dataset.support === "appearance") {
        event.stopImmediatePropagation();
        window.guiAppearance
          .open()
          .catch((error) => message(error.message, true));
      }
      if (button.dataset.support === "updates") {
        event.stopImmediatePropagation();
        showUpdates();
      }
    },
    true,
  );
  const updates = document.createElement("dialog");
  updates.className = "support-dialog";
  updates.setAttribute("aria-label", window.LanctlI18n.t("LANCTL.UI.HTML.UPDATES"));
  updates.innerHTML = `<h2><span data-i18n="LANCTL.UI.HTML.UPDATES">Actualizaciones</span></h2><p class="update-state" role="status"></p><dl class="update-versions"></dl><pre class="update-notes"></pre><a class="update-link" target="_blank" rel="noopener" hidden><span data-i18n="LANCTL.UI.HTML.VIEW_RELEASE_AND_DOWNLOADS_ON_GITHUB">Ver versión y descargas en GitHub</span></a><div class="actions"><button type="button" data-update="close"><span data-i18n="LANCTL.UI.TEXT.CLOSE">Cerrar</span></button><button type="button" data-update="later" hidden><span data-i18n="LANCTL.UI.HTML.REMIND_ME_LATER">Recordar más tarde</span></button><button type="button" class="primary" data-update="check"><span data-i18n="LANCTL.UI.HTML.CHECK_FOR_UPDATES">Buscar actualizaciones</span></button></div>`;
  document.body.append(updates);
  let latestUpdate = null,
    updateReading = false,
    announcedVersion = null;
  updates.querySelector(".update-link").onclick = (event) => {
    event.preventDefault();
    api("open_update_release").catch((error) => {
      updates.querySelector(".update-state").textContent = error.message;
    });
  };
  updates.querySelector('[data-update="close"]').onclick = () =>
    updates.close();
  updates.querySelector('[data-update="later"]').onclick = async () => {
    try {
      await api("remind_update_later", latestUpdate.available);
      updates.close();
    } catch (error) {
      updates.querySelector(".update-state").textContent = error.message;
    }
  };
  function updateView(result) {
    latestUpdate = result;
    updates.querySelector(".update-state").textContent =
      {
        idle: window.LanctlI18n.t("LANCTL.UI.VIEW.CLICK_CHECK_FOR_UPDATES_TO_QUERY_STABLE_RELEASES"),
        checking: window.LanctlI18n.t("LANCTL.UI.VIEW.CHECKING_STABLE_RELEASES"),
        current: window.LanctlI18n.t("LANCTL.UI.VIEW.THE_INSTALLED_VERSION_IS_UP_TO_DATE"),
        available: window.LanctlI18n.t("LANCTL.UI.VIEW.A_NEWER_STABLE_RELEASE_IS_AVAILABLE"),
        unavailable:
          window.LanctlI18n.t("LANCTL.UI.VIEW.COULD_NOT_QUERY_GITHUB_YOU_CAN_TRY_AGAIN_LATER"),
      }[result.status] ||
      result.error ||
      window.LanctlI18n.t("LANCTL.UI.VIEW.QUERY_FINISHED");
    const versions = updates.querySelector(".update-versions");
    versions.replaceChildren();
    for (const [label, value] of [
      [window.LanctlI18n.t("LANCTL.UI.WORD.INSTALLED"), result.installed],
      [window.LanctlI18n.t("LANCTL.UI.TEXT.AVAILABLE"), result.available],
    ])
      if (value) {
        const dt = document.createElement("dt"),
          dd = document.createElement("dd");
        dt.textContent = label;
        dd.textContent = value;
        versions.append(dt, dd);
      }
    updates.querySelector(".update-notes").textContent = result.notes || "";
    const link = updates.querySelector(".update-link");
    link.hidden = !/^https:\/\/github\.com\/CctrGy\/LANCTL\/releases\//i.test(
      result.url || "",
    );
    if (!link.hidden) link.href = result.url;
    updates.querySelector('[data-update="later"]').hidden =
      result.status !== "available";
    updates.querySelector('[data-update="check"]').disabled =
      result.status === "checking";
  }
  async function checkUpdates(manual) {
    try {
      updateView(await api("check_updates", manual));
    } catch (error) {
      updateView({ status: "unavailable", error: error.message });
    }
  }
  function showUpdates() {
    if (!updates.open) updates.showModal();
    if (latestUpdate) updateView(latestUpdate);
    checkUpdates(true);
  }
  updates.querySelector('[data-update="check"]').onclick = () =>
    checkUpdates(true);
  async function pollUpdate() {
    if (
      updateReading ||
      !window.pywebview?.api.update_status ||
      !document.querySelector("#external-cli")
    )
      return;
    updateReading = true;
    try {
      const result = await api("update_status");
      updateView(result);
      if (
        result.status === "available" &&
        !result.deferred &&
        announcedVersion !== result.available
      ) {
        announcedVersion = result.available;
        if (!updates.open) updates.showModal();
      }
    } catch (error) {
      console.warn(window.LanctlI18n.t("LANCTL.UI.FRAGMENT.UPDATES"), error.message);
    } finally {
      updateReading = false;
    }
  }
  window.addEventListener("pywebviewready", () => {
    flush();
    if (document.querySelector("#external-cli")) checkUpdates(false);
  });
  setInterval(flush, 3000);
  setInterval(pollUpdate, 2000);
  window.guiActivityFlush = flush;
})();
