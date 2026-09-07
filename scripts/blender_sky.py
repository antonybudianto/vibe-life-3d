"""Use the game's cloud bake and palette in Blender's camera-visible world."""
import bpy
from pathlib import Path
from blender_lighting import linear_rgb

def camera_sky(preset):
    path=Path(__file__).resolve().parents[1]/'public/textures/clouds.webp'
    if not path.exists():return
    world=bpy.context.scene.world;nodes=world.node_tree.nodes;links=world.node_tree.links
    # Rebuild only our named nodes. Keep the calibrated ambient world untouched.
    for node in list(nodes):
        if node.name.startswith('City sky '):nodes.remove(node)
    def node(kind,name):
        n=nodes.new(kind);n.name='City sky '+name;return n
    def math(op,a,b=None):
        n=node('ShaderNodeMath',op);n.operation=op
        if isinstance(a,(float,int)):n.inputs[0].default_value=a
        else:links.new(a,n.inputs[0])
        if b is not None:
            if isinstance(b,(float,int)):n.inputs[1].default_value=b
            else:links.new(b,n.inputs[1])
        return n.outputs[0]
    geometry=node('ShaderNodeNewGeometry','direction')
    direction=node('ShaderNodeVectorMath','outward');direction.operation='SCALE';direction.inputs['Scale'].default_value=-1;links.new(geometry.outputs['Incoming'],direction.inputs[0])
    split=node('ShaderNodeSeparateXYZ','axes');links.new(direction.outputs[0],split.inputs[0])
    # Blender Z-up and Three Y-up share the same elevation and azimuth panorama.
    u=math('ADD',math('DIVIDE',math('ARCTAN2',math('MULTIPLY',split.outputs['Y'],-1),split.outputs['X']),6.28318530718),.5)
    v=math('ADD',math('DIVIDE',math('ARCSINE',split.outputs['Z']),3.14159265359),.5)
    uv=node('ShaderNodeCombineXYZ','panorama UV');links.new(u,uv.inputs[0]);links.new(v,uv.inputs[1])
    texture=node('ShaderNodeTexImage','clouds');texture.image=bpy.data.images.load(str(path),check_existing=True);texture.image.colorspace_settings.name='Non-Color';texture.image.pack();links.new(uv.outputs[0],texture.inputs[0])
    gradient=node('ShaderNodeMixRGB','gradient');gradient.inputs[1].default_value=(*linear_rgb(preset['sky']),1);gradient.inputs[2].default_value=(*linear_rgb(preset['skyZenith']),1)
    links.new(math('POWER',math('MAXIMUM',split.outputs['Z'],0),.42),gradient.inputs[0])
    channels=node('ShaderNodeSeparateColor','cloud shading');links.new(texture.outputs['Color'],channels.inputs[0])
    color=node('ShaderNodeMixRGB','silver');color.blend_type='MULTIPLY';color.inputs[0].default_value=1;color.inputs[1].default_value=(*linear_rgb(preset['cloudTint']),1);links.new(math('ADD',math('MULTIPLY',channels.outputs[0],.32),.68),color.inputs[2])
    mix=node('ShaderNodeMixRGB','cloud cover');links.new(texture.outputs['Alpha'],mix.inputs[0]);links.new(gradient.outputs[0],mix.inputs[1]);links.new(color.outputs[0],mix.inputs[2])
    background=node('ShaderNodeBackground','visible');links.new(mix.outputs[0],background.inputs[0])
    lightpath=node('ShaderNodeLightPath','camera ray');shader=node('ShaderNodeMixShader','camera only')
    links.new(lightpath.outputs['Is Camera Ray'],shader.inputs[0]);links.new(nodes['Background'].outputs[0],shader.inputs[1]);links.new(background.outputs[0],shader.inputs[2]);links.new(shader.outputs[0],nodes.get('World Output').inputs[0])
