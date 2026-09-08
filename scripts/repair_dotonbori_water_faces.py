"""Repair existing baked scenes without regenerating their lighting or geometry.

New scenes use the same dotonbori_water_geometry authoring function. Only the
water mesh is replaced; every baked material, building and navigation mesh stays.
"""
import bpy, json, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import scene_geometry as g
from dotonbori_water_geometry import build
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/dotonbori.blend'))
sources=[o for o in bpy.context.scene.objects if o.type=='MESH' and any(m and m.get('water_surface') for m in o.data.materials)]
if len(sources)!=1:raise RuntimeError('Expected one authored canal water mesh')
source=sources[0];old=source.data
g.B.clear();g.TEXT.clear()
build(g,source.data.materials[0],json.loads((ROOT/'lib/game/dotonbori-layout.json').read_text()))
replacement=g.flush()[0]
source.data=replacement.data
bpy.data.objects.remove(replacement,do_unlink=True)
if old.users==0:bpy.data.meshes.remove(old)
if any(p.normal.z<.9 for p in source.data.polygons):raise RuntimeError('Water faces must face upward')
objects=[o for o in bpy.context.scene.objects if o.type in ['MESH','EMPTY']]
g.export_atomic(ROOT/'public/models/dotonbori.glb',objects)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
print('DOTONBORI_WATER_FACES_REPAIRED',len(source.data.polygons),flush=True)
