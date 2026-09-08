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
boatmat=mat('cruise yellow',(.94,.47,.015),.35,.22)
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

# Retaining walls and full-width promenade. Water is lower than the walking deck.
g.box((0,0,-2.05),(70,150,.7),joint)
for side in [-1,1]:
    g.box((side*13.5,0,-.27),(11,140,.54),paving)
    g.box((side*8.3,0,-1.1),(.62,140,2.2),stone)
    g.box((side*8.35,0,.035),(.7,140,.07),cap)
    for y in range(-69,70,2):
        g.box((side*8.0,y,-1.02),(.012,.015,1.98),joint)
        for x in [9.4,11.4,13.4,15.4,17.4]:g.box((side*x,y,.006),(1.97,.014,.012),joint)
    for x in [9,11,13,15,17,19]:g.box((side*x,0,.006),(.012,140,.012),joint)
    for y in range(-65,66,7):
        if min(abs(y-b) for b in [-48,0,48])<5:continue
        lamp(side*8.9,y)
        g.box((side*7.96,y,-.65),(.05,.36,.65),warm)
    for lo,hi in [(-70,-52),(-44,-4.2),(4.2,44),(52,70)]:
        rail((side*8.38,lo),(side*8.38,hi),.08)
        collider(side*8.37,(lo+hi)/2,.08,(hi-lo)/2,1.28)
    for y in [-59,-32,-18,18,33,60]:tree(side*16.7,y)
    for y in [-25,24,57]:umbrella(side*17,y)

# Stone bridges with longitudinal stairs, matching the concept's riverbank access.
def bridge(y,main=True):
    half=3.8 if main else 3.4;top=2.55 if main else 1.8;crown=.24 if main else .14
    name='Ebisubashi deck' if main else 'Canal footbridges'
    def elevation(x):return top+crown*max(0,1-(x/8.5)**2)
    # Slight arch, deep segmented stone fascia and continuous bridge railing.
    for j in range(24):
        a=-8.5+j*17/24;b=-8.5+(j+1)*17/24;ha=elevation(a);hb=elevation(b)
        g.mesh([(a,y-half,ha),(b,y-half,hb),(b,y+half,hb),(a,y+half,ha)],[(0,1,2,3)],cap,name)
        surfaces.append(dict(minX=a,maxX=b,minZ=-y-half,maxZ=-y+half,height=ha,endHeight=hb))
        for sgn in [-1,1]:
            yy=y+sgn*half
            g.mesh([(a,yy,ha),(b,yy,hb),(b,yy,hb-.94),(a,yy,ha-.94)],[(0,1,2,3),(3,2,1,0)],stone)
            g.rod((a,yy,ha-.92),(a,yy,ha-.02),.012,joint,4)
            for h in [.12,.65,1.10]:g.rod((a,yy,ha+h),(b,yy,hb+h),.04,silver,8)
            for t in [0,.5]:
                x=a+(b-a)*t;z=ha+(hb-ha)*t
                g.rod((x,yy,z+.1),(x,yy,z+1.15),.026,dark,6)
        g.box(((a+b)/2,y,(ha+hb)/2+.012),(.014,half*2,.018),joint)
    for sgn in [-1,1]:
        yy=y+sgn*half
        collider(0,yy,8.5,.055,top+crown+1.2,cameraMinY=top-.95)
        g.text('え び す 橋' if main else '道 頓 堀',(0,yy+sgn*.022,top+crown-.5),.64 if main else .45,black,0 if sgn==-1 else math.pi,font=jp)
    # Both banks have a broad upper landing and two real flights along the canal.
    count=20 if main else 15;run=6.8 if main else 5.4;rise=top/count;tread=run/count
    for side in [-1,1]:
        x=side*11.0;lo=8.5;hi=13.5
        g.mesh([(side*lo,y-half,top),(side*hi,y-half,top),(side*hi,y+half,top),(side*lo,y+half,top)],[(0,1,2,3),(3,2,1,0)],cap,name)
        surfaces.append(dict(minX=min(side*lo,side*hi),maxX=max(side*lo,side*hi),minZ=-y-half,maxZ=-y+half,height=top))
        g.box((side*13.42,y,top-.48),(.18,half*2,.96),stone)
        rail((side*13.48,y-half),(side*13.48,y+half),top)
        collider(side*13.48,y,.06,half,top+1.2)
        for end in [-1,1]:
            for i in range(count):
                yy=y+end*(half+(count-i-.5)*tread);height=(i+1)*rise
                # Separate vertex-baked risers and planar-UV tread surfaces.
                g.box((x,yy,height/2),(4.95,tread,height),stone,name='Bridge stair risers')
                g.mesh([(x-2.48,yy-tread/2,height+.008),(x+2.48,yy-tread/2,height+.008),(x+2.48,yy+tread/2,height+.008),(x-2.48,yy+tread/2,height+.008)],[(0,1,2,3)],cap,name)
                surfaces.append(dict(minX=x-2.5,maxX=x+2.5,minZ=-yy-tread/2,maxZ=-yy+tread/2,height=height+.008))
                g.box((x,yy+end*(tread/2-.025),height+.022),(4.9,.042,.025),silver)
            for xx in [side*8.52,side*13.48]:
                a=(xx,y+end*half,top+1.1);b=(xx,y+end*(half+run),1.1)
                g.rod(a,b,.05,silver,10)
                for i in range(count+1):
                    t=i/count;yy=y+end*(half+t*run);h=top*(1-t)
                    g.rod((xx,yy,h),(xx,yy,h+1.1),.034,dark,8)
                collider(xx,y+end*(half+run/2),.06,run/2,top+1.2)
            lamp(side*13.0,y+end*(half-.25),top)
        g.box((side*8.2,y,(top-1.6)/2),(.65,half*2,top+1.6),stone)
for y in [-48,0,48]:bridge(y,y==0)
for lo,hi in [(-70,-51.4),(-44.6,-3.8),(3.8,44.6),(51.4,70)]:
    collider(0,(lo+hi)/2,8.22,(hi-lo)/2,0,cameraIgnore=True)

# Blender water grid: wave geometry catches dynamic sunlight in the game.
verts=[];faces=[]
for j in range(561):
    y=-70+j*.25
    for i in range(69):
        x=-8.5+i*.25;z=-1.43+.019*math.sin(x*4.3+y*7.7)+.012*math.sin(y*14-x*3.1)
        verts.append((x,y,z))
for j in range(560):
    for i in range(68):
        k=j*69+i;faces.append((k,k+1,k+70,k+69))
g.mesh(verts,faces,water,'Dotonbori canal water',True)

# Facade coordinates: u follows the canal, v projects out from each storefront.
def pos(side,y,u,v,h):return (side*(19-v),y+u,h)
def panel(side,y,u,h,w,height,background,label='',ink=None,size=None):
    angle=-side*math.pi/2
    g.box(pos(side,y,u,.64,h),(.24,w+.13,height+.13),dark)
    g.panel(pos(side,y,u,.785,h),w,height,background,angle)
    if label:g.text(label,pos(side,y,u,.81,h),size or min(w/max(len(label)*.56,1),height*.42),ink or white,angle,font=jp if any(ord(c)>128 for c in label) else font)
def vertical(side,y,u,h,label,bg,height=8,w=1.35):
    panel(side,y,u,h,w,height,bg)
    for i,c in enumerate(label):
        o=g.text(c,pos(side,y,u,.83,h+height*.37-i*height*.74/max(1,len(label)-1)),w*1.05,white if bg in [neonred,blue,black] else black if bg==yellow else neonred,-side*math.pi/2,font=jp)
        o.scale.y=min(1.8,height*.82/len(label)/w)

def artwork(name,corners,width=512,height=1024):
    # Rectify the supplied sign artwork inside Blender. Only individual signs
    # become textures; the streets, landmarks and all depth remain modeled.
    source=bpy.data.images.load(str(ROOT/'assets/references/dotonbori-south.png'),check_existing=True)
    sw,sh=source.size;pixels=np.asarray(source.pixels[:],dtype=np.float32).reshape(sh,sw,4)
    u,v=np.meshgrid(np.linspace(0,1,width),np.linspace(1,0,height))
    a,b,c,d=[np.asarray(p)*np.array([sw/1448,sh/1086]) for p in corners]
    coords=(1-v[...,None])*((1-u[...,None])*a+u[...,None]*b)+v[...,None]*((1-u[...,None])*d+u[...,None]*c)
    xx=np.clip(coords[...,0].astype(int),0,sw-1);yy=np.clip((sh-1-coords[...,1]).astype(int),0,sh-1)
    im=bpy.data.images.new('Dotonbori reference '+name,width,height);im.pixels.foreach_set(pixels[yy,xx].reshape(-1));im.pack()
    m=mat('artwork '+name,(1,1,1),.54,0,.65)
    n=m.node_tree.nodes.new('ShaderNodeTexImage');n.image=im;p=m.node_tree.nodes['Principled BSDF']
    m.node_tree.links.new(n.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(n.outputs['Color'],p.inputs['Emission Color'])
    return m

labels=['たこ焼','大阪王将','串かつ','道頓堀','居酒屋','らーめん','焼肉','寿司','うどん','珈琲','お好み焼','餃子']
signs=[neonred,white,blue,yellow,white,neonred,cream,white]
for side in [-1,1]:
    for idx,y in enumerate(range(-65,66,10)):
        h=random.choice([19,22,25,28,32]);w=9.7
        if side==-1 and y in [-5,5,15]:h=33
        g.box((side*24.1,y,h/2),(10.2,w,h),facades[(idx+(side+1)*2)%len(facades)])
        collider(side*24.1,y,6.25,w/2,h)
        for level in range(1,int(h/3)):
            z=level*3+.8
            g.box((side*18.93,y,z-1.4),(.35,w,.19),silver)
            for u in [-3.4,-1.15,1.15,3.4]:
                g.box(pos(side,y,u,.055,z),(.08,1.83,2.04),glass)
                if (level+idx+int(u))%3:
                    interior=windows[(level+idx+round(u))%4]
                    g.panel(pos(side,y,u,.108,z),1.65,1.83,interior,-side*math.pi/2)
                    g.box(pos(side,y,u,.2,z-.5),(.09,1.85,.09),dark)
                    g.box(pos(side,y,u,.2,z),(.09,.045,2.05),dark)
                    # Tables, pendant lights and shelves read through the glazing.
                    g.box(pos(side,y,u,.23,z-.51),(.21,1.2,.10),wood)
                    if level<4:
                        for off in [-.35,.35]:
                            g.box(pos(side,y,u+off,.19,z-.78),(.09,.09,.50),dark)
                        g.sphere(pos(side,y,u,.18,z+.5),(.09,.19,.12),cream,10,6)
            for u in [-4.75,0,4.75]:g.box(pos(side,y,u,.22,z),(.22,.13,2.9),facades[idx%6])
        # Recessed shop doors, transom, noren curtain, menus, lanterns.
        g.box(pos(side,y,0,.2,1.45),(.22,8.7,2.9),glass)
        for u in [-3,-1,1,3]:
            g.panel(pos(side,y,u,.33,1.5),1.8,2.7,windows[(idx+1)%3],-side*math.pi/2)
            g.box(pos(side,y,u-.93,.41,1.45),(.17,.09,2.9),wood)
            g.box(pos(side,y,u,.47,.58),(.15,1.85,.10),wood)
            g.box(pos(side,y,u,.57,.98),(.36,1.6,.10),wood)
            for k in range(5):g.rod(pos(side,y,u-.55+k*.27,.45,1.13),pos(side,y,u-.55+k*.27,.45,1.52),.052,green if k%2 else yellow,8)
            for off in [-.43,.43]:
                g.rod(pos(side,y,u+off,.90,.08),pos(side,y,u+off,.90,.62),.033,dark)
                g.sphere(pos(side,y,u+off,.9,.63),(.18,.18,.045),red,12,6)
        g.box(pos(side,y,0,.8,3.15),(1.5,9.9,.20),dark)
        panel(side,y,0,3.72,8.9,.95,cream,labels[idx%12],neonred,.62)
        for u in [-3.8,-2.85,-1.9,-.95,0,.95,1.9,2.85,3.8]:
            p=pos(side,y,u,.81,2.65);g.sphere(p,(.19,.25,.36),warm,10,7)
            g.rod((p[0],p[1],2.99),(p[0],p[1],3.12),.025,dark)
        vertical(side,y,side*3.3,12,labels[(idx+3)%12],signs[idx%8],12,2.25)
        panel(side,y,-side*1.2,6.0,5.0,2.9,signs[(idx+2)%8],labels[(idx+5)%12],None,1.02)
        vertical(side,y,-side*3.6,18,labels[(idx+7)%12],signs[(idx+4)%8],9,1.65)
        # Dense smaller projecting signs and stacked campaigns break the grid.
        for k in range(3):
            panel(side,y,-side*.75,10.0+k*3.2,3.6,2.5,signs[(idx+k+3)%8],labels[(idx+k+2)%12],neonred if (idx+k+3)%8 in [1,4,6,7] else white,1.05)
        vertical(side,y,side*1.5,min(h-3,24),labels[(idx+9)%12],signs[(idx+6)%8],6,1.7)
        if idx%2==0:
            g.box(pos(side,y,4.2,1.5,7.9),(2.1,.18,4.1),dark)
            # Perpendicular street signs stay visible looking along the river.
            g.panel((side*17.4,y+4.05,7.9),1.8,3.8,neonred,0)
            g.text('酒\n場',(side*17.4,y+4.02,7.9),.78,white,0,font=jp)
        # Roof enclosures, AC condensers, pipes and railings make orbit views complete.
        g.box((side*24,y,h+.18),(10.3,9.8,.36),stone)
        g.box((side*25,y+1,h+1.9),(4.2,3.2,3.8),facades[(idx+2)%6])
        for u in [-2,1.3]:
            g.box((side*21.4,y+u,h+.65),(1.2,1.8,1.0),silver)
            for k in range(5):g.box((side*20.78,y+u-.7+k*.32,h+.67),(.015,.07,.6),dark)
        rail((side*19,y-4.8),(side*19,y+4.8),h+.2)
        g.rod((side*27,y+3,h),(side*27,y+3,h+5),.035,dark)
        g.sphere((side*27,y+3,h+5),(.065,.065,.07),neonred,8,5)

# Glico runner: independently modeled sign, blue track rays and raised silhouette.
side=-1;y=7
panel(side,y,0,19.2,8.6,25.3,blue)
panel(side,y,0,29.2,8.55,5.2,white,'Glico',neonred,2.18)
g.text('おいしさと健康',pos(side,y,0,.85,31.0),.5,blue,math.pi/2,font=jp)
def mark(u,h,depth=.93):return pos(-1,y,u,depth,h)
for u in [-4,-3,-2,-1,0,1,2,3,4]:g.rod(mark(0,19,.84),mark(u,7.0,.84),.025,cyan,6)
for u in [-4.15,4.15]:g.rod(mark(u,6.8,.86),mark(u,31.6,.86),.045,white)
# Pose: arms lifted, one knee raised and one foot trailing.
segments=[((-1,20.8),(-2.1,23)),((-2.1,23),(-3.15,25.5)),((1,20.8),(2.05,23.1)),((2.05,23.1),(3.12,25.5)),((-.58,16.6),(-1.15,13.4)),((-1.15,13.4),(-.35,10.0)),((.58,16.6),(1.2,14.5)),((1.2,14.5),(.40,12.4))]
for a,b in segments:
    du=b[0]-a[0];dh=b[1]-a[1];length=math.hypot(du,dh)
    for radius,m,d in [(.38,black,.94),(.27,white,.96)]:
        offset=(-dh/length*radius,du/length*radius)
        v=[mark(p[0]+sgn*offset[0],p[1]+sgn*offset[1],d) for p,sgn in [(a,1),(a,-1),(b,-1),(b,1)]]
        g.mesh(v,[(0,1,2,3)],m)
g.sphere(mark(0,19.05,.94),(.02,1.08,2.4),black,20,12)
g.sphere(mark(0,19.05,.98),(.02,.92,2.25),white,20,12)
g.sphere(mark(0,22.3,.96),(.02,.69,.90),black,20,12)
g.sphere(mark(0,22.25,1.0),(.02,.49,.64),cream,16,10)
for i,c in enumerate('グリコ'):g.text(c,mark(0,20.2-i*.9,1.04),.84,neonred,math.pi/2,font=jp)
for u in [-.35,.55]:g.sphere(mark(u,10 if u<0 else 12.3,.96),(.02,.32,.66),black,12,8)
# The actual supplied campaign artwork sits on the modeled billboard cabinet.
# Keep the authored silhouette in the editable file behind the replaceable print.
g.panel(pos(-1,7,0,1.12,19.2),8.6,25.3,artwork('Glico',[(914,115),(1035,38),(1038,547),(914,558)]),math.pi/2)
# Neighboring multi-story advertising boards.
panel(-1,20,0,25,6.7,13,yellow,'SUPER DRY',neonred,1.06)
g.rod(pos(-1,20,0,.7,19),pos(-1,20,0,.7,26),1.65,silver,32)
g.text('Asahi',pos(-1,20,0,2.38,23),1.14,black,math.pi/2,font=font)
g.text('生',pos(-1,20,0,2.4,21),1.1,black,math.pi/2,font=jp)
panel(-1,-5,0,26,7.2,8,orange,'PROMISE',blue,1.08)
panel(-1,-5,0,18.5,7.2,5.4,blue,'CHINTAI',white,1.25)
g.panel(pos(-1,-5,0,.90,26),7.2,8,artwork('Promise',[(1172,141),(1298,88),(1298,259),(1172,284)],512,512),math.pi/2)
g.panel(pos(-1,-5,0,.90,18.5),7.2,5.4,artwork('Chintai',[(1173,316),(1294,278),(1294,406),(1173,434)],512,512),math.pi/2)
panel(-1,-15,0,27,7,9,white,'日商エステム',blue,.75)
panel(-1,-15,0,18.6,7,6,green,'大阪へようこそ',white,.61)

# Giant Kani Doraku crab. Broad domed shell, articulated legs and large pincers.
def crab(side,y,h):
    def p(u,v,z):return pos(side,y,u,v,h+z)
    g.box(p(0,.55,0),(.75,9,6),wood)
    g.sphere(p(0,1.25,0),(.72,1.42,1.08),red,24,14)
    for sgn in [-1,1]:
        for k in range(4):
            a=p(sgn*.8,1.15,.35-k*.35);b=p(sgn*(2.1+k*.18),1.4,.9-k*.72);c=p(sgn*(3.1+k*.18),1.22,.62-k*.84)
            g.rod(a,b,.13,red,10,r2=.17);g.rod(b,c,.17,red,10,r2=.07);g.sphere(b,(.18,.18,.18),red,12,8)
        g.rod(p(sgn*.75,1.35,.65),p(sgn*1.5,1.5,1.8),.19,red,12)
        g.sphere(p(sgn*1.75,1.53,2.14),(.35,.47,.56),red,16,10)
        for off in [-.27,.27]:g.rod(p(sgn*1.75+off,1.54,2.3),p(sgn*1.75+off*.65,1.58,2.83),.13,red,10,r2=.025)
        g.rod(p(sgn*.44,1.45,.67),p(sgn*.5,1.58,1.22),.065,red)
        g.sphere(p(sgn*.5,1.59,1.23),(.095,.105,.13),black,12,8)
    panel(side,y,0,h-3.75,8.8,1.35,white,'かに道楽',neonred,1)
crab(1,7,10)
vertical(1,7,4.3,22,'かに道楽',white,14,1.65)
# Traditional Kani Doraku surround: pale vertical slats, tiled eaves and lanterns.
for u in np.linspace(-4.5,4.5,30):g.box(pos(1,7,float(u),.65,10),(.2,.11,6.2),cream)
for row in range(4):
    for u in np.linspace(-5,5,34):
        g.rod(pos(1,7,float(u),.6+row*.23,13.45-row*.10),pos(1,7,float(u),.83+row*.23,13.35-row*.10),.10,dark,8)
for u in np.linspace(-4.6,4.6,17):g.sphere(pos(1,7,float(u),1.1,12.75),(.18,.20,.25),warm,10,7)

# Takoyaki octopus with curling, sucker-lined tentacles.
def octopus(side,y,h):
    def p(u,v,z):return pos(side,y,u,v,h+z)
    g.sphere(p(0,1.12,.6),(.67,1.0,1.12),red,24,14)
    for j in range(8):
        a=j*math.tau/8;points=[]
        for k in range(15):
            t=k/14;u=math.cos(a)*(1.0+t*1.6)+math.sin(t*math.tau)*.32
            z=-.1+math.sin(a)*(.7+t*.7)-t*.3+math.sin(t*5)*.32
            points.append(p(u,1.0+math.sin(t*4)*.4,z))
        for k,(a1,b1) in enumerate(zip(points,points[1:])):
            g.rod(a1,b1,.20-k*.009,red,8)
            if k%2==0:g.sphere((b1[0]-side*.13,b1[1],b1[2]),(.06,.075,.075),pink,8,5)
    for u in [-.35,.35]:
        g.sphere(p(u,1.72,.7),(.09,.19,.25),white,12,8)
        g.sphere(p(u,1.81,.69),(.035,.09,.13),black,10,6)
    g.sphere(p(0,1.88,.18),(.12,.17,.17),black,12,8)
octopus(-1,-5,7.9)

# Suspended fugu lantern with fins, facial details and painted Japanese lettering.
side=1;y=-16
g.sphere(pos(side,y,0,2.1,18.7),(1.55,2.05,1.65),cream,32,20)
g.sphere(pos(side,y,0,2.1,19.9),(1.3,1.8,.59),blue,28,14)
for u in [-1.65,1.65]:
    g.sphere(pos(side,y,u,2.3,18.6),(.15,.55,.44),yellow,12,8)
    g.sphere(pos(side,y,u*.57,3.3,19.45),(.06,.12,.14),black,10,6)
g.text('づぼらや',pos(side,y,0,3.65,18.55),.75,neonred,-math.pi/2,font=jp)
for u in [-1.25,-.65,0,.65,1.25]:g.sphere(pos(side,y,u,3.27,19.7),(.055,.085,.085),black,8,5)
g.rod(pos(side,y,0,.1,24),pos(side,y,0,2.1,24),.05,dark)
g.rod(pos(side,y,0,2.1,20.5),pos(side,y,0,2.1,24),.035,dark)

# Tall narrow Don Quijote oval ferris wheel, visible over the eastern roofs.
for ring in [0,.52]:
    points=[(19.1+ring,38+4.0*math.cos(i*math.tau/96),23+15*math.sin(i*math.tau/96)) for i in range(97)]
    for a,b in zip(points,points[1:]):g.rod(a,b,.095,yellow,8)
for i in range(14):
    a=i*math.tau/14;u=38+4*math.cos(a);z=23+15*math.sin(a)
    g.box((18.95,u,z),(.8,1.3,1.5),red)
    g.box((18.5,u,z+.1),(.08,1.05,.7),glass)
panel(1,38,0,22,3.9,10,neonred,'ドンキ',yellow,1.1)

# Two open river cruisers; each is authored as an independent movable root.
# Continue the visual corridor beyond the playable bounds and close the horizon
# with a compact skyline so orbit views never reveal a world ending in empty sky.
for sign in [-1,1]:
    g.box((0,sign*92,-1.45),(17,44,.1),water,name='Dotonbori canal water')
    for side in [-1,1]:
        g.box((side*13.5,sign*92,-.3),(11,44,.6),paving)
        for i in range(4):
            yy=sign*(76+i*11);h=random.uniform(21,39)
            g.box((side*24,yy,h/2),(11,10.5,h),facades[i%6])
            for z in range(4,int(h),3):
                for u in [-3,0,3]:g.panel((side*18.45,yy+u,z),1.9,1.4,windows[(z+int(u))%4],-side*math.pi/2)
            panel(side,yy,0,11,3,11,signs[i%8],labels[i],white,1.2)
    for x in [-43,-33,-22,-9,6,21,38]:
        h=random.uniform(19,41);depth=random.uniform(133,160)
        g.box((x,sign*depth,h/2),(random.uniform(7,11),12,h),facades[abs(x)%6])
        for z in range(4,int(h),3):
            for u in [-2,0,2]:g.panel((x+u,sign*(depth-6.1),z),.75,1.25,windows[(z+int(u))%4],0 if sign==1 else math.pi)
objects=g.flush()
def person(x,y,z,coat,scale=1,angle=0):
    def p(a,b,h):return (x+scale*(a*math.cos(angle)-b*math.sin(angle)),y+scale*(a*math.sin(angle)+b*math.cos(angle)),z+scale*h)
    g.sphere(p(0,0,1.48),(.17*scale,.16*scale,.21*scale),skin,12,8)
    g.sphere(p(0,.025,1.59),(.178*scale,.16*scale,.145*scale),hair,12,8)
    g.sphere(p(0,0,1.04),(.24*scale,.15*scale,.33*scale),coat,12,8)
    for a in [-.12,.12]:
        g.rod(p(a,0,.8),p(a,.02,.15),.083*scale,black,10)
        g.sphere(p(a,-.07,.09),(.105*scale,.18*scale,.08*scale),cream,10,6)
    for a in [-.25,.25]:g.rod(p(a,0,1.26),p(a*1.2,-.04,.78),.068*scale,coat,10)
for i,(x,y) in enumerate([(-3,-24),(3,30)]):
    # Hull shape is narrower at the bow, with a full open passenger well.
    z=-1.04;v=[(x+a,y+b,z+c) for a,b,c in [(-1.65,-4.5,0),(1.65,-4.5,0),(1.8,3.5,0),(.9,4.8,0),(-.9,4.8,0),(-1.8,3.5,0),(-1.8,-4.5,.7),(1.8,-4.5,.7),(1.85,3.5,.7),(.95,4.8,.7),(-.95,4.8,.7),(-1.85,3.5,.7)]]
    g.mesh(v,[(0,5,4,3,2,1)]+[(k,(k+1)%6,(k+1)%6+6,k+6) for k in range(6)],boatmat,'Cruise hull')
    g.box((x,y,z+.24),(3.35,8.5,.16),wood)
    for yy in [-3,-1.8,-.6,.6,1.8]:
        g.box((x,y+yy,z+.64),(2.9,.43,.12),dark)
        g.box((x,y+yy+.2,z+.85),(2.9,.1,.44),dark)
        for xx in [-.88,.15,.95]:
            if random.random()<.70:person(x+xx,y+yy,z+.24,coats[random.randrange(6)],.64,math.pi)
    for xx in [-1.8,1.8]:rail((x+xx,y-4.4),(x+xx,y+3.5),z+.34)
    g.box((x,y-4.54,z+.8),(3.6,.08,.62),boatmat)
    g.text('とんぼりクルーズ',(x,y-4.59,z+.79),.30,black,0,font=jp)
    for xx in [-1.6,1.6]:g.box((x+xx,y,z+1.43),(.055,7.8,.055),warm)
    parts=g.flush();root=bpy.data.objects.new('River cruise '+str(i),None);bpy.context.collection.objects.link(root)
    root['cruise']=True;root['cruiseIndex']=i
    # Keep world-authored coordinates in the mesh; a root offset animates the cruise.
    for o in parts:o.parent=root
    objects+=parts+[root]

# Sparse on-foot visitors, placed off the main route and across the bridge.
for side in [-1,1]:
    for i,y in enumerate([-58,-40,-29,-15,12,24,39,57]):
        person(side*(11.3+(i%3)*1.3),y,0,coats[(i+(side+1))%6],random.uniform(.88,1.05),random.uniform(-math.pi,math.pi))
for x in [-6,-3,3,6]:person(x,2.75,2.55+.24*(1-(x/8.5)**2),coats[int(abs(x))%6],.97,math.pi/2)
objects+=g.flush()

# Practical light spill is baked separately from the sun.
for side in [-1,1]:
    for i,y in enumerate(range(-60,61,10)):
        bpy.ops.object.light_add(type='AREA',location=(side*17.6,y,3.1));o=bpy.context.object
        o.name='Dotonbori shop spill';o.data.energy=150;o.data.color=(1,.38,.10);o.data.shape='DISK';o.data.size=4
        o.rotation_euler=(Vector((side*12,y,0))-o.location).to_track_quat('-Z','Y').to_euler();o['baked_shop']=True;o['base_power']=150
for y,color in [(7,(.025,.15,1)),(-5,(1,.045,.02)),(20,(1,.49,.025))]:
    bpy.ops.object.light_add(type='AREA',location=(-17,y,13));o=bpy.context.object;o.data.energy=480;o.data.color=color;o.data.size=6
    o.rotation_euler=(Vector((0,y,-1))-o.location).to_track_quat('-Z','Y').to_euler();o['baked_shop']=True;o['base_power']=480
bpy.ops.object.light_add(type='SUN');bpy.context.object.name='Dotonbori sun'
bpy.context.scene.world=bpy.data.worlds.new('Dotonbori sky')
bpy.context.scene['location_id']='dotonbori'
apply_preset('evening')
bpy.ops.object.camera_add(location=(3,-42,7.6));cam=bpy.context.object;cam.name='Dotonbori review camera'
cam.rotation_euler=(Vector((-1,5,10))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.lens=26
s=bpy.context.scene;s.camera=cam;s.render.resolution_x=1500;s.render.resolution_y=1000;s.render.resolution_percentage=100
s['design_reference']='Four user supplied Dotonbori directional concept boards; compact stylized reconstruction'
s['bridge_navigation']='Four longitudinal stair flights per bridge; 0.1275m main risers, 5m landings, parabolic crown 2.79m'
s['pedestrian_count']=20
data=dict(id='dotonbori',name='Osaka Dotonbori',spawn=[10.8,0,18],bounds=[-18.8,18.8,-68,68],colliders=colliders,surfaces=surfaces,pedestrians=20,cruises=2,artRevision=2)
(ROOT/'public/models/dotonbori.json').write_text(json.dumps(data,indent=2))
if '--navigation-only' in sys.argv:
    print('DOTONBORI_NAVIGATION_UPDATED',len(colliders),flush=True)
    sys.exit(0)
g.export(ROOT/'public/models/dotonbori.glb',objects)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/dotonbori.blend'),compress=True)
print('DOTONBORI_AUTHORED',len(objects),len(colliders),flush=True)
