import type { Collider } from './physics';
import type { RoadUser, TrafficSimulation } from './traffic';

export type Person = { offset: number; speed: number; scale: number; coat: string; region: number; crosses: boolean };
type Point = { x: number; z: number };
type Waypoint = Point & { crossing?: boolean };
export type Walker = RoadUser & { yaw: number; speed: number; gait: number; crossing: boolean; vx: number; vz: number; path: Waypoint[]; region: number; steps: number; travelled: number; waiting: boolean; stalled: number };
type Node = Point & { region: number; neighbors: number[] };
const STEP = .75, EXTENT = 44;
const regionOf = (x: number, z: number) => (x > 0 ? 1 : 0) + (z > 0 ? 2 : 0);
const distance = (a: Point, b: Point) => Math.hypot(a.x - b.x, a.z - b.z);

/** A small sidewalk graph, built once from the map's actual obstacle volumes. */
class Sidewalks {
  nodes: Node[] = [];
  regions: number[][] = [[], [], [], []];
  gates: number[] = [];
  private obstacles: Collider[];

  constructor(colliders: Collider[]) {
    this.obstacles = colliders.filter(c => !c.cameraMinY || c.height! > 1).map(c => ({ ...c, halfX: c.cameraRadius && c.halfX < .4 ? .78 : c.halfX, halfZ: c.cameraRadius && c.halfZ < .4 ? .78 : c.halfZ }));
    // The bus shelter and standalone benches are walk-around furniture.
    this.obstacles.push({ x:-19,z:11.3,halfX:2.8,halfZ:.95 },{ x:-31,z:12.2,halfX:1.1,halfZ:.45 },{ x:32,z:12,halfX:1.1,halfZ:.45 });
    const cells = new Map<string, number>();
    for(let x=-EXTENT;x<=EXTENT;x++) for(let z=-EXTENT;z<=EXTENT;z++) {
      const p={x:x*STEP,z:z*STEP};
      if(!this.walkable(p)) continue;
      cells.set(`${x},${z}`,this.nodes.length); this.nodes.push({...p,region:regionOf(p.x,p.z),neighbors:[]});
    }
    this.nodes.forEach((n) => {
      for(const [dx,dz] of [[1,0],[-1,0],[0,1],[0,-1],[1,1],[-1,1],[1,-1],[-1,-1]]) {
        const id=cells.get(`${Math.round(n.x/STEP)+dx},${Math.round(n.z/STEP)+dz}`);
        if(id!==undefined&&this.clear(n,this.nodes[id])) n.neighbors.push(id);
      }
    });
    // Keep the connected public sidewalk around each corner; omit enclosed gaps.
    for(let r=0;r<4;r++) {
      const gate=this.nearest({x:r%2?9.75:-9.75,z:r>1?9.75:-9.75},r);this.gates.push(gate);
      const seen=new Set([gate]),queue=[gate];
      for(let i=0;i<queue.length;i++) for(const id of this.nodes[queue[i]].neighbors) if(!seen.has(id)){seen.add(id);queue.push(id);}
      this.regions[r]=queue;
    }
  }

  walkable(p: Point, margin=.36) {
    if(Math.abs(p.x)<9.65||Math.abs(p.z)<9.65||Math.abs(p.x)>33||Math.abs(p.z)>30) return false;
    // The northeast frontage is a walkable strip; the building fills its north side.
    if(p.x>0&&p.z< -11.55) return false;
    return !this.obstacles.some(c => Math.abs(p.x-c.x)<c.halfX+margin&&Math.abs(p.z-c.z)<c.halfZ+margin);
  }
  clear(a: Point,b: Point) {
    const count=Math.ceil(distance(a,b)/.24);
    for(let i=0;i<=count;i++) if(!this.walkable({x:a.x+(b.x-a.x)*i/Math.max(count,1),z:a.z+(b.z-a.z)*i/Math.max(count,1)})) return false;
    return true;
  }
  nearest(p: Point,region=regionOf(p.x,p.z)) {
    let id=-1,best=Infinity;
    for(let i=0;i<this.nodes.length;i++) if(this.nodes[i].region===region) {const d=distance(p,this.nodes[i]);if(d<best&&this.clear(p,this.nodes[i])){best=d;id=i;}}
    if(id<0) throw new Error('No walkable sidewalk');return id;
  }
  route(start: Point,end: number,region: number): Waypoint[] {
    const first=this.nearest(start,region),open=new Set([first]),cost=new Map([[first,0]]),parent=new Map<number,number>();
    while(open.size) {
      let current=-1,best=Infinity;
      for(const id of open) {const score=cost.get(id)!+distance(this.nodes[id],this.nodes[end]);if(score<best){best=score;current=id;}}
      if(current===end) {
        const ids=[end];while(parent.has(ids[0]))ids.unshift(parent.get(ids[0])!);
        const raw: Point[]=[start,...ids.map(id=>this.nodes[id])],result: Waypoint[]=[];
        for(let i=0;i<raw.length-1;) {let next=i+1;while(next+1<raw.length&&this.clear(raw[i],raw[next+1]))next++;result.push({x:raw[next].x,z:raw[next].z});i=next;}
        return result;
      }
      open.delete(current);
      for(const id of this.nodes[current].neighbors) {
        const next=cost.get(current)!+distance(this.nodes[current],this.nodes[id]);
        if(next<(cost.get(id)??Infinity)){cost.set(id,next);parent.set(id,current);open.add(id);}
      }
    }
    return [];
  }
}

/** Independent itineraries, personal space and distance-driven footsteps. */
export class PedestrianSimulation {
  walkers: Walker[] = [];
  private sidewalks: Sidewalks;
  private randomState = 1092026;
  constructor(private people: Person[],colliders: Collider[]) {
    this.sidewalks=new Sidewalks(colliders);
    for(const p of people) {
      const candidates=this.sidewalks.regions[p.region];let spawn=this.sidewalks.nodes[candidates[0]],best=-1;
      // Spread initial pedestrians over all four districts, including the plazas.
      for(let k=0;k<160;k++) {
        const candidate=this.sidewalks.nodes[candidates[Math.floor(this.random()*candidates.length)]];
        const clearance=Math.min(5,...this.walkers.map(w=>distance(w,candidate)));
        if(clearance>best){best=clearance;spawn=candidate;}
      }
      const w: Walker={x:spawn.x,z:spawn.z,radius:.30*p.scale,yaw:0,speed:0,gait:p.offset*Math.PI*2,crossing:false,vx:0,vz:0,path:[],region:p.region,steps:0,travelled:0,waiting:false,stalled:0};
      this.walkers.push(w);this.plan(w,p);
      const target=w.path[0];if(target)w.yaw=Math.atan2(target.x-w.x,target.z-w.z);
    }
  }
  private random(){this.randomState=(Math.imul(this.randomState,1664525)+1013904223)>>>0;return this.randomState/4294967296;}
  private plan(w: Walker,p: Person) {
    w.steps++;
    // A minority cross after a full sidewalk journey; everyone else keeps strolling.
    const destinations=[w.region^1,w.region^2].filter(r=>this.walkers.filter(other=>regionOf((other.path.at(-1)??other).x,(other.path.at(-1)??other).z)===r).length<this.people.filter(other=>other.region===r).length+1);
    const crossing=p.crosses&&w.steps%3===0&&destinations.length>0;
    let region=w.region;
    const route: Waypoint[]=[];
    if(crossing) {
      region=destinations[Math.floor(this.random()*destinations.length)];
      route.push(...this.sidewalks.route(w,this.sidewalks.gates[w.region],w.region));
      const gate=this.sidewalks.nodes[this.sidewalks.gates[region]];
      route.push({x:gate.x,z:gate.z,crossing:true});
    }
    const candidates=this.sidewalks.regions[region];
    const start=route.at(-1)??w;let destination=candidates[0],best=-Infinity;
    for(let k=0;k<30;k++) {
      const id=candidates[Math.floor(this.random()*candidates.length)],n=this.sidewalks.nodes[id];
      const room=Math.min(3,...this.walkers.filter(other=>other!==w).map(other=>distance(other.path.at(-1)??other,n)));
      const score=Math.min(distance(start,n),14)+room*2+this.random()*3;
      if(score>best){destination=id;best=score;}
    }
    route.push(...this.sidewalks.route(start,destination,region));w.path=route;
  }
  update(dt: number, traffic: TrafficSimulation, player: RoadUser) {
    if(dt<=0)return;dt=Math.min(dt,1/30);
    const before=this.walkers.map(w=>({x:w.x,z:w.z,radius:w.radius}));
    this.walkers.forEach((w,i)=>{
      const p=this.people[i];let target=w.path[0];w.waiting=false;
      if(!target){this.plan(w,p);target=w.path[0];}if(!target)return;
      let dist=distance(w,target);
      const reached=w.crossing ? dist<1.1&&this.sidewalks.walkable(w) : dist<.30;
      if(reached) {
        if(w.crossing){w.crossing=false;w.region=regionOf(target.x,target.z);}
        w.path.shift();if(!w.path.length)this.plan(w,p);target=w.path[0];if(!target)return;dist=distance(w,target);
      }
      if(target.crossing&&!w.crossing) {
        const enoughTime=traffic.phase==='pedestrians'&&27-traffic.phaseTime>dist/(p.speed*.80)+1.5;
        if(enoughTime)w.crossing=true;else w.waiting=true;
        // Busy corners encourage another sidewalk stroll, rather than a growing pile.
        if(w.waiting&&before.filter((other,j)=>j!==i&&distance(w,other)<3).length>=3) {
          this.plan(w,p);w.waiting=false;target=w.path[0];if(!target)return;dist=distance(w,target);
        }
      }
      const dx=(target.x-w.x)/Math.max(dist,.01),dz=(target.z-w.z)/Math.max(dist,.01);
      let vx=w.waiting?0:dx*p.speed,vz=w.waiting?0:dz*p.speed;
      for(let j=0;j<before.length;j++) {
        if(i===j)continue;const other=before[j],ax=other.x-w.x,az=other.z-w.z,d=Math.hypot(ax,az);
        if(d<.001||d>1.55)continue;
        const ahead=ax*dx+az*dz,lateral=ax*dz-az*dx;
        if(ahead>0&&Math.abs(lateral)<.72) {
          // Keep to the right when meeting someone, instead of forming one queue.
          const avoid=(1-d/1.55)*.95;vx+=dz*avoid;vz-=dx*avoid;
          const slow=Math.max(.3,Math.min(1,(d-.52)/.85));vx*=slow;vz*=slow;
        }
        if(d<.82){const push=(.82-d)*2;vx-=ax/d*push;vz-=az/d*push;}
      }
      const px=w.x-player.x,pz=w.z-player.z,pd=Math.hypot(px,pz),space=player.radius+w.radius+.45;
      if(pd>0&&pd<space){vx+=px/pd*(space-pd)*3;vz+=pz/pd*(space-pd)*3;}
      const speed=Math.hypot(vx,vz),limit=p.speed;if(speed>limit){vx*=limit/speed;vz*=limit/speed;}
      w.vx+=(vx-w.vx)*Math.min(1,dt*7);w.vz+=(vz-w.vz)*Math.min(1,dt*7);
      let nx=w.x+w.vx*dt,nz=w.z+w.vz*dt;
      if(!w.crossing&&!this.sidewalks.walkable({x:nx,z:nz})) {
        // Slide along the walkable corridor while avoiding buildings and furniture.
        if(this.sidewalks.walkable({x:nx,z:w.z}))nz=w.z;
        else if(this.sidewalks.walkable({x:w.x,z:nz}))nx=w.x;
        else{nx=w.x;nz=w.z;w.vx=0;w.vz=0;}
      }
      if(w.crossing) {
        // Stay inside the zebra band while giving oncoming walkers room to pass.
        if(Math.abs(target.x)<10&&Math.abs(dx)<.3)nx=Math.max(target.x-.65,Math.min(target.x+.65,nx));
        if(Math.abs(target.z)<10&&Math.abs(dz)<.3)nz=Math.max(target.z-.65,Math.min(target.z+.65,nz));
      }
      const moved=Math.hypot(nx-w.x,nz-w.z);w.x=nx;w.z=nz;w.travelled+=moved;w.gait+=moved*7.5;
      w.stalled=!w.waiting&&!w.crossing&&moved/dt<.15 ? w.stalled+dt : 0;
      if(w.stalled>2.5){w.stalled=0;this.plan(w,p);}
      w.speed+=(moved/dt-w.speed)*Math.min(1,dt*9);
      if(moved>.0005){const yaw=Math.atan2(w.vx,w.vz);w.yaw+=Math.atan2(Math.sin(yaw-w.yaw),Math.cos(yaw-w.yaw))*Math.min(1,dt*8);}
    });
  }
}
