"""WORLD-024 localhost interface: 100-Founder shared World Tree commons.
Run: python launch_world024.py --seed 820 --port 8766
"""
from __future__ import annotations
import argparse,json,threading
from http.server import HTTPServer
from pathlib import Path
from urllib.parse import urlparse
from launch_founder_world import App, Handler
from run_world_tree_pilot import bootstrap
from founders_civ.experimental.world024 import CommonsWorld

PAGE024=Path(__file__).parent/'founder_world_024.html'
class App024(App):
    def __init__(self,seed=820):
        self.seed=seed
        self.lock=threading.RLock()
        self.sim=CommonsWorld(seed=seed,days=20000)

    def action(self,body):
        op=body.get('action')
        if op=='starter_world':
            governance=body.get('governance','collective')
            extraction=body.get('extraction','careful')
            allow_private=body.get('allow_private',False)
            if not isinstance(allow_private,bool):raise ValueError('allow_private must be boolean')
            def factory(**kw):return CommonsWorld(**kw,governance=governance,
                             extraction=extraction,allow_private=allow_private)
            sim,realm,tree=bootstrap(self.seed,simulator_class=factory)
            sim.mark_shared(tree)
            self.sim=sim
            return {'scenario':'reviewed living commons','tree':tree,'realm':realm,
                    'governance':governance,'extraction':extraction,'private_option':allow_private}
        if op=='reset':
            seed=int(body.get('seed',self.seed))
            if not 0<=seed<=10_000_000:raise ValueError('invalid seed')
            self.seed=seed;self.sim=CommonsWorld(seed=seed,days=20000)
            return {'seed':seed}
        if op in ('commons_observe','tree_harvest','tree_eat','commons_enlist'):
            sim=self.sim
            a=body.get('actor')
            if a not in sim.founders.people:raise ValueError('select an existing Founder')
            if not sim.shared_tree_id:raise ValueError('start reviewed World Tree first')
            if not sim.founders.people[a].alive:raise ValueError('Founder inactive')
            return {'event':sim._do(a,(2.0,op,None,sim.shared_tree_id),[],None,None),'action':op}
        return super().action(body)

class Handler024(Handler):
    def do_GET(self):
        path=urlparse(self.path).path
        if path in ('/','/founder_world_024.html'):
            payload=PAGE024.read_bytes()
            self.send_response(200)
            self.send_header('Content-Type','text/html; charset=utf-8')
            self.send_header('Content-Length',str(len(payload)))
            self.end_headers();self.wfile.write(payload);return
        if path in ('/api/state','/api/export'):
            with self.app.lock:
                sim=self.app.sim
                data=sim.status(include_actors=True,history=60)
                data['commons']=sim.summary_024() if sim.shared_tree_id else None
                if path=='/api/export':
                    data['all_events']=sim.events
                    data['metadata']={'edition':'WORLD-024 experimental',
                     'reality_check':'Synthetic simulation; conservation does not establish ecological realism'}
                self._json(data)
            return
        return super().do_GET()

def main(port=8766,seed=820):
    Handler024.app=App024(seed)
    server=HTTPServer(('127.0.0.1',port),Handler024)
    print(f'WORLD-024 Founder Commons: http://127.0.0.1:{port}/',flush=True)
    server.serve_forever()

if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--port',type=int,default=8766)
    parser.add_argument('--seed',type=int,default=820)
    args=parser.parse_args();main(args.port,args.seed)
