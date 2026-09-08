"""Actual Cycles AO for detail + independent UV1 shop irradiance for walkways."""
import bpy, sys, json, time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bake_assets import cycles, select, occlusion, irradiance
import scene_geometry as g
start=time.time()
layout=json.loads((ROOT/'lib/game/dotonbori-layout.json').read_text())
atlas_extent=layout['promenadeEnd']+2
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/dotonbori.blend'))
s=bpy.context.scene;cycles(s);s.cycles.samples=24
# Store unit-strength practical illumination; runtime scales it once per phase.
for o in s.objects:
    if o.type=='LIGHT' and o.get('baked_shop'):o.data.energy=o['base_power']
for m in bpy.data.materials:
    if m.use_nodes and 'base_emission' in m:m.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=m['base_emission']
objects=[o for o in s.objects if o.type=='MESH']
ground=[o for o in objects if o.name in ['Dotonbori promenade paving','Ebisubashi deck','Canal footbridges']]
for o in ground:
    m=o.data.materials[0].copy();m.name=o.name+' baked surface';o.data.materials[0]=m
detail=[o for o in objects if o not in ground and not o.data.materials[0].get('water_surface') and o.data.materials[0].get('base_emission',0)==0]
saved=[];report={'asset':'dotonbori','engine':'CYCLES','samples':24,'vertexBakes':[]}
for o in detail:
    attrs=o.data.color_attributes
    attr=attrs.new(name='BakedLocalShade',type='FLOAT_COLOR',domain='CORNER')
    attrs.active_color_index=list(attrs).index(attr);attrs.render_color_index=attrs.active_color_index
for m in {o.data.materials[0] for o in detail}:
    nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes['Principled BSDF'];out=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
    saved.append((m,out.inputs['Surface'].links[0].from_socket))
    ao=nodes.new('ShaderNodeAmbientOcclusion');ao.name='Bake local AO';ao.samples=32;ao.inputs['Distance'].default_value=1.0
    ramp=nodes.new('ShaderNodeValToRGB');ramp.name='Bake tint'
    base=list(p.inputs['Base Color'].default_value);m['original_base_color']=base
    for i,k in [(0,.65),(1,1)]:ramp.color_ramp.elements[i].color=tuple(c*k for c in base[:3])+(1,)
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
    if not values or min(values)<.001:raise RuntimeError('Invalid Cycles vertex bake '+o.name)
    report['vertexBakes'].append({'mesh':o.name,'corners':len(values),'minimum':min(values),'maximum':max(values)})
print('DOTONBORI_DETAIL_BAKED',len(detail),flush=True)
for o in ground:
    uv=o.data.uv_layers.new(name='BakeUV');o.data.uv_layers.active=uv
    for p in o.data.polygons:
        for li in p.loop_indices:
            v=o.matrix_world@o.data.vertices[o.data.loops[li].vertex_index].co
            # Walkable perimeter ramps can be steeper than the former .9
            # normal cutoff; excluding them leaves black AO strips at runtime.
            uv.data[li].uv=((v.x+21)/42,(v.y+atlas_extent)/(atlas_extent*2)) if p.normal.z>.65 else (-1,-1)
    o.data.uv_layers[0].active_render=True
mats=list({o.data.materials[0] for o in ground})
report.update(occlusion(ground,mats,'dotonbori',4096))
report.update(irradiance(ground,mats,'dotonbori',4096))
report['walkableExtent']=layout['promenadeEnd']
for o in ground:o.data.uv_layers.active_index=0
for m in bpy.data.materials:
    if m.use_nodes and m.node_tree.nodes.get('Cycles bake target'):m.node_tree.nodes.remove(m.node_tree.nodes['Cycles bake target'])
from dotonbori_water import bake_water_normal
report.update(bake_water_normal(ROOT))
g.compact_baked_colors(objects)
s['baking_pipeline']='Cycles vertex AO, 4096px UV1 ambient occlusion and independent shop irradiance across seven bridges; sunlight remains dynamic'
roots=[o for o in s.objects if o.type=='EMPTY']
g.export_atomic(ROOT/'public/models/dotonbori.glb',objects+roots)
from blender_lighting import apply_preset
apply_preset('evening')
bpy.data.orphans_purge(do_recursive=True)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath,compress=True)
report['seconds']=round(time.time()-start,1)
(ROOT/'assets/bakes/dotonbori.json').write_text(json.dumps(report,indent=2))
print('DOTONBORI_BAKE_COMPLETE',report['seconds'],flush=True)
