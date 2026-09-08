"""Parcel-specific canal architecture, authored as real Blender meshes.

The four concept boards are art direction rather than consistent geography.
Keep the established landmark positions and playable promenade, but give each
landmark its own building, with no generic advertising underneath its cabinet.
"""
import math


def build(n):
    g=n['g'];mat=n['mat'];pos=n['pos'];panel=n['panel'];vertical=n['vertical']
    dark=n['dark'];silver=n['silver'];glass=n['glass'];wood=n['wood']
    white=n['white'];red=n['neonred'];cream=n['cream'];warm=n['warm']
    blue=n['blue'];yellow=n['yellow'];windows=n['windows'];jp=n['jp']
    stone=n['stone'];rail=n['rail'];collider=n['collider']
    tile=mat('pearl ceramic',(.43,.46,.48),.6)
    grout=mat('ceramic joints',(.20,.24,.27),.9)
    concrete=mat('cool concrete',(.32,.35,.39),.84)
    bronze=mat('bronze window frames',(.12,.072,.034),.37,.55)
    brick=mat('warm terracotta',(.24,.12,.08),.86)
    slate=mat('slate cladding',(.085,.115,.16),.68)
    cladding=[tile,concrete,brick,slate,n['facades'][3],n['facades'][0]]
    # Center, frontage, height, architecture family, reserved landmark.
    parcels={
        -1:[(-65,9.6,22,0,''),(-55.5,8.8,28,2,''),(-45,11.8,25,1,''),
            (-34.5,8.7,31,3,''),(-25,9.6,24,2,''),(-15,9.7,34,0,'estem'),
            (-5,9.7,32,3,'promise'),(7,13.7,34,1,'glico'),(20,11.7,32,2,'asahi'),
            (29,5.7,25,0,''),(38,11.7,29,3,''),(48.5,8.7,23,2,''),
            (58,9.7,29,1,''),(66.5,6.7,21,0,'')],
        1:[(-65,9.6,27,1,''),(-55,9.7,22,0,''),(-44.5,10.7,31,3,''),
           (-34,9.7,25,2,''),(-24.5,8.7,29,0,''),(-16,7.7,27,2,'fugu'),
           (-7,9.7,34,3,'ohsho'),(7,17.7,28,4,'kani'),(21,9.7,24,2,''),
           (29.5,6.7,31,1,''),(38,9.7,31,3,'wheel'),(48.5,10.7,26,0,''),
           (59,9.7,30,2,''),(67,5.7,22,1,'')]
    }
    labels=['串かつだるま','道頓堀横丁','炭火焼肉','お好み焼','珈琲浪漫','らーめん','寿司処','居酒屋']
    report=[]
    for side,rows in parcels.items():
        for idx,(y,w,h,style,hero) in enumerate(rows):
            front=19+[.15,.65,-.12,.35][(idx+(side+1))%4]
            n['frontages'][side,y]=front
            wall=cladding[style]
            def box(u,v,z,depth,width,height,m):
                g.box(pos(side,y,u,v,z),(depth,width,height),m)
            angle=-side*math.pi/2
            # Opaque core is set behind the glazing, leaving real window reveals.
            box(0,-5.3,h/2,9.3,w,h,wall)
            collider(side*(front+5),y,5.9,w/2,h)
            for u in [-w/2+.14,w/2-.14]:box(u,-.1,h/2,1.5,.28,h,wall)
            # Every family has its own floor rhythm and bay count.
            floor=[3.05,3.5,2.85,3.3,3.15][style]
            bay_count=max(2,round(w/[2.2,3.1,2.7,2.35,3.0][style]))
            usable=w-.70;bay=usable/bay_count
            for level in range(1,int((h-1)/floor)):
                z=4.3+(level-.5)*floor
                if z+floor/2>h:break
                box(0,-.1,z-floor/2,1.35,w,.30 if style!=3 else .56,wall)
                box(0,.24,z-floor/2-.08,.16,w+.12,.09,bronze if style==2 else silver)
                for j in range(bay_count):
                    u=-usable/2+(j+.5)*bay;ww=bay-.24;hh=floor-.55
                    # Suppress bright windows behind huge opaque landmark prints.
                    covered=(hero=='glico' and abs(u)<4.6 and z>6) or (hero in ['promise','estem'] and z>15) or (hero=='asahi' and z>16)
                    lit=not covered and (level<4 or (j+level*3+idx)%5<2)
                    interior=windows[(j+idx+level)%3] if lit else glass
                    g.panel(pos(side,y,u,-.57,z),ww,hh,interior,angle)
                    for edge in [-1,1]:box(u+edge*bay/2,-.12,z,1.15,.14,hh+.25,bronze if style==2 else wall)
                    box(u,.07,z-hh/2,.40,ww+.15,.13,stone)
                    # Transoms, slim mullions, a recessed sill, and interior furniture.
                    box(u,.02,z+.26,.12,ww,.06,bronze if style==2 else dark)
                    if style in [0,1,3]:box(u,.02,z,.12,.065,hh,dark)
                    if lit and level<4:
                        box(u,-.17,z-.64,.63,ww*.65,.10,wood)
                        for off in [-ww*.22,ww*.22]:
                            box(u+off,-.14,z-.94,.27,.09,.57,dark)
                        g.sphere(pos(side,y,u,-.27,z+.7),(.12,.17,.10),warm,8,5)
                        if (idx+j)%3==0:
                            g.sphere(pos(side,y,u+ww*.2,-.31,z-.05),(.12,.14,.17),n['skin'],8,5)
                            box(u+ww*.2,-.33,z-.40,.17,.32,.50,n['coats'][(idx+j)%6])
                if style==0:
                    # Ceramic panel seams, visible independently of the signs.
                    for u in range(math.ceil(-w/2),math.floor(w/2)+1):box(u,.18,z-floor/2,.035,.014,.27,grout)
            # Individual ground-floor restaurant, with two or three entrances.
            shops=3 if w>12 else 2
            shopw=(w-.6)/shops
            name={'kani':'かに道楽','glico':'道頓堀商店','promise':'たこ焼 道頓堀','asahi':'道頓堀ビアホール','fugu':'づぼらや','ohsho':'大阪王将','wheel':'ドン・キホーテ','estem':'大阪案内所'}.get(hero,labels[idx%len(labels)])
            for shop in range(shops):
                u=(shop-(shops-1)/2)*shopw
                g.panel(pos(side,y,u,-.57,1.70),shopw-.18,3.2,windows[(idx+shop)%3],angle)
                for j in range(5):
                    uu=u-shopw/2+.15+j*(shopw-.30)/4
                    box(uu,.12,1.6,.30,.07,3.1,wood if style in [2,4] else bronze)
                box(u,.12,.44,.32,shopw,.14,wood)
                box(u,-.04,1.03,.74,shopw*.72,.12,wood)
                # Menus and a short noren curtain give entrances a distinct silhouette.
                panel(side,y,u,3.83,shopw-.22,.98,white if (idx+shop)%2 else red,name,n['neonred'] if (idx+shop)%2 else white,.72)
                for k in range(3):
                    uu=u+(k-1)*.42
                    g.panel(pos(side,y,uu,.31,2.73),.40,.62,n['blue'] if style%2 else n['red'],angle)
                panel(side,y,u+shopw*.32,1.65,.44,.78,cream,'献立',n['black'],.19)
                box(u,.58,3.27,1.5,shopw+.02,.18,dark)
                if style in [2,4] or hero:
                    for k in range(max(3,int(shopw/.65))):
                        uu=u-shopw/2+.4+k*.65
                        g.sphere(pos(side,y,uu,.95,2.96),(.17,.19,.28),warm,10,7)
                else:
                    # Sloped fabric canopy, not the same lantern fascia everywhere.
                    v=[pos(side,y,u+a,b,z) for a,b,z in [(-shopw/2,.35,3.35),(shopw/2,.35,3.35),(shopw/2,1.3,2.98),(-shopw/2,1.3,2.98)]]
                    g.mesh(v,[(0,1,2,3),(3,2,1,0)],n['red'] if style==0 else cream)
            # Reserve landmark surfaces; other parcels use authored sign layouts.
            edge=side*(w/2-1.02)
            if not hero:
                layout=idx%4
                if layout==0:
                    vertical(side,y,edge,13.6,labels[idx%8],white,14,1.55)
                    for k in range(3):panel(side,y,-side*w*.15,6.7+k*3.6,w*.52,1.65,[red,blue,white][k],labels[(idx+k+2)%8],white if k<2 else red,.82)
                elif layout==1:
                    vertical(side,y,-edge,15.4,labels[(idx+1)%8],red,17,1.85)
                    panel(side,y,side*.8,h-3.8,w*.55,4.5,yellow,'串かつ',n['black'],1.6)
                    panel(side,y,side*.8,8,w*.51,1.2,white,'焼肉・ビール',red,.65)
                elif layout==2:
                    vertical(side,y,edge,12.2,labels[idx%8],yellow,11,1.55)
                    for k in range(5):panel(side,y,-edge,6.5+k*3.4,1.32,2.6,[white,red,blue][k%3],['焼\n肉','寿\n司','珈\n琲'][k%3],red if k%3==0 else white,.72)
                    panel(side,y,0,h-3.2,w*.80,2.1,red,'お好み焼 道頓堀',white,.80)
                else:
                    vertical(side,y,-edge,16.0,'大阪王将',red,16,2.05)
                    vertical(side,y,edge,10.5,'串かつだるま',white,9,1.5)
                    panel(side,y,0,h-3,w*.72,3.8,blue,'道頓堀',white,1.3)
                # Double-sided blade sign on brackets, readable along the canal.
                u=-side*(w/2-.28);v=1.08;z=6.5+idx%3*1.4
                box(u,v,z,1.4,.22,2.65,dark)
                for facing in [-1,1]:
                    p=pos(side,y,u+facing*.13,v,z)
                    g.panel(p,1.3,2.5,white,0 if facing<0 else math.pi)
                    g.text('酒\n場',(p[0],p[1]+facing*.018,p[2]),.72,red,0 if facing<0 else math.pi,font=jp)
            elif hero=='ohsho':
                vertical(side,y,-side*2.6,18,'大阪王将',red,21,2.35)
                vertical(side,y,side*3.4,15,'串かつだるま',white,15,1.6)
                panel(side,y,.3,28,4.7,4.0,yellow,'餃子',n['black'],1.65)
            elif hero=='fugu':
                vertical(side,y,side*2.8,12.5,'づぼらや',white,15,1.5)
                panel(side,y,0,7.2,4.5,1.8,red,'ふぐ料理',white,.9)
            elif hero=='kani':
                vertical(side,y,-6.8,14.8,'かに道楽',white,19,2.0)
                # Continuous traditional timber wing and pale ribbed upper wall.
                for u in [i*.28-7.8 for i in range(57)]:box(u,.22,18.3,.19,.065,8.9,cream)
                for z in [6,13.6,23.1]:box(0,.4,z,1.25,w,.22,wood)
            elif hero=='glico':
                vertical(side,y,-5.85,18.5,'道頓堀の味',red,19,1.25)
                vertical(side,y,5.85,18,'なにわ名物',white,18,1.18)
            elif hero=='asahi':
                vertical(side,y,side*4.7,18.5,'本場の味',white,19,1.5)
            elif hero=='wheel':
                vertical(side,y,-3.8,17,'ドン・キホーテ',red,23,1.65)
            if hero in ['promise','asahi','estem']:
                # Tenant fascias sit between the glazed podium floors and the
                # campaign cabinets, as in the concept's layered restaurant fronts.
                panel(side,y,0,10.8,w*.72,.76,red,'居酒屋・串かつ・生ビール',white,.57)
                panel(side,y,0,14.05,w*.72,.82,white,'道頓堀 うまいもん横丁',red,.62)
            # A solid parapet, inset penthouse, service yard and side elevations.
            box(0,-4.5,h+.10,10,w+.12,.24,stone)
            box(0,-.08,h+.48,.25,w,.72,wall)
            box(w*.14,-6.4,h+1.6,3.5,w*.46,3.1,cladding[(style+1)%6])
            box(w*.14,-6.4,h+3.22,3.75,w*.48,.18,silver)
            rail((side*(front+1.25),y-w/2+.2),(side*(front+1.25),y+w/2-.2),h+.2)
            for k in range(2+idx%2):
                u=-w*.3+k*1.7
                box(u,-2.8,h+.65,1.6,1.2,1.0,silver)
                for slat in range(6):box(u-.46+slat*.18,-1.985,h+.67,.04,.075,.7,dark)
                g.rod(pos(side,y,u,-3.2,h+1.1),pos(side,y,u,-3.2,h+2.1),.13,silver,10)
            for back in [2.0,6.0]:
                for end in [-1,1]:
                    yy=y+end*(w/2+.025)
                    for z in range(6,int(h)-1,4):
                        g.panel((side*(front+back),yy,z),1.15,1.55,glass,0 if end<0 else math.pi)
            g.rod(pos(side,y,w*.35,-7,h),pos(side,y,w*.35,-7,h+4.8),.035,silver,6)
            report.append(dict(side=side,center=y,width=w,height=h,front=front,family=style,landmark=hero))
    return report
