"""Render the delivered Blender scene in Cycles, using the shared day/evening presets."""
import bpy,sys,json,math,hashlib
from pathlib import Path
from mathutils import Vector,Matrix
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'scripts'))
requested=next((arg.split('=',1)[1].split(',') for arg in sys.argv if arg.startswith('--views=')),None)
def render_view(name):
    if requested is not None and name not in requested:return
    s.render.filepath=str(ROOT/'public/renders'/f'dotonbori-{name}.png')
    bpy.ops.render.render(write_still=True)
from bake_assets import cycles
from blender_lighting import apply_preset
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/dotonbori.blend'))
s=bpy.context.scene;cycles(s);s.cycles.samples=40
# Render the shared animated visitors at an actual simulation instant. These
# temporary instances are never saved in the source scene or exported game map.
snapshot=json.loads((ROOT/'work/canal-crowd.json').read_text())
fingerprint=hashlib.sha256()
for path in snapshot['inputs']:fingerprint.update((ROOT/path).read_bytes())
if snapshot['hash']!=fingerprint.hexdigest():raise RuntimeError('Run node scripts/canal_snapshot.mjs before rendering')
with bpy.data.libraries.load(str(ROOT/'assets/blender/pedestrian.blend'),link=False) as (a,b):
    b.objects=[n for n in a.objects if n not in ['Studio ground','Camera','Evening sun','Sky bounce']]
crowd=[o for o in b.objects if o and o.type=='MESH']
for person,pose in zip(snapshot['people'],snapshot['poses']):
    gait=math.sin(pose['gait'])*min(1,pose['speed']/.9)
    root=Matrix.Translation((pose['x'],-pose['z'],pose['y']+.1+abs(gait)*.025))@Matrix.Rotation(pose['yaw'],4,'Z')@Matrix.Scale(person['scale'],4)
    for source in crowd:
        o=source.copy();o.data=source.data;s.collection.objects.link(o)
        limb=Matrix.Identity(4)
        if source.get('swing'):
            x,z,y=source['pivot'];v=Vector((x,-y,z))
            limb=Matrix.Translation(v)@Matrix.Rotation(gait*.34*source['swing'],4,'X')@Matrix.Translation(-v)
        o.matrix_world=root@limb@source.matrix_world
        if source.data.materials[0].name.startswith('Crowd outfit'):
            mat=source.data.materials[0].copy();o.data=source.data.copy();o.data.materials[0]=mat
            color=person['coat'].lstrip('#');srgb=[int(color[k:k+2],16)/255 for k in [0,2,4]]
            linear=[v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4 for v in srgb]
            mat.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=tuple(v*.78 for v in linear)+(1,)
s.render.resolution_x=1440;s.render.resolution_y=960;s.render.resolution_percentage=100
s.render.image_settings.file_format='PNG'
for phase in ['evening','day']:
    apply_preset(phase)
    render_view(phase)
apply_preset('evening')
for name,position,target,lens in [
    ('bridge-realism',(2,22,20),(0,0,2),29),
    ('donki-realism',(-8,-24,21),(17,-40,28),21),
    ('riverside',(10,-22,3.2),(0,3,7),24),
    ('north',(-2,41,7),(0,-3,10),26),
    ('water',(0,-11,1.5),(0,17,-.1),30),
    ('landmarks',(15,9,23),(-19,9,17),11),
    ('south',(13,-55,32),(-18,6,12),20),
    ('geography',(2,46,16),(0,-22,11),24),
    ('east-continuation',(10.2,-34,6.4),(10.36,-94,5.8),28),
    ('west-continuation',(-10,36,6.4),(-8,100,5.8),28),
    ('extension-first',(16,77,6),(4,91,1.3),24),
    ('extension-second',(-15,151,5.2),(-3,138,1.2),22),
    ('paving-west',(12,60,11),(12,81,0),30),
    ('paving-east',(12,-60,11),(12,-81,0),30),
]:
    s.camera.location=position;s.camera.data.lens=lens
    s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler()
    render_view(name)
s.camera.location=(5,-70,67);s.camera.data.lens=28
s.camera.rotation_euler=(Vector((0,7,6))-s.camera.location).to_track_quat('-Z','Y').to_euler()
render_view('overview')
# Photo-matching reviews use daylight to expose the metalwork and open seating.
apply_preset('day')
for name,position,target,lens in [
    ('bridge-stairs',(17,20,8),(7,1,2.0),28),
    ('asahi',(12,17,16),(-21,-9,17),24),
    ('cruise',(8,-12,6),(-3,-24,-.1),34),
]:
    s.camera.location=position;s.camera.data.lens=lens
    s.camera.rotation_euler=(Vector(target)-s.camera.location).to_track_quat('-Z','Y').to_euler()
    render_view(name)
