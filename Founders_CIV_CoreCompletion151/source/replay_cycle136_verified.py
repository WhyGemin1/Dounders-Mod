"""Selected exact 30+690 replay across full Cycle136 semantic state and Book."""
import json,pickle,hashlib,argparse
from pathlib import Path
from experiment_cycle136 import fingerprint,cohort_audit,summarize136

def replay(outdir,seed,assist):
    out=Path(outdir);name=f'C136_seed{seed}_assist{int(assist)}'
    result=json.loads((out/(name+'.day720.json')).read_text())
    snap=(out/(name+'.day30.pkl')).read_bytes()
    sha=hashlib.sha256(snap).hexdigest()
    if sha != result['milestones'][0]['checkpoint_sha256']:raise AssertionError('snapshot hash mismatch')
    sim=pickle.loads(snap)
    if sim.days!=30:raise AssertionError('clock mismatch in saved day30 checkpoint')
    for _ in range(690):sim.step()
    if sim.days!=720:raise AssertionError('day720 mismatch')
    observed=fingerprint(sim)
    if observed!=result['final_semantic_sha256']:raise AssertionError('semantic replay differs')
    current=summarize136(sim,720,result['config'])
    expected=result['milestones'][-1]
    for k,v in current.items():
        if k not in expected or v!=expected[k]:raise AssertionError('summary mismatch at '+k)
    cohort,_=cohort_audit(sim)
    if cohort!=result['cohort']:raise AssertionError('cohort replay mismatch')
    a=sim.host.book.audit()
    return {'seed':seed,'assisted_feeding':assist,'replay':'exact','day30_sha256':sha,
            'day720_semantic_sha256':observed,'book_rejections':a['rejections'],
            'book_energy_error':a['energy_error'],'days_replayed':690}
if __name__=='__main__':
 x=argparse.ArgumentParser();x.add_argument('--output',required=True);x.add_argument('--seed',type=int,required=True);x.add_argument('--assist',type=int,choices=(0,1),required=True)
 a=x.parse_args();print(json.dumps(replay(a.output,a.seed,bool(a.assist)),sort_keys=True))
