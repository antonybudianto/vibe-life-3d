"""Bake a seamless capillary-wave normal map with Cycles, then use it in the canal."""
import bpy, math
import numpy as np


def bake_water_normal(root):
    size = 512
    u, v = np.meshgrid(np.arange(size) / size, np.arange(size) / size)
    height = np.full((size, size), .5)
    # Integer periods keep all four tile boundaries continuous.
    for amplitude, x, y, phase in [(.12, 2, 7, 0), (.065, -3, 13, 1.2),
                                  (.034, 7, 23, 2), (.018, -13, 41, .5),
                                  (.011, 19, 67, 2.7)]:
        height += amplitude * np.sin(math.tau * (u*x + v*y) + phase)
    rgba = np.ones((size, size, 4), dtype=np.float32)
    rgba[:, :, :3] = height[:, :, None]
    source = bpy.data.images.new('Canal periodic wave heights', size, size)
    source.colorspace_settings.name = 'Non-Color'
    source.pixels.foreach_set(rgba.reshape(-1)); source.pack()
    material = bpy.data.materials.new('Canal normal bake source'); material.use_nodes = True
    nodes = material.node_tree.nodes; links = material.node_tree.links
    tex = nodes.new('ShaderNodeTexImage'); tex.image = source
    bump = nodes.new('ShaderNodeBump'); bump.inputs['Distance'].default_value = .19
    links.new(tex.outputs['Color'], bump.inputs['Height'])
    links.new(bump.outputs['Normal'], nodes['Principled BSDF'].inputs['Normal'])
    target = bpy.data.images.new('Dotonbori Cycles water normal', size, size)
    target.colorspace_settings.name = 'Non-Color'
    output = nodes.new('ShaderNodeTexImage'); output.image = target; nodes.active = output
    bpy.ops.mesh.primitive_plane_add(size=4, location=(0, 0, -20))
    plane = bpy.context.object; plane.data.materials.append(material)
    bpy.ops.object.select_all(action='DESELECT'); plane.select_set(True)
    bpy.context.view_layer.objects.active = plane
    bpy.context.scene.render.bake.normal_space = 'TANGENT'
    bpy.ops.object.bake(type='NORMAL', target='IMAGE_TEXTURES')
    values = np.asarray(target.pixels[:]).reshape(-1, 4)
    variation = float(values[:, :2].std())
    if variation < .03: raise RuntimeError('Water normal bake has insufficient variation')
    folder = root/'public/textures'; folder.mkdir(exist_ok=True)
    target.filepath_raw = str(folder/'dotonbori-water-normal.png')
    target.file_format = 'PNG'; target.save(); target.pack()
    bpy.data.objects.remove(plane, do_unlink=True)
    water = bpy.data.materials['Dotonbori canal water']
    nodes = water.node_tree.nodes; links = water.node_tree.links
    coord = nodes.new('ShaderNodeTexCoord')
    scale = nodes.new('ShaderNodeVectorMath'); scale.operation = 'SCALE'; scale.inputs[3].default_value = .25
    tex = nodes.new('ShaderNodeTexImage'); tex.image = target; tex.label = 'Cycles baked capillary ripples'
    normal = nodes.new('ShaderNodeNormalMap'); normal.inputs['Strength'].default_value = .85
    links.new(coord.outputs['UV'], scale.inputs[0]); links.new(scale.outputs[0], tex.inputs['Vector'])
    links.new(tex.outputs['Color'], normal.inputs['Color'])
    links.new(normal.outputs['Normal'], nodes['Principled BSDF'].inputs['Normal'])
    water['normal_bake'] = 'Cycles tangent normals, seamless four-metre wave tile'
    return {'waterNormal': '/textures/dotonbori-water-normal.png', 'waterNormalSize': size,
            'waterNormalStd': variation, 'waterNormalEngine': 'CYCLES'}
