"use strict";

// Full catalog in a dedicated modal; business validation stays in shared services.
(() => {
  const labels=()=>({interface:window.LanctlI18n.t("LANCTL.UI.TEXT.STARTUP_INTERFACE"),closeGuiOnLaunch:window.LanctlI18n.t("LANCTL.UI.TEXT.CLOSE_LANCTL_WHEN_OPENING_ANOTHER_APPLICATION"),cleanupEnabled:window.LanctlI18n.t("LANCTL.UI.TEXT.CLEAN_OLD_LOGS"),retentionDays:window.LanctlI18n.t("LANCTL.UI.TEXT.RETENTION_DAYS"),errorLevel:window.LanctlI18n.t("LANCTL.UI.TEXT.ERROR_LEVEL"),saveMode:window.LanctlI18n.t("LANCTL.UI.TEXT.SAVE_MODE"),saveIntervalMinutes:window.LanctlI18n.t("LANCTL.UI.TEXT.SAVE_INTERVAL_MINUTES"),directory:window.LanctlI18n.t("LANCTL.UI.TEXT.PROJECT_FOLDER"),language:window.LanctlI18n.t("LANCTL.UI.TEXT.LANGUAGE"),safeMode:window.LanctlI18n.t("LANCTL.UI.TEXT.PLUGIN_SAFE_MODE"),range:window.LanctlI18n.t("LANCTL.UI.TEXT.NETWORK_RANGE"),cidr:window.LanctlI18n.t("LANCTL.UI.TEXT.CIDR_NETWORK"),dhcpRange:window.LanctlI18n.t("LANCTL.UI.TEXT.DHCP_RANGE"),tr064Port:window.LanctlI18n.t("LANCTL.UI.TEXT.TR_064_PORT"),gateway:window.LanctlI18n.t("LANCTL.UI.TEXT.GATEWAY"),subnetMask:window.LanctlI18n.t("LANCTL.UI.TEXT.SUBNET_MASK"),dhcpEnabled:window.LanctlI18n.t("LANCTL.UI.TEXT.DHCP_ENABLED"),dnsServers:window.LanctlI18n.t("LANCTL.UI.TEXT.DNS_SERVERS"),dns:window.LanctlI18n.t("LANCTL.UI.TEXT.DNS_SERVERS"),domainName:window.LanctlI18n.t("LANCTL.UI.TEXT.DOMAIN_NAME"),reservedAddresses:window.LanctlI18n.t("LANCTL.UI.TEXT.RESERVED_ADDRESSES"),tr064Host:window.LanctlI18n.t("LANCTL.UI.TEXT.TR_064_SERVER"),dhcpLeaseTime:window.LanctlI18n.t("LANCTL.UI.TEXT.DHCP_LEASE_SECONDS"),workers:window.LanctlI18n.t("LANCTL.UI.TEXT.CONCURRENT_CHECKS"),timeout:window.LanctlI18n.t("LANCTL.UI.TEXT.TIMEOUT_SECONDS"),maxHosts:window.LanctlI18n.t("LANCTL.UI.TEXT.MAXIMUM_HOSTS"),discovery:window.LanctlI18n.t("LANCTL.UI.TEXT.DISCOVERY_METHOD"),scanProfile:window.LanctlI18n.t("LANCTL.UI.TEXT.SCAN_PROFILE"),scanOrder:window.LanctlI18n.t("LANCTL.UI.TEXT.SCAN_ORDER"),serviceIdentification:window.LanctlI18n.t("LANCTL.UI.TEXT.IDENTIFY_SERVICES"),disconnectedRetention:window.LanctlI18n.t("LANCTL.UI.TEXT.KEEP_DISCONNECTED_DEVICES"),disconnectedRetentionTarget:window.LanctlI18n.t("LANCTL.UI.TEXT.DEVICES_AFFECTED_BY_RETENTION"),disconnectedRetentionScope:window.LanctlI18n.t("LANCTL.UI.TEXT.RETENTION_SCOPE"),port:window.LanctlI18n.t("LANCTL.UI.TEXT.PORT"),repeat:window.LanctlI18n.t("LANCTL.UI.TEXT.REPETITIONS"),interval:window.LanctlI18n.t("LANCTL.UI.TEXT.INTERVAL_SECONDS"),wait:window.LanctlI18n.t("LANCTL.UI.TEXT.WAIT_SECONDS"),method:window.LanctlI18n.t("LANCTL.UI.TEXT.METHOD"),enabled:window.LanctlI18n.t("LANCTL.UI.TEXT.ENABLED_BA5F3324"),bind:window.LanctlI18n.t("LANCTL.UI.TEXT.LISTEN_ADDRESS"),passwordAuthentication:window.LanctlI18n.t("LANCTL.UI.TEXT.PASSWORD_AUTHENTICATION"),backend:window.LanctlI18n.t("LANCTL.UI.TEXT.SERVICE_TYPE"),forcedView:window.LanctlI18n.t("LANCTL.UI.TEXT.REMOTE_VIEW"),profile:window.LanctlI18n.t("LANCTL.UI.TEXT.PROFILE"),mode:window.LanctlI18n.t("LANCTL.UI.TEXT.OPERATING_MODE"),authority:window.LanctlI18n.t("LANCTL.UI.TEXT.OPERATION_PERMISSIONS"),duration:window.LanctlI18n.t("LANCTL.UI.TEXT.DURATION_SECONDS"),failureThreshold:window.LanctlI18n.t("LANCTL.UI.TEXT.FAILURES_BEFORE_MARKING_AN_INCIDENT"),recoveryThreshold:window.LanctlI18n.t("LANCTL.UI.TEXT.SUCCESSES_TO_CONFIRM_RECOVERY"),criticalDevices:window.LanctlI18n.t("LANCTL.UI.TEXT.CRITICAL_DEVICES_SECONDS"),deviceStatus:window.LanctlI18n.t("LANCTL.UI.TEXT.DEVICE_STATUS_SECONDS"),networkDiscovery:window.LanctlI18n.t("LANCTL.UI.TEXT.NETWORK_DISCOVERY_SECONDS"),serviceScan:window.LanctlI18n.t("LANCTL.UI.TEXT.SERVICE_SCAN_SECONDS"),fullScan:window.LanctlI18n.t("LANCTL.UI.TEXT.FULL_SCAN_SECONDS"),rawSamples:window.LanctlI18n.t("LANCTL.UI.TEXT.RAW_SAMPLES"),fiveMinuteAggregates:window.LanctlI18n.t("LANCTL.UI.TEXT.FIVE_MINUTE_SUMMARIES"),hourlyAggregates:window.LanctlI18n.t("LANCTL.UI.TEXT.HOURLY_SUMMARIES"),events:window.LanctlI18n.t("LANCTL.UI.TEXT.EVENTS"),theme:window.LanctlI18n.t("LANCTL.UI.TEXT.THEME"),density:window.LanctlI18n.t("LANCTL.UI.TEXT.CONTROL_DENSITY"),fontScale:window.LanctlI18n.t("LANCTL.UI.TEXT.TEXT_SCALE"),reducedMotion:window.LanctlI18n.t("LANCTL.UI.TEXT.REDUCE_ANIMATIONS"),name:window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.NAME"),description:window.LanctlI18n.t("LANCTL.INVENTORY.MANUAL.DESCRIPTION"),author:window.LanctlI18n.t("LANCTL.UI.TEXT.AUTHOR"),location:window.LanctlI18n.t("LANCTL.UI.TEXT.LOCATION"),company:window.LanctlI18n.t("LANCTL.UI.TEXT.COMPANY"),responsible:window.LanctlI18n.t("LANCTL.UI.TEXT.RESPONSIBLE_PERSON"),nativeVlan:window.LanctlI18n.t("LANCTL.UI.TEXT.NATIVE_VLAN"),managementVlan:window.LanctlI18n.t("LANCTL.UI.TEXT.MANAGEMENT_VLAN")});
  const choiceLabels=()=>({hybrid:window.LanctlI18n.t("LANCTL.UI.TEXT.HYBRID_ICMP_AND_ARP"),icmp:"ICMP",arp:"ARP",manual:window.LanctlI18n.t("LANCTL.UI.TEXT.MANUAL_ONLY"),"manual.inCloseConsult":window.LanctlI18n.t("LANCTL.UI.TEXT.MANUAL_WITH_CONFIRMATION_ON_CLOSE"),cli:window.LanctlI18n.t("LANCTL.UI.TEXT.COMMAND_LINE_CLI"),tui:window.LanctlI18n.t("LANCTL.UI.TEXT.VISUAL_TERMINAL_TUI"),gui:window.LanctlI18n.t("LANCTL.UI.TEXT.GRAPHICAL_INTERFACE_GUI"),fast:window.LanctlI18n.t("LANCTL.UI.TEXT.FAST"),normal:window.LanctlI18n.t("LANCTL.UI.TEXT.NORMAL"),accurate:window.LanctlI18n.t("LANCTL.UI.TEXT.PRECISE"),ascending:window.LanctlI18n.t("LANCTL.UI.TEXT.ASCENDING"),descending:window.LanctlI18n.t("LANCTL.UI.TEXT.DESCENDING"),random:window.LanctlI18n.t("LANCTL.UI.TEXT.RANDOM"),auto:window.LanctlI18n.t("LANCTL.UI.TEXT.AUTOMATIC"),observe:window.LanctlI18n.t("LANCTL.UI.TEXT.OBSERVE"),operate:window.LanctlI18n.t("LANCTL.UI.TEXT.OPERATE"),administer:window.LanctlI18n.t("LANCTL.UI.TEXT.ADMINISTER"),permanent:window.LanctlI18n.t("LANCTL.UI.TEXT.PERMANENT"),temporary:window.LanctlI18n.t("LANCTL.UI.TEXT.TEMPORARY"),diagnostic:window.LanctlI18n.t("LANCTL.UI.TEXT.DIAGNOSTICS"),once:window.LanctlI18n.t("LANCTL.UI.TEXT.ONCE"),session:window.LanctlI18n.t("LANCTL.UI.TEXT.DURING_THE_SESSION"),forget:window.LanctlI18n.t("LANCTL.UI.TEXT.FORGET"),all:window.LanctlI18n.t("LANCTL.UI.TEXT.ALL"),unconfirmed:window.LanctlI18n.t("LANCTL.UI.TEXT.UNCONFIRMED"),off:window.LanctlI18n.t("LANCTL.UI.TEXT.DISABLED"),service:window.LanctlI18n.t("LANCTL.UI.TEXT.SYSTEM_SERVICE"),user:window.LanctlI18n.t("LANCTL.UI.TEXT.USER_PROCESS")});
  const shortCategories=()=>({startup:window.LanctlI18n.t("LANCTL.UI.TEXT.GENERAL"),projects:window.LanctlI18n.t("LANCTL.UI.TEXT.PROJECTS"),localization:window.LanctlI18n.t("LANCTL.UI.TEXT.LANGUAGE"),logging:window.LanctlI18n.t("LANCTL.UI.TEXT.LOGS"),plugins:window.LanctlI18n.t("LANCTL.UI.WORD.PLUGINS"),network:window.LanctlI18n.t("LANCTL.UI.TEXT.NETWORK"),ip:"LANIP",wol:window.LanctlI18n.t("LANCTL.UI.VIEW.WAKE_ON_LAN"),access:window.LanctlI18n.t("LANCTL.UI.TEXT.REMOTE_ACCESS"),monitor:"LANMON",gui:window.LanctlI18n.t("LANCTL.UI.TEXT.APPEARANCE"),identity:window.LanctlI18n.t("LANCTL.UI.TEXT.IDENTITY"),lan:"LAN",vlan:"VLAN"});
  const dialog=document.createElement("dialog");dialog.id="suite-settings";dialog.setAttribute("aria-labelledby","suite-settings-title");dialog.setAttribute("aria-describedby","ss-subtitle");
  dialog.innerHTML="<form novalidate><div class=\"ss-head\"><div><small><span data-i18n=\"LANCTL.UI.TEXT.LANCTL_SETTINGS\">LANCTL · CONFIGURACIÓN</span></small><h2 id=\"suite-settings-title\"><span data-i18n=\"LANCTL.UI.TEXT.SETTINGS\">Configuración</span></h2><p id=\"ss-subtitle\"></p></div><button type=\"button\" id=\"ss-close\" aria-label=\"Cerrar configuración\" data-i18n-aria-label=\"LANCTL.UI.TEXT.CLOSE_SETTINGS\">×</button></div><div class=\"ss-filters\"><div class=\"ss-scopes\" role=\"group\" aria-label=\"Ámbito\" data-i18n-aria-label=\"LANCTL.UI.TEXT.SCOPE\"><button type=\"button\" data-ss-scope=\"program\"><span data-i18n=\"LANCTL.UI.TEXT.PROGRAM\">Programa</span></button><button type=\"button\" data-ss-scope=\"project\"><span data-i18n=\"LANCTL.UI.TEXT.ACTIVE_PROJECT\">Proyecto activo</span></button></div><input id=\"ss-search\" type=\"search\" aria-label=\"Buscar opciones de configuración\" placeholder=\"Buscar una opción…\" data-i18n-placeholder=\"LANCTL.UI.TEXT.SEARCH_FOR_AN_OPTION\" data-i18n-aria-label=\"LANCTL.UI.TEXT.SEARCH_SETTINGS_OPTIONS\"></div><nav id=\"ss-tabs\" role=\"tablist\" aria-label=\"Categorías de configuración\" data-i18n-aria-label=\"LANCTL.UI.TEXT.SETTINGS_CATEGORIES\"></nav><div id=\"ss-content\"></div><footer class=\"ss-footer\"><p id=\"ss-status\" role=\"status\"></p><div><button type=\"button\" id=\"ss-cancel\"><span data-i18n=\"LANCTL.UI.TEXT.CLOSE\">Cerrar</span></button><button type=\"submit\" id=\"ss-save\" class=\"primary\"><span data-i18n=\"LANCTL.UI.TEXT.SAVE_CHANGES\">Guardar cambios</span></button></div></footer></form>";
  document.body.append(dialog);
  const find=s=>dialog.querySelector(s);
  let entries=[],controls=new Map(),scope="program",launcher="lanctl",active="",categories={},context,busy=false,loading=false;
  const equal=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
  const label=entry=>labels()[entry.path.split(".").pop()]||entry.path.split(".").pop().replace(/([a-z])([A-Z])/g,"$1 $2");
  function note(text,error=false){find("#ss-status").textContent=text;find("#ss-status").classList.toggle("error",error);}
  async function rpc(method,...args){
    const api=window.pywebview?.api;if(!api)throw new Error(window.LanctlI18n.t("LANCTL.UI.TEXT.THE_LANCTL_API_IS_NOT_AVAILABLE"));
    const result=api.project_call&&context!==undefined&&["save_catalog_settings","save_catalog_setting"].includes(method)?await api.project_call(context,method,args):await api[method](...args);
    if(!result.ok)throw new Error(result.error||window.LanctlI18n.t("LANCTL.UI.TEXT.COULD_NOT_COMPLETE_THE_OPERATION"));
    return result;
  }
  function value(entry,control){
    if(control.auto?.checked)return null;
    if(control.input.type==="checkbox")return control.input.checked;
    const raw=control.input.value;
    if(entry.control==="number"){
      if(!raw.trim()||!Number.isFinite(Number(raw)))throw new Error(label(entry)+window.LanctlI18n.t("LANCTL.UI.FRAGMENT.ENTER_A_VALID_NUMBER"));
      return Number(raw);
    }
    if(entry.control==="json")return JSON.parse(raw);
    if(entry.control==="lines")return raw.split("\n").map(item=>item.trim()).filter(Boolean);
    return raw;
  }
  function changed(entry){try{return !equal(value(entry,controls.get(entry.path)),entry.value);}catch{return true;}}
  const dirty=()=>entries.some(entry=>!entry.readOnly&&changed(entry));
  function setBusy(value){busy=value;dialog.setAttribute("aria-busy",String(value));for(const entry of entries){const control=controls.get(entry.path);if(!control)continue;control.input.disabled=value||Boolean(entry.readOnly)||Boolean(control.auto?.checked);if(control.auto)control.auto.disabled=value||Boolean(entry.readOnly);if(control.save)control.save.disabled=value||!changed(entry);if(control.browse)control.browse.disabled=value;}find("#ss-save").disabled=value;find("#ss-close").disabled=value;find("#ss-cancel").disabled=value;for(const button of dialog.querySelectorAll("[data-ss-scope]"))button.disabled=value;}
  function update(){
    const count=entries.filter(entry=>!entry.readOnly&&changed(entry)).length;
    note(count? window.LanctlI18n.t("LANCTL.UI.WEB.UNSAVED_CHANGES",{value0:(count),value1:(count===1?"":"s")}): window.LanctlI18n.t("LANCTL.UI.WEB.SETTING_OPTIONS",{value0:(entries.length),value1:(scope==="project"?window.LanctlI18n.t("LANCTL.UI.VIEW.SAVE_EACH_SETTING_WITH_ITS_BUTTON"):window.LanctlI18n.t("LANCTL.UI.VIEW.NO_PENDING_CHANGES"))}));
    for(const entry of entries){const item=controls.get(entry.path);item.card.classList.toggle("ss-changed",changed(entry));if(item.save)item.save.disabled=busy||!changed(entry);}
    find("#ss-save").disabled=busy||count===0;
  }
  async function allowDiscard(){return !dirty()||await confirmAction(window.LanctlI18n.t("LANCTL.UI.TEXT.THERE_ARE_UNSAVED_SETTINGS_DISCARD_THEM"),window.LanctlI18n.t("LANCTL.UI.TEXT.DISCARD_CHANGES"));}
  async function close(){if(busy||loading)return false;if(!await allowDiscard())return false;dialog.close();return true;}
  window.confirmSettingsClose=async()=>!dialog.open||close();
  find("#ss-close").onclick=find("#ss-cancel").onclick=close;
  dialog.addEventListener("cancel",event=>{event.preventDefault();close();});
  function filter(){
    const query=find("#ss-search").value.trim().toLocaleLowerCase();
    const matches=entry=>(label(entry)+" "+entry.path+" "+(categories[entry.category]||"")).toLocaleLowerCase().includes(query);
    for(const entry of entries)controls.get(entry.path).card.hidden=!matches(entry)||(!query&&entry.category!==active);
    for(const tab of find("#ss-tabs").children){tab.setAttribute("aria-selected",String(!query&&tab.dataset.category===active));tab.tabIndex=tab.dataset.category===active?0:-1;}
    for(const pane of find("#ss-content").querySelectorAll(".ss-grid"))pane.hidden=![...pane.children].some(card=>!card.hidden);
    const empty=find("#ss-empty");if(empty)empty.hidden=entries.some(entry=>!controls.get(entry.path).card.hidden);
  }
  function choose(category){active=category;find("#ss-search").value="";filter();find("#ss-content").scrollTop=0;}
  find("#ss-search").oninput=filter;
  function makeControl(entry){
    const card=document.createElement("section");card.className="ss-card";card.dataset.path=entry.path;
    const caption=document.createElement("label"),title=document.createElement("span");title.className="ss-label";title.textContent=label(entry);caption.append(title);
    const id="ss-field-"+controls.size;caption.htmlFor=id;
    const choices=entry.choices||[];
    let input=document.createElement(choices.length?"select":["lines","json"].includes(entry.control)?"textarea":"input");input.id=id;
    if(choices.length){for(const choice of choices)input.add(new Option(choiceLabels()[choice.value]||choice.label,String(choice.value)));if(entry.value!==null&&!choices.some(choice=>choice.value===entry.value))input.add(new Option(String(entry.value),String(entry.value)));input.value=entry.value??String(choices[0].value);}
    else if(entry.control==="boolean"){input.type="checkbox";input.checked=Boolean(entry.value);card.classList.add("ss-checkbox");}
    else if(entry.control==="number"){input.type="number";input.step="any";input.value=entry.value??"";}
    else if(entry.control==="json"){input.value=JSON.stringify(entry.value,null,2);input.rows=5;card.classList.add("ss-wide");}
    else if(entry.control==="lines"){input.value=(entry.value||[]).join("\n");input.rows=3;}
    else{input.type="text";input.value=entry.value??"";}
    card.append(caption,input);
    const help=document.createElement("small");help.className="ss-hint";help.textContent=entry.readOnly|| (entry.control==="lines"?window.LanctlI18n.t("LANCTL.UI.TEXT.ONE_ADDRESS_OR_VALUE_PER_LINE"):entry.control==="json"?window.LanctlI18n.t("LANCTL.UI.TEXT.ADVANCED_JSON_STRUCTURE"):entry.path.startsWith("monitor.retention.")?window.LanctlI18n.t("LANCTL.UI.TEXT.EXAMPLES_24H_30D_OR_PERMANENT"):"");if(help.textContent)card.append(help);
    let auto=null;
    if(entry.nullable){const row=document.createElement("label");row.className="ss-auto";auto=document.createElement("input");auto.type="checkbox";auto.checked=entry.value===null;row.append(auto,document.createTextNode(window.LanctlI18n.t("LANCTL.UI.VIEW.USE_AUTOMATIC_VALUE")));card.append(row);auto.onchange=()=>{input.disabled=busy||Boolean(entry.readOnly)||auto.checked;update();};}
    input.disabled=Boolean(entry.readOnly)||Boolean(auto?.checked);if(auto)auto.disabled=Boolean(entry.readOnly);
    input.oninput=input.onchange=update;
    const technical=document.createElement("p"),captionKey=document.createElement("span"),code=document.createElement("code");technical.className="ss-technical";window.LanctlI18n.bindText(captionKey,"LANCTL.UI.TEXT.TECHNICAL_KEY");code.textContent=entry.path;technical.append(captionKey,code);card.append(technical);
    const control={input,auto,card};controls.set(entry.path,control);
    if(entry.path==="projects.directory"&&!entry.readOnly){
      const browse=document.createElement("button");browse.type="button";browse.className="ss-save-one";window.LanctlI18n.bindText(browse,"LANCTL.UI.TEXT.CHOOSE_FOLDER");card.append(browse);control.browse=browse;
      browse.onclick=async()=>{if(busy)return;setBusy(true);try{const folder=await rpc("select_project_directory");if(folder.path){if(auto)auto.checked=false;input.value=folder.path;update();}}catch(error){note(error.message,true);}finally{setBusy(false);updateButtons();}};
    }
    if(scope==="project"&&!entry.readOnly){
      const save=document.createElement("button");save.type="button";save.className="ss-save-one";window.LanctlI18n.bindText(save,"LANCTL.UI.TEXT.SAVE_THIS_SETTING");control.save=save;card.append(save);
      save.onclick=async()=>{if(busy)return;try{const next=value(entry,control);setBusy(true);await rpc("save_catalog_setting","project",entry.path,next);entry.value=next;update();note(window.LanctlI18n.t("LANCTL.UI.VIEW.PROJECT_SETTING_SAVED"));}catch(error){note(error.message,true);}finally{setBusy(false);updateButtons();}};
    }
    return card;
  }
  function updateButtons(){find("#ss-save").disabled=busy||!dirty();for(const entry of entries){const item=controls.get(entry.path);if(item.save)item.save.disabled=busy||!changed(entry);}}
  async function load(nextScope,nextLauncher){
    if(loading)return;loading=true;setBusy(true);
    try{
      const payload=await rpc(nextLauncher!=="lanctl"?"launcher_settings":"settings_catalog",nextLauncher!=="lanctl"?nextLauncher:nextScope);
      scope=nextScope;launcher=nextLauncher;
      entries=payload.entries.filter(entry=>entry.path!=="access.remote"||!payload.entries.some(other=>other.path.startsWith("access.remote.")));
      categories=payload.categories;controls=new Map();
      const order=["startup","gui","projects","network","ip","access","monitor","logging","plugins","localization","wol","identity","lan","vlan"];
      const categoryNames=[...new Set(entries.map(entry=>entry.category))].sort((a,b)=>{const rank=key=>order.indexOf(key)<0?order.length:order.indexOf(key);return rank(a)-rank(b);});active=categoryNames[0]||"";
      find("#suite-settings-title").textContent=launcher==="lanctl"?window.LanctlI18n.t("LANCTL.UI.TEXT.SETTINGS"):window.LanctlI18n.t("LANCTL.UI.FRAGMENT.SETTINGS_FOR")+launcher.toUpperCase();
      find("#ss-subtitle").textContent=scope==="project"?window.LanctlI18n.t("LANCTL.UI.TEXT.ACTIVE_PROJECT_SETTINGS_EACH_SETTING_IS_SAVED_SEPARATELY"):window.LanctlI18n.t("LANCTL.UI.TEXT.PROGRAM_OPTIONS_GROUPED_BY_TOPIC");
      find("#ss-content").replaceChildren();find("#ss-tabs").replaceChildren();find("#ss-search").value="";
      find(".ss-scopes").hidden=launcher!=="lanctl";
      find("#ss-save").hidden=scope==="project";
      for(const button of dialog.querySelectorAll("[data-ss-scope]"))button.classList.toggle("primary",button.dataset.ssScope===scope);
      for(const category of categoryNames){
        const tab=document.createElement("button");tab.type="button";tab.role="tab";tab.dataset.category=category;tab.id="ss-tab-"+category;tab.textContent=shortCategories()[category]||categories[category]||category;tab.title=categories[category]||category;tab.onclick=()=>choose(category);
        const pane=document.createElement("div");pane.id="ss-pane-"+category;pane.role="tabpanel";pane.className="ss-grid";pane.setAttribute("aria-labelledby",tab.id);tab.setAttribute("aria-controls",pane.id);
        for(const entry of entries.filter(item=>item.category===category))pane.append(makeControl(entry));
        find("#ss-tabs").append(tab);find("#ss-content").append(pane);
      }
      const empty=document.createElement("p");empty.id="ss-empty";empty.className="ss-hint";empty.role="status";window.LanctlI18n.bindText(empty,"LANCTL.UI.TEXT.NO_OPTIONS_MATCH_THE_SEARCH");find("#ss-content").append(empty);
      filter();update();if(!dialog.open)dialog.showModal();find("#ss-search").focus();
    }finally{loading=false;setBusy(false);updateButtons();}
  }
  for(const button of dialog.querySelectorAll("[data-ss-scope]"))button.onclick=async()=>{if(!await allowDiscard())return;try{await load(button.dataset.ssScope,"lanctl");}catch(error){note(error.message,true);}};
  find("#ss-tabs").onkeydown=event=>{
    const tabs=[...find("#ss-tabs").children];let index=tabs.indexOf(document.activeElement);if(index<0)return;
    if(event.key==="ArrowRight")index=(index+1)%tabs.length;else if(event.key==="ArrowLeft")index=(index+tabs.length-1)%tabs.length;else if(event.key==="Home")index=0;else if(event.key==="End")index=tabs.length-1;else return;
    event.preventDefault();tabs[index].click();tabs[index].focus();
  };
  dialog.querySelector("form").onsubmit=async event=>{
    event.preventDefault();if(busy||scope==="project")return;
    const changes={};
    try{
      for(const entry of entries)if(!entry.readOnly&&changed(entry)){
        try{changes[entry.path]=value(entry,controls.get(entry.path));}
        catch(error){choose(entry.category);controls.get(entry.path).input.focus();throw new Error(label(entry)+": "+error.message);}
      }
      if(!Object.keys(changes).length)return;
      setBusy(true);await rpc("save_catalog_settings",changes,launcher);
      for(const entry of entries)if(Object.hasOwn(changes,entry.path))entry.value=changes[entry.path];
      update();note(window.LanctlI18n.t("LANCTL.UI.TEXT.SETTINGS_SAVED"));
    }catch(error){note(error.message,true);}finally{setBusy(false);updateButtons();}
  };
  window.openSettingsWindow=async(nextScope="program",nextLauncher="lanctl")=>{
    if(dialog.open){dialog.focus();return;}
    context=state.projectContext===undefined?undefined:JSON.parse(JSON.stringify(state.projectContext));
    await load(nextScope,nextLauncher);
  };
})();
