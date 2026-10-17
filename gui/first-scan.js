"use strict";
(() => {
  let pending = false,
    first = false,
    options;
  const button = document.createElement("button");
  button.type = "button";
  button.id = "scan-target";
  button.textContent = "Red de escaneo";
  button.hidden = true;
  document.querySelector(".scan-controls")?.append(button);
  const dialog = document.createElement("dialog");
  dialog.className = "support-dialog first-scan-dialog";
  dialog.setAttribute("aria-label", "Red de escaneo");
  dialog.innerHTML = `<form><h2>Red de escaneo</h2><p class="first-scan-network"></p><p class="first-scan-notice"></p><label>Interfaz de red<select name="source" required></select></label><label>Rango de red (CIDR)<input name="range" placeholder="192.168.1.0/24" required></label><label class="first-scan-profile">Perfil de escaneo<select name="profile"><option value="fast">Rápido</option><option value="normal" selected>Normal</option><option value="accurate">Detallado</option></select></label><p role="status" class="first-scan-error"></p><div class="actions"><button type="button" data-first-scan="cancel">Ahora no</button><button type="button" data-first-scan="retry">Actualizar interfaces</button><button type="submit" class="primary">Confirmar y escanear</button></div></form>`;
  document.body.append(dialog);
  function change() {
    const form = dialog.querySelector("form"),
      explicit = first || Boolean(form.elements.source.value);
    form.elements.range.disabled = !explicit;
    form.elements.range.required = explicit;
    form.elements.source.required = first;
    if (!explicit)
      dialog.querySelector(".first-scan-notice").textContent =
        "Se conserva el escaneo habitual con las rutas y la configuración del sistema.";
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
      source.add(new Option("Rutas del sistema (configuración habitual)", ""));
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
      : "No se han podido obtener interfaces de red disponibles. Puedes reintentar; el primer escaneo sigue pendiente.";
    dialog.querySelector(".first-scan-network").textContent = result.localIp
      ? "Dirección local detectada: " + result.localIp
      : "Selecciona un adaptador disponible.";
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
      ? "Primer escaneo de la red"
      : "Red de escaneo";
    dialog.querySelector('[type="submit"]').textContent = first
      ? "Confirmar y escanear"
      : "Aplicar";
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
      ? "Red: " +
        options.networks.find((nic) => nic.id === window.lanipScanTarget.source)
          .name
      : "Red de escaneo";
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
