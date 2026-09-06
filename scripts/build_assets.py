"""Reproducible Blender source for Shibuya Life. Run with Blender --background --python.
All visible world, character and vehicle geometry is authored here in Blender.
Blender coordinates: Z up, forward -Y. glTF exports Y up, forward +Z.
"""
import bpy, math, random, json, os
from mathutils import Vector
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'public' / 'models'
SOURCE = ROOT / 'assets' / 'blender'
RENDERS = ROOT / 'public' / 'renders'
for p in (OUT, SOURCE, RENDERS): p.mkdir(parents=True, exist_ok=True)
random.seed(109)
M = {}

def reset():
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)

def mat(name, color, rough=.7, metal=0, glow=0):
    if name in M: return M[name]
    m=bpy.data.materials.new(name); m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
    p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
    if glow:
        p.inputs['Emission Color'].default_value=(*color,1); p.inputs['Emission Strength'].default_value=glow
    m.diffuse_color=(*color,1); M[name]=m; return m

def materialize(obj, material, name):
    obj.name=name
    if material: obj.data.materials.append(material)
    return obj

def box(name, pos, size, material, bevel=0):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos); o=bpy.context.object; o.scale=size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel:
        m=o.modifiers.new('Soft edges','BEVEL'); m.width=bevel; m.segments=2
        bpy.ops.object.modifier_apply(modifier=m.name)
        m=o.modifiers.new('Weighted normals','WEIGHTED_NORMAL'); bpy.ops.object.modifier_apply(modifier=m.name)
    return materialize(o,material,name)

def uv(name,pos,size,material,segments=24,rings=12):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments,ring_count=rings,location=pos)
    o=bpy.context.object; o.scale=size; bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for p in o.data.polygons:p.use_smooth=True
    return materialize(o,material,name)

def cylinder(name,pos,radius,depth,material,vertices=20):
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=radius,depth=depth,location=pos)
    o=bpy.context.object
    for p in o.data.polygons:p.use_smooth=len(p.vertices)==4
    return materialize(o,material,name)

def link(name,a,b,r,material,vertices=10):
    d=Vector(b)-Vector(a); o=cylinder(name,(Vector(a)+Vector(b))/2,r,d.length,material,vertices)
    o.rotation_euler=d.to_track_quat('Z','Y').to_euler(); return o

def torus(name,pos,major,minor,material,rotation=(0,0,0)):
    bpy.ops.mesh.primitive_torus_add(major_segments=24,minor_segments=8,location=pos,major_radius=major,minor_radius=minor,rotation=rotation)
    o=bpy.context.object
    for p in o.data.polygons:p.use_smooth=True
    return materialize(o,material,name)

def empty(name,pos=(0,0,0)):
    o=bpy.data.objects.new(name,None); bpy.context.collection.objects.link(o); o.location=pos;return o

def parent_new(before, parent):
    bpy.context.view_layer.update()
    for o in set(bpy.data.objects)-before:
        if o!=parent: o.parent=parent; o.matrix_parent_inverse=parent.matrix_world.inverted()

FONT=None
for path in ['C:/Windows/Fonts/arialbd.ttf','C:/Windows/Fonts/arial.ttf']:
    if Path(path).exists(): FONT=bpy.data.fonts.load(path);break
def text_obj(body,pos,size,material,name='Sign lettering'):
    data=bpy.data.curves.new(name,'FONT');data.body=body;data.align_x='CENTER';data.align_y='CENTER';data.size=size;data.extrude=.002;data.resolution_u=2
    if FONT:data.font=FONT
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(math.pi/2,0,0);data.materials.append(material);return o

skin=mat('Skin peach',(.65,.39,.25),.74)
blush=mat('Warm ears',(.57,.27,.19),.82)
hair=mat('Soft espresso hair',(.025,.019,.017),.8)
black=mat('Charcoal fabric',(.024,.026,.032),.86)
seam=mat('Raised fabric seams',(.059,.061,.067),.84)
hoodie=mat('Warm gray cotton',(.38,.365,.35),.94)
cuff=mat('Ribbed cotton',(.28,.265,.255),.93)
ivory=mat('Warm ivory',(.86,.84,.76),.7)
white=mat('Clean white',(.94,.96,1),.58)
signwhite=mat('Luminous lettering',(.93,.96,1),.6,0,1.4)
iris=mat('Chocolate irises',(.075,.038,.023),.32)
eye=mat('Obsidian eyes',(.008,.006,.005),.18)
pink=mat('Neon sakura',(.94,.16,.48),.46,0,2)
blue=mat('Neon sky',(.08,.44,.87),.4,0,2)
warm=mat('Warm lit windows',(.98,.58,.23),.5,0,.7)
glass=mat('Blue smoked glass',(.045,.073,.10),.24,.5)
metal=mat('Graphite metal',(.07,.082,.09),.4,.6)
silver=mat('Brushed silver',(.38,.43,.48),.34,.7)
stone=mat('Concrete light',(.34,.36,.39),.88)
darkstone=mat('Concrete shadow',(.15,.17,.21),.9)
road=mat('Asphalt',(.085,.095,.13),.78)
paint=mat('Crosswalk ivory paint',(.69,.70,.70),.91)
yellow=mat('Tactile ochre',(.75,.44,.075),.85)
red=mat('Vermilion',(.54,.025,.035),.45,.18)
green=mat('Station green',(.018,.22,.105),.64,0,.3)
bark=mat('Tree bark',(.12,.072,.043),.97)
leaves=[mat('Leaves '+str(i),c,.95) for i,c in enumerate([(.075,.17,.055),(.12,.235,.07),(.20,.28,.09),(.08,.22,.14)])]

def character():
    reset(); root=empty('Character')
    before=set(bpy.data.objects)
    # Compact plush body and rounded hoodie, tucked above baggy trousers.
    uv('Hoodie body',(0,0,1.03),(.31,.22,.39),hoodie)
    box('Ribbed waistband',(0,0,.78),(.49,.35,.10),cuff,.045)
    uv('Hood folded behind neck',(0,.115,1.36),(.295,.19,.14),cuff)
    uv('Hood outer',(0,.14,1.37),(.265,.17,.13),hoodie)
    cylinder('Neck',(0,0,1.45),.12,.22,skin)
    # Head silhouette, cheek and chin mass with oversized eyes.
    head=uv('Head',(0,-.015,1.85),(.445,.365,.465),skin,40,24)
    cheeks=uv('Cheeks',(0,-.04,1.70),(.385,.32,.245),skin,32,16)
    bpy.ops.object.select_all(action='DESELECT');head.select_set(True);cheeks.select_set(True);bpy.context.view_layer.objects.active=head;bpy.ops.object.join()
    rem=head.modifiers.new('Sculpted head union','REMESH');rem.mode='VOXEL';rem.voxel_size=.015;bpy.ops.object.modifier_apply(modifier=rem.name)
    smooth=head.modifiers.new('Soft cheek transition','SMOOTH');smooth.factor=1.1;smooth.iterations=4;bpy.ops.object.modifier_apply(modifier=smooth.name)
    dec=head.modifiers.new('Game ready surface','DECIMATE');dec.ratio=.4;bpy.ops.object.modifier_apply(modifier=dec.name)
    for p in head.data.polygons:p.use_smooth=True
    for s in [-1,1]:
        uv('Ear',(s*.427,-.005,1.79),(.084,.069,.123),skin)
        uv('Ear inner',(s*.448,-.059,1.79),(.042,.018,.066),blush)
        uv('Eye white',(s*.163,-.337,1.88),(.094,.023,.118),ivory)
        uv('Iris',(s*.158,-.357,1.884),(.069,.020,.093),iris)
        uv('Pupil',(s*.158,-.375,1.892),(.048,.012,.075),eye)
        uv('Eye glint',(s*.158-.021,-.388,1.922),(.019,.008,.024),white,16,8)
        uv('Eye glint small',(s*.158+.019,-.388,1.865),(.008,.006,.010),white,12,6)
        eyebrow=uv('Eyebrow',(s*.16,-.324,2.033),(.10,.02,.021),hair);eyebrow.rotation_euler[1]=s*.13
    uv('Button nose',(0,-.368,1.77),(.034,.032,.040),skin)
    uv('Quiet smile',(0,-.354,1.66),(.052,.012,.010),blush,20,8)
    uv('Hair volume',(0,.055,2.00),(.43,.31,.28),hair,32,16)
    uv('Back hair',(0,.16,1.96),(.415,.28,.29),hair,32,16)
    uv('Nape hair',(0,.235,1.83),(.31,.14,.175),hair,24,12)
    for s in [-1,1]:
        uv('Sideburn',(s*.365,-.037,1.925),(.065,.19,.21),hair)
    for x,z,ang in [(-.30,2.00,-.35),(-.14,2.015,-.4),(.08,2.022,.40),(.29,1.99,.45)]:
        o=uv('Swept fringe',(x,-.304,z),(.105,.057,.105),hair);o.rotation_euler[1]=ang
    # Mesh cap crown is a hemisphere, avoiding a second sphere over the face.
    verts=[];faces=[];N=40;R=10
    for j in range(R+1):
        phi=(math.pi/2)*j/R
        for i in range(N):
            th=2*math.pi*i/N
            verts.append((.467*math.sin(phi)*math.cos(th),.39*math.sin(phi)*math.sin(th)+.03,2.085+.34*math.cos(phi)))
    for j in range(R):
        for i in range(N):
            a=j*N+i;b=j*N+(i+1)%N;faces.append((a,b,b+N,a+N))
    me=bpy.data.meshes.new('Six panel cap mesh');me.from_pydata(verts,[],faces);me.update()
    o=bpy.data.objects.new('Black cap crown',me);bpy.context.collection.objects.link(o);me.materials.append(black)
    for p in me.polygons:p.use_smooth=True
    uv('Curved cap brim',(0,-.36,2.09),(.49,.33,.043),black,40,12)
    uv('Cap button',(0,.03,2.425),(.036,.036,.018),seam)
    box('Cap woven badge',(.04,-.351,2.245),(.13,.017,.074),seam,.008)
    text_obj('S',(.04,-.363,2.245),.062,black,'Cap badge embroidery')
    # Backpack with separate pockets, zipper, straps and grab loop.
    box('Backpack main',(0,.274,1.08),(.45,.215,.55),black,.085)
    box('Backpack front pocket',(0,.405,.98),(.34,.07,.22),seam,.036)
    box('Pocket face',(0,.444,.98),(.31,.02,.17),black,.02)
    link('Zipper',( -.15,.46,1.075),(.15,.46,1.075),.007,silver)
    box('Zip pull',(.115,.465,1.048),(.016,.014,.04),silver,.004)
    for s in [-1,1]:
        link('Shoulder strap',(s*.225,.26,1.29),(s*.22,-.187,1.31),.038,black)
        link('Front strap',(s*.22,-.187,1.31),(s*.23,-.19,.91),.034,black)
        box('Strap buckle',(s*.23,-.222,1.01),(.069,.025,.054),metal,.008)
    torus('Backpack grab loop',(0,.265,1.397),.064,.013,black,(math.pi/2,0,0))
    parent_new(before,root)
    # Pivot groups export intact for deterministic walking animation in the game.
    for s,label in [(-1,'L'),(1,'R')]:
        pivot=empty('Arm_'+label,(s*.285,0,1.30));pivot.parent=root
        before=set(bpy.data.objects)
        arm=uv('Sleeve '+label,(s*.355,-.008,1.077),(.126,.13,.276),hoodie);arm.rotation_euler[1]=-s*.13
        uv('Cuff '+label,(s*.389,-.018,.885),(.113,.114,.07),cuff)
        uv('Hand '+label,(s*.39,-.026,.801),(.087,.084,.117),skin)
        uv('Thumb '+label,(s*.324,-.077,.815),(.034,.038,.06),skin)
        parent_new(before,pivot)
        pivot=empty('Leg_'+label,(s*.151,0,.735));pivot.parent=root;before=set(bpy.data.objects)
        uv('Trouser '+label,(s*.151,.003,.455),(.146,.16,.30),black)
        box('Pant cuff '+label,(s*.151,0,.237),(.235,.26,.09),seam,.032)
        box('Sneaker sole '+label,(s*.151,-.079,.079),(.258,.425,.082),ivory,.032)
        box('Sneaker upper '+label,(s*.151,-.058,.145),(.231,.345,.14),black,.051)
        box('Toe cap '+label,(s*.151,-.232,.133),(.217,.079,.095),ivory,.025)
        for y in [-.10,-.14,-.18]:link('Shoelace',(s*.151-.062,y,.207),(s*.151+.062,y,.207),.009,ivory)
        parent_new(before,pivot)
    export('character',merge=False)
    lighting();camera((3.35,-5.6,2.7),(0,0,1.22),58)
    box('Studio ground',(0,0,-.06),(200,200,.10),darkstone)
    save_render('character',840,1000)

def merge_by_material():
    bpy.ops.object.select_all(action='DESELECT')
    for o in list(bpy.context.scene.objects):
        if o.type=='FONT':
            bpy.context.view_layer.objects.active=o;o.select_set(True);bpy.ops.object.convert(target='MESH');o.select_set(False)
    groups={}
    for o in bpy.context.scene.objects:
        if o.type=='MESH':groups.setdefault(o.data.materials[0].name if o.data.materials else 'none',[]).append(o)
    for name,objs in groups.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in objs:o.select_set(True)
        bpy.context.view_layer.objects.active=objs[0]
        if len(objs)>1:bpy.ops.object.join()
        bpy.context.object.name='Batch_'+name
        if name=='Crosswalk ivory paint':bpy.context.object.visible_shadow=False

def export(name,merge=True):
    if merge:merge_by_material()
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.export_scene.gltf(filepath=str(OUT/(name+'.glb')),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_yup=True,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=12)
    print('EXPORTED',name,flush=True)

def lighting():
    scene=bpy.context.scene; scene.render.engine='CYCLES';scene.cycles.samples=32
    scene.cycles.use_denoising=True
    scene.world=bpy.data.worlds.new('Violet evening');scene.world.use_nodes=True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value=(.26,.30,.44,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value=.65
    bpy.ops.object.light_add(type='SUN',location=(-20,-15,30));o=bpy.context.object;o.name='Evening sun';o.data.energy=2.2;o.data.color=(1,.73,.51);o.data.angle=.12;o.rotation_euler=(.60,-.45,-.5)
    bpy.ops.object.light_add(type='AREA',location=(6,-4,8));o=bpy.context.object;o.name='Sky bounce';o.data.energy=450;o.data.color=(.52,.64,1);o.data.shape='DISK';o.data.size=10
    o.rotation_euler=(Vector((0,0,1))-o.location).to_track_quat('-Z','Y').to_euler()
    scene.view_settings.view_transform='AgX'
    import sys
    if str(ROOT/'scripts') not in sys.path:sys.path.insert(0,str(ROOT/'scripts'))
    from blender_lighting import apply_preset
    apply_preset('evening')

def camera(pos,target,lens=45):
    bpy.ops.object.camera_add(location=pos);o=bpy.context.object;o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler();o.data.lens=lens;bpy.context.scene.camera=o

def save_render(name,w=1440,h=900,render=True):
    s=bpy.context.scene;s.render.resolution_x=w;s.render.resolution_y=h;s.render.resolution_percentage=100
    s.render.image_settings.file_format='PNG';s.render.filepath=str(RENDERS/(name+'.png'))
    bpy.ops.wm.save_as_mainfile(filepath=str(SOURCE/(name+'.blend')))
    if render:
        bpy.ops.render.render(write_still=True)
        if name=='character':
            s.render.image_settings.file_format='WEBP';s.render.image_settings.quality=86
            bpy.data.images['Render Result'].save_render(str(RENDERS/'character.webp'),scene=s)
            s.render.image_settings.file_format='PNG'

COL=[]
def obstacle(x,y,w,d,height=45):COL.append({'x':x,'z':-y,'halfX':w/2,'halfZ':d/2,'height':height})

def sign(body,x,y,z,w,h,color,fontsize=None):
    box('Billboard housing',(x,y,z),(w,.24,h),metal,.05)
    box('Billboard face',(x,y-.14,z),(w-.12,.025,h-.12),color)
    text_obj(body,(x,y-.164,z),fontsize or min(w/max(len(line) for line in body.split('\n'))*1.40,h*.5),signwhite)

def concept_texture(name,corners):
    # Unwarp the user's billboard art in Blender. No external art service or models.
    import numpy as np
    source=bpy.data.images.load('C:/Users/USER/Downloads/ChatGPT Image Sep 6, 2026, 10_08_45 PM.png',check_existing=True)
    sw,sh=source.size[:];pixels=np.empty(sw*sh*4,dtype=np.float32);source.pixels.foreach_get(pixels);pixels=pixels.reshape(sh,sw,4)
    w,h=512,640;u,v=np.meshgrid(np.linspace(0,1,w),np.linspace(1,0,h))
    a,b,c,d=[np.array(pt) for pt in corners]
    coords=(1-v[...,None])*((1-u[...,None])*a+u[...,None]*b)+v[...,None]*((1-u[...,None])*d+u[...,None]*c)
    xx=np.clip(coords[...,0].astype(int),0,sw-1);yy=np.clip((sh-1-coords[...,1]).astype(int),0,sh-1)
    out=bpy.data.images.new(name,w,h);out.pixels.foreach_set(pixels[yy,xx].reshape(-1));out.pack()
    m=bpy.data.materials.new(name);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');t=m.node_tree.nodes.new('ShaderNodeTexImage');t.image=out
    m.node_tree.links.new(t.outputs['Color'],p.inputs['Base Color']);m.node_tree.links.new(t.outputs['Color'],p.inputs['Emission Color']);p.inputs['Emission Strength'].default_value=.8;p.inputs['Roughness'].default_value=.65
    return m

def picture_panel(x,y,z,w,h,material):
    box('Screen frame',(x,y,z),(w+.2,.26,h+.2),metal,.04)
    verts=[(x-w/2,y-.145,z-h/2),(x+w/2,y-.145,z-h/2),(x+w/2,y-.145,z+h/2),(x-w/2,y-.145,z+h/2)]
    mesh=bpy.data.meshes.new('Billboard screen');mesh.from_pydata(verts,[],[(0,1,2,3)]);mesh.update();uvs=mesh.uv_layers.new()
    for idx,uvv in enumerate([(0,0),(1,0),(1,1),(0,1)]):uvs.data[idx].uv=uvv
    ob=bpy.data.objects.new('Concept billboard',mesh);bpy.context.collection.objects.link(ob);mesh.materials.append(material)

def building(x,y,w,d,h,facade=stone,shop=None):
    box('Building',(x,y,h/2),(w,d,h),facade,.10);obstacle(x,y,w,d,h)
    box('Roof lip',(x,y,h+.1),(w+.3,d+.3,.3),silver)
    # Window grids on south and side walls. Lit rooms intentionally irregular.
    for zz in [2+i*2.5 for i in range(int((h-2)/2.5))]:
        for xx in range(max(2,int(w/1.7))):
            px=x-w/2+.6+xx*1.7
            if px>x+w/2-.4:continue
            mt=warm if random.random()<.41 else glass
            box('South window',(px,y-d/2-.025,zz),(1.48,.035,2.08),mt)
            box('Window mullion',(px,y-d/2-.06,zz),(.045,.04,2.06),silver)
        for yy in range(max(2,int(d/2))):
            py=y-d/2+.7+yy*1.9
            if py>y+d/2-.4:continue
            for sx in [-1,1]:box('Side window',(x+sx*(w/2+.021),py,zz),(.03,1.65,2.08),warm if random.random()<.32 else glass)
        box('Facade horizontal',(x,y-d/2-.065,zz+1.18),(w,.11,.12),silver)
    for i in range(3):
        box('Rooftop HVAC',(x-w*.28+i*w*.25,y,h+.75),(w*.17,1.45,1.15),darkstone,.07)
        for j in range(4):box('HVAC vent',(x-w*.28+i*w*.25,y-.735,h+.36+j*.21),(w*.13,.025,.055),metal)
    if shop:
        box('Shop window wall',(x,y-d/2-.075,1.55),(w-.4,.04,2.7),warm)
        for xx in range(int(w/1.5)+1):box('Shop mullion',(x-w/2+xx*1.5,y-d/2-.12,1.6),(.10,.13,3.1),metal)
        sign(shop,x,y-d/2-.22,3.6,w,1.0,metal,.65)
        # Window ledges and awning.
        box('Store canopy',(x,y-d/2-.6,4.25),(w+.1,1.2,.17),metal)

def tree(x,y,scale=1):
    obstacle(x,y,.45*scale,.45*scale,5.5*scale)
    COL[-1].update(cameraRadius=2.25*scale,cameraMinY=2.0*scale)
    cylinder('Tree trunk',(x,y,1.7*scale),.14*scale,3.4*scale,bark,10)
    for k in range(5):
        a=k*2.4;xx=x+math.cos(a)*.7*scale;yy=y+math.sin(a)*.7*scale
        link('Branch',(x,y,2*scale),(xx,yy,3.7*scale),.065*scale,bark)
    for k in range(28):
        a=k*2.4;rr=math.sqrt(k/28)*1.55*scale
        p=(x+math.cos(a)*rr,y+math.sin(a)*rr,(3.7+random.uniform(-.35,.5))*scale)
        uv('Leaf cluster',p,(.54*scale,.54*scale,.61*scale),random.choice(leaves),10,6)
    box('Stone planter',(x,y,.22),(1.45*scale,1.45*scale,.44),stone,.07)
    box('Planter soil',(x,y,.45),(1.22*scale,1.22*scale,.035),bark)

def streetlamp(x,y):
    cylinder('Lamp post',(x,y,2.5),.07,5,metal,12)
    cylinder('Lamp foot',(x,y,.28),.16,.55,metal,12)
    link('Lamp arm',(x,y,4.9),(x+.65,y,5.1),.055,metal)
    box('Lamp housing',(x+.65,y,5.04),(.62,.32,.12),metal,.05)
    box('Lamp diffuser',(x+.65,y,4.965),(.48,.26,.025),warm)

def signal(x,y,rot=0):
    before=set(bpy.data.objects);root=empty('Traffic signal',(x,y,0))
    cylinder('Signal pole',(x,y,2.1),.09,4.2,metal,12)
    box('Signal box',(x,y-.1,3.58),(.35,.3,1),metal,.10)
    for i,mt in enumerate([red,yellow,green]):
        uv('Signal lens',(x,y-.267,3.88-i*.29),(.10,.025,.10),mt)
    parent_new(before,root);root.rotation_euler[2]=rot

def crossing():
    reset();COL.clear()
    box('City foundation',(0,0,-.38),(100,100,.65),darkstone)
    box('Road surface',(0,0,-.032),(100,100,.06),road)
    for sx in [-1,1]:
        for sy in [-1,1]:
            box('Pavement',(sx*29,sy*29,.01),(40,40,.12),stone)
            # Paver joints and tactile strips.
            box('Tactile path horizontal',(sx*29,sy*9.8,.08),(39,.28,.025),yellow)
            box('Tactile path vertical',(sx*9.8,sy*29,.08),(.28,39,.025),yellow)
            for k in range(10,49,2):
                box('Paver joint',(sx*29,sy*k,.076),(40,.022,.003),darkstone)
                box('Paver joint',(sx*k,sy*29,.076),(.022,40,.003),darkstone)
    for i in range(-8,9):
        for y in [-7,7]:box('Zebra crossing',(i*.92,y,.007),(.51,4.0,.012),paint)
        for x in [-7,7]:box('Zebra crossing',(x,i*.92,.008),(4.0,.51,.012),paint)
    # Two diagonal scramble stripes.
    for diag in [-1,1]:
        for i in range(-8,9):
            o=box('Diagonal crossing',(i*.73,diag*i*.73,.022+(diag==1)*.008),(.48,3.0,.015),paint);o.rotation_euler[2]=diag*math.pi/4
    for k in range(12,49,5):
        for s in [-1,1]:
            box('Lane dash',(s*2.2,s*k,.006),(.12,2.2,.012),paint)
            box('Lane dash',(s*k,s*2.2,.006),(2.2,.12,.012),paint)
    building(18,20,16,15,27,darkstone,'TSUTAYA')
    sign('GOOD PEOPLE\nGOOD COFFEE\nBETTER DAYS',18,12.22,17.5,14,9,mat('Lavender billboard',(.36,.25,.65),.6,0,1.2),1.12)
    sign('SHIBUYA  /  CULTURE  /  ALWAYS FORWARD',18,12.14,23.5,15,1.4,metal,.47)
    building(33,17,12,10,16,darkstone,'STARBUCKS')
    building(-18,19,11,14,22,darkstone,'SHIBUYA 109')
    cylinder('109 tower',(-18,17,16),5.1,32,stone,48)
    cylinder('109 crown',(-18,17,32.15),5.27,.35,silver,48)
    sign('SHIBUYA\n109',-18,11.82,27.5,8.5,7.5,pink,2.35)
    for z in range(4,24,3):
        torus('109 bands',(-18,17,z),5.11,.028,silver)
    building(-31,16,11,10,21,stone,'BIG ECHO')
    poster=concept_texture('Concept - Good Days anime poster',[(174,188),(367,121),(370,317),(185,366)])
    picture_panel(-31,10.77,13.4,10.2,10,poster)
    building(-11,37,6,13,26,darkstone,'COFFEE')
    sign('UN I\nQ LO',-11,30.25,22,5.2,5.5,red,1.6)
    building(13,37,8,12,31,stone,'BOOKS')
    sign('TOKYO\nFM 80.0',13,30.8,24,7,6,blue,1.6)
    building(-31,31,12,15,29,darkstone)
    building(32,33,12,15,34,darkstone)
    # A layered media tower closes the distant view like the crossing's landmark signs.
    building(-1,34,7,8,23,darkstone,'TOKYO RECORDS')
    cat=concept_texture('Concept - Shibuya cat billboard',[(689,241),(796,232),(797,302),(690,308)])
    picture_panel(-1,29.77,16.5,6.6,4.5,cat)
    sign('DHC',-1,29.67,19.7,6.7,1.4,blue,1.0)
    sign('SHIBUYA\nFM',-1,29.75,22,6.5,3.0,green,1.1)
    sign('MUSIC\nIS LIFE',-1,29.73,10.5,6.5,5.1,pink,1.3)
    # Tall lightboxes, banners and fine architectural trim break up the glass facades.
    for x,y,z,body,mt in [(-23.8,11.7,10,'K\nA\nR\nA\nO\nK\nE',red),(-12.1,11.7,10,'1\n0\n9',pink),(9.75,12.1,12,'T\nS\nU\nT\nA\nY\nA',blue),(26.3,11.8,10,'C\nA\nF\nE',red),(-36.8,10.4,11,'T\nO\nK\nY\nO',blue)]:
        sign(body,x,y,z,1.1,10,mt,.68)
    for x,y,w in [(-31,10.7,10),(-18,11.7,10),(18,12.1,15),(33,11.7,11)]:
        sign('COFFEE   /   MUSIC   /   GOOD COMPANY',x,y,5.1,w,.7,red,.30)
        for offset in [-w*.35,0,w*.35]:
            box('Window sill',(x+offset,y-.12,.45),(1.0,.36,.12),metal)
            cylinder('Cafe planter',(x+offset,y-.33,.65),.18,.32,darkstone,12)
            uv('Cafe plant',(x+offset,y-.33,1),(.25,.23,.35),leaves[1],12,8)
    # Distant city silhouettes avoid an empty horizon at street level.
    for x in [-38,-23,-8,8,24,39]:building(x,52,12,8,random.uniform(13,27),darkstone)
    for sx in [-1,1]:
        for sy in [-1,1]:
            if sy==-1:
                building(sx*22,-23,20,13,14 if sx==1 else 19,darkstone,'SHIBUYA STATION' if sx==1 else 'RECORDS  /  CAFE')
            for k in [14,24,36,45]:
                tree(sx*10.9,sy*k,random.uniform(.80,1.10))
                streetlamp(sx*9.35,sy*(k+3))
            for k in range(13,45,4):
                cylinder('Bollard',(sx*9.15,sy*k,.40),.10,.8,metal,10)
            signal(sx*9.3,sy*9.3)
    sign('JR   SHIBUYA STATION',22,-16.32,5.8,17,1.5,green,.88)
    # street-side vending machines and bike parking.
    for x in [-28,-26.4,-24.8]:
        box('Vending machine',(x,9.6,1.07),(1.2,.8,2.0),red,.06)
        box('Vending display',(x,9.175,1.30),(.93,.035,1.13),warm)
        for j in range(3):
            for k in range(4):cylinder('Drink bottle',(x-.31+k*.20,9.135,.96+j*.28),.047,.13,blue,8)
        box('Vending slot',(x,9.17,.45),(.65,.02,.17),metal)
    export('crossing')
    (OUT/'crossing.json').write_text(json.dumps({'id':'crossing','name':'Shibuya Crossing','spawn':[0,0,10],'bounds':[-47,47,-47,47],'colliders':COL}),encoding='utf8')
    lighting();camera((45,-58,47),(0,8,9),32)
    save_render('crossing',1440,1000,False)

def park():
    reset();COL.clear()
    grass=mat('Mossy park ground',(.115,.195,.091),.97)
    box('Park foundation',(0,0,-.3),(66,66,.55),darkstone)
    box('Park lawn',(0,0,-.012),(66,66,.04),grass)
    box('Stone promenade',(0,0,.016),(6.5,65,.045),stone)
    box('Garden cross path',(0,0,.017),(65,6.5,.045),stone)
    for i in range(-32,33,2):
        box('Path joints',(0,i,.042),(6.5,.04,.005),darkstone)
    for x in [-11,-19,11,19]:
        for y in [-24,-12,3,16,26]:tree(x+random.uniform(-2,2),y,random.uniform(1.1,1.8))
    for y in [-22,-10,4,14]:
        for x in [-4.5,4.5]:
            streetlamp(x,y)
            for k in range(3):box('Bench slat',(x,y+1.8,.52+k*.09),(1.7,.36,.065),bark,.015)
            for sx in [-.62,.62]:box('Bench leg',(x+sx,y+1.8,.24),(.095,.35,.48),metal)
    # Vermilion torii and small shrine beyond it.
    for x in [-3,3]:cylinder('Torii pillar',(x,12,2.4),.23,4.8,red,16)
    box('Torii lintel',(0,12,4.75),(7.8,.47,.35),red,.06)
    box('Torii top',(0,12,5.05),(8.4,.61,.21),black,.08)
    box('Torii crosspiece',(0,12,4.03),(6.5,.27,.24),red)
    box('Shrine stone platform',(0,23,.3),(10,9,.6),stone,.05);obstacle(0,23,10,9)
    box('Shrine timber',(0,23,2.3),(7,6,4),bark)
    for x in [-2.5,0,2.5]:box('Shrine pillars',(x,19.88,2.4),(.22,.24,4.2),red)
    for x in [-1.6,1.6]:box('Shrine sliding doors',(x,19.95,2.2),(2.5,.06,3.1),ivory)
    for x in [-2.7,-1.8,-.9,0,.9,1.8,2.7]:box('Door lattice',(x,19.83,2.2),(.07,.06,3.1),bark)
    for z in [1.2,2.1,3.0]:box('Door lattice',(0,19.82,z),(6,.06,.07),bark)
    for s in [-1,1]:
        o=box('Shrine sloping roof',(s*2.22,23,4.9),(5.3,8.3,.30),black);o.rotation_euler[1]=s*.34
    sign('A LITTLE QUIETER HERE',0,19.72,3.98,5.4,.6,metal,.25)
    export('park')
    (OUT/'park.json').write_text(json.dumps({'id':'park','name':'Yoyogi Garden','spawn':[0,0,11],'bounds':[-30,30,-30,30],'colliders':COL}),encoding='utf8')
    lighting();camera((22,-30,20),(0,9,1),40);save_render('park',1440,900,False)

def car():
    reset();body=mat('Kei warm white paint',(.73,.73,.67),.3,.35)
    box('Kei chassis',(0,0,.52),(1.67,3.15,.61),body,.17)
    box('Kei cabin',(0,.13,1.11),(1.52,1.97,.92),body,.19)
    box('Windshield',(0,-.87,1.26),(1.29,.038,.54),glass,.06)
    box('Rear windshield',(0,1.126,1.28),(1.29,.035,.50),glass,.04)
    for x in [-.773,.773]:
        for y in [-.4,.49]:box('Door window',(x,y,1.27),(.038,.71,.49),glass,.032)
        for y in [-.42,.5]:box('Door handle',(x*1.02,y+.17,.91),(.025,.16,.035),metal,.012)
        box('Wing mirror',(x*1.16,-.64,1.15),(.20,.22,.13),body,.045)
    box('Bumper',(0,-1.57,.43),(1.50,.07,.15),metal,.035)
    box('Grille',(0,-1.584,.70),(.62,.026,.21),metal,.025)
    for x in [-.60,.60]:
        uv('Headlight',(x,-1.57,.79),(.19,.026,.135),warm)
        box('Tail lamp',(x,1.57,.73),(.21,.023,.23),red,.04)
    box('Plate',(0,-1.627,.45),(.37,.025,.17),yellow,.015)
    for x in [-.83,.83]:
        for y in [-.97,1.02]:
            torus('Car tire',(x,y,.37),.25,.096,black,(0,math.pi/2,0))
            o=cylinder('Wheel hub',(x,y,.37),.197,.14,silver,20);o.rotation_euler[1]=math.pi/2
    export('car');lighting();camera((4,-6,3),(0,0,.7),52);save_render('car',900,700,False)

def motorcycle():
    reset()
    for y in [-.83,.85]:
        torus('Bike tire',(0,y,.34),.25,.081,black,(0,math.pi/2,0))
        torus('Bike chrome rim',(0,y,.34),.215,.026,silver,(0,math.pi/2,0))
        for i in range(12):
            a=i*math.pi/6;link('Spoke',(0,y,.34),(0,y+math.cos(a)*.21,.34+math.sin(a)*.21),.008,silver,6)
    for x in [-.11,.11]:
        link('Front fork',(x,-.83,.34),(x,-.58,1.05),.033,silver)
        link('Rear frame',(x,.85,.34),(x,.40,.74),.04,metal)
        link('Frame',(x,-.5,.49),(x,.4,.70),.042,red)
    box('Engine',(0,-.02,.52),(.46,.49,.36),metal,.06)
    for z in [.43,.49,.55,.61]:box('Engine cooling fins',(0,-.03,z),(.5,.51,.022),silver)
    uv('Red fuel tank',(0,-.24,.94),(.27,.40,.19),red)
    box('Saddle',(0,.34,.90),(.44,.80,.17),black,.08)
    link('Handlebar',(-.42,-.59,1.20),(.42,-.59,1.20),.032,silver)
    for x in [-.36,.36]:
        link('Grip',(x,-.56,1.2),(x,-.34,1.23),.043,black)
        link('Mirror stalk',(x,-.59,1.22),(x,-.62,1.48),.012,silver)
        uv('Mirror',(x,-.62,1.5),(.08,.025,.055),silver)
    uv('Round headlight',(0,-.77,1.02),(.16,.06,.16),warm)
    link('Chrome exhaust',(.27,-.1,.40),(.27,.9,.37),.066,silver)
    uv('Tail light',(0,.82,.87),(.10,.04,.06),red)
    export('motorcycle');lighting();camera((3,-5,2.3),(0,0,.6),55);save_render('motorcycle',900,700,False)

if __name__=='__main__':
    import sys
    targets=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['character','crossing','park','car','motorcycle']
    for target in targets: globals()[target]()
    print('ALL ASSETS COMPLETE',flush=True)
