"""Cycle108: event-grounded generational audit for HabitatBridge cohorts.
Initial animals are G0; offspring of G0 are G1; offspring of G1 are G2.
Maturity threshold is the bridge's strict age >80 rule, not a nonexistent attribute.
"""
def generation_metrics(bridge):
    actors=bridge.actors
    generations={}
    visiting=set()
    def generation(actor_id):
        if actor_id in generations:return generations[actor_id]
        if actor_id in visiting:raise ValueError('cyclic parent lineage')
        visiting.add(actor_id)
        actor=actors[actor_id]
        if actor.parent is None:gen=0
        elif actor.parent not in actors:raise ValueError('missing parent')
        else:gen=1+generation(actor.parent)
        visiting.remove(actor_id)
        generations[actor_id]=gen
        return gen
    for actor_id in actors:generation(actor_id)
    births=[e for e in bridge.events if e.get('event')=='birth']
    return {
        'g1_adults':sum(a.alive and generation(a.id)==1 and a.age>80 for a in actors.values()),
        'g1_living':sum(a.alive and generation(a.id)==1 for a in actors.values()),
        'g2_births':sum(generation(e['actor'])>=2 for e in births),
        'g1_births':sum(generation(e['actor'])==1 for e in births),
        'birth_events':len(births),
        'generations_present':sorted(set(generations.values())),
    }
