"""Use the same Blender assets, crowd placement and camera convention as the game."""
import bpy,sys,json,math
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bake_assets import cycles
from blender_lighting import apply_preset
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/crossing.blend'))
s=bpy.context.scene;cycles(s);s.cycles.samples=80
meta=json.loads((ROOT/'public/models/crossing-life.json').read_text())
def append(name):
    with bpy.data.libraries.load(str(ROOT/'assets/blender'/f'{name}.blend'),link=False) as (a,b):b.objects=[n for n in a.objects if n not in ['Studio ground','Camera','Evening sun','Sky bounce']]
    return [o for o in b.objects if o and o.type in ['MESH','EMPTY','FONT']]
crowd=append('pedestrian')
for i,p in enumerate(meta['people']):
    a,b=p['a'],p['b'];dx=b[0]-a[0];dz=b[1]-a[1];length=math.hypot(dx,dz);phase=p['offset']*2 if length else 0;t=phase if phase<=1 else 2-phase
    yaw=math.atan2(dx,dz)+(math.pi if phase>1 else 0) if length else p['offset']*math.tau
    gait=math.sin(p['offset']*math.pi*8) if length else 0
    root=Matrix.Translation((a[0]+dx*t,-a[1]-dz*t,.1+abs(gait)*.025))@Matrix.Rotation(yaw,4,'Z')@Matrix.Scale(p['scale'],4)
    for source in crowd:
        o=source.copy();o.data=source.data;s.collection.objects.link(o)
        limb=Matrix.Identity(4)
        if source.get('swing'):
            x,z,y=source['pivot'];v=Vector((x,-y,z))
            limb=Matrix.Translation(v)@Matrix.Rotation(gait*.34*source['swing'],4,'X')@Matrix.Translation(-v)
        o.matrix_world=root@limb@source.matrix_world
        if source.data.materials[0].name.startswith('Crowd outfit'):
            mat=source.data.materials[0].copy();o.data=source.data.copy();o.data.materials[0]=mat
            c=p['coat'].lstrip('#');srgb=[int(c[k:k+2],16)/255 for k in [0,2,4]];linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in srgb]
            mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=tuple(v*.78 for v in linear)+(1,)
for name in ['taxi','citybus']:
    parts=append(name)
    for v in meta['vehicles']:
        if v['model']!=name:continue
        transform=Matrix.Translation((v['x'],-v['z'],.02))@Matrix.Rotation(v['yaw'],4,'Z')
        for source in parts:
            o=source.copy();o.data=source.data;s.collection.objects.link(o);o.matrix_world=transform@source.matrix_world
apply_preset('evening')
s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'public/renders/crossing.png')
bpy.ops.render.render(write_still=True)
for o in append('character'):s.collection.objects.link(o)
character=bpy.data.objects.get('Character');character.location=(0,-13,0);character.rotation_euler[2]=math.pi
cam=s.camera;cam.data.type='PERSP';cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=32;cam.data.lens=32/(2*math.tan(math.radians(55)/2))
cam.location=(math.sin(.22)*math.cos(.24)*8.8,-13-math.cos(.22)*math.cos(.24)*8.8,1.35+math.sin(.24)*8.8)
cam.rotation_euler=(Vector((0,-13,2.35))-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=1280;s.render.resolution_y=800
for phase in ['evening','night']:
    apply_preset(phase);s.render.filepath=str(ROOT/'public/renders'/f'crossing-{phase}-cycles.png');bpy.ops.render.render(write_still=True)
apply_preset('evening')
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/crossing-review.blend'),compress=True)
print('CONCEPT_REVIEW_COMPLETE',flush=True)
