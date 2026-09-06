"""Cycles reviews from the actual game assets, including a matching gameplay camera."""
import bpy,sys,math
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from blender_lighting import apply_preset
from bake_assets import cycles

for name in ['character','crossing','park']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender'/f'{name}.blend'))
    s=bpy.context.scene;cycles(s);s.cycles.samples=64;apply_preset('evening')
    s.render.image_settings.file_format='PNG';s.render.filepath=str(ROOT/'public/renders'/f'{name}.png')
    bpy.ops.render.render(write_still=True)
    if name=='character':
        s.render.image_settings.file_format='WEBP';s.render.image_settings.quality=86
        bpy.data.images['Render Result'].save_render(str(ROOT/'public/renders/character.webp'),scene=s)
    if name!='crossing':continue
    with bpy.data.libraries.load(str(ROOT/'assets/blender/character.blend'),link=False) as (source,destination):
        destination.objects=[n for n in source.objects if n not in ['Studio ground','Camera','Evening sun','Sky bounce']]
    for o in destination.objects:
        if o:s.collection.objects.link(o)
    character=bpy.data.objects.get('Character');character.location=(0,-10,0);character.rotation_euler[2]=math.pi
    cam=s.camera;cam.data.sensor_fit='VERTICAL';cam.data.sensor_height=32;cam.data.lens=32/(2*math.tan(math.radians(55)/2))
    cam.location=(math.sin(.22)*math.cos(.24)*8.8,-10-math.cos(.22)*math.cos(.24)*8.8,1.35+math.sin(.24)*8.8)
    cam.rotation_euler=(Vector((0,-10,2.35))-cam.location).to_track_quat('-Z','Y').to_euler()
    s.render.resolution_x=1280;s.render.resolution_y=800
    for phase in ['evening','night']:
        apply_preset(phase);s.render.filepath=str(ROOT/'public/renders'/f'crossing-{phase}-cycles.png')
        bpy.ops.render.render(write_still=True)
    print('CYCLES_REVIEW_COMPLETE',name,flush=True)
