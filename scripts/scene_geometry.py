"""Fast Blender mesh batching for the Shibuya art pass. Coordinates are Z-up."""
import bpy,math,random
from array import array
from mathutils import Vector,Matrix

M={};B={};TEXT=[]

def compact_baked_colors(objects):
    """8-bit sRGB vertex colors are sufficient for the subtle local AO tint."""
    seen=set()
    for o in objects:
        if o.type!='MESH' or o.data in seen:continue
        seen.add(o.data)
        attrs=o.data.color_attributes;old=attrs.get('BakedLocalShade')
        if not old or old.data_type!='FLOAT_COLOR':continue
        values=array('f',[0])*(len(old.data)*4);old.data.foreach_get('color',values)
        name=old.name;new=attrs.new(name=name+' compact',type='BYTE_COLOR',domain=old.domain)
        new.data.foreach_set('color',values);attrs.remove(old);new.name=name
        attrs.active_color_index=list(attrs).index(new);attrs.render_color_index=attrs.active_color_index

def material(name,color,rough=.7,metal=0,emission=0,alpha=1):
    if name in M:return M[name]
    m=bpy.data.materials.new(name);m.use_nodes=True
    p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(*color,alpha)
    p.inputs['Roughness'].default_value=rough;p.inputs['Metallic'].default_value=metal
    p.inputs['Alpha'].default_value=alpha
    if emission:p.inputs['Emission Color'].default_value=(*color,1);p.inputs['Emission Strength'].default_value=emission
    m['base_emission']=emission
    if alpha<1:m.surface_render_method='DITHERED'
    M[name]=m;return m

def mesh(verts,faces,mat,name=None,smooth=False,uvs=None):
    key=(name or mat.name,mat)
    if key not in B:B[key]=[[],[],[],[]]
    v,f,s,u=B[key];off=len(v);v.extend(verts);f.extend([tuple(i+off for i in face) for face in faces]);s.extend([smooth]*len(faces))
    if uvs:u.extend(uvs)
    else:
        for face in faces:
            a,b,c=[Vector(verts[i]) for i in face[:3]];n=(b-a).cross(c-a)
            axis=max(range(3),key=lambda i:abs(n[i]));axes=[i for i in range(3) if i!=axis]
            u.extend([(verts[i][axes[0]],verts[i][axes[1]]) for i in face])

def box(pos,size,mat,rot=0,name=None):
    x,y,z=pos;w,d,h=[s/2 for s in size];co,si=math.cos(rot),math.sin(rot)
    v=[(x+a*co-b*si,y+a*si+b*co,z+c) for a,b,c in [(-w,-d,-h),(w,-d,-h),(w,d,-h),(-w,d,-h),(-w,-d,h),(w,-d,h),(w,d,h),(-w,d,h)]]
    mesh(v,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],mat,name)

def sphere(pos,scale,mat,segments=12,rings=8,name=None):
    v=[];f=[]
    for j in range(rings+1):
        phi=math.pi*j/rings
        for i in range(segments):
            a=2*math.pi*i/segments;v.append((pos[0]+scale[0]*math.sin(phi)*math.cos(a),pos[1]+scale[1]*math.sin(phi)*math.sin(a),pos[2]+scale[2]*math.cos(phi)))
    for j in range(rings):
        for i in range(segments):
            a=j*segments+i;b=j*segments+(i+1)%segments;f.append((a,b,b+segments,a+segments))
    mesh(v,f,mat,name,True)

def rod(a,b,r,mat,segments=8,r2=None,name=None):
    start,end=Vector(a),Vector(b);direction=end-start;rot=direction.to_track_quat('Z','Y').to_matrix();v=[]
    for center,rad in [(start,r),(end,r if r2 is None else r2)]:
        for i in range(segments):
            ang=2*math.pi*i/segments;v.append(tuple(center+rot@Vector((math.cos(ang)*rad,math.sin(ang)*rad,0))))
    faces=[tuple(reversed(range(segments))),tuple(range(segments,segments*2))]
    for i in range(segments):j=(i+1)%segments;faces.append((i,j,j+segments,i+segments))
    mesh(v,faces,mat,name,True)

def panel(pos,w,h,mat,angle=0):
    x,y,z=pos;co,si=math.cos(angle),math.sin(angle)
    v=[(x+a*co,y+a*si,z+b) for a,b in [(-w/2,-h/2),(w/2,-h/2),(w/2,h/2),(-w/2,h/2)]]
    mesh(v,[(0,1,2,3)],mat,uvs=[(0,0),(1,0),(1,1),(0,1)])

def text(body,pos,size,mat,angle=0,font=None):
    data=bpy.data.curves.new('Lettering','FONT');data.body=body;data.size=size;data.align_x='CENTER';data.align_y='CENTER';data.resolution_u=1;data.extrude=0
    if font:data.font=font
    o=bpy.data.objects.new('Sign '+body[:20],data);bpy.context.collection.objects.link(o);o.location=pos;o.rotation_euler=(math.pi/2,0,angle);data.materials.append(mat);TEXT.append(o)
    return o

def flush():
    objects=[]
    for (name,mat),(verts,faces,smooth,uvs) in B.items():
        data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.materials.append(mat);data.update()
        layer=data.uv_layers.new(name='UVMap')
        for item,uv in zip(layer.data,uvs):item.uv=uv
        for p,value in zip(data.polygons,smooth):p.use_smooth=value
        o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);objects.append(o)
    B.clear()
    # Convert and batch signage once, after geometry authoring is complete.
    bymaterial={}
    for o in TEXT:
        bpy.ops.object.select_all(action='DESELECT');o.select_set(True);bpy.context.view_layer.objects.active=o;bpy.ops.object.convert(target='MESH')
        bymaterial.setdefault(o.data.materials[0],[]).append(o)
    for mat,parts in bymaterial.items():
        bpy.ops.object.select_all(action='DESELECT')
        for o in parts:o.select_set(True)
        bpy.context.view_layer.objects.active=parts[0]
        if len(parts)>1:bpy.ops.object.join()
        o=bpy.context.object;o.name='Lettering '+mat.name;objects.append(o)
    TEXT.clear();return objects

def export(path,objects):
    bpy.ops.object.select_all(action='DESELECT')
    for o in objects:o.select_set(True)
    bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_apply=True,export_extras=True,export_cameras=False,export_lights=False,export_image_format='WEBP',export_image_quality=88,export_draco_mesh_compression_enable=True,export_draco_mesh_compression_level=6,export_draco_position_quantization=16,export_draco_normal_quantization=12,export_draco_texcoord_quantization=14,export_draco_color_quantization=10)
