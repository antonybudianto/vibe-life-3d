export type Collider = { x: number; z: number; halfX: number; halfZ: number; height?: number; cameraRadius?: number; cameraMinY?: number };
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
      if (ax * ax + az * az >= radius * radius) continue;
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
