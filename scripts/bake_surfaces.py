"""Bake Blender procedural surface color into the existing shared UV1 layout.
Run after bake_assets.py. Keeps PBR lighting dynamic and avoids browser noise shaders.
"""
import bpy, sys, json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'scripts'))
from bake_assets import cycles, target, image, select, save_texture
from blender_lighting import apply_preset

def main(name):
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender'/f'{name}.blend'))
    s=bpy.context.scene;cycles(s)
    objects=[o for o in s.objects if o.type=='MESH' and o.name!='Studio ground']
    # Tiny embroidery remains a simple PBR material; text has no baked UV layout.
    for o in s.objects:
        if o.type=='FONT':
            m=bpy.data.materials.new('Embroidery thread');m.use_nodes=True
            bsdf=m.node_tree.nodes.get('Principled BSDF');bsdf.inputs['Base Color'].default_value=(.059,.061,.067,1);bsdf.inputs['Roughness'].default_value=.9
            o.data.materials.clear();o.data.materials.append(m)
    materials=list({m for o in objects for m in o.data.materials if m and m.node_tree.nodes.get('Baked ambient occlusion')})
    size=s.get('bake_resolution',1024)
    im=image(name+' surface color',size,True);saved=[]
    for m in materials:
        nodes=m.node_tree.nodes;links=m.node_tree.links
        bsdf=nodes.get('Principled BSDF');out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
        emit=nodes.new('ShaderNodeEmission');emit.name='Surface bake emission'
        saved.append((m,out.inputs['Surface'].links[0].from_socket))
        if 'original_base_color' not in m:m['original_base_color']=list(bsdf.inputs['Base Color'].default_value)
        base=list(m['original_base_color'])
        # Keep concept billboard artwork in its original higher-density UV0 texture.
        if m.name.startswith('Concept -'):
            original=bsdf.inputs['Base Color'].links[0].from_socket if bsdf.inputs['Base Color'].links else bsdf.inputs['Emission Color'].links[0].from_socket
            links.new(original,bsdf.inputs['Base Color'])
            links.new(original,emit.inputs['Color'])
        else:
            if m.name=='Asphalt':base=[.036,.043,.062,1];bsdf.inputs['Roughness'].default_value=.48
            if m.name=='Crosswalk ivory paint':base=[.66,.65,.60,1]
            coord=nodes.new('ShaderNodeNewGeometry');coord.name='Surface world coordinates'
            noise=nodes.new('ShaderNodeTexNoise');noise.name='Baked surface grain'
            noise.inputs['Scale'].default_value=95 if name=='character' else 7
            noise.inputs['Detail'].default_value=2;noise.inputs['Roughness'].default_value=.7
            links.new(coord.outputs['Position'],noise.inputs['Vector'])
            ramp=nodes.new('ShaderNodeValToRGB');ramp.name='Surface grain colors'
            variation=.07 if name=='character' else .20
            if 'Leaves' in m.name:variation=.25
            ramp.color_ramp.elements[0].position=.12;ramp.color_ramp.elements[1].position=.88
            ramp.color_ramp.elements[0].color=tuple(c*(1-variation) for c in base[:3])+(1,)
            ramp.color_ramp.elements[1].color=tuple(min(1,c*(1+variation)) for c in base[:3])+(1,)
            links.new(noise.outputs['Fac'],ramp.inputs[0]);links.new(ramp.outputs['Color'],emit.inputs['Color'])
        links.new(emit.outputs[0],out.inputs['Surface']);target(m,im)
    select(objects);bpy.ops.object.bake(type='EMIT',uv_layer='BakeUV')
    path=ROOT/'assets/bakes'/f'{name}-color.png';path.parent.mkdir(exist_ok=True);save_texture(im,path)
    baked=bpy.data.images.load(str(path),check_existing=False);baked.pack()
    for m,socket in saved:
        nodes=m.node_tree.nodes;links=m.node_tree.links
        links.new(socket,next(n for n in nodes if n.type=='OUTPUT_MATERIAL').inputs['Surface'])
        nodes.remove(nodes['Surface bake emission'])
        if m.name.startswith('Concept -'):continue
        tex=nodes.get('Baked surface color') or nodes.new('ShaderNodeTexImage');tex.name='Baked surface color';tex.image=baked
        links.new(nodes['Baked UV'].outputs['UV'],tex.inputs['Vector'])
        links.new(tex.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
        nodes['Principled BSDF'].inputs['Base Color'].default_value=(1,1,1,1)
    # WebP makes the new atlases small enough for mobile downloads; PNG masters stay packed in Blender.
    for m in materials:
        if m.get('bakedLightmap'):
            original=ROOT/'assets/bakes'/f'{name}-light.png'
            imlight=bpy.data.images.load(str(original),check_existing=True)
            dest=ROOT/'public/bakes'/f'{name}-light.webp'
            settings=s.render.image_settings
            old=(s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure)
            s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0
            settings.file_format='WEBP';settings.quality=90
            imlight.save_render(str(dest),scene=s)
            s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure=old
            m['bakedLightmap']='/bakes/'+dest.name
    apply_preset('evening')
    select(objects)
    if name=='character':
        for o in s.objects:
            if o.type in ['EMPTY','FONT']:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models'/f'{name}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_extras=True,export_yup=True,export_image_format='WEBP',export_image_quality=88,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=12,export_draco_texcoord_quantization=14)
    s.render.image_settings.file_format='PNG'
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    print('SURFACES_COMPLETE',name,flush=True)

if __name__=='__main__':
    names=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['character','crossing','park']
    for name in names:main(name)
