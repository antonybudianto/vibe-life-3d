"""Real photographed advertising next to Glico, on modeled sign cabinets."""
import math


def snow_brand(n):
    g=n['g'];pos=n['pos'];art=n['artwork'];silver=n['silver'];dark=n['dark']
    side=-1;y=11.5;u=-6.5;width=5.8
    def p(v,z):return pos(side,y,u,v,z)
    photo='dotonbori-asahi-cruise.jpg'
    signs=[
        ('Snow Brand blue logo',27.0,8.5,[(744,156),(855,84),(855,255),(743,306)]),
        ('Snow Brand yellow 6P cheese',17.0,11.2,[(742,313),(850,262),(852,478),(741,506)]),
        ('Snow Brand blue tagline',10.0,2.4,[(741,512),(855,484),(855,528),(741,550)]),
    ]
    g.box(p(.51,20.0),(.64,width+.38,23.0),dark,name='Snow Brand sign cabinet')
    for label,z,height,corners in signs:
        artwork=art(label,corners,512,768 if height>4 else 256,photo,(1300,866),True)
        g.panel(p(.91,z),width,height,artwork,-side*math.pi/2)
        for zz in [z-height/2-.08,z+height/2+.08]:
            g.box(p(.96,zz),(.14,width+.24,.12),silver)
        for edge in [-1,1]:
            g.box(pos(side,y,u+edge*(width/2+.07),.93,z),(.13,.11,height+.18),silver)
    for z in [11.4,22.8,31.4]:
        for du in [-2.1,0,2.1]:
            g.rod(pos(side,y,u+du,.98,z),pos(side,y,u+du,1.40,z+.23),.025,silver,6)
            g.box(pos(side,y,u+du,1.42,z+.25),(.22,.42,.13),dark)
