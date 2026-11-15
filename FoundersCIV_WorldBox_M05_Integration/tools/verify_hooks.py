#!/usr/bin/env python3
"""Verify observer hook targets against the uploaded native WorldBox assembly."""
import sys,json,hashlib,argparse
from pathlib import Path
from inspect_assembly import Reader

EXPECTED={
  'Actor.addNutritionFromEating':('int32','bool','bool'),
  'ai.behaviours.BehConsumeActorTarget.consume':('Actor','Actor'),
  'Actor.consumeFoodResource':('ResourceAsset',),
  'Actor.newKillAction':('Actor','Kingdom','AttackType'),
  'Actor.die':('bool','AttackType','bool','bool'),
  'ActorManager.createBabyActorFromData':('ActorData','WorldTile','*'),
  'Actor.birthEvent':('string','string'),
  'Actor.getNutrition':(),
  'Actor.hasDied':(),
  'BaseSimObject.getID':()
}

def verify(path):
    a=Reader(path)
    def typ(t):
        if '#' not in t:return t
        left,right=t.split('#',1)
        try:
            token=int(right); tag=token&3; rid=token>>2
            if tag==0 and rid>0 and rid<=len(a.types):return a.types[rid-1]['name']
        except ValueError:pass
        return t
    results=[]
    for name,expected in EXPECTED.items():
        matches=[m for m in a.methods if m.get('owner','')+'.'+m['name']==name]
        matches=[m for m in matches if len((m.get('sig') or {}).get('params',[]))==len(expected)]
        if not matches:results.append({'target':name,'verified':False,'reason':'method missing'});continue
        found=None
        for m in matches:
            actual=tuple(typ(x) for x in m['sig']['params'])
            if all(e=='*' or e==got for e,got in zip(expected,actual)):
                found=m;break
        if found is None:
            results.append({'target':name,'verified':False,'reason':'signature mismatch',
                            'actual_signatures':[m['sig']['params'] for m in matches]});continue
        results.append({'target':name,'verified':True,'rva_hex':hex(found['rva']),
                        'method_rid':found['rid'],'return_type':typ(found['sig']['return']),
                        'parameter_types':[typ(x) for x in found['sig']['params']]})
    return {'assembly_name':a.path.name,'assembly_sha256':hashlib.sha256(a.b).hexdigest(),
            'metadata_types':len(a.types),'metadata_methods':len(a.methods),
            'all_targets_verified':all(r['verified'] for r in results),
            'targets':results,
            'scope':'metadata signature check only; not a C# compile or runtime Harmony attachment test'}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('assembly');ap.add_argument('--output');a=ap.parse_args()
    result=verify(a.assembly)
    text=json.dumps(result,indent=2)
    print(text)
    if a.output:Path(a.output).write_text(text,encoding='utf-8')
    sys.exit(0 if result['all_targets_verified'] else 2)
