import * as THREE from 'three';
import type { Person } from './pedestrians';

export type CrowdPose = { x: number; z: number; y?: number; yaw: number; speed: number; gait: number };

/** Shared Shibuya pedestrian meshes and distance-driven limb animation. */
export class CrowdModel {
  readonly group = new THREE.Group();
  private parts: { mesh: THREE.InstancedMesh; pivot: THREE.Vector3; swing: number; local: THREE.Matrix4 }[] = [];
  private dummy = new THREE.Object3D();
  private matrix = new THREE.Matrix4();
  private limb = new THREE.Matrix4();
  private origin = new THREE.Matrix4();

  constructor(private people: Person[], private source: THREE.Group, radius = 65) {
    source.updateMatrixWorld(true);
    source.traverse(o => {
      if (!(o instanceof THREE.Mesh)) return;
      const mesh = new THREE.InstancedMesh(o.geometry, o.material, people.length);
      mesh.name = `Crowd ${o.name}`; mesh.castShadow = mesh.receiveShadow = true;
      mesh.instanceMatrix.setUsage(THREE.DynamicDrawUsage);
      const material = Array.isArray(o.material) ? o.material[0] : o.material;
      if (material.name === 'Crowd outfit') people.forEach((p, i) => mesh.setColorAt(i, new THREE.Color(p.coat)));
      mesh.boundingSphere = new THREE.Sphere(new THREE.Vector3(0, 2, 0), radius);
      this.parts.push({ mesh, pivot: new THREE.Vector3().fromArray(o.userData.pivot ?? [0, 0, 0]), swing: o.userData.swing ?? 0, local: o.matrixWorld.clone() });
      this.group.add(mesh);
    });
  }

  pose(walkers: CrowdPose[]) {
    this.people.forEach((p, i) => {
      const w = walkers[i], gait = Math.sin(w.gait) * Math.min(1, w.speed / .9);
      this.dummy.position.set(w.x, (w.y ?? 0) + .1 + Math.abs(gait) * .025, w.z);
      this.dummy.rotation.set(0, w.yaw, 0);
      this.dummy.scale.setScalar(p.scale); this.dummy.updateMatrix();
      for (const part of this.parts) {
        this.matrix.copy(this.dummy.matrix);
        if (part.swing) {
          const p = part.pivot;
          this.limb.makeTranslation(p.x, p.y, p.z).multiply(this.origin.makeRotationX(gait * .34 * part.swing)).multiply(this.origin.makeTranslation(-p.x, -p.y, -p.z));
          this.matrix.multiply(this.limb);
        }
        this.matrix.multiply(part.local); part.mesh.setMatrixAt(i, this.matrix);
      }
    });
    this.parts.forEach(p => { p.mesh.instanceMatrix.needsUpdate = true; });
  }

  dispose() {
    this.parts.forEach(p => p.mesh.dispose());
    disposeCrowdAsset(this.source); this.group.clear();
  }
}

export function disposeCrowdAsset(root: THREE.Object3D) {
  const geometries = new Set<THREE.BufferGeometry>(), materials = new Set<THREE.Material>(), textures = new Set<THREE.Texture>();
  root.traverse(o => { if (o instanceof THREE.Mesh) { geometries.add(o.geometry); (Array.isArray(o.material) ? o.material : [o.material]).forEach(m => materials.add(m)); } });
  materials.forEach(m => { Object.values(m).forEach(v => { if (v instanceof THREE.Texture) textures.add(v); }); m.dispose(); });
  textures.forEach(t => t.dispose()); geometries.forEach(g => g.dispose());
}
