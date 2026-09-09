"""Individual central infill, with the CHINTAI neighbor based on a 2021 photo.

The other parcels are architectural interpretations, not surveyed addresses.
Keep the authored setbacks inside the existing building collision envelopes.
"""
import math


def build(n, side, y, w, h, front):
    g=n['g'];mat=n['mat'];pos=n['pos'];panel=n['panel']
    dark=n['dark'];silver=n['silver'];glass=n['glass'];stone=n['stone']
    angle=-side*math.pi/2
    tile=mat('infill biscuit mosaic',(.43,.39,.29),.89)
    plaster=mat('infill weathered plaster',(.43,.46,.45),.88)
    burgundy=mat('infill oxidized bronze',(.105,.059,.046),.62,.24)
    gold=mat('infill brass sign rim',(.65,.38,.055),.43,.58)
    paper=mat('infill ivory lightbox',(.79,.78,.68),.68,0,.38)
    ink=n['black'];wall=tile if side<0 else plaster
    def p(u,v,z):return pos(side,y,u,v,z)
    def box(u,v,z,d,ww,hh,m):g.box(p(u,v,z),(d,ww,hh),m,name='Individual canal infill')
    def face(u,v,z,ww,hh,m):g.panel(p(u,v,z),ww,hh,m,angle)
    signhouse=side==-1
    # Broad asymmetric wall areas and narrow recessed bays replace an office grid.
    box(0,-5.3,h/2,9.3,w,h,wall)
    spine=-w*.34 if signhouse else w*.27
    box(spine,-.18,h/2,.94,w*.21,h,wall)
    levels=[4.8,8.4,12.1,15.8,19.5,23.1] if signhouse else [4.7,8.2,11.8,15.3,18.9,22.4]
    for level,z in enumerate(levels):
        if z>h-1:continue
        for j,u in enumerate([w*.10,w*.34] if signhouse else [-w*.28,-w*.025]):
            ww=w*.205;hh=2.45 if level%3 else 2.1
            lit=(level+j+int(abs(y)))%5==1
            face(u,-.60,z,ww,hh,n['windows'][2] if lit else glass)
            for off in [-ww/2,0,ww/2]:box(u+off,-.14,z,.22,.07,hh+.12,silver)
            for off in [-hh/2,hh/2]:box(u,-.10,z+off,.34,ww+.13,.08,silver)
            # Interrupted balconies, not continuous identical floor bands.
            if (level+j)%3==0:
                box(u,.30,z-hh/2,.95,ww+.28,.17,stone)
                for k in range(7):box(u-ww/2+k*ww/6,.67,z-.65,.045,.045,.92,silver)
                box(u,.67,z-.18,.05,ww+.12,.045,silver)
        if level%2==0:
            u=spine
            box(u,.04,z-.72,.72,1.15,.71,silver)
            for k in range(7):box(u-.45+k*.15,.42,z-.72,.04,.045,.52,dark)
    # Small exterior tiles, vents and rainwater services give the blank wall scale.
    for z in range(4,int(h),2):
        box(0,-.615,z,.02,w,.016,burgundy)
    for u in [-w/2+.28,w/2-.22]:
        g.rod(p(u,.12,.2),p(u,.12,h),.052,silver,8)
        for z in range(2,int(h),4):box(u,.14,z,.18,.19,.05,dark)
    if signhouse:
        # White calligraphy cabinet and a narrow black/gold blade beside CHINTAI.
        # Lettering is newly typeset; the artist's photograph is reference only.
        u=-w*.13;z=15.5;ww=w*.30;hh=17
        box(u,.48,z,.64,ww+.26,hh+.26,silver)
        face(u,.82,z,ww,hh,paper)
        for i,c in enumerate('不滅のミナミ'):
            g.text(c,p(u,.85,z+6.4-i*2.55),2.02,ink,angle,font=n['jp'])
        u=-w*.385
        box(u,1.0,15,.74,w*.18+ .14,22.4,gold)
        face(u,1.39,15,w*.18,22.12,ink)
        g.text('koyo',p(u,1.42,23.4),.53,gold,angle,font=n['font'])
        for i,c in enumerate('高陽社'):g.text(c,p(u,1.42,7.9-i*.83),.65,gold,angle,font=n['jp'])
        panel(side,y,w*.29,h-1.6,w*.38,2.4,paper,'ビル',ink,.9)
    else:
        # Compact service stair enclosure and a single tenant directory.
        for z in [5,8.6,12.2,15.8]:
            if z<h-2:box(spine,-.12,z,.8,w*.2,.27,burgundy)
        panel(side,y,spine,7.7,w*.18,5.6,paper,'珈琲\n食事\n酒場',ink,.56)
        box(-w*.14,.30,3.5,1.05,w*.65,.24,burgundy)
    # Different ground-floor uses: a quiet service entry and one occupied room.
    for j,u in enumerate([-w*.23,w*.23]):
        ww=w*.40
        face(u,-.58,1.65,ww,3.1,n['windows'][2] if j else glass)
        for off in [-ww/2,ww*.15,ww/2]:box(u+off,-.10,1.65,.30,.09,3.15,burgundy)
        if j:
            box(u,-.20,1.02,.6,ww*.75,.12,n['wood'])
            panel(side,y,u,3.5,ww,.56,paper,'川沿い',ink,.4)
        else:
            for z in [.25,.65,1.05,1.45,1.85,2.25,2.65]:box(u,-.40,z,.06,ww,.025,silver)
    box(0,-4.7,h+.15,9.7,w+.08,.30,stone)
    box(0,-.06,h+.57,.22,w,.7,wall)
    box(w*.14,-6.8,h+1.55,3.8,w*.38,2.6,burgundy)
    for u in [-w*.22,w*.25]:box(u,-3,h+.7,1.65,1.5,1.05,silver)
    return 'photographed sign house' if signhouse else 'asymmetric canal infill'
