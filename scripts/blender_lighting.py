"""Shared art presets. Run inside Blender after opening a delivered .blend scene.
blender --background scene.blend --python scripts/blender_lighting.py -- night
"""
import bpy, json, math, sys
from pathlib import Path
from mathutils import Vector

def linear_rgb(value):
    channels=[int(value[i:i+2],16)/255 for i in (1,3,5)]
    return tuple(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in channels)

def apply_preset(preset='evening'):
    root=Path(__file__).resolve().parents[1]
    path='dotonbori-lighting.json' if bpy.context.scene.get('location_id')=='dotonbori' else 'lighting.json'
    p=json.loads((root/'lib/game'/path).read_text())[preset]
    s=bpy.context.scene;s['lighting_preset']=preset
    # Cycles world radiance and Three's hemisphere + environment use different units.
    # Calibrated together against the exported crossing under the shared AgX view.
    if s.world:
        s.world.use_nodes=True;bg=s.world.node_tree.nodes.get('Background')
        bg.inputs[0].default_value=(*linear_rgb(p['sky']),1);bg.inputs[1].default_value=p['ambient']*1.7
    for o in s.objects:
        if o.type=='LIGHT' and o.get('baked_shop'):
            o.data.energy=o.get('base_power',o.data.energy)*p['emission']
        if o.type=='LIGHT' and o.data.type=='SUN':
            o.data.color=linear_rgb(p['sun']);o.data.energy=p['power']*.55;o.data.angle=.12
            o.location=(-22,-14,28);o.rotation_euler=(-o.location).to_track_quat('-Z','Y').to_euler()
    for m in bpy.data.materials:
        if not m.use_nodes:continue
        node=m.node_tree.nodes.get('Principled BSDF')
        if not node:continue
        if 'base_emission' not in m:m['base_emission']=node.inputs['Emission Strength'].default_value
        node.inputs['Emission Strength'].default_value=m['base_emission']*p['emission']
    s.view_settings.view_transform='AgX';s.view_settings.exposure=math.log2(p['exposure'])
    from blender_sky import camera_sky
    camera_sky(p)

if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
    apply_preset(args[0] if args else 'evening')
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
