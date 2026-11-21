#!/usr/bin/env python3
"""Founders-CIV WorldBox M01 read-only actor enrollment and shadow comparisons."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
from founders_worldbox import ActorRegistry,BridgeIntegrityError
from founders_worldbox.client import BridgeClient
from founders_worldbox.core151_adapter import core151_snapshot,shadow_compare

def show(value): print(json.dumps(value,indent=2,sort_keys=True))
def main():
    p=argparse.ArgumentParser(description='WorldBox 0.51.2 / Core151 M01, OBSERVE ONLY')
    p.add_argument('--db',default='m01_actor_registry.sqlite3')
    subs=p.add_subparsers(dest='command',required=True)
    q=subs.add_parser('init-world');q.add_argument('--world-id',required=True);q.add_argument('--seed',type=int,required=True)
    q=subs.add_parser('enroll');q.add_argument('--world-id',required=True);q.add_argument('--native-id',required=True)
    q.add_argument('--core-id',required=True);q.add_argument('--asset',required=True);q.add_argument('--species',required=True)
    q.add_argument('--generation',type=int,default=None)
    q=subs.add_parser('observe');q.add_argument('--world-id',required=True);q.add_argument('--snapshot',required=True)
    q=subs.add_parser('new-epoch');q.add_argument('--world-id',required=True)
    q=subs.add_parser('links');q.add_argument('--world-id',required=True)
    q=subs.add_parser('shadow');q.add_argument('--world-id',required=True);q.add_argument('--core-source');q.add_argument('--core-state-json');q.add_argument('--seed',type=int,default=100001)
    q=subs.add_parser('export-core');q.add_argument('--core-source',required=True);q.add_argument('--seed',type=int,default=100001);q.add_argument('--output',required=True)
    q=subs.add_parser('live-probe');q.add_argument('--base-url',default='http://127.0.0.1:8723')
    q=subs.add_parser('live-snapshot');q.add_argument('--base-url',default='http://127.0.0.1:8723');q.add_argument('--output',required=True);q.add_argument('--asset-id',help='Exact native actor asset_id, e.g. rabbit; filter cohort in worlds with over 5000 actors');q.add_argument('--min-actors',type=int,default=20,help='Minimum filtered cohort size; use 20 before, 0 after to observe loss')
    args=p.parse_args()
    try:
        if args.command.startswith('live-'):
            client=BridgeClient(base_url=args.base_url)
            if args.command=='live-probe':
                health=client.health();cap=client.capabilities()
                names=[c.get('name') for c in cap.get('commands',[])
                       if isinstance(c,dict)]
                present='query_actor_identities' in names
                show({'health':health,
                      'worldbox_version':cap.get('worldbox_version'),
                      'native_assembly_sha256':cap.get('assembly_csharp_sha256'),
                      'registered_commands':len(names),
                      'query_actor_identities_registered':present,
                      'next_step':('Pause a fully loaded disposable WorldBox world, then run -Stage before.'
                                   if present else
                                   'M01 command not in live capabilities. Check installed WorldBoxBridge.dll and BepInEx logs.'),
                      'note':'Read-only bridge probe; no native mutations or Book writes.'})
                if not present:raise RuntimeError('M01 command absent from live /capabilities; do not attempt identity snapshots')
                return
            cohort=args.asset_id.strip() if args.asset_id is not None else None
            if args.asset_id is not None and not cohort:
                raise ValueError('--asset-id must name a non-empty native asset')
            request_args={'asset_id':cohort} if cohort else {}
            snap=client.command('query_actor_identities',request_args)
            from founders_worldbox import normalize_snapshot
            meta,items=normalize_snapshot(snap)
            # Explicit source-consistency gate: a filter must not silently
            # include animals from another species; at least 20 identities
            # are needed for our first save/reload acceptance experiment.
            if args.min_actors < 0 or args.min_actors > 5000:
                raise ValueError('--min-actors must be between 0 and 5000')
            if cohort is not None:
                if any(item.get('asset_id') != cohort for item in items):
                    raise BridgeIntegrityError('Native bridge returned actors outside requested cohort')
                if len(items) < args.min_actors:
                    raise ValueError(f'Only {len(items)} native actors of asset_id={cohort}; required minimum {args.min_actors}')
                snap['capture_asset_id']=cohort
            Path(args.output).write_text(json.dumps(snap,indent=2))
            show({'saved':str(Path(args.output).resolve()),'asset_id_filter':cohort,**meta,
                  'note':'Paused native observation only; no Book writes; matching filter required on reload'})
            return
        if args.command=='export-core':
            core=core151_snapshot(args.core_source,seed=args.seed)
            Path(args.output).write_text(json.dumps(core,indent=2))
            show({'saved':str(Path(args.output).resolve()),'actors':core['actor_count'],
                'founders':core['founder_count'],'Book_shared':core['book_shared'],
                'Book_rejections':core['book_rejections']})
            return
        with ActorRegistry(args.db) as reg:
            if args.command=='init-world':
                reg.init_world(args.world_id,args.seed);show({'world_id':args.world_id,'seed':args.seed,'status':'registered'})
            elif args.command=='enroll':
                added=reg.enroll(args.world_id,args.native_id,args.core_id,args.asset,args.species,args.generation)
                show({'added':added,'world_id':args.world_id,'native_id':args.native_id,'core_id':args.core_id})
            elif args.command=='observe':
                show(reg.observe(args.world_id,json.loads(Path(args.snapshot).read_text())))
            elif args.command=='new-epoch':show({'new_epoch':reg.new_epoch(args.world_id)})
            elif args.command=='links':show(reg.links(args.world_id))
            elif args.command=='shadow':
                if bool(args.core_source)==bool(args.core_state_json):
                    raise ValueError('Specify exactly one of --core-source or --core-state-json')
                state=(core151_snapshot(args.core_source,args.seed) if args.core_source
                       else json.loads(Path(args.core_state_json).read_text()))
                show(shadow_compare(reg,args.world_id,state))
    except (BridgeIntegrityError,ValueError,FileNotFoundError,ConnectionError,RuntimeError) as e:
        print(f'M01 blocked safely: {e}',file=sys.stderr)
        raise SystemExit(2)
if __name__=='__main__':main()
