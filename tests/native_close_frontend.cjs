const fs=require('node:fs');
const vm=require('node:vm');
const assert=require('node:assert/strict');
const calls=[], messages=[];
const listeners=new Set();
const state={addEventListener:(name,handler)=>listeners.add(handler),removeEventListener:(name,handler)=>listeners.delete(handler)};
const context={
  window:{pywebview:{state,api:{prepare_native_close(){}}},LanctlI18n:{t:key=>key}},
  call:async(...args)=>{calls.push(args);return args[0]==='prepare_native_close'?{token:'receipt'}:{closed:true};},
  message:(...args)=>messages.push(args),
};
vm.runInNewContext(fs.readFileSync(process.argv[2],'utf8'),context);
(async()=>{
  await context.window.requestNativeClose('discard');
  assert.deepEqual(calls,[['prepare_native_close','discard']]);
  assert.equal(state.lanctl_close_receipt,'receipt');
  assert.equal(context.window.nativeClosePending,true);
  await context.window.requestNativeClose('save');
  assert.equal(calls.length,1);
  for(const handler of [...listeners])handler({detail:{key:'lanctl_close_error',value:{token:'wrong',error:'ignored'}}});
  assert.equal(messages.length,0);
  for(const handler of [...listeners])handler({detail:{key:'lanctl_close_error',value:{token:'receipt',error:'original',errorId:'event'}}});
  assert.equal(messages[0][0],'original (event)');
  assert.equal(context.window.nativeClosePending,false);
  assert.equal(listeners.size,0);
  context.window.pywebview.state=null;
  await context.window.requestNativeClose('save');
  assert.deepEqual(calls.at(-1),['request_close','save']);
  await context.window.requestNativeClose();
  assert.deepEqual(calls.at(-1),['request_close']);
})().catch(error=>{console.error(error);process.exitCode=1;});
