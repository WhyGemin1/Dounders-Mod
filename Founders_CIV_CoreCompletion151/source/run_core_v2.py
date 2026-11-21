import sys,json,argparse
sys.path.insert(0,'src')
from core_physiology_v2 import UnifiedCoreV2
p=argparse.ArgumentParser()
p.add_argument('--seed',type=int,default=100001)
p.add_argument('--days',type=int,default=30)
p.add_argument('--output')
a=p.parse_args()
sim=UnifiedCoreV2(seed=a.seed)
points={}
for day in range(1,a.days+1):
    sim.step()
    if day in (1,7,30,60,90,180,360,720,1080):
        points[str(day)]={'ledger':sim.host.book.audit(),'physiology':sim.bridge.physiology_report(),
                          'guilds':sim.bridge.guild_summary()}
result={'seed':a.seed,'days':sim.days,'checkpoints':points,
        'ledger':sim.host.book.audit(),'core_v2':sim.report()['core_v2']}
if a.output:
    with open(a.output,'w') as f:json.dump(result,f,indent=2,default=str)
print(json.dumps({'seed':a.seed,'days':sim.days,'ledger':result['ledger'],
                  'physiology':sim.bridge.physiology_report()},default=str))
