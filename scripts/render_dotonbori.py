"""Render the delivered Blender scene in Cycles, using the shared day/evening presets."""
import bpy,sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bake_assets import cycles
from blender_lighting import apply_preset
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/dotonbori.blend'))
s=bpy.context.scene;cycles(s);s.cycles.samples=40
s.render.resolution_x=1440;s.render.resolution_y=960;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
for phase in ['evening','day']:
    apply_preset(phase)
    s.render.filepath=str(ROOT/'public/renders'/f'dotonbori-{phase}.png')
    bpy.ops.render.render(write_still=True)
apply_preset('evening')
s.camera.location=(5,-70,67);s.camera.data.lens=28
s.camera.rotation_euler=(Vector((0,7,6))-s.camera.location).to_track_quat('-Z','Y').to_euler()
s.render.filepath=str(ROOT/'public/renders/dotonbori-overview.png');bpy.ops.render.render(write_still=True)
