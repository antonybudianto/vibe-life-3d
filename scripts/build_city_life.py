"""Reusable Blender-authored crowd, taxi and city bus for instanced scenery."""
import bpy,sys,math,json,random
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import scene_geometry as g

def reset():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    g.M.clear();g.B.clear();g.TEXT.clear()

def save(name):
    objects=g.flush()
    for o in objects:
        if name in ['taxi','citybus'] and o.data.materials[0].name.endswith(('paint','trim')):
            bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o
            bevel=o.modifiers.new('Soft coachwork edges','BEVEL');bevel.width=.055;bevel.segments=3;bevel.limit_method='ANGLE'
            bpy.ops.object.modifier_apply(modifier=bevel.name)
        if 'Arm' in o.name:o['pivot']=[-.31 if 'Left' in o.name else .31,1.16,0];o['swing']=1 if 'Left' in o.name else -1
        if 'Leg' in o.name:o['pivot']=[-.145 if 'Left' in o.name else .145,.69,0];o['swing']=-1 if 'Left' in o.name else 1
        if name=='pedestrian':o['crowd_part']=o.name
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender'/f'{name}.blend'),compress=True)
    g.export(ROOT/'public/models'/f'{name}.glb',objects)

reset()
skin=g.material('Crowd skin',(.68,.39,.23),.79)
hair=g.material('Crowd hair',(.034,.022,.019),.9)
fabric=g.material('Crowd outfit',(.78,.78,.78),.87)
pants=g.material('Crowd denim',(.035,.045,.068),.9)
bag=g.material('Crowd backpack',(.052,.048,.044),.82)
sole=g.material('Crowd sneaker sole',(.69,.67,.61),.84)
eye=g.material('Crowd eyes',(.005,.004,.006),.25)
white=g.material('Crowd eye white',(.86,.82,.73),.35)
g.sphere((0,0,1.01),(.285,.195,.39),fabric,name='Body')
g.sphere((0,0,1.56),(.39,.32,.41),skin,16,10,name='Head')
for sx in [-1,1]:
    g.sphere((sx*.377,-.015,1.55),(.072,.055,.11),skin,name='Head')
    g.sphere((sx*.143,-.285,1.60),(.096,.034,.115),white,name='Head')
    g.sphere((sx*.15,-.317,1.60),(.063,.022,.09),eye,name='Head')
    g.sphere((sx*.16,-.337,1.63),(.018,.01,.026),white,8,6,name='Head')
    g.sphere((sx*.13,-.285,1.79),(.12,.06,.115),hair,name='Head')
g.sphere((0,.035,1.78),(.401,.32,.225),hair,16,8,name='Head')
g.sphere((0,-.325,1.49),(.045,.035,.05),skin,name='Head')
g.rod((-.045,-.306,1.385),(.045,-.306,1.385),.012,hair,6,name='Head')
g.sphere((0,.202,1.0),(.23,.11,.27),bag,name='Body')
g.sphere((0,.282,.93),(.19,.06,.135),bag,name='Body')
for sx in [-1,1]:
    side='Left' if sx<0 else 'Right'
    g.sphere((sx*.318,0,1.02),(.10,.13,.25),fabric,name=side+'Arm')
    g.sphere((sx*.33,-.018,.80),(.09,.09,.115),skin,name=side+'Arm')
    g.sphere((sx*.145,0,.445),(.12,.135,.29),pants,name=side+'Leg')
    g.sphere((sx*.15,-.065,.12),(.145,.215,.10),sole,name=side+'Leg')
    g.sphere((sx*.15,-.065,.183),(.14,.20,.091),pants,name=side+'Leg')
    g.rod((sx*.20,-.11,.90),(sx*.20,-.075,1.27),.027,bag,6,name='Body')
save('pedestrian')

def vehicle(name,bus=False):
    reset()
    body=g.material(name+' paint',(.48,.55,.55) if bus else (.014,.020,.029),.26,.50)
    metal=g.material(name+' trim',(.23,.27,.29),.23,.8)
    rubber=g.material(name+' tires',(.01,.013,.019),.88)
    glass=g.material(name+' tinted windows',(.025,.062,.084),.19,.55)
    seats=g.material(name+' seats',(.12,.17,.20),.87)
    ivory=g.material(name+' headlights',(.92,.81,.50),.4,0,2)
    red=g.material(name+' tail lights',(.55,.012,.016),.3,0,1.2)
    blue=g.material(name+' blue stripe',(.025,.18,.46),.37,.16)
    ochre=g.material(name+' taxi crown',(.95,.60,.055),.42,0,.6)
    w,l,h=(2.45,7.3,2.95) if bus else (1.92,4.7,1.54)
    g.box((0,0,.61),(w,l,.62),body)
    if bus:
        g.box((0,0,1.68),(w*.98,l,2.16),body)
        for sx in [-1,1]:
            for i in range(6):g.panel((sx*(w/2+.009),-l/2+.83+i*.98,2.0),.86,1.17,glass,sx*math.pi/2)
            g.box((sx*(w/2+.018),0,.87),(.025,l,.30),blue)
        g.panel((0,-l/2-.012,2.02),w*.90,1.22,glass)
        g.box((0,0,2.89),(w*.80,l*.94,.14),body)
        g.box((0,.7,3.07),(1.5,2.3,.26),metal)
        g.text('SHIBUYA  渋谷',(0,-l/2-.03,2.67),.22,ivory,font=bpy.data.fonts.load('C:/Windows/Fonts/YuGothB.ttc'))
    else:
        # Sloped windscreen and roof form a recognizable Tokyo sedan silhouette.
        g.mesh([(-.89,-1.12,.94),(.89,-1.12,.94),(.76,-.68,1.62),(-.76,-.68,1.62),(-.89,1.15,.94),(.89,1.15,.94),(.76,.76,1.62),(-.76,.76,1.62)],[(0,1,2,3),(1,5,6,2),(5,4,7,6),(4,0,3,7),(3,2,6,7)],glass)
        g.box((0,.04,1.64),(1.56,1.53,.075),body)
        for sx in [-1,1]:
            g.rod((sx*.76,-.68,1.62),(sx*.89,-1.12,.94),.045,body)
            g.rod((sx*.76,.1,1.62),(sx*.89,.1,.94),.045,body)
            g.rod((sx*.76,.76,1.62),(sx*.89,1.15,.94),.045,body)
            g.box((sx*.973,0,.83),(.025,2.4,.13),ochre)
            g.box((sx*1.02,-.89,1.09),(.22,.24,.10),body)
        g.box((0,.03,1.79),(.58,.34,.23),ochre)
        g.text('TAXI',(0,-.148,1.79),.14,rubber)
    for sx in [-1,1]:
        for yy in [-l*.30,l*.31]:
            g.rod((sx*(w/2-.13),yy,.40),(sx*(w/2+.10),yy,.40),.40 if bus else .34,rubber,20)
            g.rod((sx*(w/2+.106),yy,.40),(sx*(w/2+.117),yy,.40),.235 if bus else .20,metal,16)
        g.box((sx*w*.32,-l/2-.017,.74),(w*.23,.04,.18),ivory)
        g.box((sx*w*.36,l/2+.018,.74),(.21,.045,.23),red)
    g.box((0,-l/2-.015,.49),(w*.50,.06,.16),metal)
    g.box((0,-l/2-.05,.33),(.41,.035,.20),ivory)
    save(name)
vehicle('taxi');vehicle('citybus',True)

random.seed(109)
people=[]
coats=['#a5aaa1','#29404b','#796151','#bfa875','#464f39','#bbb7af','#41464e','#9c655b']
routes=[([-11,-8.5],[11,-8.5]),([-11,8.5],[11,8.5]),([-8.5,-11],[-8.5,11]),([8.5,-11],[8.5,11]),([-9.2,9.2],[9.2,-9.2])]
for i in range(36):
    a,b=routes[i%5];offset=((i//5)%3-1)*.48
    a=[a[0]+offset,a[1]+offset];b=[b[0]+offset,b[1]+offset]
    people.append({'a':a,'b':b,'offset':random.random(),'speed':random.uniform(.75,1.05),'scale':random.uniform(.86,1.07),'coat':coats[i%8]})
for i in range(38):
    sx=-1 if i%2 else 1;sy=-1 if i%4<2 else 1
    # Waiting pedestrians inhabit the curb and bus-stop apron, clear of shops.
    if i<20:a=[sx*random.uniform(10.8,15.8),sy*random.uniform(10.6,11.15)]
    else:a=[sx*random.uniform(10.7,11.25),sy*random.uniform(14,39)]
    people.append({'a':a,'b':a,'offset':random.random(),'speed':0,'scale':random.uniform(.86,1.06),'coat':coats[i%8]})
data={'people':people,'vehicles':[{'model':'citybus','x':-4.5,'z':-20,'yaw':0},{'model':'taxi','x':-4.5,'z':-13.6,'yaw':0},{'model':'taxi','x':4.4,'z':17,'yaw':math.pi},{'model':'taxi','x':-18,'z':4.4,'yaw':math.pi/2},{'model':'taxi','x':22,'z':-4.4,'yaw':-math.pi/2}]}
(ROOT/'public/models/crossing-life.json').write_text(json.dumps(data,indent=2))
print('CITY_LIFE_COMPLETE',len(people),'pedestrians',flush=True)
