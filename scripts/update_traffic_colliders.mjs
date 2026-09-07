import fs from 'node:fs';
const path='public/models/crossing.json', map=JSON.parse(fs.readFileSync(path,'utf8'));
map.colliders=map.colliders.filter(c=>c.kind!=='traffic');
for(const v of JSON.parse(fs.readFileSync('public/models/crossing-life.json','utf8')).vehicles) {
  const [w,d,height]=v.model==='citybus'?[2.45,7.3,3.2]:[1.92,4.7,1.9], co=Math.abs(Math.cos(v.yaw)),si=Math.abs(Math.sin(v.yaw));
  map.colliders.push({x:v.x,z:v.z,halfX:(w*co+d*si)/2,halfZ:(w*si+d*co)/2,height,kind:'traffic'});
}
fs.writeFileSync(path,JSON.stringify(map,null,2)+'\n');
