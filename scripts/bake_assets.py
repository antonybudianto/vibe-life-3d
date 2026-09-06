"""Cycles AO + shop irradiance bakes, preserving editable meshes and animation pivots.

blender --background --factory-startup --python-exit-code 1 --python scripts/bake_assets.py -- character crossing park
AO is glTF-native. Shop irradiance uses material extras + a shared UV1 atlas;
the runtime applies its intensity with the shared time-of-day presets.
"""
import bpy, math, sys, json, time
import numpy as np
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/bakes';OUT.mkdir(exist_ok=True)
sys.path.insert(0,str(ROOT/'scripts'))
from blender_lighting import apply_preset

def select(objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.context.view_layer.objects.active=objects[0]

def cycles(scene):
    scene.render.engine='CYCLES';scene.cycles.samples=48
    scene.cycles.use_denoising=True
    prefs=bpy.context.preferences.addons['cycles'].preferences
    try:
        prefs.compute_device_type='OPTIX';prefs.get_devices()
        for d in prefs.devices:d.use=d.type=='OPTIX'
        scene.cycles.device='GPU'
    except Exception:scene.cycles.device='CPU'
    scene.render.bake.margin=3;scene.render.bake.use_clear=True
    scene.render.bake.use_selected_to_active=False

def target(material,image):
    nodes=material.node_tree.nodes
    for n in nodes:n.select=False
    n=nodes.get('Cycles bake target') or nodes.new('ShaderNodeTexImage')
    n.name='Cycles bake target';n.image=image;n.select=True;nodes.active=n
    return n

def image(name,size,color=False):
    old=bpy.data.images.get(name)
    if old:bpy.data.images.remove(old)
    im=bpy.data.images.new(name,width=size,height=size,alpha=False,float_buffer=color)
    im.colorspace_settings.name='Linear Rec.709' if color else 'Non-Color'
    return im

def unwrap(objects):
    # Merged batches retain the first primitive's scale. Apply it before unwrap:
    # otherwise a 100m road can receive fewer pixels than a 10cm lamp fitting.
    select(objects)
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    for o in objects:
        # UV0 remains intact for the concept billboards. All baked data uses UV1.
        if not o.data.uv_layers:o.data.uv_layers.new(name='UVMap')
        uv=o.data.uv_layers.get('BakeUV') or o.data.uv_layers.new(name='BakeUV')
        o.data.uv_layers.active=uv
        o.data.uv_layers[0].active_render=True
    select(objects)
    bpy.ops.object.mode_set(mode='EDIT');bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.uv.smart_project(angle_limit=math.radians(72),island_margin=.0018,area_weight=0,correct_aspect=True,scale_to_bounds=True)
    bpy.ops.object.mode_set(mode='OBJECT')

def save_texture(im,path,linear=False):
    s=bpy.context.scene
    saved=(s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma,s.render.image_settings.file_format,s.render.image_settings.color_mode)
    s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=0;s.view_settings.gamma=1
    if linear:s.view_settings.view_transform='Raw'
    s.render.image_settings.file_format='WEBP' if path.suffix=='.webp' else 'PNG';s.render.image_settings.color_mode='RGB'
    s.render.image_settings.quality=90
    im.save_render(str(path),scene=s)
    s.view_settings.view_transform,s.view_settings.look,s.view_settings.exposure,s.view_settings.gamma,s.render.image_settings.file_format,s.render.image_settings.color_mode=saved

def occlusion(objects,materials,name,size):
    im=image(name+' AO',size)
    saved=[]
    for m in materials:
        nodes=m.node_tree.nodes;links=m.node_tree.links
        output=next(n for n in nodes if n.type=='OUTPUT_MATERIAL')
        saved.append((m,output.inputs['Surface'].links[0].from_socket))
        ao=nodes.new('ShaderNodeAmbientOcclusion');ao.name='Bake ambient occlusion';ao.samples=64
        ao.inputs['Distance'].default_value=.19 if name=='character' else 2.1
        emit=nodes.new('ShaderNodeEmission');emit.name='Bake AO emission'
        links.new(ao.outputs['AO'],emit.inputs['Color']);links.new(emit.outputs[0],output.inputs['Surface'])
        target(m,im)
    select(objects);bpy.ops.object.bake(type='EMIT',uv_layer='BakeUV')
    for m,socket in saved:
        nodes=m.node_tree.nodes;m.node_tree.links.new(socket,next(n for n in nodes if n.type=='OUTPUT_MATERIAL').inputs['Surface'])
        nodes.remove(nodes['Bake AO emission']);nodes.remove(nodes['Bake ambient occlusion'])
    pix=np.asarray(im.pixels[:],dtype=np.float32).reshape(-1,4)
    print('AO_RANGE',name,float(pix[:,:3].min()),float(pix[:,:3].max()),float(pix[:,:3].std()),flush=True)
    if float(pix[:,:3].std())<.03:raise RuntimeError('AO bake is unexpectedly uniform')
    path=OUT/(name+'-ao.png');save_texture(im,path,linear=True)
    baked=bpy.data.images.load(str(path),check_existing=False);baked.colorspace_settings.name='Non-Color';baked.pack()
    group=bpy.data.node_groups.get('glTF Material Output')
    if not group:
        group=bpy.data.node_groups.new('glTF Material Output','ShaderNodeTree')
        group.interface.new_socket(name='Occlusion',in_out='INPUT',socket_type='NodeSocketFloat')
    for m in materials:
        nodes=m.node_tree.nodes;links=m.node_tree.links
        uv=nodes.get('Baked UV') or nodes.new('ShaderNodeUVMap');uv.name='Baked UV';uv.uv_map='BakeUV'
        tex=nodes.get('Baked ambient occlusion') or nodes.new('ShaderNodeTexImage');tex.name='Baked ambient occlusion';tex.image=baked
        links.new(uv.outputs['UV'],tex.inputs['Vector'])
        out=nodes.get('glTF baked shading') or nodes.new('ShaderNodeGroup');out.name='glTF baked shading';out.node_tree=group
        links.new(tex.outputs['Color'],out.inputs['Occlusion'])
    return {'ao':path.name,'resolution':size,'aoStd':float(pix[:,:3].std())}

def shop_lights(scene,name):
    if any(o.get('baked_shop') for o in scene.objects):return
    coords=[(-18,10,3),(18,11.1,3),(33,11,3),(-31,10,3),(-1,29,3),(-13,-11,3),(17,-11,3)] if name=='crossing' else [(-9,-7,2.2),(9,-7,2.2),(0,16,2.2)]
    for i,co in enumerate(coords):
        data=bpy.data.lights.new(f'Shop spill {i}','AREA');data.energy=180 if name=='crossing' else 75
        data.color=(1,.47,.16);data.shape='DISK';data.size=4
        ob=bpy.data.objects.new(data.name,data);scene.collection.objects.link(ob);ob.location=co
        ob.rotation_euler=(Vector((co[0],co[1]-2,0))-ob.location).to_track_quat('-Z','Y').to_euler()
        ob['baked_shop']=True;ob['base_power']=data.energy

def irradiance(objects,materials,name,size):
    s=bpy.context.scene;shop_lights(s,name)
    im=image(name+' shop irradiance',size,True)
    bg=s.world.node_tree.nodes.get('Background');strength=bg.inputs[1].default_value;bg.inputs[1].default_value=0
    lights=[(o,o.hide_render) for o in s.objects if o.type=='LIGHT']
    for o,_ in lights:o.hide_render=not o.get('baked_shop',False)
    for m in materials:target(m,im)
    s.render.bake.use_pass_direct=True;s.render.bake.use_pass_indirect=True;s.render.bake.use_pass_color=False
    select(objects);bpy.ops.object.bake(type='DIFFUSE',uv_layer='BakeUV')
    bg.inputs[1].default_value=strength
    for o,hidden in lights:o.hide_render=hidden
    pix=np.asarray(im.pixels[:],dtype=np.float32).reshape(-1,4)
    # Store irradiance / 4 in sRGB; recover linear radiance in the renderer.
    maximum=float(pix[:,:3].max());pix[:,:3]=np.clip(pix[:,:3]/4,0,1)
    im.pixels.foreach_set(pix.reshape(-1));im.update()
    path=OUT/(name+'-light.png');save_texture(im,path)
    webpath=ROOT/'public/bakes'/(name+'-light.webp');webpath.parent.mkdir(exist_ok=True)
    save_texture(im,webpath)
    loaded=bpy.data.images.load(str(path),check_existing=False);loaded.pack()
    for m in materials:
        m['bakedLightmap']='/bakes/'+webpath.name;m['bakedLightmapScale']=4
        n=m.node_tree.nodes.get('Baked shop irradiance') or m.node_tree.nodes.new('ShaderNodeTexImage')
        n.name='Baked shop irradiance';n.image=loaded
        m.node_tree.links.new(m.node_tree.nodes['Baked UV'].outputs['UV'],n.inputs['Vector'])
    print('LIGHT_RANGE',name,maximum,flush=True)
    return {'lightmap':webpath.name,'lightmapScale':4,'lightmapMaximum':maximum}

def main(name):
    start=time.time();bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender'/f'{name}.blend'))
    scene=bpy.context.scene;cycles(scene);apply_preset('evening')
    objects=[o for o in scene.objects if o.type=='MESH' and o.name!='Studio ground']
    materials=list({m for o in objects for m in o.data.materials if m})
    # The layout is regenerated. Disconnect previous color atlases while baking;
    # irradiance must see the original albedo, not an old UV layout.
    for m in materials:
        if 'original_base_color' in m and not m.name.startswith('Concept -'):
            bsdf=m.node_tree.nodes.get('Principled BSDF')
            for link in list(bsdf.inputs['Base Color'].links):m.node_tree.links.remove(link)
            base=list(m['original_base_color'])
            if m.name=='Asphalt':base=[.036,.043,.062,1]
            bsdf.inputs['Base Color'].default_value=base
    unwrap(objects)
    size=1024 if name in ['character','car','motorcycle'] else 2048
    report=occlusion(objects,materials,name,size)
    if name in ['crossing','park']:report.update(irradiance(objects,materials,name,size))
    # Restore primary UV for normal material editing; baked nodes explicitly use UV1.
    for o in objects:o.data.uv_layers.active_index=0
    select(objects)
    if name=='character':
        for o in scene.objects:
            if o.type in ['EMPTY','FONT']:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(ROOT/'public/models'/f'{name}.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_extras=True,export_yup=True,export_image_format='WEBP',export_image_quality=88,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=12,export_draco_texcoord_quantization=14)
    scene['baking_pipeline']='Cycles local AO UV1 + separately scalable shop irradiance';scene['bake_resolution']=size
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    report.update(asset=name,seconds=round(time.time()-start,1))
    (OUT/(name+'.json')).write_text(json.dumps(report,indent=2))
    print('BAKE_COMPLETE',json.dumps(report),flush=True)

if __name__=='__main__':
    names=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['character','crossing','park']
    for name in names:main(name)
