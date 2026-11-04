// Behavioral DOM adapter: no browser/native focus certification.
const assert = require('node:assert/strict');
const fs = require('node:fs');
const vm = require('node:vm');
const path = require('node:path');
class Element {
  constructor() { this.value=''; this.open=false; this.hidden=false; this.children=[]; this.listeners={}; this.nodes=new Map(); }
  querySelector(selector) {
    if(selector==='textarea') return this.querySelector('description');
    if(selector==='[name="reportSession"]') return this.querySelector('source');
    if(!this.nodes.has(selector)) this.nodes.set(selector,new Element());
    return this.nodes.get(selector);
  }
  querySelectorAll(selector) {
    if(selector==='textarea') return ['description','steps','expected'].map(name=>this.querySelector(name));
    return ['export','github','copy'].map(name=>this.querySelector(name));
  }
  addEventListener(name,fn) { this.listeners[name]=fn; }
  replaceChildren(...children) { this.children=children; }
  append() {}
  showModal() { assert.equal(this.open,false); this.open=true; }
  close() { this.open=false; }
  focus() { this.focused=true; }
}
async function main() {
  const listeners={}, report=new Element(), calls=[], intervals=[];
  const state={launcher:'lanmon'};
  const context={
    state, console, Intl, Promise, setTimeout, render:()=>{},
    setInterval:(_callback,delay)=>{intervals.push(delay);return 0;},
    Option:function(text,value) { this.text=text; this.value=value; },
    $:()=>new Element(),
    call:async (name)=>{ calls.push(name); if(name==='monitor_view') return {view:'report',sourceSession:'initial-source'}; assert.equal(name,'monitor_activity'); await Promise.resolve(); return {sessions:['source-A','source-B']}; },
    document:{createElement:()=>report,body:{append(){}},addEventListener(){}},
    window:{
      pywebview:{api:{monitor_view(){}}},
      addEventListener:(name,fn)=>{listeners[name]=fn;},
      LanctlI18n:{code:'en',t:key=>key,bindAttribute(){},bindText:(node,key)=>{node.textContent=key;}},
    },
  };
  vm.createContext(context);
  vm.runInContext(fs.readFileSync(path.join(__dirname,'../../gui/monitor-support.js'),'utf8'),context);
  const deliver=detail=>listeners['lanctl-monitor-view']({detail});
  await listeners.pywebviewready();
  assert.equal(report.open,true);
  assert.equal(report.querySelector('source').value,'initial-source');
  assert.deepEqual(intervals,[1500]);
  report.close();
  // Simultaneous requests must preserve the first form/source rather than race.
  await Promise.all([
    deliver({view:'report',sourceSession:'source-A'}),
    deliver({view:'report',sourceSession:'source-B'}),
  ]);
  assert.equal(report.open,true);
  assert.equal(report.querySelector('source').value,'source-A');
  assert.equal(calls.filter(name=>name==='monitor_activity').length,2);
  report.querySelector('description').value='Keep my draft';
  report.close();
  await deliver({view:'report',sourceSession:'source-B'});
  assert.equal(report.open,true);
  assert.equal(report.querySelector('description').value,'Keep my draft');
  assert.equal(report.querySelector('source').value,'source-A');
  assert.equal(report.querySelector('.report-state').textContent,'LANCTL.MONITOR.VIEW.DRAFT_PRESERVED');
  assert.equal(report.querySelector('description').focused,true);
  const count=calls.length;
  await deliver({view:'arbitrary',sourceSession:'source-B'});
  assert.equal(calls.length,count);
  console.log('monitor request routing, queue and draft preservation: passed');
}
main().catch(error=>{console.error(error);process.exitCode=1;});
