"""Yellow open-deck Tombori cruisers, authored from the user's real-life photo."""
import math
import random


def build_cruises(n):
    g=n['g'];mat=n['mat'];yellow=n['boatmat'];dark=n['dark'];silver=n['silver'];black=n['black'];cream=n['cream']
    blue=mat('cruise blue seats',(.035,.085,.15),.67)
    deck=mat('cruise nonslip deck',(.30,.28,.23),.86)
    rubber=mat('cruise rubber rubbing strip',(.035,.033,.027),.87)
    orange=mat('cruise rescue equipment',(.93,.11,.012),.59)
    banner=mat('cruise cream advertising',(.84,.73,.42),.67)
    results=[]
    def passenger(x,y,z,coat,scale=.88,standing=False):
        # People face the bow (+Y), with bent knees visibly meeting the seats.
        def p(a,b,h):return (x+scale*a,y+scale*b,z+scale*h)
        head=1.48 if standing else 1.27;hip=.80 if standing else .55
        g.sphere(p(0,0,head),(.17*scale,.16*scale,.21*scale),n['skin'],12,8)
        g.sphere(p(0,-.025,head+.11),(.178*scale,.16*scale,.14*scale),n['hair'],12,8)
        g.sphere(p(0,0,hip+.27),(.24*scale,.16*scale,.32*scale),coat,12,8)
        for a in [-.12,.12]:
            knee=p(a,.24 if not standing else 0,.43 if not standing else .45)
            g.rod(p(a,0,hip),knee,.086*scale,black,10)
            g.rod(knee,p(a,.27,.12),.078*scale,black,10)
            g.sphere(p(a,.34,.09),(.105*scale,.18*scale,.075*scale),dark,10,6)
            g.rod(p(a*2,0,hip+.48),p(a*2.1,.15,hip+.16),.063*scale,coat,10)
            g.rod(p(a*2.1,.15,hip+.16),p(a*1.5,.33,hip+.12),.059*scale,coat,10)
    # The longer hulls retain clearance throughout their existing eight-meter motion.
    for index,(x,y) in enumerate([(-3,-24),(3,28)]):
        z=-1.10
        outline=[(-1.80,-6.9),(1.80,-6.9),(1.90,5.3),(1.20,6.8),(0,7.2),(-1.20,6.8),(-1.90,5.3)]
        count=len(outline)
        vertices=[(x+a*.86,y+b*.96,z-.55) for a,b in outline]+[(x+a,y+b,z+.70) for a,b in outline]
        g.mesh(vertices,[tuple(reversed(range(count)))]+[(k,(k+1)%count,(k+1)%count+count,k+count) for k in range(count)],yellow,'Cruise yellow hull')
        g.mesh([(x+a*.96,y+b*.985,z+.46) for a,b in outline],[tuple(range(count))],deck,'Cruise open deck')
        for i,a in enumerate(outline):
            b=outline[(i+1)%count]
            g.rod((x+a[0],y+a[1],z+.71),(x+b[0],y+b[1],z+.71),.070,yellow,10)
            g.rod((x+a[0]*.96,y+a[1]*.99,z+.06),(x+b[0]*.96,y+b[1]*.99,z+.06),.085,rubber,10)
        # Four blue seats per row, separated by a center aisle.
        for row,yy in enumerate([-4.40,-3.22,-2.04,-.86,.32,1.50,2.68,3.86]):
            for col,xx in enumerate([-1.14,-.54,.54,1.14]):
                g.box((x+xx,y+yy,z+.88),(.53,.48,.12),blue,name='Cruise passenger seats')
                g.box((x+xx,y+yy-.22,z+1.08),(.53,.085,.44),blue,name='Cruise passenger seats')
                for dx in [-.18,.18]:g.rod((x+xx+dx,y+yy,z+.48),(x+xx+dx,y+yy,z+.84),.025,silver,6)
                if (row+col+index)%6!=0:
                    passenger(x+xx,y+yy-.025,z+.46,n['coats'][(row*3+col+index)%6],.84+random.random()*.06)
        # Thin yellow rails preserve the open silhouette and the view of passengers.
        for side in [-1,1]:
            xx=x+side*1.84
            for level in [.92,1.32]:g.rod((xx,y-6.7,z+level),(xx,y+5.25,z+level),.035,yellow,8,name='Cruise yellow handrails')
            for yy in [-6.7,-5.4,-4.2,-3,-1.8,-.6,.6,1.8,3,4.2,5.25]:
                g.rod((xx,y+yy,z+.72),(xx,y+yy,z+1.33),.027,yellow,8,name='Cruise yellow handrails')
            # The cream advertising panels sit below the handrail, as in the photo.
            g.panel((x+side*1.91,y-.6,z+.68),7.0,.78,banner,side*math.pi/2)
            g.text('とんぼりリバークルーズ',(x+side*1.935,y-.6,z+.82),.29,black,side*math.pi/2,font=n['jp'])
            g.text('TOMBORI RIVER CRUISE',(x+side*1.94,y-.6,z+.52),.20,black,side*math.pi/2,font=n['font'])
            # Tire fenders hang below the gunwale near the bow and stern.
            for yy in [-5.8,4.6]:
                for k in range(16):
                    a=k*math.tau/16;b=(k+1)*math.tau/16
                    g.rod((xx+side*.055,y+yy+math.cos(a)*.23,z+.29+math.sin(a)*.29),(xx+side*.055,y+yy+math.cos(b)*.23,z+.29+math.sin(b)*.29),.055,rubber,8)
        # Open helm, steering wheel and a standing guide at the tapered bow.
        g.box((x-.65,y+5.45,z+.95),(1.1,.55,.85),yellow,name='Cruise helm')
        g.box((x-.65,y+5.15,z+1.28),(.85,.08,.15),dark)
        for i in range(20):
            a=i*math.tau/20;b=(i+1)*math.tau/20
            g.rod((x-.65+.24*math.cos(a),y+5.09,z+1.45+.24*math.sin(a)),(x-.65+.24*math.cos(b),y+5.09,z+1.45+.24*math.sin(b)),.025,silver,6)
        passenger(x-.63,y+4.78,z+.46,n['coats'][1],.80,True)
        # Brown stern engine covers and orange safety boxes replace the former cabin.
        for xx in [-.98,.98]:
            g.box((x+xx,y-5.65,z+.98),(1.03,1.12,1.0),n['wood'],name='Cruise stern equipment')
            g.box((x+xx,y-5.65,z+1.52),(1.12,1.18,.10),yellow)
            g.box((x+xx,y-6.65,z+.88),(.82,.47,.55),orange,name='Cruise stern equipment')
            g.box((x+xx,y-6.67,z+1.18),(.22,.17,.06),silver)
            g.box((x+xx,y-7.05,z+.20),(.44,.29,.85),rubber,name='Cruise stern equipment')
        g.box((x,y-6.89,z+.94),(3.62,.10,.42),yellow)
        g.text('とんぼりクルーズ',(x,y-6.955,z+.95),.28,black,0,font=n['jp'])
        parts=g.flush()
        import bpy
        root=bpy.data.objects.new('River cruise '+str(index),None);bpy.context.collection.objects.link(root)
        root['cruise']=True;root['cruiseIndex']=index;root['cruiseStyle']='yellow open deck'
        root['cruiseLength']=14.25;root['cruiseBeam']=3.95
        for o in parts:o.parent=root
        results+=parts+[root]
    return results
