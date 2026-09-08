export type Collider = { x: number; z: number; halfX: number; halfZ: number; height?: number; cameraRadius?: number; cameraMinY?: number; cameraIgnore?: boolean };
export type WalkSurface = { minX: number; maxX: number; minZ: number; maxZ: number; endMinZ?: number; endMaxZ?: number; height: number; endHeight?: number };

/** Sloped decks use the same endpoints as the Blender bridge mesh. */
export function groundHeight(x: number, z: number, surfaces: WalkSurface[] = []) {
  let height = 0;
  for (const s of surfaces) {
    if (x < s.minX || x > s.maxX) continue;
    const t = (x - s.minX) / Math.max(.001, s.maxX - s.minX);
    const minZ = s.minZ + ((s.endMinZ ?? s.minZ) - s.minZ) * t;
    const maxZ = s.maxZ + ((s.endMaxZ ?? s.maxZ) - s.maxZ) * t;
    if (z < minZ || z > maxZ) continue;
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
/** Stair risers are climbable; a raised landing cannot be entered through its side. */
export function canStepTo(y: number, oldFloor: number, floor: number) {
  return floor <= Math.max(y, oldFloor) + .24;
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

// The bike is about .88m across the handlebars and 2.32m from tire to tire.
// A capsule retains its length without treating that length as sideways width.
export const MOTORCYCLE_RADIUS = .44;
const MOTORCYCLE_HALF_LENGTH = .72;
function motorcycleContact(x: number, z: number, sin: number, cos: number, c: Collider) {
  const r = MOTORCYCLE_RADIUS, h = MOTORCYCLE_HALF_LENGTH;
  const rx = x - c.x, rz = z - c.z;
  if (Math.abs(rx) >= c.halfX + Math.abs(sin) * h + r || Math.abs(rz) >= c.halfZ + Math.abs(cos) * h + r) return null;
  const ax = rx - sin * h, az = rz - cos * h, dx = sin * h * 2, dz = cos * h * 2;
  let enter = 0, leave = 1;
  for (const [a, d, half] of [[ax, dx, c.halfX], [az, dz, c.halfZ]]) {
    if (Math.abs(d) < 1e-10) {
      if (Math.abs(a) > half) { enter = 2; break; }
    } else {
      const t0 = (-half - a) / d, t1 = (half - a) / d;
      enter = Math.max(enter, Math.min(t0, t1)); leave = Math.min(leave, Math.max(t0, t1));
    }
  }
  if (enter <= leave) {
    // When the center segment is inside a box, choose a separating direction.
    let depth = Infinity, nx = 0, nz = 0;
    for (const [ux, uz] of [[1, 0], [0, 1], [cos, -sin]]) {
      const projection = rx * ux + rz * uz;
      const overlap = c.halfX * Math.abs(ux) + c.halfZ * Math.abs(uz) + h * Math.abs(sin * ux + cos * uz) + r - Math.abs(projection);
      if (overlap < depth) { depth = overlap; nx = ux * (projection < 0 ? -1 : 1); nz = uz * (projection < 0 ? -1 : 1); }
    }
    return { x: nx * depth, z: nz * depth };
  }
  // Otherwise the closest pair includes a segment endpoint or a box corner.
  let best = Infinity, vx = 0, vz = 0;
  const candidate = (px: number, pz: number, qx: number, qz: number) => {
    const ex = px - qx, ez = pz - qz, distance = ex * ex + ez * ez;
    if (distance < best) { best = distance; vx = ex; vz = ez; }
  };
  for (const t of [0, 1]) {
    const px = ax + dx * t, pz = az + dz * t;
    candidate(px, pz, Math.max(-c.halfX, Math.min(c.halfX, px)), Math.max(-c.halfZ, Math.min(c.halfZ, pz)));
  }
  for (const qx of [-c.halfX, c.halfX]) for (const qz of [-c.halfZ, c.halfZ]) {
    const t = Math.max(0, Math.min(1, ((qx - ax) * dx + (qz - az) * dz) / (4 * h * h)));
    candidate(ax + dx * t, az + dz * t, qx, qz);
  }
  const distance = Math.sqrt(best);
  if (distance >= r - 1e-7) return null;
  return { x: vx / distance * (r - distance), z: vz / distance * (r - distance) };
}

export function motorcycleFits(x: number, z: number, heading: number, colliders: Collider[], bounds: [number, number, number, number]) {
  const sin = Math.sin(heading), cos = Math.cos(heading);
  const ex = Math.abs(sin) * MOTORCYCLE_HALF_LENGTH + MOTORCYCLE_RADIUS, ez = Math.abs(cos) * MOTORCYCLE_HALF_LENGTH + MOTORCYCLE_RADIUS;
  return x >= bounds[0] + ex - 1e-7 && x <= bounds[1] - ex + 1e-7 && z >= bounds[2] + ez - 1e-7 && z <= bounds[3] - ez + 1e-7
    && colliders.every(c => !motorcycleContact(x, z, sin, cos, c));
}

export function moveMotorcycleWithCollision(x: number, z: number, dx: number, dz: number, heading: number, colliders: Collider[], bounds: [number, number, number, number]) {
  const sin = Math.sin(heading), cos = Math.cos(heading);
  const ex = Math.abs(sin) * MOTORCYCLE_HALF_LENGTH + MOTORCYCLE_RADIUS, ez = Math.abs(cos) * MOTORCYCLE_HALF_LENGTH + MOTORCYCLE_RADIUS;
  let nx = x + dx, nz = z + dz;
  for (let pass = 0; pass < 8; pass++) {
    let moved = false;
    for (const c of colliders) {
      const contact = motorcycleContact(nx, nz, sin, cos, c);
      if (contact) { nx += contact.x; nz += contact.z; moved = true; }
    }
    const bx = Math.max(bounds[0] + ex, Math.min(bounds[1] - ex, nx)), bz = Math.max(bounds[2] + ez, Math.min(bounds[3] - ez, nz));
    moved ||= Math.abs(bx - nx) + Math.abs(bz - nz) > 1e-7;
    nx = bx; nz = bz;
    if (!moved) break;
  }
  return { x: nx, z: nz, clear: motorcycleFits(nx, nz, heading, colliders, bounds) };
}

/** Mount parallel to a tight passage rather than spawning across its railings. */
export function placeMotorcycle(x: number, z: number, heading: number, colliders: Collider[], bounds: [number, number, number, number], surfaces: WalkSurface[] = []) {
  const floor = groundHeight(x, z, surfaces);
  let best: { x: number; z: number; heading: number } | null = null, score = Infinity;
  for (let i = 0; i <= 6; i++) for (const sign of i === 0 ? [1] : [-1, 1]) {
    const angle = heading + sign * i * Math.PI / 12;
    const p = moveMotorcycleWithCollision(x, z, 0, 0, angle, colliders, bounds);
    const distance = Math.hypot(p.x - x, p.z - z), cost = distance + i * .02;
    if (p.clear && distance < 1.2 && Math.abs(groundHeight(p.x, p.z, surfaces) - floor) <= .24 && cost < score) {
      best = { x: p.x, z: p.z, heading: angle }; score = cost;
    }
  }
  return best;
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
