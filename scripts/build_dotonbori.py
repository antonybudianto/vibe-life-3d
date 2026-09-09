"""Blender-authored Dotonbori canal district. Z-up geometry, Y-up navigation.

blender -b -t 8 --python-exit-code 1 --python scripts/build_dotonbori.py
Then run bake_dotonbori.py. Geometry is authored here; selected sign prints
are rectified from the user's concept boards inside Blender.
"""
import bpy, math, random, sys, json
import numpy as np
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1]
layout=json.loads((ROOT/'lib/game/dotonbori-layout.json').read_text())
sys.path.insert(0,str(ROOT/'scripts'))
import scene_geometry as g
from blender_lighting import apply_preset
random.seed(92026)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
g.M.clear();g.B.clear();g.TEXT.clear()
font=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
jp=bpy.data.fonts.load('C:/Windows/Fonts/YuGothB.ttc')
def mat(n,c,r=.65,m=0,e=0):return g.material('Dotonbori '+n,c,r,m,e)
stone=mat('limestone',(.39,.38,.36),.86)
cap=mat('bridge coping',(.59,.57,.53),.75)
paving=mat('promenade paving',(.24,.235,.24),.54)
joint=mat('paving joints',(.12,.13,.14),.9)
dark=mat('graphite steel',(.025,.038,.052),.38,.65)
silver=mat('brushed rails',(.37,.40,.44),.3,.72)
wood=mat('cedar',(.23,.095,.034),.7)
glass=mat('shop glass',(.021,.044,.068),.2,.5)
cream=mat('ivory',(.83,.79,.67),.68)
white=mat('white sign',(.92,.95,1),.4,0,.65)
red=mat('vermilion enamel',(.72,.018,.025),.26,.25)
black=mat('ink',(.008,.014,.031),.8)
neonred=mat('red neon',(.8,.0015,.004),.35,0,1.25)
blue=mat('cobalt neon',(.0015,.027,.72),.4,0,1)
cyan=mat('cyan neon',(.015,.6,.96),.4,0,1.25)
yellow=mat('gold light',(.99,.54,.026),.4,0,.8)
warm=mat('lantern glow',(1,.36,.07),.36,0,3.2)
windows=[mat('interior amber '+str(i),c,.62,0,e) for i,(c,e) in enumerate([((.40,.18,.055),.5),((.65,.32,.10),.7),((.23,.12,.065),.25),((.018,.03,.045),0)])]
pink=mat('pink neon',(.94,.04,.25),.4,0,1.5)
green=mat('green neon',(.025,.49,.19),.5,0,.85)
orange=mat('orange sign',(.98,.12,.014),.5,0,.8)
boatmat=mat('cruise yellow enamel',(.98,.58,.008),.31,.12)
water=mat('canal water',(.008,.045,.058),.13,.45)
water.node_tree.nodes['Principled BSDF'].inputs['IOR'].default_value=1.333
water['water_surface']=True
facades=[mat('facade '+str(i),c,.82) for i,c in enumerate([(.21,.245,.28),(.38,.36,.33),(.14,.17,.21),(.47,.46,.41),(.28,.24,.235),(.18,.22,.25)])]
leaves=[mat('leaves '+str(i),c,.8) for i,c in enumerate([(.018,.065,.02),(.04,.12,.027),(.095,.18,.038),(.035,.09,.046),(.17,.23,.06)])]
for m in leaves:m.use_backface_culling=False
skin=mat('pedestrian skin',(.58,.33,.20),.78)
hair=mat('pedestrian hair',(.018,.012,.012),.78)
coats=[mat('pedestrian coat '+str(i),c,.9) for i,c in enumerate([(.59,.60,.59),(.035,.06,.095),(.28,.10,.095),(.72,.63,.40),(.18,.27,.24),(.57,.34,.39)])]
colliders=[];surfaces=[]
def collider(x,y,hx,hy,height=1.2,**kw):
    colliders.append(dict(x=x,z=-y,halfX=hx,halfZ=hy,height=height,**kw))
def lamp(x,y,z=0):
    g.box((x,y,z+.12),(.45,.45,.24),stone)
    g.rod((x,y,z+.23),(x,y,z+2.8),.065,dark)
    g.box((x,y,z+2.9),(.40,.40,.62),warm)
    for dx in [-.23,.23]:
        for dy in [-.23,.23]:g.rod((x+dx,y+dy,z+2.53),(x+dx,y+dy,z+3.26),.023,dark,6)
    for zz in [2.52,3.27]:g.box((x,y,z+zz),(.55,.55,.085),dark)
    collider(x,y,.23,.23,z+3.32,cameraMinY=z,cameraRadius=.28)
def rail(a,b,z):
    length=(Vector(b)-Vector(a)).length
    for h in [.25,.65,1.1]:g.rod((*a,z+h),(*b,z+h),.035,silver,8)
    for i in range(math.ceil(length/.65)+1):
        t=i/math.ceil(length/.65);x=a[0]+(b[0]-a[0])*t;y=a[1]+(b[1]-a[1])*t
        g.rod((x,y,z+.07),(x,y,z+1.15),.033,dark,6)
def tree(x,y):
    g.box((x,y,.20),(1.5,1.5,.4),stone)
    g.box((x,y,.40),(1.3,1.3,.035),wood)
    trunk=Vector((x+.13,y-.06,2.85))
    g.rod((x,y,.42),trunk,.105,wood,10,r2=.06)
    # Open branching structure and thousands of individual folded leaf blades.
    # There are no opaque spheres inside these canopies.
    for branch in range(11):
        a=branch*2.399;reach=random.uniform(.65,1.45)
        tip=Vector((x+math.cos(a)*reach,y+math.sin(a)*reach,random.uniform(3.8,5.2)))
        fork=trunk.lerp(tip,.52)
        g.rod(trunk,fork,.057,wood,7,r2=.03);g.rod(fork,tip,.03,wood,6,r2=.008)
        for twig in range(5):
            az=random.uniform(0,math.tau)
            end=tip+Vector((math.cos(az)*.63,math.sin(az)*.63,random.uniform(-.45,.48)))
            g.rod(fork.lerp(tip,.72),end,.013,wood,5,r2=.003)
            for k in range(48):
                center=end+Vector((random.gauss(0,.30),random.gauss(0,.30),random.gauss(0,.24)))
                rot=Matrix.Rotation(random.uniform(-math.pi,math.pi),3,'X')@Matrix.Rotation(random.uniform(0,math.tau),3,'Z')
                length=random.uniform(.11,.20);w=length*.56
                points=[(-length,0,0),(0,-w,0),(0,0,.025),(0,w,0),(length,0,0)]
                g.mesh([tuple(center+rot@Vector(p)) for p in points],[(0,1,2),(0,2,3),(2,1,4),(3,2,4)],random.choice(leaves))
            if twig<2:g.sphere(tuple(end),(.025,.025,.032),warm,6,4)
    for i in range(24):
        a=i*.9;z=.9+i*.085
        g.sphere((x+.12*math.cos(a),y+.12*math.sin(a),z),(.018,.018,.026),warm,6,4)
    collider(x,y,.78,.78,.42,cameraRadius=.14)
    collider(x,y,.12,.12,6.0,cameraRadius=1.4)
def umbrella(x,y):
    g.rod((x,y,0),(x,y,2.8),.035,wood)
    v=[(x,y,2.96)]+[(x+1.2*math.cos(i*math.tau/8),y+1.2*math.sin(i*math.tau/8),2.58) for i in range(8)]
    g.mesh(v,[(0,i+1,(i+1)%8+1) for i in range(8)],cream)
    g.rod((x,y,0),(x,y,.76),.12,dark)
    g.rod((x,y,.74),(x,y,.81),.59,wood,20)
    for yy in [-.8,.8]:
        g.box((x,y+yy,.47),(.6,.5,.07),wood)
        g.box((x,y+yy*1.22,.80),(.6,.06,.5),wood)
        for xx in [-.22,.22]:g.rod((x+xx,y+yy,0),(x+xx,y+yy,.47),.03,dark)
    collider(x,y,.66,1.1,.85)

def paving_joints(side,start,stop):
    """Keep the same tile grid and global phase across every promenade segment."""
    for y in range(math.floor(start/2)*2+1,math.ceil(stop),2):
        for x in [9.4,11.4,13.4,15.4,17.4]:
            g.box((side*x,y,.006),(1.97,.014,.012),joint)
    for x in [9,11,13,15,17,19]:
        g.box((side*x,(start+stop)/2,.006),(.012,stop-start,.012),joint)

# Retaining walls and full-width promenade. Water is lower than the walking deck.
from dotonbori_streetscape import paving_segment, details as streetscape_details
g.box((0,0,-2.05),(70,150,.7),joint)
for side in [-1,1]:
    paving_segment(globals(),side,-70,70)
    g.box((side*8.3,0,-1.1),(.62,140,2.2),stone)
    g.box((side*8.35,0,.035),(.7,140,.07),cap)
    for y in range(-69,70,2):
        g.box((side*8.0,y,-1.02),(.012,.015,1.98),joint)
    paving_joints(side,-70,70)
    for y in [-65,-56,-39,-28,-18,-9,12,23,34,57,66]:
        if abs(y)<7 or min(abs(y-b) for b in [-48,0,48])<5:continue
        lamp(side*8.9,y)
        g.box((side*7.96,y,-.65),(.05,.36,.65),warm)
    for lo,hi in [(-70,-52),(-44,-5.5),(5.5,44),(52,70)]:
        rail((side*8.38,lo),(side*8.38,hi),.08)
        collider(side*8.37,(lo+hi)/2,.08,(hi-lo)/2,1.28)
    # The central riverwalk is a working urban frontage, not a planted boulevard.
    for y in ([-59,60] if side==-1 else [60]):tree(side*16.7,y)

# Rounded Ebisubashi plaza and ramps; secondary crossings retain stair access.
def bridge(y,main=True):
    half=3.8 if main else 3.4;top=2.55 if main else 1.8;crown=.24 if main else .14
    name='Ebisubashi deck' if main else 'Canal footbridges'
    def elevation(x):return top+crown*max(0,1-(x/8.5)**2)
    def edge(x):return max(half,math.sqrt(max(0,6.9**2-x*x))) if main else half
    # Slight arch, deep segmented stone fascia and continuous bridge railing.
    for j in range(24):
        a=-8.5+j*17/24;b=-8.5+(j+1)*17/24;ha=elevation(a);hb=elevation(b)
        ea,eb=edge(a),edge(b)
        if not main:g.mesh([(a,y-ea,ha),(b,y-eb,hb),(b,y+eb,hb),(a,y+ea,ha)],[(0,1,2,3)],cap,name)
        # The reflection camera sees the real underside. A top-only bridge lets
        # billboards show through its back faces in the water.
        g.mesh([(a,y+ea,ha-.94),(b,y+eb,hb-.94),(b,y-eb,hb-.94),(a,y-ea,ha-.94)],[(0,1,2,3)],stone,'Bridge solid soffits')
        surfaces.append(dict(minX=a,maxX=b,minZ=-y-ea,maxZ=-y+ea,endMinZ=-y-eb,endMaxZ=-y+eb,height=ha,endHeight=hb))
        for sgn in [-1,1]:
            yy=y+sgn*ea;yb=y+sgn*eb
            entrance=main and j in [11,12]
            # The ramp's retaining wall owns this elevation outside the entry.
            # A second fascia here overlaps it and flickers after GLB export.
            if not main or entrance:
                g.mesh([(a,yy,ha),(b,yb,hb),(b,yb,hb-.94),(a,yy,ha-.94)],[(0,1,2,3) if sgn==1 else (3,2,1,0)],silver if main else stone)
            if not main:g.rod((a,yy,ha-.92),(a,yy,ha-.02),.012,joint,4)
            if main and not entrance:
                from dotonbori_bridge import parapet
                parapet(globals(),(a,yy,ha),(b,yb,hb))
            elif not entrance:
                for h in [.12,.65,1.10]:g.rod((a,yy,ha+h),(b,yb,hb+h),.04,silver,8)
                for t in ([0,.2,.4,.6,.8] if main else [0,.5]):
                    x=a+(b-a)*t;z=ha+(hb-ha)*t
                    g.rod((x,yy+(yb-yy)*t,z+.1),(x,yy+(yb-yy)*t,z+1.15),.026,silver if main else dark,6)
            if main and not entrance:
                # Small AABBs follow the curved rail without cutting off the plaza.
                for k in range(4):
                    ta=k/4;tb=(k+1)/4
                    xa=a+(b-a)*ta;xb=a+(b-a)*tb;ya=yy+(yb-yy)*ta;yc=yy+(yb-yy)*tb
                    collider((xa+xb)/2,(ya+yc)/2,(xb-xa)/2+.012,abs(yc-ya)/2+.035,top+crown+1.2,cameraMinY=top-.95)
        if not main:g.box(((a+b)/2,y,(ha+hb)/2+.012),(.014,(ea+eb),.018),joint)
    for x in ([-8.0,8.0] if main else [-5.9,5.9]):
        soffit=elevation(x)-.94
        g.box((x,y,(-1.8+soffit)/2),(.75,half*2-.3,soffit+1.8),stone,name='Bridge support piers')
        g.box((x,y,soffit-.12),(1.25,half*2,.28),cap,name='Bridge pier capitals')
    for end in ([] if main else [-1,1]):
        for x in [-8,-4,0,4,8]:
            z=elevation(x)
            g.box((x,y+end*half,z+.53),(.34,.30,1.10),stone)
            g.box((x,y+end*half,z+1.13),(.47,.43,.14),cap)
    for sgn in [-1,1]:
        yy=y+sgn*half
        if not main:collider(0,yy,8.5,.055,top+crown+1.2,cameraMinY=top-.95)
        if not main:g.text('道 頓 堀',(0,y+sgn*(edge(0)+.022),top+crown-.5),.45,black,0 if sgn==-1 else math.pi,font=jp)
    # Both banks have a broad upper landing and two real flights along the canal.
    count=20 if main else 15;run=6.8 if main else 5.4;rise=top/count;tread=run/count
    for side in [-1,1]:
        x=side*11.0;lo=8.5;hi=13.5
        if not main:g.mesh([(side*lo,y-half,top),(side*hi,y-half,top),(side*hi,y+half,top),(side*lo,y+half,top)],[(0,1,2,3) if side==1 else (3,2,1,0)],cap,name)
        g.box((x,y,top-.26),(4.95,half*2,.50),stone,name='Bridge landing soffits')
        surfaces.append(dict(minX=min(side*lo,side*hi),maxX=max(side*lo,side*hi),minZ=-y-half,maxZ=-y+half,height=top))
        g.box((side*13.42,y,top-.48),(.18,half*2,.96),stone)
        rail((side*13.48,y-half),(side*13.48,y+half),top)
        collider(side*13.48,y,.06,half,top+1.2)
        stairx=side*12 if main else x;stairwidth=2.95 if main else 4.95
        for end in [-1,1]:
            for i in range(count):
                yy=y+end*(half+(count-i-.5)*tread);height=(i+1)*rise
                # Separate vertex-baked risers and planar-UV tread surfaces.
                g.box((stairx,yy,height/2),(stairwidth,tread,height),stone,name='Bridge stair risers')
                sw=stairwidth/2
                g.mesh([(stairx-sw,yy-tread/2,height+.008),(stairx+sw,yy-tread/2,height+.008),(stairx+sw,yy+tread/2,height+.008),(stairx-sw,yy+tread/2,height+.008)],[(0,1,2,3)],cap,name)
                surfaces.append(dict(minX=stairx-sw-.025,maxX=stairx+sw+.025,minZ=-yy-tread/2,maxZ=-yy+tread/2,height=height+.008))
                g.box((stairx,yy+end*(tread/2-.025),height+.022),(stairwidth-.05,.042,.025),silver)
            for xx in [side*(10.52 if main else 8.52),side*13.48]:
                a=(xx,y+end*half,top+1.1);b=(xx,y+end*(half+run),1.1)
                g.rod(a,b,.05,silver,10)
                for i in range(count+1):
                    t=i/count;yy=y+end*(half+t*run);h=top*(1-t)
                    g.rod((xx,yy,h),(xx,yy,h+1.1),.034,dark,8)
                collider(xx,y+end*(half+run/2),.06,run/2,top+1.2)
            lamp(side*13.0,y+end*(half-.25),top)
        g.box((side*8.2,y,(top-1.6)/2),(.65,half*2,top+1.6),stone)
    if main:
        from dotonbori_bridge import paving as bridge_paving
        bridge_paving(globals(),y,edge,elevation)
        from dotonbori_realism import perimeter_ramps
        perimeter_ramps(globals(),y,edge,top+crown)
for y in [-48,0,48]:bridge(y,y==0)
for lo,hi in [(-70,-51.4),(-44.6,-8.6),(8.6,44.6),(51.4,70)]:
    collider(0,(lo+hi)/2,8.22,(hi-lo)/2,0,cameraIgnore=True)

# Blender water grid: wave geometry catches dynamic sunlight in the game.
from dotonbori_water_geometry import build as build_water
build_water(g,water,layout)

# Facade coordinates: u follows the canal, v projects out from each storefront.
frontages={}
def pos(side,y,u,v,h):return (side*(frontages.get((side,y),19)-v),y+u,h)
def panel(side,y,u,h,w,height,background,label='',ink=None,size=None):
    angle=-side*math.pi/2
    g.box(pos(side,y,u,.64,h),(.24,w+.13,height+.13),dark)
    g.panel(pos(side,y,u,.785,h),w,height,background,angle)
    if label:
        japanese=any(ord(c)>128 for c in label)
        lines=label.split('\n')
        fitted=min((size*1.15) if size else height*.80/len(lines),w/max(max(map(len,lines))*(.94 if japanese else .64),1),height*.90/len(lines))
        g.text(label,pos(side,y,u,.81,h),fitted,ink or white,angle,font=jp if japanese else font)
def vertical(side,y,u,h,label,bg,height=8,w=1.35,ink=None):
    panel(side,y,u,h,w,height,bg)
    for i,c in enumerate(label):
        step=height*.90/max(len(label),1);glyph=w*1.13
        o=g.text(c,pos(side,y,u,.83,h+(len(label)-1)*step/2-i*step),glyph,ink or (white if bg in [neonred,blue,black] else black if bg==yellow else neonred),-side*math.pi/2,font=jp)
        o.scale.y=min(2.8,step/glyph*1.10)

def artwork(name,corners,width=512,height=1024,source_name='dotonbori-south.png',reference_size=(1448,1086),perspective=False):
    # Rectify the supplied sign artwork inside Blender. Only individual signs
    # become textures; the streets, landmarks and all depth remain modeled.
    source=bpy.data.images.load(str(ROOT/'assets/references'/source_name),check_existing=True)
    sw,sh=source.size;pixels=np.asarray(source.pixels[:],dtype=np.float32).reshape(sh,sw,4)
    u,v=np.meshgrid(np.linspace(0,1,width),np.linspace(1,0,height))
    a,b,c,d=[np.asarray(p)*np.array([sw/reference_size[0],sh/reference_size[1]]) for p in corners]
    if perspective:
        rows=[];values=[]
        for (uu,vv),(xx,yy) in zip([(0,0),(1,0),(1,1),(0,1)],[a,b,c,d]):
            rows.extend([[uu,vv,1,0,0,0,-xx*uu,-xx*vv],[0,0,0,uu,vv,1,-yy*uu,-yy*vv]]);values.extend([xx,yy])
        h=np.linalg.solve(np.asarray(rows),np.asarray(values));den=h[6]*u+h[7]*v+1
        coords=np.stack([(h[0]*u+h[1]*v+h[2])/den,(h[3]*u+h[4]*v+h[5])/den],axis=-1)
    else:coords=(1-v[...,None])*((1-u[...,None])*a+u[...,None]*b)+v[...,None]*((1-u[...,None])*d+u[...,None]*c)
    xx=np.clip(coords[...,0],0,sw-1);yy=np.clip(sh-1-coords[...,1],0,sh-1)
    x0=xx.astype(int);y0=yy.astype(int);x1=np.minimum(x0+1,sw-1);y1=np.minimum(y0+1,sh-1)
    fx=(xx-x0)[...,None];fy=(yy-y0)[...,None]
    samples=(pixels[y0,x0]*(1-fx)+pixels[y0,x1]*fx)*(1-fy)+(pixels[y1,x0]*(1-fx)+pixels[y1,x1]*fx)*fy
    im=bpy.data.images.new('Dotonbori reference '+name,width,height);im.pixels.foreach_set(samples.astype(np.float32).reshape(-1));im.pack()
    m=mat('artwork '+name,(1,1,1),.54,0,.65)
    n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;p=m.node_tree.nodes['Principled BSDF']
    m.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(n.outputs['Color'],p.inputs['Emission Color'])
    return m

labels=['たこ焼','大阪王将','串かつ','道頓堀','居酒屋','らーめん','焼肉','寿司','うどん','珈琲','お好み焼','餃子']
signs=[neonred,white,blue,yellow,white,neonred,cream,white]
from dotonbori_architecture import build as build_architecture
architecture=build_architecture(globals())

# Advertising composition follows the selected north/south concept.
def campaign(side,y,u,h,w,height,name,corners,source='dotonbori-north-v2.png'):
    panel(side,y,u,h,w,height,white)
    g.panel(pos(side,y,u,.91,h),w,height,artwork(name,corners,512,1024,source),-side*math.pi/2)
    for edge in [-1,1]:
        g.box(pos(side,y,u+edge*(w/2+.09),.81,h),(.35,.12,height+.22),silver)
    for z in [h-height/2-.09,h+height/2+.09]:g.box(pos(side,y,u,.81,z),(.35,w+.3,.12),silver)

# Official sixth-generation panel dimensions, including the masthead.
campaign(-1,11.5,2.0,19.0,10.38,20.0,'Glico north',[(791,174),(919,174),(919,438),(791,438)])
# The adjacent sign is Snow Brand / 6P cheese, not the concept's city artwork.
from dotonbori_billboards import snow_brand
snow_brand(globals())
campaign(-1,28.5,-2.7,26.0,4.55,8.7,'Estem north',[(927,211),(1008,211),(1008,287),(927,287)])
campaign(-1,28.5,2.7,26.0,4.55,8.7,'Promise north',[(1014,209),(1084,209),(1084,293),(1014,293)])
campaign(-1,28.5,0,18.8,9.9,4.8,'Gam City',[(1022,294),(1126,294),(1126,339),(1022,339)])
campaign(-1,28.5,0,12.7,9.9,6.6,'Chintai north',[(928,357),(1036,357),(1036,415),(928,415)])
# Asahi's two billboard faces are authored with its full corner building.

# Giant Kani Doraku crab. Broad domed shell, articulated legs and large pincers.
def crab(side,y,h):
    def p(u,v,z):return pos(side,y,u*1.65,v,h+z*1.42)
    enamel=mat('illuminated crab enamel',(.86,.022,.012),.21,.18,.22)
    seam=mat('crab shell ridges',(1,.19,.075),.25,.28,.32)
    g.box(p(0,.28,0),(.45,14.8,9),white)
    g.sphere(p(0,1.25,0),(.88,2.18,1.53),enamel,28,18)
    for sign in [-1,1]:
        points=[]
        for i in range(21):
            z=(i/20*2-1)*.88;u=sign*(.47+.14*(z/.88)**2)
            depth=1.25+.88*math.sqrt(max(0,1-(u*1.65/2.18)**2-(z*1.42/1.53)**2))
            points.append(p(u,depth+.016,z))
        for a,b in zip(points,points[1:]):g.rod(a,b,.027,seam,8)
    for sgn in [-1,1]:
        for k in range(4):
            a=p(sgn*.8,1.15,.35-k*.35);b=p(sgn*(2.1+k*.18),1.4,.9-k*.72);c=p(sgn*(3.1+k*.18),1.22,.62-k*.84)
            g.rod(a,b,.27,enamel,12,r2=.31);g.rod(b,c,.31,enamel,12,r2=.10);g.sphere(b,(.32,.32,.32),enamel,12,8)
        g.rod(p(sgn*.75,1.35,.65),p(sgn*1.5,1.5,1.8),.32,enamel,12)
        g.sphere(p(sgn*1.75,1.53,2.14),(.40,.70,.79),enamel,20,12)
        for off in [-.27,.27]:g.rod(p(sgn*1.75+off,1.54,2.3),p(sgn*1.75+off*.65,1.58,2.83),.23,enamel,12,r2=.055)
        g.rod(p(sgn*.44,1.45,.67),p(sgn*.5,1.58,1.22),.065,enamel)
        g.sphere(p(sgn*.5,1.59,1.23),(.095,.105,.13),black,12,8)
    panel(side,y,0,h-5.2,14.8,1.75,white,'かに道楽',black,1.45)
# The restaurant frontage belongs on Dotonbori Street, behind the south bank.
# Mirror only this sign assembly to the street-facing rear of the canal block.
frontages[1,-23.8]=-29.8
crab(1,-23.8,7.5)
vertical(1,-23.8,8.35,8.0,'本場の味',white,11,1.3)
# Traditional Kani Doraku surround: pale vertical slats, tiled eaves and lanterns.
for u in np.linspace(-7.5,7.5,50):g.box(pos(1,-23.8,float(u),.65,7.5),(.2,.11,9.2),cream)
for row in range(4):
    for u in np.linspace(-7.8,7.8,50):
        g.rod(pos(1,-23.8,float(u),.6+row*.23,12.35-row*.10),pos(1,-23.8,float(u),.83+row*.23,12.25-row*.10),.10,dark,8)
for u in np.linspace(-7.3,7.3,26):g.sphere(pos(1,-23.8,float(u),1.1,11.9),(.18,.20,.25),warm,10,7)

# Kukuru and Acchichi Honpo are authored with their tenant frontages in
# dotonbori_takoyaki.py, replacing the former unbranded rear octopus.

# Present-day riverfront: no retired Zuboraya lantern on the north bank.
from dotonbori_realism import wheel, river_details
wheel(globals())
river_details(globals())

# The two open-deck vessels are added after the static scenery is batched.
from dotonbori_background import build as build_background
background=build_background(globals())
streetscape_details(globals())
objects=g.flush()
from dotonbori_cruises import build_cruises
objects+=build_cruises(globals())

# On-foot visitors use the same animated pedestrian asset as Shibuya at runtime.
# Boat passengers remain part of their moving vessel; no static walkers are baked.

# Practical light spill is baked separately from the sun.
for side in [-1,1]:
    for i,y in enumerate(range(-150,151,10)):
        bpy.ops.object.light_add(type='AREA',location=(side*17.6,y,3.1));o=bpy.context.object
        power=[95,180,65,130,80][(i+(side+1))%5]
        o.name='Dotonbori shop spill';o.data.energy=power;o.data.color=[(1,.50,.24),(1,.72,.44),(.55,.71,1)][i%3];o.data.shape='DISK';o.data.size=3.2
        o.rotation_euler=(Vector((side*13.8,y,0))-o.location).to_track_quat('-Z','Y').to_euler();o['baked_shop']=True;o['base_power']=power
# Sign-matched pools point onto the near pavement instead of across the river.
for side,y,z,color,power in [(-1,13.5,15,(.08,.28,1),1100),(-1,-9,12,(1,.56,.14),950),(-1,28.5,10,(.16,.32,1),850),(1,-40,10,(1,.38,.07),750)]:
    bpy.ops.object.light_add(type='AREA',location=(side*16.8,y,z));o=bpy.context.object;o.data.energy=power;o.data.color=color;o.data.shape='RECTANGLE';o.data.size=7;o.data.size_y=5
    o.name='Dotonbori billboard pavement spill'
    o.rotation_euler=(Vector((side*12.7,y,0))-o.location).to_track_quat('-Z','Y').to_euler();o['baked_shop']=True;o['base_power']=power
bpy.ops.object.light_add(type='SUN');bpy.context.object.name='Dotonbori sun'
bpy.context.scene.world=bpy.data.worlds.new('Dotonbori sky')
bpy.context.scene['location_id']='dotonbori'
apply_preset('evening')
bpy.ops.object.camera_add(location=(3,-42,7.6));cam=bpy.context.object;cam.name='Dotonbori review camera'
cam.rotation_euler=(Vector((-1,5,10))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=26
s=bpy.context.scene;s.camera=cam;s.render.resolution_x=1500;s.render.resolution_y=1000;s.render.resolution_percentage=100
s['design_reference']='Photo-informed Ebisubashi plaza, retail corner buildings and Ebisu Tower; compact stylized reconstruction'
s['bridge_navigation']='Rounded Ebisubashi plaza, four straight bank stairs, separate curved perimeter ramps with central entrances and lower landings'
s['pedestrian_count']=36
data=dict(id='dotonbori',name='Osaka Dotonbori',spawn=[10.8,0,18],bounds=[-18.8,18.8,-layout['promenadeEnd'],layout['promenadeEnd']],colliders=colliders,surfaces=surfaces,pedestrians=36,cruises=2,artRevision=12,architecture=architecture,background=background)
(ROOT/'public/models/dotonbori.json').write_text(json.dumps(data,indent=2))
if '--navigation-only' in sys.argv:
    print('DOTONBORI_NAVIGATION_UPDATED',len(colliders),flush=True)
    sys.exit(0)
g.export_atomic(ROOT/'public/models/dotonbori.glb',objects)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/dotonbori.blend'),compress=True)
print('DOTONBORI_AUTHORED',len(objects),len(colliders),flush=True)
