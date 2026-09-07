// Share the runtime's seeded starting poses with the Blender review assembly.
import fs from 'node:fs';
import vm from 'node:vm';
import ts from 'typescript';
import crypto from 'node:crypto';
const context={exports:{},Math,Map,Set};
vm.runInNewContext(ts.transpileModule(fs.readFileSync('lib/game/pedestrians.ts','utf8'),{compilerOptions:{module:ts.ModuleKind.CommonJS,target:ts.ScriptTarget.ES2022}}).outputText,context);
const life=JSON.parse(fs.readFileSync('public/models/crossing-life.json','utf8'));
const colliders=['crossing','hachiko'].flatMap(name=>JSON.parse(fs.readFileSync(`public/models/${name}.json`,'utf8')).colliders);
const crowd=new context.exports.PedestrianSimulation(life.people,colliders);
const inputs=['lib/game/pedestrians.ts','public/models/crossing-life.json','public/models/crossing.json','public/models/hachiko.json'];
const hash=crypto.createHash('sha256');inputs.forEach(path=>hash.update(fs.readFileSync(path)));
fs.mkdirSync('work',{recursive:true});
fs.writeFileSync('work/crowd-start.json',JSON.stringify({hash:hash.digest('hex'),poses:crowd.walkers.map(w=>({x:w.x,z:w.z,yaw:w.yaw,gait:0}))}));
console.log('Saved current crowd poses for Blender.');
