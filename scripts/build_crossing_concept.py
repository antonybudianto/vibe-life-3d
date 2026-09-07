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
asphalt=g.material('Rain-dark asphalt',(.025,.031,.045),.48,.06)
paint=g.material('Crosswalk ivory paint',(.64,.65,.65),.6)
yellow=g.material('Tactile ochre',(.69,.40,.06),.82)
wood=g.material('Walnut shop joinery',(.15,.073,.035),.7)
black=g.material('Soft black rubber',(.012,.015,.023),.83)
cream=g.material('Store plaster',(.46,.38,.28),.85)
glass=g.material('Glazing architectural',(.19,.25,.31),.16,.45,alpha=.19)
blueglass=g.material('Dark reflective glass',(.024,.055,.09),.19,.6)
warm=[g.material('Interior amber '+str(i),c,.7,0,e) for i,(c,e) in enumerate([((.57,.28,.10),.36),((.44,.23,.12),.22),((.73,.46,.20),.52),((.075,.087,.11),0)])]
white=g.material('Ivory neon lettering',(.86,.86,.75),.5,0,1.7)
lamp=g.material('Warm lamps', (1,.52,.18),.35,0,3.2)
pink=g.material('Sakura neon',(.85,.09,.34),.4,0,2.0)
blue=g.material('Electric blue signage',(.025,.23,.62),.45,0,1.1)
green=g.material('Station emerald',(.014,.24,.10),.65,0,.35)
red=g.material('Karaoke vermilion',(.48,.014,.029),.6,0,.18)
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

def building(x,y,w,d,h,shop=None,rounded=False):
    front=y-d/2;levels=round(h/2.7);step=h/levels;r=2.4 if rounded else .12
    obstacle(x,y,w,d,h)
    box((x,y+.5,h/2),(w-2.8,d-2.4,h),concrete)
    for floor in range(levels+1):footprint(x,y,w+.10,d+.10,r,floor*step,.16,trim if rounded else stone)
    # Facades have real shallow rooms and mullions, not flat glowing rectangles.
    columns=max(3,int((w-(r if rounded else 0))/1.85));spacing=(w-(r if rounded else 0))/columns
    for floor in range(levels):
        z=floor*step+.16
        for col in range(columns):
            xx=x-w/2+(col+.5)*spacing
            light=warm[2 if floor<2 else (floor*7+col*3)%4]
            opaque=floor>=2 and not rounded and (col+int(abs(x)))%3!=0
            box((xx,front+1.28,z+step*.46),(spacing-.05,.07,step-.15),light)
            box((xx,front+.66,z+.035),(spacing-.06,1.34,.065),wood if floor<2 else stone)
            box((xx,front-.04,z+step/2),(.055,.12,step),trim)
            g.panel((xx,front-.10,z+step/2),spacing-.07,step-.15,cladding[int(abs(x))%4] if opaque else glass)
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
                opaque=floor>=2 and not rounded and (col+floor//3)%3!=0
                g.panel((xx+side*.05,yy,z+step/2),1.74,step-.18,cladding[int(abs(x))%4] if opaque else glass,side*math.pi/2)
                box((xx,yy-.91,z+step/2),(.12,.055,step),trim)
        if rounded:
            for i in range(8):
                a=-math.pi/2+(i+.5)*math.pi/16;cx=x+w/2-r;cy=front+r
                px=cx+r*math.cos(a);py=cy+r*math.sin(a)
                g.panel((px,py,z+step/2),r*math.pi/16,step-.16,glass,a+math.pi/2)
                box((cx+(r-.48)*math.cos(a),cy+(r-.48)*math.sin(a),z+step/2),(.6,.6,step-.17),warm[(floor+i)%3])
                g.rod((px,py,z),(px,py,z+step),.029,trim,6)
    for dx in [-w/2,w/2]:box((x+dx,front-.13,h/2),(.14,.18,h),metal)
    # Roof railings, plant rooms, ducts, aerials and cable runs.
    box((x,y,h+.25),(w,d,.28),concrete)
    for dx in [-w/2+.15,w/2-.15]:
        for dz in [.35,.94]:g.rod((x+dx,y-d/2,h+dz),(x+dx,y+d/2,h+dz),.025,metal)
        for k in range(int(d)):g.rod((x+dx,y-d/2+k,h+.25),(x+dx,y-d/2+k,h+1),.018,metal,6)
    for i in range(3):
        xx=x-w*.29+i*w*.27
        box((xx,y+.6,h+.85),(w*.19,1.7,1.2),stone)
        for j in range(5):box((xx,y-.264,h+.43+j*.18),(w*.15,.025,.048),metal)
        g.rod((xx+.28,y+.7,h+1.48),(xx+.28,y+.7,h+1.57),.33,metal,16)
        g.rod((xx,y+1.7,h+.6),(xx,y+2.6,h+.6),.19,trim,10)
    g.rod((x-w*.28,y+d*.2,h),(x-w*.28,y+d*.2,h+3),.035,metal,8)
    for z in [h+2.1,h+2.5]:g.rod((x-w*.28-.5,y+d*.2,z),(x-w*.28+.5,y+d*.2,z),.018,metal,6)
    if shop:
        if rounded or shop=='STARBUCKS':sign(shop,x,front-.29,6.05,w-.25,1.35,metal,1.12 if rounded else .98)
        else:sign(shop,x,front-.29,3.13,w-.25,.80,metal,.60)
        box((x,front-.60,3.72),(w+.25,1.30,.13),metal)
        shop_positions.append((x,front-1.05,2.6,w))

def tree(x,y,scale=1):
    height=6.5*scale;radius=2.75*scale
    obstacle(x,y,.52*scale,.52*scale,height+1.9*scale)
    colliders[-1].update(cameraRadius=radius,cameraMinY=height-2.1*scale)
    g.rod((x,y,.2),(x+.07,y,height-.75),.19*scale,bark,10,.09*scale)
    for i in range(9):
        a=i*2.4;rr=(.8+random.random()*.7)*scale
        g.rod((x,y,height-1.8),(x+math.cos(a)*rr,y+math.sin(a)*rr,height+random.uniform(-.5,.4)),.065*scale,bark,6,.018*scale)
    for i in range(800):
        a=random.random()*math.tau;r=radius*random.random()**.5
        px=x+math.cos(a)*r;py=y+math.sin(a)*r;pz=height+random.uniform(-1.6,1.6)*scale*math.sqrt(max(.15,1-(r/radius)**2))
        angle=random.random()*math.tau;length=random.uniform(.21,.41)*scale;width=length*.55
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

def ground():
    box((0,0,-2.62),(94,94,.5),concrete)
    box((0,0,-.065),(94,18,.08),asphalt)
    for y in [-28,28]:box((0,y,-.065),(18,38,.08),asphalt)
    for sx in [-1,1]:
        for sy in [-1,1]:
            # Pavement around the station stairwell is deliberately open.
            if sx==1 and sy==-1:
                for x,y,w,d in [(12.8,-28,7.6,38),(36.2,-28,21.6,38),(21,-11.2,8.8,4.4),(21,-35.8,8.8,22.4)]:box((x,y,-.015),(w,d,.20),sidewalk)
            else:box((sx*28,sy*28,-.015),(38,38,.20),sidewalk)
            box((sx*9.15,sy*28,.03),(.26,38,.24),stone)
            box((sx*28,sy*9.15,.03),(38,.26,.24),stone)
            box((sx*10.2,sy*28,.10),(.24,38,.015),yellow)
            box((sx*28,sy*10.2,.10),(38,.24,.015),yellow)
            for k in range(10,47):
                box((sx*28,sy*k,.091),(38,.018,.008),concrete)
                box((sx*k,sy*28,.092),(.018,38,.008),concrete)
    # Four separated crossings and one diagonal; no overlapping zebra grids.
    for i in range(-7,8):
        for y in [-9.3,9.3]:box((i*.89,y,.009),(.44,2.65,.01),paint)
        for x in [-9.3,9.3]:box((x,i*.89,.009),(2.65,.44,.01),paint)
    for i in range(-9,10):
        p=i*.63;box((p,p,.011),(.45,2.6,.01),paint,math.pi/4)
    for i in range(15,47,5):
        for s in [-1,1]:box((s*2.2,s*i,.007),(.10,2,.008),paint);box((s*i,s*2.2,.007),(2,.10,.008),paint)
    for s in [-1,1]:
        box((0,s*13,.009),(7,.18,.01),paint)
        box((s*13,0,.009),(.18,7,.01),paint)

def station():
    x,y=21,-18
    for i in range(13):box((x,-21+i*.50,-.05-i*.16),(7.8,.51,.18),stone)
    for xx in [16.8,25.2]:
        box((xx,y,-.2),(.32,6.3,3.7),stone)
        g.rod((xx,-21.1,.9),(xx,-15.3,.9),.05,trim)
        g.rod((xx,-21,0),(xx,-21,3.4),.10,metal,8)
    box((x,y,3.49),(9.1,6.6,.20),metal)
    sign('JR   渋谷駅',x,-21.35,2.84,8.9,1.12,green,.82,japanese=True)
    g.text('Shibuya Station',(x,-21.51,2.43),.28,white,font=font)
    obstacle(x,-18,8.9,6.6,3.6)

def streets():
    for x,y,s in [(-11.4,15,.9),(-11.6,25,1),(-11.5,37,.9),(11.5,16,.95),(11.6,31,1.1),(11.8,43,1),(-11.5,-15,.95),(-11.6,-29,1.1),(11.5,-13,1.0),(11.7,-32,1.1),(-25,-11.5,.95),(-36,-11.5,1),(33,-11.4,1),(41,11.5,.9),(-31,10.7,.85)]:tree(x,y,s)
    for sx in [-1,1]:
        for sy in [-1,1]:
            signal(sx*10.1,sy*10.1)
            for y in [18,29,40]:lamp_post(sx*9.6,sy*y)
            for y in range(14,45,4):
                g.rod((sx*9.6,sy*y,.1),(sx*9.6,sy*y,.75),.068,metal)
                if y<41:g.rod((sx*9.6,sy*y,.62),(sx*9.6,sy*(y+4),.62),.026,metal)
    shelter(-19,-11.3);bench(-31,-12.2);bench(32,-12)
    for x in [-30,-28.5,-27]:
        box((x,11.65,1.06),(1.25,.74,2.05),red)
        g.panel((x,11.27,1.3),1.02,1.03,warm[2])
        for j in range(3):
            for k in range(4):box((x-.34+k*.22,11.22,1+j*.27),(.11,.025,.15),books[(k+j)%4])
        box((x,11.24,.44),(.63,.027,.19),metal)
    for x,y in [(-12,-11),(13,12),(-33,10.4),(34,-12)]:
        box((x,y,.7),(.63,.62,1.3),metal);box((x,y-.32,1.12),(.46,.04,.20),black)
        sign('MAP',x+.68,y,1.49,.67,1.12,blue,.26)

def city():
    ground()
    building(20,23,19,22,29,'TSUTAYA',True)
    building(37,19.5,12,14,18,'STARBUCKS')
    building(-24,22,14,20,23,'BIG ECHO')
    building(-38,22,10,18,20,'BOOKS & COFFEE')
    building(-12.8,36,9,12,24,'SHIBUYA 109')
    # The 109 landmark is a cylindrical tower, with horizontal rings and a neon crown.
    g.rod((-13.2,34,5),(-13.2,34,32.3),4.2,stone,48)
    for z in np.arange(7,33,2.5):g.rod((-13.2,34,float(z)),(-13.2,34,float(z)+.055),4.25,trim,48)
    g.text('SHIBUYA',(-13.2,29.72,30.2),1.04,pink,font=font)
    g.text('109',(-13.2,29.70,27.95),3.2,pink,font=font)
    building(-1.0,31,7.6,9,26,'TOKYO RECORDS')
    building(9.0,39,8.2,13,27,'H&M')
    building(-28,43,15,12,29)
    building(35,40,17,16,30)
    building(-40,-33,10,17,13,'SHIBUYA  /  MUSIC')
    building(41,-37,10,14,12,'TOKYO MARKET')
    for x in [-40,-20,0,20,40]:building(x,53,13,8,random.randint(17,28))
    anime=artwork('Concept anime billboard',[(174,188),(367,121),(370,317),(185,366)],768,768)
    cat=artwork('Concept cat billboard',[(689,241),(796,232),(797,302),(690,308)],512,384)
    cityposter=artwork('Concept brighter tomorrow',[(847,163),(1030,201),(1032,351),(848,310)],768,768)
    screen(-24,11.71,16.5,12.9,9.3,anime)
    sign('カラオケ',-24,11.50,10.15,12.9,1.44,red,1.05,japanese=True)
    sign('BIG ECHO',-24,11.50,8.55,12.9,1.53,red,1.28)
    screen(18.7,11.63,19.9,16,10.1,cityposter)
    sign('SHIBUYA PEOPLE CULTURE',19.0,11.49,26.2,16.5,.9,metal,.57)
    screen(-1,26.28,17.4,6.9,4.4,cat)
    sign('DHC',-1,26.1,20.36,7,1.35,blue,1.07)
    sign('サロンパス',-1,26.1,23.07,7,2.75,green,1.16,japanese=True)
    sign('Hisamitsu',-1,26.1,25.34,7,1.28,blue,.90)
    sign('DAM',-1,26.12,12.85,7,3.95,metal,1.48)
    sign('UNIQLO',-13,29.18,20.8,7.6,2.45,red,1.10)
    sign('H&M',9,32.35,23.4,7.7,4.7,cream,2)
    for x,y,z,body,mat in [(-31.25,11.38,10.5,'も\nっ\nと\n好\nき\nな\n渋\n谷\nを',blue),(-16.6,11.45,12,'カ\nラ\nオ\nケ',red),(9.91,11.41,11.3,'T\nS\nU\nT\nA\nY\nA',blue),(30.21,12.12,12,'渋\n谷\n書\n店',pink),(-5.2,26.05,17.3,'も\nん\nじ\nゃ',cream),(-37,12.61,9,'珈\n琲',red)]:
        sign(body,x,y,z,1.25,10.5,mat,.80,japanese=True)
    for x,y,z,body,mt in [(-40.5,12.68,11,'音\n楽\n館',pink),(-34.5,12.68,15,'映\n画',blue),(-15.1,15,6.2,'牛\nか\nつ',red),(-6.1,28,8,'東\n京\n食\n堂',lamp),(3.0,26.13,11,'レ\nコ\nー\nド',blue),(6.0,32.2,16,'フ\nァ\nッ\nシ\nョ\nン',red),(32,12.25,8,'本\nと\n珈\n琲',green),(43.3,12.25,11,'渋\n谷\n散\n歩',blue)]:
        sign(body,x,y,z,.86,6,mt,.60,japanese=True)
    # Small secondary signs and lanterns make the ground-level rhythm less uniform.
    for x,y in [(-21,11.2),(-34,12.6),(33,12.1),(40,12.1)]:
        sign('OPEN  /  COFFEE',x,y,4.68,3.8,.65,green,.32)
        for dx in [-1.1,0,1.1]:
            g.rod((x+dx,y-.5,3.65),(x+dx,y-.5,4.17),.18,lamp,12)
            box((x+dx,y-.5,4.18),(.25,.25,.08),metal)
    station();streets()

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
    if 'Glazing' in o.name or 'Crosswalk' in o.name:o.visible_shadow=False
setup_lights()
g.export(ROOT/'public/models/crossing.glb',objects)
metadata={'id':'crossing','name':'Shibuya Crossing','spawn':[0,0,13],'bounds':[-45,45,-45,45],'colliders':colliders,'artRevision':3}
life_path=ROOT/'public/models/crossing-life.json'
if life_path.exists():
    for v in json.loads(life_path.read_text())['vehicles']:
        w,d,h=(2.45,7.3,3.2) if v['model']=='citybus' else (1.92,4.7,1.9)
        co,si=abs(math.cos(v['yaw'])),abs(math.sin(v['yaw']))
        colliders.append({'x':v['x'],'z':v['z'],'halfX':(w*co+d*si)/2,'halfZ':(w*si+d*co)/2,'height':h,'kind':'traffic'})
(ROOT/'public/models/crossing.json').write_text(json.dumps(metadata,indent=2),encoding='utf8')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/crossing.blend'),compress=True)
s=bpy.context.scene;s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'public/renders/crossing.png')
try:
    prefs=bpy.context.preferences.addons['cycles'].preferences;prefs.compute_device_type='OPTIX';prefs.get_devices()
    for d in prefs.devices:d.use=d.type=='OPTIX'
    s.cycles.device='GPU'
except Exception:pass
bpy.ops.render.render(write_still=True)
print('CONCEPT_SCENE_COMPLETE',len(objects),'objects',sum(len(o.data.polygons) for o in objects),'faces',flush=True)
