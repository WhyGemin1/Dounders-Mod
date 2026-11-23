"""Read-only, conservative pregnancy cohort classification from ordered event logs."""
from collections import Counter

def cohort_outcomes(events, observation_day, species=None):
    """Do not infer miscarriage from missing birth records or death events."""
    pending={}; outcomes=[]; counts=Counter()
    for index,event in enumerate(events):
        if not isinstance(event,dict): continue
        if species is not None and event.get("species") != species: continue
        day=event.get("day")
        if isinstance(day,(int,float)) and day>observation_day: continue
        kind=event.get("kind",event.get("type",event.get("event")))
        mother=event.get("mother")
        if kind=="conception" and mother is not None:
            if mother in pending:
                outcomes.append({**pending.pop(mother),"outcome":"superseded_unresolved"});counts["superseded_unresolved"]+=1
            pending[mother]={"mother":mother,"due":event.get("due"),"conception_index":index}
        elif kind=="birth" and mother in pending:
            outcomes.append({**pending.pop(mother),"outcome":"recorded_birth","birth_index":index});counts["recorded_birth"]+=1
        elif kind=="death":
            actor=event.get("actor")
            if actor in pending:
                outcomes.append({**pending.pop(actor),"outcome":"maternal_death_no_recorded_birth","death_index":index});counts["maternal_death_no_recorded_birth"]+=1
    for item in pending.values():
        due=item["due"]
        status="overdue_no_recorded_birth" if isinstance(due,(int,float)) and observation_day>due else "pending_or_due_unknown"
        outcomes.append({**item,"outcome":status});counts[status]+=1
    return {"counts":dict(counts),"cohorts":outcomes,"observation_day":observation_day}
