import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import ts from 'typescript';
import * as THREE from 'three';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {Reflector} from 'three/addons/objects/Reflector.js';
function moduleFrom(path, require = () => ({})) {
  const ctx = {exports:{},require,Math,Set,Map,Intl,Date};
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path,'utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,ctx);
  return ctx.exports;
}
const physics=moduleFrom('lib/game/physics.ts');
const {findCanalSurface,CanalWater}=moduleFrom('lib/game/canal-water.ts',n=>n==='three'?THREE:{Reflector});
// Reproduce the actual GLTFLoader name transformation that previously disabled water.
const bytes=Buffer.from(new Float32Array([-1,0,-1,1,0,-1,0,0,1]).buffer);
globalThis.ProgressEvent ??= class ProgressEvent extends Event { constructor(type,init) { super(type); Object.assign(this,init); } };
const imported=await new GLTFLoader().parseAsync(JSON.stringify({
  asset:{version:'2.0'},scene:0,scenes:[{nodes:[0]}],nodes:[{name:'Dotonbori canal water',mesh:0}],
  meshes:[{primitives:[{attributes:{POSITION:0},material:0}]}],materials:[{extras:{water_surface:true}}],
  buffers:[{uri:'data:application/octet-stream;base64,'+bytes.toString('base64'),byteLength:bytes.length}],
  bufferViews:[{buffer:0,byteLength:bytes.length}],accessors:[{bufferView:0,componentType:5126,count:3,type:'VEC3',min:[-1,0,-1],max:[1,0,1]}]
}), '');
assert.equal(imported.scene.getObjectByName('Dotonbori canal water'),undefined,'Loader changes the authored name');
const waterSource=findCanalSurface(imported.scene);
assert.ok(waterSource instanceof THREE.Mesh,'Water is discovered by its exported role');
imported.scene.updateMatrixWorld(true);
const water=new CanalWater(waterSource,new THREE.Texture());
assert.equal(waterSource.visible,false,'The non-reflective source is replaced');
assert.equal(water.mesh.getRenderTarget().texture.type,THREE.HalfFloatType,'Reflections retain HDR sign colors');
water.dispose();assert.equal(waterSource.visible,true);
const {World}=moduleFrom('lib/game/world.ts', n => n==='three'?THREE:n==='./physics'?physics:n.endsWith('.json')?{default:JSON.parse(fs.readFileSync('lib/game/'+n.slice(2),'utf8'))}:{});
const data=JSON.parse(fs.readFileSync('public/models/dotonbori.json','utf8'));
function world(x,z,yaw=0) {
  return Object.assign(Object.create(World.prototype),{data,character:{},paused:false,status:{loading:false,error:null},keys:new Set(),joystick:{x:0,y:0},player:new THREE.Vector3(x,physics.groundHeight(x,z,data.surfaces),z),travel:'walk',running:false,velocity:0,verticalVelocity:0,heading:Math.PI,yaw,cruises:[]});
}
const spawn=world(data.spawn[0],data.spawn[2]);
spawn.step(1/60);assert.equal(spawn.player.x,data.spawn[0]);assert.equal(spawn.player.z,data.spawn[2]);
function walkTo(w,x,z) {
  let maxY=w.player.y;
  for(let i=0;i<1800;i++) {
    const dx=x-w.player.x,dz=z-w.player.z,d=Math.hypot(dx,dz);
    if(d<.02)return maxY;
    const speed=Math.min(1,d/(2.1/60));
    w.joystick.x=dx/d*speed;w.joystick.y=dz/d*speed;
    const lastY=w.player.y;w.step(1/60);maxY=Math.max(maxY,w.player.y);
    assert.ok(Math.abs(w.player.y-lastY)<.145,'Each real riser stays below the avatar step limit');
    assert.ok(Math.abs(w.player.y-physics.groundHeight(w.player.x,w.player.z,data.surfaces))<1e-6,'Feet contact the authored treads and deck');
  }
  assert.fail(`Blocked route to ${x},${z} at ${w.player.toArray()}`);
}
// All twelve flights: approach along the river, turn across the deck and descend.
for (const z of [-48,0,48]) for (const side of [-1,1]) for(const end of [-1,1]) {
  const extent=z===0?10.6:8.8;
  const w=world(side*11,z+end*(extent+.5));
  walkTo(w,side*11,z);
  assert.ok(Math.abs(w.player.y-(z===0?2.55:1.8))<.01);
  const highest=walkTo(w,-side*11,z);
  assert.ok(Math.abs(highest-(z===0?2.79:1.94))<.002,'Cross the crowned bridge deck');
  walkTo(w,-side*11,z-end*(extent+.5));
  assert.equal(w.player.y,0,'Descend to the opposite promenade');
}
const sideEntry=world(15,0,Math.PI/2);sideEntry.keys.add('KeyW');
for(let i=0;i<150;i++)sideEntry.step(1/60);
assert.equal(sideEntry.player.y,0,'Raised landings cannot be climbed from their sides');
assert.ok(sideEntry.player.x>13.5);
assert.equal(physics.canStepTo(0,0,2.55),false);
const jumper=world(0,0);jumper.jump();
let apex=jumper.player.y;
for(let i=0;i<100;i++){jumper.step(1/60);apex=Math.max(apex,jumper.player.y);}
assert.ok(apex>3.6,'Jump starts from bridge deck');assert.equal(jumper.player.y,2.79,'Jump lands back on the deck');
jumper.jump();assert.equal(jumper.verticalVelocity,5.3,'Jump can be repeated on elevated ground');
jumper.step(1/60);const airVelocity=jumper.verticalVelocity;jumper.jump();assert.equal(jumper.verticalVelocity,airVelocity,'No mid-air jump');
for (const z of [-62,-30,23,63]) {
  const w=world(11,z,Math.PI/2);w.keys.add('KeyW');
  for(let i=0;i<400;i++)w.step(1/60);
  assert.ok(w.player.x>8.6,'Canal rail prevents walking into water');
}
const edge=world(0,0,Math.PI);edge.keys.add('KeyW');
for(let i=0;i<300;i++)edge.step(1/60);
assert.ok(edge.player.z<3.5,'Bridge side railing blocks canal access');assert.ok(Math.abs(edge.player.y-2.79)<1e-6);
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
assert.ok(b.length<9e6,'Detailed foliage and signs stay within the 9 MB map budget');
assert.equal(gltf.nodes.filter(n=>n.extras?.cruise).length,2);
assert.ok(gltf.nodes.some(n=>n.name==='Ebisubashi deck'));
assert.ok(gltf.nodes.some(n=>n.name==='Dotonbori canal water'));
assert.equal(gltf.materials.filter(m=>m.extras?.bakedLightmap).length,3,'Every walkable surface batch has its completed light bake');
assert.ok(gltf.materials.filter(m=>m.extras?.bake_mode).length>25,'Completed detail bakes must be in the delivered GLB');
const bake=JSON.parse(fs.readFileSync('assets/bakes/dotonbori.json','utf8'));
assert.equal(bake.engine,'CYCLES');assert.ok(bake.vertexBakes.length>30);assert.ok(bake.aoStd>.03);assert.ok(bake.lightmapMaximum>.1);
assert.ok(bake.vertexBakes.every(v=>v.minimum>.001&&v.corners>0));
assert.equal(bake.waterNormalEngine,'CYCLES');assert.ok(bake.waterNormalStd>.03);
assert.ok(fs.existsSync('public'+bake.waterNormal));
for(const mesh of gltf.meshes) for(const p of mesh.primitives) {
  const m=gltf.materials[p.material];
  if(m.extras?.bake_mode)assert.ok(p.attributes.COLOR_0!==undefined,'Cycles shading is exported');
  if(m.extras?.bakedLightmap) {
    assert.ok(p.attributes.TEXCOORD_1!==undefined,'Lightmaps retain UV1');
    assert.equal(m.occlusionTexture.texCoord,1);
    assert.ok(fs.existsSync('public'+m.extras.bakedLightmap));
  }
}
console.log(`PASS: GLTF water discovery and HDR reflection hookup; twelve stair routes with crossings and descents; raised landing barriers, elevated jumps, canal/bridge rails, pause, day/evening/night cycling and Cycles lighting/normal bakes (${(b.length/1e6).toFixed(2)} MB).`);
