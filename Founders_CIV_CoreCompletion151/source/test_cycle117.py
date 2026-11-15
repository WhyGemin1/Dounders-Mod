from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from juvenile_foraging_021117 import enable_juvenile_feeding_access

def test_opt_in_and_conservation():
 s=Unified260(seed=9711,counts={'field_mouse':8,'meadow_grazer':8,'forest_browser':8,'ridge_hound':8,'carrion_bird':8})
 b=s.bridge
 assert not getattr(b,'_juvenile_feeding_access',False)
 enable_juvenile_feeding_access(b)
 for _ in range(3):s.step()
 a=s.host.book.audit()
 assert a['rejections']==0 and abs(a['mass_error'])<1e-5 and abs(a['energy_error'])<1e-5

def test_duplicate_enable_rejected():
 s=Unified260(seed=9711,counts={'field_mouse':8,'meadow_grazer':8,'forest_browser':8,'ridge_hound':8,'carrion_bird':8})
 enable_juvenile_feeding_access(s.bridge)
 try:enable_juvenile_feeding_access(s.bridge)
 except RuntimeError:return
 assert False

def test_finite_river_energy_funding():
 from river_capacity_021117 import fund_river_floodplain_energy
 s=Unified260(seed=9711,counts={k:8 for k in ('field_mouse','meadow_grazer','forest_browser','ridge_hound','carrion_bird')})
 b=s.host.book;dest=s.bridge.tree.acct('chem','floodplain')
 before=(b.energy['river_pool'],b.energy[dest],sum(b.mass.values()),sum(b.energy.values()))
 record=fund_river_floodplain_energy(s.bridge.tree,1.0)
 after=(b.energy['river_pool'],b.energy[dest],sum(b.mass.values()),sum(b.energy.values()))
 assert round(before[0]-after[0],8)==1 and round(after[1]-before[1],8)==1
 assert abs(before[2]-after[2])<1e-6 and abs(before[3]-after[3])<1e-6
 assert record['mass_added']==0
 try:fund_river_floodplain_energy(s.bridge.tree,1.0)
 except ValueError:return
 assert False
