"use strict";
(() => {
  const form = document.querySelector("#account-form"),
    status = document.querySelector("#status"),
    cancel = document.querySelector("#cancel"),
    submit = document.querySelector('[type="submit"]');
  let busy = false, complete = false;
  async function call(method, ...args) {
    const result = await window.pywebview.api[method](...args);
    if (!result.ok) throw new Error(result.error || window.LanctlI18n.t("LANCTL.UI.VIEW.COULD_NOT_COMPLETE_THE_OPERATION"));
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
      message(window.LanctlI18n.t("LANCTL.UI.VIEW.PASSWORDS_DO_NOT_MATCH"), "error");
      return;
    }
    busy = true; submit.disabled = true; cancel.disabled = true;
    message(window.LanctlI18n.t("LANCTL.UI.VIEW.CREATING_ACCOUNT"));
    try {
      const result = await call("create_initial_user", form.elements.username.value.trim(),
        form.elements.password.value, form.elements.confirmation.value);
      complete = true;
      message(result.message || window.LanctlI18n.t("LANCTL.UI.VIEW.REMOTE_ACCESS_ACCOUNT_CREATED"), "success");
      for (const input of form.querySelectorAll("input")) input.disabled = true;
      submit.hidden = true; window.LanctlI18n.bindText(cancel,"LANCTL.UI.WORD.FINISH");
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
        ? window.LanctlI18n.t("LANCTL.UI.VIEW.THE_SERVICE_ALREADY_HAS_ACCOUNTS_ALL_ARE_PRESERVED_USE_LANACCESS_TO_MANAGE_THEM")
        : window.LanctlI18n.t("LANCTL.UI.VIEW.THE_FIRST_LANACCESS_SERVICE_ADMINISTRATOR_ACCOUNT_WILL_BE_CREATED_AVAILABLE_FOR_REMOTE_ACCESS_W");
      window.LanctlI18n.bindText(document.querySelector("#account-role"),"LANCTL.UI.VIEW.CREATING_THIS_ACCOUNT_DOES_NOT_ENABLE_HTTPS_SSH_OR_FIREWALL_RULES_THOSE_SERVICES_REQUIRE_LATER_");
      if (!result.canCreate) return;
      for (const input of form.querySelectorAll("input")) input.disabled = false;
      submit.disabled = false;
      form.elements.username.focus();
    } catch (error) { message(error.message, "error"); }
  });
})();
