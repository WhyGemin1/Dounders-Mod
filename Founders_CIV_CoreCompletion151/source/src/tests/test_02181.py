from integrated_02181 import Unified281
from species_life_02115 import PROFILES

def test_juvenile_provisioning_book_conservation():
 s=Unified281(seed=9711,reproductive_ecology=True,juvenile_provisioning=True)
 b=s.bridge
 parent=next(a for a in b.actors.values() if a.alive and a.species=='field_mouse' and a.stage=='adult')
 child=next(a for a in b.actors.values() if a.alive and a.species=='field_mouse' and a.id!=parent.id)
 child.age=PROFILES[child.species].independence
 child.habitat=parent.habitat
 child.parent_ids=(parent.id,)
 donor=b.physical.reserve(parent);recipient=b.physical.reserve(child)
 # Transfer real finite energy from another existing reserve into parent.
 b.book.move(energy=[(b.tree.acct('chem',parent.habitat),donor,.03)])
 before=sum(b.book.energy.values());old=b.book.energy[recipient]
 b._care(parent)
 assert b.book.energy[recipient]>old
 assert abs(sum(b.book.energy.values())-before)<1e-8

def test_opt_out():
 s=Unified281(seed=9711,juvenile_provisioning=False)
 assert not s.bridge.juvenile_provisioning
