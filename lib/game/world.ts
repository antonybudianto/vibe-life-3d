import * as THREE from 'three';
import { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { DRACOLoader } from 'three/addons/loaders/DRACOLoader.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/addons/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/addons/postprocessing/RenderPass.js';
import { UnrealBloomPass } from 'three/addons/postprocessing/UnrealBloomPass.js';
import { OutputPass } from 'three/addons/postprocessing/OutputPass.js';
import { moveWithCollision, resolveTime, groundHeight, followGround, canStepTo, type Collider, type WalkSurface } from './physics';
import phases from './lighting.json';
import dotonboriPhases from './dotonbori-lighting.json';
import { elevatedPitch, zoomDistance } from './camera';
import { Ambience } from './ambience';
import { CitySky } from './sky';
import { Atmosphere, type HazeLevel } from './atmosphere';
import { CanalWater, findCanalSurface } from './canal-water';
import { CanalLife } from './canal-life';

export type TravelMode = 'walk' | 'motorcycle' | 'car';
export type TimeMode = 'day' | 'evening' | 'night' | 'live';
export type MapId = 'crossing' | 'park' | 'dotonbori';
export type Status = { loading: boolean; progress: number; map: MapId; x: number; z: number; speed: number; fps: number; clock: string; phase: string; error: string | null };
type MapData = { id: MapId; name: string; spawn: [number, number, number]; bounds: [number, number, number, number]; colliders: Collider[]; surfaces?: WalkSurface[]; pedestrians?: number; cruises?: number };
type LandmarkData = { model: string; position: [number, number, number]; colliders: Collider[] };
const INITIAL: Status = { loading: true, progress: 0, map: 'crossing', x: 0, z: 10, speed: 0, fps: 0, clock: '17:30', phase: 'evening', error: null };

export class World {
  scene = new THREE.Scene();
  camera = new THREE.PerspectiveCamera(55, 1, .12, 240);
  renderer: THREE.WebGLRenderer;
  composer: EffectComposer;
  bloom: UnrealBloomPass;
  loader = new GLTFLoader();
  private draco = new DRACOLoader().setDecoderPath('/draco/').setWorkerLimit(2);
  character: THREE.Group | null = null;
  vehicles: Partial<Record<TravelMode, THREE.Group>> = {};
  environment: THREE.Group | null = null;
  private ambience: Ambience | null = null;
  private canalLife: CanalLife | null = null;
  private sky = new CitySky();
  private atmosphere = new Atmosphere();
  private movementColliders: Collider[] = [];
  data: MapData | null = null;
  player = new THREE.Vector3(0, 0, 10);
  heading = Math.PI;
  yaw = .22;
  pitch = .24;
  distance = 8.8;
  velocity = 0;
  verticalVelocity = 0;
  travel: TravelMode = 'walk';
  time: TimeMode = 'evening';
  running = false;
  paused = false;
  quality: 'high' | 'balanced' = matchMedia('(pointer: fine)').matches ? 'high' : 'balanced';
  keys = new Set<string>();
  joystick = { x: 0, y: 0 };
  pointers = new Map<number, { x: number; y: number }>();
  status = { ...INITIAL };
  private alive = true;
  private requestId = 0;
  private loadSerial = 0;
  private clock = new THREE.Clock();
  private accumulator = 0;
  private elapsed = 0;
  private frameCount = 0;
  private statsElapsed = 0;
  private lastPhase = '';
  private cleanup: (() => void)[] = [];
  private limbs: THREE.Object3D[] = [];
  private cruises: THREE.Object3D[] = [];
  private canalWater: CanalWater | null = null;
  private hemi = new THREE.HemisphereLight(0xb6c7fa, 0x625c66, 2.1);
  private sun = new THREE.DirectionalLight(0xffc99a, 3.1);
  private fill = new THREE.DirectionalLight(0x95b1ff, 1.2);
  private nightLights: THREE.PointLight[] = [];
  private envTarget: THREE.WebGLRenderTarget;
  private focus = new THREE.Vector3();
  private desired = new THREE.Vector3();
  private look = new THREE.Vector3();
  private cameraBox = new THREE.Box3();
  private ray = new THREE.Ray();
  private hit = new THREE.Vector3();
  private update: (state: Status) => void;

  constructor(private host: HTMLElement, onUpdate: (state: Status) => void) {
    this.update = onUpdate;
    this.loader.setDRACOLoader(this.draco);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    this.renderer.toneMapping = THREE.AgXToneMapping;
    this.renderer.toneMappingExposure = 1.25;
    this.renderer.shadowMap.enabled = true;
    this.renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    this.renderer.info.autoReset = false;
    this.renderer.domElement.setAttribute('aria-label', 'Shibuya Life 3D game. WASD to move, Space to jump, drag to look.');
    this.renderer.domElement.tabIndex = 0;
    host.appendChild(this.renderer.domElement);
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    const room = new RoomEnvironment();
    this.envTarget = pmrem.fromScene(room, .04);
    this.scene.environment = this.envTarget.texture;
    this.scene.environmentIntensity = .35;
    room.dispose(); pmrem.dispose();
    this.scene.background = new THREE.Color(0x8896b8);
    this.scene.fog = this.atmosphere.fog;
    this.scene.add(this.sky.mesh);
    this.sun.position.set(-22, 28, 14);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    Object.assign(this.sun.shadow.camera, { left: -32, right: 32, top: 32, bottom: -32, near: 1, far: 100 });
    this.sun.shadow.normalBias = .035;
    this.sun.shadow.bias = -.00015;
    this.fill.position.set(25, 15, -15);
    this.scene.add(this.hemi, this.sun, this.sun.target, this.fill);
    for (const [x, z] of [[-15, -10], [17, -11], [-10, 12], [15, 14]]) {
      const light = new THREE.PointLight(0xffae60, 30, 15, 2);
      light.position.set(x, 3, z); this.nightLights.push(light); this.scene.add(light);
    }
    // The bloom pipeline renders offscreen, so it needs its own antialiasing.
    const postTarget = new THREE.WebGLRenderTarget(1, 1, { type: THREE.HalfFloatType, samples: Math.min(4, this.renderer.capabilities.maxSamples) });
    this.composer = new EffectComposer(this.renderer, postTarget);
    this.composer.addPass(new RenderPass(this.scene, this.camera));
    this.bloom = new UnrealBloomPass(new THREE.Vector2(1, 1), .20, .4, 1.3);
    this.composer.addPass(this.bloom);
    this.composer.addPass(new OutputPass());
    this.bindInputs();
    const resize = new ResizeObserver(() => this.resize()); resize.observe(host);
    this.cleanup.push(() => resize.disconnect());
    this.resize(); this.updateCamera(1); this.animate();
    void this.initialize();
  }

  private emit() { if (this.alive) this.update({ ...this.status }); }
  private prep(group: THREE.Group, world = false) {
    // GLTFLoader decomposes node transforms. Compose them before freezing static meshes.
    group.updateMatrixWorld(true);
    group.traverse((o) => {
      if (o instanceof THREE.Mesh) {
        o.castShadow = !o.name.includes('Crosswalk') && !o.name.includes('Glazing'); o.receiveShadow = true;
        if (world) o.matrixAutoUpdate = false;
        const materials = Array.isArray(o.material) ? o.material : [o.material];
        for (const m of materials) if (m instanceof THREE.MeshStandardMaterial) {
          this.atmosphere.applyTo(m);
          m.envMapIntensity = .55;
          if (m.name.includes('Glazing')) { m.depthWrite = false; o.castShadow = false; }
          const roadPaint = m.userData.surface_role === 'road-marking';
          const roadRepair = m.name === 'Asphalt repairs';
          if (roadPaint || roadRepair) {
            // Thin road overlays need depth bias at maximum zoom. Repairs draw
            // before paint; depth testing keeps both behind vehicles and people.
            m.polygonOffset = true; m.polygonOffsetFactor = -2; m.polygonOffsetUnits = -4;
            m.depthWrite = false; o.renderOrder = roadPaint ? 2 : 1; o.castShadow = false;
          }
          m.aoMapIntensity = .85;
          if (m.aoMap) m.aoMap.anisotropy = Math.min(4, this.renderer.capabilities.getMaxAnisotropy());
          m.userData.baseEmission = m.userData.base_emission ?? m.emissiveIntensity;
        }
      }
    });
    return group;
  }

  private async loadBakedLighting(group: THREE.Group) {
    const textures = new Map<string, Promise<THREE.Texture>>();
    const loaded: THREE.Texture[] = [];
    const materials = new Set<THREE.MeshStandardMaterial>();
    group.traverse((o) => {
      if (o instanceof THREE.Mesh) for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        if (m instanceof THREE.MeshStandardMaterial && m.userData.bakedLightmap) materials.add(m);
      }
    });
    try {
      await Promise.all([...materials].map(async (m) => {
        const path = m.userData.bakedLightmap as string;
        if (!textures.has(path)) textures.set(path, new THREE.TextureLoader().loadAsync(path).then((texture) => {
          texture.flipY = false; texture.channel = 1; texture.colorSpace = THREE.SRGBColorSpace;
          texture.anisotropy = Math.min(4, this.renderer.capabilities.getMaxAnisotropy());
          loaded.push(texture); return texture;
        }));
        m.lightMap = await textures.get(path)!;
        m.lightMapIntensity = m.userData.bakedLightmapScale ?? 4;
        m.needsUpdate = true;
      }));
    } catch (error) { loaded.forEach((texture) => texture.dispose()); throw error; }
  }

  private async initialize() {
    try {
      await this.sky.load();
      if (!this.alive) return;
      const asset = await this.loader.loadAsync('/models/character.glb', (e) => {
        this.status.progress = e.total ? Math.round(e.loaded / e.total * 25) : 10; this.emit();
      });
      if (!this.alive) { this.disposeObject(asset.scene); return; }
      this.character = this.prep(asset.scene); this.scene.add(this.character);
      this.limbs = ['Arm_L', 'Arm_R', 'Leg_L', 'Leg_R'].map((n) => this.character!.getObjectByName(n)!);
      this.status.progress = 25; this.emit();
      const requestedMap = new URLSearchParams(window.location.search).get('map');
      await this.switchMap(requestedMap === 'dotonbori' || requestedMap === 'park' ? requestedMap : 'crossing');
    } catch (e) { this.fail(e); }
  }

  async switchMap(id: MapId) {
    const serial = ++this.loadSerial;
    this.clearInput();
    this.status.loading = true; this.status.error = null; this.status.progress = 28; this.emit();
    try {
      const [asset, data] = await Promise.all([
        this.loader.loadAsync(`/models/${id}.glb`, (e) => {
          if (serial !== this.loadSerial) return;
          this.status.progress = e.total ? 28 + Math.round(e.loaded / e.total * 65) : 45; this.emit();
        }),
        fetch(`/models/${id}.json`).then((r) => { if (!r.ok) throw new Error('Map description unavailable'); return r.json() as Promise<MapData>; }),
      ]);
      let life: Ambience | null = null;
      let canalLife: CanalLife | null = null;
      let waterNormals: THREE.Texture | null = null;
      try {
        await this.loadBakedLighting(asset.scene);
        if (id === 'dotonbori') {
          waterNormals = await new THREE.TextureLoader().loadAsync('/textures/dotonbori-water-normal.png');
          canalLife = await CanalLife.load(this.loader, data);
        }
        if (id === 'crossing') {
          const landmarkData = await fetch('/models/hachiko.json').then((r) => { if (!r.ok) throw new Error('Landmark unavailable'); return r.json() as Promise<LandmarkData>; });
          const landmark = await this.loader.loadAsync('/models/hachiko.glb');
          landmark.scene.position.fromArray(landmarkData.position); asset.scene.add(landmark.scene);
          for (const x of [-4.6, 4.6]) {
            const lantern = new THREE.PointLight(0xffba73, 12, 7, 2);
            lantern.position.set(x, 3.2, 1.8); lantern.userData.plazaPower = 12; landmark.scene.add(lantern);
          }
          data.colliders.push(...landmarkData.colliders);
          life = await Ambience.load(this.loader, data.colliders);
        }
      }
      catch (error) { this.disposeObject(asset.scene); life?.dispose(); canalLife?.dispose(); waterNormals?.dispose(); throw error; }
      if (!this.alive || serial !== this.loadSerial) { this.disposeObject(asset.scene); life?.dispose(); canalLife?.dispose(); waterNormals?.dispose(); return; }
      const next = this.prep(asset.scene, true);
      this.canalWater?.dispose(); this.canalWater = null;
      if (this.environment) { this.scene.remove(this.environment); this.disposeObject(this.environment); }
      if (this.ambience) { this.scene.remove(this.ambience.group); this.ambience.dispose(); }
      if (this.canalLife) { this.scene.remove(this.canalLife.group); this.canalLife.dispose(); }
      this.ambience = life;
      this.canalLife = canalLife;
      if (life) this.scene.add(this.prep(life.group));
      if (canalLife) this.scene.add(this.prep(canalLife.group));
      this.environment = next; this.data = data; this.scene.add(next);
      this.cruises = [];
      next.traverse((o) => { if (o.userData.cruise) this.cruises.push(o); });
      const water = findCanalSurface(next);
      if (water instanceof THREE.Mesh && waterNormals) {
        this.canalWater = new CanalWater(water, waterNormals);
        this.atmosphere.applyTo(this.canalWater.mesh.material as THREE.ShaderMaterial);
        this.scene.add(this.canalWater.mesh);
      }
      else waterNormals?.dispose();
      this.movementColliders = [...data.colliders, ...(life?.traffic.colliders ?? [])];
      this.player.fromArray(data.spawn); this.velocity = 0; this.verticalVelocity = 0; this.heading = Math.PI;
      this.yaw = id === 'crossing' ? .22 : id === 'dotonbori' ? .10 : .02;
      if (id === 'dotonbori') { this.pitch = .30; this.distance = 9; }
      this.status.map = id; this.status.loading = false; this.status.progress = 100;
      this.lastPhase = ''; this.applyTime(); this.updateCamera(1); this.emit();
    } catch (e) { if (serial === this.loadSerial) this.fail(e); }
  }

  async setTravel(mode: TravelMode) {
    if (this.status.loading) return;
    if (mode !== 'walk' && !this.vehicles[mode]) {
      this.status.loading = true; this.status.progress = 25; this.emit();
      try {
        const asset = await this.loader.loadAsync(`/models/${mode}.glb`);
        if (!this.alive) { this.disposeObject(asset.scene); return; }
        this.vehicles[mode] = this.prep(asset.scene); this.scene.add(asset.scene);
      } catch (e) { this.fail(e); return; }
      this.status.loading = false; this.status.progress = 100; this.emit();
    }
    this.travel = mode; this.velocity = 0; this.verticalVelocity = 0;
    this.lastPhase = ''; this.applyTime();
    // A larger vehicle cannot spawn inside a wall when changing from walking.
    if (this.data) {
      const p = moveWithCollision(this.player.x, this.player.z, 0, 0, this.radius(), this.movementColliders, this.data.bounds);
      this.player.x = p.x; this.player.z = p.z;
    }
    this.player.y = groundHeight(this.player.x, this.player.z, this.data?.surfaces);
    for (const [name, object] of Object.entries(this.vehicles)) object!.visible = name === mode;
    if (this.character) this.character.visible = mode !== 'car';
    this.clearInput();
  }
  setTime(mode: TimeMode) { this.time = mode; this.lastPhase = ''; this.applyTime(); this.emit(); }
  setHaze(level: HazeLevel) { this.atmosphere.setLevel(level); }
  setRunning(value: boolean) { this.running = value; }
  setPaused(value: boolean) { this.paused = value; this.clearInput(); }
  zoom(delta: number) { this.distance = zoomDistance(this.distance, delta); }
  recenter() { this.yaw = this.heading - Math.PI; this.pitch = .30; }
  jump() { if (!this.paused && !this.status.loading && this.travel === 'walk' && this.player.y <= groundHeight(this.player.x, this.player.z, this.data?.surfaces) + .025) this.verticalVelocity = 5.3; }
  setQuality(value: 'high' | 'balanced') { this.quality = value; this.bloom.enabled = value === 'high'; this.resize(); }
  private radius() { return this.travel === 'car' ? 1.7 : this.travel === 'motorcycle' ? .95 : .32; }
  private clearInput() { this.keys.clear(); this.joystick.x = 0; this.joystick.y = 0; this.pointers.clear(); }

  private bindInputs() {
    const canvas = this.renderer.domElement;
    const on = (target: EventTarget, name: string, fn: EventListener, options?: AddEventListenerOptions) => {
      target.addEventListener(name, fn, options); this.cleanup.push(() => target.removeEventListener(name, fn, options));
    };
    on(window, 'keydown', ((e: KeyboardEvent) => {
      if (this.paused || e.ctrlKey || e.metaKey || e.altKey || (e.target instanceof HTMLElement && e.target.closest('input,select,textarea,[role="dialog"],[role="listbox"],[role="combobox"]'))) return;
      const code = e.code;
      if (['KeyW', 'KeyA', 'KeyS', 'KeyD', 'ArrowUp', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'Space', 'ShiftLeft', 'ShiftRight', 'KeyR'].includes(code)) {
        if (code === 'Space' && e.target instanceof HTMLElement && e.target.closest('button')) return;
        e.preventDefault(); this.keys.add(code);
        if (code === 'Space' && !e.repeat) this.jump();
        if (code === 'KeyR') this.recenter();
      }
    }) as EventListener);
    on(window, 'keyup', ((e: KeyboardEvent) => { this.keys.delete(e.code); }) as EventListener);
    on(window, 'blur', (() => this.clearInput()) as EventListener);
    on(document, 'visibilitychange', (() => { this.clearInput(); this.clock.getDelta(); }) as EventListener);
    on(canvas, 'contextmenu', ((e: Event) => e.preventDefault()) as EventListener);
    on(canvas, 'wheel', ((e: WheelEvent) => { e.preventDefault(); if (!this.paused) this.zoom(e.deltaY * .009); }) as EventListener, { passive: false });
    on(canvas, 'pointerdown', ((e: PointerEvent) => {
      if (this.paused) return;
      canvas.focus({ preventScroll: true }); canvas.setPointerCapture(e.pointerId);
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    }) as EventListener);
    on(canvas, 'pointermove', ((e: PointerEvent) => {
      const old = this.pointers.get(e.pointerId); if (!old || this.paused) return;
      if (this.pointers.size === 2) {
        const other = [...this.pointers.entries()].find(([id]) => id !== e.pointerId)![1];
        const before = Math.hypot(old.x - other.x, old.y - other.y);
        const after = Math.hypot(e.clientX - other.x, e.clientY - other.y);
        this.zoom((before - after) * .025);
      } else {
        this.yaw -= (e.clientX - old.x) * .005;
        this.pitch = THREE.MathUtils.clamp(this.pitch + (e.clientY - old.y) * .004, .12, 1.02);
      }
      this.pointers.set(e.pointerId, { x: e.clientX, y: e.clientY });
    }) as EventListener);
    for (const type of ['pointerup', 'pointercancel', 'lostpointercapture']) on(canvas, type, ((e: PointerEvent) => { this.pointers.delete(e.pointerId); }) as EventListener);
    on(canvas, 'webglcontextlost', ((e: Event) => { e.preventDefault(); this.status.error = 'Graphics paused. Reload to restore the world.'; this.emit(); }) as EventListener);
  }

  private resize() {
    const w = this.host.clientWidth, h = this.host.clientHeight;
    this.renderer.setPixelRatio(Math.min(devicePixelRatio, this.quality === 'high' ? 2 : 1.35));
    this.renderer.setSize(w, h); this.composer.setPixelRatio(this.renderer.getPixelRatio()); this.composer.setSize(w, h);
    this.camera.aspect = w / Math.max(h, 1); this.camera.updateProjectionMatrix();
    this.bloom.enabled = this.quality === 'high';
  }

  private applyTime() {
    const p = resolveTime(this.time, new Date());
    this.status.clock = p.clock; this.status.phase = p.phase;
    const key = `${p.phase}-${p.blend.toFixed(2)}`; if (key === this.lastPhase) return; this.lastPhase = key;
    const palette = this.data?.id === 'dotonbori' ? dotonboriPhases : phases;
    const a = palette[p.phase], b = palette[p.next]; const t = p.blend;
    const sky = new THREE.Color(a.sky).lerp(new THREE.Color(b.sky), t);
    this.scene.background = sky;
    this.sky.setTime(p.phase, p.next, t, palette, this.data?.id === 'dotonbori');
    (this.scene.fog as THREE.Fog).color.copy(sky);
    this.hemi.color.copy(sky).lerp(new THREE.Color(0xc5d3ef), .25);
    this.hemi.groundColor.set(0x3b303d);
    this.sun.color.set(a.sun).lerp(new THREE.Color(b.sun), t);
    this.sun.intensity = THREE.MathUtils.lerp(a.power, b.power, t);
    this.hemi.intensity = THREE.MathUtils.lerp(a.ambient, b.ambient, t);
    this.fill.intensity = this.hemi.intensity * .18;
    this.scene.environmentIntensity = THREE.MathUtils.lerp(a.environment, b.environment, t);
    this.renderer.toneMappingExposure = THREE.MathUtils.lerp(a.exposure, b.exposure, t);
    const emission = THREE.MathUtils.lerp(a.emission, b.emission, t);
    const seen = new Set<THREE.Material>();
    this.scene.traverse((o) => {
      if (o instanceof THREE.PointLight && o.userData.plazaPower) o.intensity = o.userData.plazaPower * emission;
      if (o instanceof THREE.Mesh) for (const m of Array.isArray(o.material) ? o.material : [o.material]) {
        if (m instanceof THREE.MeshStandardMaterial && !seen.has(m)) {
          seen.add(m); m.emissiveIntensity = (m.userData.baseEmission ?? m.emissiveIntensity) * emission;
          if (m.lightMap) m.lightMapIntensity = (m.userData.bakedLightmapScale ?? 4) * emission;
        }
      }
    });
    this.nightLights.forEach((l) => l.intensity = 22 * emission);
  }

  private step(dt: number) {
    if (!this.data || !this.character || this.paused || this.status.loading || this.status.error) return;
    this.ambience?.update(dt, { x: this.player.x, z: this.player.z, radius: this.radius() });
    this.canalLife?.update(dt, { x: this.player.x, y: this.player.y, z: this.player.z, radius: this.radius() });
    this.movementColliders = [...this.data.colliders, ...(this.ambience?.traffic.colliders ?? [])];
    const oldFloor = groundHeight(this.player.x, this.player.z, this.data.surfaces);
    const left = this.keys.has('KeyA') || this.keys.has('ArrowLeft');
    const right = this.keys.has('KeyD') || this.keys.has('ArrowRight');
    const forward = this.keys.has('KeyW') || this.keys.has('ArrowUp');
    const backward = this.keys.has('KeyS') || this.keys.has('ArrowDown');
    let ix = Number(right) - Number(left) + this.joystick.x;
    let iz = Number(backward) - Number(forward) + this.joystick.y;
    const len = Math.hypot(ix, iz); if (len > 1) { ix /= len; iz /= len; }
    let dx = 0, dz = 0;
    if (this.travel === 'walk') {
      const sprint = this.running || this.keys.has('ShiftLeft') || this.keys.has('ShiftRight');
      const speed = sprint ? 4.8 : 2.1;
      dx = (ix * Math.cos(this.yaw) + iz * Math.sin(this.yaw)) * speed * dt;
      dz = (-ix * Math.sin(this.yaw) + iz * Math.cos(this.yaw)) * speed * dt;
      this.velocity = Math.hypot(dx, dz) / dt;
      if (len > .05) {
        const target = Math.atan2(dx, dz);
        this.heading += Math.atan2(Math.sin(target - this.heading), Math.cos(target - this.heading)) * Math.min(dt * 12, 1);
      }
    } else {
      const max = this.travel === 'car' ? 12 : 10;
      this.velocity += -iz * 7 * dt;
      if (Math.abs(iz) < .08) this.velocity *= Math.exp(-2.1 * dt);
      this.velocity = THREE.MathUtils.clamp(this.velocity, -max * .35, max);
      this.heading -= ix * dt * 1.7 * THREE.MathUtils.clamp(this.velocity / 3, -1, 1);
      dx = Math.sin(this.heading) * this.velocity * dt;
      dz = Math.cos(this.heading) * this.velocity * dt;
    }
    const p = moveWithCollision(this.player.x, this.player.z, dx, dz, this.radius(), this.movementColliders, this.data.bounds);
    if (!canStepTo(this.player.y, oldFloor, groundHeight(p.x, p.z, this.data.surfaces))) {
      p.x = this.player.x; p.z = this.player.z;
    }
    if (this.travel !== 'walk' && Math.hypot(p.x - this.player.x, p.z - this.player.z) < Math.hypot(dx, dz) * .3) this.velocity *= .7;
    this.player.x = p.x; this.player.z = p.z;
    const floor = groundHeight(p.x, p.z, this.data.surfaces);
    const vertical = this.travel === 'walk' ? followGround(this.player.y, this.verticalVelocity, oldFloor, floor, dt) : { y: floor, velocity: 0 };
    this.player.y = vertical.y; this.verticalVelocity = vertical.velocity;
    for (const boat of this.cruises) {
      // Root offsets remain in the safe interval between bridges; no recycling pops.
      const phase = this.elapsed * .09 + Number(boat.userData.cruiseIndex) * Math.PI;
      boat.position.z = Math.sin(phase) * 8;
      boat.position.y = Math.sin(this.elapsed * 1.2 + phase) * .035;
      boat.updateMatrixWorld(true);
    }
  }

  private pose() {
    if (!this.character) return;
    this.character.position.copy(this.player); this.character.rotation.y = this.heading;
    const moving = this.travel === 'walk' && !this.paused && !this.status.loading ? Math.min(this.velocity / 2.1, 1) : 0;
    const phase = this.elapsed * (this.velocity > 3 ? 12 : 8);
    const swing = Math.sin(phase) * .58 * moving;
    this.character.position.y += moving * Math.abs(Math.sin(phase)) * .035;
    for (let i = 0; i < this.limbs.length; i++) if (this.limbs[i]) {
      this.limbs[i].rotation.x = swing * (i === 0 || i === 3 ? 1 : -1);
    }
    if (this.travel === 'motorcycle') {
      this.character.position.y = this.player.y + .67; this.character.scale.setScalar(.83);
      this.limbs.forEach((o, i) => { if (o) o.rotation.x = i < 2 ? -1.12 : -1.0; });
    } else this.character.scale.setScalar(1);
    const vehicle = this.vehicles[this.travel];
    if (vehicle) { vehicle.position.copy(this.player); vehicle.rotation.y = this.heading; }
  }

  private updateCamera(dt: number) {
    const height = this.travel === 'walk' ? 1.35 : 1.4;
    this.focus.copy(this.player); this.focus.y += height;
    const distance = this.distance + (this.travel === 'car' ? 2 : 0);
    const pitch = elevatedPitch(this.pitch, this.distance);
    this.desired.set(Math.sin(this.yaw) * Math.cos(pitch), Math.sin(pitch), Math.cos(this.yaw) * Math.cos(pitch)).multiplyScalar(distance).add(this.focus);
    // Clip the spring arm against building volumes; remain outside the avatar.
    if (this.data) {
      const dir = this.desired.clone().sub(this.focus).normalize(); this.ray.set(this.focus, dir);
      let nearest = distance;
      for (const c of this.data.colliders) {
        if (c.cameraIgnore) continue;
        const halfX = c.cameraRadius ?? c.halfX, halfZ = c.cameraRadius ?? c.halfZ;
        this.cameraBox.min.set(c.x - halfX - .2, c.cameraMinY ?? -.5, c.z - halfZ - .2);
        this.cameraBox.max.set(c.x + halfX + .2, c.height ?? 45, c.z + halfZ + .2);
        if (this.ray.intersectBox(this.cameraBox, this.hit)) nearest = Math.min(nearest, Math.max(1.25, this.focus.distanceTo(this.hit) - .3));
      }
      this.desired.copy(this.focus).addScaledVector(dir, nearest);
    }
    this.camera.position.lerp(this.desired, 1 - Math.exp(-14 * dt));
    this.look.copy(this.focus); this.look.y += 1.0;
    this.camera.lookAt(this.look);
  }

  private animate = () => {
    if (!this.alive) return;
    this.requestId = requestAnimationFrame(this.animate);
    const realDelta = this.clock.getDelta();
    const dt = Math.min(realDelta, .05);
    if (document.hidden) return;
    this.elapsed += this.paused ? 0 : dt;
    this.accumulator += dt;
    while (this.accumulator >= 1 / 60) { this.step(1 / 60); this.accumulator -= 1 / 60; }
    this.pose(); this.updateCamera(dt);
    this.sky.update(this.camera, this.elapsed);
    this.atmosphere.update(this.elapsed);
    this.canalWater?.update(this.elapsed, this.camera, this.sun);
    // Follow the player with a bounded shadow camera instead of shadowing the entire map.
    this.sun.position.set(this.player.x - 22, 28, this.player.z + 14);
    this.sun.target.position.copy(this.player);
    this.renderer.info.reset();
    if (this.quality === 'high') this.composer.render(); else this.renderer.render(this.scene, this.camera);
    this.frameCount++; this.statsElapsed += realDelta;
    if (this.statsElapsed >= .5) {
      this.status.x = this.player.x; this.status.z = this.player.z;
      this.status.speed = Math.round(Math.abs(this.velocity) * 3.6);
      this.status.fps = Math.round(this.frameCount / this.statsElapsed);
      this.frameCount = 0; this.statsElapsed = 0; this.applyTime(); this.emit();
      this.renderer.domElement.dataset.position = `${this.player.x.toFixed(2)},${this.player.y.toFixed(2)},${this.player.z.toFixed(2)}`;
      this.renderer.domElement.dataset.mode = this.travel;
      this.renderer.domElement.dataset.map = this.status.map;
      this.renderer.domElement.dataset.camera = `${this.yaw.toFixed(2)},${this.pitch.toFixed(2)},${this.distance.toFixed(2)}`;
      this.renderer.domElement.dataset.drawCalls = String(this.renderer.info.render.calls);
      this.renderer.domElement.dataset.haze = this.atmosphere.level;
      this.renderer.domElement.dataset.atmosphereTime = this.elapsed.toFixed(2);
      this.renderer.domElement.dataset.streetLife = this.ambience ? '74 pedestrians, 5 vehicles' : this.canalLife ? `${this.canalLife.simulation.walkers.length} walking visitors, 2 river cruises` : 'none';
      // Visible diagnostics for local scene and animation checks.
      this.renderer.domElement.dataset.canalCrowd = this.canalLife ? JSON.stringify(this.canalLife.simulation.walkers.map(w => ({x:+w.x.toFixed(2),y:+w.y.toFixed(2),z:+w.z.toFixed(2),gait:+w.gait.toFixed(2),activity:w.activity,crossings:w.crossings}))) : '';
      this.renderer.domElement.dataset.crossingPhase = this.ambience?.traffic.phase ?? 'none';
    }
  };

  private fail(e: unknown) {
    console.error('World load failed', e);
    this.status.loading = false; this.status.error = 'We couldn’t load the world. Check your connection and try again.'; this.emit();
  }
  private disposeObject(object: THREE.Object3D) {
    const geometries = new Set<THREE.BufferGeometry>(), materials = new Set<THREE.Material>();
    object.traverse((o) => { if (o instanceof THREE.Mesh) { geometries.add(o.geometry); (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => materials.add(m)); } });
    geometries.forEach((g) => g.dispose());
    materials.forEach((m) => { for (const v of Object.values(m)) if (v instanceof THREE.Texture) v.dispose(); m.dispose(); });
  }
  dispose() {
    this.alive = false; this.loadSerial++; cancelAnimationFrame(this.requestId);
    this.canalWater?.dispose(); this.canalWater = null;
    if (this.ambience) { this.scene.remove(this.ambience.group); this.ambience.dispose(); this.ambience = null; }
    if (this.canalLife) { this.scene.remove(this.canalLife.group); this.canalLife.dispose(); this.canalLife = null; }
    this.scene.remove(this.sky.mesh); this.sky.dispose();
    this.cleanup.forEach((f) => f()); this.disposeObject(this.scene); this.scene.clear();
    this.sun.shadow.dispose(); this.envTarget.dispose(); this.bloom.dispose(); this.composer.dispose();
    this.draco.dispose(); this.renderer.dispose(); this.renderer.domElement.remove();
  }
}
