import * as THREE from 'three';
import { Reflector } from 'three/addons/objects/Reflector.js';

/** GLTFLoader sanitizes node names; material extras preserve the authored role. */
export function findCanalSurface(root: THREE.Object3D): THREE.Mesh | undefined {
  let surface: THREE.Mesh | undefined;
  root.traverse(o => {
    if (o instanceof THREE.Mesh && (Array.isArray(o.material) ? o.material : [o.material]).some(m => m.userData.water_surface)) surface = o;
  });
  return surface;
}

/** HDR reflections of the live district, perturbed by Cycles-baked ripple normals. */
export class CanalWater {
  readonly mesh: Reflector;
  private source: THREE.Mesh;
  private normals: THREE.Texture;
  constructor(source: THREE.Mesh, normals: THREE.Texture) {
    this.source = source; this.normals = normals;
    normals.wrapS = normals.wrapT = THREE.RepeatWrapping;
    normals.colorSpace = THREE.NoColorSpace;
    normals.anisotropy = 4;
    const geometry = source.geometry.clone();
    geometry.applyMatrix4(source.matrixWorld);
    const positions = geometry.getAttribute('position');
    // Reflector's local +Z defines its mathematical mirror plane. The Blender
    // footprint is retained; its fine waves live in the normal bake.
    for (let i = 0; i < positions.count; i++) positions.setY(i, 0);
    geometry.rotateX(Math.PI / 2);
    geometry.computeVertexNormals(); geometry.computeBoundingSphere();
    this.mesh = new Reflector(geometry, { textureWidth: 1024, textureHeight: 1024, clipBias: .003, multisample: 0 });
    this.mesh.name = 'Dotonbori rippling canal reflections';
    this.mesh.rotation.x = -Math.PI / 2; this.mesh.position.y = -1.43;
    const material = this.mesh.material as THREE.ShaderMaterial;
    Object.assign(material.uniforms, {
      time: { value: 0 }, normalMap: { value: normals }, eye: { value: new THREE.Vector3() },
      sunlight: { value: new THREE.Color() }, sunDirection: { value: new THREE.Vector3(-22, 28, 14).normalize() },
    });
    material.vertexShader = `
      uniform mat4 textureMatrix;
      varying vec4 mirrorCoord;
      varying vec3 worldPosition;
      #include <common>
      #include <logdepthbuf_pars_vertex>
      void main() {
        mirrorCoord = textureMatrix * vec4(position, 1.0);
        worldPosition = (modelMatrix * vec4(position, 1.0)).xyz;
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        #include <logdepthbuf_vertex>
      }`;
    material.fragmentShader = `
      uniform sampler2D tDiffuse;
      uniform sampler2D normalMap;
      uniform float time;
      uniform vec3 eye;
      uniform vec3 sunlight;
      uniform vec3 sunDirection;
      varying vec4 mirrorCoord;
      varying vec3 worldPosition;
      #include <common>
      #include <logdepthbuf_pars_fragment>
      void main() {
        #include <logdepthbuf_fragment>
        vec2 p = worldPosition.xz;
        vec3 a = texture2D(normalMap, p * .25 + vec2(time * .014, -time * .019)).xyz * 2.0 - 1.0;
        vec3 b = texture2D(normalMap, p * .61 + vec2(-time * .011, time * .009)).xyz * 2.0 - 1.0;
        vec2 slope = a.xy * .78 + b.xy * .32;
        vec3 normal = normalize(vec3(slope.x, 1.0, -slope.y));
        vec3 view = normalize(eye - worldPosition);
        float distanceToEye = length(eye - worldPosition);
        vec2 uv = mirrorCoord.xy / mirrorCoord.w;
        uv += slope * (.025 + .10 / max(distanceToEye, 3.0));
        vec3 reflection = texture2D(tDiffuse, uv).rgb * .6
          + texture2D(tDiffuse, uv + vec2(.0006, 0.0)).rgb * .2
          + texture2D(tDiffuse, uv - vec2(.0006, 0.0)).rgb * .2;
        float fresnel = .18 + .82 * pow(1.0 - max(dot(normal, view), 0.0), 4.0);
        vec3 halfVector = normalize(view + sunDirection);
        float sparkle = pow(max(dot(normal, halfVector), 0.0), 180.0);
        vec3 deepWater = vec3(.006, .025, .031);
        vec3 color = mix(deepWater, reflection, .48 + .52 * fresnel);
        // Stone spans shield direct sun while retaining reflected undersides.
        float shade = smoothstep(3.8, 4.5, abs(p.y))
          * smoothstep(3.4, 4.1, abs(abs(p.y) - 48.0));
        color += sunlight * sparkle * .42 * shade;
        gl_FragColor = vec4(color, 1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`;
    source.visible = false;
  }
  update(time: number, camera: THREE.Camera, sun: THREE.DirectionalLight) {
    const u = (this.mesh.material as THREE.ShaderMaterial).uniforms;
    u.time.value = time; u.eye.value.copy(camera.position);
    u.sunlight.value.copy(sun.color).multiplyScalar(sun.intensity);
  }
  dispose() {
    this.mesh.removeFromParent(); this.mesh.dispose(); this.mesh.geometry.dispose();
    this.normals.dispose(); this.source.visible = true;
  }
}
