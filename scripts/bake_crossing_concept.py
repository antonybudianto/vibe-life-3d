"""Cycles local shading: vertex colors for detail, planar lightmaps for streets."""
import bpy,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
import scene_geometry as g
from bake_assets import cycles,select,occlusion,irradiance
from surface_textures import add_street_grain
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/crossing.blend'))
s=bpy.context.scene;cycles(s);s.cycles.samples=24
objects=[o for o in s.objects if o.type=='MESH']
ground_names=['Rain-dark asphalt','Pavement stone','Crosswalk ivory paint','Tactile ochre',
              'District asphalt','District paving','District road paint','District ochre markings']
ground=[o for o in objects if o.name in ground_names]
detail=[o for o in objects if o.name not in ground_names and not o.name.startswith(('Glazing','Concept','Lettering')) and o.data.materials[0].get('base_emission',0)==0]
saved=[];report={'asset':'crossing','artRevision':6,'vertexBakes':[]}
for o in detail:
    attrs=o.data.color_attributes
    attr=attrs.get('BakedLocalShade') or attrs.new(name='BakedLocalShade',type='FLOAT_COLOR',domain='CORNER')
    attrs.active_color_index=list(attrs).index(attr);attrs.render_color_index=attrs.active_color_index
for m in {o.data.materials[0] for o in detail}:
    nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes['Principled BSDF'];out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
    saved.append((m,out.inputs['Surface'].links[0].from_socket))
    ao=nodes.new('ShaderNodeAmbientOcclusion');ao.name='Bake local AO';ao.samples=32;ao.inputs['Distance'].default_value=1.0
    ramp=nodes.new('ShaderNodeValToRGB');ramp.name='Bake tint'
    base=list(p.inputs['Base Color'].default_value);m['original_base_color']=base
    for i,k in [(0,.65),(1,1.0)]:ramp.color_ramp.elements[i].color=tuple(c*k for c in base[:3])+(1,)
    emit=nodes.new('ShaderNodeEmission');emit.name='Bake emit'
    links.new(ao.outputs['AO'],ramp.inputs[0]);links.new(ramp.outputs[0],emit.inputs['Color']);links.new(emit.outputs[0],out.inputs['Surface'])
select(detail);bpy.ops.object.bake(type='EMIT',target='VERTEX_COLORS')
for m,socket in saved:
    nodes=m.node_tree.nodes;links=m.node_tree.links
    links.new(socket,next(n for n in nodes if n.type=='OUTPUT_MATERIAL').inputs['Surface'])
    for label in ['Bake local AO','Bake tint','Bake emit']:nodes.remove(nodes[label])
    col=nodes.new('ShaderNodeVertexColor');col.layer_name='BakedLocalShade';col.name='Cycles local shading'
    links.new(col.outputs['Color'],nodes['Principled BSDF'].inputs['Base Color']);nodes['Principled BSDF'].inputs['Base Color'].default_value=(1,1,1,1)
    m['bake_mode']='Cycles color attribute: tinted local AO'
for o in detail:
    values=[max(c.color[:3]) for c in o.data.color_attributes['BakedLocalShade'].data]
    if not values or min(values)<.001:raise RuntimeError('Missing vertex bake '+o.name)
    report['vertexBakes'].append({'mesh':o.name,'corners':len(values),'minimum':min(values),'maximum':max(values)})
print('DETAIL_BAKE_COMPLETE',len(detail),flush=True)
for o in ground:
    uv=o.data.uv_layers.new(name='BakeUV');o.data.uv_layers.active=uv
    for p in o.data.polygons:
        for li in p.loop_indices:
            v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
            uv.data[li].uv=((v.x+120)/240,(v.y+110)/235) if p.normal.z>.9 and v.z>-.06 else (-1,-1)
    o.data.uv_layers[0].active_render=True
mats=list({o.data.materials[0] for o in ground})
report.update(occlusion(ground,mats,'crossing',4096))
report.update(irradiance(ground,mats,'crossing',4096))
for o in ground:o.data.uv_layers.active_index=0
for m in bpy.data.materials:
    if m.use_nodes and m.node_tree.nodes.get('Cycles bake target'):m.node_tree.nodes.remove(m.node_tree.nodes['Cycles bake target'])
s['baking_pipeline']='Cycles vertex AO for architecture + shared 4096px district AO and shop irradiance'
add_street_grain()
g.compact_baked_colors(objects)
g.export(ROOT/'public/models/crossing.glb',objects)
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
(ROOT/'assets/bakes/crossing.json').write_text(json.dumps(report,indent=2))
print('CONCEPT_BAKE_COMPLETE',flush=True)
