// Check the delivered Draco triangles, where coincident front/back faces and
// overlapping material batches cause the wall streaks seen in the browser.
import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {createRequire} from 'node:module';
import assert from 'node:assert/strict';
import * as THREE from 'three';

const context={module:{exports:{}},exports:{},require:createRequire(import.meta.url),__dirname:path.resolve('public/draco'),process,console,Buffer,TextDecoder,TextEncoder,WebAssembly,setTimeout,clearTimeout,performance};
vm.runInNewContext(fs.readFileSync('public/draco/draco_wasm_wrapper.js','utf8'),context);
const draco=await context.module.exports({wasmBinary:fs.readFileSync('public/draco/draco_decoder.wasm')});
const bytes=fs.readFileSync(process.argv[2]??'public/models/dotonbori.glb');
const gltf=JSON.parse(bytes.toString('utf8',20,20+bytes.readUInt32LE(12)));
const bin=28+bytes.readUInt32LE(12),surfaces=[];
const names=new Set(['Dotonbori brushed rails','Dotonbori limestone','Ebisubashi ramp retaining walls','Ebisubashi ramp fascia','Bridge solid soffits']);
const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
for(const node of gltf.nodes.filter(n=>names.has(n.name))) {
  assert.ok(!node.matrix&&!node.rotation&&!node.translation&&!node.scale,'Bridge batches must be in exported world coordinates');
  for(const primitive of gltf.meshes[node.mesh].primitives) {
    const extension=primitive.extensions.KHR_draco_mesh_compression;
    const view=gltf.bufferViews[extension.bufferView];
    const source=bytes.subarray(bin+(view.byteOffset??0),bin+(view.byteOffset??0)+view.byteLength);
    const decoder=new draco.Decoder(),mesh=new draco.Mesh();
    const result=decoder.DecodeArrayToMesh(source,source.length,mesh);
    assert.ok(result.ok(),result.error_msg());
    let pointer=draco._malloc(mesh.num_points()*12);
    decoder.GetAttributeDataArrayForAllPoints(mesh,decoder.GetAttributeByUniqueId(mesh,extension.attributes.POSITION),draco.DT_FLOAT32,mesh.num_points()*12,pointer);
    const positions=new Float32Array(draco.HEAPF32.buffer,pointer,mesh.num_points()*3).slice();draco._free(pointer);
    pointer=draco._malloc(mesh.num_faces()*12);decoder.GetTrianglesUInt32Array(mesh,mesh.num_faces()*12,pointer);
    const triangles=new Uint32Array(draco.HEAPF32.buffer,pointer,mesh.num_faces()*3).slice();draco._free(pointer);
    draco.destroy(mesh);draco.destroy(decoder);
    const selected=[];
    for(let i=0;i<triangles.length;i+=3) {
      a.fromArray(positions,triangles[i]*3);b.fromArray(positions,triangles[i+1]*3);c.fromArray(positions,triangles[i+2]*3);
      if([a,b,c].some(v=>Math.abs(v.x)>8.6||Math.abs(v.z)>9.0))continue;
      const normal=new THREE.Vector3().subVectors(b,a).cross(new THREE.Vector3().subVectors(c,a));
      // Exclude handrails, seam rods and horizontal decks. These checks target
      // the large vertical wall faces, not intentionally layered decoration.
      if(normal.length()<.03||Math.abs(normal.normalize().y)>.02)continue;
      selected.push(triangles[i],triangles[i+1],triangles[i+2]);
    }
    const geometry=new THREE.BufferGeometry();geometry.setAttribute('position',new THREE.BufferAttribute(positions,3));geometry.setIndex(selected);
    const surface=new THREE.Mesh(geometry,new THREE.MeshBasicMaterial({side:THREE.DoubleSide}));surface.name=node.name;surface.updateMatrixWorld(true);surfaces.push(surface);
  }
}
const outline=x=>Math.max(3.8,Math.sqrt(Math.max(0,6.9**2-x*x)));
const deck=x=>2.55+.24*Math.max(0,1-(x/8.5)**2);
function sample(fn,x,steps) {
  const i=Math.max(0,Math.min(steps-1,Math.floor((x+8.5)*steps/17))),a=-8.5+i*17/steps,b=a+17/steps;
  return fn(a)+(fn(b)-fn(a))*(x-a)/(b-a);
}
const ramp=x=>{const t=Math.abs(x)/8.5;return 2.79*(1-t*t*(3-2*t));};
const ray=new THREE.Raycaster();ray.far=.6;
const failures=[];let checks=0;
for(const end of [-1,1])for(const x of [-7.31,-6.27,-5.43,-4.61,-3.39,-2.57,-1.63,1.63,2.57,3.39,4.61,5.43,6.27,7.31]) {
  const edge=sample(outline,x,24);
  for(const [role,offset,height] of [['retaining wall',0,sample(deck,x,24)-.27],['outer fascia',1.65,sample(ramp,x,48)-.31]]) {
    ray.set(new THREE.Vector3(x,height,end*(edge+offset+.3)),new THREE.Vector3(0,0,-end));
    const hits=ray.intersectObjects(surfaces);checks++;
    if(hits.length!==1)failures.push({role,x,end,faces:hits.length,meshes:hits.map(h=>h.object.name)});
  }
}
for(const surface of surfaces){surface.geometry.dispose();surface.material.dispose();}
assert.equal(failures.length,0,`Every wall sample must hit one face; overlapping or missing panels: ${JSON.stringify(failures.slice(0,8))}`);
console.log(`PASS: ${checks} compressed-GLB wall samples across both bridge sides have exactly one visible surface, with no competing fascia faces.`);
