// Freeze actual runtime poses for Cycles review, without baking static walkers into the map.
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import crypto from 'node:crypto';
function moduleFrom(path, require = () => ({})) {
  const context = { exports: {}, require, Math, Map, Set };
  vm.runInNewContext(ts.transpileModule(fs.readFileSync(path, 'utf8'), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2022 },
  }).outputText, context);
  return context.exports;
}
const physics = moduleFrom('lib/game/physics.ts');
const { CanalPedestrianSimulation } = moduleFrom('lib/game/canal-pedestrians.ts', () => physics);
const crowd = new CanalPedestrianSimulation(JSON.parse(fs.readFileSync('public/models/dotonbori.json', 'utf8')));
for (let tick = 0; tick < 65 * 30; tick++) crowd.update(1 / 30, { x: 12, y: 0, z: 18, radius: .32 });
const inputs = ['lib/game/physics.ts', 'lib/game/canal-pedestrians.ts', 'lib/game/crowd-model.ts', 'public/models/dotonbori.json'];
const hash = crypto.createHash('sha256');
inputs.forEach(path => hash.update(fs.readFileSync(path)));
fs.mkdirSync('work', { recursive: true });
fs.writeFileSync('work/canal-crowd.json', JSON.stringify({
  inputs, hash: hash.digest('hex'), seconds: 65, people: crowd.people,
  poses: crowd.walkers.map(({ x, y, z, yaw, speed, gait }) => ({ x, y, z, yaw, speed, gait })),
}));
console.log(`Saved ${crowd.walkers.length} live canal visitor poses for Blender review.`);
