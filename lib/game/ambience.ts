import * as THREE from 'three';
import type { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { pedestrianPose, TrafficSimulation, type TrafficSpec, type RoadUser } from './traffic';

type Person = { a: [number, number]; b: [number, number]; offset: number; speed: number; scale: number; coat: string };
type CityLife = { people: Person[]; vehicles: TrafficSpec[] };

/** One shared geometry per body part; no per-pedestrian model downloads. */
export class Ambience {
  group = new THREE.Group();
  private parts: { mesh: THREE.InstancedMesh; pivot: THREE.Vector3; swing: number; local: THREE.Matrix4 }[] = [];
  private dummy = new THREE.Object3D();
  private matrix = new THREE.Matrix4();
  private limb = new THREE.Matrix4();
  private origin = new THREE.Matrix4();
  private trafficSources: THREE.Group[] = [];
  private vehicleModels: THREE.Group[] = [];
  traffic: TrafficSimulation;
  private elapsed = 0;
  private people: RoadUser[] = [];

  private constructor(private data: CityLife, private pedestrian: THREE.Group) {
    this.traffic = new TrafficSimulation(data.vehicles);
    pedestrian.updateMatrixWorld(true);
    pedestrian.traverse((source) => {
      if (!(source instanceof THREE.Mesh)) return;
      const mesh = new THREE.InstancedMesh(source.geometry, source.material, data.people.length);
      mesh.name = `Crowd ${source.name}`; mesh.castShadow = true; mesh.receiveShadow = true;
      mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      const mat = Array.isArray(source.material) ? source.material[0] : source.material;
      if (mat.name === 'Crowd outfit') data.people.forEach((p, i) => mesh.setColorAt(i, new THREE.Color(p.coat)));
      // The crowd walks within a fixed 90m block; keep one conservative bound.
      mesh.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 1, 0), 65);
      this.parts.push({ mesh, pivot: new THREE.Vector3().fromArray(source.userData.pivot ?? [0, 0, 0]), swing: source.userData.swing ?? 0, local: source.matrixWorld.clone() });
      this.group.add(mesh);
    });
    this.group.name = 'Shibuya street life'; this.posePeople();
  }

  static async load(loader: GLTFLoader) {
    // Settle every request so a failed load also disposes successful siblings.
    const results = await Promise.allSettled([
      fetch('/models/crossing-life.json').then((r) => { if (!r.ok) throw new Error('Street life unavailable'); return r.json() as Promise<CityLife>; }),
      loader.loadAsync('/models/pedestrian.glb'), loader.loadAsync('/models/taxi.glb'), loader.loadAsync('/models/citybus.glb'),
    ]);
    if (results.some((r) => r.status === 'rejected')) {
      results.slice(1).forEach((r) => { if (r.status === 'fulfilled' && 'scene' in r.value) disposeShared(r.value.scene); });
      throw new Error('Could not load street life');
    }
    const [meta, people, taxi, bus] = results as [PromiseFulfilledResult<CityLife>, PromiseFulfilledResult<Awaited<ReturnType<GLTFLoader['loadAsync']>>>, PromiseFulfilledResult<Awaited<ReturnType<GLTFLoader['loadAsync']>>>, PromiseFulfilledResult<Awaited<ReturnType<GLTFLoader['loadAsync']>>>];
    const life = new Ambience(meta.value, people.value.scene);
    life.trafficSources = [taxi.value.scene, bus.value.scene];
    for (const v of meta.value.vehicles) {
      const model = (v.model === 'taxi' ? taxi : bus).value.scene.clone();
      model.position.set(v.x, .02, v.z); model.rotation.y = v.yaw;
      life.group.add(model); life.vehicleModels.push(model);
    }
    return life;
  }

  update(dt: number, player: RoadUser) {
    this.elapsed += dt;
    this.traffic.step(dt, this.people, player);
    this.posePeople();
    this.traffic.cars.forEach((v, i) => {
      const model = this.vehicleModels[i];
      model.position.set(v.x, .02, v.z);
      model.visible = Math.abs(v.x) < 48 && Math.abs(v.z) < 48;
    });
  }

  private posePeople() {
    this.people.length = 0;
    this.data.people.forEach((p, i) => {
      const pose = pedestrianPose(p, this.traffic.pedestrianWave, this.traffic.pedestrianTime);
      const gait = pose.moving ? Math.sin(this.elapsed * pose.speed * 7.5 + p.offset * Math.PI * 8) : 0;
      this.people.push({ x: pose.x, z: pose.z, radius: .35 * p.scale });
      this.dummy.position.set(pose.x, .1 + Math.abs(gait) * .025, pose.z);
      this.dummy.rotation.set(0, pose.yaw, 0);
      this.dummy.scale.setScalar(p.scale); this.dummy.updateMatrix();
      for (const part of this.parts) {
        this.matrix.copy(this.dummy.matrix);
        if (part.swing) {
          const v = part.pivot;
          this.limb.makeTranslation(v.x, v.y, v.z).multiply(this.origin.makeRotationX(gait * .34 * part.swing)).multiply(this.origin.makeTranslation(-v.x, -v.y, -v.z));
          this.matrix.multiply(this.limb);
        }
        this.matrix.multiply(part.local); part.mesh.setMatrixAt(i, this.matrix);
      }
    });
    for (const part of this.parts) part.mesh.instanceMatrix.needsUpdate = true;
  }

  dispose() {
    for (const part of this.parts) part.mesh.dispose();
    disposeShared(this.pedestrian); this.trafficSources.forEach(disposeShared); this.group.clear();
  }
}

function disposeShared(root: THREE.Object3D) {
  const geometries = new Set<THREE.BufferGeometry>(), materials = new Set<THREE.Material>();
  root.traverse((o) => { if (o instanceof THREE.Mesh) { geometries.add(o.geometry); (Array.isArray(o.material) ? o.material : [o.material]).forEach((m) => materials.add(m)); } });
  geometries.forEach((g) => g.dispose()); materials.forEach((m) => m.dispose());
}
