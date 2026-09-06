"""Keep only delivery textures, preserve simple text materials, compress .blend sources."""
import bpy,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
for name in ['character','crossing','park']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender'/f'{name}.blend'))
    scene=bpy.context.scene
    for o in scene.objects:
        if o.type=='FONT':
            m=bpy.data.materials.new('Embroidery thread');m.use_nodes=True
            bsdf=m.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.059,.061,.067,1);bsdf.inputs['Roughness'].default_value=.9
            o.data.materials.clear();o.data.materials.append(m)
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        nodes=m.node_tree.nodes
        if nodes.get('Cycles bake target'):nodes.remove(nodes['Cycles bake target'])
    for im in list(bpy.data.images):
        if not im.users:bpy.data.images.remove(im)
    if name=='character':
        groups={}
        for o in scene.objects:
            if o.type=='MESH' and o.parent and len(o.data.materials)==1:
                groups.setdefault((o.parent,o.data.materials[0]),[]).append(o)
        for (parent,material),objects in groups.items():
            if len(objects)<2:continue
            bpy.ops.object.select_all(action='DESELECT')
            for o in objects:o.select_set(True)
            bpy.context.view_layer.objects.active=objects[0];bpy.ops.object.join()
            bpy.context.object.name=f'{parent.name} — {material.name}'
    bpy.ops.object.select_all(action='DESELECT')
    for o in scene.objects:
        if o.type in ['MESH','FONT','EMPTY'] and o.name!='Studio ground':o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models'/f'{name}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_extras=True,export_yup=True,export_image_format='WEBP',export_image_quality=88,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=12,export_draco_texcoord_quantization=14)
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
    print('FINALIZED_BAKES',name,flush=True)
