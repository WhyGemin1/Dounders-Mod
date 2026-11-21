"""Read-only, event-order-aware ridge-hound reproductive cohort audit."""
from collections import Counter

def audit_reproduction_events(events, actors=None):
    counts=Counter(); causes=Counter(); deaths_by_sex=Counter(); conceptions={}; births_by_mother=Counter(); transitions=[]; open_pregnancies={}
    for index,e in enumerate(events):
        if not isinstance(e,dict): continue
        kind=e.get("kind",e.get("type",e.get("event")))
        if kind not in ("death","conception","birth","mate_cue_move","mate_search_move"): continue
        counts[kind]+=1
        if kind=="death" and e.get("species")=="ridge_hound":
            causes[e.get("cause") or "unknown"]+=1
            actor=(actors or {}).get(e.get("actor"))
            deaths_by_sex[getattr(actor,"sex","unknown")]+=1
        if kind=="conception":
            mother=e.get("mother");conceptions[mother]=e.get("due")
            if mother is not None: open_pregnancies[mother]={"due":e.get("due"),"event_index":index}
        if kind=="birth":
            mother=e.get("mother")
            if mother is not None:
                births_by_mother[mother]+=1
                if mother in open_pregnancies: del open_pregnancies[mother]
        transitions.append({"index":index,"kind":kind,"actor":e.get("actor"),"mother":e.get("mother"),"day":e.get("day")})
    return {"events":dict(counts),"hound_death_causes":dict(causes),"hound_deaths_by_sex":dict(deaths_by_sex),"conception_due_dates":conceptions,"births_by_mother":dict(births_by_mother),"unresolved_conceptions":open_pregnancies,"timeline":transitions}
