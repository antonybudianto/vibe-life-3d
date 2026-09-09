import { groundHeight, type Collider, type WalkSurface } from './physics';
import type { Person } from './pedestrians';

type Point = { x: number; z: number };
type Node = Point & { y: number; neighbors: number[] };
export type CanalMap = { colliders: Collider[]; surfaces?: WalkSurface[]; pedestrians?: number };
export type CanalWalker = Point & {
  y: number; yaw: number; speed: number; gait: number; radius: number; vx: number; vz: number;
  path: Point[]; destination: number; spot: number; activity: 'walking' | 'sightseeing';
  remaining: number; journeys: number; crossings: number; bank: number; travelled: number; stalled: number;
};
const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.z - b.z);
const BRIDGES = [-48, 0, 48];
const GRID = .75;

/** Navigation is derived from the same colliders and treads as player movement. */
export class CanalNavigation {
  nodes: Node[] = [];
  banks: number[][] = [[], []];
  spots: { node: number; yaw: number; kind: 'bridge' | 'photo' | 'shop' }[] = [];
  private surfaces: WalkSurface[];
  private surfaceCells = new Map<string, WalkSurface[]>();
  constructor(private map: CanalMap) {
    this.surfaces = map.surfaces ?? [];
    for (const s of this.surfaces) for (let x=Math.floor(s.minX/2);x<=Math.floor(s.maxX/2);x++) for (let z=Math.floor(Math.min(s.minZ,s.endMinZ??s.minZ));z<=Math.floor(Math.max(s.maxZ,s.endMaxZ??s.maxZ));z++) {
      const key=`${x},${z}`, cell=this.surfaceCells.get(key) ?? []; cell.push(s); this.surfaceCells.set(key,cell);
    }
    const cells = new Map<string, number>();
    for (let ix = -24; ix <= 24; ix++) for (let iz = -88; iz <= 88; iz++) {
      const p = { x: ix * GRID, z: iz * GRID };
      if (!this.walkable(p)) continue;
      cells.set(`${ix},${iz}`, this.nodes.length);
      this.nodes.push({ ...p, y: this.height(p), neighbors: [] });
    }
    this.nodes.forEach((n,index) => {
      for (const [dx, dz] of [[1,0],[0,1],[1,1],[1,-1]]) {
        const id = cells.get(`${Math.round(n.x / GRID) + dx},${Math.round(n.z / GRID) + dz}`);
        if (id !== undefined && this.clear(n, this.nodes[id])) { n.neighbors.push(id); this.nodes[id].neighbors.push(index); }
      }
    });
    // Exclude enclosed pockets: all destinations must belong to the main walk.
    const first = this.nearest({ x: 14.5, z: 20 }), seen = new Set([first]), queue = [first];
    for (let i = 0; i < queue.length; i++) for (const id of this.nodes[queue[i]].neighbors) if (!seen.has(id)) { seen.add(id); queue.push(id); }
    for (const id of queue) {
      const n = this.nodes[id];
      if (n.y === 0 && Math.abs(n.x) > 10 && Math.abs(n.x) < 15.6) this.banks[n.x < 0 ? 0 : 1].push(id);
    }
    for (const z of BRIDGES) for (const x of [-5, -2.5, 2.5, 5]) for (const end of [-1, 1]) {
      const node = this.nearest({ x, z: z + end * (z === 0 ? Math.max(3.8,Math.sqrt(Math.max(0,6.9**2-x*x)))-.85 : 2.65) });
      if (seen.has(node)) this.spots.push({ node, yaw: z === 0 ? Math.atan2(-18-x,-13.5-this.nodes[node].z) : end < 0 ? Math.PI : 0, kind: 'bridge' });
    }
    if (!this.banks[0].length || !this.banks[1].length || this.spots.length !== 24) throw new Error('Canal pedestrian routes are disconnected');
    // Small photo groups opposite Glico and short shop queues off the through route.
    // Resolve onto reachable nodes, leaving the stair landings unobstructed.
    for (const [x,z,kind] of [[10.5,-17,'photo'],[10.5,-15.5,'photo'],[11.75,-17,'photo'],[11.75,-15.5,'photo'],[15,54,'shop'],[15,55.5,'shop'],[-15,-29,'shop'],[-15,-30.5,'shop']] as const) {
      const candidates=this.banks[x<0?0:1].filter(id=>!this.spots.some(s=>s.node===id));
      candidates.sort((a,b)=>distance(this.nodes[a],{x,z})-distance(this.nodes[b],{x,z}));
      const node=candidates[0];
      if(node!==undefined&&distance(this.nodes[node],{x,z})<2) this.spots.push({node,yaw:kind==='photo'?-Math.PI/2:Math.sign(x)*Math.PI/2,kind});
    }
  }
  height(p: Point) {
    if (Math.abs(p.x) > 14.5 || BRIDGES.every(z => Math.abs(p.z - z) > 11)) return 0;
    return groundHeight(p.x, p.z, this.surfaceCells.get(`${Math.floor(p.x/2)},${Math.floor(p.z)}`));
  }
  walkable(p: Point, radius = .39, candidates = this.map.colliders) {
    if (Math.abs(p.x) > 18.1 || Math.abs(p.z) > 66.1 || (Math.abs(p.x) < 8.5 && this.height(p) === 0)) return false;
    return !candidates.some(c => {
      const dx = Math.max(0, Math.abs(p.x - c.x) - c.halfX), dz = Math.max(0, Math.abs(p.z - c.z) - c.halfZ);
      return dx * dx + dz * dz < radius * radius;
    });
  }
  clear(a: Point, b: Point, radius = .39) {
    const minX=Math.min(a.x,b.x)-radius,maxX=Math.max(a.x,b.x)+radius,minZ=Math.min(a.z,b.z)-radius,maxZ=Math.max(a.z,b.z)+radius;
    const candidates = this.map.colliders.filter(c => c.x+c.halfX >= minX && c.x-c.halfX <= maxX && c.z+c.halfZ >= minZ && c.z-c.halfZ <= maxZ);
    const steps = Math.max(1, Math.ceil(distance(a, b) / .12)); let previous = this.height(a);
    for (let i = 1; i <= steps; i++) {
      const p = { x: a.x + (b.x-a.x)*i/steps, z: a.z + (b.z-a.z)*i/steps }, height = this.height(p);
      if (Math.abs(height - previous) > .145 || !this.walkable(p, radius, candidates)) return false;
      previous = height;
    }
    return true;
  }
  nearest(p: Point) {
    const candidates=this.nodes.map((n,id)=>({id,d:distance(p,n)}));
    const local=candidates.filter(c=>c.d<1.6).sort((a,b)=>a.d-b.d);
    const match=local.find(c=>this.clear(p,this.nodes[c.id]));
    if(match)return match.id;
    const fallback=candidates.sort((a,b)=>a.d-b.d).find(c=>this.clear(p,this.nodes[c.id]));
    if(!fallback)throw new Error(`No canal walkway at ${p.x}, ${p.z}`);
    return fallback.id;
  }
  route(start: Point, end: number): Point[] {
    const first = this.nearest(start), open = new Set([first]);
    const costs = new Map([[first,0]]), parent = new Map<number,number>();
    while (open.size) {
      let current = -1, best = Infinity;
      for (const id of open) { const score = costs.get(id)! + distance(this.nodes[id],this.nodes[end]); if (score < best) { best = score; current = id; } }
      if (current === end) {
        const ids = [end]; while (parent.has(ids[0])) ids.unshift(parent.get(ids[0])!);
        const raw: Point[] = [start,...ids.map(i => this.nodes[i])], path: Point[] = [];
        for (let i = 0; i < raw.length-1;) {
          let next = raw.length-1;
          while (next>i+1 && !this.clear(raw[i],raw[next])) next--;
          path.push({ x: raw[next].x, z: raw[next].z }); i = next;
        }
        return path;
      }
      open.delete(current);
      for (const id of this.nodes[current].neighbors) {
        const next = costs.get(current)! + distance(this.nodes[current],this.nodes[id]);
        if (next < (costs.get(id) ?? Infinity)) { costs.set(id,next); parent.set(id,current); open.add(id); }
      }
    }
    throw new Error('Canal destination is unreachable');
  }
}

/** Strolls, bridge crossings and timed, reserved sightseeing spots. */
export class CanalPedestrianSimulation {
  readonly navigation: CanalNavigation;
  readonly people: Person[];
  readonly walkers: CanalWalker[] = [];
  private state = 8092026;
  constructor(map: CanalMap) {
    this.navigation = new CanalNavigation(map);
    const colors = ['#304d71','#b88675','#c7bdae','#67734d','#493e58','#cc9c42','#334245','#985350'];
    this.people = Array.from({length:map.pedestrians ?? 36}, (_,i) => ({offset:this.random(),speed:.83+this.random()*.49,scale:.90+this.random()*.17,coat:colors[i%colors.length],region:i%2,crosses:true}));
    this.people.forEach((p,i) => {
      const bank = i%2, preferred = {x:bank ? 11.5 : -11.5,z:BRIDGES[Math.floor(i/2)%3]+(i%4<2 ? 13 : -13)};
      const candidates = this.navigation.banks[bank]; let spawn = candidates[0], best = -Infinity;
      for (const id of candidates) {
        const n = this.navigation.nodes[id], room = Math.min(3,...this.walkers.map(w => distance(w,n)));
        const score = room*7 - distance(n,preferred)*.3 + this.random();
        if (score > best) { best = score; spawn = id; }
      }
      const n = this.navigation.nodes[spawn];
      const w: CanalWalker = {x:n.x,z:n.z,y:n.y,yaw:0,speed:0,gait:p.offset*6.28,radius:.30*p.scale,vx:0,vz:0,path:[],destination:spawn,spot:-1,activity:'walking',remaining:0,journeys:i%3,crossings:0,bank,travelled:0,stalled:0};
      this.walkers.push(w); this.plan(w,i);
      if (w.path[0]) w.yaw = Math.atan2(w.path[0].x-w.x,w.path[0].z-w.z);
    });
  }
  private random() { this.state=(Math.imul(this.state,1664525)+1013904223)>>>0; return this.state/4294967296; }
  private plan(w: CanalWalker, index: number) {
    const nav = this.navigation;
    w.journeys++; w.spot = -1; w.activity = 'walking';
    if (w.journeys%3 === 1) {
      const available = nav.spots.map((s,i) => ({...s,i})).filter(s => !this.walkers.some(other => other!==w && other.spot===s.i));
      const preference=index%4===0?'shop':index%4===1?'photo':'bridge';
      available.sort((a,b) => (distance(w,nav.nodes[a.node])-(a.kind===preference?35:0))-(distance(w,nav.nodes[b.node])-(b.kind===preference?35:0)));
      const spot = available[Math.floor(this.random()*Math.min(4,available.length))];
      if (spot) { w.spot=spot.i; w.destination=spot.node; }
    }
    if (w.spot < 0) {
      const bank = w.journeys%3 === 2 ? 1-w.bank : w.bank;
      const candidates = nav.banks[bank]; let best = -Infinity, chosen = candidates[0];
      const bridge = BRIDGES[(index+Math.floor(w.journeys/3))%3];
      for (let k=0;k<45;k++) {
        const id=candidates[Math.floor(this.random()*candidates.length)], n=nav.nodes[id];
        const score = Math.min(distance(w,n),22) - Math.abs(n.z-bridge)*.22 + this.random()*5;
        if(score>best){best=score;chosen=id;}
      }
      w.destination=chosen;
    }
    w.path=nav.route(w,w.destination);
  }
  update(dt: number, player: Point & {y?:number;radius:number}) {
    if (dt<=0) return; dt=Math.min(dt,1/30);
    const before=this.walkers.map(w=>({x:w.x,z:w.z,y:w.y}));
    this.walkers.forEach((w,i)=>{
      const p=this.people[i];
      if(w.activity==='sightseeing') {
        w.remaining-=dt; w.speed*=Math.exp(-12*dt); w.vx=w.vz=0;
        const target=this.navigation.spots[w.spot].yaw;
        w.yaw+=Math.atan2(Math.sin(target-w.yaw),Math.cos(target-w.yaw))*Math.min(1,dt*4);
        if(w.remaining<=0)this.plan(w,i);
        return;
      }
      let target=w.path[0];
      if(target&&distance(w,target)<.13){w.path.shift();target=w.path[0];}
      if(!target) {
        if(w.spot>=0){w.activity='sightseeing';w.remaining=this.navigation.spots[w.spot].kind==='shop'?7+this.random()*10:12+this.random()*16;w.vx=w.vz=0;return;}
        this.plan(w,i);target=w.path[0];if(!target)return;
      }
      const d=distance(w,target),dx=(target.x-w.x)/Math.max(d,.001),dz=(target.z-w.z)/Math.max(d,.001);
      const pace=Math.min(p.speed,d/dt), oldHeight=w.y;
      let vx=dx*pace,vz=dz*pace;
      for(let j=0;j<before.length;j++) {
        if(i===j||Math.abs(w.y-before[j].y)>.7)continue;
        const ax=before[j].x-w.x,az=before[j].z-w.z,space=Math.hypot(ax,az);
        if(space<.001||space>1.3)continue;
        const ahead=ax*dx+az*dz, lateral=ax*dz-az*dx;
        if(ahead>0&&Math.abs(lateral)<.65){const avoid=(1-space/1.3)*.85;vx+=dz*avoid;vz-=dx*avoid;const slow=Math.max(.2,Math.min(1,(space-.44)/.75));vx*=slow;vz*=slow;}
        if(space<.66){vx-=ax/space*(.66-space)*2;vz-=az/space*(.66-space)*2;}
      }
      const px=w.x-player.x,pz=w.z-player.z,pd=Math.hypot(px,pz),room=player.radius+w.radius+.30;
      if(Math.abs(w.y-(player.y??0))<1&&pd>.001&&pd<room){vx+=px/pd*(room-pd)*2.5;vz+=pz/pd*(room-pd)*2.5;}
      const speed=Math.hypot(vx,vz);if(speed>p.speed){vx*=p.speed/speed;vz*=p.speed/speed;}
      w.vx+=(vx-w.vx)*Math.min(1,dt*8);w.vz+=(vz-w.vz)*Math.min(1,dt*8);
      let next={x:w.x+w.vx*dt,z:w.z+w.vz*dt};
      if(!this.navigation.clear(w,next,w.radius+.06)) {
        const xOnly={x:next.x,z:w.z},zOnly={x:w.x,z:next.z};
        if(this.navigation.clear(w,xOnly,w.radius+.06))next=xOnly;
        else if(this.navigation.clear(w,zOnly,w.radius+.06))next=zOnly;
        else next={x:w.x,z:w.z};
      }
      const moved=distance(w,next);w.x=next.x;w.z=next.z;w.y=this.navigation.height(w);
      w.travelled+=moved;w.gait+=moved*7.5;w.speed+=(moved/dt-w.speed)*Math.min(1,dt*9);
      if(moved>.0001){const yaw=Math.atan2(w.vx,w.vz);w.yaw+=Math.atan2(Math.sin(yaw-w.yaw),Math.cos(yaw-w.yaw))*Math.min(1,dt*8);}
      if(w.y===0&&Math.abs(w.x)>8.5){const bank=w.x<0?0:1;if(bank!==w.bank){w.crossings++;w.bank=bank;}}
      w.stalled=moved/dt<.13?w.stalled+dt:0;
      if(w.stalled>3){w.stalled=0;w.path=this.navigation.route(w,w.destination);}
      if(Math.abs(w.y-oldHeight)>.145)throw new Error('Pedestrian left a walkable stair surface');
    });
  }
}
