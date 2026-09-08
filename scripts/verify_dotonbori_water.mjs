import fs from 'node:fs';
import vm from 'node:vm';
import path from 'node:path';
import {createRequire} from 'node:module';
import * as THREE from 'three';
import assert from 'node:assert/strict';
import ts from 'typescript';
import {Reflector} from 'three/addons/objects/Reflector.js';
// Decode the delivered Draco primitive: duplicate-face loss is invisible in
// Blender renders and in checks of uncompressed accessor bounds alone.
const ctx={module:{exports:{}},exports:{},require:createRequire(import.meta.url),__dirname:path.resolve('public/draco'),process,console,Buffer,TextDecoder,TextEncoder,WebAssembly,setTimeout,clearTimeout,performance};
vm.runInNewContext(fs.readFileSync('public/draco/draco_wasm_wrapper.js','utf8'),ctx);
const draco=await ctx.module.exports({wasmBinary:fs.readFileSync('public/draco/draco_decoder.wasm')});
const bytes=fs.readFileSync(process.argv[2]??'public/models/dotonbori.glb');
const g=JSON.parse(bytes.toString('utf8',20,20+bytes.readUInt32LE(12)));
const bin=20+bytes.readUInt32LE(12)+8;
const primitive=g.meshes.find(m=>m.primitives.some(p=>g.materials[p.material]?.extras?.water_surface)).primitives[0];
const compression=primitive.extensions.KHR_draco_mesh_compression;
const view=g.bufferViews[compression.bufferView],array=bytes.subarray(bin+view.byteOffset,bin+view.byteOffset+view.byteLength);
const decoder=new draco.Decoder(),mesh=new draco.Mesh();
const status=decoder.DecodeArrayToMesh(array,array.length,mesh);if(!status.ok())throw Error(status.error_msg());
const count=mesh.num_points(),faces=mesh.num_faces();
const pointer=draco._malloc(count*3*4);
decoder.GetAttributeDataArrayForAllPoints(mesh,decoder.GetAttributeByUniqueId(mesh,compression.attributes.POSITION),draco.DT_FLOAT32,count*3*4,pointer);
const positions=new Float32Array(draco.HEAPF32.buffer,pointer,count*3).slice();draco._free(pointer);
const ip=draco._malloc(faces*3*4);decoder.GetTrianglesUInt32Array(mesh,faces*3*4,ip);
const indices=new Uint32Array(draco.HEAPF32.buffer,ip,faces*3).slice();draco._free(ip);
draco.destroy(mesh);draco.destroy(decoder);
const geo=new THREE.BufferGeometry();geo.setAttribute('position',new THREE.BufferAttribute(positions,3));geo.setIndex(new THREE.BufferAttribute(indices,1));
const water=new THREE.Mesh(geo,new THREE.MeshBasicMaterial());water.updateMatrixWorld(true);
const moduleContext={exports:{},require:name=>name==='three'?THREE:{Reflector}};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/game/canal-water.ts','utf8'),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022},
}).outputText,moduleContext);
const reflected=new moduleContext.exports.CanalWater(water,new THREE.Texture());
reflected.mesh.updateMatrixWorld(true);
const ray=new THREE.Raycaster();
let samples=0;
for(const z of [-237,-220,-190,-167,-151,-140,-110,-91,-75,-70,-69,-48,0,48,69,70,75,91,110,140,151,167,190,220,237]){
  const center=Math.max(0,Math.abs(z)-167)*.42;
  for(const offset of [-8.2,-6,0,6,8.2]){
    const x=center+offset;
    ray.set(new THREE.Vector3(x,5,z),new THREE.Vector3(0,-1,0));
    assert.ok(ray.intersectObject(water).length>0,`Exported water must face upward at ${x},${z}`);
    const hits=ray.intersectObject(reflected.mesh);
    assert.ok(hits.length>0,`Actual reflection mesh must cover ${x},${z}`);
    assert.ok(Math.abs(hits[0].point.y+1.43)<1e-5,'Mirror surface stays at the canal water level');
    samples++;
  }
}
const counts={central:{up:0,down:0,degenerate:0},extension:{up:0,down:0,degenerate:0}};
const a=new THREE.Vector3(),b=new THREE.Vector3(),c=new THREE.Vector3();
for(let i=0;i<indices.length;i+=3){a.fromArray(positions,indices[i]*3);b.fromArray(positions,indices[i+1]*3);c.fromArray(positions,indices[i+2]*3);const area=new THREE.Vector3().subVectors(b,a).cross(new THREE.Vector3().subVectors(c,a)).y;const bucket=Math.abs((a.z+b.z+c.z)/3)>70.1?counts.extension:counts.central;bucket[Math.abs(area)<1e-8?'degenerate':area>0?'up':'down']++;}
assert.equal(counts.extension.down,0,'Every mirrored extension face points upward after compression');
assert.equal(counts.extension.up,24,'All twelve extension quads survive compression');
reflected.dispose();geo.dispose();water.material.dispose();
console.log(`PASS: ${samples} points across the central canal, both ±70 seams, all seven bridges and both distant bends; exported front faces and the runtime reflection footprint remain continuous.`);
