"""Remove unused bake intermediates from saved Blender source files."""
import bpy,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
import scene_geometry as g
from bake_assets import save_texture
for name in ['crossing','crossing-review']:
    path=ROOT/'assets/blender'/f'{name}.blend';before=path.stat().st_size
    bpy.ops.wm.open_mainfile(filepath=str(path))
    objects=[o for o in bpy.context.scene.objects if o.type=='MESH']
    g.compact_baked_colors(objects)
    # Blender keeps full-resolution PNG masters locally; the editable scene can
    # pack the same compact image representation used by the browser.
    for old in list(bpy.data.images):
        master=old.name in ['crossing-light.png','crossing-ao.png']
        if not master and 'aggregate' not in old.name and not old.name.startswith('Concept '):continue
        light=old.name=='crossing-light.png'
        linear=old.colorspace_settings.name=='Non-Color'
        packed=ROOT/'public/bakes/crossing-light.webp' if light else ROOT/'work'/('packed-'+hashlib.sha1(old.name.encode()).hexdigest()[:12]+'.webp')
        if not light:save_texture(old,packed,linear=linear)
        image=bpy.data.images.load(str(packed),check_existing=False)
        image.colorspace_settings.name='Non-Color' if linear else 'sRGB';image.pack()
        for material in bpy.data.materials:
            if material.use_nodes:
                for node in material.node_tree.nodes:
                    if node.type=='TEX_IMAGE' and node.image==old:node.image=image
        if old.users==0:bpy.data.images.remove(old)
    for i in bpy.data.images:i.use_fake_user=False
    print('UNUSED_IMAGES',name,[(i.name,list(i.size)) for i in bpy.data.images if i.users==0],flush=True)
    bpy.data.orphans_purge(do_recursive=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(path),compress=True)
    if name=='crossing':g.export(ROOT/'public/models/crossing.glb',objects)
    print('COMPACTED',name,before,path.stat().st_size,flush=True)
