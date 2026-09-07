"""Small, seamless material textures authored inside Blender; shared by GLB and Cycles."""
import bpy,numpy as np

def add_street_grain():
    rng=np.random.default_rng(109);n=512
    noise=rng.random((n,n)).astype(np.float32)
    broad=sum(np.roll(np.roll(noise,y,0),x,1) for x in range(-3,4) for y in range(-3,4))/49
    grain=(noise-.5)*.26+(broad-.5)*2.8
    def image(name,rgb,color=False):
        im=bpy.data.images.new(name,width=n,height=n,alpha=False,float_buffer=color)
        im.colorspace_settings.name='Linear Rec.709' if color else 'Non-Color'
        rgba=np.ones((n,n,4),dtype=np.float32);rgba[:,:,:3]=rgb;im.pixels.foreach_set(rgba.reshape(-1));im.pack();return im
    for name in ['Rain-dark asphalt','Pavement stone','Crosswalk ivory paint','District asphalt','District paving','District road paint']:
        m=bpy.data.materials.get(name)
        if not m or m.get('surface_texture'):continue
        nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes['Principled BSDF'];base=np.array(p.inputs['Base Color'].default_value[:3])
        tint=np.clip(1+grain, .65,1.35)
        uv=nodes.new('ShaderNodeUVMap');uv.uv_map='UVMap'
        tex=nodes.new('ShaderNodeTexImage');tex.image=image(name+' aggregate albedo',tint[:,:,None]*base,True)
        links.new(uv.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],p.inputs['Base Color'])
        dx=np.roll(noise,1,1)-np.roll(noise,-1,1);dy=np.roll(noise,1,0)-np.roll(noise,-1,0)
        normal=np.stack((.5+dx*.075,.5+dy*.075,np.ones_like(dx)),axis=-1)
        tex=nodes.new('ShaderNodeTexImage');tex.image=image(name+' aggregate normal',normal)
        links.new(uv.outputs['UV'],tex.inputs['Vector']);node=nodes.new('ShaderNodeNormalMap');node.inputs['Strength'].default_value=.45
        links.new(tex.outputs['Color'],node.inputs['Color']);links.new(node.outputs['Normal'],p.inputs['Normal'])
        rough=np.clip(float(p.inputs['Roughness'].default_value)+grain*.42,.30,.94)
        tex=nodes.new('ShaderNodeTexImage');tex.image=image(name+' aggregate roughness',np.repeat(rough[:,:,None],3,axis=2))
        links.new(uv.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],p.inputs['Roughness'])
        m['surface_texture']='Blender seamless aggregate: albedo, roughness and tangent normal'
    # Large-scale wear needs its own world UVs; one-metre repeating grain alone
    # becomes a flat gray plane at gameplay distance. AO/lightmap UV1 stays intact.
    names=['Rain-dark asphalt','District asphalt']
    if not bpy.data.materials.get(names[0]):return
    # One world coordinate system and shared images prevent a visible material
    # seam at the old 47 m boundary. Keep the same texel density as the core.
    n=2048
    def field(size):
        grid=rng.random((size,size)).astype(np.float32)
        knots=np.linspace(0,n-1,size);coords=np.arange(n)
        rows=np.stack([np.interp(coords,knots,row) for row in grid])
        return np.stack([np.interp(coords,knots,row) for row in rows.T],axis=1)
    fine=field(384);mid=field(70);broad=field(26)
    yy,xx=np.meshgrid(np.linspace(-110,125,n),np.linspace(-120,120,n),indexing='ij')
    lanes=np.maximum(np.exp(-((np.abs(xx)-4.5)/1.55)**2),np.exp(-((np.abs(yy)-4.5)/1.55)**2))
    for offsets,coordinates in [([64.5,69.5],yy),([50.5,55.5,-63.5,-68.5],xx)]:
        for offset in offsets:lanes=np.maximum(lanes,np.exp(-((coordinates-offset)/1.4)**2))
    damp=np.clip((broad-.40)*2.7,0,1)
    tint=np.clip(.86+(mid-.5)*.34+(fine-.5)*.28-lanes*.11-damp*.14,.49,1.12)
    albedo=image('Rain-dark asphalt aggregate weathering',tint[:,:,None]*np.array([.038,.043,.055]),True)
    rough=np.clip(.67-damp*.36-lanes*.11+(fine-.5)*.11,.23,.76)
    roughness=image('Rain-dark asphalt aggregate wet roughness',np.repeat(rough[:,:,None],3,axis=2))
    for name in names:
        m=bpy.data.materials.get(name);o=bpy.data.objects.get(name)
        if not m or not o:continue
        uvlayer=o.data.uv_layers.get('RoadSurfaceUV') or o.data.uv_layers.new(name='RoadSurfaceUV')
        for loop in o.data.loops:
            v=o.matrix_world@o.data.vertices[loop.vertex_index].co
            uvlayer.data[loop.index].uv=((v.x+120)/240,(v.y+110)/235)
        nodes=m.node_tree.nodes;links=m.node_tree.links;p=nodes['Principled BSDF']
        uv=nodes.new('ShaderNodeUVMap');uv.uv_map='RoadSurfaceUV'
        for im,socket in [(albedo,'Base Color'),(roughness,'Roughness')]:
            tex=nodes.new('ShaderNodeTexImage');tex.image=im
            links.new(uv.outputs['UV'],tex.inputs['Vector']);links.new(tex.outputs['Color'],p.inputs[socket])
        m['road_weathering']='Shared district world-space damp patches, lane wear and aggregate'
        o.data.uv_layers.active_index=0
