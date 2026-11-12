"use strict";
// Adapt the native pywebview contract to the authenticated, allowlisted LAN API.
// The launcher HTML/CSS/JS remains shared with the installed desktop program.
window.LANCTL_WEB = true;
(() => {
  const page=location.pathname.split("/").filter(Boolean).at(-1);
  const routes={lanctl:"panel",lanip:"ip",lanwire:"wire",lanaccess:"access",lanrack:"rack",lanmon:"mon"};
  const tr=key=>window.LanctlI18n.t(key);
  function decorate() {
    for(const selector of ["#external-cli","#cli","#lanip-cli","#open-terminal","#open-device","#show-shares","[data-page=terminal]","[data-action=shortcut]","[data-action=project-directory]"])
      document.querySelectorAll(selector).forEach(node=>{node.hidden=true;});
    for(const selector of ["#session-state","#connection","footer .ready"]){const node=document.querySelector(selector);if(node)node.textContent=tr("LANCTL.WEB.REMOTE_SESSION");}
  }
  async function chooseProject() {
    const dialog=document.createElement("dialog"),form=document.createElement("form"),title=document.createElement("h2"),select=document.createElement("select"),actions=document.createElement("div");
    title.textContent=tr("LANCTL.WEB.CHOOSE_PROJECT");form.method="dialog";select.setAttribute("aria-label",title.textContent);
    for(const project of parent.LanctlWeb.projects())select.add(new Option(project.name,project.path));
    for(const [value,key] of [["cancel","LANCTL.INVENTORY.MANUAL.CANCEL"],["select","LANCTL.UI.TEXT.SELECT"]]){const button=document.createElement("button");button.value=value;button.textContent=tr(key);if(value==="select")button.disabled=!select.options.length;actions.append(button);}
    actions.className="web-picker-actions";form.append(title,select,actions);dialog.append(form);document.body.append(dialog);
    return new Promise(resolve=>{dialog.addEventListener("close",()=>{const path=dialog.returnValue==="select"?select.value:"";dialog.remove();resolve({ok:true,path});},{once:true});dialog.showModal();});
  }
  addEventListener("DOMContentLoaded",async()=>{
    if(parent===window||!parent.LanctlWeb)return;
    try{
      let context=parent.LanctlWeb.context();
      let initial=await parent.LanctlWeb.rpc(page,"bootstrap",[],context);
      if(!initial.ok)throw new Error(initial.error||tr("LANCTL.WEB.DENIED"));
      context=initial.projectContext||context;
      const invoke=async(method,args)=>{
        const response=await parent.LanctlWeb.rpc(page,method,args,context);
        if(response.projectContext)context=response.projectContext;
        setTimeout(decorate,0);return response;
      };
      const api=Object.create(null);
      for(const method of initial.webMethods||[])api[method]=(...args)=>invoke(method,args);
      api.project_call=(...args)=>invoke("project_call",args);
      api.bootstrap=async()=>{if(initial){const payload=initial;initial=null;setTimeout(decorate,0);return payload;}return invoke("bootstrap",[]);};
      const go=launcher=>{const route=routes[launcher]||launcher;if(!["panel","ip","wire","access","rack","mon"].includes(route))return Promise.resolve({ok:false,error:tr("LANCTL.WEB.DENIED")});parent.LanctlWeb.navigate(route);return Promise.resolve({ok:true});};
      api.launch_gui=go;api.open_gui=go;api.open_suite=()=>go("panel");api.open_monitor=()=>go("mon");api.open_live_logs=()=>go("mon");
      api.select_project_file=chooseProject;
      api.select_project_directory=async()=>({ok:false,error:tr("LANCTL.WEB.NATIVE_ONLY")});
      api.request_close=async()=>({ok:false,error:tr("LANCTL.WEB.NATIVE_ONLY")});
      window.pywebview={api};
      decorate();window.dispatchEvent(new Event("pywebviewready"));
      addEventListener("message",event=>{
        if(event.origin!==location.origin||event.source!==parent||event.data?.type!=="lanctl-web-settings")return;
        if(page!=="panel"||!window.openSettingsWindow)return;
        Promise.resolve(window.openSettingsWindow()).catch(error=>parent.LanctlWeb.notice(error.message));
      });
      parent.postMessage({type:"lanctl-web-ready"},location.origin);
      const observer=new MutationObserver(()=>{for(const node of document.querySelectorAll("[data-action=project-directory],[data-page=terminal],[data-action=shortcut]"))node.hidden=true;});
      observer.observe(document.body,{childList:true,subtree:true});
    }catch(error){parent.LanctlWeb.notice(error.message);}
  });
})();
