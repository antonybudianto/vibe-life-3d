"""Use Cycles vertex bakes for thin props that cannot fit cleanly in a map atlas.
This avoids oversized textures for paint, rails, lettering and small foliage.
"""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bake_assets import cycles, select
coverage=json.loads((ROOT/'work/bake-coverage.json').read_text())
for asset in coverage:
    bad={o['mesh'] for o in asset['objects'] if o['blackAreaFraction']>.08}
    if not bad:continue
    name=asset['asset'];bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender'/f'{name}.blend'))
    scene=bpy.context.scene;cycles(scene);scene.cycles.samples=16
    objects=[o for o in scene.objects if o.name in bad]
    materials=list({m for o in objects for m in o.data.materials})
    saved=[]
    for o in objects:
        attrs=o.data.color_attributes
        attr=attrs.get('BakedLocalShade') or attrs.new(name='BakedLocalShade',type='FLOAT_COLOR',domain='CORNER')
        attrs.active_color_index=list(attrs).index(attr);attrs.render_color_index=attrs.active_color_index
    for m in materials:
        nodes=m.node_tree.nodes;links=m.node_tree.links
        output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL');saved.append((m,output.inputs['Surface'].links[0].from_socket))
        ao=nodes.new('ShaderNodeAmbientOcclusion');ao.name='Vertex bake AO';ao.samples=64;ao.inputs['Distance'].default_value=1.2
        ramp=nodes.new('ShaderNodeValToRGB');ramp.name='Vertex bake tint'
        base=list(m['original_base_color'])
        for index,strength in [(0,.7),(1,1.0)]:ramp.color_ramp.elements[index].color=tuple(c*strength for c in base[:3])+(1,)
        emit=nodes.new('ShaderNodeEmission');emit.name='Vertex bake emit'
        links.new(ao.outputs['AO'],ramp.inputs[0]);links.new(ramp.outputs[0],emit.inputs['Color']);links.new(emit.outputs[0],output.inputs['Surface'])
    select(objects);bpy.ops.object.bake(type='EMIT',target='VERTEX_COLORS')
    white=bpy.data.images.new('Unoccluded UV1 carrier',width=1,height=1,alpha=False)
    white.pixels[:]=[1,1,1,1];white.pack()
    for m,socket in saved:
        nodes=m.node_tree.nodes;links=m.node_tree.links
        links.new(socket,next(n for n in nodes if n.type=='OUTPUT_MATERIAL').inputs['Surface'])
        for label in ['Vertex bake emit','Vertex bake tint','Vertex bake AO','Baked surface color']:
            if nodes.get(label):nodes.remove(nodes[label])
        color=nodes.get('Cycles vertex shading') or nodes.new('ShaderNodeVertexColor');color.name='Cycles vertex shading';color.layer_name='BakedLocalShade'
        links.new(color.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color'])
        nodes['Principled BSDF'].inputs['Base Color'].default_value=(1,1,1,1)
        # Preserve explicit UV1 in glTF for the independently loaded light atlas.
        nodes['Baked ambient occlusion'].image=white
        m['bake_mode']='Cycles color attribute: tinted local AO'
    for o in objects:
        values=[max(c.color[:3]) for c in o.data.color_attributes['BakedLocalShade'].data]
        if not values or min(values)<.001:raise RuntimeError(f'{o.name} has missing vertex bake values')
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
    print('VERTEX_BAKE_COMPLETE',name,len(objects),flush=True)
