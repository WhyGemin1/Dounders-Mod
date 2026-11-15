"""Persistent, fail-closed read-only WorldBox / Core151 actor binding.

Does NOT write to the Book, create animals, or change WorldBox's AI. A returned
native actor ID must be sourced from WorldBox ActorData.id, never name/position.
"""
from __future__ import annotations
import hashlib
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

class BridgeIntegrityError(ValueError):
    pass

def _ident(value: Any, label: str) -> str:
    if isinstance(value, bool) or not isinstance(value, (str,int)):
        raise BridgeIntegrityError(f'{label}: expected a WorldBox stable integer/string ID')
    s=str(value).strip()
    if not s or len(s)>160 or '\x00' in s:
        raise BridgeIntegrityError(f'{label}: empty, oversized or malformed ID')
    return s

def normalize_snapshot(snapshot: dict) -> tuple[dict, list[dict]]:
    """Validate the *new* bridge command, not existing query_actors (no native IDs).

    Snapshots must be captured with a PAUSED WorldBox map, and in M01 use a
    single complete response: no unstable HashSet pagination in a live world.
    """
    if snapshot.get('paused') is not True:
        raise BridgeIntegrityError('world must be paused for identity snapshot')
    if snapshot.get('world_loading') is True:
        raise BridgeIntegrityError('world currently loading')
    if snapshot.get('has_more') or int(snapshot.get('offset',0)) != 0:
        raise BridgeIntegrityError('partial/paginated snapshot rejected in M01')
    if int(snapshot.get('missing_identity_count',0)) or int(snapshot.get('duplicate_identity_count',0)):
        raise BridgeIntegrityError('bridge reported missing or duplicate native actor IDs')
    tick = snapshot.get('tick')
    if isinstance(tick,bool) or not isinstance(tick,int) or tick<0:
        raise BridgeIntegrityError('snapshot has no nonnegative integer WorldBox tick')
    seed = snapshot.get('world_seed')
    if isinstance(seed,bool) or not isinstance(seed,int):
        raise BridgeIntegrityError('snapshot has no integer WorldBox world seed')
    items = snapshot.get('items')
    if not isinstance(items,list) or snapshot.get('matched')!=len(items):
        raise BridgeIntegrityError('incomplete snapshot: matched count and items differ')
    result=[]; seen=set()
    for item in items:
        if not isinstance(item,dict):
            raise BridgeIntegrityError('actor item is not a dictionary')
        native=_ident(item.get('native_actor_id'), 'native_actor_id')
        if native in seen: raise BridgeIntegrityError('duplicate native actor ID in snapshot')
        seen.add(native)
        asset=_ident(item.get('asset_id'),'asset_id')
        generation=item.get('generation')
        if generation is not None and (isinstance(generation,bool) or not isinstance(generation,int) or generation<0):
            raise BridgeIntegrityError('invalid generation')
        row={'native_actor_id':native,'asset_id':asset,
             'name':item.get('name') if isinstance(item.get('name'),str) else None,
             'x':item.get('x'),'y':item.get('y'),
             'parent_id_1':str(item['parent_id_1']) if item.get('parent_id_1') is not None else None,
             'parent_id_2':str(item['parent_id_2']) if item.get('parent_id_2') is not None else None,
             'generation':generation,'nutrition':item.get('nutrition'),'stamina':item.get('stamina'),
             'native_created_time':item.get('native_created_time')}
        result.append(row)
    result.sort(key=lambda a:a['native_actor_id'])
    return {'world_seed':seed,'tick':tick,'count':len(result)},result

_SCHEMA="""
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS world (
 world_id TEXT PRIMARY KEY, world_seed INTEGER NOT NULL, epoch INTEGER NOT NULL DEFAULT 0,
 last_tick INTEGER, last_digest TEXT
);
CREATE TABLE IF NOT EXISTS actor_link (
 world_id TEXT NOT NULL, native_actor_id TEXT NOT NULL, core_actor_id TEXT NOT NULL UNIQUE,
 worldbox_asset_id TEXT NOT NULL, core_species TEXT NOT NULL,
 initial_generation INTEGER, first_epoch INTEGER NOT NULL, first_tick INTEGER NOT NULL,
 last_epoch INTEGER NOT NULL, last_tick INTEGER NOT NULL, seen_in_last_snapshot INTEGER NOT NULL DEFAULT 0,
 last_native_json TEXT,
 PRIMARY KEY(world_id,native_actor_id), FOREIGN KEY(world_id) REFERENCES world(world_id)
);
CREATE TABLE IF NOT EXISTS snapshot_log (
 world_id TEXT NOT NULL, epoch INTEGER NOT NULL, tick INTEGER NOT NULL,
 digest TEXT NOT NULL, native_count INTEGER NOT NULL, mapped_count INTEGER NOT NULL,
 PRIMARY KEY(world_id,epoch,tick)
);
"""

class ActorRegistry:
    def __init__(self,path: str | Path):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
        self.db=sqlite3.connect(str(self.path),isolation_level=None)
        self.db.row_factory=sqlite3.Row
        self.db.executescript(_SCHEMA)
    @contextmanager
    def _transaction(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
        except BaseException:
            self.db.execute('ROLLBACK')
            raise
        else:
            self.db.execute('COMMIT')
    def close(self):self.db.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def init_world(self,world_id: str,seed: int):
        world_id=_ident(world_id,'world_id')
        if isinstance(seed,bool) or not isinstance(seed,int):raise BridgeIntegrityError('seed is not an integer')
        existing=self.db.execute('SELECT world_seed FROM world WHERE world_id=?',(world_id,)).fetchone()
        if existing is not None and existing['world_seed']!=seed:
            raise BridgeIntegrityError('World seed changed for existing world_id: explicit migration required')
        if existing is None:
            self.db.execute('INSERT INTO world(world_id,world_seed) VALUES(?,?)',(world_id,seed))
    def new_epoch(self,world_id: str):
        """Explicit change after a verified world load/switch; no implicit tick rollback."""
        row=self.db.execute('SELECT epoch FROM world WHERE world_id=?',(world_id,)).fetchone()
        if row is None:raise BridgeIntegrityError('unknown world')
        self.db.execute('UPDATE world SET epoch=?,last_tick=NULL,last_digest=NULL WHERE world_id=?',(row['epoch']+1,world_id))
        return row['epoch']+1
    def _world(self,world_id):
        row=self.db.execute('SELECT * FROM world WHERE world_id=?',(world_id,)).fetchone()
        if row is None:raise BridgeIntegrityError('unknown World Tree; register explicitly')
        return row
    def enroll(self,world_id: str,native_actor_id: str,core_actor_id: str,asset_id: str,core_species: str,
               generation: int|None=None,tick: int=0):
        """Only explicit pairings; never infer identity by matching species, name, or coordinates."""
        native_actor_id=_ident(native_actor_id,'native_actor_id');core_actor_id=_ident(core_actor_id,'core_actor_id')
        asset_id=_ident(asset_id,'asset_id');core_species=_ident(core_species,'core_species')
        world=self._world(world_id)
        if generation is not None and (not isinstance(generation,int) or generation<0):raise BridgeIntegrityError('bad generation')
        with self._transaction():
            match=self.db.execute('SELECT * FROM actor_link WHERE world_id=? AND native_actor_id=?',(world_id,native_actor_id)).fetchone()
            if match:
                if (match['core_actor_id'],match['worldbox_asset_id'],match['core_species'])!=(core_actor_id,asset_id,core_species):
                    raise BridgeIntegrityError('native actor already bound to different core actor/species')
                return False
            if self.db.execute('SELECT 1 FROM actor_link WHERE core_actor_id=?',(core_actor_id,)).fetchone():
                raise BridgeIntegrityError('Core actor already mapped elsewhere')
            self.db.execute('''INSERT INTO actor_link(world_id,native_actor_id,core_actor_id,worldbox_asset_id,core_species,
             initial_generation,first_epoch,first_tick,last_epoch,last_tick) VALUES(?,?,?,?,?,?,?,?,?,?)''',
              (world_id,native_actor_id,core_actor_id,asset_id,core_species,generation,world['epoch'],tick,world['epoch'],tick))
        return True
    def observe(self,world_id: str,snapshot: dict):
        meta,items=normalize_snapshot(snapshot)
        w=self._world(world_id)
        if meta['world_seed']!=w['world_seed']:
            raise BridgeIntegrityError('visible WorldBox map does not match registered World Tree seed')
        tick=meta['tick'];epoch=w['epoch'];
        if w['last_tick'] is not None and tick<w['last_tick']:
            raise BridgeIntegrityError('WorldBox tick went backwards: explicit new_epoch required after load')
        digest=hashlib.sha256(json.dumps(items,sort_keys=True,separators=(',',':')).encode()).hexdigest()
        old=self.db.execute('SELECT digest FROM snapshot_log WHERE world_id=? AND epoch=? AND tick=?',(world_id,epoch,tick)).fetchone()
        if old is not None and old['digest']!=digest:
            raise BridgeIntegrityError('same world/epoch/tick yielded conflicting native state')
        paired=[];unmapped=[];native_ids=set()
        for a in items:
            native_ids.add(a['native_actor_id'])
            link=self.db.execute('SELECT * FROM actor_link WHERE world_id=? AND native_actor_id=?',
                (world_id,a['native_actor_id'])).fetchone()
            if link:
                if link['worldbox_asset_id']!=a['asset_id']:
                    raise BridgeIntegrityError('mapped actor changed asset/species unexpectedly')
                if link['last_native_json']:
                    prior=json.loads(link['last_native_json'])
                    if (prior.get('native_created_time') is not None and a.get('native_created_time') is not None
                            and prior['native_created_time']!=a['native_created_time']):
                        raise BridgeIntegrityError('native ID possibly reused: actor creation marker changed')
                    for parent_field in ('parent_id_1','parent_id_2'):
                        if (prior.get(parent_field) not in (None,'','-1','0') and
                                a.get(parent_field) not in (None,'','-1','0') and
                                prior[parent_field]!=a[parent_field]):
                            raise BridgeIntegrityError('native actor lineage changed unexpectedly')
                paired.append({'native_actor_id':a['native_actor_id'],'core_actor_id':link['core_actor_id'],
                    'core_species':link['core_species'],'native_generation':a['generation'],
                    'native_nutrition':a['nutrition'],'native_stamina':a['stamina']})
            else:unmapped.append(a['native_actor_id'])
        # Entire batch remains atomic; any error above leaves the previous snapshot intact.
        with self._transaction():
            if old is None:
                self.db.execute('INSERT INTO snapshot_log VALUES(?,?,?,?,?,?)',(world_id,epoch,tick,digest,len(items),len(paired)))
                self.db.execute('UPDATE actor_link SET seen_in_last_snapshot=0 WHERE world_id=?',(world_id,))
                for link in paired:
                    self.db.execute('''UPDATE actor_link SET last_epoch=?,last_tick=?,seen_in_last_snapshot=1
                        WHERE world_id=? AND native_actor_id=?''',(epoch,tick,world_id,link['native_actor_id']))
            if old is None:
                for a in items:
                    if a['native_actor_id'] in {link['native_actor_id'] for link in paired}:
                        self.db.execute('''UPDATE actor_link SET last_native_json=? WHERE world_id=? AND native_actor_id=?''',
                        (json.dumps(a,sort_keys=True),world_id,a['native_actor_id']))
            self.db.execute('UPDATE world SET last_tick=?,last_digest=? WHERE world_id=?',(tick,digest,world_id))
        return {'world_id':world_id,'epoch':epoch,'tick':tick,'native_count':len(items),
                'mapped_count':len(paired),'unmapped_count':len(unmapped),
                'unmapped_native_ids':unmapped,'pairs':paired,'replayed':old is not None,'digest':digest}
    def links(self,world_id: str):
        self._world(world_id)
        return [dict(r) for r in self.db.execute('SELECT * FROM actor_link WHERE world_id=? ORDER BY native_actor_id',(world_id,))]
    def snapshots(self,world_id: str):
        return [dict(r) for r in self.db.execute('SELECT * FROM snapshot_log WHERE world_id=? ORDER BY epoch,tick',(world_id,))]
