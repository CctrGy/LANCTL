"use strict";
// Explicit labels only. Never inspect arbitrary text, logs, user data or HTML.
(() => {
  let code = "en";
  let strings = Object.assign(Object.create(null), window.LANCTL_DEFAULT_STRINGS || {});
  const bindings = new Map();
  const attributeBindings = new Map();
  const attributes = ["title", "placeholder", "aria-label", "alt"];
  function t(key, values = {}) {
    const template = Object.hasOwn(strings, key) ? strings[key] : key;
    return template.replace(/\{\{|\}\}|\{([A-Za-z_][A-Za-z0-9_]*)(?:![sra])?(?::[^{}]*)?\}/g,
      (token, name) => {
        if (token === "{{") return "{";
        if (token === "}}") return "}";
        if (!Object.hasOwn(values, name)) throw new Error(`Missing language argument: ${name}`);
        return String(values[name]);
      });
  }
  function html(key, values = {}) {
    return t(key, values).replace(/[&<>"']/g, character => ({
      "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
    })[character]);
  }
  function apply(root = document) {
    const elements = [];
    if (root.nodeType === 1) elements.push(root);
    if (root.querySelectorAll) elements.push(...root.querySelectorAll(
      "[data-i18n],[data-i18n-title],[data-i18n-placeholder],[data-i18n-aria-label],[data-i18n-alt]"));
    for (const element of elements) {
      const key = element.getAttribute("data-i18n");
      if (key && Object.hasOwn(strings, key) && element.textContent !== t(key)) element.textContent = t(key);
      for (const attribute of attributes) {
        const attrKey = element.getAttribute(`data-i18n-${attribute}`);
        if (attrKey && Object.hasOwn(strings, attrKey)) element.setAttribute(attribute, t(attrKey));
      }
    }
  }
  function setCatalog(payload) {
    if (!payload || typeof payload.code !== "string" || !payload.strings || typeof payload.strings !== "object") {
      throw new Error("Invalid presentation language catalog");
    }
    const next = Object.create(null);
    for (const [key, value] of Object.entries(payload.strings)) {
      if (typeof value !== "string") throw new Error("Invalid presentation translation");
      next[key] = value;
    }
    strings = next;
    code = payload.code;
    document.documentElement.lang = code;
    apply();
    for (const [element, binding] of bindings) {
      if (!element.isConnected) {bindings.delete(element); continue;}
      binding.node.data = t(binding.key, binding.values);
    }
    for (const [element, attributes] of attributeBindings) {
      if (!element.isConnected) {attributeBindings.delete(element); continue;}
      for (const [attribute, key] of attributes) element.setAttribute(attribute, t(key));
    }
    window.dispatchEvent(new CustomEvent("lanctl-language-ready", {detail: {code}}));
  }
  function bindText(element, key, values = {}) {
    element.textContent = t(key, values);
    if (!element.firstChild) element.append(document.createTextNode(""));
    bindings.set(element, {node: element.firstChild, key, values});
    return element.textContent;
  }
  function bindAttribute(element, attribute, key) {
    if (!attributes.includes(attribute)) throw new Error("Unsupported language attribute");
    const registered = attributeBindings.get(element) || new Map();
    registered.set(attribute, key);
    attributeBindings.set(element, registered);
    element.setAttribute(attribute, t(key));
  }
  const observer = new MutationObserver(records => {
    for (const record of records) for (const node of record.addedNodes) {
      if (node.nodeType === 1) apply(node);
    }
  });
  observer.observe(document.documentElement, {childList: true, subtree: true});
  window.addEventListener("DOMContentLoaded", () => apply());
  window.LanctlI18n = Object.freeze({t, html, apply, setCatalog, bindText, bindAttribute, get code() {return code;}});
})();
