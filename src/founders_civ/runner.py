"""CLI and API runner for one observable simulation."""
from pathlib import Path
import json, csv, argparse, time
from .observatory import ObservatorySimulation

def run(seed=42,days=30,arm='1111',progress=None):
    if not isinstance(seed,int) or abs(seed)>100000000:raise ValueError('seed must be an integer within ±100,000,000')
    if not isinstance(days,int) or days<1 or days>720:raise ValueError('days must be in 1..720')
    if not isinstance(arm,str) or len(arm)!=4 or set(arm)-set('01'):raise ValueError('arm must be 4 binary digits')
    sim=ObservatorySimulation(seed,days,arm,trace=True,progress=progress)
    sim.run()
    return sim.export()

def write_package(data,dest):
    dest=Path(dest);dest.mkdir(parents=True,exist_ok=True)
    output=dest/'simulation.json'
    output.write_text(json.dumps(data,separators=(',',':'),ensure_ascii=False),encoding='utf-8')
    (dest/'summary.json').write_text(json.dumps(data['results'],indent=2),encoding='utf-8')
    if data['daily']:
        keys=list(data['daily'][0].keys())
        with (dest/'daily.csv').open('w',newline='',encoding='utf-8') as f:
            writer=csv.DictWriter(f,fieldnames=keys);writer.writeheader();writer.writerows(data['daily'])
    if data['events']:
        keys=sorted({k for e in data['events'] for k in e})
        with (dest/'events.csv').open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(data['events'])
    return str(output)

def main():
    ap=argparse.ArgumentParser(description='Founders-CIV observable local simulation')
    ap.add_argument('--seed',type=int,default=42)
    ap.add_argument('--days',type=int,default=30)
    ap.add_argument('--arm',default='1111',help='S F B I binary factor flags')
    ap.add_argument('--output',default='results/latest')
    args=ap.parse_args();start=time.perf_counter()
    data=run(args.seed,args.days,args.arm)
    path=write_package(data,args.output)
    print(json.dumps({'saved':path,'runtime_s':round(time.perf_counter()-start,2),
       'seed':args.seed,'days':args.days,'arm':args.arm,'actors':len(data['actors']),
       'events':len(data['events']),'audit':data['audit']},indent=2))
if __name__=='__main__':main()
