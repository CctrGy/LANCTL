"use strict";
function applyTheme(theme){Object.entries(theme.tokens||{}).forEach(([n,v])=>document.documentElement.style.setProperty(n,v));Object.entries(theme.components||{}).forEach(([id,tokens])=>document.querySelectorAll(`[data-component-id="${id}"]`).forEach(el=>Object.entries(tokens).forEach(([n,v])=>el.style.setProperty(n,v))));document.documentElement.dataset.themeId=theme.id||"lanctl.core.fallback"}
async function bootstrap(){if(!window.pywebview?.api)return;const state=await window.pywebview.api.bootstrap();applyTheme(state.theme);document.title=`LANCTL ${state.version}`}
window.addEventListener("pywebviewready",bootstrap);
