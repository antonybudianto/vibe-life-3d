"""Continuous small paving units and restrained riverside wear, without obstacles."""
import math


def paving_segment(n,side,start,stop,inner=8,outer=19):
    g=n['g'];mat=n['mat']
    palette=[(.24,.235,.24),(.255,.248,.243),(.221,.223,.227),(.268,.261,.25)]
    finishes=[n['paving']]+[mat('promenade stone '+str(i),c,.69) for i,c in enumerate(palette[1:])]
    # The shared base material also covers distant streets outside the UV atlas;
    # its promenade batch is already identified by name in the bake pipeline.
    for m in finishes[1:]:m['walkable_paving']=True
    # The global tile origin remains the same at both extension seams.
    for row in range(math.floor((start-1)/2),math.ceil((stop-1)/2)):
        lo=max(start,1+row*2);hi=min(stop,3+row*2)
        if hi<=lo:continue
        for col in range(math.floor(inner),math.ceil(outer)):
            left=max(inner,col);right=min(outer,col+1)
            key=(row*73+col*37+side*19)%29
            finish=finishes[0 if key<19 else 1+(key%3)]
            g.box((side*(left+right)/2,(lo+hi)/2,-.27),(right-left,hi-lo,.54),finish,name='Dotonbori promenade paving')


def details(n):
    g=n['g'];mat=n['mat'];limit=n['layout']['promenadeEnd']
    stain=mat('river wall mineral stains',(.23,.25,.22),.96)
    damp=mat('river wall waterline',(.13,.18,.15),.88)
    metal=mat('drain covers',(.105,.12,.125),.78,.18)
    for side in [-1,1]:
        for z in [-1.65,-1.38]:
            g.box((side*7.977,0,z),(.018,140,.12 if z<-1.5 else .065),damp)
        for y in range(-67,70,5):
            width=.16+((y*7+side)%5)*.065
            height=.25+((y*3+side)%7)*.11
            g.box((side*7.976,y,-1.02-height*.25),(.018,width,height),stain)
        for y in range(-145,146,11):
            if any(abs(y-b)<10 for b in [-140,-91,-48,0,48,91,140]):continue
            # Flush grates leave the walking routes and stair access unchanged.
            x=side*15.3
            g.box((x,y,.011),(.48,.88,.022),metal)
            for k in range(8):g.box((x,y-.36+k*.10,.026),(.39,.025,.01),n['dark'])
        for y in [-118,-61,-27,31,74,119]:
            x=side*(16.1 if abs(y)<70 else 17.1)
            g.box((x,y,.018),(.85,1.2,.036),metal)
            for off in [-.30,.30]:g.box((x+off,y,.04),(.035,.96,.008),n['silver'])
        # Fine expansion strips divide the long waterfront into unequal sections.
        for y in [-126,-83,-31,25,67,113]:
            if abs(y)<limit:g.box((side*14,y,.010),(9.5,.035,.018),n['joint'])
