const fs=require('fs'),vm=require('vm'),assert=require('assert');
const source=fs.readFileSync(process.argv[2],'utf8');
const context={structuredClone,physicalSize:n=>n.size || {w:240,h:130}};
vm.createContext(context);
vm.runInContext(source.slice(source.indexOf('function physicalPack('),source.indexOf('wireLayout = function (nodes)')),context);
function layout(nodes,edges){context.nodes=nodes;context.edges=edges;return Array.from(vm.runInContext('physicalPack(nodes,edges)',context));}
function check(nodes,edges){
 const before=JSON.stringify({nodes,edges}), positions=new Map(layout(nodes,edges));
 assert.equal(positions.size,nodes.length);
 assert.equal(JSON.stringify({nodes,edges}),before);
 for(let i=0;i<nodes.length;i++)for(let j=i+1;j<nodes.length;j++){
  const a=positions.get(nodes[i].id),b=positions.get(nodes[j].id),sa=context.physicalSize(nodes[i]),sb=context.physicalSize(nodes[j]);
  assert(a.x+sa.w<=b.x || b.x+sb.w<=a.x || a.y+sa.h<=b.y || b.y+sb.h<=a.y,'overlapping cards');
 }
 const reversed=new Map(layout([...nodes].reverse(),[...edges].reverse()));
 for(const [id,p] of positions)assert.deepEqual(p,reversed.get(id));
 return positions;
}
const nodes=Array.from({length:18},(_,i)=>({id:String(i).padStart(3,'0'),data:{type:i===0?'device.router':'device.switch'},size:{w:240+(i%4)*60,h:100+(i%3)*40}}));
const edges=[];
for(let i=1;i<14;i++)edges.push({a:{device:nodes[Math.floor((i-1)/3)].id},b:{device:nodes[i].id}});
edges.push({a:{device:'004'},b:{device:'007'}},{a:{device:'003'},b:{device:'003'}},{a:{device:'missing'},b:{device:'001'}});
check(nodes,edges);check([],[]);check([nodes[0]],[]);
const large=Array.from({length:1000},(_,i)=>({id:'N'+String(i).padStart(4,'0'),data:{}}));
const links=large.slice(1).map((n,i)=>({a:{device:large[Math.floor(i/4)].id},b:{device:n.id}}));
const start=Date.now();check(large,links);assert(Date.now()-start<5000,'layout exceeded its small fixture budget');
console.log('layout: deterministic, no overlaps, cycles/disconnected/1000 nodes checked');
const branchNodes=['R','A','B','a1','a2','z1','z2'].map(id=>({id,data:{type:id==='R'?'device.router':'device.switch'}}));
const branchEdges=[['R','A'],['R','B'],['A','z1'],['A','z2'],['B','a1'],['B','a2']].map(([a,b])=>({a:{device:a},b:{device:b}}));
const branch=check(branchNodes,branchEdges);
assert((branch.get('A').x-branch.get('B').x)*(branch.get('z1').x-branch.get('a1').x)>0,'crossed child branches');
const boxes=[{id:'A',x:0,y:0,w:300,h:200},{id:'B',x:350,y:0,w:300,h:200},{id:'C',x:700,y:0,w:300,h:200},{id:'D',x:350,y:500,w:300,h:200}];
const points={a:{x:30,y:70},b:{x:380,y:70},c:{x:730,y:70},d:{x:380,y:570}};
const members={a:'A',b:'B',c:'C',d:'D'},sizes=Object.fromEntries(Object.keys(points).map(id=>[id,{w:100,h:60}]));
function resize(regions,positions,id,side,delta){Object.assign(context,{regions,positions,members,sizes,id,side,delta});return vm.runInContext('physicalResizeRegions(regions,positions,members,id,side,delta,sizes)',context);}
const initial=JSON.stringify({boxes,points});
const pushed=resize(boxes,points,'A','e',250);
assert.equal(pushed.regions[0].w,550);assert.equal(pushed.regions[1].x,590);assert.equal(pushed.regions[2].x,930);
assert.deepEqual(pushed.positions.a,points.a);assert.deepEqual(pushed.positions.d,points.d);
assert.equal(pushed.positions.b.x-points.b.x,pushed.regions[1].x-boxes[1].x);
const left=resize(boxes,points,'C','w',-500);assert(left.positions.a.x<points.a.x&&left.positions.b.x<points.b.x);assert.deepEqual(left.positions.c,points.c);
const shrunk=resize(boxes,points,'A','e',-1000);assert(shrunk.regions[0].w>=155);assert.deepEqual(shrunk.positions,points);
const transposed=boxes.map(r=>({...r,x:r.y,y:r.x,w:r.h,h:r.w}));
const transposedPoints=Object.fromEntries(Object.entries(points).map(([id,p])=>[id,{x:p.y,y:p.x}]));
for(const value of Object.values(sizes)){value.w=60;value.h=100;}
const down=resize(transposed,transposedPoints,'A','s',250);assert(down.positions.b.y>points.b.x&&down.positions.c.y>points.c.x);assert.deepEqual(down.positions.a,transposedPoints.a);
const up=resize(transposed,transposedPoints,'C','n',-500);assert(up.positions.a.y<points.a.x&&up.positions.b.y<points.b.x);assert.deepEqual(up.positions.c,transposedPoints.c);
assert.equal(JSON.stringify({boxes,points}),initial);
console.log('resize: four directions, chain push, fixed own nodes, shrink limits and unaffected blocks checked');
