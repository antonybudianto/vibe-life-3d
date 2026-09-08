import type { GLTFLoader } from 'three/addons/loaders/GLTFLoader.js';
import { CrowdModel, disposeCrowdAsset } from './crowd-model';
import { CanalPedestrianSimulation, type CanalMap } from './canal-pedestrians';

export class CanalLife {
  readonly simulation: CanalPedestrianSimulation;
  readonly group;
  private constructor(private models: CrowdModel, simulation: CanalPedestrianSimulation) {
    this.simulation=simulation;this.group=models.group;this.group.name='Dotonbori walking visitors';
    models.pose(simulation.walkers);
  }
  static async load(loader: GLTFLoader, map: CanalMap) {
    const asset=await loader.loadAsync('/models/pedestrian.glb');
    try {
      const simulation=new CanalPedestrianSimulation(map);
      return new CanalLife(new CrowdModel(simulation.people,asset.scene,78),simulation);
    } catch(error) { disposeCrowdAsset(asset.scene);throw error; }
  }
  update(dt: number, player: {x:number;y:number;z:number;radius:number}) {
    this.simulation.update(dt,player);this.models.pose(this.simulation.walkers);
  }
  dispose(){this.models.dispose();}
}
