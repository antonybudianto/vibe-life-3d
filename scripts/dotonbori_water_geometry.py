"""One upward-facing water footprint, including both mirrored canal ends."""
import math

def build(g,water,layout):
    verts=[];faces=[]
    for j in range(561):
        y=-70+j*.25
        for i in range(69):
            x=-8.5+i*.25
            z=-1.43+.019*math.sin(x*4.3+y*7.7)+.012*math.sin(y*14-x*3.1)
            verts.append((x,y,z))
    for j in range(560):
        for i in range(68):
            k=j*69+i;faces.append((k,k+1,k+70,k+69))
    g.mesh(verts,faces,water,'Dotonbori canal water',True)
    limit=layout['promenadeEnd']
    for end in [-1,1]:
        for start,stop in [(70,110),(110,limit),(limit,167),(167,190),(190,214),(214,238)]:
            a=max(0,start-167)*.42;b=max(0,stop-167)*.42
            # Match the central footprint and overlap beneath the retaining
            # walls at ±8.3, rather than leaving a visible 0.3 m bank gap.
            vertices=[(a-8.5,end*start,-1.45),(a+8.5,end*start,-1.45),
                      (b+8.5,end*stop,-1.45),(b-8.5,end*stop,-1.45)]
            # Reversing the river direction reverses the vertex winding.
            # Never add an opposed duplicate: Draco may keep the wrong side.
            face=(0,1,2,3) if end>0 else (3,2,1,0)
            g.mesh(vertices,[face],water,'Dotonbori canal water')
