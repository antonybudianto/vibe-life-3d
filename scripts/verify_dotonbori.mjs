import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import ts from 'typescript';
import * as THREE from 'three';
function moduleFrom(path, require = () => ({})) {
  const ctx = {exports:{},require,Math,Set,Map,Intl,Date};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,ctx);
  return ctx.exports;
}
const physics=moduleFrom('lib/game/physics.ts');
const {World}=moduleFrom('lib/game/world.ts', n => n==='three'?THREE:n==='./physics'?physics:n.endsWith('.json')?{default:JSON.parse(fs.readFileSync('lib/game/'+n.slice(2),'utf8'))}:{});
const data=JSON.parse(fs.readFileSync('public/models/dotonbori.json','utf8'));
function world(x,z,yaw=0) {
  return Object.assign(Object.create(World.prototype),{data,character:{},paused:false,status:{loading:false,error:null},keys:new Set(),joystick:{x:0,y:0},player:new THREE.Vector3(x,physics.groundHeight(x,z,data.surfaces),z),travel:'walk',running:false,velocity:0,verticalVelocity:0,heading:Math.PI,yaw,cruises:[]});
}
const spawn=world(data.spawn[0],data.spawn[2]);
spawn.step(1/60);assert.equal(spawn.player.x,data.spawn[0]);assert.equal(spawn.player.z,data.spawn[2]);
// Actual World.step crosses each mesh-backed bridge in both directions.
for (const z of [-48,0,48]) for (const direction of [-1,1]) {
  const w=world(-direction*17,z,-direction*Math.PI/2);w.keys.add('KeyW');
  let maxY=0;
  for(let i=0;i<1020;i++) {
    const lastY=w.player.y;w.step(1/60);maxY=Math.max(maxY,w.player.y);
    assert.ok(Math.abs(w.player.y-lastY)<.025,'Approach elevation is continuous, without floating or snapping');
    assert.ok(Math.abs(w.player.y-physics.groundHeight(w.player.x,z,data.surfaces))<1e-6,'Feet follow the authored deck');
  }
  assert.ok(w.player.x*direction>17,'Avatar reaches the opposite promenade');
  assert.equal(w.player.y,0,'Avatar descends to ground at the far end');
  assert.ok(Math.abs(maxY-(z===0?2.4:1.8))<1e-6,'Avatar reaches the raised deck height');
}
const jumper=world(0,0);jumper.jump();
let apex=jumper.player.y;
for(let i=0;i<100;i++){jumper.step(1/60);apex=Math.max(apex,jumper.player.y);}
assert.ok(apex>3.25,'Jump starts from bridge deck');assert.equal(jumper.player.y,2.4,'Jump lands back on the deck');
jumper.jump();assert.equal(jumper.verticalVelocity,5.3,'Jump can be repeated on elevated ground');
jumper.step(1/60);const airVelocity=jumper.verticalVelocity;jumper.jump();assert.equal(jumper.verticalVelocity,airVelocity,'No mid-air jump');
for (const z of [-62,-30,23,63]) {
  const w=world(11,z,Math.PI/2);w.keys.add('KeyW');
  for(let i=0;i<400;i++)w.step(1/60);
  assert.ok(w.player.x>8.6,'Canal rail prevents walking into water');
}
const edge=world(0,0,Math.PI);edge.keys.add('KeyW');
for(let i=0;i<300;i++)edge.step(1/60);
assert.ok(edge.player.z<3.5,'Bridge side railing blocks canal access');assert.ok(Math.abs(edge.player.y-2.4)<1e-6);
assert.ok(Math.abs(edge.player.x)<.01,'Touching a long railing does not teleport the avatar sideways');
const paused=world(0,0);paused.keys.add('KeyW');paused.paused=true;paused.step(1);assert.equal(paused.player.z,0);
// Exercise actual time application repeatedly, including returning to daytime.
const lit=world(0,0), material=new THREE.MeshStandardMaterial({emissive:0xff6020,emissiveIntensity:2});
material.userData.baseEmission=2;material.userData.bakedLightmapScale=4;material.lightMap=new THREE.Texture();
Object.assign(lit,{scene:new THREE.Scene(),sky:{setTime:()=>{}},hemi:new THREE.HemisphereLight(),sun:new THREE.DirectionalLight(),fill:new THREE.DirectionalLight(),renderer:{},nightLights:[],lastPhase:''});
lit.scene.fog=new THREE.Fog(0,1,200);lit.scene.add(new THREE.Mesh(new THREE.BoxGeometry(),material));
for(const phase of ['day','evening','night','day']) {
  lit.time=phase;lit.applyTime();
  const palette=JSON.parse(fs.readFileSync('lib/game/dotonbori-lighting.json','utf8'))[phase];
  assert.equal(material.emissiveIntensity,2*palette.emission);
  assert.equal(material.lightMapIntensity,4*palette.emission);
  assert.equal(lit.sun.intensity,palette.power);
}
const b=fs.readFileSync('public/models/dotonbori.glb');assert.equal(b.toString('utf8',0,4),'glTF');
const gltf=JSON.parse(b.toString('utf8',20,20+b.readUInt32LE(12)));
assert.ok(b.length<6e6,'Map stays below 6 MB');
assert.equal(gltf.nodes.filter(n=>n.extras?.cruise).length,2);
assert.ok(gltf.nodes.some(n=>n.name==='Ebisubashi deck'));
assert.ok(gltf.nodes.some(n=>n.name==='Dotonbori canal water'));
assert.equal(gltf.materials.filter(m=>m.extras?.bakedLightmap).length,3,'Every walkable surface batch has its completed light bake');
assert.ok(gltf.materials.filter(m=>m.extras?.bake_mode).length>25,'Completed detail bakes must be in the delivered GLB');
const bake=JSON.parse(fs.readFileSync('assets/bakes/dotonbori.json','utf8'));
assert.equal(bake.engine,'CYCLES');assert.ok(bake.vertexBakes.length>30);assert.ok(bake.aoStd>.03);assert.ok(bake.lightmapMaximum>.1);
assert.ok(bake.vertexBakes.every(v=>v.minimum>.001&&v.corners>0));
for(const mesh of gltf.meshes) for(const p of mesh.primitives) {
  const m=gltf.materials[p.material];
  if(m.extras?.bake_mode)assert.ok(p.attributes.COLOR_0!==undefined,'Cycles shading is exported');
  if(m.extras?.bakedLightmap) {
    assert.ok(p.attributes.TEXCOORD_1!==undefined,'Lightmaps retain UV1');
    assert.equal(m.occlusionTexture.texCoord,1);
    assert.ok(fs.existsSync('public'+m.extras.bakedLightmap));
  }
}
console.log(`PASS: six bridge traversals, ramp continuity, elevated jump/landing, canal and bridge barriers, pause, day/evening/night cycling, Cycles bakes and GLB structure (${(b.length/1e6).toFixed(2)} MB).`);
