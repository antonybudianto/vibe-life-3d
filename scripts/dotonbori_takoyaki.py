"""Photo-informed Kukuru and Acchichi Honpo tenant frontages.

The district is compressed: both face its playable riverwalk. Kukuru's main
store actually faces Dotonbori Street. Sources and this adaptation are recorded
in assets/references/takoyaki-sources.md. All signs and food are real meshes.
"""
import math
from mathutils import Vector


def build_store(n, side, y, width, front, brand):
    g=n['g']; mat=n['mat']; pos=n['pos']; jp=n['jp']
    dark=mat('takoyaki charcoal',(.014,.019,.024),.66)
    timber=mat('takoyaki stained timber',(.085,.044,.027),.78)
    red=mat('takoyaki octopus lacquer',(.78,.020,.016),.30,.08)
    suction=mat('takoyaki sucker coral',(.91,.25,.16),.45)
    ivory=mat('takoyaki warm lettering',(.96,.90,.73),.52,0,.24)
    blue=mat('Acchichi blue lettering',(.012,.055,.40),.44)
    orange=mat('Acchichi orange canvas',(.98,.23,.014),.87)
    yellow=mat('takoyaki golden yellow',(.96,.59,.033),.51)
    food=mat('takoyaki golden batter',(.66,.29,.058),.69)
    sauce=mat('takoyaki brown sauce',(.13,.034,.008),.24)
    green=mat('takoyaki aonori',(.10,.23,.025),.80)
    steel=n['silver']; glow=n['warm']; ink=n['black']
    angle=-side*math.pi/2
    prefix='Kukuru' if brand=='kukuru' else 'Acchichi Honpo'
    def p(u,v,z):return pos(side,y,u,v,z)
    def box(u,v,z,d,w,h,m):g.box(p(u,v,z),(d,w,h),m,name=prefix+' frontage')
    def face(u,v,z,w,h,m):g.panel(p(u,v,z),w,h,m,angle)
    def sphere(u,v,z,su,sv,sz,m):
        g.sphere(p(u,v,z),(sv,su,sz),m,20,12,name=prefix+' sculpture')
    def text(label,u,v,z,size,m=ivory):
        return g.text(label,p(u,v,z),size,m,angle,font=jp if any(ord(c)>128 for c in label) else n['font'])
    def sign(label,u,v,z,w,h,bg=ivory,fg=blue,size=.6):
        box(u,v-.06,z,.18,w+.12,h+.12,dark)
        face(u,v+.04,z,w,h,bg)
        o=text(label,u,v+.065,z,size,fg)
        # Font bounding boxes, rather than character estimates, keep mixed
        # Japanese and Latin lettering inside its actual modeled cabinet.
        n['bpy'].context.view_layer.update()
        span=max(pt[0] for pt in o.bound_box)-min(pt[0] for pt in o.bound_box)
        if span>w*.92:o.scale.x=w*.92/span
    def tube(points,radius=.28,m=red,suckers=False):
        """Continuous Catmull-Rom tube with rounded bends and tapered tips."""
        controls=[Vector(t) for t in points]; samples=[]
        extended=[controls[0]]+controls+[controls[-1]]
        for i in range(len(controls)-1):
            a,b,c,d=extended[i:i+4]
            for k in range(8):
                t=k/8
                samples.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
        samples.append(controls[-1]); verts=[];faces=[];seg=10
        for i,q in enumerate(samples):
            tangent=samples[min(i+1,len(samples)-1)]-samples[max(0,i-1)]
            tangent.normalize(); normal=tangent.cross(Vector((0,1,0)))
            if normal.length<.01:normal=tangent.cross(Vector((0,0,1)))
            normal.normalize();cross=tangent.cross(normal).normalized()
            t=i/(len(samples)-1);r=radius*(1-.83*t**1.7)
            for k in range(seg):
                v=q+r*(math.cos(k*math.tau/seg)*normal+math.sin(k*math.tau/seg)*cross)
                verts.append(p(*v))
            if i:
                for k in range(seg):
                    a=(i-1)*seg+k;b=(i-1)*seg+(k+1)%seg
                    faces.append((a,b,b+seg,a+seg))
            if suckers and i%4==0 and .16<t<.88:
                sphere(q.x,q.y+r*.92,q.z,r*.42,.055,r*.42,suction)
        faces.extend([tuple(reversed(range(seg))),tuple(range(len(verts)-seg,len(verts)))])
        # p() has determinant side; preserve outward normals on both banks.
        if side<0:faces=[tuple(reversed(f)) for f in faces]
        g.mesh(verts,faces,m,prefix+' curved tentacles',smooth=True)
    def ball(u,v,z,r):
        sphere(u,v,z,r,r,r,food)
        sphere(u,v,z+r*.68,r*.79,r*.79,r*.22,sauce)
        for j in range(4):
            a=(j-1.5)*r*.30
            tube([(u-r*.62,v+a,z+r*.82),(u,v+a,z+r*.94),(u+r*.62,v+a,z+r*.82)],r*.042,ivory)
        for j in range(7):
            a=j*2.399;rr=r*.57*(.5+(j%3)*.22)
            sphere(u+math.cos(a)*rr,v+math.sin(a)*rr,z+r*.94,r*.06,r*.025,r*.025,green)

    # Set the low shop facade ahead of the existing building shell. Recessed
    # serving openings show real counters, griddles and back-wall shelving.
    w=width-.50
    box(0,.34,1.6,.40,w,3.2,dark)
    face(0,.565,1.8,w-.35,2.35,n['windows'][0])
    for u in [-w/2+.14,w/2-.14, w*.24]:box(u,.82,1.55,.62,.22,3.1,timber)
    for z in [.18,2.9]:box(0,.84,z,.62,w,.17,timber)
    box(0,1.02,.67,.94,w-.3,1.15,timber)
    for i in range(int(w/.20)):
        box(-w/2+.20+i*.20,1.51,.68,.035,.075,.98,dark)
    box(0,1.13,1.25,1.28,w-.15,.16,steel)
    for u in [-w*.30,-w*.06]:
        box(u,.91,1.40,.70,1.65,.12,dark)
        for row in range(3):
            for col in range(6):
                sphere(u+(col-2.5)*.23,.70+row*.20,1.49,.088,.088,.062,food)
        box(u,.55,2.52,.43,1.6,.12,steel)
    for u in [-w*.35,-w*.05,w*.13]:
        box(u,.67,1.67,.11,.11,.34,yellow if u<0 else red)
        box(u,.67,1.88,.07,.065,.08,ivory)
    # Food tray on the sales counter and a compact wall-mounted menu.
    box(w*.07,1.42,1.37,.39,.65,.045,ivory)
    for u in [w*.07-.16,w*.07,w*.07+.16]:
        for v in [1.31,1.48]:ball(u,v,1.44,.075)
    sign('たこ焼',w*.36,1.19,2.19,1.6,.42,ivory,red,.28)
    sign('TAKOYAKI',w*.36,1.19,1.76,1.6,.29,dark,ivory,.17)
    for j in range(3):
        sign(['ソース','しょうゆ','ねぎ'][j],w*.36,1.19,1.46-j*.20,1.6,.17,ivory,ink,.13)
    # Noren, lamps and canopy all remain above head height.
    if brand=='kukuru':
        box(0,1.1,3.25,2.05,w+.10,.24,dark)
        for j in range(14):
            u=-w/2+.35+j*(w-.7)/13
            face(u,1.80,2.88,(w-.7)/14,.51,red if j%2==0 else ivory)
            text('く',u,1.825,2.88,.23,ivory if j%2==0 else red)
        for u in [-w*.4,0,w*.4]:sphere(u,1.20,2.95,.09,.09,.08,glow)
        box(0,.56,5.75,.62,w,4.9,dark)
        for u in [-w/2+.18,w/2-.18]:box(u,.92,5.74,.18,.14,4.85,timber)
        sphere(0,1.35,7.13,1.04,.80,1.28,red)
        # Eight individual, asymmetric arms wrap the central wordmark.
        arms=[[(.45,1.6,6.55),(1.9,1.7,6.5),(3.2,1.3,7.1),(2.95,1.45,8.00),(2.55,1.7,7.86)],
              [(-.45,1.6,6.55),(-2.1,1.7,6.4),(-3.5,1.4,7.0),(-3.25,1.3,7.88)],
              [(.55,1.6,6.05),(2.4,1.8,5.8),(3.8,1.4,6.0),(4.15,1.5,6.44)],
              [(-.55,1.6,6.05),(-2.5,1.7,5.7),(-4.12,1.4,5.9),(-4.25,1.5,6.35)],
              [(.45,1.6,5.72),(2.05,1.6,5.16),(3.7,1.5,4.94),(4.16,1.65,4.38)],
              [(-.45,1.6,5.72),(-2.0,1.7,5.14),(-3.65,1.4,4.97),(-3.9,1.6,4.37)],
              [(.35,1.6,5.53),(1.75,1.7,4.4),(2.5,1.4,3.89),(3.15,1.4,4.19)],
              [(-.35,1.6,5.53),(-1.7,1.7,4.4),(-2.7,1.45,3.85),(-3.3,1.5,4.12)]]
        for arm in arms:tube(arm,.35,red,True)
        for u in [-.62,.62]:
            sphere(u,2.05,7.13,.20,.12,.30,yellow)
            sphere(u,2.165,7.13,.049,.045,.21,ink)
        # White outlined letters float across the octopus's chest.
        text('くくる',0,2.25,6.0,1.32,ink)
        text('くくる',0,2.285,6.02,1.23,ivory)
        text('KUKURU',0,2.25,5.02,.51,ivory)
        text('道\n頓\n堀',side*2.05,2.05,6.08,.42,ivory)
        g.rod(p(2.68,1.45,7.1),p(2.34,1.45,8.59),.038,timber,8)
        ball(2.34,1.45,8.23,.44)
    else:
        # Acchichi's wide white/blue name board and orange sloping awning.
        box(0,.55,4.65,.56,w,3.0,orange)
        sign('元祖大阪たこ焼',0,1.00,5.75,w-.25,.65,yellow,red,.48)
        sign('あっちち本舗',0,1.03,4.86,w-.25,1.08,ivory,blue,.96)
        sign('ACCHICHI HONPO   TAKOYAKI',0,1.03,4.07,w-.25,.43,ivory,blue,.33)
        verts=[p(u,v,z) for u,v,z in [(-w/2,.65,3.82),(w/2,.65,3.82),(w/2,2.1,3.05),(-w/2,2.1,3.05)]]
        g.mesh(verts,[(0,1,2,3),(3,2,1,0)],orange,prefix+' orange awning')
        box(0,2.04,2.96,.16,w,.27,orange)
        for u in [-w/2+.10,0,w/2-.10]:
            g.rod(p(u,.64,3.78),p(u,2.04,3.02),.028,steel,6)
        for j in range(9):
            u=-w*.43+j*w*.1075
            face(u,1.60,2.74,w*.10,.41,ivory)
            text('あ' if j%2 else 'ち',u,1.62,2.74,.21,blue)
        # Rounded lantern-like mascot, puckered mouth and short curled feet.
        cu=-side*2.05
        sphere(cu,1.15,7.12,1.16,.91,1.12,red)
        for j in range(8):
            a=j*math.tau/8;du=math.cos(a);dv=math.sin(a)
            tube([(cu+du*.60,1.15+dv*.48,6.5),(cu+du*1.10,1.15+dv*.83,6.07),(cu+du*1.47,1.15+dv*.97,6.24)],.25,red)
        for u in [cu-.36,cu+.36]:
            sphere(u,1.98,7.34,.24,.11,.31,ivory)
            sphere(u,2.09,7.33,.065,.035,.12,ink)
        sphere(cu,2.08,6.89,.36,.35,.31,red)
        sphere(cu,2.40,6.90,.21,.035,.18,ink)
        sign('道頓堀店',side*1.95,.91,6.78,3.25,.80,ivory,blue,.55)
        sign('鉄板焼き',side*1.95,.91,7.55,3.25,.54,yellow,red,.36)
        for u in [-w*.36,-w*.12,w*.12,w*.36]:sphere(u,1.2,3.45,.095,.095,.095,glow)
    # Only the projected counter needs an extra walking collider. Do not give
    # the overhead awning a ground-level obstruction beside the bridge stairs.
    n['collider'](side*(front-.94),y,.64,w/2,1.43)
