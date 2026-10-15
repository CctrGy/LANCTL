"use strict";

// Presentation-only adapters; all mutations continue through the existing RPCs.
const essentialColumns = ["state", "icon", "ip", "latency", "alias", "vendor", "group"];
const graphiteTokens = {
  "--color-background":"#15181c", "--color-surface":"#1d2328",
  "--color-surface-raised":"#252d33", "--color-border":"#374149",
  "--color-text":"#eef2f5", "--color-text-muted":"#a6b3c1",
  "--color-accent":"#b2ef26", "--color-success":"#91d748",
  "--color-warning":"#e4b56c", "--color-danger":"#ef7777",
  "--radius-panel":"12px", "--radius-control":"7px"
};
const previousTheme = applyTheme;
applyTheme = function(theme = {}) {
  if(!theme.id || ["lanctl.core.fallback","lanctl.theme.default.palette"].includes(theme.id)) {
    previousTheme({tokens:graphiteTokens,components:{}});
  } else previousTheme(theme);
};
function columnPreferences() {
  try {
    const saved=JSON.parse(localStorage.getItem("lanctl.columns")||"null");
    if(saved && typeof saved==="object" && !Array.isArray(saved)) return saved;
  } catch { /* Ignore invalid presentation preferences, not project data. */ }
  return Object.fromEntries(columns.map(key=>[key,essentialColumns.includes(key)]));
}
function selectedPreset(saved) {
  if(columns.every(key=>saved[key]!==false)) return "complete";
  if(columns.every(key=>(saved[key]!==false)===essentialColumns.includes(key))) return "essential";
  return "custom";
}
setupColumns = function() {
  const host=$("#column-options");host.replaceChildren();
  document.querySelectorAll(".table-panel th[data-column]").forEach(header=>{
    const key=header.dataset.column,label=document.createElement("label"),input=document.createElement("input");
    input.type="checkbox";input.dataset.columnToggle=key;
    input.addEventListener("change",()=>{
      const saved=columnPreferences();saved[key]=input.checked;
      // Keep at least one useful identifier visible.
      if(!columns.some(column=>saved[column]!==false)){input.checked=true;return;}
      localStorage.setItem("lanctl.columns",JSON.stringify(saved));applyColumnPreferences();
    });
    label.append(input,header.textContent);host.append(label);
  });
  applyColumnPreferences();
};
applyColumnPreferences = function() {
  const saved=columnPreferences();
  columns.forEach(key=>{
    document.querySelectorAll(`.table-panel [data-column="${key}"]`).forEach(cell=>cell.classList.toggle("column-hidden",saved[key]===false));
    const input=document.querySelector(`[data-column-toggle="${key}"]`);if(input)input.checked=saved[key]!==false;
  });
  $("#inventory-view").value=selectedPreset(saved);
};
restoreWidths = function() {
  columns.forEach(key=>{
    const width=Number(localStorage.getItem(`lanctl.width.${key}`));
    const header=document.querySelector(`.table-panel th[data-column="${key}"]`);
    if(header && Number.isFinite(width) && width>=45 && width<=1000){header.style.width=width+"px";header.style.minWidth=width+"px";}
  });
};
$("#inventory-view").addEventListener("change",event=>{
  const preset=event.target.value;
  if(preset==="custom"){$(".column-menu").open=true;return;}
  const saved=Object.fromEntries(columns.map(key=>[key,preset==="complete"||essentialColumns.includes(key)]));
  localStorage.setItem("lanctl.columns",JSON.stringify(saved));applyColumnPreferences();
});
function syncInspector() {
  const selected=state.devices.some(device=>device.id===state.selectedId);
  document.querySelectorAll(".inspector input,.inspector select,.inspector button:not(.contract-only)").forEach(control=>control.disabled=!selected||desktopBusy);
  const device=state.devices.find(device=>device.id===state.selectedId);
  $("#wake-device").disabled=!selected||desktopBusy||!device?.wolAvailable;
  $(".inspector").setAttribute("aria-label",selected?"Opciones del equipo seleccionado":"Selecciona un equipo del inventario");
}
const selectedRenderer=renderSelected;
renderSelected=function(device){selectedRenderer(device);syncInspector();};
const clearedRenderer=clearSelected;
clearSelected=function(){clearedRenderer();syncInspector();};
const presentationBusy=setBusy;
setBusy=function(busy,text){presentationBusy(busy,text);syncInspector();};
document.addEventListener("keydown",event=>{
  if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==="k"&&!document.querySelector("dialog[open]")){
    event.preventDefault();$("#device-search").focus();$("#device-search").select();
  }
  if(event.key==="Escape")$(".column-menu").open=false;
});
document.addEventListener("click",event=>{const menu=$(".column-menu");if(menu.open&&!menu.contains(event.target)&&event.target!==$("#inventory-view"))menu.open=false;});
syncInspector();
