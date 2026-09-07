"""Bake Blender cloud sculpts into a tiny reusable transparent panorama."""
import bpy, math, random, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bake_assets import cycles
random.seed(109810)
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;cycles(s);s.cycles.samples=32
m=bpy.data.materials.new('Soft cloud silver');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.86,.88,.94,1);p.inputs['Roughness'].default_value=1
for i in range(26):
    a=i/26*math.tau+random.uniform(-.09,.09);e=random.uniform(.12,.58);distance=random.uniform(95,130)
    center=Vector((math.cos(a)*distance,math.sin(a)*distance,e*distance));parts=[]
    for k in range(random.randint(5,9)):
        x=random.uniform(-13,13);z=random.uniform(-2,4);radius=random.uniform(4,9)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=10,location=center+Vector((-math.sin(a)*x,math.cos(a)*x,z)))
        o=bpy.context.object;o.scale=(radius*1.8,radius*.85,radius*.56);parts.append(o)
    bpy.ops.object.select_all(action='DESELECT')
    for o in parts:o.select_set(True)
    bpy.context.view_layer.objects.active=parts[0];bpy.ops.object.join();o=bpy.context.object
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    mod=o.modifiers.new('Joined cumulus','REMESH');mod.mode='VOXEL';mod.voxel_size=.8;bpy.ops.object.modifier_apply(modifier=mod.name)
    mod=o.modifiers.new('Soft cloud contours','SMOOTH');mod.factor=.9;mod.iterations=5;bpy.ops.object.modifier_apply(modifier=mod.name)
    for face in o.data.polygons:face.use_smooth=True
    o.data.materials.clear();o.data.materials.append(m);o.name='Cloud bank %02d'%i
s.world=bpy.data.worlds.new('Cloud illumination');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[0].default_value=(.69,.76,1,1);s.world.node_tree.nodes['Background'].inputs[1].default_value=.65
bpy.ops.object.light_add(type='SUN',location=(-22,-14,28));bpy.context.object.rotation_euler=(-bpy.context.object.location).to_track_quat('-Z','Y').to_euler();bpy.context.object.data.energy=2;bpy.context.object.data.angle=.4
bpy.ops.object.camera_add(location=(0,0,0),rotation=(math.pi/2,0,0));s.camera=bpy.context.object;s.camera.data.type='PANO';s.camera.data.panorama_type='EQUIRECTANGULAR';s.camera.data.clip_end=500
s.render.resolution_x=2048;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.film_transparent=True
s.view_settings.view_transform='Standard';s.view_settings.look='None';s.view_settings.exposure=-1
s.render.image_settings.file_format='WEBP';s.render.image_settings.color_mode='RGBA';s.render.image_settings.quality=90
(ROOT/'public/textures').mkdir(exist_ok=True)
s.render.filepath=str(ROOT/'public/textures/clouds.webp')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/cloud-sky.blend'),compress=True)
bpy.ops.render.render(write_still=True)
print('CLOUD_SKY_COMPLETE',flush=True)
