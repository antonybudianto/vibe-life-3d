import * as THREE from 'three';
import phases from './lighting.json';

/** One Blender-baked cloud panorama, recolored smoothly through the Tokyo day. */
export class CitySky {
  private texture = new THREE.Texture();
  private canalTexture = new THREE.Texture();
  private alive = true;
  private material = new THREE.ShaderMaterial({
    side: THREE.BackSide, depthWrite: false, depthTest: false, toneMapped: true,
    uniforms: { clouds: { value: this.texture }, zenith: { value: new THREE.Color() }, horizon: { value: new THREE.Color() }, cloudTint: { value: new THREE.Color() }, drift: { value: 0 } },
    vertexShader: `varying vec3 vDirection;
      void main(){vDirection=position;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}`,
    fragmentShader: `uniform sampler2D clouds; uniform vec3 zenith,horizon,cloudTint; uniform float drift; varying vec3 vDirection;
      void main(){
        vec3 d=normalize(vDirection);
        vec2 uv=vec2(atan(d.z,d.x)/6.28318530718+0.5+drift,asin(clamp(d.y,-1.0,1.0))/3.14159265359+0.5);
        vec4 cloud=texture2D(clouds,uv);
        vec3 clearSky=mix(horizon,zenith,pow(max(d.y,0.0),0.42));
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
  update(camera: THREE.Camera, time: number) { this.mesh.position.copy(camera.position); this.material.uniforms.drift.value = time * .00018; }
  dispose() { this.alive = false; this.texture.dispose(); this.canalTexture.dispose(); this.mesh.geometry.dispose(); this.material.dispose(); }
}
