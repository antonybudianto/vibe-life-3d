import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
import ts from 'typescript';
import * as THREE from 'three';

function moduleFrom(path, require = () => ({})) {
  const context = { exports: {}, require, Math, Set, Map, Intl, Date };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, context);
  return context.exports;
}
const physics = moduleFrom('lib/game/physics.ts');
const { World } = moduleFrom('lib/game/world.ts', name => name === 'three' ? THREE : name === './physics' ? physics : {});
const data = JSON.parse(fs.readFileSync('public/models/dotonbori.json'));
function rider(x, z, heading = 0) {
  return Object.assign(Object.create(World.prototype), {
    data, character: {}, paused: false, status: { loading: false, error: null },
    keys: new Set(), joystick: { x: 0, y: 0 },
    player: new THREE.Vector3(x, physics.groundHeight(x, z, data.surfaces), z),
    travel: 'motorcycle', running: false, velocity: 0, verticalVelocity: 0,
    heading, yaw: 0, cruises: [],
  });
}
function step(w) {
  const previous = w.player.clone();
  w.step(1 / 60);
  assert.ok(physics.motorcycleFits(w.player.x, w.player.z, w.heading, data.colliders, data.bounds), `Bike clips scenery at ${w.player.toArray()}, heading ${w.heading}`);
  assert.ok(Math.hypot(w.player.x - previous.x, w.player.z - previous.z) < .27, 'Contact cannot eject the bike across the promenade');
  assert.equal(w.player.y, physics.groundHeight(w.player.x, w.player.z, data.surfaces));
}
function run(w, seconds, keys) {
  w.keys = new Set(keys);
  for (let i = 0; i < seconds * 60; i++) step(w);
}

// Retain tire-to-tire length while allowing handlebar-width passages.
const bounds = [-20, 20, -20, 20];
assert.ok(physics.motorcycleFits(0, 0, 0, [{ x: .7, z: 0, halfX: .1, halfZ: 4 }], bounds));
assert.equal(physics.motorcycleFits(0, 0, Math.PI / 2, [{ x: .7, z: 0, halfX: .1, halfZ: 4 }], bounds), false);
assert.equal(physics.motorcycleFits(0, 0, 0, [{ x: 0, z: 1.2, halfX: 2, halfZ: .1 }], bounds), false, 'Front wheel still collides');
assert.equal(physics.motorcycleFits(0, 0, 0, [{ x: 0, z: -1.2, halfX: 2, halfZ: .1 }], bounds), false, 'Rear wheel still collides');
assert.equal(physics.motorcycleFits(0, 19, 0, [], bounds), false, 'Whole bike stays inside map bounds');

const turn = rider(11, 128.21);
run(turn, 1, ['KeyA']);
assert.ok(turn.heading > 1, 'A stopped bike can turn with steering alone');
assert.equal(turn.velocity, 0, 'Stationary steering does not accelerate');
const reverse = rider(11, 128.21);
run(reverse, .5, ['KeyS', 'KeyA']);
assert.ok(reverse.heading < 0 && reverse.velocity < 0, 'Reverse keeps reversed steering');

const wall = rider(10.5, 128.21, -Math.PI / 2);
run(wall, 2, ['KeyW']);
const stopped = wall.player.clone();
run(wall, 1.5, ['KeyW', 'KeyA']);
assert.ok(wall.player.distanceTo(stopped) > 2, 'Escape a canal railing without dismounting');

const lamp = rider(9.51, 128.21, Math.PI);
run(lamp, 3, ['KeyW']);
assert.ok(lamp.player.z < 120, 'The reported road lamp no longer traps the bike');

// All seven bridges, both banks, in both directions, with the real lamp colliders.
for (const bridge of [-140, -91, -48, 0, 48, 91, 140]) for (const side of [-1, 1]) for (const direction of [-1, 1]) {
  const extent = bridge === 0 ? 11 : 10;
  const w = rider(side * (bridge === 0 ? 12 : 11), bridge - direction * extent, direction === 1 ? 0 : Math.PI);
  w.keys.add('KeyW');
  let highest = 0;
  for (let i = 0; i < 360 && (w.player.z - bridge) * direction < extent; i++) { step(w); highest = Math.max(highest, w.player.y); }
  assert.ok((w.player.z - bridge) * direction >= extent, `Blocked on bridge ${bridge}, bank ${side}, direction ${direction} at ${w.player.toArray()}`);
  assert.ok(highest > (bridge === 0 ? 2.5 : 1.7), 'Bike ascends onto the landing');
  assert.equal(w.player.y, 0, 'Bike descends back onto the promenade');
}

// Mounting on the narrow outer ramps finds an orientation that fits, without
// teleporting to the higher bridge plaza or leaving an overlap for the next step.
for (const side of [-1, 1]) for (const end of [-1, 1]) for (const u of [2, 4, 6]) {
  const x = side * u, z = end * (3.8 + 3.1 * (1 - (u / 8.5) ** 2) + .825);
  const placement = physics.placeMotorcycle(x, z, 0, data.colliders, data.bounds, data.surfaces);
  assert.ok(placement, `Cannot mount on perimeter ramp ${x},${z}`);
  assert.ok(physics.motorcycleFits(placement.x, placement.z, placement.heading, data.colliders, data.bounds));
  assert.ok(Math.abs(physics.groundHeight(placement.x, placement.z, data.surfaces) - physics.groundHeight(x, z, data.surfaces)) <= .24);
}
console.log('PASS: motorcycle length/width, stationary and reverse steering, railing escape, reported road lamp, all 28 stair traversals, and mounting on all four perimeter ramps without clipping.');
