import json,sys
from experiment_cycle136 import make_sim,summarize136
from juvenile_transition_cycle138 import enable_transition_support
results=[]
for arm in ('baseline','dependent','transition'):
 s,c=make_sim(9711,arm=='dependent')
 if arm=='transition':enable_transition_support(s)
 for _ in range(30):s.step()
 x=summarize136(s,30,c)
 results.append({'arm':arm,'day':30,'living':x['living'],'g1_births':x['g1_births'],'g2_births':x['g2_births'],'book_rejections':x['book_rejections'],'tree_state':x['tree_state'],'transition_metrics':dict(getattr(s.bridge,'juvenile_transition_metrics',{}))})
print(json.dumps(results,indent=2))
