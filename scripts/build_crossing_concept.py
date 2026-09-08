"""Blender scene reconstruction guided by the supplied Shibuya concept.
Fast material batches, modeled interiors, foliage, street props and staged traffic.
"""
import bpy,math,random,json,sys
import numpy as np
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import scene_geometry as g
from blender_lighting import apply_preset
random.seed(10903)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
for data in list(bpy.data.materials):bpy.data.materials.remove(data)
g.M.clear();g.B.clear();g.TEXT.clear()

metal=g.material('Charcoal architectural metal',(.035,.042,.055),.34,.65)
trim=g.material('Champagne aluminum',(.24,.22,.20),.35,.62)
stone=g.material('Warm concrete',(.27,.25,.24),.89)
concrete=g.material('Slate concrete',(.12,.135,.17),.9)
cladding=[g.material('Facade cladding '+str(i),c,.72,.12) for i,c in enumerate([(.30,.32,.37),(.21,.24,.31),(.40,.38,.36),(.15,.17,.23)])]
sidewalk=g.material('Pavement stone',(.23,.235,.25),.83)
asphalt=g.material('Rain-dark asphalt',(.031,.036,.048),.48,.06)
paint=g.material('Crosswalk ivory paint',(.64,.65,.65),.6)
paint['surface_role']='road-marking'
# Separate batches share world-aligned surface textures and the district atlas.
district_asphalt=g.material('District asphalt',(.031,.036,.048),.48,.06)
district_paving=g.material('District paving',(.23,.235,.25),.83)
district_paint=g.material('District road paint',(.64,.65,.65),.6)
district_paint['surface_role']='road-marking'
district_yellow=g.material('District ochre markings',(.69,.40,.06),.82)
deck_paving=g.material('Deck paving',(.23,.235,.25),.83)
deck_yellow=g.material('Deck stair nosings',(.69,.40,.06),.82)
porcelain=g.material('Landmark white ceramic',(.57,.59,.61),.73,.12)
silver=g.material('Landmark silver aluminum',(.46,.49,.52),.38,.58)
bookblue=g.material('Taiseido cobalt enamel',(.012,.10,.43),.53,.04)
bookred=g.material('Taiseido red sign border',(.56,.012,.022),.56)
magred=g.material('MAGNET red enamel',(.48,.018,.043),.46,.08)
magcyan=g.material('MAGNET cyan enamel',(.008,.38,.48),.46,.08)
hotelglass=g.material('Mark City blue gray glass',(.115,.19,.23),.24,.52)
yellow=g.material('Tactile ochre',(.69,.40,.06),.82)
wood=g.material('Walnut shop joinery',(.15,.073,.035),.7)
black=g.material('Soft black rubber',(.012,.015,.023),.83)
cream=g.material('Store plaster',(.46,.38,.28),.85)
glass=g.material('Glazing architectural',(.19,.25,.31),.16,.45,alpha=.19)
blueglass=g.material('Dark reflective glass',(.024,.055,.09),.19,.6)
upperglass=g.material('Glazing smoked curtain wall',(.033,.060,.095),.13,.62,alpha=.74)
brick=g.material('Terracotta tile cladding',(.21,.105,.085),.84)
granite=g.material('Pale granite curb',(.34,.33,.32),.83)
drain=g.material('Drain iron',(.034,.038,.041),.63,.6)
roofing=g.material('Zinc roof panels',(.10,.125,.15),.54,.5)
patch=g.material('Asphalt repairs',(.020,.025,.032),.68)
warm=[g.material('Interior amber '+str(i),c,.7,0,e) for i,(c,e) in enumerate([((.57,.28,.10),.54),((.44,.23,.12),.36),((.73,.46,.20),.78),((.075,.087,.11),0)])]
white=g.material('Ivory neon lettering',(.86,.86,.75),.5,0,1.7)
lamp=g.material('Warm lamps', (1,.52,.18),.35,0,3.2)
pink=g.material('Sakura neon',(.85,.09,.34),.4,0,2.0)
blue=g.material('Electric blue signage',(.025,.23,.62),.45,0,1.1)
green=g.material('Station emerald',(.014,.24,.10),.65,0,.35)
red=g.material('Karaoke vermilion',(.48,.014,.029),.6,0,.18)
brandred=g.material('Scarlet brand lettering',(.68,.014,.030),.5,0,.9)
bark=g.material('Textured tree bark',(.105,.057,.031),.96)
leaves=[g.material('Ginkgo leaves '+str(i),c,.78) for i,c in enumerate([(.034,.11,.028),(.065,.18,.033),(.14,.24,.055),(.038,.145,.082),(.21,.27,.078)])]
books=[g.material('Book spines '+str(i),c,.85) for i,c in enumerate([(.38,.055,.05),(.025,.18,.22),(.65,.49,.21),(.39,.31,.27)])]
font=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf')
jp=bpy.data.fonts.load('C:/Windows/Fonts/YuGothB.ttc')
colliders=[];shop_positions=[]

def obstacle(x,y,w,d,h):colliders.append({'x':x,'z':-y,'halfX':w/2,'halfZ':d/2,'height':h})
def box(pos,size,mat,rot=0):g.box(pos,size,mat,rot)
def sign(body,x,y,z,w,h,mat,size=None,angle=0,japanese=False):
    box((x,y,z),(w+.16,.22,h+.16),metal,angle)
    g.panel((x+math.sin(angle)*.13,y-math.cos(angle)*.13,z),w,h,mat,angle)
    g.text(body,(x+math.sin(angle)*.15,y-math.cos(angle)*.15,z),size or min(h*.53,w/max(map(len,body.split('\n')))*1.32),white,angle,jp if japanese else font)

def artwork(name,corners,w=768,h=768):
    source=bpy.data.images.load('C:/Users/USER/Downloads/ChatGPT Image Sep 6, 2026, 10_08_45 PM.png',check_existing=True)
    sw,sh=source.size;pixels=np.asarray(source.pixels[:],dtype=np.float32).reshape(sh,sw,4)
    u,v=np.meshgrid(np.linspace(0,1,w),np.linspace(1,0,h))
    a,b,c,d=[np.asarray(p)*np.array([sw/1402,sh/1122]) for p in corners]
    coords=(1-v[...,None])*((1-u[...,None])*a+u[...,None]*b)+v[...,None]*((1-u[...,None])*d+u[...,None]*c)
    xx=np.clip(coords[...,0].astype(int),0,sw-1);yy=np.clip((sh-1-coords[...,1]).astype(int),0,sh-1)
    im=bpy.data.images.new(name,w,h);im.pixels.foreach_set(pixels[yy,xx].reshape(-1));im.pack()
    m=g.material(name,(1,1,1),.56,0,.72);node=m.node_tree.nodes.new('ShaderNodeTexImage');node.image=im
    p=m.node_tree.nodes.get('Principled BSDF');m.node_tree.links.new(node.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(node.outputs['Color'],p.inputs['Emission Color'])
    return m

def screen(x,y,z,w,h,mat):
    box((x,y,z),(w+.32,.35,h+.32),metal);g.panel((x,y-.185,z),w,h,mat)
    for sx in [-1,1]:box((x+sx*(w/2+.16),y-.2,z),(.045,.07,h+.1),trim)

def curved_screen(x,y,z,w,h,mat,bow=1.1):
    """Continuous artwork UVs over a genuinely curved, framed LED surface."""
    for i in range(24):
        u0=i/24;u1=(i+1)/24
        a=(x+(u0-.5)*w,y+bow*(2*u0-1)**2)
        b=(x+(u1-.5)*w,y+bow*(2*u1-1)**2)
        g.mesh([(a[0],a[1],z-h/2),(b[0],b[1],z-h/2),(b[0],b[1],z+h/2),(a[0],a[1],z+h/2)],[(0,1,2,3)],mat,uvs=[(u0,0),(u1,0),(u1,1),(u0,1)])
        for zz in [z-h/2-.12,z+h/2+.12]:g.rod((*a,zz),(*b,zz),.12,metal,6)
    for xx in [x-w/2,x+w/2]:g.rod((xx,y+bow,z-h/2),(xx,y+bow,z+h/2),.12,metal,6)

def prism(points,z,height,mat):
    n=len(points)
    g.mesh([(x,y,z+dz) for dz in [0,height] for x,y in points],
           [tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)],mat)

def roof_detail(x,y,w,d,h,variant=0):
    """Different roof silhouettes, occupied plant rooms and connected services."""
    box((x,y,h+.14),(w,d,.25),roofing)
    for dx in [-w/2+.16,w/2-.16]:
        for dz in [.35,1.02]:g.rod((x+dx,y-d/2,h+dz),(x+dx,y+d/2,h+dz),.029,metal)
        for k in range(int(d)+1):g.rod((x+dx,y-d/2+k,h+.25),(x+dx,y-d/2+k,h+1.02),.022,metal,6)
    if variant%3!=1:
        box((x+w*.16,y+d*.19,h+1.25),(w*.42,d*.32,2.2),cladding[variant%4])
        box((x+w*.16,y+d*.19,h+2.42),(w*.45,d*.35,.18),metal)
        g.panel((x+w*.16,y+d*.03-.02,h+1.16),.8,1.85,metal)
    count=2+variant%4
    for i in range(count):
        xx=x-w*.37+i*w*.64/max(1,count-1);yy=y-d*.24
        box((xx,yy,h+.57),(1.38,1.5,.9),stone)
        for j in range(5):box((xx,yy-.76,h+.25+j*.15),(1.14,.025,.048),metal)
        g.rod((xx,yy,h+1.04),(xx,yy,h+1.11),.43,metal,16)
        g.rod((xx,yy+.75,h+.42),(xx,yy+2.1,h+.42),.16,trim,10)
    for yy in [y-d*.37,y+d*.35]:g.rod((x-w*.39,yy,h+.24),(x+w*.39,yy,h+.24),.045,metal,6)
    g.rod((x-w*.3,y+d*.22,h),(x-w*.3,y+d*.22,h+3.6),.035,metal,8)
    for dz in [2.5,2.95,3.4]:g.rod((x-w*.3-.6,y+d*.22,h+dz),(x-w*.3+.6,y+d*.22,h+dz),.02,metal,6)

def footprint(x,y,w,d,r,z,height,mat):
    points=[(x-w/2,y-d/2),(x+w/2-r,y-d/2)]
    for i in range(1,9):
        a=-math.pi/2+i*math.pi/16;points.append((x+w/2-r+r*math.cos(a),y-d/2+r+r*math.sin(a)))
    points.extend([(x+w/2,y+d/2),(x-w/2,y+d/2)])
    n=len(points);verts=[(a,b,z+c) for c in [0,height] for a,b in points]
    faces=[tuple(reversed(range(n))),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    g.mesh(verts,faces,mat)

def shop_furniture(x,y,z,w,index):
    box((x,y+.8,z+.48),(w*.75,.46,.12),wood)
    for dx in [-w*.24,w*.24]:
        for dy in [-.13,.13]:g.rod((x+dx,y+.8+dy,z),(x+dx,y+.8+dy,z+.46),.026,metal)
        g.rod((x+dx,y+.28,z+.26),(x+dx,y+.28,z+.43),.16,wood,10)
        for sx in [-.10,.10]:g.rod((x+dx+sx,y+.28,z),(x+dx+sx,y+.28,z+.29),.019,metal,6)
    if index%3==0:
        box((x,y+1.02,z+1.15),(w*.65,.25,1.15),wood)
        for level in [.71,1.05,1.4]:
            box((x,y+.87,z+level),(w*.62,.34,.055),trim)
            for j in range(6):box((x-w*.24+j*w*.088,y+.91,z+level+.14),(.07,.14,.23),books[(index+j)%4])
    else:
        for dx in [-.22,.22]:g.rod((x+dx,y+.72,z+.55),(x+dx,y+.72,z+.69),.047,cream,8)

def building(x,y,w,d,h,shop=None,rounded=False,style=0):
    front=y-d/2;levels=round(h/(3.1 if style==2 else 2.8));step=h/levels;r=3.8 if rounded else .12
    obstacle(x,y,w,d,h)
    box((x,y+.5,h/2),(w-2.8,d-2.4,h),concrete)
    for floor in range(levels+1):footprint(x,y,w+.10,d+.10,r,floor*step,.10 if style==2 else .18,trim if rounded or style==2 else stone)
    # Facades have real shallow rooms and mullions, not flat glowing rectangles.
    columns=max(3,int((w-(r if rounded else 0))/(1.45 if style==2 else 2.1)));spacing=(w-(r if rounded else 0))/columns
    for floor in range(levels):
        z=floor*step+.16
        for col in range(columns):
            xx=x-w/2+(col+.5)*spacing
            light=warm[(col+floor)%3 if floor<2 else (1 if (floor*7+col*3)%7==0 else 3)]
            opaque=floor>=2 and not rounded and style!=2 and (col+int(abs(x)))%3!=0
            box((xx,front+1.28,z+step*.46),(spacing-.05,.07,step-.15),light)
            box((xx,front+.66,z+.035),(spacing-.06,1.34,.065),wood if floor<2 else stone)
            box((xx,front-.04,z+step/2),(.055,.12,step),trim)
            g.panel((xx,front-.10,z+step/2),spacing-.07,step-.15,(brick if style==1 else cladding[(style+floor//3)%4]) if opaque else (upperglass if floor>=2 else glass))
            if opaque:
                box((xx,front-.17,z+step*.16),(spacing-.15,.14,.075),trim)
                if style==1:
                    for row in range(1,7):box((xx,front-.105,z+row*step/7),(spacing-.1,.015,.012),stone)
            if floor<2:shop_furniture(xx,front,z,spacing,col)
            elif (floor+col)%3==0:
                box((xx,front+.58,z+.71),(spacing*.72,.55,.09),wood)
                box((xx,front+.83,z+1.02),(.40,.06,.29),metal)
            if floor<3:box((xx,front+.48,z+step-.21),(.48,.44,.045),lamp)
        # Side facade visible from the crossing's wide camera.
        for side in [-1,1]:
            for col in range(int(d/1.9)):
                yy=front+(col+.5)*d/int(d/1.9)
                if rounded and side==1 and yy<front+r:continue
                xx=x+side*w/2
                box((xx-side*.9,yy,z+step/2),(.06,1.72,step-.19),warm[(col+floor*3)%4])
                opaque=floor>=2 and not rounded and style!=2 and (col+floor//3)%3!=0
                g.panel((xx+side*.05,yy,z+step/2),1.74,step-.18,(brick if style==1 else cladding[(style+floor//3)%4]) if opaque else (upperglass if floor>=2 else glass),side*math.pi/2)
                box((xx,yy-.91,z+step/2),(.12,.055,step),trim)
        if rounded:
            for i in range(8):
                a=-math.pi/2+(i+.5)*math.pi/16;cx=x+w/2-r;cy=front+r
                px=cx+r*math.cos(a);py=cy+r*math.sin(a)
                g.panel((px,py,z+step/2),r*math.pi/16,step-.16,glass,a+math.pi/2)
                box((cx+(r-.48)*math.cos(a),cy+(r-.48)*math.sin(a),z+step/2),(.6,.6,step-.17),warm[(floor+i)%3])
                g.rod((px,py,z),(px,py,z+step),.029,trim,6)
    for dx in [-w/2,w/2]:box((x+dx,front-.13,h/2),(.14,.18,h),metal)
    roof_detail(x,y,w,d,h,int(abs(x))+style)
    if shop:
        if rounded or shop=='STARBUCKS':sign(shop,x,front-.29,6.05,w-.25,1.35,metal,1.12 if rounded else .98)
        else:sign(shop,x,front-.29,3.13,w-.25,.80,metal,.60)
        box((x,front-.60,3.72),(w+.25,1.30,.13),metal)
        shop_positions.append((x,front-1.05,2.6,w))

def tsutaya():
    x,y,w,d,h=27,23.5,20,22,33
    front=y-d/2;bow=2.25;columns=14;step=3.0
    # The front bows toward the crossing; columns follow the actual curved edge.
    edge=[(x-w/2+w*i/columns,front+bow*(2*i/columns-1)**2) for i in range(columns+1)]
    outline=edge+[(x+w/2,y+d/2),(x-w/2,y+d/2)]
    obstacle(x,y,w,d,h)
    box((x,y+3,h/2),(w-3,d-8,h),concrete)
    for floor in range(12):prism(outline,floor*step,.13,trim if floor<3 else metal)
    for floor in range(11):
        z=floor*step+.14
        for i,(a,b) in enumerate(zip(edge,edge[1:])):
            xx=(a[0]+b[0])/2;yy=(a[1]+b[1])/2
            span=math.dist(a,b);angle=math.atan2(b[1]-a[1],b[0]-a[0])
            g.panel((xx,yy-.025,z+1.4),span-.045,2.76,glass if floor<4 else upperglass,angle)
            g.rod((*a,z),(*a,z+2.88),.037,trim,6)
            box((xx,yy+1.28,z+1.35),(1.34,.1,2.7),warm[(i+floor)%3] if floor<4 else warm[1 if (i+floor*2)%9==0 else 3])
            if floor<4:
                shop_furniture(xx,yy+.06,z,1.4,i+floor)
                box((xx,yy+.5,z+2.6),(.35,.32,.06),lamp)
        for side in [-1,1]:
            for col in range(9):
                xx=x+side*w/2;yy=front+bow+(col+.5)*(d-bow)/9
                g.panel((xx+side*.03,yy,z+1.4),(d-bow)/9-.06,2.76,glass if floor<4 else upperglass,side*math.pi/2)
                box((xx-side*.75,yy,z+1.4),(.1,2.04,2.7),warm[1 if (col+floor)%6==0 or floor<2 else 3])
                g.rod((xx,yy-1.05,z),(xx,yy-1.05,z+2.88),.035,trim,6)
    roof_detail(x,y,w,d,h,5)
    sign('TSUTAYA',x,front-.2,6.65,19.6,1.15,metal,1.36)
    shop_positions.append((x,front-1,2.8,w))
    return x,front

def tower_109():
    x,y,r,h=-15.2,35.7,4.4,36
    obstacle(x,y,r*2,r*2,h)
    g.rod((x,y,.1),(x,y,h),r,stone,64)
    # Vertical seams and narrow recessed windows make a full-height landmark.
    for i in range(48):
        a=i*math.tau/48;xx=x+(r+.018)*math.cos(a);yy=y+(r+.018)*math.sin(a)
        g.rod((xx,yy,1),(xx,yy,29.1),.018,trim,5)
        if i%4==0:
            for z in [7.3,10.6,13.9,17.2,20.5,23.8,27.1]:g.panel((xx,yy,z),.33,1.55,blueglass,a+math.pi/2)
    for z in np.arange(3,36,3):g.rod((x,y,float(z)),(x,y,float(z)+.045),r+.035,trim,64)
    g.rod((x,y,29.7),(x,y,35.8),r+.065,cladding[3],64)
    for z in [29.7,35.8]:g.rod((x,y,z),(x,y,z+.10),r+.16,trim,64)
    g.text('SHIBUYA',(x,y-r-.13,34.2),1.11,pink,font=font)
    g.text('109',(x,y-r-.14,31.85),3.45,pink,font=font)
    sign('SHIBUYA 109',x,y-r-.15,3.2,7.7,.85,metal,.65)
    for dx in [-2.6,-1.3,0,1.3,2.6]:
        yy=y-math.sqrt(r*r-dx*dx)-.03
        g.panel((x+dx,yy,1.4),1.12,2.4,glass)
    # The separate square UNIQLO sign stands beside, rather than covers, 109.
    box((x-6.25,y-2.4,25.9),(3.4,2.1,5.2),concrete)
    sign('UNI\nQLO',x-6.25,y-3.51,26.15,3.4,3.6,red,1.13)

def tree(x,y,scale=1):
    height=6.5*scale;radius=2.75*scale
    obstacle(x,y,.52*scale,.52*scale,height+1.9*scale)
    colliders[-1].update(cameraRadius=radius,cameraMinY=height-2.1*scale)
    g.rod((x,y,.2),(x+.07,y,height-.75),.19*scale,bark,10,.09*scale)
    for i in range(9):
        a=i*2.4;rr=(.8+random.random()*.7)*scale
        g.rod((x,y,height-1.8),(x+math.cos(a)*rr,y+math.sin(a)*rr,height+random.uniform(-.5,.4)),.065*scale,bark,6,.018*scale)
    for i in range(1100):
        a=random.random()*math.tau;r=radius*random.random()**.5
        px=x+math.cos(a)*r;py=y+math.sin(a)*r;pz=height+random.uniform(-2.1,2.1)*scale*math.sqrt(max(.15,1-(r/radius)**2))
        angle=random.random()*math.tau;length=random.uniform(.28,.48)*scale;width=length*.62
        axis=Vector((math.cos(angle)*length,math.sin(angle)*length,random.uniform(-.16,.16)*scale))
        cross=Vector((-math.sin(angle)*width,math.cos(angle)*width,.025*scale));center=Vector((px,py,pz))
        verts=[tuple(center-axis),tuple(center-axis*.3+cross),tuple(center+axis*.55+cross*.75),tuple(center+axis),tuple(center+axis*.55-cross*.75),tuple(center-axis*.3-cross),tuple(center+Vector((0,0,.045*scale)))]
        g.mesh(verts,[(0,1,6),(1,2,6),(2,3,6),(3,4,6),(4,5,6),(5,0,6)],random.choice(leaves))
    box((x,y,.23),(1.55*scale,1.55*scale,.42),stone)
    box((x,y,.45),(1.31*scale,1.31*scale,.035),bark)

def lamp_post(x,y):
    g.rod((x,y,.1),(x,y,4.8),.065,metal,10,.042)
    g.rod((x,y,.1),(x,y,.52),.14,metal,10,.11)
    g.rod((x,y,4.5),(x+.5,y,4.84),.046,metal)
    box((x+.48,y,4.79),(.55,.38,.10),metal)
    box((x+.48,y,4.72),(.43,.29,.035),lamp)

def bench(x,y,angle=0):
    for k in range(4):box((x,y+(k-1.5)*.12,.55),(1.85,.09,.065),wood,angle)
    for z in [.79,.94,1.09]:box((x,y+.23,z),(1.85,.065,.095),wood,angle)
    for dx in [-.66,.66]:g.rod((x+dx,y,.1),(x+dx,y,.6),.04,metal)

def shelter(x,y):
    for dx in [-2.4,2.4]:
        for dy in [-.52,.52]:g.rod((x+dx,y+dy,.1),(x+dx,y+dy,2.75),.055,trim)
    box((x,y,2.84),(5.35,1.66,.18),metal)
    g.panel((x,y+.56,1.52),4.8,2.35,glass)
    bench(x-.95,y);bench(x+1.02,y)
    sign('SHIBUYA BUS STOP',x,y-.82,2.84,5.05,.32,blue,.19)
    box((x+2.45,y+.35,1.63),(.08,.42,.68),cream)

def signal(x,y):
    g.rod((x,y,.1),(x,y,3.75),.07,metal,10)
    box((x,y-.04,3.45),(.31,.30,.9),metal)
    for i,mt in enumerate([red,yellow,green]):g.sphere((x,y-.213,3.74-i*.28),(.087,.024,.087),mt,10,6)
    box((x+.28,y,2.5),(.24,.18,.33),metal);g.text('人',(x+.28,y-.1,2.5),.22,green,font=jp)

def planter(x,y,w,d):
    obstacle(x,y,w,d,1.25)
    box((x,y,.35),(w,d,.60),granite)
    box((x,y,.67),(w-.22,d-.22,.07),bark)
    for i in range(max(2,int(w/.45))):
        for j in range(max(1,int(d/.45))):
            xx=x-w/2+.3+i*.43;yy=y-d/2+.3+j*.40
            g.sphere((xx,yy,.84+random.uniform(-.06,.08)),(.37,.33,.31),leaves[(i+j)%5],8,5)

def ground():
    box((0,7.5,-2.62),(240,235,.5),concrete)
    box((0,0,-.055),(94,94,.12),asphalt)
    # Four adjoining tiles completely surround the baked core, without coplanar
    # overlap. Every backdrop building now has actual terrain underneath it.
    for x,y,w,d in [(-83.5,7.5,73,235),(83.5,7.5,73,235),(0,86,94,78),(0,-78.5,94,63)]:
        box((x,y,-.055),(w,d,.12),district_asphalt)
    # Streets continue through the expanded side blocks and meet a rear T street.
    for x,y,w,d in [(-28,54.5,38,15),(28,54.5,38,15),(0,98.5,240,53),
                    (-54,35.5,14,53),(-95.5,35.5,49,53),(89.5,35.5,61,53),
                    (-83.5,-59.5,73,101),(89.5,-59.5,61,101),
                    (28,-78.5,38,63),(-28,-78.5,38,63)]:
        box((x,y,-.015),(w,d,.20),district_paving)
    # Curbs and paving joints reveal continuous sidewalks in rear/orbit views.
    for sx in [-1,1]:
        box((sx*9,54.5,.02),(.23,15,.19),granite)
        box((sx*9,-78.5,.02),(.23,63,.19),granite)
        for sy in [-1,1]:
            spans=[(59,120)] if sx==1 else ([(47,61),(71,120)] if sy==1 else [(47,120)])
            for lo,hi in spans:box((sx*(lo+hi)/2,sy*9,.02),(hi-lo,.23,.19),granite)
    box((0,72,.02),(240,.23,.19),granite)
    # Leave the rear road's mouth open at the T junction.
    for xx in [-64.5,64.5]:box((xx,62,.02),(111,.23,.19),granite)
    for x in [-71,-61,59]:box((x,35.5,.02),(.23,53,.19),granite)
    # Continue the same slab size and staggered joints along all new approaches.
    def paving_strip(x0,x1,y0,y1):
        for row in range(int((y1-y0)/.9)):
            yy=y0+row*.9
            box(((x0+x1)/2,yy,.088),(x1-x0,.012,.008),concrete)
            for xx in np.arange(x0+(row%2)*.9,x1,1.8):box((float(xx),yy+.44,.088),(.012,.88,.008),concrete)
    for x0,x1,y0,y1 in [(-119,-71.2,9.2,12.0),(-60.8,-47,9.2,12.0),(59.2,119,-12,-9.2),(-119,-47,-12,-9.2),
                         (59.2,119,9.2,12),(9.2,13,-109,-47),(-13,-9.2,-109,-47),
                         (-47,-9.2,47,61.8),(9.2,47,47,61.8)]:paving_strip(x0,x1,y0,y1)
    for sx in [-1,1]:
        for sy in [-1,1]:
            # The eastern side avenue has an open mouth at x=47..59.
            spans=[(59.2,118)] if sx==1 else ([(47,60.8),(71.2,118)] if sy==1 else [(47,118)])
            for lo,end in spans:
                box((sx*(lo+end)/2,sy*9.85,.096),(end-lo,.43,.02),district_yellow)
                box((sx*(lo+end)/2,sy*8.75,.030),(end-lo,.12,.004),district_yellow)
        box((sx*9.85,-78.5,.096),(.43,63,.02),district_yellow)
        box((sx*8.75,-78.5,.030),(.12,63,.004),district_yellow)
        box((sx*9.85,54.5,.096),(.43,15,.02),district_yellow)
        box((sx*8.75,54.5,.030),(.12,15,.004),district_yellow)
    # Side-street drains and inspection covers use the same metalwork as the core.
    for x,y in [(-61,8.65),(-83,-8.65),(-104,8.65),(75,-8.65),(98,8.65),(8.65,-66),(-8.65,-88)]:
        box((x,y,.015),(.76,.38,.02),drain)
        for k in range(6):box((x-.31+k*.12,y,.029),(.045,.31,.009),metal)
    for x,y in [(-72,5),(86,-4),(-5,-72),(5,-96)]:g.rod((x,y,.010),(x,y,.024),.42,drain,32)
    for x in range(-114,119,5):
        box((x,66.9,.028),(2.5,.12,.006),district_paint)
    for yy in range(14,60,5):
        for xx in [-66,53]:box((xx,yy,.030),(.10,2,.008),district_paint)
    for sx in [-1,1]:
        for sy in [-1,1]:
            # Chamfered curb corners leave room for the diagonal scramble crossing.
            points=[(9,11.8),(11.8,9),(47,9),(47,47),(9,47)]
            points=[(sx*x,sy*y) for x,y in points]
            if sx*sy<0:points.reverse()
            # The station stairwell remains an actual opening in the pavement.
            if sx==1 and sy==-1:
                for x,y,w,d in [(12.8,-29.4,7.6,35.2),(36.2,-28,21.6,38),(21,-11.2,8.8,4.4),(21,-35.8,8.8,22.4)]:box((x,y,-.015),(w,d,.20),sidewalk)
                prism([(9,-11.8),(16.6,-11.8),(16.6,-9),(11.8,-9)],-.115,.20,sidewalk)
            else:prism(points,-.115,.20,sidewalk)
            for a,b in [((9,11.8),(11.8,9)),((9,11.8),(9,47)),((11.8,9),(47,9))]:
                ax,ay=sx*a[0],sy*a[1];bx,by=sx*b[0],sy*b[1]
                length=math.hypot(bx-ax,by-ay);angle=math.atan2(by-ay,bx-ax)
                box(((ax+bx)/2,(ay+by)/2,.02),(length,.23,.19),granite,angle)
            for k in range(13,47):
                box((sx*9.02,sy*k,.119),(.27,.018,.015),concrete)
                box((sx*k,sy*9.02,.119),(.018,.27,.015),concrete)
            box((sx*9.85,sy*29.4,.096),(.43,35.2,.02),yellow)
            box((sx*29.4,sy*9.85,.096),(35.2,.43,.02),yellow)
            # Wider tactile pads at the crossing arrivals, with raised dot geometry.
            for x,y in [(10.8,12.4),(12.4,10.8)]:
                box((sx*x,sy*y,.096),(1.0,.85,.022),yellow)
                for i in range(5):
                    for j in range(4):g.rod((sx*(x-.36+i*.18),sy*(y-.27+j*.18),.11),(sx*(x-.36+i*.18),sy*(y-.27+j*.18),.125),.027,yellow,6)
            # Rectangular stone slabs with staggered joints, rather than a square grid.
            for row in range(41):
                y=10.2+row*.9;lo=11.8 if y<11.8 else 9.25
                spans=[(lo,47)] if not(sx==1 and sy==-1 and 13.4<y<24.6) else [(lo,16.6),(25.4,47)]
                for a,b in spans:box((sx*(a+b)/2,sy*y,.088),(b-a,.012,.008),concrete)
                for col in range(21):
                    x=lo+col*1.8+(row%2)*.9
                    hole=sx==1 and sy==-1 and 16.6<x<25.4 and 12.5<y<24.6
                    if x<46.9 and not hole:box((sx*x,sy*(y+.44),.088),(.012,.88,.008),concrete)
    # Paint is clipped into disjoint bands where straight and diagonal routes meet.
    def clip(poly,a,b,c):
        result=[]
        for p,q in zip(poly,poly[1:]+poly[:1]):
            fp=a*p[0]+b*p[1]-c;fq=a*q[0]+b*q[1]-c
            if fp>=0:result.append(p)
            if (fp>=0)!=(fq>=0):
                t=fp/(fp-fq);result.append((p[0]+t*(q[0]-p[0]),p[1]+t*(q[1]-p[1])))
        return result
    def marking(poly):
        # 25 mm clearance survives Draco quantization and distant depth testing.
        if len(poly)>=3:g.mesh([(x,y,.030) for x,y in poly],[tuple(range(len(poly)))],paint)
    for i in range(-9,10):
        for s in [-1,1]:
            for swap in [False,True]:
                x=i*.94;y=s*11.25
                poly=[(x-.29,y-1.8),(x+.29,y-1.8),(x+.29,y+1.8),(x-.29,y+1.8)]
                if swap:poly=[(v,u) for u,v in poly][::-1]
                # Reserve the diagonal band continuously to its chamfered curb.
                marking(clip(poly,1,-1,2.08));marking(clip(poly,-1,1,2.08))
    for i in range(-15,16):
        p=i*.68;co=math.sqrt(.5)
        poly=[(p+(a-b)*co,p+(a+b)*co) for a,b in [(-.27,-2.08),(.27,-2.08),(.27,2.08),(-.27,2.08)]]
        marking(clip(clip(poly,1,1,-20.77),-1,-1,-20.77))
    for i in range(19,117,5):
        mat=paint if i<47 else district_paint
        for s in [-1,1]:
            if (s==1 and i<61) or (s==-1 and i<108):box((s*2.2,s*i,.030),(.10,2,.008),mat)
            box((s*i,s*2.2,.030),(2,.10,.008),mat)
    for s in [-1,1]:
        box((s*4.5,s*14.1,.030),(8.1,.32,.005),paint)
        box((s*14.1,-s*4.5,.030),(.32,8.1,.005),paint)
        # Painted edge lines, repaired seams, drains and utility covers.
        for k in [-1,1]:
            box((k*8.75,s*30,.030),(.12,30,.004),yellow)
            box((s*30,k*8.75,.030),(30,.12,.004),yellow)
        for y in [17,28,40]:
            box((s*8.65,s*y,.008),(.38,.86,.009),drain)
            for j in range(7):box((s*8.65,s*y-.35+j*.11,.014),(.29,.037,.005),metal)
    for x,y,r in [(-6,-23,.44),(6,19,.40),(-25,5,.38),(28,-4,.46)]:
        g.rod((x,y,.006),(x,y,.012),r,drain,32)
        for j in range(-3,4):box((x,y+j*.09,.017),(math.sqrt(max(.01,r*r-(j*.09)**2))*1.6,.023,.006),trim)
    for x,y,w,d in [(-6,-31,2.7,4.5),(5,26,2.4,3.2),(-32,5,4.1,2.2),(31,-6,3.4,2.1)]:box((x,y,.0065),(w,d,.002),patch)

def station():
    x,y=21,-18
    for i in range(13):box((x,-21+i*.50,-.05-i*.16),(7.8,.51,.18),stone)
    for xx in [16.8,25.2]:
        box((xx,y,-.2),(.32,6.3,3.7),stone)
        g.rod((xx,-21.1,.9),(xx,-15.3,.9),.05,trim)
        box((xx,-21,.95),(.48,.55,2.1),granite)
        box((xx,-21,3.1),(.48,.55,2.2),granite)
    box((x,y,4.29),(9.1,6.6,.25),roofing)
    sign('JR   渋谷駅',x,-21.35,3.55,8.9,1.27,green,.89,japanese=True)
    g.text('Shibuya Station',(x,-21.51,3.09),.29,white,font=font)
    for xx in [18,21,24]:box((xx,-19,4.11),(.95,.42,.06),lamp)
    obstacle(x,-18,8.9,6.6,4.5)

def streets():
    for x,y,s in [(-12.2,14,.9),(-11.8,44,.95),(12.6,13.3,.85),(11.8,43,1),(-11.5,-16,.95),(-11.6,-29,1.1),(12.9,-14,1.0),(11.7,-32,1.1),(-28,-11.5,.95),(-38,-11.5,1),(33,-11.4,1),(42,10.7,.9),(-31,10.7,.85)]:tree(x,y,s)
    for sx in [-1,1]:
        for sy in [-1,1]:
            signal(sx*12.7,sy*10.15)
            for y in [18,29,40]:lamp_post(sx*9.6,sy*y)
            for y in range(14,45,4):
                g.rod((sx*9.6,sy*y,.1),(sx*9.6,sy*y,.75),.068,metal)
                if y<41:g.rod((sx*9.6,sy*y,.62),(sx*9.6,sy*(y+4),.62),.026,metal)
    shelter(-22,-12.1);obstacle(-22,-12.1,5.5,1.9,3.0)
    bench(-31,-12.2);bench(32,-12)
    for x,y,w,d in [(-34,-14,4.3,1.2),(-30,-29,5.4,1.4),(-16,-31,5.2,1.2),(-31,-38,4.5,1.3),(30,-29,5,1.3),(37,-13,4,1.2),(14.8,13.8,1.2,2.3)]:planter(x,y,w,d)
    for x,y in [(-30,-26.5),(-16,-28.5),(31,-26.5)]:bench(x,y);obstacle(x,y,2.0,.72,1.2)
    for x in [-30,-28.5,-27]:
        box((x,11.65,1.06),(1.25,.74,2.05),red)
        g.panel((x,11.27,1.3),1.02,1.03,warm[2])
        for j in range(3):
            for k in range(4):box((x-.34+k*.22,11.22,1+j*.27),(.11,.025,.15),books[(k+j)%4])
        box((x,11.24,.44),(.63,.027,.19),metal)
    for x,y in [(-12,-11),(13,12),(-33,10.4),(34,-12)]:
        box((x,y,.7),(.63,.62,1.3),metal);box((x,y-.32,1.12),(.46,.04,.20),black)
        sign('MAP',x+.68,y,1.49,.67,1.12,blue,.26)

def facade_strip(path,z,height,mat,offset=0):
    """A continuous vertical ribbon following the building's actual outline."""
    for a,b in zip(path,path[1:]):
        angle=math.atan2(b[1]-a[1],b[0]-a[0]);nx,ny=math.sin(angle),-math.cos(angle)
        aa=(a[0]+nx*offset,a[1]+ny*offset);bb=(b[0]+nx*offset,b[1]+ny*offset)
        g.mesh([(*aa,z-height/2),(*bb,z-height/2),(*bb,z+height/2),(*aa,z+height/2)],[(0,1,2,3)],mat)


def path_label(body,path,z,size,mat,offset=.12,inset=.75,font=jp):
    lengths=[math.dist(a,b) for a,b in zip(path,path[1:])];total=sum(lengths)
    for index,letter in enumerate(body):
        distance=inset+(total-2*inset)*(index+.5)/len(body)
        for a,b,length in zip(path,path[1:],lengths):
            if distance<=length:
                t=distance/length;angle=math.atan2(b[1]-a[1],b[0]-a[0])
                px=a[0]+(b[0]-a[0])*t+math.sin(angle)*offset
                py=a[1]+(b[1]-a[1])*t-math.cos(angle)*offset
                g.text(letter,(px,py,z),size,mat,angle,font);break
            distance-=length


def taiseido():
    """Photographed Center-gai shop: bowed signs, small entrance, upper ad board."""
    x,y,w,d,h=-54,20,10,16,18
    front=y-d/2;bow=1.05
    edge=[(x-w/2+w*i/24,front+bow*(2*i/24-1)**2) for i in range(25)]
    outline=edge+[(x+w/2,y+d/2),(x-w/2,y+d/2)]
    obstacle(x,y,w,d,h)
    # The upper frontage is occupied by advertising, not an office-window grid.
    prism(outline,3.1,h-3.1,porcelain)
    prism(outline,.10,.12,porcelain)
    box((x,y+2,1.6),(w,d-4,3.0),porcelain)
    for dx in [-4.45,4.45]:box((x+dx,front+1.0,1.6),(1.1,2.0,3.0),porcelain)
    for z in np.arange(.4,3.1,.34):
        for dx in [-4.45,4.45]:box((x+dx,front-.03,float(z)),(1.06,.04,.017),stone)
    # Recessed doorway and outward-facing magazine racks, as in the shop photo.
    g.panel((x,front+1.0,1.55),2.25,2.8,black)
    box((x,front+.13,.24),(2.4,1.75,.07),black)
    for dx in [-2.35,2.35]:
        g.panel((x+dx,front+.22,1.65),2.0,2.65,warm[1])
        for row in range(5):
            z=.38+row*.46
            box((x+dx,front-.20,z),(1.8,.58,.07),metal)
            for col in range(6):
                xx=x+dx-.73+col*.29
                box((xx,front-.42,z+.21),(.255,.055,.38),books[(row+col)%4])
                g.panel((xx,front-.455,z+.22),.17,.045,porcelain)
    for dx in [-1.16,1.16]:box((x+dx,front+.90,1.55),(.07,.14,2.8),silver)
    # Blue canopy and white sign bend across the entire convex shop front.
    facade_strip(edge,3.28,.28,bookblue,.34)
    path_label('TAISEIDO',edge,3.28,.27,porcelain,.39,inset=2.1,font=font)
    facade_strip(edge,4.90,2.88,bookblue,.08)
    facade_strip(edge,4.90,2.60,porcelain,.13)
    for z in [3.77,6.03]:facade_strip(edge[3:-3],z,.065,bookred,.19)
    for p in [edge[3],edge[-4]]:g.rod((p[0],p[1]-.22,3.77),(p[0],p[1]-.22,6.03),.034,bookred,6)
    path_label('大盛堂書店',edge,4.95,2.55,bookblue,.24,inset=.18)
    g.text('BOOKS TAISEIDO',(x+3.25,front+.20,3.99),.18,bookred,font=font)
    # A metal maintenance grate and floodlights sit immediately above the sign.
    for a,b in zip(edge,edge[1:]):
        for dy in [.20,.75]:g.rod((a[0],a[1]-dy,6.51),(b[0],b[1]-dy,6.51),.028,metal,5)
        g.rod((a[0],a[1]-.20,6.51),(a[0],a[1]-.75,6.51),.019,metal,5)
    # DMM is documented here; the neutral board is not a claimed current campaign.
    curved_screen(x,front-.12,11.58,w-.24,9.68,cladding[3],bow)
    ad_edge=[(x-4.3+8.6*i/20,front-.12+bow*(2*(x-4.3+8.6*i/20-(x-w/2))/w-1)**2) for i in range(21)]
    path_label('DMM',ad_edge,8.45,3.25,porcelain,.12,inset=.25,font=font)
    for dx in [-3.7,0,3.7]:
        yy=front+bow*(dx/(w/2))**2
        g.rod((x+dx,yy-.2,6.52),(x+dx,yy-.72,7.02),.035,metal,6)
        box((x+dx,yy-.72,7.05),(.55,.29,.23),metal)
    for z in [16.55,18.04]:facade_strip(edge,z,.10,silver,.04)
    sign('大\n盛\n堂\n商\n事\nビ\nル',x+w/2+.20,front+3.0,12.0,1.25,7.0,bookblue,.71,math.pi/2,True)
    prism(outline,h,.15,silver)
    facade_strip(edge,h+.3,.42,porcelain,.01)
    for dx in [-2.7,1.1]:
        box((x+dx,y+3,h+.48),(1.45,1.55,.8),stone)
        for dz in [-.23,0,.23]:box((x+dx,y+2.21,h+.48+dz),(1.15,.035,.055),metal)
    for yy in [y+1,y+6]:g.rod((x-4.5,yy,h+.25),(x+4.5,yy,h+.25),.03,metal,5)
    shop_positions.append((x,front-.7,2.5,8))


def magnet():
    """MAGNET's rounded ceramic hinge, ribbon windows and taller glass frontage."""
    x,y,w,d,h=70,25,22,28,34
    front=y-d/2
    obstacle(x,y,w,d,h)
    # The white wing ends where the glass tower starts. Overlapping solids here
    # used to leave coplanar white/glass front faces shimmering down the middle.
    radius=4.6;cx=x-11+radius;cy=front+radius
    # Follow the western elevation into the curved front-left corner. The
    # original box lost this distinctive junction in every street-level view.
    wing_edge=[(x-11,y+d/2),(x-11,cy)]
    wing_edge.extend((cx+radius*math.cos(math.pi+i*math.pi/40),cy+radius*math.sin(math.pi+i*math.pi/40)) for i in range(1,21))
    wing_edge.append((x-1,front))
    wing_outline=wing_edge+[(x-1,y+d/2)]
    prism(wing_outline,0,27.6,porcelain)
    for z in [9.4,12.9,16.4,19.9,23.4]:
        facade_strip(wing_edge,z,.83,blueglass,.055)
        for dz in [-.46,.46]:facade_strip(wing_edge,z+dz,.055,silver,.07)
    for z in np.arange(6.5,27.5,.70):facade_strip(wing_edge,float(z),.015,stone,.025)
    for a in [math.pi+i*math.pi/10 for i in range(6)]:
        px=cx+(radius+.028)*math.cos(a);py=cy+(radius+.028)*math.sin(a)
        g.rod((px,py,6.4),(px,py,27.5),.009,stone,4)
    # Narrow vertical advertising blade beside the curved wing.
    box((x-11.16,front+10.5,17),(.24,2.3,19),metal)
    g.panel((x-11.34,front+10.5,17),2.1,18.5,porcelain,-math.pi/2)
    g.text('M\nA\nG\nN\nE\nT',(x-11.40,front+10.5,17),1.25,magred,-math.pi/2,font)
    # Taller glazed square tower at the station-facing corner; stepped crown.
    box((x+5,y-3,h/2),(12,d-6,h),blueglass)
    box((x+2,y+11,15.5),(6,6,31),blueglass)
    for zz in np.arange(1.8,h,1.8):
        box((x+5,front-.035,float(zz)),(12,.065,.055),silver)
        box((x+11.035,y-3,float(zz)),(.065,d-6,.055),silver)
    for xx in np.arange(x-.9,x+11,1.5):box((float(xx),front-.04,17),(.055,.065,34),silver)
    for yy in np.arange(front+.8,y+8,1.5):box((x+11.04,float(yy),17),(.065,.055,34),silver)
    # The tower's exposed upper western elevation also has a curtain-wall grid.
    for zz in [28.8,30.6,32.4,33.95]:box((x-1.035,y-3,zz),(.065,d-6,.055),silver)
    for yy in np.arange(front+.8,y+8,1.5):box((x-1.035,float(yy),30.8),(.065,.055,6.4),silver)
    for zz in [28.8,30.6]:box((x-1.035,y+11,zz),(.065,6,.055),silver)
    for yy in [y+8,y+9.5,y+11,y+12.5,y+14]:box((x-1.035,yy,29.3),(.065,.055,3.4),silver)
    # Deep rectangular advertising frame on the glass tower, and small lower screen.
    box((x+5,front-.55,20),(9.6,.95,17.2),metal)
    g.panel((x+5,front-1.04,20),8.7,16.25,cladding[0])
    g.panel((x+5,front-1.10,19.3),7.9,7.4,blueglass)
    # Retain the operator's red/cyan identity instead of white generic lettering.
    serif=bpy.data.fonts.load('C:/Windows/Fonts/georgiab.ttf')
    for dx,dy,mat in [(.045,.04,magcyan),(0,0,magred)]:
        label=g.text('MAGNET',(x+5+dx,front-1.16+dy,24.8),1.45,mat,font=serif)
        label.data.space_character=1.05
    g.text('by SHIBUYA109',(x+5,front-1.17,23.75),.46,magred,font=serif)
    # Crossing-shaped stripes approximate the official angular M emblem.
    for a,b,mat in [((-1.0,.95),(.95,-.90),magred),((-1.0,.40),(.35,-.90),magcyan),((-1.0,-.15),(-.20,-.90),magred),
                    ((.12,.20),(1.0,1.03),magcyan),((.46,-.15),(1.0,.36),magred),((.78,-.49),(1.0,-.29),magcyan)]:
        vx,vz=b[0]-a[0],b[1]-a[1];length=math.hypot(vx,vz);nx,nz=-vz/length*.105,vx/length*.105
        yy=front-(1.25 if mat==magred else 1.19)
        g.mesh([(x+5+xx,yy,26.8+zz) for xx,zz in [(a[0]+nx,a[1]+nz),(a[0]-nx,a[1]-nz),(b[0]-nx,b[1]-nz),(b[0]+nx,b[1]+nz)]],[(0,1,2,3)],mat)
    g.text('MAGNET',(x-5.4,front-.17,5.5),.90,magred,font=serif)
    g.text('by SHIBUYA109',(x-5.4,front-.18,4.78),.28,magred,font=serif)
    # Roof viewing terrace, open steel safety fence and glazed corner lookout.
    prism(wing_outline,27.6,.14,roofing)
    for a,b in zip(wing_edge,wing_edge[1:]):
        g.rod((*a,28.82),(*b,28.82),.035,metal,6)
        steps=max(1,math.ceil(math.dist(a,b)/.55))
        for i in range(steps):
            xx=a[0]+(b[0]-a[0])*i/steps;yy=a[1]+(b[1]-a[1])*i/steps
            g.rod((xx,yy,27.74),(xx,yy,28.82),.018,metal,5)
    for xx in [x-5,x-2]:
        g.panel((xx,front-.10,1.5),2.55,2.6,glass)
        box((xx,front+.55,1.4),(2.4,.10,2.6),warm[1])
    box((x-4.25,front-.33,3.12),(5.55,.82,.16),metal)
    g.panel((x+4.5,front-.10,4.55),10.4,1.95,glass)
    for xx in [x+1,x+9]:g.rod((xx,y+5,34),(xx,y+5,36),.04,metal)
    shop_positions.append((x-4.0,front-.9,2.6,6))


def mark_city():
    """Mark City's long shopping podium, slimmer East hotel and taller West office."""
    x,y=-78,-36
    box((x,y,3.1),(58,22,6.2),porcelain);obstacle(x,y,58,22,6.2)
    for sy in [-1,1]:
        yy=y+sy*11
        for xx in np.arange(-105,-49,2.4):
            g.panel((float(xx),yy+sy*.05,3.15),2.3,4.8,hotelglass,0 if sy<0 else math.pi)
            box((float(xx)-1.18,yy,3.2),(.13,.25,6.0),silver)
        box((x,yy,6.1),(58,.35,.30),silver)
    # Towers are modeled separately, preserving the two distinct proportions.
    for tx,ty,w,d,h,hotel in [(-59,-33,18,20,57,True),(-94,-36,22,22,70,False)]:
        box((tx,ty,(h+6.3)/2),(w,d,h-6.3),hotelglass);obstacle(tx,ty,w,d,h)
        floors=25 if hotel else 23;step=(h-6.3)/floors
        for i in range(floors+1):
            zz=6.3+i*step
            box((tx,ty,zz),(w+.14,d+.14,.13),silver)
            if hotel:
                for sy in [-1,1]:box((tx,ty+sy*(d/2+.035),zz+.52),(w-.10,.08,.82),porcelain)
        for sx in [-1,1]:
            for yy in np.arange(ty-d/2+.65,ty+d/2,1.3):box((tx+sx*(w/2+.06),float(yy),(h+6.3)/2),(.10,.075,h-6.3),silver)
        for sy in [-1,1]:
            for xx in np.arange(tx-w/2+.65,tx+w/2,1.3):box((float(xx),ty+sy*(d/2+.06),(h+6.3)/2),(.075,.10,h-6.3),silver)
            if hotel:
                # Solid center strip and narrow glass edge piers on the hotel.
                box((tx,ty+sy*(d/2+.12),32),(w*.34,.22,51),porcelain)
                for zz in np.arange(8,56,step):g.panel((tx,ty+sy*(d/2+.25),float(zz)),w*.29,step*.58,hotelglass,0 if sy<0 else math.pi)
        box((tx,ty,h+1.35),(w*.76,d*.72,2.7),silver)
        for zz in np.arange(h+.15,h+2.7,.38):box((tx,ty-d*.36-.02,float(zz)),(w*.76,.05,.04),metal)
        if hotel:
            box((tx,ty,h+4.0),(w*.35,d*.45,2.6),silver)
            g.rod((tx,ty,h+4),(tx,ty,h+8.0),.055,metal)
    sign('SHIBUYA MARK CITY',-76,-47.2,4.6,33,1.3,metal,1.25)
    sign('SHIBUYA MARK CITY',-76,-24.8,4.6,33,1.3,metal,1.25,math.pi)
    sign('EAST MALL',-49,-33,4.5,14,1.0,metal,.80,math.pi/2)


def station_deck():
    """Covered second-level station walkway, derived from the west-side network.

    This is a compressed scenic connection, outside the scramble and traffic
    envelope. Only its ground piers/stair flights receive movement colliders.
    """
    # One continuous L/U outline avoids overlapping deck/roof faces at elbows.
    def outline(r):
        return [(-48.4-r,-33),(-48.4-r,-48-r),(21+r,-48-r),(21+r,-44),
                (21-r,-44),(21-r,-48+r),(-48.4+r,-48+r),(-48.4+r,-33)]
    edge=outline(2.1)
    prism(edge,5.54,.42,silver)
    prism(edge,5.96,.055,deck_paving)
    prism(outline(2.225),8.66,.16,silver)
    for a,b in zip(edge,edge[1:]+edge[:1]):
        # Open mouths at the shopping podium and station stairs.
        if a[1]==b[1] and a[1] in [-33,-44]:continue
        angle=math.atan2(b[1]-a[1],b[0]-a[0]);length=math.dist(a,b)
        for zz in [6.14,7.13]:g.rod((*a,zz),(*b,zz),.045,metal)
        g.panel(((a[0]+b[0])/2,(a[1]+b[1])/2,6.65),length,1.0,glass,angle)
    def span(a,b):
        ax,ay=a;bx,by=b;length=math.dist(a,b);angle=math.atan2(by-ay,bx-ax)
        nx,ny=-math.sin(angle),math.cos(angle);cx,cy=(ax+bx)/2,(ay+by)/2
        for i in range(max(1,int(length/5.7))+1):
            t=i/max(1,int(length/5.7));xx=ax+(bx-ax)*t;yy=ay+(by-ay)*t
            for side in [-1,1]:g.rod((xx+nx*side*1.88,yy+ny*side*1.88,5.98),(xx+nx*side*1.88,yy+ny*side*1.88,8.7),.052,silver)
            box((xx,yy,8.61),(.22,4.05,.16),metal,angle)
            box((xx,yy,8.48),(.4,1.2,.035),lamp,angle)
        for t in [.08,.50,.92]:
            xx=ax+(bx-ax)*t;yy=ay+(by-ay)*t
            # Keep the extended road center free even beneath the bridge.
            if abs(xx)<10:continue
            g.rod((xx,yy,.1),(xx,yy,5.55),.30,porcelain,12)
            obstacle(xx,yy,.65,.65,5.55)
    span((-48.4,-33),(-48.4,-48))
    span((-48.4,-48),(21,-48))
    span((21,-48),(21,-44))
    # Two rising stair flights with a landing and parallel stainless handrails.
    for i in range(32):
        yy=-32-(i+.5)*.375;top=(i+1)*.1875
        box((21,yy,top/2),(3.7,.38,top),deck_paving)
        box((21,yy+.15,top+.015),(3.6,.065,.025),deck_yellow)
    for xx in [19.2,21,22.8]:
        g.rod((xx,-32,1.0),(xx,-44,7.0),.045,trim)
        for i in range(9):
            yy=-32-i*1.5;zz=i*.75
            g.rod((xx,yy,zz),(xx,yy,zz+1.0),.035,trim)
    obstacle(21,-38,3.8,12,6.1)
    sign('渋谷駅   SHIBUYA STATION  →',-13,-50.15,6.62,20,.60,green,.50,japanese=True)
    sign('←  MARK CITY',-30,-50.15,6.62,10,.60,metal,.49)


def city():
    ground()
    tx,tf=tsutaya()
    building(43,20,10,15,19.3,'STARBUCKS',style=2)
    building(-27,22,17,20,25,'BIG ECHO',style=0)
    building(-41,23,9,21,21,'BOOKS & COFFEE',style=1)
    building(-15.5,23,5.4,12,18,'牛かつ',style=3)
    tower_109()
    # Both sides flank an unobstructed 18 m road all the way to the map boundary.
    building(13,22.5,7.4,11,29,'TOKYO RECORDS',style=3)
    building(-26,40,8.5,11,29,'H&M',style=0)
    building(-38,44,12,10,31,style=2)
    building(31,43,16,12,29,style=3)
    building(-40,-30,12,22,15,'SHIBUYA  /  MUSIC',style=1)
    building(42,-36,10,17,14,'TOKYO MARKET',style=0)
    building(-30,-39,7,8,5.8,'交番  KOBAN',style=3)
    for x,w,h,y in [(-43,8,24,57),(-30,11,35,57),(-16,10,23,53),(16,10,34,54),(31,13,38,58),(45,9,27,55)]:building(x,y,w,8,h,style=int(abs(x))%4)
    # A distant cross street and staggered skyline close the view beyond the
    # playable area; the taxi/bus corridor remains completely clear to its exit.
    for x,w,h,y in [(-28,10,27,75),(-15,12,35,82),(0,13,22,88),(15,11,31,80),(28,12,25,75)]:building(x,y,w,9,h,style=int(abs(x)+1)%4)
    anime=artwork('Concept anime billboard',[(174,188),(367,121),(370,317),(185,366)],768,768)
    cat=artwork('Concept cat billboard',[(689,241),(796,232),(797,302),(690,308)],512,384)
    cityposter=artwork('Concept brighter tomorrow',[(847,163),(1030,201),(1032,351),(848,310)],768,768)
    portrait=artwork('Concept DAM portrait',[(692,312),(765,311),(767,376),(691,374)],512,512)
    curved_screen(-27,10.75,18.3,16.2,10.6,anime,1.10)
    sign('カラオケ',-27,11.30,11.55,15.8,1.65,red,1.25,japanese=True)
    sign('BIG ECHO',-27,11.30,9.64,15.8,1.95,red,1.68)
    curved_screen(tx,tf-.23,22.4,18.8,10.2,cityposter,2.10)
    # Separate architectural campaign panel wraps the building's right elevation.
    sign('SHIBUYA\nPEOPLE\nCULTURE\nALWAYS\nMOVES\nFORWARD',37.20,23.8,21.6,12.1,14.4,cladding[0],1.10,math.pi/2)
    g.rod((37.34,18.4,14.8),(37.34,28.7,23.4),.085,pink,6)
    screen(13,16.70,18.8,6.9,4.7,cat)
    sign('DHC',13,16.53,21.94,7,1.35,blue,1.07)
    sign('サロンパス',13,16.53,24.52,7,2.75,green,1.16,japanese=True)
    sign('Hisamitsu',13,16.53,27.0,7,1.6,blue,1.04)
    screen(13,16.68,13.4,6.9,4.85,portrait)
    sign('DAM',13,16.46,11.12,6.9,.70,metal,.68)
    screen(-26,34.3,25,7.7,4.7,cream)
    g.text('H&M',(-26,34.09,25),2.2,brandred,font=font)
    for x,y,z,body,mat in [(-36.2,12.18,12,'も\nっ\nと\n好\nき\nな\n渋\n谷\nを',blue),(-18.4,11.45,13,'カ\nラ\nオ\nケ',red),(16.0,14.5,11.9,'T\nS\nU\nT\nA\nY\nA',blue),(38.2,12.12,12,'渋\n谷\n書\n店',pink),(8.85,16.55,18.1,'も\nん\nじ\nゃ',cream),(-41.2,12.31,9,'珈\n琲',red)]:
        sign(body,x,y,z,1.25,10.5,mat,.80,japanese=True)
    for x,y,z,body,mt in [(-44.6,12.18,12,'音\n楽\n館',pink),(-37.2,12.18,16,'映\n画',blue),(-12.6,16.7,8,'牛\nか\nつ',red),(-17.3,16.7,8,'東\n京\n食\n堂',lamp),(17.0,16.63,13,'レ\nコ\nー\nド',blue),(-21.5,34.2,18,'フ\nァ\nッ\nシ\nョ\nン',red),(39,12.25,8,'本\nと\n珈\n琲',green),(47.3,12.25,11,'渋\n谷\n散\n歩',blue)]:
        sign(body,x,y,z,.86,6,mt,.60,japanese=True)
    # Small secondary signs and lanterns make the ground-level rhythm less uniform.
    for x,y in [(-23,11.2),(-40,12.2),(22,12.4),(43,12.1)]:
        sign('OPEN  /  COFFEE',x,y,4.68,3.8,.65,green,.32)
        for dx in [-1.1,0,1.1]:
            g.rod((x+dx,y-.5,3.65),(x+dx,y-.5,4.17),.18,lamp,12)
            box((x+dx,y-.5,4.18),(.25,.25,.08),metal)
    # Starbucks has its own timber fascia, a coffee counter and upstairs bar seating.
    for xx in [39.6,41.3,43,44.7,46.4]:
        box((xx,13.03,4.03),(1.1,.5,.11),wood)
        g.rod((xx,13.55,3.07),(xx,13.55,3.77),.12,metal,8)
        g.rod((xx,13.55,3.77),(xx,13.55,3.89),.23,wood,12)
    box((43,14.1,1.1),(6.4,.8,1.05),wood)
    for xx in [41.5,43,44.5]:box((xx,14.1,1.82),(.62,.43,.43),metal)
    station();streets()
    taiseido();magnet();mark_city();station_deck()

def setup_lights():
    s=bpy.context.scene;s.render.engine='CYCLES';s.cycles.samples=48;s.cycles.use_denoising=True
    s.world=bpy.data.worlds.new('Blue hour Shibuya');s.world.use_nodes=True
    data=bpy.data.lights.new('Evening sun','SUN');ob=bpy.data.objects.new(data.name,data);s.collection.objects.link(ob)
    for i,(x,y,z,w) in enumerate(shop_positions):
        data=bpy.data.lights.new('Shop spill '+str(i),'AREA');data.energy=140+w*9;data.shape='RECTANGLE';data.size=w*.7;data.size_y=2.2;data.color=(1,.50,.20)
        ob=bpy.data.objects.new(data.name,data);s.collection.objects.link(ob);ob.location=(x,y,z)
        ob.rotation_euler=(Vector((x,y-2,0))-ob.location).to_track_quat('-Z','Y').to_euler();ob['baked_shop']=True;ob['base_power']=data.energy
    apply_preset('evening')
    data=bpy.data.cameras.new('Concept review camera');cam=bpy.data.objects.new(data.name,data);s.collection.objects.link(cam)
    cam.location=(52,-76,63);cam.rotation_euler=(Vector((0,10,9))-cam.location).to_track_quat('-Z','Y').to_euler();data.type='ORTHO';data.ortho_scale=111;s.camera=cam
    s.render.resolution_x=1440;s.render.resolution_y=1100;s.render.resolution_percentage=100

city();objects=g.flush()
for o in objects:
    if 'Glazing' in o.name or o.data.materials[0].get('surface_role')=='road-marking':o.visible_shadow=False
setup_lights()
g.export(ROOT/'public/models/crossing.glb',objects)
metadata={'id':'crossing','name':'Shibuya Crossing','spawn':[0,0,16],'bounds':[-114,114,-118,104],'colliders':colliders,'artRevision':7,'roadHalfWidth':9,'crossingCenter':11.25,'cornerChamfer':2.8,'terrainBounds':[-120,120,-125,110],'landmarks':['Taiseido Bookstore','MAGNET by SHIBUYA109','Shibuya Mark City East','Shibuya Mark City West'],'districtScale':'Concept-scale dimensions and compressed distances; see assets/references/shibuya-landmarks.md','pedestrianDeck':{'scenic':True,'height':6.0,'roadClearance':5.54}}
# Moving traffic owns its current collision volumes in lib/game/traffic.ts.
(ROOT/'public/models/crossing.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/crossing.blend'),compress=True)
renders=ROOT/'work/renders';renders.mkdir(parents=True,exist_ok=True)
s=bpy.context.scene;s.render.image_settings.file_format='PNG';s.render.filepath=str(renders/'crossing.png')
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    s.cycles.device='GPU'
except Exception:pass
if '--skip-render' not in sys.argv:bpy.ops.render.render(write_still=True)
print('CONCEPT_SCENE_COMPLETE',len(objects),'objects',sum(len(o.data.polygons) for o in objects),'faces',flush=True)
