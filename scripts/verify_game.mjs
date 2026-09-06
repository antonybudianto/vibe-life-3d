import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import ts from 'typescript';
import zlib from 'node:zlib';

const source = fs.readFileSync('lib/game/physics.ts', 'utf8');
const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText;
const context = { exports: {}, Intl, Date, Math, Number, String }; vm.runInNewContext(compiled, context);
const { moveWithCollision: move, resolveTime } = context.exports;
const bounds = [-20,20,-20,20], wall = [{ x: 5, z: 0, halfX: 1, halfZ: 8 }];
let p = { x: 0, z: 0 };
for (let i=0;i<1000;i++) p = move(p.x,p.z,.1,0,.32,wall,bounds);
assert.ok(p.x <= 3.681 && p.x >= 3.67, 'Walking stops at a building');
const slide = move(p.x,p.z,.1,.1,.32,wall,bounds); assert.ok(slide.z>p.z && slide.x<=3.681,'Character slides along walls');
const car = move(3.8,0,0,0,1.7,wall,bounds);assert.ok(car.x<=2.301,'A car entering near a wall gets pushed out');
const edge = move(19,19,3,3,1.7,[],bounds);assert.equal(edge.x,18.3);assert.equal(edge.z,18.3);
for (const [iso,phase,next,blend,clock] of [
  ['2026-09-06T03:00:00Z','day','day',0,'12:00'],
  ['2026-09-06T08:00:00Z','day','evening',.5,'17:00'],
  ['2026-09-06T10:00:00Z','evening','night',.5,'19:00'],
  ['2026-09-06T15:00:00Z','night','night',0,'00:00'],
  ['2026-09-05T21:00:00Z','night','day',.5,'06:00'],
]) { const t=resolveTime('live',new Date(iso));assert.equal(t.phase,phase);assert.equal(t.next,next);assert.equal(t.blend,blend);assert.equal(t.clock,clock); }
assert.equal(resolveTime('evening',new Date()).clock,'17:30');

const report = [];
for (const name of ['character','crossing','park','car','motorcycle']) {
  const buf=fs.readFileSync(`public/models/${name}.glb`);
  assert.equal(buf.toString('utf8',0,4),'glTF');assert.equal(buf.readUInt32LE(8),buf.length);
  const json=JSON.parse(buf.toString('utf8',20,20+buf.readUInt32LE(12)));
  assert.ok(json.meshes.length>0);
  for (const node of json.nodes) if(node.translation) assert.ok(node.translation.every(Number.isFinite));
  if(name==='character') for(const joint of ['Character','Arm_L','Arm_R','Leg_L','Leg_R']) assert.ok(json.nodes.some(n=>n.name===joint),`${joint} preserved`);
  if(['crossing','park'].includes(name)) {
    const m=JSON.parse(fs.readFileSync(`public/models/${name}.json`,'utf8'));
    assert.ok(m.colliders.length>0);
    const resolved=move(m.spawn[0],m.spawn[2],0,0,.32,m.colliders,m.bounds);
    assert.equal(resolved.x,m.spawn[0]);assert.equal(resolved.z,m.spawn[2]);
  }
  report.push({ name, bytes:buf.length, gzipBytes:zlib.gzipSync(buf).length, meshes:json.meshes.length, triangles:json.meshes.reduce((n,m)=>n+m.primitives.reduce((s,p)=>s+json.accessors[p.indices].count/3,0),0), compressed:!!json.extensionsUsed?.includes('KHR_draco_mesh_compression') });
}
fs.mkdirSync('work',{recursive:true});fs.writeFileSync('work/asset-report.json',JSON.stringify(report,null,2));
console.log('PASS: collisions, wall sliding, vehicle clearance, map bounds, Tokyo time transitions, glTF structure, animation pivots, safe map spawns.');
console.table(report);
