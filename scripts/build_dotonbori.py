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
boatmat=mat('cruise navy',(.035,.065,.12),.36,.25)
cruiseglass=g.material('Cruise Glazing',(.13,.24,.33),.18,.15,0,.34)
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
        # The reflection camera sees the real underside. A top-only bridge lets
        # billboards show through its back faces in the water.
        g.mesh([(a,y+half,ha-.94),(b,y+half,hb-.94),(b,y-half,hb-.94),(a,y-half,ha-.94)],[(0,1,2,3)],stone,'Bridge solid soffits')
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
    for x in [-5.9,5.9]:
        soffit=elevation(x)-.94
        g.box((x,y,(-1.8+soffit)/2),(.75,half*2-.3,soffit+1.8),stone,name='Bridge support piers')
        g.box((x,y,soffit-.12),(1.25,half*2,.28),cap,name='Bridge pier capitals')
    for end in [-1,1]:
        for x in [-8,-4,0,4,8]:
            z=elevation(x)
            g.box((x,y+end*half,z+.53),(.34,.30,1.10),stone)
            g.box((x,y+end*half,z+1.13),(.47,.43,.14),cap)
    for sgn in [-1,1]:
        yy=y+sgn*half
        collider(0,yy,8.5,.055,top+crown+1.2,cameraMinY=top-.95)
        g.text('え び す 橋' if main else '道 頓 堀',(0,yy+sgn*.022,top+crown-.5),.64 if main else .45,black,0 if sgn==-1 else math.pi,font=jp)
    # Both banks have a broad upper landing and two real flights along the canal.
    count=20 if main else 15;run=6.8 if main else 5.4;rise=top/count;tread=run/count
    for side in [-1,1]:
        x=side*11.0;lo=8.5;hi=13.5
        g.mesh([(side*lo,y-half,top),(side*hi,y-half,top),(side*hi,y+half,top),(side*lo,y+half,top)],[(0,1,2,3),(3,2,1,0)],cap,name)
        g.box((x,y,top-.26),(4.95,half*2,.50),stone,name='Bridge landing soffits')
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

def artwork(name,corners,width=512,height=1024,source_name='dotonbori-south.png'):
    # Rectify the supplied sign artwork inside Blender. Only individual signs
    # become textures; the streets, landmarks and all depth remain modeled.
    source=bpy.data.images.load(str(ROOT/'assets/references'/source_name),check_existing=True)
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
from dotonbori_architecture import build as build_architecture
architecture=build_architecture(globals())

# Advertising composition follows the selected north/south concept.
def campaign(side,y,u,h,w,height,name,corners,source='dotonbori-north-v2.png'):
    panel(side,y,u,h,w,height,white)
    g.panel(pos(side,y,u,.91,h),w,height,artwork(name,corners,512,1024,source),-side*math.pi/2)
    for edge in [-1,1]:
        g.box(pos(side,y,u+edge*(w/2+.09),.81,h),(.35,.12,height+.22),silver)
    for z in [h-height/2-.09,h+height/2+.09]:g.box(pos(side,y,u,.81,z),(.35,w+.3,.12),silver)

campaign(-1,11.5,2.0,19.0,10.2,25.0,'Glico north',[(791,174),(919,174),(919,438),(791,438)])
campaign(-1,11.5,-6.5,19.0,5.8,25.0,'Snowflake city',[(697,174),(786,174),(786,438),(697,438)])
campaign(-1,28.5,-2.7,26.0,4.55,8.7,'Estem north',[(927,211),(1008,211),(1008,287),(927,287)])
campaign(-1,28.5,2.7,26.0,4.55,8.7,'Promise north',[(1014,209),(1084,209),(1084,293),(1014,293)])
campaign(-1,28.5,0,18.8,9.9,4.8,'Gam City',[(1022,294),(1126,294),(1126,339),(1022,339)])
campaign(-1,28.5,0,12.7,9.9,6.6,'Chintai north',[(928,357),(1036,357),(1036,415),(928,415)])
# Retain the Asahi campaign on the opposite restaurant bank.
campaign(1,7,0,23.5,7.0,13.3,'Asahi',[(745,156),(830,178),(830,352),(745,348)],'dotonbori-south.png')

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
crab(-1,-20,15.6)
vertical(-1,-20,8.35,15.3,'本場の味',white,17,1.65)
# Traditional Kani Doraku surround: pale vertical slats, tiled eaves and lanterns.
for u in np.linspace(-7.5,7.5,50):g.box(pos(-1,-20,float(u),.65,15.6),(.2,.11,9.2),cream)
for row in range(4):
    for u in np.linspace(-7.8,7.8,50):
        g.rod(pos(-1,-20,float(u),.6+row*.23,20.45-row*.10),pos(-1,-20,float(u),.83+row*.23,20.35-row*.10),.10,dark,8)
for u in np.linspace(-7.3,7.3,26):g.sphere(pos(-1,-20,float(u),1.1,20.0),(.18,.20,.25),warm,10,7)

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
octopus(1,21,7.9)

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

# Don Quijote is on the north bank east of Ebisubashi, across from Glico.
# This compact map uses +X for north and -Blender-Y (+game-Z) for east.
# Official access map: https://www.donki.com/kanransha/index_en.php
side=1;y=-40
for depth in [.85,1.5]:
    for radius in [4.75,5.30]:
        points=[pos(side,y,radius*math.cos(i*math.tau/96),depth,23+15.1*math.sin(i*math.tau/96)) for i in range(97)]
        for aa,bb in zip(points,points[1:]):g.rod(aa,bb,.08,yellow,8)
for i in range(32):
    a=i*math.tau/32;b=(i+1)*math.tau/32
    g.rod(pos(side,y,5.3*math.cos(a),.85,23+15.1*math.sin(a)),pos(side,y,4.75*math.cos(b),1.5,23+15.1*math.sin(b)),.055,yellow,6)
    g.rod(pos(side,y,5.3*math.cos(a),.85,23+15.1*math.sin(a)),pos(side,y,5.3*math.cos(a),1.5,23+15.1*math.sin(a)),.07,yellow,6)
for u in [-2.6,2.6]:g.rod(pos(side,y,u,1.05,8),pos(side,y,u,1.05,37),.10,yellow,8)
for z in range(9,36,3):
    g.rod(pos(side,y,-2.6,1.05,z),pos(side,y,2.6,1.05,z+3),.055,yellow,6)
    g.rod(pos(side,y,2.6,1.05,z),pos(side,y,-2.6,1.05,z+3),.055,yellow,6)
for i in range(16):
    a=i*math.tau/16;u=5.3*math.cos(a);z=23+15.1*math.sin(a)
    g.sphere(pos(side,y,u,1.65,z),(.45,.72,.92),red,16,10)
    g.panel(pos(side,y,u,2.13,z+.05),1.0,1.1,glass,-side*math.pi/2)
    for off in [-.55,.55]:g.rod(pos(side,y,u+off,2.15,z-.62),pos(side,y,u+off,2.15,z+.63),.025,yellow,6)
    g.sphere(pos(side,y,u,2.17,z+.74),(.045,.045,.045),warm,8,5)
# The mascot print sits on an independently modeled central sign cabinet.
campaign(side,y,0,23,4.2,6.8,'Don Quijote mascot',[(1311,205),(1364,205),(1364,290),(1311,290)])
panel(side,y,0,6.5,13.7,2.4,black,'ドン・キホーテ',yellow,1.6)

# Two covered river cruisers; each is authored as an independent movable root.
# Continue the visual corridor beyond the playable bounds and close the horizon
# with a compact skyline so orbit views never reveal a world ending in empty sky.
for sign in [-1,1]:
    g.box((0,sign*122,-1.45),(17,104,.1),water,name='Dotonbori canal water')
    for side in [-1,1]:
        g.box((side*22,sign*122,-.3),(28,104,.6),paving,name='Dotonbori distant paving')
        g.box((side*8.3,sign*122,-1.1),(.62,104,2.2),stone)
        for i in range(8):
            yy=sign*(76+i*11);h=[23,29,25,32,22,27,24,30][(i+(side+1))%8]
            g.box((side*24,yy,h/2),(10,10.5,h),facades[(i+2)%6])
            for z in range(4,int(h),3):
                g.box((side*18.9,yy,z-1.25),(.32,10.5,.26),stone)
                for u in [-3.6,-1.2,1.2,3.6]:
                    g.panel((side*18.82,yy+u,z),1.8,1.9,windows[(z+round(u)+i)%4],-side*math.pi/2)
                    g.box((side*18.76,yy+u,z),(.12,.08,1.9),dark)
            vertical(side,yy,side*3.8,h*.52,labels[i%12],signs[i%8],h*.7,1.65)
            panel(side,yy,-side,4.2,6.1,1.2,white,labels[(i+2)%12],neonred,.8)
            panel(side,yy,-side,10.1,4.6,2.1,signs[(i+3)%8],labels[(i+6)%12],None,.9)
            g.box((side*25,yy+1,h+1.35),(4.6,4.1,2.7),facades[(i+4)%6])
            rail((side*19.2,yy-5),(side*19.2,yy+5),h+.1)
            g.box((side*21.2,yy-2,h+.55),(1.5,2.2,1.1),silver)
            for u in [-4,-2,0,2,4]:g.sphere((side*17.9,yy+u,3.1),(.15,.19,.26),warm,8,5)
            g.box((side*8.0,yy,-.6),(.08,.4,.6),warm)
        # Small bridges continue the perspective beyond the playable district.
        rail((side*8.4,sign*71),(side*8.4,sign*168),0)
    for yy in [sign*88,sign*122]:
        g.box((0,yy,1.75),(18,3.2,.65),stone)
        for end in [-1,1]:rail((-9,yy+end*1.55),(9,yy+end*1.55),2.08)
    for x in [-43,-33,-22,-9,6,21,38]:
        h=random.uniform(19,41);depth=random.uniform(174,184)
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
    g.box((x,y-4.54,z+.8),(3.6,.08,.62),cream)
    g.text('とんぼりクルーズ',(x,y-4.59,z+.79),.30,black,0,font=jp)
    for xx in [-1.6,1.6]:g.box((x+xx,y,z+1.43),(.055,7.8,.055),warm)
    # Enclosed river cruisers from the revised concept: glazed cabin, pale roof
    # ribs, a dark hull and a continuous warm cabin light.
    for xx in [-1.75,1.75]:
        g.box((x+xx,y,z+1.58),(.03,8.1,1.25),cruiseglass,name='Cruise Glazing')
        for yy in [-4,-2.7,-1.35,0,1.35,2.7,4]:g.rod((x+xx,y+yy,z+.95),(x+xx,y+yy,z+2.22),.043,cream,8)
        for zz in [z+.91,z+2.23]:g.box((x+xx,y,zz),(.10,8.3,.11),cream)
    for yy in [-4.05,4.05]:g.box((x,y+yy,z+1.58),(3.5,.035,1.25),cruiseglass,name='Cruise Glazing')
    g.box((x,y,z+2.25),(3.64,8.35,.10),silver)
    for yy in [-3.3,-1.65,0,1.65,3.3]:
        g.box((x,y+yy,z+2.32),(2.9,1.35,.035),cruiseglass,name='Cruise Glazing')
        g.box((x,y+yy-.73,z+2.32),(3.66,.075,.075),cream)
    for xx in [-1.82,1.82]:g.box((x+xx,y,z+.76),(.07,8.45,.17),neonred)
    parts=g.flush();root=bpy.data.objects.new('River cruise '+str(i),None);bpy.context.collection.objects.link(root)
    root['cruise']=True;root['cruiseIndex']=i
    # Keep world-authored coordinates in the mesh; a root offset animates the cruise.
    for o in parts:o.parent=root
    objects+=parts+[root]

# On-foot visitors use the same animated pedestrian asset as Shibuya at runtime.
# Boat passengers remain part of their moving vessel; no static walkers are baked.

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
s['pedestrian_count']=36
data=dict(id='dotonbori',name='Osaka Dotonbori',spawn=[10.8,0,18],bounds=[-18.8,18.8,-68,68],colliders=colliders,surfaces=surfaces,pedestrians=36,cruises=2,artRevision=4,architecture=architecture)
(ROOT/'public/models/dotonbori.json').write_text(json.dumps(data,indent=2))
if '--navigation-only' in sys.argv:
    print('DOTONBORI_NAVIGATION_UPDATED',len(colliders),flush=True)
    sys.exit(0)
g.export_atomic(ROOT/'public/models/dotonbori.glb',objects)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/dotonbori.blend'),compress=True)
print('DOTONBORI_AUTHORED',len(objects),len(colliders),flush=True)
