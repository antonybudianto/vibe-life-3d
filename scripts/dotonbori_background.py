"""Modeled canal continuation that holds up with distance haze disabled.

The first two bridges in each direction and their banks are playable. Beyond
the end railings, the scenic river bends behind staggered urban blocks.
"""
import math


def build(n):
    g=n['g'];stone=n['stone'];dark=n['dark'];silver=n['silver']
    glass=n['glass'];windows=n['windows'];wood=n['wood'];warm=n['warm']
    walls=[n['facades'][3],n['facades'][2],n['facades'][4],n['facades'][0]]
    report=[]
    limit=n['layout']['promenadeEnd'];bridges=n['layout']['extensionBridges']
    collider=n['collider']

    def building(x,y,w,d,h,angle,style,index,shops=True):
        co,si=math.cos(angle),math.sin(angle);wall=walls[style]
        def p(u,v,z):return (x+u*co-v*si,y+u*si+v*co,z)
        def box(u,v,z,ww,dd,hh,m):g.box(p(u,v,z),(ww,dd,hh),m,angle,name='Dotonbori background architecture')
        def face(u,v,z,ww,hh,m):g.panel(p(u,v,z),ww,hh,m,angle)
        front=-d/2
        # Recessed glazing sits behind projecting floor slabs and facade piers.
        box(0,.25,h/2,w,d-.5,h,wall)
        floor=[3.0,3.45,2.9,3.25][style]+[0,.25,-.18,.12,.38][index%5]
        far=index>=5
        bays=max(2,round(w/(3.7 if far else [2.55,3.1,2.8,2.45][style])));bay=(w-.7)/bays
        for level in range(1,int((h-1.4)/floor)):
            z=3.8+(level-.5)*floor
            if z+floor*.5>h:break
            box(0,front-.1,z-floor*.5,w+.13,.58,.24 if style!=2 else .4,stone if style==0 else wall)
            if style in [0,1]:box(0,front-.24,z-floor*.5+.17,w,.09,.065,silver)
            for j in range(bays):
                u=-w/2+.35+(j+.5)*bay;ww=bay-.25;hh=floor-.65
                lit=(level*7+j*3+index)%11<2
                if (index%3==1 and j==0) or (style==2 and level%4==0):
                    face(u,front-.018,z,ww,hh,wall)
                else:face(u,front-.012,z,ww,hh,windows[(index+j+level)%3] if lit else glass)
                box(u-bay/2,front-.1,z,.18,.44,hh+.15,dark if style==1 else wall)
                if not far:
                    box(u,front-.085,z+.1,ww,.12,.06,dark)
                    if style!=2:box(u,front-.09,z,.055,.14,hh,dark)
                box(u,front-.21,z-hh/2,ww+.16,.38,.10,stone)
            # Both returns are articulated, especially important at the bend.
            for side in [-1,1]:
                return_bays=2 if far else max(2,int(d/3))
                for k in range(return_bays):
                    v=-d/2+(k+.5)*d/return_bays
                    if v>d/2-1:continue
                    g.panel(p(side*(w/2+.012),v,z),d/return_bays-.6,hh,
                            windows[2] if (k+level+index)%6==0 else glass,angle+side*math.pi/2)
                box(side*(w/2+.08),0,z-floor*.5,.26,d,.22,wall)
        for edge in [-1,1]:box(edge*(w/2-.09),front-.06,h/2,.22,.50,h,wall)
        # Large street-level bays avoid the former blank wall below the windows.
        shopcount=max(2,round(w/4));sw=(w-.5)/shopcount
        for j in range(shopcount):
            u=(j-(shopcount-1)/2)*sw
            face(u,front-.025,1.75,sw-.15,3.1,windows[(j+index)%3] if shops else glass)
            for t in [-.5,0,.5]:box(u+t*(sw-.15),front-.13,1.65,.075,.26,3.2,dark)
            box(u,front-.14,.42,sw,.25,.13,stone)
            if (index+j)%3!=0:box(u,front-.7,3.28,sw+.08,1.5,.16,dark)
            if shops:
                face(u,front-.74,3.79,sw-.13,.80,n['cream'] if index%2 else n['neonred'])
                if index<7:
                    g.text(n['labels'][(index+j)%12],p(u,front-.77,3.79),min(.64,sw/4),
                           n['neonred'] if index%2 else n['white'],angle,font=n['jp'])
                for k in [-1,0,1]:
                    box(u+k*sw*.28,front-.51,2.82,.44,.14,.48,n['blue'] if index%3 else n['red'])
        # A few well-spaced sign cabinets, with exposed brackets and real depth.
        if shops and index%3!=2:
            u=w/2-.66;z=min(h*.58,16)
            box(u,front-.48,z,1.2,.55,min(11,h*.55),dark)
            face(u,front-.78,z,1.02,min(10.7,h*.53),n['white'] if index%2 else n['neonred'])
            if index<8:
                label=n['labels'][(index+style)%12]
                for j,c in enumerate(label):g.text(c,p(u,front-.80,z+(len(label)-1-2*j)*.7),.91,
                        n['neonred'] if index%2 else n['white'],angle,font=n['jp'])
        # Roof setbacks, solid parapets, metal coping, HVAC and a service shaft.
        box(0,0,h+.07,w+.25,d+.25,.20,stone)
        for v in [-d/2+.12,d/2-.12]:box(0,v,h+.45,w,.22,.72,wall)
        for u in [-w/2+.12,w/2-.12]:box(u,0,h+.45,.22,d,.72,wall)
        box(-w*.12,d*.13,h+1.55,w*.48,d*.43,2.85,walls[(style+1)%4])
        box(-w*.12,d*.13,h+3.02,w*.49,d*.44,.18,silver)
        for u in [-w*.27,w*.19]:
            box(u,front+1.5,h+.7,1.45,1.3,1.05,silver)
            if not far:
                for k in range(4):box(u-.48+k*.31,front+.82,h+.7,.09,.07,.72,dark)
        box(w/2-.7,d/2-.75,h+2.0,.8,.85,3.6,wall)
        g.rod(p(w/2-.7,d/2-.75,h+3.8),p(w/2-.7,d/2-.75,h+5.4),.035,silver,6)
        report.append(dict(x=round(x,2),y=round(y,2),width=w,depth=d,height=h,family=style))
        if abs(y)-w/2 <= limit and abs(x)-d/2 < 21:
            # These river-facing buildings are rotated by exactly 90 degrees.
            collider(x,y,d/2+.20,w/2+.12,h)

    def fence(a,b,z=0):
        dx=b[0]-a[0];dy=b[1]-a[1];length=math.hypot(dx,dy);angle=math.atan2(dy,dx)
        for height in [.35,.72,1.12]:
            g.box(((a[0]+b[0])/2,(a[1]+b[1])/2,z+height),(length,.055,.06),dark,angle)
        for i in range(math.ceil(length/1.15)+1):
            t=i/math.ceil(length/1.15)
            g.box((a[0]+dx*t,a[1]+dy*t,z+.57),(.055,.055,1.14),dark)

    # Unequal frontages, heights and setbacks prevent mirrored, repeated banks.
    rows=[(76,10.2,24),(87,10.8,29),(98.5,11,22),(111,12.4,33),
          (124,12.3,27),(137,12.5,24),(151,13.8,31),(165.5,13.5,26),
          (181,14.8,23),(198,15.8,30),(216,17.3,25)]
    def bend(t):return max(0,t-167)*.42
    for end in [-1,1]:
        # Segment the river and stone banks around a shallow bend. The far end
        # is occluded by the neighborhood, not by freestanding skyline boxes.
        for start,stop in [(70,110),(110,limit),(limit,167),(167,190),(190,214),(214,238)]:
            a=bend(start);b=bend(stop)
            def strip(lo,hi,z,m,name=None):
                vertices=[(a+lo,end*start,z),(a+hi,end*start,z),(b+hi,end*stop,z),(b+lo,end*stop,z)]
                g.mesh(vertices,[(0,1,2,3),(3,2,1,0)],m,name)
            for side in [-1,1]:
                if stop <= limit:
                    # A solid top shares the promenade's AO/irradiance atlas.
                    lo,hi=sorted([end*start,end*stop])
                    n['paving_segment'](n,side,lo,hi,8.3,20.3)
                else:
                    strip(min(side*8.3,side*20.3),max(side*8.3,side*20.3),0,n['paving'],'Dotonbori distant paving')
                aa=(a+side*8.3,end*start);bb=(b+side*8.3,end*stop)
                g.mesh([(*aa,0),(*bb,0),(*bb,-2.2),(*aa,-2.2)],[(0,1,2,3),(3,2,1,0)],stone)
                if stop <= limit:
                    cuts=[start]+[v for t in bridges for v in [t-3.4,t+3.4] if start<v<stop]+[stop]
                    for lo,hi in zip(cuts,cuts[1:]):
                        if any(abs((lo+hi)/2-t)<3.4 for t in bridges):continue
                        fence((side*8.3,end*lo),(side*8.3,end*hi))
                        collider(side*8.3,end*(lo+hi)/2,.06,(hi-lo)/2,1.14)
                else:fence(aa,bb)
        # Canal exclusion has openings only beneath the new bridge decks.
        cuts=[70]+[v for t in bridges for v in [t-3.4,t+3.4]]+[limit]
        for lo,hi in zip(cuts,cuts[1:]):
            if any(abs((lo+hi)/2-t)<3.4 for t in bridges):continue
            collider(0,end*(lo+hi)/2,8.22,(hi-lo)/2,0,cameraIgnore=True)
        for side in [-1,1]:
            n['paving_joints'](side,*sorted([end*70,end*limit]))
            fence((side*8.3,end*limit),(side*20.3,end*limit))
            collider(side*14.3,end*limit,6,.06,1.14)
        for side in [-1,1]:
            for i,(t,w,h) in enumerate(rows):
                style=(i+(2 if side==1 else 0)+(1 if end==1 else 0))%4
                setback=[.1,.55,-.1,.3][(i+(side+1))%4]
                center=bend(t);depth=[10,12,9.5,11][style]
                angle=-side*math.pi/2
                building(center+side*(19+setback+depth/2),end*t,w,depth,
                         h+[0,3,-2,1][(i+side+end)%4],angle,style,i)
                # More compact river lamps, pavement joints and planted benches.
                # Keep lamp bases off the added stair treads and landings.
                beside_stairs=t<=limit and any(abs(t-b)<9.4 for b in bridges)
                x=center+side*(14.25 if beside_stairs else 9.05);y=end*t
                g.box((x,y,.16),(.45,.45,.32),stone)
                g.box((x,y,1.48),(.11,.11,2.65),dark)
                g.box((x,y,2.88),(.35,.35,.56),warm)
                for z in [2.57,3.19]:g.box((x,y,z),(.49,.49,.08),dark)
                g.box((center+side*8.16,y,-.55),(.07,.35,.6),warm)
                if t <= limit:collider(x,y,.245,.245,3.24,cameraRadius=.25)
                if t > limit:
                    for offset in [-4,-2,0,2,4]:
                        g.box((center+side*13.7,y+offset,.008),(10.5,.018,.016),n['joint'])
                if i%2==0:
                    x=center+side*16.65
                    g.box((x,y,.29),(1.35,2.3,.58),stone)
                    g.box((x,y,.60),(1.17,2.1,.05),wood)
                    g.rod((x,y,.6),(x+.16,y,3.0),.075,wood,7)
                    # Crossed leaf clusters retain open silhouettes at distance.
                    for k in range(7):
                        az=k*2.4;xx=x+math.cos(az)*.70;yy=y+math.sin(az)*.78;zz=3.2+(k%3)*.32
                        g.rod((x+.16,y,2.4),(xx,yy,zz),.035,wood,6)
                        for j in range(12):
                            a=j*2.4;cx=xx+math.cos(a)*.36;cy=yy+math.sin(a)*.38;cz=zz+(j%3)*.16
                            g.mesh([(cx-.28,cy,cz),(cx,cy-.18,cz+.10),(cx+.28,cy,cz),(cx,cy+.18,cz-.04)],[(0,1,2,3),(3,2,1,0)],n['leaves'][(j+k)%5])
                    g.box((x-side*1.0,y,.5),(.45,1.9,.12),wood)
                    if t <= limit:
                        collider(x,y,.675,1.15,.63,cameraRadius=.15)
                        collider(x,y,.16,.10,4.3,cameraRadius=.85)
                        collider(x-side*1.0,y,.225,.95,.56)
            # Secondary blocks step up behind the bank and frame the skyline.
            for i,t in enumerate([102,181]):
                building(bend(t)+side*(38+i%2*5),end*(t+5),13+i%2*4,13,
                         [36,30,39,33][i],-side*math.pi/2,(i+2)%4,12+i,False)
        for t in [91,140,186]:
            if t in bridges:
                n['bridge'](end*t,False)
                continue
            x=bend(t);y=end*t
            g.box((x,y,1.9),(18,3.6,.70),stone)
            g.box((x,y,2.30),(18.3,3.8,.14),n['cap'])
            for edge in [-1,1]:
                fence((x-9,y+edge*1.75),(x+9,y+edge*1.75),2.37)
                g.box((x+edge*6.1,y,-.10),(1.2,3.8,3.3),stone)
        # An articulated corner hotel on the inside of the bend closes the old
        # straight sightline while leaving the curved waterway unobstructed.
        building(2,end*225,20,17,27,0 if end==1 else math.pi,0,14,True)
        # A cross street and a final occupied block continue beyond the bend.
        # Their overlapping silhouettes keep clear-sky views from looking out
        # through a blue gap at pavement level, even from the outer footbridge.
        building(32,end*255,34,18,28,0 if end==1 else math.pi,1,15,True)
        x=bend(238);y=end*238
        g.box((x,end*247,-.3),(64,19,.6),n['paving'],name='Dotonbori distant paving')
        g.box((x,y,1.9),(20,6,.7),stone)
        for edge in [-1,1]:
            fence((x-10,y+edge*2.85),(x+10,y+edge*2.85),2.28)
            g.box((x+edge*6.6,y,-.1),(1.3,6.2,3.3),stone)
    return dict(buildings=report,canalEnd=238,bendStart=167,playableEnd=limit,walkableBridges=[end*t for end in [-1,1] for t in bridges])
