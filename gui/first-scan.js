"use strict";
(() => {
  let pending = false,
    first = false,
    options;
  const button = document.createElement("button");
  button.type = "button";
  button.id = "scan-target";
  window.LanctlI18n.bindText(button,"LANCTL.UI.VIEW.SCAN_NETWORK");
  button.hidden = true;
  document.querySelector(".scan-controls")?.append(button);
  const dialog = document.createElement("dialog");
  dialog.className = "support-dialog first-scan-dialog";
  dialog.setAttribute("aria-label", window.LanctlI18n.t("LANCTL.UI.VIEW.SCAN_NETWORK"));
  dialog.innerHTML = `<form><h2><span data-i18n="LANCTL.UI.VIEW.SCAN_NETWORK">Red de escaneo</span></h2><p class="first-scan-network"></p><p class="first-scan-notice"></p><label><span data-i18n="LANCTL.UI.TEXT.NETWORK_INTERFACE">Interfaz de red</span><select name="source" required></select></label><label><span data-i18n="LANCTL.UI.HTML.NETWORK_RANGE_CIDR">Rango de red (CIDR)</span><input name="range" placeholder="192.168.1.0/24" required></label><label class="first-scan-profile"><span data-i18n="LANCTL.UI.TEXT.SCAN_PROFILE">Perfil de escaneo</span><select name="profile"><option value="fast" data-i18n="LANCTL.UI.TEXT.FAST">Rápido</option><option value="normal" selected data-i18n="LANCTL.UI.TEXT.NORMAL">Normal</option><option value="accurate" data-i18n="LANCTL.UI.HTML.DETAILED">Detallado</option></select></label><p role="status" class="first-scan-error"></p><div class="actions"><button type="button" data-first-scan="cancel"><span data-i18n="LANCTL.UI.TEXT.NOT_NOW">Ahora no</span></button><button type="button" data-first-scan="retry"><span data-i18n="LANCTL.UI.HTML.REFRESH_INTERFACES">Actualizar interfaces</span></button><button type="submit" class="primary"><span data-i18n="LANCTL.UI.VIEW.CONFIRM_AND_SCAN">Confirmar y escanear</span></button></div></form>`;
  document.body.append(dialog);
  function change() {
    const form = dialog.querySelector("form"),
      explicit = first || Boolean(form.elements.source.value);
    form.elements.range.disabled = !explicit;
    form.elements.range.required = explicit;
    form.elements.source.required = first;
    if (!explicit)
      window.LanctlI18n.bindText(dialog.querySelector(".first-scan-notice"),"LANCTL.UI.VIEW.THE_USUAL_SCAN_WITH_SYSTEM_ROUTES_AND_SETTINGS_IS_PRESERVED");
    else if (options.networks?.length)
      dialog.querySelector(".first-scan-notice").textContent = options.notice;
  }
  function populate(result) {
    options = result;
    const form = dialog.querySelector("form"),
      source = form.elements.source,
      selected = window.lanipScanTarget;
    source.replaceChildren();
    if (!first)
      source.add(new Option(window.LanctlI18n.t("LANCTL.UI.VIEW.SYSTEM_ROUTES_USUAL_CONFIGURATION"), ""));
    for (const nic of result.networks || [])
      source.add(
        new Option(`${nic.name} · ${nic.address} (${nic.network})`, nic.id),
      );
    if (
      selected &&
      [...source.options].some((option) => option.value === selected.source)
    )
      source.value = selected.source;
    else if (first && source.options.length)
      source.value = (
        result.networks.find((nic) => nic.address === result.localIp) ||
        result.networks[0]
      ).id;
    form.elements.range.value =
      selected?.network ||
      result.networks?.find((nic) => nic.id === source.value)?.network ||
      result.range ||
      "";
    const available = !first || Boolean(result.networks?.length);
    dialog.querySelector('[type="submit"]').disabled = !available;
    source.disabled = !available;
    dialog.querySelector(".first-scan-notice").textContent = available
      ? result.notice
      : window.LanctlI18n.t("LANCTL.UI.VIEW.COULD_NOT_OBTAIN_AVAILABLE_NETWORK_INTERFACES_YOU_CAN_RETRY_THE_FIRST_SCAN_IS_STILL_PENDING");
    dialog.querySelector(".first-scan-network").textContent = result.localIp
      ? window.LanctlI18n.t("LANCTL.UI.FRAGMENT.DETECTED_LOCAL_ADDRESS") + result.localIp
      : window.LanctlI18n.t("LANCTL.UI.VIEW.SELECT_AN_AVAILABLE_ADAPTER");
    change();
  }
  dialog.querySelector('[name="source"]').onchange = (event) => {
    const nic = options.networks?.find((nic) => nic.id === event.target.value);
    if (nic) dialog.querySelector('[name="range"]').value = nic.network;
    change();
  };
  async function show(initial = false, result = null) {
    result ||= await call(initial ? "first_scan_options" : "scan_targets");
    if (initial && !result.requested) {
      pending = false;
      initial = false;
      result = await call("scan_targets");
    }
    first = initial;
    dialog.querySelector("h2").textContent = first
      ? window.LanctlI18n.t("LANCTL.UI.VIEW.FIRST_NETWORK_SCAN")
      : window.LanctlI18n.t("LANCTL.UI.VIEW.SCAN_NETWORK");
    dialog.querySelector('[type="submit"]').textContent = first
      ? window.LanctlI18n.t("LANCTL.UI.VIEW.CONFIRM_AND_SCAN")
      : window.LanctlI18n.t("LANCTL.UI.TEXT.APPLY");
    dialog.querySelector(".first-scan-profile").hidden = !first;
    dialog.querySelector(".first-scan-error").textContent = "";
    populate(result);
    if (!dialog.open) dialog.showModal();
  }
  dialog.querySelector('[data-first-scan="retry"]').onclick = () =>
    show(first).catch((error) => {
      dialog.querySelector(".first-scan-error").textContent = error.message;
    });
  dialog.querySelector('[data-first-scan="cancel"]').onclick = async () => {
    try {
      if (first && options.networks?.length) {
        await call("dismiss_first_scan");
        pending = false;
      }
      dialog.close();
    } catch (error) {
      dialog.querySelector(".first-scan-error").textContent = error.message;
    }
  };
  dialog.querySelector("form").onsubmit = async (event) => {
    event.preventDefault();
    const form = event.target;
    window.lanipScanTarget = form.elements.source.value
      ? {
          source: form.elements.source.value,
          network: form.elements.range.value.trim(),
        }
      : null;
    if (first && !window.lanipScanTarget) return;
    button.textContent = window.lanipScanTarget
      ? window.LanctlI18n.t("LANCTL.UI.FRAGMENT.NETWORK") +
        options.networks.find((nic) => nic.id === window.lanipScanTarget.source)
          .name
      : window.LanctlI18n.t("LANCTL.UI.VIEW.SCAN_NETWORK");
    const start = first;
    if (start) $("#scan-profile").value = form.elements.profile.value;
    dialog.close();
    if (start) $("#scan-network").click();
  };
  window.lanipScanCompleted = () => {
    pending = false;
  };
  button.onclick = () =>
    show(pending).catch((error) => message(error.message, true));
  window.addEventListener("pywebviewready", async () => {
    if (
      !window.pywebview?.api.first_scan_options ||
      !window.pywebview?.api.scan_targets
    )
      return;
    try {
      for (let attempt = 0; attempt < 100 && !inventorySnapshot; attempt++)
        await new Promise((resolve) => setTimeout(resolve, 100));
      if (!inventorySnapshot) return;
      button.hidden = false;
      const result = await call("first_scan_options");
      pending = result.requested;
      if (pending) await show(true, result);
    } catch (error) {
      message(error.message, true);
    }
  });
})();
