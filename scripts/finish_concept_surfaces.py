"""Update the packed street textures without repeating the completed light bake."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from surface_textures import add_street_grain
from blender_lighting import apply_preset
import scene_geometry as g
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/crossing.blend'))
add_street_grain()
apply_preset('evening')
g.export(ROOT/'public/models/crossing.glb',[o for o in bpy.context.scene.objects if o.type=='MESH'])
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
