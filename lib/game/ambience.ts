import * as THREE from 'three';
import type { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { TrafficSimulation, type TrafficSpec, type RoadUser } from './traffic';
import { PedestrianSimulation, type Person } from './pedestrians';
import type { Collider } from './physics';
import { CrowdModel, disposeCrowdAsset as disposeShared } from './crowd-model';

type CityLife = { people: Person[]; vehicles: TrafficSpec[] };

/** One shared geometry per body part; no per-pedestrian model downloads. */
export class Ambience {
  group = new THREE.Group();
  private models: CrowdModel;
  private trafficSources: THREE.Group[] = [];
  private vehicleModels: THREE.Group[] = [];
  traffic: TrafficSimulation;
  private crowd: PedestrianSimulation;

  private constructor(data: CityLife, pedestrian: THREE.Group, colliders: Collider[]) {
    this.traffic = new TrafficSimulation(data.vehicles);
    this.crowd = new PedestrianSimulation(data.people, colliders);
    this.models = new CrowdModel(data.people, pedestrian);
    this.group.add(this.models.group);
    this.group.name = 'Shibuya street life'; this.posePeople();
  }

  static async load(loader: GLTFLoader, colliders: Collider[]) {
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
    const life = new Ambience(meta.value, people.value.scene, colliders);
    life.trafficSources = [taxi.value.scene, bus.value.scene];
    for (const v of meta.value.vehicles) {
      const model = (v.model === 'taxi' ? taxi : bus).value.scene.clone();
      model.position.set(v.x, .02, v.z); model.rotation.y = v.yaw;
      life.group.add(model); life.vehicleModels.push(model);
    }
    return life;
  }

  update(dt: number, player: RoadUser) {
    this.traffic.step(dt, this.crowd.walkers, player);
    this.crowd.update(dt, this.traffic, player);
    this.posePeople();
    this.traffic.cars.forEach((v, i) => {
      const model = this.vehicleModels[i];
      model.position.set(v.x, .02, v.z);
      model.visible = Math.abs(v.x) < 48 && Math.abs(v.z) < 48;
    });
  }

  private posePeople() { this.models.pose(this.crowd.walkers); }

  dispose() {
    this.models.dispose(); this.trafficSources.forEach(disposeShared); this.group.clear();
  }
}
