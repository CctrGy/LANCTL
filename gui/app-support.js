"use strict";

(() => {
  if (/^https?:$/.test(window.location.protocol)) return;
  const api = async (method, ...args) => {
    const result = await window.pywebview.api[method](...args);
    if (!result.ok) {
      throw Object.assign(
        new Error(result.error || "No se pudo completar la operación"),
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
    button.textContent = label;
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
        console.warn("Actividad pendiente de enviar a LANMON:", error.message);
      }
    })().finally(() => {
      transmission = null;
    });
    return transmission;
  }
  const notice = document.createElement("dialog");
  notice.className = "support-dialog";
  notice.setAttribute("aria-labelledby", "support-error-title");
  notice.innerHTML = `<h2 id="support-error-title">No se ha completado la operación</h2><p class="support-error-summary"></p><details><summary>Ver detalles</summary><pre class="support-error-details"></pre></details><div class="actions"><button type="button" data-error="close">Cerrar</button><button type="button" class="primary" data-error="report">Preparar reporte en LANMON</button></div>`;
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
      text.slice(0, 260) + (repeats > 1 ? ` · Repetido ${repeats} veces` : "");
    notice.querySelector(".support-error-details").textContent =
      text +
      (details
        ? "\n\n" +
          [
            ["Origen", details.origin],
            ["Código", details.code],
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
        "No se ha podido conservar la actividad. Reintenta antes de abrir el reporte.",
      );
    if (window.openLanmonView) return window.openLanmonView(view);
    return api("open_monitor", view);
  }
  footerButton("report-bug", "Report a bug", () => openMonitor("report"));
  if (document.querySelector("#lanip-cli"))
    footerButton("live-logs", "Registros", () => api("open_live_logs"));
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
  updates.setAttribute("aria-label", "Actualizaciones");
  updates.innerHTML = `<h2>Actualizaciones</h2><p class="update-state" role="status"></p><dl class="update-versions"></dl><pre class="update-notes"></pre><a class="update-link" target="_blank" rel="noopener" hidden>Ver versión y descargas en GitHub</a><div class="actions"><button type="button" data-update="close">Cerrar</button><button type="button" data-update="later" hidden>Recordar más tarde</button><button type="button" class="primary" data-update="check">Buscar actualizaciones</button></div>`;
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
        idle: "Pulsa Buscar actualizaciones para consultar versiones estables.",
        checking: "Buscando versiones estables…",
        current: "La versión instalada está al día.",
        available: "Hay una versión estable superior disponible.",
        unavailable:
          "No se pudo consultar GitHub. Puedes reintentarlo más tarde.",
      }[result.status] ||
      result.error ||
      "Consulta finalizada.";
    const versions = updates.querySelector(".update-versions");
    versions.replaceChildren();
    for (const [label, value] of [
      ["Instalada", result.installed],
      ["Disponible", result.available],
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
      console.warn("Actualizaciones:", error.message);
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
