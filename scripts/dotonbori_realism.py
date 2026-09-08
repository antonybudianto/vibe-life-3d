"""Photo-informed canal landmarks, kept as modeled architecture at game scale.

References: CTI Ebisubashi project photograph and Don Quijote Ebisu Tower.
The historic H&M shell is retained without its former tenant branding.
"""
import math


def perimeter_ramps(n,y,edge,top):
    """Separate outer curved paths, entered through the middle of the plaza.

    Compact interpretation of CVV's Ebisubashi photographs (8) and (9): the
    ramp is outside the plaza railing, alongside—not replacing—the stairs.
    """
    g=n['g'];silver=n['silver'];stone=n['stone'];width=1.65
    def deck_sample(fn,x):
        # The deck is 24 planar strips. Match their interpolation exactly;
        # independently sampling the circle at 48 points crosses the fascia.
        i=max(0,min(23,math.floor((x+8.5)*24/17)))
        a=-8.5+i*17/24;b=a+17/24
        return fn(a)+(fn(b)-fn(a))*(x-a)/(b-a)
    def deck_height(x):return deck_sample(lambda xx:2.55+.24*max(0,1-(xx/8.5)**2),x)
    def level(x):
        t=abs(x)/8.5
        # Level transitions at the plaza entrance and lower bank landings.
        return top*(1-t*t*(3-2*t))
    for end in [-1,1]:
        for i in range(48):
            a=-8.5+i*17/48;b=-8.5+(i+1)*17/48
            ea,eb=deck_sample(edge,a),deck_sample(edge,b)
            za=level(a);zb=level(b)
            ia,ib=y+end*ea,y+end*eb;oa,ob=ia+end*width,ib+end*width
            v=[(a,ia,za),(b,ib,zb),(b,ob,zb),(a,oa,za)]
            # One upward-facing surface: reversed duplicate faces also compete
            # in the depth buffer and sample the underside's excluded bake UVs.
            g.mesh(v,[(0,1,2,3) if end==1 else (3,2,1,0)],n['cap'],'Ebisubashi deck')
            g.mesh([(x,yy,zz-.20) for x,yy,zz in v],[(3,2,1,0) if end==1 else (0,1,2,3)],stone,'Bridge solid soffits')
            n['surfaces'].append(dict(minX=a,maxX=b,minZ=min(-ia,-oa),maxZ=max(-ia,-oa),endMinZ=min(-ib,-ob),endMaxZ=max(-ib,-ob),height=za,endHeight=zb))
            # Inner wall separates the lower path from the higher plaza. The
            # two middle slices form the entrance and must remain open.
            if not (a>=-17/24-.001 and b<=17/24+.001):
                ha,hb=deck_height(a),deck_height(b)
                # One continuous retaining face covers the deck fascia and
                # lower ramp wall. Materials already render both sides.
                g.mesh([(a,ia,min(za-.2,ha-.94)),(b,ib,min(zb-.2,hb-.94)),(b,ib,hb),(a,ia,ha)],[(3,2,1,0) if end==1 else (0,1,2,3)],stone,'Ebisubashi ramp retaining walls')
                g.rod((a,ia+end*.07,za+.86),(b,ib+end*.07,zb+.86),.032,silver,8)
            g.mesh([(a,oa,za),(b,ob,zb),(b,ob,zb-.6),(a,oa,za-.6)],[(0,1,2,3) if end==1 else (3,2,1,0)],silver,'Ebisubashi ramp fascia')
            from dotonbori_bridge import baluster
            for h in [.10,1.1]:g.rod((a,oa,za+h),(b,ob,zb+h),.040,silver,8)
            tangent=(b-a,ob-oa)
            count=max(1,math.ceil(math.hypot(*tangent)/.27))
            for k in range(count):
                t=(k+.5)/count
                x=a+(b-a)*t;yy=oa+(ob-oa)*t;z=za+(zb-za)*t
                baluster(n,(x,yy,z),tangent)
            # Folded panel casing with fine vertical seams and rolled lower edge.
            g.rod((a,oa+end*.015,za-.56),(b,ob+end*.015,zb-.56),.048,silver,10)
            g.rod((a,oa+end*.019,za-.53),(a,oa+end*.019,za-.025),.009,n['joint'],6)
            for k in range(4):
                ta=k/4;tb=(k+1)/4;xa=a+(b-a)*ta;xb=a+(b-a)*tb
                ya=oa+(ob-oa)*ta;yb=oa+(ob-oa)*tb
                n['collider']((xa+xb)/2,(ya+yb)/2,(xb-xa)/2+.01,abs(yb-ya)/2+.035,top+1.2,cameraMinY=min(za,zb)-.2)
        g.text('え び す 橋',(0,y+end*(edge(0)+width+.038),top-.29),.42,n['black'],0 if end==-1 else math.pi,font=n['jp'])
        for side in [-1,1]:
            # The existing promenade at z=0 is the lower landing. A second
            # coplanar floor here causes flashing beside the stairs at a distance.
            n['rail']((side*8.5,y+end*3.8),(side*10.45,y+end*3.8),0)
            n['collider'](side*9.475,y+end*3.8,.975,.035,1.2)


def frontage(n,side,y,w,h,front,hero):
    g=n['g'];mat=n['mat'];pos=n['pos'];panel=n['panel']
    silver=n['silver'];dark=n['dark'];glass=n['glass'];white=n['white']
    pale=mat('retail porcelain',(.76,.77,.73),.64)
    steelblue=mat('retail blue fins',(.075,.16,.25),.42,.45)
    glazing=mat('retail pale glazing',(.17,.26,.29),.25,.38)
    angle=-side*math.pi/2
    def box(u,v,z,d,ww,hh,m):g.box(pos(side,y,u,v,z),(d,ww,hh),m)
    def face(u,v,z,ww,hh,m):g.panel(pos(side,y,u,v,z),ww,hh,m,angle)
    box(0,-5.0,h/2,9.0,w,h,pale)
    if hero in ['glass-retail','glass-tower']:
        # Contrasting white vertical tower and blue-finned glazed west wing.
        if hero=='glass-tower':
            face(0,.06,h*.5,w-1,h-1,glazing)
            for u in [-w/2+.32,w/2-.32]:box(u,.42,h/2,.90,.65,h,pale)
            for z in range(4,int(h),4):box(0,.35,z,.6,w,.24,pale)
            for z in range(13,int(h)-2,3):
                box(0,.18,z,.35,w-1.4,.08,silver)
            panel(side,y,0,10,w-1.6,.9,dark,'EBISUBASHI',white,.65)
        else:
            face(0,.05,h/2,w-.5,h-.6,glazing)
            for u in [(-w/2+.4)+j*1.55 for j in range(int(w/1.55))]:box(u,.60,h/2,1.2,.22,h,steelblue)
            for z in range(4,int(h),4):box(0,.38,z,.8,w,.18,silver)
        face(0,.11,1.8,w-.8,3.4,glass)
        for u in [-w*.3,0,w*.3]:box(u,.4,1.8,.6,.10,3.4,silver)
    else:
        # Donki's large tiled retail box and open upper boarding balcony.
        for z in range(2,int(h),3):
            box(0,.15,z,.25,w,.055,silver)
            for u in range(-int(w/2),int(w/2)+1,2):box(u,.16,z+1.45,.26,.025,2.85,silver)
        face(0,.20,5.8,w-.8,3.9,dark)
        panel(side,y,0,6.4,w-1,2.0,dark,'ドン・キホーテ',n['yellow'],1.45)
        panel(side,y,0,9.0,w-1,.9,white,'驚安の殿堂',n['red'],.7)
        box(0,1.4,4.6,3.0,w,.18,n['red'])
        face(0,.25,2.0,w-.5,3.9,glass)
        box(0,1.2,11.1,3.0,w-.4,.4,pale)
        for u in [-w/2+.4+i*.45 for i in range(int((w-.8)/.45))]:
            g.rod(pos(side,y,u,2.4,11.3),pos(side,y,u,2.4,12.4),.035,silver,6)
        for z in [11.5,12.4]:g.rod(pos(side,y,-w/2+.3,2.4,z),pos(side,y,w/2-.3,2.4,z),.05,silver,8)
    box(0,-4.6,h+.2,10,w+.1,.4,pale)


def wheel(n):
    g=n['g'];pos=n['pos'];mat=n['mat'];panel=n['panel'];side=1;y=-40
    yellow=n['yellow'];silver=n['silver'];dark=n['dark'];glass=n['glass']
    gold=mat('Ebisu structural yellow',(.97,.56,.025),.36,.28,.12)
    def p(u,v,z):return pos(side,y,u,v,z)
    # Racetrack shape: straight vertical runs and rounded ends, with 32 cabins.
    r=6.4;lo=14.5;hi=47.0;straight=hi-lo;length=2*straight+2*math.pi*r
    def path(t):
        d=(t%1)*length
        if d<straight:return (r,lo+d)
        d-=straight
        if d<math.pi*r:
            a=d/r;return (r*math.cos(a),hi+r*math.sin(a))
        d-=math.pi*r
        if d<straight:return (-r,hi-d)
        a=(d-straight)/r+math.pi;return (r*math.cos(a),lo+r*math.sin(a))
    for depth in [1.3,2.5]:
        for inset in [0,.5]:
            for i in range(160):
                u,z=path(i/160);v,zz=path((i+1)/160)
                g.rod(p(u*(1-inset/r),depth,z),p(v*(1-inset/r),depth,zz),.12,gold,8,name='Ebisu Tower rails')
    for i in range(64):
        u,z=path(i/64);v,zz=path((i+1)/64)
        g.rod(p(u,1.3,z),p(v,2.5,zz),.075,gold,6)
        g.rod(p(u,1.3,z),p(u,2.5,z),.09,gold,6)
    for u in [-4.8,4.8]:
        for depth in [1.1,2.4]:g.rod(p(u,depth,2),p(u,depth,49),.22,gold,10)
    for z in range(3,47,4):
        g.rod(p(-4.8,1.1,z),p(4.8,1.1,z+4),.11,gold,8)
        g.rod(p(4.8,1.1,z),p(-4.8,1.1,z+4),.11,gold,8)
    for i in range(32):
        u,z=path(i/32)
        g.sphere(p(u,3.0,z),(.68,.79,.95),n['red'],16,10,name='Ebisu Tower 32 gondolas')
        g.panel(p(u,3.7,z+.08),1.18,1.22,glass,-math.pi/2)
        for off in [-.58,.58]:g.rod(p(u+off,3.73,z-.58),p(u+off,3.73,z+.65),.045,silver,6)
        g.rod(p(u-.58,3.73,z+.65),p(u+.58,3.73,z+.65),.045,silver,6)
    # Large relief mascot: Ebisu's smiling face and cap, green robe and Donpen.
    skin=mat('Ebisu mascot face',(.91,.64,.43),.56)
    green=mat('Ebisu mascot robe',(.025,.31,.19),.54)
    navy=mat('Donpen blue',(.025,.095,.42),.42)
    def oval(u,v,z,sx,sy,sz,m):g.sphere(p(u,v,z),(sx,sy,sz),m,24,16,name='Ebisu and Donpen relief')
    oval(0,3.0,31,1.0,4.2,6.8,green)
    oval(0,3.4,40,1.3,3.4,3.7,skin)
    oval(0,3.6,43.4,1.0,3.6,1.4,dark)
    oval(0,4.0,44.4,.6,1.5,1.8,dark)
    for u in [-1.4,1.4]:
        oval(u,4.55,40.6,.12,.47,.16,dark)
        oval(u*1.55,4.45,39.1,.12,.63,.35,n['pink'])
    oval(0,4.65,38.65,.15,1.25,.35,n['white'])
    oval(0,4.85,39.75,.25,.57,.55,skin)
    oval(-1.5,4.2,29.5,1.0,2.1,3.0,navy)
    oval(-1.5,5.15,28.6,.2,1.4,1.7,n['white'])
    for u in [-2.25,-.75]:
        oval(u,5.1,30.7,.10,.43,.54,n['white']);oval(u,5.23,30.7,.07,.18,.27,dark)
    oval(-1.5,5.35,29.85,.32,.8,.35,yellow)
    oval(-1.4,4.6,32.7,.6,2.15,.75,n['red'])
    oval(2.35,4.0,28.0,.8,1.25,3.7,yellow)
    panel(side,y,0,19.6,10.4,2.0,n['white'],'えびすタワー',n['red'],1.0)


def river_details(n):
    g=n['g'];warm=n['warm'];dark=n['dark'];silver=n['silver']
    # The restaurant street runs behind the south-bank block, at right angles
    # to the bridge approach; the moved crab and octopus face this pavement.
    g.box((-34,-24,-.18),(8,90,.36),n['paving'],name='Dotonbori restaurant street')
    for y in range(-64,20,3):g.box((-34,y,.008),(8,.025,.015),n['joint'])
    # Red lantern strings characterize the Donki bank; they vary by season.
    for start,stop in [(-64,-52),(-44,-13),(15,39)]:
        g.rod((8.45,start,2.7),(8.45,stop,2.7),.016,dark,6)
        for y in range(start,stop,2):
            g.rod((8.45,y,2.7),(8.45,y,2.35),.014,dark,6)
            g.sphere((8.45,y,2.12),(.22,.22,.29),n['red'],12,8)
            for z in [1.85,2.4]:g.box((8.45,y,z),(.18,.18,.05),dark)
    # Boarding information remains on the existing promenade, outside routes.
    n['panel'](1,-40,7,2.7,2.0,2.4,n['yellow'],'TOMBORI\nRIVER CRUISE',n['black'],.43)
    for y in [-32,-27]:
        g.box((15.8,y,.5),(.5,.55,1.0),silver)
    # Distinct dark timber strips beneath the north-bank shops.
    for start,stop in [(-65,-53),(-43,-13),(13,38)]:
        for y in range(start*4,stop*4):
            g.box((15.7,y/4,.017),(1.5,.22,.025),n['wood'])
