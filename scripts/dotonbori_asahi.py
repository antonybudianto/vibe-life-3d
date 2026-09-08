"""The photographed Asahi corner building: ribbon windows and a wrapped cabinet."""
import math


def build_asahi(n,side,y,w,h,front):
    g=n['g'];mat=n['mat'];pos=n['pos'];panel=n['panel'];artwork=n['artwork']
    silver=n['silver'];dark=n['dark'];glass=n['glass'];white=n['white'];red=n['neonred']
    aluminum=mat('Asahi anodized aluminum',(.34,.36,.36),.39,.48)
    spandrel=mat('Asahi gray spandrels',(.29,.285,.265),.68,.18)
    gold=mat('Asahi gold cabinet',(.95,.58,.025),.34,.34)
    angle=-side*math.pi/2;podium=14.9;bottom=15.3;top=h-.25
    def p(u,v,z):return pos(side,y,u,v,z)
    def box(u,v,z,depth,width,height,m,name=None):g.box(p(u,v,z),(depth,width,height),m,name=name)
    box(0,-5.1,podium/2,10,w,podium,spandrel,'Asahi corner podium')
    # Continuous metal floor bands and narrow ribbon windows turn the corner.
    for floor in range(6):
        z=1.42+floor*2.35
        box(0,.08,z-1.07,.52,w+.12,.28,aluminum)
        box(0,.20,z+.89,.22,w+.27,.15,silver)
        box(0,.16,z-.87,.22,w+.20,.14,dark)
        for j in range(7):
            u=-w/2+.33+(j+.5)*(w-.66)/7;bay=(w-.66)/7
            lit=(floor+j)%4!=0
            g.panel(p(u,.015,z),bay-.09,1.68,n['windows'][(floor+j)%3] if lit else glass,angle)
            box(u+bay/2,.27,z,.34,.075,1.85,dark)
            box(u,.25,z+.22,.12,bay,.052,aluminum)
            if lit and floor<3:
                box(u,-.08,z-.62,.38,bay*.75,.065,n['wood'])
        # West-facing return is visible from Ebisubashi and Glico.
        yy=y+w/2+.035
        for j in range(7):
            xx=side*(front+.62+(j+.5)*9.3/7)
            g.panel((xx,yy,z),9.3/7-.10,1.68,n['windows'][(j+floor+1)%4] if (j+floor)%3 else glass,math.pi)
            g.box((xx,yy+.12,z+.22),(9.3/7,.11,.052),aluminum)
            g.box((xx+9.3/14,yy+.12,z),(.075,.25,1.87),dark)
        g.box((side*(front+5.05),yy+.10,z-1.07),(9.9,.48,.28),aluminum)
        g.box((side*(front+5.05),yy+.20,z+.89),(10.05,.15,.15),silver)
    for u in [-w/2+.1,w/2-.1]:box(u,.27,podium/2,.42,.20,podium,aluminum)
    box(0,-4.7,podium+.07,10.4,w+.40,.32,dark,'Asahi billboard plinth')
    box(0,-4.7,podium+.27,10.5,w+.45,.14,silver)
    # The reference is projectively rectified separately on each real 3D face.
    # Pixel coordinates refer to the original 1300 x 866 photograph.
    photo='dotonbori-asahi-cruise.jpg'
    face=artwork('Asahi photo front',[(532,152),(679,192),(680,435),(530,413)],512,1024,photo,(1300,866),True)
    turn=artwork('Asahi photo return',[(444,224),(529,153),(529,412),(439,449)],512,1024,photo,(1300,866),True)
    center=(bottom+top)/2;height=top-bottom
    box(0,-4.60,center,10.0,w,height,gold,'Asahi wraparound cabinet')
    g.panel(p(0,.435,center),w-.10,height-.06,face,angle)
    g.panel((side*(front+4.55),y+w/2+.038,center),9.83,height-.06,turn,math.pi)
    for u in [-w/2,w/2]:g.rod(p(u,.47,bottom),p(u,.47,top),.047,silver,10)
    for z in [bottom,top]:
        box(0,.43,z,.16,w+.15,.12,silver)
        g.box((side*(front+4.55),y+w/2+.08,z),(10.0,.15,.12),silver)
    # Ribbed aluminum service return, vents and braced roof cap.
    for z in [17,19.7,22.4,25.1,27.8,30.5]:
        g.box((side*(front+9.2),y-w/2-.10,z),(1.7,.27,.22),white)
        g.box((side*(front+9.2),y-w/2-.10,z-.34),(1.45,.23,.18),dark)
    box(0,-4.60,h,10.2,w+.20,.22,aluminum)
    for u in [-w*.34,0,w*.34]:
        g.rod(p(u,-1.3,h+.08),p(u,-2.6,h+.95),.055,dark,8)
        box(u,-2.6,h+1.0,1.0,1.25,.22,silver)
    # Small Japanese tenants and a traditional entrance sit below the billboard.
    n['vertical'](side,y,w/2-.48,9.2,'本場の味 かに道楽',white,9.1,.61,n['black'])
    for u,label in [(-w*.27,'かに道楽'),(w*.25,'道頓堀')]:
        panel(side,y,u,3.66,w*.43,.64,white,label,red,.50)
    box(0,.58,3.11,1.05,w-.45,.15,dark)
    for u in [-w*.26,w*.26]:
        g.panel(p(u,.21,1.38),1.55,2.55,glass,angle)
        for edge in [-.78,0,.78]:box(u+edge,.34,1.38,.14,.065,2.6,silver)
    for u in [-2.8,-1.4,0,1.4,2.8]:
        g.rod(p(u,.45,podium+.3),p(u,1.08,podium+.75),.035,dark,8)
        g.box(p(u,1.08,podium+.75),(.22,.36,.18),white)
    # The narrow side street exposes the advertising return, as in the photo.
    lane=y+w/2+2.0
    g.box((side*24,lane,-.07),(13,3.9,.12),n['paving'])
    g.box((side*30,lane,2.2),(1.2,3.85,4.4),spandrel)
    g.panel((side*29.35,lane,1.7),2.8,3.2,n['windows'][1],angle)
    for u in [-1.5,1.5]:g.box((side*28.9,lane+u,1.6),(.20,.14,3.2),n['red'])
    g.box((side*28.9,lane,3.1),(.65,3.5,.18),n['red'])
    for u in [-1.2,-.6,0,.6,1.2]:g.sphere((side*28.6,lane+u,2.9),(.13,.16,.22),n['warm'],10,6)
