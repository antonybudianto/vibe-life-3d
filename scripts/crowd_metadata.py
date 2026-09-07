"""Reproducible crowd personalities; no model rebuild needed for walking behavior."""
import random

def people_metadata():
    rng=random.Random(109)
    coats=['#a5aaa1','#29404b','#796151','#bfa875','#464f39','#bbb7af','#41464e','#9c655b']
    people=[]
    for region,count in enumerate([18,12,22,22]):
        for i in range(count):
            people.append({'region':region,'crosses':i<4,'offset':rng.random(),'speed':round(rng.uniform(1.08,1.58),3),'scale':round(rng.uniform(.86,1.07),3),'coat':coats[len(people)%len(coats)]})
    return people

if __name__=='__main__':
    import json
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'public/models/crossing-life.json'
    data=json.loads(path.read_text());data['people']=people_metadata();path.write_text(json.dumps(data,indent=2)+'\n')
