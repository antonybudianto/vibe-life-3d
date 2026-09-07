import type { Collider } from './physics';

export type TrafficSpec = { model: 'taxi' | 'citybus'; x: number; z: number; yaw: number };
export type RoadUser = { x: number; z: number; radius: number; crossing?: boolean };
export type TrafficCar = TrafficSpec & { speed: number; dx: number; dz: number; halfLength: number; halfWidth: number };
export type CrossingPhase = 'north-south' | 'east-west' | 'pedestrians' | 'clear';

/** Small left-hand traffic simulation; shared by movement, collisions and signals. */
export class TrafficSimulation {
  cars: TrafficCar[];
  phase: CrossingPhase = 'north-south';
  phaseTime = 0;
  pedestrianTime = 0;
  pedestrianWave = 0;
  private next = 1;
  private sequence: CrossingPhase[] = ['north-south', 'east-west', 'pedestrians'];

  constructor(specs: TrafficSpec[]) {
    this.cars = specs.map((v) => ({ ...v, speed: 0, dx: Math.round(Math.sin(v.yaw)), dz: Math.round(Math.cos(v.yaw)), halfLength: v.model === 'citybus' ? 3.65 : 2.35, halfWidth: v.model === 'citybus' ? 1.225 : .96 }));
  }

  get colliders(): Collider[] {
    return this.cars.filter((v) => Math.abs(v.x) < 48 && Math.abs(v.z) < 48).map((v) => ({ x: v.x, z: v.z, halfX: v.dx ? v.halfLength : v.halfWidth, halfZ: v.dz ? v.halfLength : v.halfWidth, height: v.model === 'citybus' ? 3.2 : 1.9 }));
  }

  step(dt: number, people: RoadUser[], player: RoadUser) {
    if (dt <= 0) return;
    // Bound each update, including after a background-tab pause.
    dt = Math.min(dt, 1 / 30);
    this.phaseTime += dt;
    const occupied = people.some(p=>p.crossing) || this.cars.some((v) => Math.abs(v.x) < 12 + v.halfLength * Math.abs(v.dx) && Math.abs(v.z) < 12 + v.halfLength * Math.abs(v.dz));
    if (this.phase === 'clear') {
      if (this.phaseTime >= 2 && !occupied) {
        this.phase = this.sequence[this.next]; this.next = (this.next + 1) % 3; this.phaseTime = 0;
        if (this.phase === 'pedestrians') { this.pedestrianTime = 0; this.pedestrianWave++; }
      }
    } else if (this.phaseTime >= (this.phase === 'pedestrians' ? 27 : 16)) {
      this.phase = 'clear'; this.phaseTime = 0;
    }
    if (this.phase === 'pedestrians') this.pedestrianTime = this.phaseTime;

    // Snapshot positions: vehicle following must not depend on array order.
    const before = this.cars.map((v) => ({ ...v }));
    this.cars.forEach((v, index) => {
      const along = v.x * v.dx + v.z * v.dz;
      let gap = Infinity;
      const green = (v.dz !== 0 && this.phase === 'north-south') || (v.dx !== 0 && this.phase === 'east-west');
      const stop = -13.4 - v.halfLength;
      // Cars that already passed the stop line finish clearing the junction.
      if (!green && along <= stop + .02) gap = Math.min(gap, stop - along);
      for (const [i, other] of before.entries()) {
        if (i === index || other.dx !== v.dx || other.dz !== v.dz) continue;
        const ahead = (other.x - v.x) * v.dx + (other.z - v.z) * v.dz;
        if (ahead > 0) gap = Math.min(gap, ahead - other.halfLength - v.halfLength - 1.2);
      }
      for (const other of [...people, player]) {
        const ax = other.x - v.x, az = other.z - v.z;
        const ahead = ax * v.dx + az * v.dz;
        const lateral = Math.abs(ax * v.dz - az * v.dx);
        if (ahead >= 0 && lateral < v.halfWidth + other.radius + .35) gap = Math.min(gap, ahead - v.halfLength - other.radius - .65);
      }
      const cruise = v.model === 'citybus' ? 4.4 : 5.5;
      const target = Math.min(cruise, Math.sqrt(Math.max(0, 2 * 5 * (gap - .05))));
      v.speed += Math.max(-6 * dt, Math.min(2.3 * dt, target - v.speed));
      const distance = Math.max(0, Math.min(v.speed * dt, gap));
      if (distance === 0) v.speed = 0;
      v.x += v.dx * distance; v.z += v.dz * distance;
      // Recycle beyond the walkable map, hiding models beyond the road end.
      if (along > 54) { v.x -= v.dx * 108; v.z -= v.dz * 108; v.speed = 0; }
    });
  }
}
