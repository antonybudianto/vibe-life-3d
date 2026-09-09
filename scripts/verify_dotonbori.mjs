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
// Curved bridge slices and longitudinal ramps must agree with rendered geometry.
const tapered={minX:0,maxX:2,minZ:-2,maxZ:2,endMinZ:-4,endMaxZ:4,height:2,endHeight:3};
assert.equal(physics.groundHeight(1,2.8,[tapered]),2.5);
assert.equal(physics.groundHeight(1,3.2,[tapered]),0,'No invisible floor beyond a curved deck edge');
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
// Exercise the actual reflector camera: bridge undersides are seen from below
// the water plane, and the reflection is not a screen-space copy of the deck.
const mirrorScene=new THREE.Scene();mirrorScene.add(water.mesh);mirrorScene.updateMatrixWorld(true);
const mirrorCamera=new THREE.PerspectiveCamera(55,1.4,.12,240);
mirrorCamera.position.set(4,6,13);mirrorCamera.lookAt(0,1,0);mirrorCamera.updateMatrixWorld(true);
let reflectedY;
const renderer={xr:{enabled:false},shadowMap:{autoUpdate:true},state:{buffers:{depth:{setMask(){}}}},autoClear:true,getRenderTarget(){return null;},setRenderTarget(){},render(_scene,camera){reflectedY=camera.position.y;}};
water.mesh.onBeforeRender(renderer,mirrorScene,mirrorCamera);
assert.ok(Math.abs(reflectedY-(2*-1.43-6))<1e-6,'Camera mirrors at the actual canal level');
assert.equal(renderer.shadowMap.autoUpdate,true,'Reflection restores renderer state');
water.dispose();assert.equal(waterSource.visible,true);
const {World,CRUISE_CYCLE}=moduleFrom('lib/game/world.ts', n => n==='three'?THREE:n==='./physics'?physics:n.endsWith('.json')?{default:JSON.parse(fs.readFileSync('lib/game/'+n.slice(2),'utf8'))}:{});
const data=JSON.parse(fs.readFileSync('public/models/dotonbori.json','utf8'));
const {CanalPedestrianSimulation}=moduleFrom('lib/game/canal-pedestrians.ts',()=>physics);
const crowd=new CanalPedestrianSimulation(data);
const sawSightseeing=new Set(),resumed=new Set(),stairEntrances=new Set(),stopKinds=new Set();
const frozen=JSON.stringify(crowd.walkers);crowd.update(0,{x:12,y:0,z:18,radius:.32});assert.equal(JSON.stringify(crowd.walkers),frozen,'Paused crowd does not advance');
for(let tick=0;tick<300*30;tick++) {
  crowd.update(1/30,{x:12,y:0,z:18,radius:.32});
  if(tick%15)continue;
  crowd.walkers.forEach((w,i)=>{
    assert.ok(crowd.navigation.walkable(w,w.radius+.02),'Walkers stay on clear navigation surfaces');
    assert.ok(Math.abs(w.y-physics.groundHeight(w.x,w.z,data.surfaces))<1e-6,'Feet match authored treads and bridge crowns');
    if(w.activity==='sightseeing') {
      sawSightseeing.add(i);
      const spot=crowd.navigation.spots[w.spot];
      stopKinds.add(spot.kind);
      if(spot.kind==='bridge')assert.ok(w.y>1.7&&Math.abs(w.x)<6,'Bridge photo stops remain on the railings');
      else assert.ok(w.y===0&&Math.abs(w.x)>9,'Shop queues and bank photo stops stay on the promenade');
      assert.ok(Math.hypot(w.x-crowd.navigation.nodes[spot.node].x,w.z-crowd.navigation.nodes[spot.node].z)<.2,'Visitors reach their reserved stop');
    } else if(sawSightseeing.has(i))resumed.add(i);
    for(const z of [-48,0,48])if(Math.abs(w.x)>8.8&&Math.abs(w.x)<13.1&&Math.abs(w.z-z)>4&&w.y>.15)stairEntrances.add(`${z},${Math.sign(w.x)},${Math.sign(w.z-z)}`);
  });
}
assert.equal(crowd.walkers.length,36,'Static visitors have been replaced with the live crowd');
assert.deepEqual([...stopKinds].sort(),['bridge','photo','shop'],'Visitors actually use bridge views, canal photo groups and shop stops');
assert.ok(crowd.walkers.every(w=>w.travelled>100&&w.crossings>0),'Every visitor walks and reaches the opposite bank');
assert.equal(stairEntrances.size,12,'Live routes use all twelve stair entrances');
assert.ok(sawSightseeing.size>=30&&resumed.size>=28,'Visitors pause at railings and resume walking');
console.log(`PASS: 36 animated visitors, all 12 stairs, ${crowd.walkers.reduce((n,w)=>n+w.crossings,0)} bank crossings, ${resumed.size} resumed sightseeing stops in five minutes.`);
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
assert.ok(edge.player.z>7.9&&edge.player.z<8.3,'Central opening reaches the perimeter ramp and its outer railing blocks canal access');assert.ok(Math.abs(edge.player.y-2.79)<1e-6);
assert.ok(Math.abs(edge.player.x)<.01,'Touching a long railing does not teleport the avatar sideways');
// Stairs and the outer ramp are independent, usable routes in both directions.
const mainTreads=data.surfaces.filter(s=>s.minX>10&&s.maxX<14&&s.minZ>3.799&&s.maxZ<10.61);
assert.equal(mainTreads.length,20,'Main bank approach has twenty actual stair treads');
assert.ok(mainTreads.every(s=>s.endHeight===undefined&&s.endHeightZ===undefined),'Bank stairs have level treads');
for(const side of [-1,1])for(const end of [-1,1]) {
  const w=world(0,0),points=[[0,end*7.725]];
  for(let i=1;i<=34;i++) { const x=i*.25;points.push([side*x,end*(Math.max(3.8,Math.sqrt(Math.max(0,6.9**2-x*x)))+.825)]); }
  points.push([side*9.4,end*4.625],[side*9.4,end*8]);
  for(const [x,z] of points)walkTo(w,x,z);
  assert.equal(w.player.y,0,'Perimeter ramp exits beside the stairs onto the riverwalk');
  for(const [x,z] of points.slice().reverse())walkTo(w,x,z);
  walkTo(w,0,0);assert.equal(w.player.y,2.79,'Separate ramp returns to the plaza through its central opening');
}
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
const glicoPanel=gltf.meshes.find(m=>m.name==='Dotonbori artwork Glico north');
const glicoBounds=gltf.accessors[glicoPanel.primitives[0].attributes.POSITION];
assert.ok(Math.abs(glicoBounds.max[1]-glicoBounds.min[1]-20)<.01&&Math.abs(glicoBounds.max[2]-glicoBounds.min[2]-10.38)<.01,'Exported Glico panel matches the official 20 x 10.38 m dimensions');
// Seven navigable bridges and the larger shared AO atlas add about 1 MB.
assert.ok(b.length<10.5e6,'The expanded seven-bridge district stays within 10.5 MB');
assert.equal(gltf.nodes.filter(n=>n.extras?.cruise).length,2);
assert.ok(gltf.nodes.some(n=>n.name==='Ebisubashi deck'));
assert.ok(gltf.nodes.some(n=>n.name==='Dotonbori canal water'));
assert.ok(gltf.nodes.some(n=>n.name==='Bridge solid soffits'),'Bridge undersides are present for reflection cameras');
assert.ok(gltf.nodes.some(n=>n.name==='Bridge support piers'),'Bridge has actual stone supports');
const glico=data.architecture.find(p=>p.landmark==='glico'),donki=data.architecture.find(p=>p.landmark==='wheel');
assert.equal(donki.side,1,'Don Quijote occupies the north bank');
assert.equal(glico.side,-1,'Glico occupies the opposite south bank');
assert.ok(donki.center<0&&glico.center>0,'Don Quijote is east of Ebisubashi; Glico is west (game +Z is east)');
const asahi=data.architecture.find(p=>p.landmark==='asahi');
assert.ok(data.architecture.some(p=>p.landmark==='tsutaya'&&p.side===-1&&p.center<0),'TSUTAYA anchors the south-bank retail block');
assert.ok(data.architecture.some(p=>p.landmark==='glass-retail'&&p.side===1),'Contrasting glazed retail shell is across the canal');
assert.ok(!data.architecture.some(p=>p.landmark==='fugu'||p.landmark==='kani'),'Retired or street-facing attractions are not canal-front parcels');
assert.ok(gltf.nodes.some(n=>n.name==='Ebisu Tower 32 gondolas'),'The full wheel cabin assembly is exported');
assert.equal(asahi.side,glico.side,'Asahi shares Glico’s bank in the supplied photograph');
assert.ok(asahi.center<0,'Asahi occupies the corner east of the main bridge');
assert.ok(!gltf.nodes.some(n=>n.name.startsWith('Cruise Glazing')),'The photo reference requires open passenger decks');
// Use exported mesh bounds and the actual World.step cruise motion, so a longer
// replacement hull cannot silently pass through a bridge or retaining wall.
function vesselBounds(index) {
  const bounds=new THREE.Box3(),parts=[];
  function visit(id,parent) {
    const node=gltf.nodes[id],local=node.matrix?new THREE.Matrix4().fromArray(node.matrix):new THREE.Matrix4().compose(new THREE.Vector3().fromArray(node.translation??[0,0,0]),new THREE.Quaternion().fromArray(node.rotation??[0,0,0,1]),new THREE.Vector3().fromArray(node.scale??[1,1,1]));
    const matrix=parent.clone().multiply(local);
    if(node.mesh!==undefined)for(const primitive of gltf.meshes[node.mesh].primitives){
      const {min,max}=gltf.accessors[primitive.attributes.POSITION];
      const part=new THREE.Box3();
      for(const x of [min[0],max[0]])for(const y of [min[1],max[1]])for(const z of [min[2],max[2]])part.expandByPoint(new THREE.Vector3(x,y,z).applyMatrix4(matrix));
      parts.push(part);bounds.union(part);
    }
    for(const child of node.children??[])visit(child,matrix);
  }
  visit(index,new THREE.Matrix4());return {bounds,parts};
}
const cruiseWorld=world(0,0);
const vessels=gltf.nodes.flatMap((node,index)=>node.extras?.cruise?[{node,...vesselBounds(index)}]:[]);
for(const {bounds,parts} of vessels) { const center=bounds.getCenter(new THREE.Vector3()),offset=new THREE.Vector3(-center.x,0,-center.z);bounds.translate(offset);parts.forEach(part=>part.translate(offset)); }
cruiseWorld.cruises=vessels.map(({node})=>{const object=new THREE.Object3D();object.userData=node.extras;return object;});
const crossed=vessels.map(()=>new Set());
for(let time=0;time<=CRUISE_CYCLE;time+=.1){
  cruiseWorld.elapsed=time;cruiseWorld.step(1/60);
  const occupied=[];
  vessels.forEach(({bounds,parts},index)=>{
    const boat=cruiseWorld.cruises[index],moved=bounds.clone().applyMatrix4(boat.matrixWorld);
    occupied.push(moved);
    assert.ok(moved.min.x>-7.875&&moved.max.x<7.875,'The complete hull clears walls and bridge piers, including during U-turns');
    assert.ok(moved.min.z>-167&&moved.max.z<167,'Turnarounds finish before the distant canal bend');
    for(const bridge of [-140,-91,-48,0,48,91,140]) {
      const half=bridge===0?8.55:3.4;
      if(moved.max.z<bridge-half||moved.min.z>bridge+half)continue;
      const x=Math.max(Math.abs(moved.min.x),Math.abs(moved.max.x));
      const underside=(bridge===0?2.55:1.8)+(bridge===0?.24:.14)*Math.max(0,1-(x/8.5)**2)-.94;
      assert.ok(moved.max.y+.10<underside,'Passengers and helm clear the bridge soffit by at least 10cm');
      if(bridge===0)for(const part of parts) {
        const p=part.clone().applyMatrix4(boat.matrixWorld),t=Math.max(Math.abs(p.min.x),Math.abs(p.max.x))/8.5;
        const rampBottom=2.79*(1-t*t*(3-2*t))-.60;
        assert.ok(p.max.y+.10<rampBottom,'Each passenger and equipment group clears the lower perimeter-ramp fascia');
      }
      if(Math.abs(boat.position.z-bridge)<.2)crossed[index].add(`${bridge},${Math.cos(boat.rotation.y)>0?'west':'east'}`);
    }
  });
  assert.ok(!occupied[0].intersectsBox(occupied[1]),'Opposing boats never intersect');
}
assert.ok(crossed.every(bridges=>bridges.size===14),'Both boats pass under all seven bridges in both directions');
console.log('PASS: both boats pass under all seven bridges in both directions; passengers clear soffits, full hulls clear piers and U-turns, and opposing boats stay separated.');
assert.equal(gltf.materials.filter(m=>m.extras?.bakedLightmap).length,12,'All four promenade finishes, bridges and six Ebisubashi finishes have completed light bakes');
assert.ok(gltf.materials.filter(m=>m.extras?.bake_mode).length>25,'Completed detail bakes must be in the delivered GLB');
const bake=JSON.parse(fs.readFileSync('assets/bakes/dotonbori.json','utf8'));
assert.equal(bake.engine,'CYCLES');assert.ok(bake.vertexBakes.length>30);assert.ok(bake.aoStd>.03);assert.ok(bake.lightmapMaximum>.1);
assert.equal(bake.resolution,4096,'Expanded walkways retain the original texel density');
assert.equal(bake.walkableExtent,152,'The bake covers both new ends of the playable district');
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
