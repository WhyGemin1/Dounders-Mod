#!/usr/bin/env python3
"""Founders–CIV WorldBox M05 command-line interface. Python 3.10+, stdlib only.

All commands except 'doctor'/'fingerprint' operate on an explicitly bound world.
This is a persistent virtual energy sidecar + read-only native observer, not a
completed Core151 or native-gameplay integration.
"""
import argparse
import hashlib
import json
import sys
import sqlite3
from pathlib import Path
from m05_core import Store, IntegrationError, digest

ROOT=Path(__file__).resolve().parent
EXPECTED_SHA='51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'

def output(data, path=None):
    body=json.dumps(data,indent=2,sort_keys=True,ensure_ascii=False)
    if path:
        dest=Path(path);dest.parent.mkdir(parents=True,exist_ok=True)
        temp=dest.with_name(dest.name+'.tmp')
        temp.write_text(body+'\n',encoding='utf-8');temp.replace(dest)
    print(body)

def read_json(path):
    value=json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(value,dict):raise IntegrationError('JSON document must be an object')
    return value

def doctor(game):
    report={'python_compatible':sys.version_info[:2]>=(3,10),
            'expected_assembly_sha256':EXPECTED_SHA,'worldbox_native_write_enabled':False,
            'source_only_CSharp_build_required':True,'checks':[]}
    if not game:
        report['checks'].append({'item':'game','status':'NOT_TESTED','reason':'Provide --game path to installed WorldBox folder'})
        return report
    root=Path(game)
    asm=root/'WorldBox_Data'/'Managed'/'Assembly-CSharp.dll'
    if not asm.exists():
        report['checks'].append({'item':'assembly','status':'MISSING','path':str(asm)})
    else:
        sha=hashlib.sha256(asm.read_bytes()).hexdigest()
        report['checks'].append({'item':'assembly','status':'PASS' if sha==EXPECTED_SHA else 'MISMATCH_FAIL_CLOSED',
                                'sha256':sha,'path':str(asm)})
    for name,path in [('BepInEx',root/'BepInEx'/'core'/'BepInEx.dll'),
                      ('Harmony',root/'BepInEx'/'core'/'0Harmony.dll'),
                      ('UnityCore',root/'WorldBox_Data'/'Managed'/'UnityEngine.CoreModule.dll'),
                      ('UnityIMGUI',root/'WorldBox_Data'/'Managed'/'UnityEngine.IMGUIModule.dll')]:
        report['checks'].append({'item':name,'status':'PASS' if path.is_file() else 'MISSING', 'path':str(path)})
    plugins=root/'BepInEx'/'plugins'
    report['checks'].append({'item':'observer_plugins',
         'files':[p.name for p in plugins.glob('*Founders*CIV*.dll')] if plugins.exists() else [],
         'warning':'Do not enable separate M03 and M05 observers simultaneously; duplicates can overload capture.'})
    report['build_ready']=all(x.get('status')=='PASS' for x in report['checks'] if x.get('item') in ('assembly','BepInEx','Harmony','UnityCore','UnityIMGUI'))
    return report

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db',default='data/m05.sqlite',help='World-bound SQLite state; use different DB per save')
    sub=p.add_subparsers(dest='command',required=True)
    x=sub.add_parser('doctor',help='Check game assembly and BepInEx dependencies');x.add_argument('--game')
    x=sub.add_parser('init');x.add_argument('--world-key',required=True)
    x=sub.add_parser('setup');x.add_argument('--config',required=True)
    x=sub.add_parser('add-founder');x.add_argument('--founder',required=True)
    x=sub.add_parser('add-tree');x.add_argument('--id',required=True);x.add_argument('--config',required=True)
    x=sub.add_parser('cycle');x.add_argument('--period',type=int,required=True);x.add_argument('--river-supply',type=int,required=True);x.add_argument('--conditions');x.add_argument('--output')
    x=sub.add_parser('harvest');x.add_argument('--fruit',required=True);x.add_argument('--founder',required=True);x.add_argument('--operation',required=True)
    x=sub.add_parser('create');x.add_argument('--founder',required=True);x.add_argument('--kind',choices=['creation','world_seed','realm_link'],required=True);x.add_argument('--attempt',required=True)
    x=sub.add_parser('establish-tree');x.add_argument('--id',required=True);x.add_argument('--attempt',required=True);x.add_argument('--config',required=True)
    x=sub.add_parser('feed-virtual');x.add_argument('--founder',required=True);x.add_argument('--tree',required=True);x.add_argument('--amount',type=int,required=True);x.add_argument('--event',required=True)
    x=sub.add_parser('body-cycle');x.add_argument('--founder',required=True);x.add_argument('--cycle',required=True);x.add_argument('--rest',type=float,required=True);x.add_argument('--workload',type=float,required=True)
    x=sub.add_parser('ingest-events');x.add_argument('jsonl');x.add_argument('--output')
    x=sub.add_parser('native-audit');x.add_argument('--output')
    x=sub.add_parser('import-snapshot');x.add_argument('json')
    x=sub.add_parser('compare-snapshots');x.add_argument('earlier');x.add_argument('later');x.add_argument('--output')
    x=sub.add_parser('audit');x.add_argument('--output')
    x=sub.add_parser('status');x.add_argument('--output')
    x=sub.add_parser('export-core151-review');x.add_argument('--output',required=True)
    x=sub.add_parser('publish-overlay');x.add_argument('--game',required=True)
    a=p.parse_args()
    try:
        if a.command=='doctor':
            report=doctor(a.game);output(report)
            return 0 if report.get('build_ready',True) else 2
        s=Store(a.db)
        try:
            if a.command=='init':r=s.initialize(a.world_key)
            elif a.command=='setup':
                cfg=read_json(a.config)
                s.initialize(cfg['world_key'])
                for f in cfg.get('founders',[]):s.add_founder(f)
                for t in cfg.get('trees',[]):s.add_tree(t['id'],t['config'])
                r={'world_key':s.require_world(),'tree_count':len(cfg.get('trees',[])),'founder_count':len(cfg.get('founders',[])),
                   'native_worldbox_worlds_created':0}
            else:
                s.require_world()
                if a.command=='add-founder':r=s.add_founder(a.founder)
                elif a.command=='add-tree':r=s.add_tree(a.id,read_json(a.config))
                elif a.command=='cycle':r=s.cycle(a.period,a.river_supply,read_json(a.conditions) if a.conditions else None)
                elif a.command=='harvest':r=s.harvest(a.fruit,a.founder,a.operation)
                elif a.command=='create':r=s.create(a.attempt,a.founder,a.kind)
                elif a.command=='establish-tree':r=s.establish_tree(a.id,a.attempt,read_json(a.config))
                elif a.command=='feed-virtual':r=s.feed_virtual(a.founder,a.tree,a.amount,a.event)
                elif a.command=='body-cycle':r=s.body_cycle(a.founder,a.cycle,a.rest,a.workload)
                elif a.command=='ingest-events':r=s.ingest_events(a.jsonl)
                elif a.command=='native-audit':r=s.native_audit()
                elif a.command=='import-snapshot':r=s.import_snapshot(a.json)
                elif a.command=='compare-snapshots':r=s.compare_snapshots(a.earlier,a.later)
                elif a.command=='audit':r={'book':s.audit(),'native':s.native_audit()}
                elif a.command=='status':r=s.status()
                elif a.command=='export-core151-review':r=s.journal_export()
                elif a.command=='publish-overlay':
                    diag=doctor(a.game)
                    if not diag.get('build_ready'):raise IntegrationError('WorldBox doctor failed; refusing to publish')
                    path=Path(a.game)/'BepInEx'/'FoundersCIV_M05'/'world_key.txt'
                    if not path.is_file() or path.read_text(encoding='utf-8').strip()!=s.require_world():
                        raise IntegrationError('observer world_key.txt absent or different; no overlay published')
                    projection=s.status()
                    projection['projection_kind']='VIRTUAL_M05_NOT_NATIVE_WORLD_STATE'
                    dest=path.parent/'live_state.json'
                    tmp=dest.with_suffix('.json.tmp')
                    tmp.write_text(json.dumps(projection,ensure_ascii=False,sort_keys=True),encoding='utf-8')
                    tmp.replace(dest)
                    r={'published':str(dest),'world_key':s.require_world(),'native_gameplay_writes':0}
            output(r,getattr(a,'output',None))
        finally:s.close()
        return 0
    except (IntegrationError,KeyError,TypeError,ValueError,sqlite3.Error) as ex:
        print('M05 ERROR: '+str(ex),file=sys.stderr)
        return 2

if __name__=='__main__':
    sys.exit(main())
