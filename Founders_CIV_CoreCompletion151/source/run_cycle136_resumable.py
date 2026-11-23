"""Resumable deterministic checkpoint runner for long Cycle136 ecological experiments."""
import argparse,hashlib,json,os,pickle,time
from pathlib import Path
from experiment_cycle136 import make_sim,cohort_audit,fingerprint,summarize136
MILESTONES=(30,60,120,180,240,300,360,420,480,540,600,660,720)

def atomic_write(p,blob):
    temp=p.with_suffix(p.suffix+'.new')
    temp.write_bytes(blob);os.replace(temp,p)

def execute(seed,assist,out_dir,stop_at):
    if seed not in (9711,9712,9731) or type(assist)!=bool or stop_at not in MILESTONES:
        raise ValueError('outside bounded preregistered design')
    out=Path(out_dir);out.mkdir(exist_ok=True,parents=True)
    name=f'C136_seed{seed}_assist{int(assist)}'
    progress=out/(name+'.progress.json')
    snap=out/(name+'.progress.pkl')
    if progress.exists():
        p=json.loads(progress.read_text());b=snap.read_bytes()
        if hashlib.sha256(b).hexdigest()!=p['progress_sha256']:
            raise AssertionError('resumption checkpoint differs from recorded SHA-256')
        sim=pickle.loads(b)
        if sim.days!=p['last_day']:raise AssertionError('resume clock mismatch')
        if sim.host.book.audit()['rejections']:
            raise AssertionError('rejections in resume book')
        config=p['config'];rows=p['rows'];current=p['last_day']
        print('RESUME',name,current,flush=True)
    else:
        sim,config=make_sim(seed,assist);rows=[];current=0
        p={'cycle':136,'seed':seed,'assist':assist,'config':config,'rows':rows,'last_day':0,'numerical_tolerance':'Book relative to starting energy, scale-aware; no transaction changes'}
    start=time.monotonic()
    for day in MILESTONES:
        if day<=current or day>stop_at:continue
        for _ in range(day-current):sim.step()
        row=summarize136(sim,day,config)
        row['cohort'],_=cohort_audit(sim)
        row['assisted_feeding_metrics']=dict(getattr(sim.bridge,'juvenile_support_metrics',{}))
        if day==30:
            first=pickle.dumps(sim,pickle.HIGHEST_PROTOCOL)
            atomic_write(out/(name+'.day30.pkl'),first)
            row['checkpoint_sha256']=hashlib.sha256(first).hexdigest()
        rows.append(row);current=day
        if day in (360,720):
            cohort,individuals=cohort_audit(sim)
            result=dict(cycle=136,seed=seed,assist=assist,days=day,
                        config=config,milestones=rows,cohort=cohort,individual_g1=individuals,
                        book_audit=sim.host.book.audit(),final_semantic_sha256=fingerprint(sim),
                        assistance=dict(getattr(sim.bridge,'juvenile_support_metrics',{})))
            atomic_write(out/(name+f'.day{day}.json'),json.dumps(result,sort_keys=True).encode())
        blob=pickle.dumps(sim,pickle.HIGHEST_PROTOCOL)
        p.update(rows=rows,last_day=day,progress_sha256=hashlib.sha256(blob).hexdigest())
        atomic_write(snap,blob)
        atomic_write(progress,json.dumps(p,sort_keys=True).encode())
        print('MILESTONE',name,'day',day,'living',row['living'],
              'G1births',row['g1_births'],'G1matured',row['g1_reached_maturity_ever'],
              'G2',row['g2_births'],'seconds',round(time.monotonic()-start,1),flush=True)
    return current

if __name__=='__main__':
    x=argparse.ArgumentParser();x.add_argument('--seed',type=int,required=True)
    x.add_argument('--assist',type=int,required=True,choices=(0,1))
    x.add_argument('--output',required=True);x.add_argument('--stop-at',type=int,required=True)
    a=x.parse_args();execute(a.seed,bool(a.assist),a.output,a.stop_at)
