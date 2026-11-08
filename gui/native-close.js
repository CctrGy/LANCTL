"use strict";
// State updates have no RPC return callback. Only publish the receipt after the
// prepare RPC resolves; Python additionally joins that RPC thread before closing.
window.requestNativeClose=async(decision)=>{
  const bridge=window.pywebview;
  if(!bridge?.state?.addEventListener||typeof bridge.api?.prepare_native_close!=="function"){
    return decision===undefined?call("request_close"):call("request_close",decision);
  }
  if(window.nativeClosePending)return {queued:true};
  window.nativeClosePending=true;
  try{
    const prepared=await call("prepare_native_close",decision??"save");
    const failed=event=>{
      if(event.detail.key!=="lanctl_close_error"||event.detail.value?.token!==prepared.token)return;
      bridge.state.removeEventListener("change",failed);window.nativeClosePending=false;
      const result=event.detail.value;
      message((result.error||window.LanctlI18n.t("LANCTL.GUI.CLOSE.INVALID"))+(result.errorId?` (${result.errorId})`:""),true);
    };
    bridge.state.addEventListener("change",failed);
    bridge.state.lanctl_close_receipt=prepared.token;
    return {queued:true};
  }catch(error){window.nativeClosePending=false;throw error;}
};
