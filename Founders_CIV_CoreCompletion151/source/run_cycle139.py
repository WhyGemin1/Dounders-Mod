import json,sys
from experiment_cycle136 import make_sim,summarize136
from energy_conservation_cycle139 import enable_conservation
rows=[]
for seed in (9711,9712):
 for arm in ('baseline','conservation'):
  s,c=make_sim(seed,False)
  if arm=='conservation':enable_conservation(s)
  for day in range(1,61):
   s.step()
   if day in (30,60):
    x=summarize136(s,day,c)
    rows.append({'seed':seed,'arm':arm,'day':day,'living':x['living'],'g1_births':x['g1_births'],'g2_births':x['g2_births'],'book_rejections':x['book_rejections'],'tree_state':x['tree_state']})
print(json.dumps(rows,indent=2))
