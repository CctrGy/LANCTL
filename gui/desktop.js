"use strict";

// Desktop-only extension. Remote clients retain the original, restricted RPC API.
let desktopReady = false;
let inventorySnapshot = null;
let sortColumn = "ip";
let sortDirection = 1;
let desktopBusy = false;
function editorValues() {
  return {name:$("#edit-name").value,alias:$("#edit-alias").value,
    description:$("#edit-description").value,icon:$("#edit-icon").value,cnf:$("#edit-cnf").value};
}
function editorDirty() {
  const device=state.devices.find(item=>item.id===state.selectedId);
  if(!device) return false;
  const values=editorValues();
  return values.name!==(device.name||"") || values.alias!==(device.alias||"") ||
    values.description!==(device.description==="-"?"":device.description||"") ||
    values.cnf!==(device.editableCnf??(device.cnf==="@"?"O":device.cnf)) ||
    values.icon!==(device.iconId||"");
}
async function commitEditor() {
  if(editorDirty()) renderInventory(await call("update_device",state.selectedId,editorValues(),state.devices.find(item=>item.id===state.selectedId)?.editRevision));
}
const originalClear = clearSelected;
clearSelected = function() {
  originalClear();
  ["#selected-ip","#selected-mac","#selected-vendor","#selected-protocols"].forEach(id=>$(id).textContent="—");
  ["#edit-name","#edit-alias","#edit-description"].forEach(id=>$(id).value="");
  $("#selected-icon").hidden=true;
};
const originalSelected = renderSelected;
renderSelected = function(device) {
  originalSelected(device);
  $("#selected-icon").hidden=!iconFor(device.iconId);
  $("#edit-cnf").value=device.editableCnf??(device.cnf==="@"?"O":device.cnf);
};
const originalMessage = message;
message = function(text, error=false) {
  originalMessage(text, error);
  const row = document.createElement("li");
  row.textContent = `${new Date().toLocaleTimeString()} · ${text}`;
  if(error) row.classList.add("error-text");
  $("#session-events").prepend(row);
  while($("#session-events").children.length > 150) $("#session-events").lastChild.remove();
};
const originalBusy = setBusy;
setBusy = function(busy, text) {
  desktopBusy = busy;
  originalBusy(busy, text);
  $("#cancel-scan").disabled = false;
};
function replaceHandler(selector, event, handler) {
  const old = $(selector), fresh = old.cloneNode(true);
  old.replaceWith(fresh);
  fresh.addEventListener(event, handler);
}
function chooseSave(shared = false) {
  return new Promise(resolve => {
    const dialog = $("#save-dialog");
    dialog.querySelector("p").textContent = shared
      ? "Los cambios aplicados son compartidos con otras sesiones. Cerrar sin guardar conserva esos cambios para las otras sesiones y no modifica el archivo del proyecto."
      : "El proyecto tiene modificaciones sin guardar.";
    dialog.querySelector('[data-decision="discard"]').textContent = shared ? "Cerrar sin guardar" : "Descartar";
    dialog.oncancel = event => {event.preventDefault(); finish("cancel");};
    function finish(answer) { dialog.close(); resolve(answer); }
    dialog.querySelectorAll("button").forEach(button => button.onclick=()=>finish(button.dataset.decision));
    dialog.showModal();
  });
}
async function protectProject() {
  const status = await call("project_state");
  if(!status.dirty && !editorDirty()) return true;
  const answer = await chooseSave();
  if(answer === "cancel") return false;
  if(answer === "save") {await commitEditor(); message((await call("save_project")).message);}
  return true;
}
async function desktopClose() {
  if(window.desktopClosing)return;window.desktopClosing=true;
  try {
    if(desktopBusy){await call("cancel_scan");let stopped=false;for(let i=0;i<100;i++){if(!(await call("scan_status")).running){stopped=true;break;}await new Promise(resolve=>setTimeout(resolve,100));}if(!stopped)return message("Cancelación solicitada. Espera a que termine la operación y vuelve a cerrar.",true);}
    const status = await call("project_state");
    const decision = status.dirty || editorDirty() ? await chooseSave(status.shared) : "discard";
    if(decision === "save") await commitEditor();
    if(decision !== "cancel") await call("request_close", decision);
  } catch(error) { message(error.message, true); }
  finally {window.desktopClosing=false;}
}
function showForm(title, fields, submit) {
  const dialog = $("#desktop-dialog"), host = $("#desktop-fields");
  $("#desktop-dialog-title").textContent = title;
  $("#desktop-error").textContent = "";
  host.replaceChildren();
  fields.forEach(field => {
    if(field.section && ![...host.querySelectorAll("h3")].some(heading=>heading.textContent===field.section)) {
      const heading=document.createElement("h3");heading.textContent=field.section;host.append(heading);
    }
    const choices=field.choices || {discovery:["icmp","arp","hybrid"],scanProfile:["fast","normal","accurate"],projectSaveMode:["manual","manual.inCloseConsult","automatic.toClose","automatic.toScan","automatic.timeToSave","automatic.allChanges"]}[field.key];
    const label = document.createElement("label"), input = document.createElement(choices?"select":"input");
    if(choices) choices.forEach(choice=>input.add(new Option(choice.label||choice,choice.value||choice)));
    label.textContent = field.label;
    input.name = field.key; input.value = field.value ?? "";
    label.append(input); host.append(label);
  });
  $("#desktop-dismiss").onclick = () => dialog.close();
  $("#desktop-form").onsubmit = async event => {
    event.preventDefault();
    const button = event.submitter; button.disabled = true;
    try { await submit(Object.fromEntries(new FormData(event.target))); dialog.close(); }
    catch(error) { $("#desktop-error").textContent = error.message; }
    finally { button.disabled = false; }
  };
  dialog.showModal(); host.querySelector("input")?.focus();
}
const inventoryRenderer = renderInventory;
renderInventory = function(payload) {
  inventorySnapshot = payload;
  const select = $("#group-filter"), previous = select.value;
  select.replaceChildren(new Option("Todos los grupos", ""));
  [...new Set([...(payload.devices||[]).flatMap(device=>device.groups),...(payload.groupCatalog||[]).map(group=>group.name)])].sort().forEach(group=>select.add(new Option(group, group)));
  select.value = previous;
  for(const [id,values] of [["#vendor-filter",(payload.devices||[]).map(d=>d.manufacturer)],["#protocol-filter",(payload.devices||[]).flatMap(d=>d.protocols)]]){
    const input=$(id),value=input.value;input.replaceChildren(new Option("Todos",""));[...new Set(values.filter(Boolean))].sort().forEach(item=>input.add(new Option(item,item)));input.value=value;
  }
  filterInventory();
};
function filterInventory() {
  if(!inventorySnapshot) return;
  const filter = $("#state-filter").value, group = $("#group-filter").value;
  const query = $("#device-search").value.toLocaleLowerCase();
  const vendor=$("#vendor-filter").value,protocol=$("#protocol-filter").value,cnf=$("#cnf-filter").value,membership=$("#membership-filter").value;
  const mapping = {vendor:"manufacturer", group:"groups", latency:"responseMs", state:"active"};
  const key = mapping[sortColumn] || sortColumn;
  const devices = (inventorySnapshot.devices||[]).filter(device =>
    (filter === "all" || (filter === "active" ? device.active : !device.active)) &&
    (!group || device.groups.includes(group)) &&
    (!vendor || device.manufacturer===vendor) &&
    (!protocol || device.protocols.includes(protocol)) &&
    (!cnf || (device.editableCnf??device.cnf)===cnf) &&
    (!membership || (membership==="grouped"?device.groups.length>0:device.groups.length===0)) &&
    [device.ip,device.mac,device.alias,device.name,device.manufacturer,...device.groups].join(" ").toLocaleLowerCase().includes(query)
  ).sort((a,b)=>sortDirection*String(a[key]??"").localeCompare(String(b[key]??""),undefined,{numeric:true}));
  inventoryRenderer({...inventorySnapshot,devices});
  if(!devices.length) clearSelected();
}
window.addEventListener("pywebviewready", () => {
  if(!window.pywebview.api.project_state) return;
  desktopReady = true;
  replaceHandler("#project-save","click",async()=>{
    setBusy(true,"Guardando proyecto…");
    try {await commitEditor(); const payload=await call("save_project"); renderProjects(payload); renderInventory(payload);message(payload.message);}
    catch(error){message(error.message,true);} finally{setBusy(false);}
  });
  replaceHandler("#save-device","click",async()=>{
    if(!state.selectedId) return message("Selecciona un elemento",true);
    setBusy(true,"Guardando elemento…");
    try {
      const payload=await call("update_device",state.selectedId,{
        name:$("#edit-name").value, alias:$("#edit-alias").value,
        description:$("#edit-description").value, icon:$("#edit-icon").value,
        cnf:$("#edit-cnf").value
      },state.devices.find(item=>item.id===state.selectedId)?.editRevision);
      renderInventory(payload); message(payload.message);
    } catch(error){message(error.message,true);} finally{setBusy(false);}
  });
  $("#device-groups").onclick=()=>showForm("Grupos del elemento",[
    {key:"action",label:"Acción",value:"add",choices:[{label:"Crear grupo",value:"create"},{label:"Añadir elemento",value:"add"},{label:"Retirar elemento",value:"remove"}]},
    {key:"name",label:"Nombre del grupo",value:""}
  ],async values=>{
    if(values.action!=="create" && !state.selectedId) throw new Error("Selecciona un elemento");
    const payload=await call("group_action",values.action,values.name,state.selectedId||"");
    renderInventory(payload); message(payload.message);
  });
  replaceHandler("#device-search", "input", filterInventory);
  $("#state-filter").onchange = filterInventory;
  $("#group-filter").onchange = filterInventory;
  document.querySelectorAll("th[data-column]").forEach(header=>header.addEventListener("click",()=>{
    sortDirection = sortColumn === header.dataset.column ? -sortDirection : 1;
    sortColumn = header.dataset.column;
    document.querySelectorAll("th[aria-sort]").forEach(th=>th.removeAttribute("aria-sort"));
    header.setAttribute("aria-sort",sortDirection===1?"ascending":"descending");
    filterInventory();
  }));
  replaceHandler("#scan-network", "click", async()=>{
    setBusy(true,"Escaneando la red…");
    $("#cancel-scan").hidden=false; $("#scan-progress").hidden=false;
    const poll=setInterval(async()=>{
      try {const status=await call("scan_status"); $("#scan-progress").value=100*status.current/Math.max(1,status.total);}
      catch(error) { message(error.message,true); }
    },500);
    try {const target=window.lanipScanTarget;const payload=await call("scan_network",$("#scan-profile").value,...(target?[target.source,target.network]:[])); renderInventory(payload);window.lanipScanCompleted?.(); message(payload.message);}
    catch(error) {message(error.message,true);}
    finally {clearInterval(poll); $("#cancel-scan").hidden=true; $("#scan-progress").hidden=true; setBusy(false);}
  });
  $("#cancel-scan").onclick=async()=>{try {message((await call("cancel_scan")).message);} catch(error){message(error.message,true);}};
  // Project selection belongs to LANCTL; these legacy DOM IDs remain for API compatibility.
  for (const id of ["#project-select", "#project-open", "#project-new"]) {
    const el = $(id); el.hidden = true; el.disabled = true;
    replaceHandler(id, id === "#project-select" ? "change" : "click", () => {});
  }
  $("#desktop-settings").onclick=async()=>{
    try {
      const payload=await call("get_settings");
      showForm("Configuración de LANIP",payload.fields,async values=>{
        const changed=Object.fromEntries(payload.fields.filter(field=>String(field.value??"")!==values[field.key]).map(field=>[field.key,values[field.key]|| (field.key==="projectsDirectory"?"auto":"")]));
        if(Object.keys(changed).length) message((await call("save_settings",changed)).message);
      });
    } catch(error){message(error.message,true);}
  };
});
document.addEventListener("keydown",event=>{
  if(!desktopReady || desktopBusy || document.querySelector("dialog[open]")) return;
  if(event.ctrlKey && event.key.toLowerCase()==="s") {event.preventDefault(); $("#project-save").click();}
  if(event.key==="F5") {event.preventDefault(); $("#scan-network").click();}
});

// Coalesce notifications; never replace an editor or an in-flight operation.
setInterval(async()=>{
  if(!window.desktopDataChanged || !desktopReady || desktopBusy || editorDirty() || document.querySelector("dialog[open]")) return;
  window.desktopDataChanged=false;
  try {
    const selectedProject=$("#project-select").value;
    const payload=await call(window.pywebview?.api?.sync_project?"sync_project":"list_devices",$("#device-search").value);
    if(desktopBusy || editorDirty() || document.querySelector("dialog[open]") || $("#project-select").value!==selectedProject) {
      window.desktopDataChanged=true; return;
    }
    if(payload.projects)renderProjects(payload);
    renderInventory(payload);
  }
  catch(error) { window.desktopDataChanged=true; message(error.message,true); }
},1000);
