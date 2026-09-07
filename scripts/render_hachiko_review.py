"""Render the new landmark in its actual map position without rebaking the city."""
import bpy,sys,json
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bake_assets import cycles
from blender_lighting import apply_preset
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/crossing.blend'))
s=bpy.context.scene;cycles(s);s.cycles.samples=48
meta=json.loads((ROOT/'public/models/hachiko.json').read_text());x,y,z=meta['position']
with bpy.data.libraries.load(str(ROOT/'assets/blender/hachiko.blend'),link=False) as (a,b):b.objects=a.objects
for o in b.objects:
    if o and o.type in ['MESH','FONT']:
        s.collection.objects.link(o);o.location+=Vector((x,-z,y))
for xx in [-4.6,4.6]:
    bpy.ops.object.light_add(type='POINT',location=(x+xx,-z-1.8,3.2));o=bpy.context.object;o.data.energy=150;o.data.color=(1,.48,.2);o.data.shadow_soft_size=.4;o['baked_shop']=True;o['base_power']=150
cam=s.camera;cam.data.type='PERSP';cam.data.lens=38;cam.location=(-20,-33,8);cam.rotation_euler=(Vector((-20,-20,1.9))-cam.location).to_track_quat('-Z','Y').to_euler()
s.render.resolution_x=1280;s.render.resolution_y=900;s.render.resolution_percentage=100;s.render.image_settings.file_format='PNG'
apply_preset('evening');s.render.filepath=str(ROOT/'work/hachiko-in-crossing.png');bpy.ops.render.render(write_still=True)
cam.data.lens=25;cam.location=(0,-22,3.5);cam.rotation_euler=(Vector((0,0,11))-cam.location).to_track_quat('-Z','Y').to_euler()
apply_preset('day');s.render.filepath=str(ROOT/'work/blue-sky-crossing.png');bpy.ops.render.render(write_still=True)
print('HACHIKO_CONTEXT_REVIEW_COMPLETE',flush=True)
