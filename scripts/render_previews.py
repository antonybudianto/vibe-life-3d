"""Render deliverable previews from the actual editable Blender assets."""
import bpy,sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
targets=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else ['character','crossing']
for name in targets:
    bpy.ops.wm.open_mainfile(filepath=str(root/'assets'/'blender'/(name+'.blend')))
    if str(root/'scripts') not in sys.path:sys.path.insert(0,str(root/'scripts'))
    from blender_lighting import apply_preset
    apply_preset('evening')
    bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath)
    scene=bpy.context.scene
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(root/'public'/'renders'/(name+'.png'))
    bpy.ops.render.render(write_still=True)
    if name=='character':
        scene.render.image_settings.file_format='WEBP';scene.render.image_settings.quality=86
        bpy.data.images['Render Result'].save_render(str(root/'public'/'renders'/'character.webp'),scene=scene)
    print('PREVIEW COMPLETE',name,flush=True)
