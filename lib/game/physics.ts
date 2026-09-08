export type Collider = { x: number; z: number; halfX: number; halfZ: number; height?: number; cameraRadius?: number; cameraMinY?: number; cameraIgnore?: boolean };
export type WalkSurface = { minX: number; maxX: number; minZ: number; maxZ: number; height: number; endHeight?: number };

/** Sloped decks use the same endpoints as the Blender bridge mesh. */
export function groundHeight(x: number, z: number, surfaces: WalkSurface[] = []) {
  let height = 0;
  for (const s of surfaces) {
    if (x < s.minX || x > s.maxX || z < s.minZ || z > s.maxZ) continue;
    const t = (x - s.minX) / Math.max(.001, s.maxX - s.minX);
    height = Math.max(height, s.height + ((s.endHeight ?? s.height) - s.height) * t);
  }
  return height;
}

export function followGround(y: number, velocity: number, oldFloor: number, floor: number, dt: number) {
  if (y <= oldFloor + .025 && velocity <= 0) return { y: floor, velocity: 0 };
  const nextVelocity = velocity - 15 * dt;
  const nextY = y + nextVelocity * dt;
  return nextY <= floor ? { y: floor, velocity: 0 } : { y: nextY, velocity: nextVelocity };
}
export function moveWithCollision(x: number, z: number, dx: number, dz: number, radius: number, colliders: Collider[], bounds: [number, number, number, number]) {
  // Axis-separated circle/AABB resolution permits wall sliding and prevents tunneling
  // at the fixed simulation step. Also resolves an overlapping vehicle on entry.
  let nx = x + dx, nz = z;
  for (const axis of ['x', 'z'] as const) {
    if (axis === 'z') nz += dz;
    for (const c of colliders) {
      const cx = Math.max(c.x - c.halfX, Math.min(nx, c.x + c.halfX));
      const cz = Math.max(c.z - c.halfZ, Math.min(nz, c.z + c.halfZ));
      const ax = nx - cx, az = nz - cz;
      // Contact rounding must not eject a stationary avatar along a long railing.
      if (ax * ax + az * az >= radius * radius - 1e-9) continue;
      if (axis === 'x') {
        const inset = Math.sqrt(Math.max(0, radius * radius - az * az));
        nx = nx < c.x ? c.x - c.halfX - inset : c.x + c.halfX + inset;
      } else {
        const inset = Math.sqrt(Math.max(0, radius * radius - ax * ax));
        nz = nz < c.z ? c.z - c.halfZ - inset : c.z + c.halfZ + inset;
      }
    }
  }
  return { x: Math.max(bounds[0] + radius, Math.min(bounds[1] - radius, nx)), z: Math.max(bounds[2] + radius, Math.min(bounds[3] - radius, nz)) };
}

type Phase = 'day' | 'evening' | 'night';
export function resolveTime(mode: Phase | 'live', date: Date) {
  if (mode !== 'live') return { phase: mode, next: mode, blend: 0, clock: mode === 'day' ? '12:00' : mode === 'evening' ? '17:30' : '21:00' };
  const parts = new Intl.DateTimeFormat('en-GB', { timeZone: 'Asia/Tokyo', hour: '2-digit', minute: '2-digit', hourCycle: 'h23' }).formatToParts(date);
  const h = Number(parts.find((p) => p.type === 'hour')?.value ?? 0), m = Number(parts.find((p) => p.type === 'minute')?.value ?? 0);
  const hour = h + m / 60;
  let phase: Phase = 'night', next: Phase = 'night', blend = 0;
  if (hour >= 5 && hour < 7) { phase = 'night'; next = 'day'; blend = (hour - 5) / 2; }
  else if (hour >= 7 && hour < 16) { phase = next = 'day'; }
  else if (hour >= 16 && hour < 18) { phase = 'day'; next = 'evening'; blend = (hour - 16) / 2; }
  else if (hour >= 18 && hour < 20) { phase = 'evening'; next = 'night'; blend = (hour - 18) / 2; }
  return { phase, next, blend, clock: `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}` };
}
