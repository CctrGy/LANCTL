"use strict";
(() => {
  const form = document.querySelector("#account-form"),
    status = document.querySelector("#status"),
    cancel = document.querySelector("#cancel"),
    submit = document.querySelector('[type="submit"]');
  let busy = false, complete = false;
  async function call(method, ...args) {
    const result = await window.pywebview.api[method](...args);
    if (!result.ok) throw new Error(result.error || "No se pudo completar la operación.");
    return result;
  }
  function message(text, kind = "") {
    status.textContent = text;
    status.className = kind;
  }
  async function close() {
    if (busy) return;
    form.elements.password.value = "";
    form.elements.confirmation.value = "";
    try { await call("request_close"); }
    catch (error) { message(error.message, "error"); }
  }
  window.remoteSetupClose = close;
  cancel.onclick = close;
  document.addEventListener("keydown", event => {
    if (event.key === "Escape") close();
  });
  form.onsubmit = async event => {
    event.preventDefault();
    if (busy || complete) return;
    if (form.elements.password.value !== form.elements.confirmation.value) {
      message("Las contraseñas no coinciden.", "error");
      return;
    }
    busy = true; submit.disabled = true; cancel.disabled = true;
    message("Creando la cuenta…");
    try {
      const result = await call("create_initial_user", form.elements.username.value.trim(),
        form.elements.password.value, form.elements.confirmation.value);
      complete = true;
      message(result.message || "Cuenta de acceso remoto creada.", "success");
      for (const input of form.querySelectorAll("input")) input.disabled = true;
      submit.hidden = true; cancel.textContent = "Finalizar";
    } catch (error) { message(error.message, "error"); }
    finally {
      form.elements.password.value = "";
      form.elements.confirmation.value = "";
      busy = false; submit.disabled = false; cancel.disabled = false;
    }
  };
  window.addEventListener("pywebviewready", async () => {
    try {
      const result = await call("setup_status");
      document.querySelector("#scope").textContent = result.hasUsers
        ? "El servicio ya tiene cuentas. Se conservan todas; utiliza LANACCESS para gestionarlas."
        : "Se creará la primera cuenta administrativa del servicio LANACCESS, disponible para el acceso remoto cuando lo configures.";
      document.querySelector("#account-role").textContent = "Crear esta cuenta no activa HTTPS, SSH ni reglas de firewall. Estos servicios requieren configuración posterior.";
      if (!result.canCreate) return;
      for (const input of form.querySelectorAll("input")) input.disabled = false;
      submit.disabled = false;
      form.elements.username.focus();
    } catch (error) { message(error.message, "error"); }
  });
})();
