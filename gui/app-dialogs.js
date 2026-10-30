"use strict";
// Local presentation only; decisions remain with the calling application.
const appNotice=document.createElement("dialog");
appNotice.setAttribute("aria-labelledby","app-notice-title");
appNotice.innerHTML="<h2 id=\"app-notice-title\">LANIP</h2><p id=\"app-notice-text\"></p><input id=\"app-notice-value\" aria-label=\"Valor\" hidden data-i18n-aria-label=\"LANCTL.UI.TEXT.VALUE\"><div class=\"dialog-actions\"><button type=\"button\" id=\"app-notice-cancel\"><span data-i18n=\"LANCTL.INVENTORY.MANUAL.CANCEL\">Cancelar</span></button><button type=\"button\" id=\"app-notice-accept\" class=\"primary\"><span data-i18n=\"LANCTL.UI.TEXT.CONTINUE\">Continuar</span></button></div>";
document.body.append(appNotice);
let appNoticeResolve=null,appNoticePrompt=false;
function appDecision(text,prompt=false){
  if(appNoticeResolve)return Promise.resolve(prompt?null:false);
  appNoticePrompt=prompt;
  document.querySelector("#app-notice-text").textContent=text;
  const input=document.querySelector("#app-notice-value");input.hidden=!prompt;input.value="";
  return new Promise(resolve=>{appNoticeResolve=resolve;appNotice.showModal();(prompt?input:document.querySelector("#app-notice-cancel")).focus();});
}
function appDecisionFinish(accepted){
  if(!appNoticeResolve)return;
  const resolve=appNoticeResolve;appNoticeResolve=null;
  const value=appNoticePrompt?(accepted?document.querySelector("#app-notice-value").value:null):accepted;
  appNotice.close();resolve(value);
}
document.querySelector("#app-notice-cancel").onclick=()=>appDecisionFinish(false);
document.querySelector("#app-notice-accept").onclick=()=>appDecisionFinish(true);
appNotice.addEventListener("cancel",event=>{event.preventDefault();appDecisionFinish(false);});
appNotice.addEventListener("keydown",event=>{if(event.key==="Enter"&&appNoticePrompt){event.preventDefault();appDecisionFinish(true);}});
