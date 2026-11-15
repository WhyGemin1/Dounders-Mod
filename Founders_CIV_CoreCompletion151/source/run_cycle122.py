"""Cycle122 resumable, per-arm durable matched experiment runner."""
import sys,json,csv,pickle,argparse,os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent/'src'))
from integrated_02160 import Unified260
from habitat_bridge import SPECIES
from interworld_split_021121 import fund_split_shipment
from generation_audit_021108 import generation_metrics

def run(seed, fraction, output, days=180):
    output=Path(output);output.mkdir(parents=True,exist_ok=True)
    name=f"seed{seed}_fraction{fraction:g}"
    final=output/(name+".jsonl")
    if final.exists():
        return list(map(json.loads,final.read_text().splitlines()))
    s=Unified260(seed=seed,counts={k:8 for k in SPECIES},capacity_scale=.5,family_benefits=True,resource_aware_family=True)
    funding=fund_split_shipment(s.bridge.tree,fraction)
    initial=s.host.sim.tick
    rows=[]
    for day in range(1,days+1):
        s.step()
        if day in (30,60,120,180):
            audit=s.host.book.audit()
            row=dict(seed=seed,floodplain_fraction=fraction,day=day,living=sum(a.alive for a in s.bridge.actors.values()),tree_state=s.bridge.tree.state,book_rejections=audit['rejections'],mass_error=audit['mass_error'],energy_error=audit['energy_error'],**generation_metrics(s.bridge))
            assert s.host.sim.tick-initial==day and audit['rejections']==0 and abs(audit['mass_error'])<1e-5 and abs(audit['energy_error'])<1e-5
            rows.append(row)
            # Persist observations at every milestone, not after whole batch.
            tmp=output/(name+".jsonl.tmp")
            tmp.write_text(''.join(json.dumps(r,default=str)+'\\n' for r in rows))
            os.replace(tmp,final)
            if day==30:
                tmp=output/(name+"_day30.pkl.tmp")
                with tmp.open('wb') as f:pickle.dump(s,f)
                os.replace(tmp,output/(name+"_day30.pkl"))
    return rows

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=9712);p.add_argument('--fraction',type=float,default=1.);p.add_argument('--days',type=int,default=180);p.add_argument('--output',default='/mnt/data/cycle122')
    a=p.parse_args();print(json.dumps(run(a.seed,a.fraction,a.output,a.days),default=str))
