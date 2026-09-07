"""Check terrain coverage, paint clearance and seamless district material UVs."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender/crossing.blend'))
depsgraph=bpy.context.evaluated_depsgraph_get()
ground=[bpy.data.objects[n] for n in ['Rain-dark asphalt','District asphalt']]
trees=[BVHTree.FromObject(o,depsgraph) for o in ground]
metadata=json.loads((ROOT/'public/models/crossing.json').read_text())

def road_height(x,y):
    hits=[tree.ray_cast(Vector((x,y,1)),Vector((0,0,-1)),2)[0] for tree in trees]
    return max((p.z for p in hits if p is not None),default=-math.inf)

# Coverage throughout the camera-visible district, including all tile seams.
count=0
for x in range(-119,120,7):
    for y in range(-109,125,7):
        assert abs(road_height(x,y)-.005)<.0001,(x,y,'missing terrain')
        count+=1
for c in metadata['colliders']:
    if c['height']<12:continue
    for sx in [-1,1]:
        for sy in [-1,1]:
            x=c['x']+sx*c['halfX'];y=-c['z']+sy*c['halfZ']
            assert math.isfinite(road_height(x,y)),(x,y,'floating building')

for name in ['Crosswalk ivory paint','District road paint']:
    o=bpy.data.objects[name];positions=[o.matrix_world@v.co for v in o.data.vertices]
    span=max(max(p[i] for p in positions)-min(p[i] for p in positions) for i in range(3))
    quantization_step=span/(2**16-1)
    clearance=min(p.z-road_height(p.x,p.y) for p in positions)
    assert clearance>4*quantization_step and clearance>.018,(name,clearance,quantization_step)
    assert o.data.materials[0].get('surface_role')=='road-marking'

for name in ['Rain-dark asphalt','Pavement stone','Crosswalk ivory paint','Tactile ochre',
             'District asphalt','District paving','District road paint','District ochre markings']:
    o=bpy.data.objects[name];uv=o.data.uv_layers['BakeUV']
    for p in o.data.polygons:
        if p.normal.z<.9:continue
        for li in p.loop_indices:
            v=o.data.vertices[o.data.loops[li].vertex_index].co
            if v.z<=-.06:continue
            assert all(-.0001<=c<=1.0001 for c in uv.data[li].uv),(name,tuple(v),'outside district bake')
            expected=((v.x+120)/240,(v.y+110)/235)
            assert max(abs(a-b) for a,b in zip(uv.data[li].uv,expected))<.0001,'Shared world lighting coordinates'
for name in ['Rain-dark asphalt','District asphalt']:
    o=bpy.data.objects[name];uv=o.data.uv_layers['RoadSurfaceUV']
    for loop in o.data.loops:
        v=o.data.vertices[loop.vertex_index].co
        assert max(abs(a-b) for a,b in zip(uv.data[loop.index].uv,((v.x+120)/240,(v.y+110)/235)))<.0001,'Continuous road weathering coordinates'
# At MAGNET's former overlap, ceramic and glass must not share an exterior plane.
ceramic=BVHTree.FromObject(bpy.data.objects['Landmark white ceramic'],depsgraph)
glazing=BVHTree.FromObject(bpy.data.objects['Dark reflective glass'],depsgraph)
for x in [59.3,60.2,61.5,63.0]:
    hit=ceramic.ray_cast(Vector((x,0,8.9)),Vector((0,1,0)),30)[0]
    expected=15.6-math.sqrt(4.6**2-(x-63.6)**2)
    assert hit is not None and abs(hit.y-expected)<.015,(x,'MAGNET rounded ceramic corner missing')
for x in [69.2,70.5,72.5]:
    for origin,direction in [(Vector((x,0,8.9)),Vector((0,1,0))),(Vector((x,45,8.9)),Vector((0,-1,0)))]:
        a=ceramic.ray_cast(origin,direction,45)[0];b=glazing.ray_cast(origin,direction,45)[0]
        assert b is not None,(x,'MAGNET glass missing')
        assert a is None or (a-b).length>.02,(x,'MAGNET coplanar facade overlap')
print('DISTRICT_GEOMETRY_OK',count,'terrain samples; building corners; paint clearance; bake UVs; MAGNET curved corner and separated facades')
