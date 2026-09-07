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
    for name in ['Rain-dark asphalt','Pavement stone']:
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
