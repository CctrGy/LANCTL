"use strict";

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
  showForm("Crear grupo",[{key:"name",label:"Nombre del grupo",value:""},{key:"description",label:"Descripción (máximo 42 caracteres)",value:""}],async values=>{
    if(!values.name.trim())throw new Error("Indica el nombre del grupo.");
    const result=await call("create_group",values.name,values.description);renderInventory(result);message(result.message);
  });
  document.querySelector('#desktop-fields input[name="name"]').required=true;
  document.querySelector('#desktop-fields input[name="description"]').maxLength=42;
});
window.addEventListener("pywebviewready",()=>{if(!desktopReady){$("#lanip-cli").hidden=true;$("#new-group").hidden=true;}});
