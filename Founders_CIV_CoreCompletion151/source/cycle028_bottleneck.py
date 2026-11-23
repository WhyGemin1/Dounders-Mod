"""Observational reproductive bottleneck classifier; no model mutations."""
def classify(rows):
    previous=None; observed=[]
    for row in rows:
        day=int(row['day'])
        if previous is not None and day<=previous: raise ValueError('Days must be strictly increasing')
        previous=day
        if day>=40: observed.append(row)
    def first(field):
        return next((r['day'] for r in observed if r.get(field,0)>0),None)
    return {'breeding_observed_days':len(observed),
      'first_day_with_funded_colocation':first('colocated_funded_pairs'),
      'last_day_with_living_male':next((r['day'] for r in reversed(observed) if r.get('male',0)>0),None),
      'first_day_with_birth':first('births')}
