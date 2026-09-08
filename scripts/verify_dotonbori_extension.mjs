import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import ts from 'typescript';
import * as THREE from 'three';

function moduleFrom(path, require = () => ({})) {
  const ctx = { exports: {}, require, Math, Set, Map, Intl, Date };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, ctx);
  return ctx.exports;
}
const physics = moduleFrom('lib/game/physics.ts');
const { World } = moduleFrom('lib/game/world.ts', (name) => name === 'three' ? THREE : name === './physics' ? physics : {});
const data = JSON.parse(fs.readFileSync('public/models/dotonbori.json', 'utf8'));
const layout = JSON.parse(fs.readFileSync('lib/game/dotonbori-layout.json', 'utf8'));
const bridges = layout.extensionBridges.flatMap((z) => [-z, z]);
assert.deepEqual(bridges.slice().sort((a, b) => a - b), [-140, -91, 91, 140]);
assert.deepEqual(data.bounds, [-18.8, 18.8, -152, 152]);

function world(x, z) {
  return Object.assign(Object.create(World.prototype), {
    data, character: {}, paused: false, status: { loading: false, error: null },
    keys: new Set(), joystick: { x: 0, y: 0 },
    player: new THREE.Vector3(x, physics.groundHeight(x, z, data.surfaces), z),
    travel: 'walk', running: false, velocity: 0, verticalVelocity: 0,
    heading: Math.PI, yaw: 0, cruises: [],
  });
}
function walkTo(w, x, z) {
  let highest = w.player.y;
  for (let i = 0; i < 6000; i++) {
    const dx = x - w.player.x, dz = z - w.player.z, d = Math.hypot(dx, dz);
    if (d < .02) return highest;
    const speed = Math.min(1, d / (2.1 / 60));
    w.joystick = { x: dx / d * speed, y: dz / d * speed };
    const previous = w.player.y;
    w.step(1 / 60);
    highest = Math.max(highest, w.player.y);
    assert.ok(Math.abs(w.player.y - previous) < .145, 'Treads stay within the real step height');
    assert.ok(Math.abs(w.player.y - physics.groundHeight(w.player.x, w.player.z, data.surfaces)) < 1e-6, 'Feet stay on the authored surface');
  }
  assert.fail(`Route to ${x},${z} blocked at ${w.player.toArray()}`);
}
// Reproduce the reported invisible wall, then cover both continuous banks.
for (const end of [-1, 1]) for (const side of [-1, 1]) {
  const w = world(side * 13, end * 67.68);
  walkTo(w, side * 13, end * 74);
  walkTo(w, side * 14.9, end * 74);
  walkTo(w, side * 14.9, end * 151);
  // Return along the same promenade, including the old scenery seam at 70.
  walkTo(w, side * 14.9, end * 64);
}
// Every added flight, crossing and descent must be reachable from ground level.
for (const z of bridges) for (const side of [-1, 1]) for (const end of [-1, 1]) {
  const w = world(side * 11, z + end * 9.3);
  walkTo(w, side * 11, z);
  assert.ok(Math.abs(w.player.y - 1.8) < .01);
  assert.ok(Math.abs(walkTo(w, -side * 11, z) - 1.94) < .002);
  walkTo(w, -side * 11, z - end * 9.3);
  assert.equal(w.player.y, 0, 'Both banks are accessible beyond the second bridge');
}
function push(w, dx, dz, ticks = 500) {
  w.joystick = { x: dx, y: dz };
  for (let i = 0; i < ticks; i++) w.step(1 / 60);
}
for (const end of [-1, 1]) for (const side of [-1, 1]) {
  for (const t of [72, 78, 105, 115, 128, 150]) {
    const w = world(side * 11, end * t);
    push(w, -side, 0);
    assert.ok(Math.abs(w.player.x) >= 8.67, 'Continuous canal rails block entry into water');
  }
  const endpoint = world(side * 14.9, end * 150);
  push(endpoint, 0, end);
  assert.ok(Math.abs(endpoint.player.z - end * 151.62) < .01, 'Visible end railing is reached before the bounds clamp');
  const planter = world(side * 14, end * 76);
  push(planter, side, 0);
  assert.ok(Math.abs(planter.player.x) < 15.11, 'Planter seat blocks walking through the furniture');
  const lamp = world(side * 11, end * 87);
  // Approach a relocated lamp from the outer corridor, off the bridge stairs.
  lamp.player.set(side * 14.25, 0, end * 84);
  push(lamp, 0, end);
  assert.ok(Math.abs(lamp.player.z - end * 86.435) < .01, 'Relocated lamp base blocks the player');
}
for (const z of bridges) {
  const rail = world(0, z); push(rail, 0, 1);
  assert.ok(rail.player.z < z + 3.1, 'Bridge side rails keep the avatar above the canal');
  assert.ok(Math.abs(rail.player.y - 1.94) < .002);
  const jumper = world(0, z); jumper.jump();
  let highest = jumper.player.y;
  for (let i = 0; i < 100; i++) { jumper.step(1 / 60); highest = Math.max(highest, jumper.player.y); }
  assert.ok(highest > 2.7); assert.ok(Math.abs(jumper.player.y - 1.94) < .002);
  const sideEntry = world(15, z); push(sideEntry, -1, 0);
  assert.equal(sideEntry.player.y, 0); assert.ok(sideEntry.player.x > 13.8, 'Landings cannot be entered through their raised sides');
}
console.log('PASS: both old boundaries removed; four continuous bank extensions; all 16 new stair entrances, bridge crossings and descents; canal/end/bridge rails, lamps, benches, raised landings and elevated jumps.');
