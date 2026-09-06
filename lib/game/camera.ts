export const MIN_ZOOM = 4.2;
export const MAX_ZOOM = 60;

/** Proportional dolly: precise near the avatar, faster across the neighborhood. */
export function zoomDistance(current: number, delta: number) {
  return Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, current * Math.exp(delta * .095)));
}

/** Keep a following third-person view while opening up the skyline at distance. */
export function elevatedPitch(pitch: number, distance: number) {
  const t = Math.max(0, Math.min(1, (distance - 13) / 34));
  return Math.min(1.38, pitch + t * t * (3 - 2 * t) * .88);
}
