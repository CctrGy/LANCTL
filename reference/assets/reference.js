(() => {
  "use strict";

  const data = window.LANCTL_REFERENCE;
  const search = document.querySelector("#search");
  const entriesRoot = document.querySelector("#entries");
  const categoriesRoot = document.querySelector("#category-list");
  const resultCount = document.querySelector("#result-count");
  const emptyState = document.querySelector("#empty-state");
  const activeFilter = document.querySelector("#active-filter");
  const detail = document.querySelector("#detail");
  const detailContent = document.querySelector("#detail-content");
  const backdrop = document.querySelector("#backdrop");
  let selectedCategory = "";

  const escapeHtml = (value = "") => String(value).replace(/[&<>'"]/g, (char) => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "'": "&#39;", '"': "&quot;",
  })[char]);
  const normalized = (value) => String(value || "").normalize("NFD").replace(/[\u0300-\u036f]/g, "").toLowerCase();
  const searchable = (entry) => normalized(JSON.stringify(entry));
  const docUrl = (name) => `https://github.com/CctrGy/LANCTL/blob/main/docs/${encodeURIComponent(name)}`;

  document.querySelector("#version").textContent = `v${data.meta.version}`;

  function renderCategories() {
    const counts = new Map(data.categories.map((category) => [category, 0]));
    data.entries.forEach((entry) => counts.set(entry.category, (counts.get(entry.category) || 0) + 1));
    categoriesRoot.innerHTML = data.categories.map((category) => `
      <button class="category-button" type="button" data-category="${escapeHtml(category)}" aria-pressed="${selectedCategory === category}">
        ${escapeHtml(category)} <span>${counts.get(category)}</span>
      </button>`).join("");
  }

  function filteredEntries() {
    const terms = normalized(search.value).trim().split(/\s+/).filter(Boolean);
    return data.entries.filter((entry) => {
      if (selectedCategory && entry.category !== selectedCategory) return false;
      const haystack = searchable(entry);
      return terms.every((term) => haystack.includes(term));
    });
  }

  function render() {
    const matches = filteredEntries();
    const groups = new Map();
    matches.forEach((entry) => {
      if (!groups.has(entry.category)) groups.set(entry.category, []);
      groups.get(entry.category).push(entry);
    });
    entriesRoot.innerHTML = [...groups.entries()].map(([category, items]) => `
      <section class="entry-section" id="category-${normalized(category).replace(/[^a-z0-9]+/g, "-")}">
        <h3>${escapeHtml(category)}</h3>
        ${items.map((entry) => `
          <button class="entry-row" type="button" data-entry="${escapeHtml(entry.id)}">
            <span class="entry-group">${escapeHtml(entry.group)}</span>
            <span class="entry-name">${escapeHtml(entry.title || entry.name)}</span>
            <span class="entry-description">${escapeHtml(entry.description)}</span>
            <span class="entry-arrow" aria-hidden="true">→</span>
          </button>`).join("")}
      </section>`).join("");
    resultCount.textContent = `${matches.length} de ${data.entries.length} entradas`;
    emptyState.hidden = matches.length !== 0;
    activeFilter.hidden = !selectedCategory;
    activeFilter.textContent = selectedCategory ? `Categoría activa: ${selectedCategory}` : "";
    renderCategories();
  }

  function openDetail(entry, updateHash = true) {
    const args = entry.arguments || [];
    const examples = entry.examples || [];
    const docs = entry.docs || [];
    detailContent.innerHTML = `
      <span class="detail-kind">${escapeHtml(entry.kind)} · ${escapeHtml(entry.category)}</span>
      <h2 id="detail-title">${escapeHtml(entry.title || entry.name)}</h2>
      <p class="detail-summary">${escapeHtml(entry.description)}</p>
      ${entry.usage ? `<h3>Sintaxis</h3><pre><code>${escapeHtml(entry.usage)}</code></pre>` : ""}
      ${examples.length ? `<h3>Ejemplos</h3>${examples.map((item) => `<pre><code>${escapeHtml(item)}</code></pre>`).join("")}` : ""}
      ${entry.children?.length ? `<h3>Subcomandos</h3><p>${entry.children.map((item) => `<code>${escapeHtml(item)}</code>`).join(" · ")}</p>` : ""}
      ${entry.aliases?.length ? `<h3>Alias</h3><p>${entry.aliases.map((item) => `<code>${escapeHtml(item)}</code>`).join(" · ")}</p>` : ""}
      ${args.length ? `<h3>Argumentos y opciones</h3><dl class="argument-list">${args.map((arg) => `
        <div class="argument"><dt>${escapeHtml(arg.label)}</dt><dd>${escapeHtml(arg.description || "Sin descripción adicional.")}${arg.choices.length ? ` Valores: ${escapeHtml(arg.choices.join(", "))}.` : ""}${arg.default ? ` Predeterminado: ${escapeHtml(arg.default)}.` : ""}</dd></div>`).join("")}</dl>` : ""}
      ${entry.details && entry.kind === "concept" ? `<h3>Descripción</h3><p>${escapeHtml(entry.details)}</p>` : ""}
      ${docs.length ? `<h3>Documentación relacionada</h3><div class="doc-links">${docs.map((name) => `<a href="${docUrl(name)}">${escapeHtml(name)}</a>`).join("")}</div>` : ""}`;
    detail.classList.add("open");
    detail.setAttribute("aria-hidden", "false");
    backdrop.hidden = false;
    document.body.classList.add("drawer-open");
    if (updateHash) history.replaceState(null, "", `#${entry.id}`);
    document.querySelector("#close-detail").focus();
  }

  function closeDetail(updateHash = true) {
    detail.classList.remove("open");
    detail.setAttribute("aria-hidden", "true");
    backdrop.hidden = true;
    document.body.classList.remove("drawer-open");
    if (updateHash && location.hash.startsWith("#command-") || updateHash && location.hash.startsWith("#concept-") || updateHash && location.hash.startsWith("#doc-")) {
      history.replaceState(null, "", `${location.pathname}${location.search}`);
    }
  }

  categoriesRoot.addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    selectedCategory = selectedCategory === button.dataset.category ? "" : button.dataset.category;
    render();
    document.querySelector("#catalog").scrollIntoView();
  });
  entriesRoot.addEventListener("click", (event) => {
    const button = event.target.closest("[data-entry]");
    if (!button) return;
    const entry = data.entries.find((item) => item.id === button.dataset.entry);
    if (entry) openDetail(entry);
  });
  search.addEventListener("input", render);
  document.querySelector("#clear-filters").addEventListener("click", () => { search.value = ""; selectedCategory = ""; render(); });
  document.querySelector("#close-detail").addEventListener("click", () => closeDetail());
  backdrop.addEventListener("click", () => closeDetail());
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement !== search) { event.preventDefault(); search.focus(); }
    if (event.key === "Escape") detail.classList.contains("open") ? closeDetail() : (search.value = "", render());
  });

  render();
  const initialEntry = data.entries.find((entry) => `#${entry.id}` === location.hash);
  if (initialEntry) openDetail(initialEntry, false);
})();
