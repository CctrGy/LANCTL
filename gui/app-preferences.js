"use strict";

// Shared native desktop presentation. Preferences are validated and stored by Core.
(() => {
  if (/^https?:$/.test(window.location.protocol)) return;
  const rpc = async (method, ...args) => {
    const result = await window.pywebview.api[method](...args);
    if (!result.ok)
      throw new Error(result.error || window.LanctlI18n.t("LANCTL.UI.TEXT.COULD_NOT_COMPLETE_THE_OPERATION"));
    return result;
  };
  let saved = null,
    editing = false,
    reading = false;
  const componentStyles = new Map();
  const aliases = {
    "--color-background": "--bg",
    "--color-surface": "--surface",
    "--color-border": "--line",
    "--color-text": "--text",
    "--color-text-muted": "--muted",
    "--color-accent": "--lime",
  };
  function apply(payload, preferences = payload.preferences) {
    const root = document.documentElement;
    const selected = payload.themes.find((t) => t.id === preferences.theme);
    const theme =
      preferences === payload.preferences
        ? payload.theme
        : {
            ...selected,
            tokens: { ...selected.tokens, ...payload.theme.pluginTokens },
            components:
              payload.theme.pluginComponents || payload.theme.components,
          };
    for (const [key, value] of Object.entries(theme?.tokens || {})) {
      root.style.setProperty(key, value);
      if (aliases[key]) root.style.setProperty(aliases[key], value);
    }
    root.dataset.density = preferences.density;
    const rgb = (key) =>
      (root.style.getPropertyValue(key).match(/[a-f0-9]{2}/gi) || [])
        .slice(0, 3)
        .map((c) => parseInt(c, 16));
    const brightness = (color) =>
      color.length === 3
        ? color[0] * 0.299 + color[1] * 0.587 + color[2] * 0.114
        : 0;
    root.style.colorScheme =
      brightness(rgb("--color-background")) > 150 ? "light" : "dark";
    root.style.setProperty(
      "--gui-primary-ink",
      rgb("--color-accent").reduce((sum, value, index) => {
        const channel = value / 255;
        return (
          sum +
          [0.2126, 0.7152, 0.0722][index] *
            (channel <= 0.04045
              ? channel / 12.92
              : ((channel + 0.055) / 1.055) ** 2.4)
        );
      }, 0) > 0.179
        ? "#101810"
        : "#ffffff",
    );
    for (const [element, keys] of componentStyles)
      for (const key of keys) element.style.removeProperty(key);
    componentStyles.clear();
    for (const [id, tokens] of Object.entries(theme.components || {})) {
      document
        .querySelectorAll(`[data-component-id="${id}"]`)
        .forEach((element) => {
          componentStyles.set(element, new Set(Object.keys(tokens)));
          for (const [key, value] of Object.entries(tokens))
            element.style.setProperty(key, value);
        });
    }
    root.dataset.reducedMotion = String(preferences.reducedMotion);
    root.style.setProperty("--gui-font-scale", preferences.fontScale);
    root.classList.add("gui-preferences-active");
  }
  const dialog = document.createElement("dialog");
  dialog.className = "preferences-dialog";
  dialog.setAttribute("aria-label", window.LanctlI18n.t("LANCTL.UI.VIEW.INTERFACE_APPEARANCE"));
  dialog.innerHTML = `<form><h2><span data-i18n="LANCTL.UI.TEXT.APPEARANCE">Apariencia</span></h2><p><span data-i18n="LANCTL.UI.HTML.PREVIEW_IN_THIS_WINDOW_APPLY_SAVES_THE_SELECTION_FOR_THE_ENTIRE_SUITE">Vista previa en esta ventana. Aplicar guarda la selección para toda la suite.</span></p>
    <div class="theme-choices" role="group" aria-label="Tema" data-i18n-aria-label="LANCTL.UI.TEXT.THEME"></div>
    <label><span data-i18n="LANCTL.UI.HTML.DENSITY">Densidad</span><select name="density"><option value="comfortable" data-i18n="LANCTL.UI.SCREEN.COMFORTABLE">Cómoda</option><option value="compact" data-i18n="LANCTL.UI.HTML.COMPACT">Compacta</option></select></label>
    <label><span data-i18n="LANCTL.UI.HTML.TEXT_SIZE">Tamaño del texto</span><select name="fontScale"><option value="0.9">90 %</option><option value="1">100 %</option><option value="1.1">110 %</option><option value="1.2">120 %</option><option value="1.3">130 %</option></select></label>
    <label class="check"><input type="checkbox" name="reducedMotion"> <span data-i18n="LANCTL.UI.TEXT.REDUCE_ANIMATIONS">Reducir animaciones</span></label>
    <p role="status" class="preferences-feedback"></p><div class="actions"><button type="button" data-preference="reset"><span data-i18n="LANCTL.UI.HTML.RESET">Restablecer</span></button><button type="button" data-preference="cancel"><span data-i18n="LANCTL.INVENTORY.MANUAL.CANCEL">Cancelar</span></button><button class="primary" type="submit"><span data-i18n="LANCTL.UI.TEXT.APPLY">Aplicar</span></button></div></form>`;
  document.body.append(dialog);
  let draft;
  function preview() {
    const form = dialog.querySelector("form");
    draft.density = form.elements.density.value;
    draft.fontScale = Number(form.elements.fontScale.value);
    draft.reducedMotion = form.elements.reducedMotion.checked;
    apply(saved, draft);
    dialog
      .querySelectorAll("[data-theme]")
      .forEach((b) =>
        b.setAttribute("aria-pressed", String(b.dataset.theme === draft.theme)),
      );
  }
  function fill() {
    const form = dialog.querySelector("form");
    form.elements.density.value = draft.density;
    if (
      ![...form.elements.fontScale.options].some(
        (option) => option.value === String(draft.fontScale),
      )
    )
      form.elements.fontScale.add(
        new Option(
          Math.round(draft.fontScale * 100) + " %",
          String(draft.fontScale),
        ),
      );
    form.elements.fontScale.value = String(draft.fontScale);
    form.elements.reducedMotion.checked = draft.reducedMotion;
    preview();
  }
  function cancel() {
    if (saved) apply(saved);
    editing = false;
    dialog.close();
  }
  async function open() {
    saved = await rpc("gui_preferences");
    draft = { ...saved.preferences };
    editing = true;
    const choices = dialog.querySelector(".theme-choices");
    choices.replaceChildren();
    for (const theme of saved.themes) {
      const button = document.createElement("button");
      button.type = "button";
      button.dataset.theme = theme.id;
      button.textContent = theme.name;
      const swatches = document.createElement("span");
      swatches.className = "theme-swatches";
      swatches.setAttribute("aria-hidden", "true");
      for (const token of [
        "--color-background",
        "--color-surface",
        "--color-accent",
      ]) {
        const swatch = document.createElement("i");
        swatch.style.backgroundColor = theme.tokens[token];
        swatches.append(swatch);
      }
      button.prepend(swatches);
      button.onclick = () => {
        draft.theme = theme.id;
        preview();
      };
      choices.append(button);
    }
    dialog.querySelector(".preferences-feedback").textContent =
      saved.effectivePlugin
        ? window.LanctlI18n.t("LANCTL.UI.FRAGMENT.PLUGIN") +
          saved.effectivePlugin +
          window.LanctlI18n.t("LANCTL.UI.FRAGMENT.EXTENDS_THE_SELECTED_PALETTE")
        : "";
    fill();
    dialog.showModal();
  }
  dialog.addEventListener("change", preview);
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    cancel();
  });
  dialog.querySelector('[data-preference="cancel"]').onclick = cancel;
  dialog.querySelector('[data-preference="reset"]').onclick = () => {
    draft = {
      theme: "graphite",
      density: "comfortable",
      fontScale: 1,
      reducedMotion: false,
    };
    fill();
  };
  dialog.querySelector("form").onsubmit = async (event) => {
    event.preventDefault();
    const submit = dialog.querySelector('[type="submit"]');
    submit.disabled = true;
    try {
      saved = await rpc("save_gui_preferences", draft);
      apply(saved);
      editing = false;
      dialog.close();
    } catch (error) {
      dialog.querySelector(".preferences-feedback").textContent = error.message;
    } finally {
      submit.disabled = false;
    }
  };
  const button = document.createElement("button");
  button.type = "button";
  button.id = "gui-appearance";
  button.hidden = true;
  window.LanctlI18n.bindText(button,"LANCTL.UI.TEXT.APPEARANCE");
  button.onclick = () =>
    open().catch((error) => {
      if (typeof message === "function") message(error.message, true);
    });
  const footer = document.querySelector("footer > div, footer > span");
  footer?.append(button);
  async function sync() {
    if (editing || reading || !window.pywebview?.api.gui_preferences) return;
    reading = true;
    try {
      const result = await rpc("gui_preferences");
      button.hidden = false;
      saved = result;
      apply(result);
    } catch (error) {
      console.warn(window.LanctlI18n.t("LANCTL.UI.VIEW.GUI_PREFERENCES"), error.message);
    } finally {
      reading = false;
    }
  }
  window.addEventListener("pywebviewready", sync);
  setInterval(sync, 3000);
  window.guiAppearance = { open, sync };
})();
