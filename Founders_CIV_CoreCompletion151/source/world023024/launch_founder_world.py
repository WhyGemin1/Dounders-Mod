"""Run an interactive, localhost-only world backed by the Python simulation.
Usage: python launch_founder_world.py --port 8765 --seed 400
"""
from __future__ import annotations
import argparse,json, threading
from http.server import HTTPServer,BaseHTTPRequestHandler
from urllib.parse import urlparse
from pathlib import Path
from random import Random
from founders_civ.experimental.world_integration import IntegratedWorld

PAGE=Path(__file__).parent/'founder_world.html'
class App:
    def __init__(self,seed=400):
        self.seed=seed;self.sim=IntegratedWorld(seed=seed,days=20000)
        self.lock=threading.RLock()
    def action(self,body):
        s=self.sim;op=body.get('action')
        if op=='step':
            n=int(body.get('cycles',1))
            if not 1<=n<=100:raise ValueError('cycles must be 1–100')
            for _ in range(n):s.step()
            return {'cycles_completed':n}
        if op=='starter_world':
            from run_world_tree_pilot import bootstrap
            sim,realm_id,tree_id=bootstrap(self.seed)
            self.sim=sim
            return {'scenario':'researched_and_reviewed','realm':realm_id,'world_tree':tree_id,'species_seeds':1}
        if op=='reset':
            k=int(body.get('seed',self.seed))
            if not 0<=k<=10_000_000:raise ValueError('invalid seed')
            self.seed=k;self.sim=IntegratedWorld(seed=k,days=20000)
            return {'seed':k}
        a=body.get('actor')
        if a not in s.founders.people:raise ValueError('select a valid Founder')
        s._current_parent=None
        if op=='tree_observe':
            tree=s.world_trees.worlds[body['creation_id']]
            return tree.observe(a)
        if op=='tree_research':
            tree=s.world_trees.worlds[body['creation_id']]
            return tree.study(a)
        if op=='draft':
            b=s.seeds.draft(a,body.get('kind'),body.get('name'),body.get('parent'),body.get('rules'),body.get('x',50),body.get('y',50))
            return {'blueprint_id':b.id,'stage':b.stage}
        if op=='research':
            b=s.seeds.research(a,body['seed_id']);return {'blueprint_id':b.id,'stage':b.stage,'research_cycles':len(b.research_ticks)}
        if op=='validate':
            b=s.seeds.validate(a,body['seed_id']);return {'blueprint_id':b.id,'stage':b.stage}
        if op=='plant':
            item=s.seeds.plant(a,body['seed_id']);return {'creation_id':item['id'],'status':item['status']}
        if op=='tend':
            item=s.seeds.tend(a,body['creation_id'],float(body.get('amount',.6)));return {'creation_id':item['id']}
        if op=='travel':
            dst=body.get('destination')
            from founders_civ.experimental.social_agents import LINKS
            f=s.founders.people[a]
            if dst not in LINKS[f.location]:raise ValueError('destination not adjacent')
            origin=f.location
            outcome,txn,info=s._move(a,Random(s.seed+s.tick+int(a[1:])),force=dst)
            s.log('manual_travel',a,txn=txn,from_site=origin,destination=dst,outcome=outcome)
            return {'destination':dst,'outcome':outcome}
        if op=='recharge':
            place=s.founders.people[a].location
            source='house' if place=='house' else ('river_pool' if place=='riverbank' else None)
            if source is None:raise ValueError('must visit House fountain or riverbank to recharge')
            q=min(1.15,s.book.energy[source])
            if q<=0:raise ValueError('energy source depleted')
            txn=s.book.move(energy=[(source,f'founder:{a}',q)])
            s.log('manual_recharge',a,txn=txn,amount=q,source=source)
            return {'energy_recovered':q,'source':source}
        if op=='checkpoint':
            if s.book.energy[f'founder:{a}']<.03:raise ValueError('insufficient energy')
            if s.founders.people[a].location!='house':raise ValueError('Founder must be at House')
            txn=s.book.move(energy=[(f'founder:{a}','environment:heat',.03)])
            s.save_checkpoint(a);s.log('manual_checkpoint',a,txn=txn)
            return {'checkpoint_version':s.founders.people[a].checkpoint_version}
        if op=='goal':
            from founders_civ.experimental.social_agents import GOALS
            goal=body.get('goal')
            if goal not in GOALS:raise ValueError('invalid goal')
            state=s.states[a];old=state.main_goal;state.main_goal=goal
            s.founders.people[a].goals=[goal,state.secondary_goal]
            s.log('goal_updated',a,goal_from=old,goal_to=goal,source='manual_override')
            return {'goal':goal}
        raise ValueError('unknown action')

class Handler(BaseHTTPRequestHandler):
    app=None
    def _json(self,data,status=200):
        b=json.dumps(data,default=str,separators=(',',':'),allow_nan=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type','application/json; charset=utf-8')
        self.send_header('Cache-Control','no-store')
        self.send_header('Content-Length',str(len(b)))
        self.end_headers();self.wfile.write(b)
    def do_GET(self):
        p=urlparse(self.path).path
        if p in ('/','/founder_world.html'):
            payload=PAGE.read_bytes()
            self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(payload)))
            self.end_headers();self.wfile.write(payload);return
        if p=='/api/state':
            with self.app.lock:self._json(self.app.sim.status(include_actors=True,history=48))
            return
        if p=='/api/export':
            with self.app.lock:
                sim=self.app.sim
                data=sim.status(history=300)
                data['all_events']=sim.events
                data['metadata']={'generated_by':'Founders-CIV WORLD-023 experimental','interpretation':'synthetic experimental simulation'}
                self._json(data)
            return
        self._json({'error':'not found'},404)
    def do_POST(self):
        if self.path!='/api/action':return self._json({'error':'not found'},404)
        try:
            n=int(self.headers.get('Content-Length','0'))
            if n<1 or n>15000:raise ValueError('invalid payload length')
            body=json.loads(self.rfile.read(n))
            if not isinstance(body,dict):raise ValueError('object required')
            with self.app.lock:
                result=self.app.action(body)
                self.app.sim.book.audit()
                self._json({'ok':True,'result':result})
        except (ValueError,KeyError,TypeError) as exc:
            self._json({'ok':False,'error':str(exc)},400)
        except Exception as exc:
            self._json({'ok':False,'error':f'internal error: {type(exc).__name__}'},500)
    def log_message(self,*args):pass

def start(port=8765,seed=400):
    app=App(seed)
    Handler.app=app
    srv=HTTPServer(('127.0.0.1',port),Handler)
    print(f'Founder World ready: http://127.0.0.1:{port}/ (Ctrl+C to stop)',flush=True)
    srv.serve_forever()

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=8765);parser.add_argument('--seed',type=int,default=400)
    opt=parser.parse_args();start(opt.port,opt.seed)
