import * as THREE from 'three';
import phases from './lighting.json';

/** Blender cloud bakes advected in layers, with slow, seamless shape evolution. */
export class CitySky {
  private texture = new THREE.Texture();
  private canalTexture = new THREE.Texture();
  private alive = true;
  private material = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, depthTest: false, toneMapped: true,
    uniforms: { clouds: { value: this.texture }, zenith: { value: new THREE.Color() }, horizon: { value: new THREE.Color() }, cloudTint: { value: new THREE.Color() }, time: { value: 0 } },
    vertexShader: `varying vec3 vDirection;
      void main(){vDirection=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader: `uniform sampler2D clouds; uniform vec3 zenith,horizon,cloudTint; uniform float time; varying vec3 vDirection;
      vec4 cloudLayer(vec3 direction, float speed, float offset) {
        // Distort a direction, not the wrapped UV: both sides of the panorama
        // seam and the poles stay joined as the cloud edges gently billow.
        vec3 wind = vec3(sin(direction.z*5.0 + time*.013),
          sin(direction.x*4.0 - time*.011)*.45, sin(direction.y*5.0 + time*.009));
        vec3 d = normalize(direction + wind*.025);
        vec2 uv = vec2(atan(d.z,d.x)/6.28318530718 + .5 + time*speed + offset,
          asin(clamp(d.y,-1.0,1.0))/3.14159265359 + .5);
        return texture2D(clouds, uv);
      }
      void main(){
        vec3 d=normalize(vDirection);
        vec4 cloud=cloudLayer(d, .00032, 0.0);
        vec4 highCloud=cloudLayer(normalize(d + vec3(0.0,.12,0.0)), .00019, .31);
        vec3 clearSky=mix(horizon,zenith,pow(max(d.y,0.0),0.42));
        // A faint, higher layer moves more slowly, adding depth between banks.
        clearSky=mix(clearSky,cloudTint,highCloud.a*.14*smoothstep(.08,.45,d.y));
        vec3 silver=cloudTint*mix(0.68,1.0,cloud.r);
        gl_FragColor=vec4(mix(clearSky,silver,cloud.a*smoothstep(-0.03,0.12,d.y)),1.0);
        #include <tonemapping_fragment>
        #include <colorspace_fragment>
      }`,
  });
  mesh = new THREE.Mesh(new THREE.SphereGeometry(190, 40, 24), this.material);

  constructor() {
    this.mesh.name = 'Blue sky and Blender cloud panorama'; this.mesh.renderOrder = -1000; this.mesh.frustumCulled = false;
  }
  async load() {
    const [texture, canalTexture] = await Promise.all(['/textures/clouds.webp', '/textures/dotonbori-clouds.webp'].map(path => new THREE.TextureLoader().loadAsync(path)));
    if (!this.alive) { texture.dispose(); canalTexture.dispose(); return; }
    for (const t of [texture, canalTexture]) { t.wrapS = THREE.RepeatWrapping; t.colorSpace = THREE.NoColorSpace; }
    this.canalTexture.dispose(); this.canalTexture = canalTexture;
    this.texture.dispose(); this.texture = texture; this.material.uniforms.clouds.value = texture;
  }
  setTime(phase: keyof typeof phases, next: keyof typeof phases, blend: number, palette = phases, canal = false) {
    this.material.uniforms.clouds.value = canal ? this.canalTexture : this.texture;
    for (const [uniform, key] of [['zenith','skyZenith'],['horizon','sky'],['cloudTint','cloudTint']] as const) {
      (this.material.uniforms[uniform].value as THREE.Color).set(palette[phase][key]).lerp(new THREE.Color(palette[next][key]),blend);
    }
  }
  update(camera: THREE.Camera, time: number) { this.mesh.position.copy(camera.position); this.material.uniforms.time.value = time; }
  dispose() { this.alive = false; this.texture.dispose(); this.canalTexture.dispose(); this.mesh.geometry.dispose(); this.material.dispose(); }
}
