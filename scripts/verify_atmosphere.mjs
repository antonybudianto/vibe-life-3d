import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import ts from 'typescript';
import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';

function moduleFrom(path, require) {
  const context = { exports: {}, require };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, context);
  return context.exports;
}
const palette = JSON.parse(fs.readFileSync('lib/game/lighting.json', 'utf8'));
const { Atmosphere } = moduleFrom('lib/game/atmosphere.ts', () => THREE);
const { CitySky } = moduleFrom('lib/game/sky.ts', name => name === 'three' ? THREE : { default: palette });
const { CanalWater } = moduleFrom('lib/game/canal-water.ts', name => name === 'three' ? THREE : { Reflector });
const atmosphere = new Atmosphere();
const material = new THREE.MeshStandardMaterial();
const compiled = () => {
  const shader = { vertexShader: THREE.ShaderLib.standard.vertexShader,
    fragmentShader: THREE.ShaderLib.standard.fragmentShader, uniforms: {} };
  material.onBeforeCompile(shader, {});
  return shader;
};
atmosphere.applyTo(material);
const shader = compiled();
assert.equal(atmosphere.level, 'clear');
assert.equal(shader.uniforms.hazeStrength.value, 0, 'Clear removes fog at every distance');
assert.equal(atmosphere.fog.near, 85);
assert.equal(atmosphere.fog.far, 200, 'Medium preserves the existing distance falloff');
const version = material.version;
atmosphere.setLevel('small');
const small = shader.uniforms.hazeStrength.value;
atmosphere.setLevel('medium');
assert.ok(small > 0 && small < shader.uniforms.hazeStrength.value);
assert.equal(shader.uniforms.hazeStrength.value, 1);
assert.equal(material.version, version, 'Changing haze updates live uniforms without shader recompilation');
atmosphere.applyTo(material);
assert.equal(material.version, version, 'Shared/instanced materials are not patched twice');
assert.equal(compiled().fragmentShader, shader.fragmentShader);
atmosphere.update(30);
assert.equal(shader.uniforms.hazeTime.value, 30);
const camera = new THREE.PerspectiveCamera();
camera.position.set(12, 4, 18);
const sky = new CitySky();
sky.update(camera, 30);
assert.ok(sky.mesh.position.equals(camera.position));
assert.equal(sky.mesh.material.uniforms.time.value, shader.uniforms.hazeTime.value);
// A paused simulation supplies the same timestamp even as the camera moves.
camera.position.x += 5;
sky.update(camera, 30); atmosphere.update(30);
assert.equal(sky.mesh.material.uniforms.time.value, 30);
assert.equal(shader.uniforms.hazeTime.value, 30);
for (const phase of ['day', 'evening', 'night']) {
  sky.setTime(phase, phase, 0);
  assert.equal(atmosphere.level, 'medium');
}
const surface = new THREE.Mesh(new THREE.PlaneGeometry(4, 8), new THREE.MeshStandardMaterial());
surface.updateMatrixWorld(true);
const water = new CanalWater(surface, new THREE.Texture());
atmosphere.applyTo(water.mesh.material);
const waterShader = { vertexShader: water.mesh.material.vertexShader,
  fragmentShader: water.mesh.material.fragmentShader, uniforms: { ...water.mesh.material.uniforms } };
water.mesh.material.onBeforeCompile(waterShader, {});
assert.equal(water.mesh.material.fog, true);
assert.ok(waterShader.uniforms.fogColor, 'Water receives the scene fog color');
assert.equal(waterShader.uniforms.hazeTime, shader.uniforms.hazeTime, 'Water and reflected city share the same wind clock');
assert.equal(waterShader.uniforms.hazeStrength, shader.uniforms.hazeStrength);
atmosphere.setLevel('clear');
assert.equal(waterShader.uniforms.hazeStrength.value, 0, 'Returning to Clear clears the water too');
water.dispose(); sky.dispose(); material.dispose(); surface.geometry.dispose(); surface.material.dispose();
console.log('PASS: haze presets, shared city/water uniforms, stable recompilation and pause-safe cloud motion.');
