// Lightweight DOM adapter test: no browser or graphical processes required.
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
class Element {
  constructor(tag){this.tag=tag;this.children=[];this.value='';this.open=true;}
  append(...nodes){this.children.push(...nodes);}
  querySelector(tag){return this.children.find(child=>child.tag===tag);}
  focus(){}
}
let form, confirmed=false, created=0, previewed=0, dialog={open:true}, status, browseResult={cancelled:true};
const calls=[];
const context={
  window:{LanctlI18n:{t:key=>key}},
  document:{createElement:tag=>new Element(tag),querySelector:selector=>selector==='#dialog'?dialog:new Element('p')},
  field:(label,name,value)=>{const node=new Element('label'),input=new Element('input');input.name=name;input.value=value;node.append(input);return node;},
  showForm:(title,nodes,submit,label)=>{form={title,nodes,submit,label};},
  message:text=>{status=text;},
  confirmAction:async text=>{assert(text.includes('/tmp/target.desktop'));return confirmed;},
  call:async(method,...args)=>{
    calls.push([method,...args]);
    if(method==='shortcut_options')return {supported:true,launchers:['lanctl','lanip'],modes:['cli','tui','gui'],guiAvailable:false,distribution:'/opt/lanctl'};
    if(method==='preview_shortcut'){previewed++;return {token:'token',executable:'/opt/lanctl/lanctl',arguments:['--tui'],workingDirectory:'/opt/lanctl',icon:'',target:'/tmp/target.desktop'};}
    if(method==='create_shortcut'){assert.equal(args[0],'token');created++;return {message:'created'};}
    if(method==='select_shortcut_path')return browseResult;
    throw Error(method);
  },
};
vm.runInNewContext(fs.readFileSync(process.argv[2],'utf8'),context);
(async()=>{
  await context.window.openShortcutForm();
  assert.equal(form.label,'LANCTL.SHORTCUT.PREVIEW_BUTTON');
  const mode=form.nodes[1].querySelector('select');
  assert.deepEqual(mode.children.map(x=>x.value),['cli','tui']);
  const distribution=form.nodes[3],input=distribution.querySelector('input');
  await distribution.querySelector('button').onclick();
  assert.equal(input.value,'/opt/lanctl');
  browseResult={cancelled:false,path:'/tmp/distro'};
  await distribution.querySelector('button').onclick();
  assert.equal(input.value,'/tmp/distro');
  await form.submit({mode:'tui'});
  assert.equal(previewed,1);assert.equal(created,0);
  confirmed=true;await form.submit({mode:'tui'});
  assert.equal(created,1);assert.equal(status,'created');
  dialog.open=false;await form.submit({mode:'tui'});
  assert.equal(created,1);
})().catch(error=>{console.error(error);process.exitCode=1;});
