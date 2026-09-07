"""Editable Blender Hachiko plaza, with a compact shared game export and Cycles AO."""
import bpy, math, random, sys, json
from pathlib import Path
from mathutils import Vector, Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import scene_geometry as g
from bake_assets import cycles, select
from blender_lighting import apply_preset
random.seed(810)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
g.M.clear();g.B.clear();g.TEXT.clear()
bronze=g.material('Hachiko weathered bronze',(.19,.135,.069),.43,.72)
dark=g.material('Bronze carved details',(.055,.044,.028),.48,.65)
edge=g.material('Polished bronze edges',(.30,.215,.115),.39,.72)
stone=g.material('Hachiko granite',(.30,.295,.28),.9)
cap=g.material('Pedestal coping',(.41,.405,.38),.78)
joint=g.material('Stone joints',(.13,.135,.13),.95)
metal=g.material('Plaza charcoal iron',(.027,.036,.035),.48,.7)
wood=g.material('Bench honey oak',(.29,.135,.045),.75)
soil=g.material('Garden soil',(.038,.031,.021),1)
leaf=[g.material('Plaza foliage '+str(i),c,.85) for i,c in enumerate([(.045,.13,.036),(.13,.24,.045),(.032,.088,.042),(.21,.27,.063)])]
flowers=[g.material('Plaza flowers '+str(i),c,.75) for i,c in enumerate([(.65,.43,.10),(.64,.18,.29),(.68,.64,.42)])]
bark=g.material('Plaza bark',(.13,.072,.032),.94)
light=g.material('Plaza lantern glow',(1,.57,.22),.38,emission=3)
font=bpy.data.fonts.load('C:/Windows/Fonts/arialbd.ttf');jp=bpy.data.fonts.load('C:/Windows/Fonts/YuGothB.ttc')

# Seated Akita: upright ears, broad cheeks, projecting muzzle, straight forelegs,
# tucked haunches and a curled tail. Merge the sculpt volumes into one surface.
for pos,size in [((0,.10,2.35),(.44,.36,.65)),((0,-.04,2.69),(.39,.34,.46)),((0,-.09,3.15),(.40,.33,.38)),((0,-.37,3.02),(.245,.28,.17)),((-.36,.22,2.06),(.27,.36,.32)),((.36,.22,2.06),(.27,.36,.32)),((-.22,-.27,2.12),(.13,.145,.47)),((.22,-.27,2.12),(.13,.145,.47)),((-.22,-.37,1.76),(.17,.25,.12)),((.22,-.37,1.76),(.17,.25,.12))]:g.sphere(pos,size,bronze,24,16,name='Hachiko sculpt')
for side in [-1,1]:
    x=side*.25
    g.mesh([(x-.16,-.17,3.36),(x+.16,-.17,3.36),(x+side*.035,-.10,3.75),(x-.12,.08,3.36),(x+.12,.08,3.36),(x+side*.035,.035,3.69)],[(0,1,2),(5,4,3),(0,3,4,1),(1,4,5,2),(2,5,3,0)],bronze,'Hachiko sculpt',True)
tail=[]
for i in range(20):
    a=-1.2+i/19*5.3;tail.append((.45+.20*math.cos(a),.42+.16*math.sin(a),2.14+i/19*.47))
for a,b in zip(tail,tail[1:]):g.rod(a,b,.10,bronze,12,name='Hachiko sculpt')
dog=g.flush();sculpt=dog[0];select([sculpt]);bpy.context.view_layer.objects.active=sculpt
remesh=sculpt.modifiers.new('Sculpt union','REMESH');remesh.mode='VOXEL';remesh.voxel_size=.023;bpy.ops.object.modifier_apply(modifier=remesh.name)
smooth=sculpt.modifiers.new('Soft cast bronze','SMOOTH');smooth.factor=.7;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
dec=sculpt.modifiers.new('Game sculpt reduction','DECIMATE');dec.ratio=.38;bpy.ops.object.modifier_apply(modifier=dec.name)
for p in sculpt.data.polygons:p.use_smooth=True
for side in [-1,1]:
    g.sphere((side*.222,-.374,3.19),(.052,.028,.045),dark,16,10)
    g.sphere((side*.218,-.397,3.198),(.013,.007,.011),edge,10,6)
    x=side*.25;g.mesh([(x-.086,-.179,3.40),(x+.086,-.179,3.40),(x+side*.031,-.114,3.64)],[(0,1,2)],dark)
    for toe in [-.06,.025]:g.rod((side*.22+toe,-.565,1.773),(side*.22+toe,-.48,1.822),.008,dark,6)
g.sphere((0,-.627,3.061),(.115,.054,.070),dark,16,10)
g.rod((0,-.623,3.015),(0,-.574,2.953),.013,dark,8)
for side in [-1,1]:g.rod((0,-.574,2.956),(side*.15,-.518,2.963),.011,dark,8)
for i in range(32):
    a=i/32*math.tau;b=(i+1)/32*math.tau
    g.rod((.345*math.cos(a),-.04+.31*math.sin(a),2.78),(.345*math.cos(b),-.04+.31*math.sin(b),2.78),.032,edge,8)
g.box((0,-.36,2.72),(.12,.04,.13),edge)
dog+=g.flush()
turn=Matrix.Rotation(1.85,4,'Z')
for o in dog:o.data.transform(turn)

# Granite block with inset bronze dedication, stepped cap and masonry joints.
g.box((0,0,.29),(2.08,1.95,.35),joint)
g.box((0,0,.88),(1.58,1.48,1.08),stone)
g.box((0,0,1.455),(1.72,1.62,.11),joint)
g.box((0,0,1.545),(1.91,1.79,.13),cap)
g.box((0,0,1.625),(1.62,1.48,.065),bronze)
for z in [.48,.94]:g.box((0,-.743,z),(1.57,.006,.01),joint)
g.box((0,-.756,1.04),(.55,.045,.66),dark)
g.text('忠犬ハチ公',(0,-.783,1.21),.078,edge,font=jp)
g.text('HACHIKO',(0,-.784,1.04),.085,edge,font=font)
g.text('SHIBUYA · 1934',(0,-.784,.90),.042,edge,font=font)
# Low octagonal garden ring leaves generous space to approach the plaque.
for i in range(8):
    a=i*math.tau/8;r=2.03
    g.box((r*math.cos(a),r*math.sin(a),.28),(.26,1.68,.38),stone,a)
    g.box((r*math.cos(a),r*math.sin(a),.49),(.32,1.72,.07),cap,a)
    for k in range(7):
        b=a+(k-3)*.10;rr=random.uniform(1.4,1.86)
        g.sphere((rr*math.cos(b),rr*math.sin(b),.42),(random.uniform(.15,.25),.18,.21),random.choice(leaf),8,5)
        if k%2==0:g.sphere((rr*math.cos(b),rr*math.sin(b),.62),(.055,.055,.045),flowers[k%3],8,5)

def bench(x,y):
    for sx in [-.78,.78]:
        for yy in [-.22,.24]:g.rod((x+sx,y+yy,.12),(x+sx,y+yy,.58),.045,metal,8)
        g.rod((x+sx,y+.27,.48),(x+sx,y+.36,1.15),.041,metal,8)
    for yy in [-.21,0,.21]:g.box((x,y+yy,.61),(2.03,.18,.075),wood)
    for zz in [.88,1.07]:g.box((x,y+.33,zz),(2.03,.09,.15),wood)
bench(-3.2,1);bench(3.2,1)

def tree(x,y):
    g.box((x,y,.3),(1.5,1.5,.43),stone);g.box((x,y,.53),(1.33,1.33,.045),soil)
    g.rod((x,y,.5),(x+.12,y,4.4),.17,bark,10,r2=.08)
    for i in range(7):
        a=i*2.4;z=2.6+i*.19;g.rod((x+.1,y,z),(x+math.cos(a)*1.25,y+math.sin(a)*1.15,z+1.4),.075,bark,8,r2=.017)
    for i in range(850):
        a=random.uniform(0,math.tau);r=math.sqrt(random.random())*1.85
        z=4.45+random.uniform(-1.2,1.2)*math.sqrt(max(.1,1-(r/1.85)**2))
        center=Vector((x+math.cos(a)*r,y+math.sin(a)*r,z));angle=random.random()*math.tau;length=random.uniform(.21,.35)
        axis=Vector((math.cos(angle)*length,math.sin(angle)*length,random.uniform(-.2,.2)))
        cross=Vector((-math.sin(angle)*length*.55,math.cos(angle)*length*.55,.045))
        verts=[tuple(center-axis),tuple(center-axis*.3+cross),tuple(center+axis*.55+cross*.75),tuple(center+axis),tuple(center+axis*.55-cross*.75),tuple(center-axis*.3-cross),tuple(center+Vector((0,0,.045)))]
        g.mesh(verts,[(0,1,6),(1,2,6),(2,3,6),(3,4,6),(4,5,6),(5,0,6)],random.choice(leaf))
tree(-4.2,3.4);tree(4.2,3.4)
for x in [-4.6,4.6]:
    g.box((x,-1.8,.2),(.36,.36,.28),stone)
    g.rod((x,-1.8,.18),(x,-1.8,3.1),.065,metal,10)
    g.box((x,-1.8,3.23),(.26,.26,.44),light)
    g.box((x,-1.8,2.98),(.4,.4,.085),metal)
    for dx in [-.15,.15]:
        for dy in [-.15,.15]:g.rod((x+dx,-1.8+dy,3),(x+dx,-1.8+dy,3.49),.022,metal,6)
    g.rod((x,-1.8,3.65),(x,-1.8,3.48),.01,metal,8,r2=.29)
# A readable street-facing marker so the landmark is easy to find.
g.box((0,-3.5,.63),(2.8,.15,1.03),stone)
g.text('HACHIKO SQUARE',(0,-3.582,.76),.19,edge,font=font)
g.text('ハチ公前広場',(0,-3.585,.48),.12,edge,font=jp)
objects=dog+g.flush()
for o in objects:
    if o.name in ['Hachiko granite','Pedestal coping','Bench honey oak']:
        select([o]);mod=o.modifiers.new('Soft stone edges','BEVEL');mod.width=.025;mod.segments=2;bpy.ops.object.modifier_apply(modifier=mod.name)

# Cycles writes local contact shade into vertices; dynamic sun remains independent.
s=bpy.context.scene;cycles(s);s.cycles.samples=24
original={}
for m in g.M.values():
    n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');out=n.get('Material Output')
    ao=n.new('ShaderNodeAmbientOcclusion');ao.inputs['Distance'].default_value=.7
    base=p.inputs['Base Color'].default_value[:]
    mix=n.new('ShaderNodeMixRGB');mix.blend_type='MIX';mix.inputs[1].default_value=tuple(c*.65 for c in base[:3])+(1,);mix.inputs[2].default_value=base
    l.new(ao.outputs['AO'],mix.inputs[0]);em=n.new('ShaderNodeEmission');l.new(mix.outputs[0],em.inputs[0]);l.new(em.outputs[0],out.inputs['Surface']);original[m]=(p,out,[ao,mix,em])
for o in objects:
    a=o.data.color_attributes.new(name='BakedLocalShade',type='BYTE_COLOR',domain='CORNER');o.data.color_attributes.active_color_index=0;o.data.color_attributes.render_color_index=0
select(objects);s.render.bake.target='VERTEX_COLORS';bpy.ops.object.bake(type='EMIT')
for m,(p,out,nodes) in original.items():
    for n in nodes:m.node_tree.nodes.remove(n)
    m.node_tree.links.new(p.outputs[0],out.inputs['Surface'])
    v=m.node_tree.nodes.new('ShaderNodeVertexColor');v.layer_name='BakedLocalShade'
    m.node_tree.links.new(v.outputs['Color'],p.inputs['Base Color']);p.inputs['Base Color'].default_value=(1,1,1,1)
    m['bake_mode']='Cycles color attribute local AO'
g.export(ROOT/'public/models/hachiko.glb',objects)
# Export material base colors explicitly; the AO vertex color is multiplied by glTF.
meta={'model':'hachiko','position':[-20,0,20],'colliders':[{'x':-20,'z':20,'halfX':2.2,'halfZ':2.2,'height':3.8},{'x':-23.2,'z':19,'halfX':1.08,'halfZ':.44,'height':1.2},{'x':-16.8,'z':19,'halfX':1.08,'halfZ':.44,'height':1.2},{'x':-24.2,'z':16.6,'halfX':.8,'halfZ':.8,'height':5.5,'cameraRadius':1.7,'cameraMinY':3.5},{'x':-15.8,'z':16.6,'halfX':.8,'halfZ':.8,'height':5.5,'cameraRadius':1.7,'cameraMinY':3.5},{'x':-20,'z':23.5,'halfX':1.45,'halfZ':.13,'height':1.2}]}
(ROOT/'public/models/hachiko.json').write_text(json.dumps(meta,indent=2))
s.world=bpy.data.worlds.new('Shibuya plaza sky');s.world.use_nodes=True
for x in [-4.6,4.6]:
    bpy.ops.object.light_add(type='POINT',location=(x,-1.8,3.2));o=bpy.context.object;o.name='Plaza lantern light';o.data.energy=150;o.data.color=(1,.48,.2);o.data.shadow_soft_size=.4;o['baked_shop']=True;o['base_power']=150
bpy.ops.object.light_add(type='SUN',location=(-22,-14,28));s.camera=None
bpy.ops.object.camera_add(location=(8,-11,7));s.camera=bpy.context.object;s.camera.rotation_euler=(Vector((0,0,1.7))-s.camera.location).to_track_quat('-Z','Y').to_euler();s.camera.data.type='ORTHO';s.camera.data.ortho_scale=12.6
apply_preset('evening');s.cycles.samples=64;s.render.resolution_x=1200;s.render.resolution_y=1000;s.render.resolution_percentage=100
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/hachiko.blend'),compress=True)
s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'work/hachiko-review.png');bpy.ops.render.render(write_still=True)
print('HACHIKO_COMPLETE',flush=True)
