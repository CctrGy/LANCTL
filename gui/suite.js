"use strict";
const $ = selector => document.querySelector(selector);
const state = {page:"home", projects:[], plugins:[], activeProject:"", version:"", system:"", architecture:""};
let submitForm = null;
let originalForm = "";
let terminalTimer = null;
let terminalReading = false;
const listQueries={projects:"",plugins:""};
const activity = [];
const apps = [
  ["lanip","LANIP","Inventario y diagnóstico","network"],
  ["lanwire","LANWIRE","Cableado y topología","cable"],
  ["lanrack","LANRACK","Salas y racks","server"],
  ["lanaccess","LANACCESS","Credenciales y acceso","key"],
  ["lanmon","LANMON","Monitorización y eventos","activity"]
];
// Local vector icons: no remote dependency or executable plugin markup.
const icons = {
  network:'<rect x="8" y="2" width="8" height="5" rx="1"/><rect x="2" y="17" width="7" height="5" rx="1"/><rect x="15" y="17" width="7" height="5" rx="1"/><path d="M12 7v5M5.5 17v-5h13v5"/>',
  cable:'<path d="M6 3v5m4-5v5M4 8h8v5a4 4 0 0 1-8 0V8zm4 9v4m12-18v10a3 3 0 0 1-6 0V7a2 2 0 0 1 4 0v3"/>',
  server:'<rect x="3" y="3" width="18" height="7" rx="2"/><rect x="3" y="14" width="18" height="7" rx="2"/><path d="M7 6.5h.01M7 17.5h.01M11 6.5h6M11 17.5h6"/>',
  key:'<circle cx="15" cy="8" r="5"/><path d="m11 12-8 8v2h4v-3h3v-3l3-3M16 7h.01"/>',
  activity:'<path d="M2 12h5l3-9 4 18 3-9h5"/>'
};
function icon(name){return `<svg viewBox="0 0 24 24" aria-hidden="true">${icons[name]}</svg>`;}
function esc(value){return String(value??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
function message(text,error=false){$("#status").textContent=text;$("#status").classList.toggle("error",error);if(text){activity.push(new Date().toLocaleTimeString()+" · "+text);if(activity.length>100)activity.shift();}}
async function call(method,...args){
  if(!window.pywebview?.api)throw new Error("Abre esta interfaz con lanctl --gui.");
  const response=await window.pywebview.api[method](...args);
  if(!response.ok)throw new Error(response.error+(response.errorId?` (${response.errorId})`:""));
  return response;
}
function apply(payload){
  Object.assign(state,payload);
  const select=$("#project");select.replaceChildren(new Option("Sin proyecto",""));
  state.projects.forEach(p=>select.add(new Option(p.name,p.path)));select.value=state.activeProject||"";
  $("#version").textContent="v"+state.version;
  $("#project-status").textContent=(state.activeProjectInfo?.name||"Sin proyecto")+(state.activeProject?" · VLF":"");
  $("#plugin-count").textContent=state.plugins.filter(p=>p.state==="ENABLED").length+" plugins";
}
async function refresh(){apply(await call("bootstrap"));render();}
function render(){
  document.querySelectorAll("nav button").forEach(b=>b.classList.toggle("active",b.dataset.page===state.page));
  const host=$("#content");
  host.classList.toggle("list-page",["projects","plugins"].includes(state.page));
  if(state.page==="home")host.innerHTML='<div class="caption"><span>PROGRAMAS</span><span>Proyecto compartido · interfaces GUI</span></div><div class="launch-grid">'+apps.map(([id,name,title,i])=>`<button class="launch" data-launch="${id}">${icon(i)}<span><strong>${name}</strong><small>${title}${id!=="lanip"?" · GUI pendiente":""}${state.sessions?.some(s=>s.launcher===id)?" · Abierto":""}</small></span></button>`).join("")+"</div>";
  if(state.page==="projects")host.innerHTML='<div class="toolbar"><h1>Proyectos</h1><div class="row"><button data-action="open-project">Abrir VLF…</button><button data-action="save-project">Guardar</button><button data-action="new-project" class="primary">Nuevo proyecto</button></div></div><div class="stack">'+state.projects.map(p=>`<section class="panel"><div class="row"><h2>${esc(p.name)}</h2><button data-edit-project="${esc(p.path)}">Editar</button><button data-project="${esc(p.path)}" ${p.path===state.activeProject?"disabled":""}>${p.path===state.activeProject?"Activo":"Seleccionar"}</button></div><p>${esc(p.path)}</p></section>`).join("")+(!state.projects.length?'<p class="muted">Crea un proyecto o abre un archivo VLF existente.</p>':"")+"</div>";
  if(state.page==="plugins")host.innerHTML='<div class="toolbar"><h1>Plugins</h1><button data-action="refresh">Actualizar</button></div><div class="stack">'+state.plugins.map(p=>`<section class="panel"><div class="row"><h2>${esc(p.name)}</h2><div class="row">${p.hasSettings?`<button data-plugin-config="${esc(p.id)}">⚙ Configurar</button>`:""}<button data-plugin-toggle="${esc(p.id)}">${p.state==="ENABLED"?"Desactivar":"Activar"}</button></div></div><p>${esc(p.description)}</p><small class="muted">${esc(p.id)} · ${esc(p.version)} · ${esc(p.state)}</small>${p.error?`<p>${esc(p.error)}</p>`:""}${p.settingsError?`<p class="error">Configuración: ${esc(p.settingsError)}</p>`:""}</section>`).join("")+(!state.plugins.length?'<p class="muted">No hay plugins instalados. Usa el CLI para instalar paquetes LCP.</p>':"")+"</div>";
  if(["projects","plugins"].includes(state.page))prepareCollection(state.page);
  if(state.page==="settings")host.innerHTML='<div class="toolbar"><h1>Configuración general</h1><button data-action="edit-settings" class="primary">Editar preferencias</button></div><p class="muted">Red, proyectos, políticas de guardado y registros compartidos por la suite.</p>';
  if(state.page==="terminal")host.innerHTML='<div class="terminal"><header><strong>›_ LANCTL · CLI general</strong><span class="badge">Proceso local</span></header><pre id="terminal-output" role="log" aria-live="polite"></pre><form id="terminal-form"><label for="command">LANCTL&gt;</label><input id="command" autocomplete="off" spellcheck="false" aria-label="Entrada del CLI"><button>Enviar</button></form><small>Para sesiones SSH, contraseñas o TUI utiliza «CLI» en la barra inferior.</small></div>';
}
function prepareCollection(kind){
  const host=$("#content"),list=host.querySelector(".stack");list.classList.add("collection-list");list.setAttribute("aria-label",kind==="projects"?"Lista de proyectos":"Lista de plugins");
  const bar=document.createElement("div");bar.className="collection-search";
  const label=document.createElement("label");label.textContent=kind==="projects"?"Buscar proyecto":"Buscar plugin";
  const input=document.createElement("input");input.type="search";input.id="collection-search";input.placeholder="Buscar por nombre…";input.value=listQueries[kind];label.append(input);
  const count=document.createElement("span");count.className="muted";count.id="collection-count";count.setAttribute("role","status");bar.append(label,count);list.before(bar);
  const cards=[...list.querySelectorAll(".panel")];
  if(kind==="plugins")cards.forEach((card,i)=>{
    const p=state.plugins[i];card.querySelector("small.muted")?.remove();
    const data=document.createElement("div");data.className="plugin-facts";
    data.innerHTML=`<span>Versión <b>${esc(p.version||"—")}</b></span><span>Estado <b>${esc(p.state||"—")}</b></span><span>Autor <b>${esc(p.author||"No indicado")}</b></span>`;
    const details=document.createElement("details");details.className="plugin-technical";
    details.innerHTML=`<summary>Información técnica</summary><dl><dt>Identificador</dt><dd>${esc(p.id)}</dd><dt>Runtime</dt><dd>${esc(p.runtime||"No indicado")}</dd><dt>Compatibilidad LANCTL</dt><dd>${esc(p.minimumLanctl||"—")} → ${esc(p.maximumLanctl||"—")}</dd><dt>Capacidades</dt><dd>${esc((p.capabilities||[]).join(", ")||"Ninguna declarada")}</dd><dt>Permisos solicitados</dt><dd>${esc((p.permissions||[]).join(", ")||"Ninguno")}</dd><dt>Permisos concedidos</dt><dd>${esc((p.granted||[]).join(", ")||"Ninguno")}</dd><dt>Firma</dt><dd>${esc(p.signature||"No disponible")}</dd></dl>`;
    card.append(data,details);
  });
  const empty=document.createElement("p");empty.className="collection-empty muted";empty.textContent="No hay resultados para esta búsqueda.";empty.hidden=true;list.append(empty);
  function filter(){const query=input.value.trim().toLocaleLowerCase();listQueries[kind]=input.value;let shown=0;cards.forEach(card=>{card.hidden=!card.querySelector("h2").textContent.toLocaleLowerCase().includes(query);if(!card.hidden)shown++;});empty.hidden=shown>0||cards.length===0;count.textContent=shown+" de "+cards.length;list.scrollTop=0;}
  input.addEventListener("input",filter);filter();
}
async function navigate(page){
  if(page===state.page)return;
  if(terminalTimer){clearInterval(terminalTimer);terminalTimer=null;}
  state.page=page;message("");render();
  if(page==="terminal"){
    await call("start_terminal");await readTerminal();
    terminalTimer=setInterval(()=>readTerminal().catch(e=>message(e.message,true)),250);
    $("#command").focus();
  }
}
async function readTerminal(){
  if(terminalReading)return;terminalReading=true;
  try{const payload=await call("terminal_output"),host=$("#terminal-output");if(host){host.textContent=(host.textContent+payload.text).slice(-20000);host.scrollTop=host.scrollHeight;if(!payload.running)message("Consola cerrada. Cambia de sección y vuelve a Terminal para reiniciarla.");}}
  finally{terminalReading=false;}
}
function field(label,name,value,type="text"){
  const node=document.createElement("label");node.textContent=label;
  const input=document.createElement("input");input.name=name;input.type=type;
  if(type==="checkbox"){node.className="check";input.checked=Boolean(value);}else input.value=value??"";
  node.append(input);return node;
}
function showForm(title,nodes,submit,label="Guardar"){
  $("#dialog-title").textContent=title;$("#fields").replaceChildren(...nodes);$("#form-error").textContent="";
  $("#submit").textContent=label;$("#submit").hidden=!submit;$("#dismiss").hidden=!submit;submitForm=submit;originalForm=JSON.stringify([...new FormData($("#form"))]);if(!$("#dialog").open)$("#dialog").showModal();
}
const metadataFields=[["name","Nombre"],["description","Descripción"],["author","Autor"],["lan","LAN"],["location","Ubicación"],["company","Empresa"],["responsible","Responsable"]];
async function preserveProject(){
  const {dirty}=await call("project_state");
  if(!dirty)return true;
  if(!confirm("Hay cambios pendientes en el proyecto activo. ¿Guardarlos antes de continuar?"))return false;
  const result=await call("save_project");message(result.message);return true;
}
async function editProject(path){
  const data=await call("project_metadata",path);
  showForm("Editar proyecto",metadataFields.map(([key,label])=>field(label,key,data.values[key])),async values=>{
    const result=await call("save_project_metadata",path,values,data.revision);apply(result);render();message(result.message);
  });
}
async function newProject(){
  if(!await preserveProject())return;
  const directory=await call("select_project_directory");if(!directory.path)return;
  const name=field("Nombre del proyecto","name",""),location=field("Carpeta","directory",directory.path);
  name.querySelector("input").required=true;location.querySelector("input").readOnly=true;
  const help=document.createElement("small");help.textContent="Se creará un archivo .vlf vacío en esta carpeta. Los archivos existentes no se sobrescriben.";
  showForm("Crear proyecto VLF",[name,location,...metadataFields.slice(1).map(([key,label])=>field(label,key,"")),help],async values=>{
    const metadata=Object.fromEntries(metadataFields.map(([key])=>[key,values[key]||""]));
    const payload=await call("create_project",values.name,values.directory,metadata);apply(payload);await refresh();message(payload.message+" · "+payload.activeProject);
  },"Crear archivo VLF");
}
async function configurePlugin(id){
  const p=state.plugins.find(p=>p.id===id),data=await call("plugin_settings",id),nodes=[];
  const info=document.createElement("p");info.textContent=`${p.runtime} · Permisos: ${p.permissions.join(", ")||"ninguno"}. Concedidos: ${p.granted.join(", ")||"ninguno"}.`;nodes.push(info);
  if(!data.fields.length){const hint=document.createElement("p");hint.className="muted";hint.textContent="Este plugin no declara opciones propias de configuración.";nodes.push(hint);}
  for(const f of data.fields){
    let node;
    if(f.type==="select"){node=document.createElement("label");node.textContent=f.label||f.name;const select=document.createElement("select");select.name=f.name;f.choices.forEach(c=>select.add(new Option(c,c)));select.value=data.values[f.name];node.append(select);}
    else{node=field(f.label||f.name,f.name,data.values[f.name],f.type==="boolean"?"checkbox":f.type==="integer"?"number":"text");const input=node.querySelector("input");if(f.type==="integer"){input.step="1";if(f.minimum!==undefined)input.min=f.minimum;if(f.maximum!==undefined)input.max=f.maximum;}}
    nodes.push(node);
  }
  showForm(p.name,nodes,data.fields.length?async values=>{
    const options={};for(const f of data.fields)options[f.name]=f.type==="boolean"?values[f.name]==="on":f.type==="integer"?Number(values[f.name]):values[f.name];
    const result=await call("save_plugin_settings",id,options);message(result.message);
  }:null);
}
async function togglePlugin(id){
  const p=state.plugins.find(p=>p.id===id);
  if(p.state==="ENABLED"){apply(await call("set_plugin_enabled",id,false));render();return;}
  const info=document.createElement("p");info.textContent="Revisa los permisos solicitados antes de activar este complemento.";
  const nodes=[info,...p.permissions.map(permission=>field(permission,permission,p.granted.includes(permission),"checkbox"))];
  if(p.runtime==="trusted"&&!p.publisherTrusted){
    const help=document.createElement("p");
    if(!p.signature?.startsWith("VALID_ED25519:")){
      help.textContent="Este paquete no tiene una firma válida. Solicita al editor un LCP firmado e instálalo antes de activarlo. Marcar permisos no autoriza un paquete sin firma.";
      nodes.push(help);showForm("Activar "+p.name,nodes,null);return;
    }
    help.textContent="El paquete está firmado, pero su editor todavía no está autorizado. Comprueba esta huella con el editor antes de confiar: "+p.signature.slice(14);
    const trust=document.createElement("button");trust.type="button";trust.textContent="Autorizar editor seleccionando su LCP firmado…";
    trust.onclick=async()=>{trust.disabled=true;try{const result=await call("trust_plugin_publisher",id);if(!result.cancelled){apply(result);await togglePlugin(id);}}catch(error){$("#form-error").textContent=error.message;}finally{trust.disabled=false;}};
    nodes.push(help,trust);showForm("Autorizar editor de "+p.name,nodes,null);return;
  }
  if(p.runtime==="trusted")nodes.push(field("Autorizar ejecución trusted (editor autorizado)","_trust",p.trusted,"checkbox"));
  showForm("Activar "+p.name,nodes,async values=>{apply(await call("set_plugin_enabled",id,true,p.permissions.filter(x=>values[x]==="on"),values._trust==="on"));render();},"Activar plugin");
}
async function editSettings(){
  const payload=await call("get_settings");
  showForm("Configuración general",payload.fields.map(f=>{
    if(!f.choices)return field(f.label,f.key,f.value);
    const label=document.createElement("label");label.textContent=f.label;
    const select=document.createElement("select");select.name=f.key;f.choices.forEach(c=>select.add(new Option(c,c)));select.value=f.value;label.append(select);return label;
  }),async values=>message((await call("save_settings",values)).message));
}
$("#form").addEventListener("submit",async e=>{e.preventDefault();if(!submitForm)return;$("#submit").disabled=true;try{await submitForm(Object.fromEntries(new FormData(e.target)));$("#dialog").close();}catch(error){$("#form-error").textContent=error.message;}finally{$("#submit").disabled=false;}});
function dismissForm(){
  if(submitForm&&originalForm!==JSON.stringify([...new FormData($("#form"))])&&!confirm("Hay cambios sin guardar. ¿Descartarlos?"))return;
  $("#dialog").close();
}
async function suiteClose(){
  try{
    if($("#dialog").open&&submitForm&&originalForm!==JSON.stringify([...new FormData($("#form"))])&&!confirm("Hay cambios sin guardar en el formulario. ¿Descartarlos y cerrar?"))return;
    if(!await preserveProject())return;
    const result=await call("request_close");if(!result.closed)message("No se pudo cerrar la ventana.",true);
  }catch(error){message(error.message,true);}
}
$("#close-dialog").onclick=$("#dismiss").onclick=dismissForm;
$("#dialog").addEventListener("cancel",e=>{e.preventDefault();dismissForm();});
$("#project").addEventListener("change",async e=>{try{if(!e.target.value){e.target.value=state.activeProject;return;}if(!await preserveProject()){e.target.value=state.activeProject;return;}apply(await call("use_project",e.target.value));render();}catch(error){e.target.value=state.activeProject;message(error.message,true);}});
document.addEventListener("click",async e=>{
  const b=e.target.closest("button");if(!b)return;
  try{
    if(b.dataset.page)return await navigate(b.dataset.page);
    if(b.dataset.launch)return message((await call("launch_gui",b.dataset.launch)).message);
    if(b.dataset.editProject)return await editProject(b.dataset.editProject);
    if(b.dataset.project){if(!await preserveProject())return;apply(await call("use_project",b.dataset.project));render();return;}
    if(b.dataset.pluginConfig)return await configurePlugin(b.dataset.pluginConfig);
    if(b.dataset.pluginToggle)return await togglePlugin(b.dataset.pluginToggle);
    if(b.id==="external-cli")return message((await call("open_cli")).message);
    if(b.id==="activity"){const log=document.createElement("div");log.className="stack";for(const text of activity.slice(-20)){const line=document.createElement("p");line.textContent=text;log.append(line);}if(!activity.length)log.textContent="Sin operaciones registradas en esta sesión.";showForm("Actividad de sesión",[log],null);return;}
    if(b.id==="system-info"){
      const dl=document.createElement("dl");for(const [label,value] of [["Versión",state.version],["Sistema",state.system],["Arquitectura",state.architecture],["Proyecto",state.activeProject||"Sin proyecto"],["Interfaz","GUI local · pywebview"],["Archivos","Proyectos VLF · plugins LCP"]]){const dt=document.createElement("dt"),dd=document.createElement("dd");dt.textContent=label;dd.textContent=value;dl.append(dt,dd);}showForm("Información del sistema",[dl],null);return;
    }
    if(b.dataset.action==="new-project")await newProject();
    if(b.dataset.action==="refresh")await refresh();
    if(b.dataset.action==="save-project"){const result=await call("save_project");message(result.message);}
    if(b.dataset.action==="open-project"){const file=await call("select_project_file");if(file.path&&await preserveProject()){apply(await call("use_project",file.path));render();}}
    if(b.dataset.action==="edit-settings")await editSettings();
  }catch(error){message(error.message,true);}
});
document.addEventListener("submit",async e=>{if(e.target.id!=="terminal-form")return;e.preventDefault();const input=$("#command"),line=input.value;input.value="";try{await call("terminal_send",line);await readTerminal();}catch(error){message(error.message,true);}});
function clock(){const now=new Date();$("#clock").dateTime=now.toISOString();$("#clock").textContent=new Intl.DateTimeFormat("es-ES",{dateStyle:"short",timeStyle:"short"}).format(now);}
clock();setInterval(clock,30000);
window.addEventListener("pywebviewready",()=>refresh().catch(error=>message(error.message,true)));

// Reconcile shared state without replacing a form or interrupting terminal input.
window.suiteDataChanged=false;
let backgroundRefresh=false;
setInterval(async()=>{
  if(!window.suiteDataChanged||backgroundRefresh||$("#dialog").open||!window.pywebview?.api)return;
  backgroundRefresh=true;window.suiteDataChanged=false;
  try{apply(await call("bootstrap"));if(state.page!=="terminal")render();}
  catch(error){window.suiteDataChanged=true;message(error.message,true);}
  finally{backgroundRefresh=false;}
},1000);

let runtimeReading=false;
setInterval(async()=>{
  if(runtimeReading||!window.pywebview?.api.runtime_status)return;
  runtimeReading=true;
  try{
    const result=await call("runtime_status"),old=state.sessions||[],next=result.sessions;
    for(const session of next.filter(s=>s.mode==="gui"&&!old.some(p=>p.id===s.id)))message(session.launcher.toUpperCase()+" · GUI abierta");
    for(const session of old.filter(s=>s.mode==="gui"&&!next.some(p=>p.id===s.id)))message(session.launcher.toUpperCase()+" · GUI cerrada o desconectada");
    const changed=JSON.stringify(old.map(s=>s.id))!==JSON.stringify(next.map(s=>s.id));
    state.sessions=next;if(changed&&state.page==="home")render();
  }catch(error){message(error.message,true);}finally{runtimeReading=false;}
},2000);
