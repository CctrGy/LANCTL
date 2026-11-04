"use strict";
// Local suite dialog; business rules and preview tokens belong to the backend.
window.openShortcutForm=async()=>{
  const tr=key=>window.LanctlI18n.t(key);
  const options=await call("shortcut_options");
  if(!options.supported){message(tr("LANCTL.SHORTCUT.UNSUPPORTED"),true);return;}
  const nodes=[];
  const select=(label,name,items,value)=>{
    const node=document.createElement("label"),input=document.createElement("select");
    node.textContent=label;input.name=name;
    for(const item of items){const option=document.createElement("option");option.value=item;option.textContent=item.toUpperCase();input.append(option);}
    input.value=value;node.append(input);return node;
  };
  nodes.push(select(tr("LANCTL.SHORTCUT.LAUNCHER"),"launcher",options.launchers,"lanctl"));
  nodes.push(select(tr("LANCTL.SHORTCUT.MODE"),"mode",options.modes.filter(mode=>mode!=="gui"||options.guiAvailable),"tui"));
  const name=field(tr("LANCTL.SHORTCUT.NAME"),"name","LANCTL TUI");name.querySelector("input").required=true;nodes.push(name);
  for(const [key,label] of [["distribution","LANCTL.SHORTCUT.DISTRIBUTION"],["destination","LANCTL.SHORTCUT.DESTINATION"],["working_directory","LANCTL.SHORTCUT.WORKING"],["icon","LANCTL.SHORTCUT.ICON"]]){
    const node=field(tr(label),key,key==="distribution"?options.distribution:"");
    const input=node.querySelector("input"),browse=document.createElement("button");
    browse.type="button";browse.textContent=tr("LANCTL.SHORTCUT.BROWSE");
    browse.onclick=async()=>{browse.disabled=true;try{const result=await call("select_shortcut_path",key);if(!result.cancelled)input.value=result.path;}catch(error){document.querySelector("#form-error").textContent=error.message;}finally{browse.disabled=false;}};
    node.append(browse);nodes.push(node);
  }
  const note=document.createElement("p");note.className="muted";note.textContent=tr("LANCTL.SHORTCUT.NOTE");nodes.push(note);
  showForm(tr("LANCTL.SHORTCUT.TITLE"),nodes,async values=>{
    const plan=await call("preview_shortcut",values);
    if(!document.querySelector("#dialog").open)return;
    const summary=[[tr("LANCTL.SHORTCUT.EXECUTABLE"),plan.executable],[tr("LANCTL.SHORTCUT.ARGUMENTS"),plan.arguments.join(" ")],[tr("LANCTL.SHORTCUT.WORKING"),plan.workingDirectory],[tr("LANCTL.SHORTCUT.ICON"),plan.icon],[tr("LANCTL.SHORTCUT.TARGET"),plan.target]].map(([key,value])=>`${key}: ${value}`).join("\n");
    if(!await confirmAction(tr("LANCTL.SHORTCUT.CONFIRM")+"\n\n"+summary,tr("LANCTL.SHORTCUT.CREATE_BUTTON")))return;
    const result=await call("create_shortcut",plan.token);message(result.message);
  },tr("LANCTL.SHORTCUT.PREVIEW_BUTTON"));
  name.querySelector("input").focus();
};
