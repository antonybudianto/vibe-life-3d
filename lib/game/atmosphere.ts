import * as THREE from 'three';

export type HazeLevel = 'clear' | 'small' | 'medium';
const STRENGTH: Record<HazeLevel, number> = { clear: 0, small: .35, medium: 1 };

/** Shared by the city and its reflection, including instanced pedestrians. */
export class Atmosphere {
  readonly fog = new THREE.Fog(0x8896b8, 85, 200);
  level: HazeLevel = 'medium';
  private strength = { value: STRENGTH.medium };
  private time = { value: 0 };
  private materials = new WeakSet<THREE.Material>();

  setLevel(level: HazeLevel) { this.level = level; this.strength.value = STRENGTH[level]; }
  update(time: number) { this.time.value = time; }

  applyTo(material: THREE.Material) {
    if (this.materials.has(material)) return;
    this.materials.add(material);
    const compile = material.onBeforeCompile;
    const cacheKey = material.customProgramCacheKey();
    material.onBeforeCompile = (shader, renderer) => {
      compile.call(material, shader, renderer);
      shader.uniforms.hazeStrength = this.strength;
      shader.uniforms.hazeTime = this.time;
      shader.vertexShader = shader.vertexShader
        .replace('#include <fog_pars_vertex>', '#include <fog_pars_vertex>\nvarying vec3 vHazePosition;')
        .replace('#include <fog_vertex>', `#include <fog_vertex>
          vec4 hazePosition = vec4(transformed, 1.0);
          #ifdef USE_BATCHING
            hazePosition = batchingMatrix * hazePosition;
          #endif
          #ifdef USE_INSTANCING
            hazePosition = instanceMatrix * hazePosition;
          #endif
          vHazePosition = (modelMatrix * hazePosition).xyz;`);
      shader.fragmentShader = shader.fragmentShader
        .replace('#include <fog_pars_fragment>', `#include <fog_pars_fragment>
          varying vec3 vHazePosition;
          uniform float hazeStrength, hazeTime;`)
        .replace('#include <fog_fragment>', `#ifdef USE_FOG
          // Broad, slowly advected wisps. Nearby surfaces stay completely clear;
          // Medium retains the original 85–200 m falloff, with only 6% variation.
          vec3 air = vHazePosition * .025 - vec3(hazeTime * .006, 0.0, hazeTime * .004);
          float wisps = sin(air.x + sin(air.z * .73)) * sin(air.z * .91 + air.y * .4);
          float hazeFactor = smoothstep(fogNear, fogFar, vFogDepth) * hazeStrength;
          hazeFactor = clamp(hazeFactor * (1.0 + .06 * wisps), 0.0, 1.0);
          gl_FragColor.rgb = mix(gl_FragColor.rgb, fogColor, hazeFactor);
        #endif`);
    };
    material.customProgramCacheKey = () => `${cacheKey}|moving-haze-v1`;
    material.needsUpdate = true;
  }
}
