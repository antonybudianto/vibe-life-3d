"""Ebisubashi stone parapets, fine paving, and punched spatula balustrades.

The inner plaza has a solid granite wall. Only the outer ramp has the iconic
slotted metal fins; these are modeled with actual openings for reflections.
"""
import math


def parapet(n,a,b):
    g=n['g'];stone=n['stone'];cap=n['cap']
    ax,ay,az=a;bx,by,bz=b
    length=math.hypot(bx-ax,by-ay);nx=-(by-ay)/length*.13;ny=(bx-ax)/length*.13
    verts=[(x+sgn*nx,y+sgn*ny,z+h) for x,y,z in [a,b] for sgn,h in [(-1,0),(1,0),(1,.88),(-1,.88)]]
    g.mesh(verts,[(0,1,2,3),(7,6,5,4),(0,4,5,1),(1,5,6,2),(2,6,7,3),(3,7,4,0)],stone,'Ebisubashi granite parapet')
    g.rod((ax,ay,az+.88),(bx,by,bz+.88),.17,cap,12,name='Ebisubashi rounded granite cap')
    for sgn in [-1,1]:
        g.rod((ax+sgn*nx,ay+sgn*ny,az+.08),(ax+sgn*nx,ay+sgn*ny,az+.83),.008,n['joint'],6)
        g.rod((ax+sgn*nx,ay+sgn*ny,az+.43),(bx+sgn*nx,by+sgn*ny,bz+.43),.007,n['joint'],6)


def baluster(n,origin,tangent):
    g=n['g'];silver=n['silver'];x,y,z=origin
    length=math.hypot(*tangent);tx,ty=[v/length for v in tangent];nx,ny=-ty,tx
    outer=[(-.050,.07),(.050,.07),(.064,.22),(.112,.68),(.112,1.05),(-.112,1.05),(-.112,.68),(-.064,.22)]
    hole=[(-.022,.30),(.022,.30),(.035,.37),(.040,.57),(.025,.68),(-.025,.68),(-.040,.57),(-.035,.37)]
    verts=[]
    for depth in [-.022,.022]:
        for outline in [outer,hole]:
            for u,h in outline:verts.append((x+tx*u+nx*depth,y+ty*u+ny*depth,z+h))
    faces=[]
    for i in range(8):
        j=(i+1)%8
        faces.extend([(i,j,j+8,i+8),(i+16,i+24,j+24,j+16),(i,i+16,j+16,j),(i+8,j+8,j+24,i+24)])
    g.mesh(verts,faces,silver,'Ebisubashi slotted spatula balusters')


def paving(n,y,edge,elevation):
    g=n['g'];mat=n['mat']
    stones=[mat('Ebisubashi granite paving '+str(i),c,.86) for i,c in enumerate([
        (.49,.48,.46),(.53,.52,.50),(.46,.46,.445),(.56,.55,.52)])]
    centerstone=mat('Ebisubashi charcoal center paving',(.20,.215,.23),.86)
    borderstone=mat('Ebisubashi pale strip edging',(.63,.62,.59),.86)
    for m in stones+[centerstone,borderstone]:m['walkable_paving']=True
    # Small staggered rectangular slabs and a curved border follow the crowned
    # deck. Interpolate its actual 24 strips to avoid any coplanar flashing.
    def height(x):
        if abs(x)>8.5:return elevation(8.5)+.009
        strip=max(0,min(23,math.floor((x+8.5)*24/17)))
        a=-8.5+strip*17/24;b=a+17/24
        return elevation(a)+(elevation(b)-elevation(a))*(x-a)/(b-a)+.009
    def outline(x):
        if abs(x)>=8.5:return edge(8.5)
        strip=max(0,min(23,math.floor((x+8.5)*24/17)))
        a=-8.5+strip*17/24;b=a+17/24
        return edge(a)+(edge(b)-edge(a))*(x-a)/(b-a)
    # Split pavers at the actual radial/approach bands; there are no overlaid
    # coplanar decals competing for the same lightmap texels.
    radial=[(math.cos(k*math.pi/4),math.sin(k*math.pi/4)) for k in range(4)]
    dividers=[(nx,ny,offset) for nx,ny in radial for offset in [-.045,.045]]+[(0,1,q) for q in [-1.9,-1.8,1.8,1.9]]
    def split(poly,nx,ny,d):
        result=[[],[]]
        for a,b in zip(poly,poly[1:]+poly[:1]):
            da=a[0]*nx+a[1]*ny-d;db=b[0]*nx+b[1]*ny-d
            side=0 if da<=0 else 1;result[side].append(a)
            if da*db<0:
                t=da/(da-db);p=(a[0]+(b[0]-a[0])*t,a[1]+(b[1]-a[1])*t)
                result[0].append(p);result[1].append(p)
        return [p for p in result if len(p)>2]
    def tile(a,b,c,d,m):
        cuts=[a]+[-8.5+i*17/24 for i in range(25) if a<-8.5+i*17/24<b]+[b]
        for x1,x2 in zip(cuts,cuts[1:]):
            inset=.19 if max(abs(x1),abs(x2))<=8.5 else 0
            slope=(outline(x2)-outline(x1))/(x2-x1);intercept=outline(x1)-slope*x1-inset
            parts=[[(x1,c),(x2,c),(x2,d),(x1,d)]]
            for sign in [-1,1]:
                parts=[q for part in parts for q in split(part,-slope,sign,intercept)
                       if sum(-slope*x+sign*yy for x,yy in q)/len(q)<=intercept+1e-8]
            for nx,ny,offset in dividers:parts=[q for part in parts for q in split(part,nx,ny,offset)]
            for poly in parts:
                if abs(sum(a[0]*b[1]-b[0]*a[1] for a,b in zip(poly,poly[1:]+poly[:1])))<1e-8:continue
                cx=sum(p[0] for p in poly)/len(poly);cy=sum(p[1] for p in poly)/len(poly)
                inside=cx*cx+cy*cy<6.45**2
                finish=m
                if inside and min(abs(nx*cx+ny*cy) for nx,ny in radial)<.046:finish=borderstone
                elif not inside:
                    if abs(cy)<1.8:finish=centerstone
                    elif abs(cy)<1.9:finish=borderstone
                g.mesh([(x,y+yy,height(x)) for x,yy in poly],[tuple(range(len(poly)))],finish)
    for row in range(-24,24):
        for col in range(-29,29):
            a=col*.48+(row%2)*.24;b=a+.47
            a=max(-13.50,a);b=min(13.50,b)
            if b>a:
                c=row*.30+.006;d=(row+1)*.30-.006
                tile(a,b,c,d,stones[(row*3+col*5)%4])
    # Pale perimeter band emphasizes the plaza's rounded outline.
    for end in [-1,1]:
        for i in range(48):
            a=-8.5+i*17/48;b=a+17/48
            ea=outline(a);eb=outline(b)
            verts=[(a,y+end*(ea-.19),height(a)+.003),(b,y+end*(eb-.19),height(b)+.003),(b,y+end*eb,height(b)+.003),(a,y+end*ea,height(a)+.003)]
            g.mesh(verts,[(0,1,2,3) if end==1 else (3,2,1,0)],n['cap'],'Ebisubashi deck')
