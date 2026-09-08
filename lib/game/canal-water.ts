import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';

/** Reflect the actual district using the water mesh exported from Blender. */
export class CanalWater {
  readonly mesh: Reflector;
  private source: THREE.Mesh;
  constructor(source: THREE.Mesh) {
    this.source = source;
    const geometry = source.geometry.clone();
    geometry.applyMatrix4(source.matrixWorld);
    const positions = geometry.getAttribute('position');
    for (let i = 0; i < positions.count; i++) positions.setY(i, 0);
    geometry.rotateX(Math.PI / 2);
    geometry.computeVertexNormals(); geometry.computeBoundingSphere();
    this.mesh = new Reflector(geometry, { textureWidth: 768, textureHeight: 768, clipBias: .003, multisample: 0 });
    this.mesh.name = 'Dotonbori rippling canal reflections';
    this.mesh.rotation.x = -Math.PI / 2; this.mesh.position.y = -1.43;
    const material = this.mesh.material as THREE.ShaderMaterial;
    material.uniforms.time = { value: 0 };
    material.vertexShader = material.vertexShader.replace('varying vec4 vUv;', 'varying vec4 vUv; varying vec2 canalPosition;').replace('vUv = textureMatrix', 'canalPosition = position.xy; vUv = textureMatrix');
    material.fragmentShader = material.fragmentShader
      .replace('varying vec4 vUv;', 'varying vec4 vUv; varying vec2 canalPosition; uniform float time;')
      .replace('vec4 base = texture2DProj( tDiffuse, vUv );', `
        vec2 uv = vUv.xy / vUv.w;
        float wave = sin(canalPosition.y * 5.8 + canalPosition.x * 2.1 + time * 1.4)
          + .5 * sin(canalPosition.y * 11.0 - canalPosition.x * 3.2 - time * 1.1);
        uv += vec2(wave * .0035, sin(canalPosition.x * 8.0 + time) * .0009);
        vec4 base = texture2D(tDiffuse, uv);
      `)
      .replace('vec4( blendOverlay( base.rgb, color ), 1.0 )', 'vec4(mix(vec3(.008, .042, .056), base.rgb, .64) * (1.0 + wave * .08), 1.0)');
    source.visible = false;
  }
  update(time: number) { (this.mesh.material as THREE.ShaderMaterial).uniforms.time.value = time; }
  dispose() { this.mesh.removeFromParent(); this.mesh.getRenderTarget().dispose(); this.mesh.geometry.dispose(); (this.mesh.material as THREE.Material).dispose(); this.source.visible = true; }
}
