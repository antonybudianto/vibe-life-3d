"""TSUTAYA EBISUBASHI: billboard tower over a two-level Starbucks frontage.

Printed surfaces are rectified from the 2023 OSAKA STYLE photograph. Window
reveals, cladding, cabinets, cafe seating and the side return are real meshes.
"""
import math


def build(n,side,y,w,h,front):
    g=n['g'];mat=n['mat'];pos=n['pos'];art=n['artwork']
    dark=n['dark'];silver=n['silver'];glass=n['glass'];white=n['white']
    porcelain=mat('TSUTAYA ivory cladding',(.72,.73,.70),.68)
    steel=mat('TSUTAYA aluminum',(.48,.51,.51),.34,.55)
    wood=mat('Starbucks dark timber',(.095,.071,.047),.78)
    angle=-side*math.pi/2
    def p(u,v,z):return pos(side,y,u,v,z)
    def box(u,v,z,d,ww,hh,m,name=None):g.box(p(u,v,z),(d,ww,hh),m,name=name)
    def face(u,v,z,ww,hh,m):g.panel(p(u,v,z),ww,hh,m,angle)
    box(0,-5.25,h/2,9.5,w,h,porcelain,'TSUTAYA tower shell')
    # Main frontage and a narrow glazed vertical circulation bay to the right.
    boardw=w-3.5;center=-1.3;wing=w/2-1.3
    for floor in range(9):
        z=1.8+floor*3.65
        face(wing,.04,z,2.05,3.25,n['windows'][floor%3] if floor<2 else glass)
        for edge in [-1.08,1.08]:box(wing+edge,.25,z,.5,.13,3.6,steel)
        box(wing,.48,z-1.68,.8,2.5,.24,steel)
        if floor>2:
            face(wing,.10,z-.45,1.9,1.10,n['yellow'])
            box(wing,.14,z-.60,.03,.35,.8,n['blue'])
    # Cafe glazing sits in front of a recessed warm interior, with mullions,
    # continuous window seats, tables and pendant lights at the mezzanine.
    for level,z in enumerate([1.9,6.25]):
        for j in range(8):
            u=center-boardw/2+(j+.5)*boardw/8;bay=boardw/8
            face(u,-.20,z,bay-.10,3.35,n['windows'][(j+level)%3])
            box(u+bay/2,.26,z,.52,.11,3.65,steel)
            box(u,.28,z-.42,.10,bay,.055,steel)
            if level:
                box(u,.03,z-.98,.9,bay-.22,.12,n['wood'])
                box(u,-.22,z-1.46,.5,.64,.12,wood)
                g.rod(p(u,-.12,z-1.75),p(u,-.12,z-1.10),.035,silver,8)
                g.rod(p(u,-.04,z+1.55),p(u,-.04,z+.72),.014,dark,6)
                g.sphere(p(u,-.04,z+.60),(.16,.23,.22),n['warm'],12,8)
        box(center,.15,z-1.78,.6,boardw,.18,porcelain)
    box(center,.45,4.0,.70,boardw,.94,dark,'Starbucks fascia')
    for u,label in [(center-boardw*.23,'STARBUCKS\nCOFFEE'),(center+boardw*.25,'TSUTAYA')]:
        g.text(label,p(u,.82,4.0),.44 if '\n' in label else .76,white,angle,font=n['font'])
    box(center,.72,3.44,1.35,boardw,.18,steel)
    box(center,.28,8.9,.7,boardw,1.0,porcelain)
    photo='dotonbori-tsutaya.jpg';size=(900,1200)
    # Preserve the real billboard typography and its yellow/blue rooftop mark.
    main=art('TSUTAYA EBISUBASHI billboard',[(206,446),(607,220),(633,841),(83,962)],768,1024,photo,size,True)
    roof=art('TSUTAYA rooftop T',[(239,245),(646,0),(659,149),(190,424)],768,384,photo,size,True)
    for z,hh,material in [(19.0,18.8,main),(31.1,5.0,roof)]:
        box(center,.63,z,1.0,boardw+.30,hh+.28,dark,'TSUTAYA billboard cabinets')
        face(center,1.15,z,boardw,hh,material)
        for edge in [-1,1]:box(center+edge*(boardw/2+.1),1.17,z,.12,.13,hh+.22,steel)
        for zz in [z-hh/2-.1,z+hh/2+.1]:box(center,1.18,zz,.15,boardw+.3,.12,steel)
    # Actual green siren logo, mounted over vertical timber beside cafe windows.
    logo=art('Starbucks siren',[(443,982),(568,952),(567,1128),(433,1148)],256,320,photo,size,True)
    logo_u=center+boardw*.35
    box(logo_u,.55,6.27,.28,3.2,3.9,wood,'Starbucks logo backing')
    face(logo_u,.71,6.27,3.02,3.72,logo)
    n['vertical'](side,y,-w/2+.30,10.0,'TSUTAYA',dark,8.5,.80,white)
    # Clad return reveals the depth of the tower above the neighboring roofs.
    yy=y-w/2-.05
    for z in [11+i*3.65 for i in range(6)]:
        g.box((side*(front+4.7),yy,z),(9.5,.32,.22),steel)
        for j in range(6):
            xx=side*(front+.65+j*1.65)
            g.panel((xx,yy-.04,z+1.7),1.48,3.1,porcelain,0)
            g.box((xx,yy-.16,z+1.7),(.075,.20,3.4),steel)
    box(0,-4.6,h+.15,10.2,w+.25,.30,steel)
    for u in [-5,0,5]:
        box(u,-6.2,h+.7,2.1,2.0,1.1,dark)
        for k in range(5):box(u,-5.10,h+.32+k*.16,.08,1.65,.065,steel)
