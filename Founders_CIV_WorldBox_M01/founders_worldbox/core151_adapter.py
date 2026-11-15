"""Read-only export from *real* Core151; creates no game-side entities."""
from __future__ import annotations
from pathlib import Path
import sys

TRAIT_NAMES=('basal','digestion','locomotion','endurance','sense','intake','vigilance','reproductive')

def core151_snapshot(source_dir: str|Path,seed: int=100001):
    """source_dir points at extracted Founders_CIV_CoreCompletion151/source."""
    src=Path(source_dir).resolve()
    for d in (src,src/'src',src/'world023024'):
        if not d.exists():raise FileNotFoundError(f'Core151 source folder missing: {d}')
        if str(d) not in sys.path:sys.path.insert(0,str(d))
    from unified_foraging_151 import UnifiedRegulatedForaging151
    sim=UnifiedRegulatedForaging151(seed=seed)
    if not (sim.host.book is sim.bridge.book is sim.bridge.tree.book):
        raise AssertionError('Core151 Book ownership violation')
    book=sim.host.book
    audit=book.audit()
    if audit['rejections']:raise AssertionError('Core151 Book rejections')
    actors=[]
    for actor in sim.bridge.actors.values():
        phenotype=sim.bridge._trait(actor)
        actors.append({'civ_actor_id':actor.id,'species':actor.species,
            'generation':actor.generation,'parent_ids':list(actor.parent_ids),
            'traits':{k:float(getattr(phenotype,k)) for k in TRAIT_NAMES},
            'alive':actor.alive,'age':actor.age,'sex':actor.sex})
    return {'engine':'UnifiedRegulatedForaging151','seed':seed,'day':sim.days,
        'founder_count':len(sim.host.sim.founders.people),
        'book_shared':True,'book_rejections':audit['rejections'],
        'actor_count':len(actors),'actors':actors}

def shadow_compare(registry,world_id:str,core_state:dict):
    """Compare identity/lineage only. WorldBox nutrition uses uncalibrated units."""
    core={a['civ_actor_id']:a for a in core_state['actors']}
    links=registry.links(world_id)
    mapped_native_to_core={a['native_actor_id']:a['core_actor_id'] for a in links}
    findings=[]
    for link in links:
        c=core.get(link['core_actor_id'])
        if c is None:
            findings.append({'core_actor_id':link['core_actor_id'],'issue':'not_in_core151_snapshot'})
            continue
        if c['species']!=link['core_species']:
            findings.append({'core_actor_id':c['civ_actor_id'],'issue':'species_mismatch'})
        raw=link['last_native_json']
        if raw:
            n=__import__('json').loads(raw)
            if n['generation'] is not None and n['generation']!=c['generation']:
                findings.append({'core_actor_id':c['civ_actor_id'],'issue':'generation_mismatch',
                       'worldbox_generation':n['generation'],'core_generation':c['generation']})
            native_parents={v for v in (n['parent_id_1'],n['parent_id_2']) if v not in (None,'0','-1','')}
            mapped_parents={mapped_native_to_core[p] for p in native_parents if p in mapped_native_to_core}
            expected=set(c['parent_ids'])
            if mapped_parents and not mapped_parents.issubset(expected):
                findings.append({'core_actor_id':c['civ_actor_id'],'issue':'mapped_parent_mismatch'})
    return {'total_links':len(links),'compared':len(links)-sum(i['issue']=='not_in_core151_snapshot' for i in findings),
            'issues':findings,'note':'Shadow comparison only; neither game state nor Book is changed. WorldBox native nutrition is not assumed to be Core151 fuel.'}
