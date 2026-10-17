"use strict";

// An installer request opens a confirmation. It never triggers probes by itself.
window.addEventListener("pywebviewready", async () => {
  if (!window.pywebview?.api.first_scan_options) return;
  try {
    for (let attempt = 0; attempt < 100 && !inventorySnapshot; attempt++)
      await new Promise((resolve) => setTimeout(resolve, 100));
    if (!inventorySnapshot) return;
    const result = await call("first_scan_options");
    if (!result.requested) return;
    const dialog = document.createElement("dialog");
    dialog.className = "support-dialog first-scan-dialog";
    dialog.setAttribute("aria-label", "Primer escaneo");
    dialog.innerHTML = `<form><h2>Primer escaneo de la red</h2><p class="first-scan-network"></p><p class="first-scan-notice"></p><label>Rango de red (CIDR)<input name="range" placeholder="192.168.1.0/24" required></label><label>Perfil de escaneo<select name="profile"><option value="fast">Rápido</option><option value="normal" selected>Normal</option><option value="accurate">Detallado</option></select></label><p role="status" class="first-scan-error"></p><div class="actions"><button type="button" data-first-scan="cancel">Ahora no</button><button type="submit" class="primary">Confirmar y escanear</button></div></form>`;
    dialog.querySelector(".first-scan-network").textContent = result.localIp
      ? "Dirección local detectada: " + result.localIp
      : "No se ha detectado una dirección local.";
    dialog.querySelector(".first-scan-notice").textContent =
      result.notice +
      (result.rangeEstimated
        ? " El rango sugerido supone una máscara /24: revísalo antes de continuar."
        : "");
    dialog.querySelector('[name="range"]').value = result.range;
    dialog.querySelector('[data-first-scan="cancel"]').onclick = () =>
      dialog.close();
    dialog.querySelector("form").onsubmit = async (event) => {
      event.preventDefault();
      const submit = event.target.querySelector('[type="submit"]');
      submit.disabled = true;
      try {
        await call("save_settings", {
          range: event.target.elements.range.value,
        });
        $("#scan-profile").value = event.target.elements.profile.value;
        dialog.close();
        $("#scan-network").click();
      } catch (error) {
        dialog.querySelector(".first-scan-error").textContent = error.message;
      } finally {
        submit.disabled = false;
      }
    };
    document.body.append(dialog);
    dialog.showModal();
  } catch (error) {
    message(error.message, true);
  }
});
