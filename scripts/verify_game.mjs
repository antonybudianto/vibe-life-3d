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

const cameraContext = { exports: {}, Math };
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/game/camera.ts','utf8'), { compilerOptions: { module: ts.ModuleKind.CommonJS } }).outputText, cameraContext);
const { zoomDistance, elevatedPitch, MIN_ZOOM, MAX_ZOOM } = cameraContext.exports;
let zoom = 8.8;
for(let i=0;i<100;i++) zoom=zoomDistance(zoom,1);
assert.equal(zoom,60,'Dolly reaches the requested neighborhood view');
for(let i=0;i<100;i++) zoom=zoomDistance(zoom,-1);
assert.equal(zoom,MIN_ZOOM,'Dolly cannot enter first person');
assert.ok(elevatedPitch(.24,MAX_ZOOM)>1,'Wide zoom rises over the street');
assert.equal(elevatedPitch(.24,8.8),.24,'Close camera retains manual pitch');
assert.ok(elevatedPitch(1.02,MAX_ZOOM)<Math.PI/2,'Orbit cannot flip over');

const report = [];
for (const name of ['character','crossing','park','car','motorcycle','pedestrian','taxi','citybus','hachiko']) {
  const buf=fs.readFileSync(`public/models/${name}.glb`);
  assert.equal(buf.toString('utf8',0,4),'glTF');assert.equal(buf.readUInt32LE(8),buf.length);
  const json=JSON.parse(buf.toString('utf8',20,20+buf.readUInt32LE(12)));
  assert.ok(json.meshes.length>0);
  for (const node of json.nodes) if(node.translation) assert.ok(node.translation.every(Number.isFinite));
  if(name==='hachiko') {
    assert.ok(json.nodes.some(n=>n.name==='Hachiko sculpt'),'Recognizable dog sculpture is present');
    for(const mesh of json.meshes) for(const p of mesh.primitives) assert.ok(p.attributes.COLOR_0!==undefined,'Hachiko plaza carries Cycles shading');
    assert.ok(buf.length<900000,'Landmark stays under 900 KB');
  }
  if(name==='character') for(const joint of ['Character','Arm_L','Arm_R','Leg_L','Leg_R']) assert.ok(json.nodes.some(n=>n.name===joint),`${joint} preserved`);
  if(['character','crossing','park'].includes(name)) {
    const baked=json.materials.filter(m=>m.occlusionTexture);
    assert.ok(baked.length >= (name==='crossing' ? 4 : 6),`${name} includes genuine AO textures`);
    if(name==='crossing') {
      const vertexBaked = json.materials.filter(m=>m.extras?.bake_mode?.includes('Cycles color attribute'));
      assert.ok(vertexBaked.length>=20,'Detailed street props use Cycles vertex bakes');
      for(const mesh of json.meshes) for(const p of mesh.primitives) if(json.materials[p.material]?.extras?.bake_mode) assert.ok(p.attributes.COLOR_0!==undefined,'Vertex bake is exported');
      const coverage=JSON.parse(fs.readFileSync('assets/bakes/crossing.json','utf8'));
      assert.ok(coverage.vertexBakes.every(b=>b.minimum>.001&&b.corners>0),'Every baked corner has a valid color');
      assert.ok(coverage.aoStd>.03&&coverage.lightmapMaximum>.01,'Street AO and irradiance are nonuniform Cycles bakes');
      for(const material of ['Rain-dark asphalt','Pavement stone']) {
        const m=json.materials.find(m=>m.name===material);
        assert.ok(m.normalTexture&&m.pbrMetallicRoughness.baseColorTexture&&m.pbrMetallicRoughness.metallicRoughnessTexture,'Street aggregate has PBR textures');
      }
    }
    for(const mesh of json.meshes) for(const primitive of mesh.primitives) {
      if(json.materials[primitive.material]?.occlusionTexture) {
        assert.equal(json.materials[primitive.material].occlusionTexture.texCoord,1);
        assert.ok(primitive.attributes.TEXCOORD_1!==undefined,`${name} includes UV1 for bakes`);
      }
    }
    if(name!=='character') for(const m of baked) {
      assert.ok(m.extras?.bakedLightmap);
      assert.ok(fs.existsSync('public'+m.extras.bakedLightmap),'Irradiance texture exists');
    }
  }
  if(name==='pedestrian') {
    const moving=json.nodes.filter(n=>n.extras?.swing);
    assert.ok(moving.length>=8,'Blender-authored limb pivots are exported');
    assert.ok(moving.every(n=>n.extras.pivot.length===3&&n.extras.pivot.every(Number.isFinite)));
  }
  if(['crossing','park'].includes(name)) {
    const m=JSON.parse(fs.readFileSync(`public/models/${name}.json`,'utf8'));
    assert.ok(m.colliders.length>0);
    const resolved=move(m.spawn[0],m.spawn[2],0,0,.32,m.colliders,m.bounds);
    assert.equal(resolved.x,m.spawn[0]);assert.equal(resolved.z,m.spawn[2]);
  }
  report.push({ name, bytes:buf.length, gzipBytes:zlib.gzipSync(buf).length, meshes:json.meshes.length, triangles:json.meshes.reduce((n,m)=>n+m.primitives.reduce((s,p)=>s+json.accessors[p.indices].count/3,0),0), compressed:!!json.extensionsUsed?.includes('KHR_draco_mesh_compression') });
}
const life=JSON.parse(fs.readFileSync('public/models/crossing-life.json','utf8'));
assert.equal(life.people.length,74);assert.equal(life.vehicles.length,5);
for(const p of life.people) {
  assert.ok([...p.a,...p.b].every(v=>Number.isFinite(v)&&Math.abs(v)<45));
  assert.ok(p.scale>.8&&p.scale<1.2&&p.offset>=0&&p.offset<1);
}
const trafficContext={exports:{},Math};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/game/traffic.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText,trafficContext);
const {TrafficSimulation,pedestrianPose}=trafficContext.exports;
const sim=new TrafficSimulation(life.vehicles),away={x:40,z:40,radius:.32},phasesSeen=new Set();
let wrapped=false,last=sim.cars.map(v=>({x:v.x,z:v.z}));
for(let i=0;i<60*240;i++) {
  const people=life.people.map(p=>({...pedestrianPose(p,sim.pedestrianWave,sim.pedestrianTime),radius:.35*p.scale}));
  sim.step(1/60,people,away);phasesSeen.add(sim.phase);
  for(const [j,v] of sim.cars.entries()) {
    assert.ok(Number.isFinite(v.x)&&Number.isFinite(v.z)&&v.speed>=0,'Traffic state is finite');
    if(Math.hypot(v.x-last[j].x,v.z-last[j].z)>100) wrapped=true;
    if(sim.phase==='pedestrians') assert.ok(Math.abs(v.x)>12+Math.abs(v.dx)*v.halfLength||Math.abs(v.z)>12+Math.abs(v.dz)*v.halfLength,'Junction is clear during the pedestrian wave');
    for(const p of people) {
      const dx=Math.max(0,Math.abs(p.x-v.x)-(v.dx?v.halfLength:v.halfWidth));
      const dz=Math.max(0,Math.abs(p.z-v.z)-(v.dz?v.halfLength:v.halfWidth));
      assert.ok(Math.hypot(dx,dz)>=p.radius-.08,'Traffic does not intersect pedestrians');
    }
  }
  last=sim.cars.map(v=>({x:v.x,z:v.z}));
}
assert.equal(phasesSeen.size,4,'Both roads and pedestrians receive a turn');assert.ok(wrapped,'Cars keep circulating');
const stopSim=new TrafficSimulation([{model:'taxi',x:-4.5,z:-25,yaw:0}]);
for(let i=0;i<600;i++)stopSim.step(1/60,[],{x:-4.5,z:-10,radius:.32});
assert.ok(stopSim.cars[0].z<-13.3&&stopSim.cars[0].speed<.01,'Taxi stops before the player');
const before=JSON.stringify(stopSim.cars);stopSim.step(0,[],away);assert.equal(JSON.stringify(stopSim.cars),before,'Paused traffic stays still');
for(const p of life.people) assert.equal(pedestrianPose(p,1,27).moving,false,'Every pedestrian clears before traffic resumes');
const map=JSON.parse(fs.readFileSync('public/models/crossing.json','utf8'));
assert.ok(map.colliders.every(c=>c.kind!=='traffic'),'No invisible parked traffic colliders remain');
const landmark=JSON.parse(fs.readFileSync('public/models/hachiko.json','utf8'));
assert.ok(landmark.colliders.length>=6);assert.ok(fs.statSync('public/textures/clouds.webp').size<100000,'Cloud panorama remains lightweight');
const skyPalette=JSON.parse(fs.readFileSync('lib/game/lighting.json','utf8'));
for(const p of Object.values(skyPalette))assert.ok(/^#[0-9a-f]{6}$/i.test(p.skyZenith)&&/^#[0-9a-f]{6}$/i.test(p.cloudTint));
fs.mkdirSync('work',{recursive:true});fs.writeFileSync('work/asset-report.json',JSON.stringify(report,null,2));
console.log('PASS: collisions, wall sliding, vehicle clearance, map bounds, Tokyo time transitions, 60m third-person zoom, glTF structure, baked textures/UVs, animation pivots, safe map spawns.');
console.table(report);
