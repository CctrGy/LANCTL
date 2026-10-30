"use strict";

$("#search-device").addEventListener("click",()=>filterInventory());
$("#device-search").addEventListener("keydown",event=>{
  if(event.key==="Enter"){event.preventDefault();filterInventory();}
});
const manualInventoryRenderer=renderInventory;
renderInventory=function(payload){
  if(payload.manualDeviceLabels){
    state.manualDeviceLabels=payload.manualDeviceLabels;
    $("#search-device").textContent=payload.manualDeviceLabels.SEARCH;
    $("#create-device").textContent="＋ "+payload.manualDeviceLabels.TITLE;
  }
  return manualInventoryRenderer(payload);
};
$("#create-device").addEventListener("click",()=>{
  const labels=state.manualDeviceLabels;
  if(!labels){message(window.LanctlI18n.t("LANCTL.UI.VIEW.THE_MANUAL_CREATION_API_IS_NOT_AVAILABLE"),true);return;}
  const query=$("#device-search").value.trim();
  const values={name:"",alias:"",idf:"",ip:"",mac:"",description:""};
  if(/^\d{1,3}(\.\d{1,3}){3}$/.test(query))values.ip=query;
  else if(/^([0-9a-f]{2}[:-]){5}[0-9a-f]{2}$/i.test(query))values.mac=query;
  else if(/^[a-z]{2,5}-[0-9]{2,5}$/i.test(query))values.idf=query;
  else values.name=query;
  const expected=state.projectContext;
  showForm(labels.TITLE,[
    {key:"name",label:labels.NAME,value:values.name},
    {key:"alias",label:labels.ALIAS,value:values.alias},
    {key:"idf",label:labels.IDF,value:values.idf},
    {key:"ip",label:labels.IP,value:values.ip},
    {key:"mac",label:labels.MAC,value:values.mac},
    {key:"description",label:labels.DESCRIPTION,value:values.description},
  ],async fields=>{
    if(window.pywebview?.api?.project_call&&expected&&JSON.stringify(expected)!==JSON.stringify(state.projectContext))
      throw new Error(labels.STALE);
    const result=await (window.pywebview?.api?.project_call&&expected
      ?window.pywebview.api.project_call(expected,"create_device",[fields])
      :call("create_device",fields));
    if(!result.ok)throw new Error(result.error||labels.FAILED);
    $("#device-search").value="";
    $("#state-filter").value="all";$("#group-filter").value="";
    for(const id of ["#vendor-filter","#protocol-filter","#cnf-filter","#membership-filter"])$(id).value="";
    state.selectedId=result.createdId;renderInventory(result);message(result.message);
  },labels.ADD);
  $("#desktop-dismiss").textContent=labels.CANCEL;
});

// Keep plugin/history providers available without a permanent navigation row.
function updatePanelMenu(){
  const host=$("#panel-menu-items");host.replaceChildren();
  document.querySelectorAll(".main-navigation button").forEach(source=>{
    const button=document.createElement("button");button.type="button";button.textContent=source.textContent;
    button.addEventListener("click",()=>{source.click();$("#panel-menu").open=false;});host.append(button);
  });
}
new MutationObserver(updatePanelMenu).observe($("#plugin-navigation"),{childList:true});updatePanelMenu();
for(const id of ["#vendor-filter","#protocol-filter","#cnf-filter","#membership-filter"])$(id).addEventListener("change",filterInventory);
$("#clear-filters").addEventListener("click",()=>{
  $("#device-search").value="";$("#state-filter").value="all";
  for(const id of ["#group-filter","#vendor-filter","#protocol-filter","#cnf-filter","#membership-filter"])$(id).value="";
  filterInventory();
});
$("#lanip-cli").addEventListener("click",async()=>{try{message((await call("open_cli")).message);}catch(error){message(error.message,true);}});
$("#lanctl-gui").addEventListener("click",async()=>{try{message((await call("open_suite")).message);}catch(error){message(error.message,true);}});
$("#new-group").addEventListener("click",()=>{
  showForm(window.LanctlI18n.t("LANCTL.UI.TEXT.CREATE_GROUP"),[{key:"name",label:window.LanctlI18n.t("LANCTL.UI.TEXT.GROUP_NAME"),value:""},{key:"description",label:window.LanctlI18n.t("LANCTL.UI.VIEW.DESCRIPTION_MAXIMUM_42_CHARACTERS"),value:""}],async values=>{
    if(!values.name.trim())throw new Error(window.LanctlI18n.t("LANCTL.UI.VIEW.SPECIFY_THE_GROUP_NAME"));
    const result=await call("create_group",values.name,values.description);renderInventory(result);message(result.message);
  });
  document.querySelector('#desktop-fields input[name="name"]').required=true;
  document.querySelector('#desktop-fields input[name="description"]').maxLength=42;
});
window.addEventListener("pywebviewready",()=>{if(!desktopReady){$("#lanip-cli").hidden=true;$("#new-group").hidden=true;}});
