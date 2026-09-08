"""Cycles volume-cloud panorama for Dotonbori, with soft irregular dusk cloud banks."""
import bpy, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
from bake_assets import cycles
bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
s=bpy.context.scene;cycles(s);s.cycles.samples=128;s.cycles.use_adaptive_sampling=False
bpy.ops.mesh.primitive_cube_add(size=1,location=(0,0,65));o=bpy.context.object;o.name='Layered canal cloud bank';o.scale=(560,560,48)
bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
m=bpy.data.materials.new('Procedural volume clouds');m.use_nodes=True;o.data.materials.append(m)
n=m.node_tree.nodes;l=m.node_tree.links;n.clear()
geo=n.new('ShaderNodeNewGeometry')
noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=.023;noise.inputs['Detail'].default_value=5;noise.inputs['Roughness'].default_value=.68
l.new(geo.outputs['Position'],noise.inputs['Vector'])
ramp=n.new('ShaderNodeMapRange');ramp.clamp=True;ramp.inputs['From Min'].default_value=.52;ramp.inputs['From Max'].default_value=.71;ramp.inputs['To Max'].default_value=.055
l.new(noise.outputs['Fac'],ramp.inputs['Value'])
split=n.new('ShaderNodeSeparateXYZ');l.new(geo.outputs['Position'],split.inputs[0])
sub=n.new('ShaderNodeMath');sub.operation='SUBTRACT';sub.inputs[1].default_value=65;l.new(split.outputs['Z'],sub.inputs[0])
absolute=n.new('ShaderNodeMath');absolute.operation='ABSOLUTE';l.new(sub.outputs[0],absolute.inputs[0])
fade=n.new('ShaderNodeMapRange');fade.clamp=True;fade.inputs['From Min'].default_value=8;fade.inputs['From Max'].default_value=24;fade.inputs['To Min'].default_value=1;fade.inputs['To Max'].default_value=0;l.new(absolute.outputs[0],fade.inputs[0])
mult=n.new('ShaderNodeMath');mult.operation='MULTIPLY';l.new(ramp.outputs[0],mult.inputs[0]);l.new(fade.outputs[0],mult.inputs[1])
volume=n.new('ShaderNodeVolumePrincipled');volume.inputs['Color'].default_value=(.92,.95,1,1);volume.inputs['Anisotropy'].default_value=.25;l.new(mult.outputs[0],volume.inputs['Density'])
out=n.new('ShaderNodeOutputMaterial');l.new(volume.outputs[0],out.inputs['Volume'])
s.world=bpy.data.worlds.new('Soft cloud illumination');s.world.use_nodes=True;s.world.node_tree.nodes['Background'].inputs[1].default_value=.7
bpy.ops.object.light_add(type='SUN',location=(-22,-14,12));o=bpy.context.object;o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler();o.data.energy=2;o.data.angle=.3
bpy.ops.object.camera_add(location=(0,0,0),rotation=(1.57079632679,0,0));s.camera=bpy.context.object;s.camera.data.type='PANO';s.camera.data.panorama_type='EQUIRECTANGULAR';s.camera.data.clip_end=1000
s.render.resolution_x=2048;s.render.resolution_y=1024;s.render.resolution_percentage=100;s.render.film_transparent=True
s.view_settings.view_transform='Standard';s.view_settings.exposure=-1
s.render.image_settings.file_format='WEBP';s.render.image_settings.color_mode='RGBA';s.render.image_settings.quality=92
s.render.filepath=str(ROOT/'public/textures/dotonbori-clouds.webp')
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'assets/blender/dotonbori-sky.blend'),compress=True)
bpy.ops.render.render(write_still=True)
print('DOTONBORI_VOLUME_SKY_COMPLETE',flush=True)
