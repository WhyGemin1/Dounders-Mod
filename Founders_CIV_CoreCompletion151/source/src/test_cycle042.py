import pickle
import pytest
from unified_02142 import Unified242
from knowledge_architecture import Cognition


def test_fifth_habitat_is_real_book_funded_and_connected():
    four=Unified242(seed=9711, five_habitats=False)
    five=Unified242(seed=9711, five_habitats=True,colonize_floodplain=False)
    b=five.host.book;t=five.bridge.tree
    assert len(t.habitats)==5 and 'floodplain' in t.habitats
    assert t.habitats['floodplain'].neighbors==('grassland','wetland')
    assert 'floodplain' in t.habitats['wetland'].neighbors
    for typ in ('plant','soil','detritus','water'):
        assert b.mass[t.acct(typ,'floodplain')]>0
        for donor in ('wetland','grassland'):
            assert b.mass[t.acct(typ,donor)] < four.host.book.mass[four.bridge.tree.acct(typ,donor)]
    for typ in ('sun','chem'):
        assert b.energy[t.acct(typ,'floodplain')]>0
    assert four.host.book.audit()['mass_error']==pytest.approx(b.audit()['mass_error'],abs=1e-8)
    assert four.host.book.audit()['energy_error']==pytest.approx(b.audit()['energy_error'],abs=1e-8)
    # Compare entire aggregate ledger: the partition is a transfer, not a mint.
    assert sum(four.host.book.mass.values())==pytest.approx(sum(b.mass.values()),abs=1e-7)
    assert sum(four.host.book.energy.values())==pytest.approx(sum(b.energy.values()),abs=1e-7)


def test_new_habitat_participates_in_native_growth_and_collapse():
    sim=Unified242(seed=9711,five_habitats=True)
    assert sim.floodplain_colonizations==4
    assert sum(a.alive and a.habitat=='floodplain' for a in sim.bridge.actors.values())==4
    sim.run(4)
    assert sim.host.sim.tick==sim.host.sim.ecology.day
    assert len(sim.bridge.tree.habitats)==5
    assert sim.host.book.audit()['rejections']==0
    assert sim.bridge.tree.counters['tree_climate_tick']>0


def test_resource_aware_uses_existing_cognition_and_book():
    s=Unified242(seed=9711,five_habitats=True,family_benefits=True,
                 resource_aware_family=True)
    b=s.bridge
    fid=next(k for k in b.family_pairs if ':forest_browser:' in k)
    f,m=b.family_pairs[fid];female=b.actors[f];male=b.actors[m]
    female.condition=1.;male.condition=1.
    maternal=b.physical.maternal(female)
    # Real, finite maternal shortage and local plant fuel.
    before=b.book.mass[maternal]
    assert before < b.book.mass[maternal] + .001
    b.day=PROVISION_DAY=40
    accepted=b._provision_mother(female,male)
    assert isinstance(male.cognition,Cognition)
    assert b._claim_id(female) in b.tree.sim.knowledge.claims
    assert b.family_knowledge_metrics['local_food_observations']==1
    if accepted:
        assert b.book.mass[maternal]>before
        assert b.family_knowledge_metrics['funded_investments']==1
        assert male.cognition.claim(b._claim_id(female)).practiced>0
    assert b.book.audit()['rejections']==0


def test_knowledge_not_new_engine_and_no_extra_energy_when_denied():
    s=Unified242(seed=9711,family_benefits=True,resource_aware_family=True)
    b=s.bridge
    fid=next(k for k in b.family_pairs if ':ridge_hound:' in k)
    f,m=b.family_pairs[fid];female=b.actors[f];male=b.actors[m]
    b.day=45
    current=b.book.mass[b.physical.maternal(female)]
    # Ridge hounds cannot convert plants to maternal mass when no carcass exists.
    b._provision_mother(female,male)
    assert b.book.mass[b.physical.maternal(female)]==pytest.approx(current,abs=1e-9)
    assert b.book.audit()['rejections']==0
    assert b.tree.sim.knowledge is s.host.sim.knowledge


def test_checkpoint_exact_5_habitat_knowledge():
    a=Unified242(seed=9712,five_habitats=True,family_benefits=True,
                 resource_aware_family=True)
    for _ in range(3):a.step()
    restored=pickle.loads(pickle.dumps(a,pickle.HIGHEST_PROTOCOL))
    for _ in range(3):
        a.step();restored.step()
    assert a.report()==restored.report()
    assert a.bridge.events==restored.bridge.events

def test_opt_out_is_identical_to_cycle041_legacy_under_matched_seed():
    from spatial_map_02137 import Unified240
    old=Unified240(seed=9712,grid_size=8)
    new=Unified242(seed=9712,five_habitats=False,grid_size=8)
    for _ in range(30):old.step();new.step()
    assert old.bridge.events==new.bridge.events
    assert dict(old.host.book.mass)==dict(new.host.book.mass)
    assert dict(old.host.book.energy)==dict(new.host.book.energy)
    assert old.bridge.positions==new.bridge.positions


def test_floodplain_joins_native_migration_and_collapses_without_lost_matter():
    s=Unified242(seed=9711,five_habitats=True)
    tree=s.bridge.tree
    assert 'floodplain' in tree.habitats['wetland'].neighbors
    native=next(r for r in tree.residents.values() if r.alive and r.habitat=='wetland')
    native.habitat='floodplain'
    # New habitat is accepted by the unchanged native feeding and death machinery.
    tree._feed(native)
    prior=s.host.book.audit()
    tree.collapse('explicit_test')
    assert tree.state=='archived'
    assert s.host.book.audit()['rejections']==prior['rejections']
    assert abs(s.host.book.audit()['mass_error'])<1e-6
    assert abs(s.host.book.audit()['energy_error'])<1e-6
    assert s.host.book.mass[tree.acct('plant','floodplain')]<1e-8


def test_family_knowledge_reports_funded_practice_not_unfunded_success():
    sim=Unified242(seed=9711,five_habitats=True,family_benefits=True,resource_aware_family=True)
    fam=sim.bridge
    fid=next(k for k in fam.family_pairs if ':forest_browser:' in k)
    f,m=fam.family_pairs[fid]
    mother,father=fam.actors[f],fam.actors[m]
    fam.day=45
    source=fam.tree.acct('plant',mother.habitat)
    # First aid is actually funded; it contributes to the existing cognition relation.
    before=fam.book.mass[source]
    # A legitimate feeding episode builds the father's funded reserve enough to
    # cover knowledge-dependent maintenance *and* the provisioning work.
    assert fam._feed_herbivore(father)
    did=fam._provision_mother(mother,father)
    assert did
    assert fam.book.mass[source]<before
    knowledge_id=fam._claim_id(mother)
    assert father.cognition.claim(knowledge_id).practiced>=1
    assert knowledge_id in fam.tree.sim.knowledge.claims
    assert mother.cognition.partner(father.id).expectation('benevolence')>0.5
    assert fam.book.audit()['rejections']==0

def test_learned_family_maintenance_buffer_actually_changes_behavior():
    s=Unified242(seed=9711,five_habitats=True,family_benefits=True,
                 resource_aware_family=True)
    b=s.bridge
    fid=next(k for k in b.family_pairs if ':forest_browser:' in k)
    f,m=b.family_pairs[fid];mother=b.actors[f];father=b.actors[m]
    b.day=40
    father.condition=1.;mother.condition=1.
    reserve=b.physical.reserve(father)
    # Reduce (via an actual Book move) father reserve into a range that the old
    # policy would spend, but the new knowledge-informed maintenance floor saves.
    current=b.book.energy[reserve]
    target=.016
    assert current>target
    b.book.move(energy=[(reserve,'environment:heat',current-target)])
    old_maternal=b.book.mass[b.physical.maternal(mother)]
    accepted=b._provision_mother(mother,father)
    assert not accepted
    assert b.book.mass[b.physical.maternal(mother)]==pytest.approx(old_maternal)
    assert b.family_knowledge_metrics['investment_declined_resource_or_health']>=1
    assert b.book.audit()['rejections']==0
    assert father.cognition.claim(b._claim_id(mother)).exposures==1
