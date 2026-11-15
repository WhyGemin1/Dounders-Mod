import sys,pickle,json,hashlib
sys.path.insert(0,'src')
from integrated_02188 import Unified288
args=dict(seed=9711,reproductive_ecology=True,juvenile_foraging=True,capacity_scale=.5,growth_allocation=True,dependent_nutrition=True)
s=Unified288(**args)
for _ in range(30):s.step()
with open('/mnt/data/cycle088/publish/selected_checkpoint.pkl','wb') as f:pickle.dump(s,f)
for _ in range(150):s.step()
a=s.host.book.audit(); summary=lambda x:(x.days,sum(z.alive for z in x.bridge.actors.values()),x.bridge.stats['birth'],x.host.book.audit()['mass_error'],x.host.book.audit()['energy_error'])
with open('/mnt/data/cycle088/publish/selected_checkpoint.pkl','rb') as f:t=pickle.load(f)
for _ in range(150):t.step()
result={'restored':summary(t),'uninterrupted':summary(s),'match':summary(t)==summary(s)}
open('/mnt/data/cycle088/publish/replay.json','w').write(json.dumps(result,indent=2));print(result)
