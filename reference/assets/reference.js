(() => {
  "use strict";
  const data = window.LANCTL_REFERENCE;
  const search = document.querySelector("#search");
  const catalog = document.querySelector("#catalog");
  const entriesRoot = document.querySelector("#entries");
  const categoriesRoot = document.querySelector("#category-list");
  const workflowsRoot = document.querySelector("#workflow-list");
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
  const compatibilityLabel = (item) => {
    const value = item.compatibility || {};
    if (value.only) return `*Solo versión ${value.only}`;
    if (value.since && value.until) return `*Versiones ${value.since}–${value.until}`;
    if (value.since) return `*Desde la versión ${value.since}`;
    if (value.until) return `*Hasta la versión ${value.until}`;
    return `*Verificado en la versión ${value.verified || data.meta.version}`;
  };
  document.querySelector("#version").textContent = `v${data.meta.version}`;

  function renderCategories() {
    const counts = new Map(data.categories.map((category) => [category, 0]));
    data.entries.forEach((entry) => counts.set(entry.category, (counts.get(entry.category) || 0) + 1));
    categoriesRoot.innerHTML = data.categories.map((category) => `
      <button class="category-button" type="button" data-category="${escapeHtml(category)}" aria-pressed="${selectedCategory === category}">
        ${escapeHtml(category)} <span>${counts.get(category)}</span>
      </button>`).join("");
  }

  function renderWorkflows() {
    workflowsRoot.innerHTML = data.workflows.map((workflow, index) => `
      <button class="workflow-card" type="button" data-workflow="${escapeHtml(workflow.id)}">
        <span class="workflow-number">${String(index + 1).padStart(2, "0")}</span>
        <span><h3>${escapeHtml(workflow.title)}</h3><p>${escapeHtml(workflow.summary)}</p>
          <span class="workflow-meta"><span>${escapeHtml(workflow.level)}</span><span>${escapeHtml(workflow.time)}</span><span>${workflow.steps.length} pasos</span></span>
          <small class="version-note">${escapeHtml(compatibilityLabel(workflow))}</small>
        </span><span class="workflow-arrow" aria-hidden="true">→</span>
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

  function renderCatalog() {
    const matches = filteredEntries();
    const groups = new Map();
    matches.forEach((entry) => {
      if (!groups.has(entry.category)) groups.set(entry.category, []);
      groups.get(entry.category).push(entry);
    });
    entriesRoot.innerHTML = [...groups.entries()].map(([category, items]) => `
      <section class="entry-section" id="category-${normalized(category).replace(/[^a-z0-9]+/g, "-")}">
        <h3>${escapeHtml(category)}</h3>${items.map((entry) => `
          <button class="entry-row" type="button" data-entry="${escapeHtml(entry.id)}">
            <span class="entry-group">${escapeHtml(entry.group)}</span><span class="entry-name">${escapeHtml(entry.title || entry.name)}</span>
            <span class="entry-description">${escapeHtml(entry.description)}<small class="version-note">${escapeHtml(compatibilityLabel(entry))}</small></span><span class="entry-arrow" aria-hidden="true">→</span>
          </button>`).join("")}
      </section>`).join("");
    resultCount.textContent = `${matches.length} de ${data.entries.length} entradas`;
    emptyState.hidden = matches.length !== 0;
    activeFilter.hidden = !selectedCategory && !search.value.trim();
    activeFilter.textContent = selectedCategory ? `Categoría activa: ${selectedCategory}` : `Resultados para: ${search.value.trim()}`;
    renderCategories();
  }

  function showCatalog(scroll = true) {
    catalog.hidden = false;
    renderCatalog();
    if (scroll) catalog.scrollIntoView();
  }

  function returnHome() {
    search.value = "";
    selectedCategory = "";
    catalog.hidden = true;
    renderCategories();
    document.querySelector("#categories").scrollIntoView();
  }

  function entryDetail(entry) {
    const args = entry.arguments || [];
    const examples = entry.examples || [];
    const docs = entry.docs || [];
    return `<span class="detail-kind">${escapeHtml(entry.kind)} · ${escapeHtml(entry.category)}</span>
      <h2 id="detail-title">${escapeHtml(entry.title || entry.name)}</h2><p class="detail-summary">${escapeHtml(entry.description)}</p>
      <p class="compatibility-note">${escapeHtml(compatibilityLabel(entry))}</p>
      ${entry.usage ? `<h3>Sintaxis</h3><pre><code>${escapeHtml(entry.usage)}</code></pre>` : ""}
      ${examples.length ? `<h3>Ejemplos</h3>${examples.map((item) => `<pre><code>${escapeHtml(item)}</code></pre>`).join("")}` : ""}
      ${entry.children?.length ? `<h3>Subcomandos</h3><p>${entry.children.map((item) => `<code>${escapeHtml(item)}</code>`).join(" · ")}</p>` : ""}
      ${entry.aliases?.length ? `<h3>Alias</h3><p>${entry.aliases.map((item) => `<code>${escapeHtml(item)}</code>`).join(" · ")}</p>` : ""}
      ${args.length ? `<h3>Argumentos y opciones</h3><dl class="argument-list">${args.map((arg) => `<div class="argument"><dt>${escapeHtml(arg.label)}</dt><dd>${escapeHtml(arg.description || "Sin descripción adicional.")}${arg.choices.length ? ` Valores: ${escapeHtml(arg.choices.join(", "))}.` : ""}${arg.default ? ` Predeterminado: ${escapeHtml(arg.default)}.` : ""}</dd></div>`).join("")}</dl>` : ""}
      ${entry.details && entry.kind === "concept" ? `<h3>Descripción</h3><p>${escapeHtml(entry.details)}</p>` : ""}
      ${docs.length ? `<h3>Documentación relacionada</h3><div class="doc-links">${docs.map((name) => `<a href="${docUrl(name)}">${escapeHtml(name)}</a>`).join("")}</div>` : ""}`;
  }

  function workflowDetail(workflow) {
    const related = workflow.related.map((id) => data.entries.find((entry) => entry.id === id)).filter(Boolean);
    return `<span class="detail-kind">Guía práctica · ${escapeHtml(workflow.level)} · ${escapeHtml(workflow.time)}</span>
      <h2 id="detail-title">${escapeHtml(workflow.title)}</h2><p class="detail-summary">${escapeHtml(workflow.summary)}</p>
      <p class="compatibility-note">${escapeHtml(compatibilityLabel(workflow))}</p>
      <ol class="workflow-steps">${workflow.steps.map((step) => `<li class="workflow-step"><h3>${escapeHtml(step.title)}</h3>
        <p>${escapeHtml(step.description)}</p>${step.commands.map((command) => `<pre><code>${escapeHtml(command)}</code></pre>`).join("")}</li>`).join("")}</ol>
      ${related.length ? `<h3>Referencia técnica relacionada</h3><div class="related-links">${related.map((entry) => `<button class="related-link" type="button" data-related-entry="${escapeHtml(entry.id)}">${escapeHtml(entry.title)}</button>`).join("")}</div>` : ""}
      <h3>Documentación relacionada</h3><div class="doc-links">${workflow.docs.map((name) => `<a href="${docUrl(name)}">${escapeHtml(name)}</a>`).join("")}</div>`;
  }

  function openDrawer(content, id, updateHash = true) {
    detailContent.innerHTML = content;
    detail.classList.add("open");
    detail.setAttribute("aria-hidden", "false");
    backdrop.hidden = false;
    document.body.classList.add("drawer-open");
    if (updateHash) history.replaceState(null, "", `#${id}`);
    document.querySelector("#close-detail").focus();
  }
  const openEntry = (entry, updateHash = true) => openDrawer(entryDetail(entry), entry.id, updateHash);
  const openWorkflow = (workflow, updateHash = true) => openDrawer(workflowDetail(workflow), workflow.id, updateHash);

  function closeDetail(updateHash = true) {
    detail.classList.remove("open");
    detail.setAttribute("aria-hidden", "true");
    backdrop.hidden = true;
    document.body.classList.remove("drawer-open");
    if (updateHash && /#(?:command|concept|doc|workflow)-/.test(location.hash)) history.replaceState(null, "", `${location.pathname}${location.search}`);
  }

  categoriesRoot.addEventListener("click", (event) => {
    const button = event.target.closest("[data-category]");
    if (!button) return;
    selectedCategory = button.dataset.category;
    search.value = "";
    showCatalog();
  });
  workflowsRoot.addEventListener("click", (event) => {
    const button = event.target.closest("[data-workflow]");
    const workflow = button && data.workflows.find((item) => item.id === button.dataset.workflow);
    if (workflow) openWorkflow(workflow);
  });
  entriesRoot.addEventListener("click", (event) => {
    const button = event.target.closest("[data-entry]");
    const entry = button && data.entries.find((item) => item.id === button.dataset.entry);
    if (entry) openEntry(entry);
  });
  detailContent.addEventListener("click", (event) => {
    const button = event.target.closest("[data-related-entry]");
    const entry = button && data.entries.find((item) => item.id === button.dataset.relatedEntry);
    if (entry) openEntry(entry);
  });
  search.addEventListener("input", () => {
    selectedCategory = "";
    if (search.value.trim()) showCatalog(false);
    else catalog.hidden = true;
  });
  search.addEventListener("keydown", (event) => { if (event.key === "Enter" && search.value.trim()) showCatalog(); });
  document.querySelector("#clear-filters").addEventListener("click", returnHome);
  document.querySelector("#close-detail").addEventListener("click", () => closeDetail());
  backdrop.addEventListener("click", () => closeDetail());
  document.addEventListener("keydown", (event) => {
    if (event.key === "/" && document.activeElement !== search) { event.preventDefault(); search.focus(); }
    if (event.key === "Escape") detail.classList.contains("open") ? closeDetail() : returnHome();
  });

  renderCategories();
  renderWorkflows();
  const entryFromHash = data.entries.find((entry) => `#${entry.id}` === location.hash);
  const workflowFromHash = data.workflows.find((workflow) => `#${workflow.id}` === location.hash);
  if (entryFromHash) openEntry(entryFromHash, false);
  else if (workflowFromHash) openWorkflow(workflowFromHash, false);
})();
