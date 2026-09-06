"""Check meaningful image coverage at mesh face centers after Cycles baking."""
import bpy,json
import numpy as np
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
report=[]
for name in ['character','crossing','park']:
    bpy.ops.wm.open_mainfile(filepath=str(ROOT/'assets/blender'/f'{name}.blend'))
    image=bpy.data.images.load(str(ROOT/'assets/bakes'/f'{name}-color.png'),check_existing=True)
    w,h=image.size;pixels=np.asarray(image.pixels[:],dtype=np.float32).reshape(h,w,4)
    stats=[]
    for o in bpy.context.scene.objects:
        if o.type!='MESH' or not o.data.uv_layers.get('BakeUV'):continue
        if o.data.color_attributes.get('BakedLocalShade'):
            values=[max(c.color[:3]) for c in o.data.color_attributes['BakedLocalShade'].data]
            if not values or min(values)<.001:raise RuntimeError(f'{o.name}: missing vertex shading')
            stats.append({'mesh':o.name,'mode':'Cycles vertex bake','blackAreaFraction':0,'samples':len(values)})
            continue
        if not any(m.node_tree.nodes.get('Baked surface color') for m in o.data.materials):continue
        uv=o.data.uv_layers['BakeUV'];count=bad=0;area=bad_area=0
        for face in o.data.polygons:
            center=np.mean([uv.data[i].uv[:] for i in face.loop_indices],axis=0)
            x,y=min(w-1,max(0,int(center[0]*w))),min(h-1,max(0,int(center[1]*h)))
            black=pixels[y,x,:3].max()<.0001
            count+=1;bad+=bool(black);area+=face.area;bad_area+=face.area*black
        fraction=float(bad_area/max(area,1e-9));stats.append({'mesh':o.name,'blackFaceFraction':bad/count,'blackAreaFraction':fraction})
        # A few subpixel seams are expected; broad black faces are a broken bake.
        if fraction>.08:print('MISSING_COVERAGE',name,o.name,f'{fraction:.1%}',flush=True)
    report.append({'asset':name,'objects':stats})
(ROOT/'work/bake-coverage.json').write_text(json.dumps(report,indent=2))
if any(o['blackAreaFraction']>.08 for a in report for o in a['objects']):raise RuntimeError('Missing albedo coverage; see work/bake-coverage.json')
print('PASS: baked meshes have valid texture coverage or complete Cycles vertex shading.',flush=True)
