"""Resolve coincident painted surfaces in the existing Blender scene and re-export."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector,Matrix
root=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(root/'assets/blender/crossing.blend'))
o=bpy.data.objects.get('Batch_Crosswalk ivory paint')
adj={v.index:set() for v in o.data.vertices}
for edge in o.data.edges:
    a,b=edge.vertices;adj[a].add(b);adj[b].add(a)
seen=set();changed=0
for seed in adj:
    if seed in seen:continue
    stack=[seed];component=[];seen.add(seed)
    while stack:
        i=stack.pop();component.append(i)
        for n in adj[i]:
            if n not in seen:seen.add(n);stack.append(n)
    coords=[o.matrix_world@o.data.vertices[i].co for i in component]
    if not bpy.context.scene.get('paint_orientation_fixed') and len(component)==8 and .025<max(v.z for v in coords)<.06:
        center=sum(coords,Vector())/8
        rotation=Matrix.Rotation(math.pi/2,4,'Z')
        inverse=o.matrix_world.inverted()
        for i,co in zip(component,coords):o.data.vertices[i].co=inverse@(center+rotation@(co-center))
    if len(component)==8 and .029<max(v.z for v in coords)<.031:
        positive=False
        for i in component:
            for n in adj[i]:
                delta=o.matrix_world.to_3x3()@(o.data.vertices[n].co-o.data.vertices[i].co)
                if abs(delta.x)>1 and abs(delta.y)>1 and delta.x*delta.y>0:positive=True
        if positive:
            offset=o.matrix_world.inverted().to_3x3()@Vector((0,0,.008))
            for i in component:o.data.vertices[i].co+=offset
            changed+=1
o.data.update();o.visible_shadow=False;bpy.context.scene['paint_orientation_fixed']=True;print('Separated diagonal paint surfaces:',changed,flush=True)
bpy.ops.object.select_all(action='DESELECT')
for ob in bpy.context.scene.objects:
    if ob.type=='MESH':ob.select_set(True)
bpy.ops.export_scene.gltf(filepath=str(root/'public/models/crossing.glb'),export_format='GLB',use_selection=True,export_apply=True,export_cameras=False,export_lights=False,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=12)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
for name in ['crossing','park']:
    path=root/'public/models'/(name+'.json');data=json.loads(path.read_text())
    for c in data['colliders']:
        if c['halfX']<.5 and c['halfZ']<.5:
            scale=c['halfX']/.225;c.update(cameraRadius=2.25*scale,cameraMinY=2*scale,height=5.5*scale)
    path.write_text(json.dumps(data),encoding='utf8')
renders=root/'work/renders';renders.mkdir(parents=True,exist_ok=True)
bpy.context.scene.render.filepath=str(renders/'crossing.png');bpy.ops.render.render(write_still=True)
