"use strict";
(() => {
  const BASE = "/lanctl/", PAGES = ["panel","ip","wire","access","rack","mon"];
  const MODULES = {panel:"LANCTL",ip:"LANIP",wire:"LANWIRE",access:"LANACCESS",rack:"LANRACK",mon:"LANMON"};
  const $ = selector => document.querySelector(selector);
  const tr = (key, values={}) => window.LanctlI18n.t(key,values);
  let csrf = sessionStorage.getItem("lanctl.web.csrf") || "", current = "", shell = null, loading = false, pendingSettings = false, frameReady = false;
  const activePage = () => {const page=location.pathname.replace(/\/$/,"").split("/").at(-1);return PAGES.includes(page)?page:"panel";};
  function notice(text="") {$("#web-notice").textContent=text;$("#web-notice").hidden=!text;}
  function applyPresentation(payload) {
    if(payload.languageCatalog) window.LanctlI18n.setCatalog(payload.languageCatalog);
    for(const [key,value] of Object.entries(payload.theme?.tokens||{}))document.documentElement.style.setProperty(key,value);
    if(payload.preferences){document.documentElement.style.fontSize=`${14*payload.preferences.fontScale}px`;document.documentElement.dataset.motion=payload.preferences.reducedMotion?"reduced":"normal";}
  }
  async function request(path,body=null) {
    const response=await fetch(BASE+"api/"+path,{method:body===null?"GET":"POST",credentials:"same-origin",headers:body===null?{}:{"Content-Type":"application/json","X-CSRF-Token":csrf},body:body===null?undefined:JSON.stringify(body)});
    const result=await response.json();
    if(response.status===401){showLogin();throw new Error(tr("LANCTL.WEB.SESSION_ENDED"));}
    if(!response.ok)return {ok:false,error:result.error||tr("LANCTL.WEB.DENIED")};
    return result;
  }
  function setNav(open,remember=true) {
    $("#web-workspace").dataset.nav=open?"open":"closed";
    $("#web-sidebar").inert=!open;$("#web-toggle").setAttribute("aria-expanded",String(open));
    $("#web-backdrop").hidden=!open||!matchMedia("(max-width:850px)").matches;
    if(remember)localStorage.setItem("lanctl.web.navigation",open?"open":"closed");
  }
  function updateShell(payload) {
    shell=payload; applyPresentation(payload);
    $("#web-user").textContent=payload.username||"";$("#web-version").textContent=`LANCTL ${payload.version||""}`;
    const services=$("#web-services");services.replaceChildren();
    for(const service of payload.services||[]){
      const url=service.url?new URL(service.url,location.origin):null;
      const node=document.createElement(url&&["http:","https:"].includes(url.protocol)?"a":"span");
      node.textContent=service.name;
      if(node.tagName==="A"){node.href=url.href;node.target="_blank";node.rel="noopener noreferrer";}
      else{node.title=tr("LANCTL.WEB.SERVICE_PENDING");node.setAttribute("aria-disabled","true");}
      services.append(node);
    }
    $("#web-settings").hidden=!(payload.permissions||[]).includes("system.configure");
    const select=$("#web-project"); select.replaceChildren();
    select.add(new Option(tr("LANCTL.UI.TEXT.NO_PROJECT"),""));
    for(const project of payload.projects||[])select.add(new Option(project.name,project.path));
    select.value=payload.activeProject||"";
    select.disabled=!(payload.permissions||[]).includes("project.manage");
    $("#web-project-id").textContent=payload.activeProjectInfo?.name||tr("LANCTL.UI.TEXT.NO_PROJECT");
    for(const link of document.querySelectorAll("#web-navigation a"))link.hidden=!(payload.pages||[]).includes(link.dataset.route);
  }
  async function refreshShell() {
    const payload=await request("shell",{});
    if(!payload.ok)throw new Error(payload.error||tr("LANCTL.WEB.DENIED"));
    updateShell(payload);return payload;
  }
  async function rpc(page,method,args=[],context=null) {
    const payload=await request("gui",{page,method,args,projectContext:context});
    if(payload.ok&&["use_project","create_project","save_project","save_project_metadata"].includes(method))await refreshShell();
    if(payload.ok&&method==="project_call"&&["use_project","create_project","save_project"].includes(args[1]))await refreshShell();
    if(payload.ok&&method==="save_gui_preferences")applyPresentation(payload);
    return payload;
  }
  function hasOpenForm() {
    try{return Boolean($("#web-frame").contentDocument?.querySelector("dialog[open]"));}catch{return false;}
  }
  async function navigate(page,options={}) {
    if(!PAGES.includes(page)||loading)return;
    if(!(shell?.pages||[]).includes(page)){notice(tr("LANCTL.WEB.DENIED"));return;}
    if(!options.force&&page===current)return;
    if(!options.force&&hasOpenForm()&&!confirm(tr("LANCTL.WEB.DISCARD_FORM")))return;
    loading=true;frameReady=false;notice();current=page;
    if(options.history!==false)history.pushState({page},"",BASE+page);
    for(const link of document.querySelectorAll("#web-navigation a")){const active=link.dataset.route===page;link.classList.toggle("active",active);if(active)link.setAttribute("aria-current","page");else link.removeAttribute("aria-current");}
    $("#web-page-name").textContent=MODULES[page];document.title=`${MODULES[page]} · LANCTL`;
    $("#web-loading").hidden=false;
    $("#web-frame").src=BASE+"view/"+page;
    if(matchMedia("(max-width:850px)").matches)setNav(false,false);
    loading=false;
  }
  function showLogin() {
    csrf="";sessionStorage.removeItem("lanctl.web.csrf");shell=null;current="";
    $("#web-frame").removeAttribute("src");$("#web-workspace").hidden=true;$("#web-login").hidden=false;
    $("#web-login-form").elements.password.value="";
  }
  async function enter() {
    await refreshShell();$("#web-login").hidden=true;$("#web-workspace").hidden=false;
    const preferred=localStorage.getItem("lanctl.web.navigation");
    setNav(preferred?preferred==="open":!matchMedia("(max-width:850px)").matches,false);
    const page=activePage();history.replaceState({page},"",BASE+page);
    await navigate(page,{history:false,force:true});
  }
  window.LanctlWeb={rpc,navigate,context:()=>shell?.projectContext||null,projects:()=>shell?.projects||[],notice};
  document.addEventListener("click",event=>{const link=event.target.closest("a[data-route]");if(link&&!event.ctrlKey&&!event.metaKey&&!event.shiftKey){event.preventDefault();navigate(link.dataset.route).catch(error=>notice(error.message));}});
  function deliverSettings() {
    if(pendingSettings&&frameReady&&current==="panel"){
      pendingSettings=false;
      $("#web-frame").contentWindow.postMessage({type:"lanctl-web-settings"},location.origin);
    }
  }
  $("#web-settings").onclick=async()=>{
    if(!(shell?.permissions||[]).includes("system.configure"))return;
    pendingSettings=true;
    try{await navigate("panel");if(current!=="panel")pendingSettings=false;deliverSettings();}
    catch(error){pendingSettings=false;notice(error.message);}
  };
  $("#web-toggle").onclick=()=>setNav($("#web-workspace").dataset.nav!=="open");
  $("#web-backdrop").onclick=()=>setNav(false,false);
  matchMedia("(max-width:850px)").addEventListener("change",()=>setNav($("#web-workspace").dataset.nav==="open",false));
  document.addEventListener("keydown",event=>{if(event.key==="Escape"&&matchMedia("(max-width:850px)").matches)setNav(false,false);});
  $("#web-frame").onload=()=>{$("#web-loading").hidden=true;};
  $("#web-project").onchange=async event=>{
    const path=event.target.value;if(!path){event.target.value=shell.activeProject||"";return;}
    if(hasOpenForm()&&!confirm(tr("LANCTL.WEB.DISCARD_FORM"))){event.target.value=shell.activeProject||"";return;}
    event.target.disabled=true;
    try{const result=await rpc("panel","use_project",[path],shell.projectContext);if(!result.ok)throw new Error(result.error);await navigate(current,{force:true,history:false});}
    catch(error){notice(error.message);event.target.value=shell.activeProject||"";}
    finally{event.target.disabled=false;}
  };
  $("#web-logout").onclick=async()=>{try{await request("logout",{});showLogin();}catch(error){notice(error.message);}};
  $("#web-login-form").onsubmit=async event=>{
    event.preventDefault();const form=event.target,button=form.querySelector("button");button.disabled=true;$("#login-error").textContent="";
    try{const result=await request("login",{username:form.username.value,password:form.password.value});if(!result.csrfToken)throw new Error(result.error||tr("LANCTL.WEB.DENIED"));csrf=result.csrfToken;sessionStorage.setItem("lanctl.web.csrf",csrf);form.password.value="";await enter();}
    catch(error){$("#login-error").textContent=error.message;}finally{button.disabled=false;}
  };
  addEventListener("popstate",()=>{if(shell)navigate(activePage(),{history:false,force:true});});
  addEventListener("message",event=>{if(event.origin!==location.origin||event.source!==$("#web-frame").contentWindow)return;if(event.data?.type==="lanctl-web-ready"){frameReady=true;$("#web-loading").hidden=true;deliverSettings();}});
  setInterval(async()=>{if(!shell||document.hidden)return;try{const payload=await request("presentation");if(payload.ok)applyPresentation(payload);}catch{/* The next explicit action reports a lost connection. */}},5000);
  (async()=>{try{applyPresentation(await request("presentation"));if(csrf)await enter();}catch(error){showLogin();$("#login-error").textContent=error.message;}})();
})();
