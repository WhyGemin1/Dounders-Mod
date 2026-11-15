"""M05 Founders–CIV WorldBox living-energy sidecar.

The database is authoritative ONLY for M05 virtual BIO and CE assets.
WorldBox remains authoritative for native animal physiology and terrain.
Core151's real Book is NOT included and is not modified by this package.
Native WorldBox 'nutrition' never becomes virtual BIO.

No action-point costs. Time is a monotonically numbered *observation interval*,
not a currency. M05 model parameters are hypothetical until calibrated.
"""
from __future__ import annotations
import hashlib
import json
import math
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

BIO = 'bio_equiv'
CE = 'creation_charge'
SCHEMA = 6
BLUEPRINTS = {'creation': (5, 20), 'world_seed': (12, 45), 'realm_link': (15, 80)}
EXPECTED_ASSEMBLY_SHA = '51d275f0168be2f6ca26341ab292406714e694e0270eafcb25b999d5df6dd69f'
EXPECTED_HOOKS = {'Actor.addNutritionFromEating', 'ai.behaviours.BehConsumeActorTarget.consume', 'Actor.consumeFoodResource', 'Actor.newKillAction', 'Actor.die', 'ActorManager.createBabyActorFromData', 'Actor.birthEvent'}

class IntegrationError(ValueError): pass


def canonical(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(',', ':'), ensure_ascii=False, allow_nan=False)

def digest(obj: Any) -> str:
    return hashlib.sha256(canonical(obj).encode('utf-8')).hexdigest()

def normalized_id(text: str) -> str:
    if not isinstance(text, str) or not (1 <= len(text) <= 120):
        raise IntegrationError('identifier required: 1–120 characters')
    if not all(c.isalnum() or c in '_-.:' for c in text):
        raise IntegrationError('invalid identifier: ' + str(text))
    return text

def proportion(value: Any, name: str) -> float:
    if type(value) not in (float, int) or not math.isfinite(value) or not 0 <= value <= 1:
        raise IntegrationError(name + ' must be finite and in [0,1]')
    return float(value)

def positive_int(value: Any, name: str, zero: bool=False) -> int:
    if type(value) is not int or value < (0 if zero else 1) or value > 10**12:
        raise IntegrationError(name + ' must be a bounded integer')
    return value

class Store:
    def __init__(self, db: str):
        self.db_path = Path(db)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(self.db_path), timeout=30, isolation_level=None)
        self.db.row_factory = sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA busy_timeout=30000')
        self.db.execute('PRAGMA journal_mode=WAL')
        self.db.execute('PRAGMA synchronous=FULL')
        self.db.executescript('''
        CREATE TABLE IF NOT EXISTS meta(k TEXT PRIMARY KEY, v TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS balances(asset TEXT NOT NULL, account TEXT NOT NULL, amount INTEGER NOT NULL,
          PRIMARY KEY(asset,account));
        CREATE TABLE IF NOT EXISTS transfers(tx TEXT PRIMARY KEY,asset TEXT NOT NULL,
          source TEXT NOT NULL,dest TEXT NOT NULL,amount INTEGER NOT NULL CHECK(amount>0));
        CREATE TABLE IF NOT EXISTS trees(tree_id TEXT PRIMARY KEY,age INTEGER NOT NULL DEFAULT 0,
          health REAL NOT NULL DEFAULT .85, alive INTEGER NOT NULL DEFAULT 1,
          fruit_counter INTEGER NOT NULL DEFAULT 0, config_json TEXT NOT NULL,
          parent_attempt TEXT, native_status TEXT NOT NULL DEFAULT 'virtual_pending');
        CREATE TABLE IF NOT EXISTS fruits(fruit_id TEXT PRIMARY KEY,tree_id TEXT NOT NULL,
          born_period INTEGER NOT NULL,bio INTEGER NOT NULL,ce INTEGER NOT NULL,
          status TEXT NOT NULL,founder_id TEXT,FOREIGN KEY(tree_id) REFERENCES trees(tree_id));
        CREATE TABLE IF NOT EXISTS founders(founder_id TEXT PRIMARY KEY,fatigue REAL NOT NULL DEFAULT .15,
          integrity REAL NOT NULL DEFAULT 1,efficiency REAL NOT NULL DEFAULT .8);
        CREATE TABLE IF NOT EXISTS attempts(attempt_id TEXT PRIMARY KEY,founder_id TEXT NOT NULL,
          kind TEXT NOT NULL,bio INTEGER NOT NULL,ce INTEGER NOT NULL,
          state TEXT NOT NULL, FOREIGN KEY(founder_id) REFERENCES founders(founder_id));
        CREATE TABLE IF NOT EXISTS operations(op_id TEXT PRIMARY KEY,kind TEXT NOT NULL,
          input_hash TEXT NOT NULL,result_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS periods(period INTEGER PRIMARY KEY,input_hash TEXT NOT NULL,result_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS native_events(session_id TEXT NOT NULL,seq INTEGER NOT NULL,
          world_key TEXT NOT NULL,kind TEXT NOT NULL,actor_id TEXT,event_hash TEXT NOT NULL,
          data_json TEXT NOT NULL,PRIMARY KEY(session_id,seq));
        CREATE TABLE IF NOT EXISTS native_issues(issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
          code TEXT NOT NULL,description TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS snapshots(capture_id TEXT PRIMARY KEY,world_key TEXT NOT NULL,
          session_id TEXT NOT NULL,source_hash TEXT NOT NULL,native_tick TEXT,
          actor_count INTEGER NOT NULL);
        CREATE TABLE IF NOT EXISTS snapshot_actors(capture_id TEXT NOT NULL,actor_id TEXT NOT NULL,
          species TEXT,generation TEXT,creation_marker TEXT,parent_1 TEXT,parent_2 TEXT,
          PRIMARY KEY(capture_id,actor_id),FOREIGN KEY(capture_id) REFERENCES snapshots(capture_id));
        ''')
        row = self.db.execute("SELECT v FROM meta WHERE k='schema'").fetchone()
        if row is not None and int(row['v']) != SCHEMA:
            raise IntegrationError('DB schema mismatch; back up and migrate explicitly')
        if row is None:
            self.db.execute('INSERT INTO meta VALUES (?,?)', ('schema',str(SCHEMA)))

    def close(self): self.db.close()
    def meta(self, key: str, default=None):
        row = self.db.execute('SELECT v FROM meta WHERE k=?', (key,)).fetchone()
        return row['v'] if row else default

    @contextmanager
    def atomic(self):
        self.db.execute('BEGIN IMMEDIATE')
        try:
            yield
            self.db.execute('COMMIT')
        except BaseException:
            self.db.execute('ROLLBACK')
            raise

    def initialize(self, world_key: str):
        world_key=normalized_id(world_key)
        with self.atomic():
            prev = self.meta('world_key')
            if prev is not None and prev != world_key:
                raise IntegrationError('World identity mismatch: refused different save. Use a new database.')
            if prev is None:
                self.db.execute('INSERT INTO meta VALUES (?,?)', ('world_key',world_key))
                self.db.execute('INSERT INTO meta VALUES (?,?)', ('last_period','0'))
        return {'world_key':world_key,'initialized':True}

    def require_world(self):
        world=self.meta('world_key')
        if not world: raise IntegrationError('Initialize with init --world-key first')
        return world

    def balance(self, asset: str, account: str) -> int:
        row = self.db.execute('SELECT amount FROM balances WHERE asset=? AND account=?',(asset,account)).fetchone()
        return row['amount'] if row else 0

    def transfer(self, tx: str, asset: str, source: str, dest: str, amount: int):
        """Call within Store.atomic(). Exactly-once, replay conflict checked."""
        tx=normalized_id(tx)
        if asset not in (BIO,CE): raise IntegrationError('Unsupported asset')
        if not source or not dest or source==dest: raise IntegrationError('invalid transfer accounts')
        amount=positive_int(amount,'amount')
        old=self.db.execute('SELECT asset,source,dest,amount FROM transfers WHERE tx=?',(tx,)).fetchone()
        record=(asset,source,dest,amount)
        if old is not None:
            if tuple(old) != record: raise IntegrationError('conflicting transfer replay '+tx)
            return False
        available=self.balance(asset,source)
        if available<amount and not source.startswith('external:'):
            raise IntegrationError('insufficient '+asset+' in '+source)
        for account,delta in ((source,-amount),(dest,amount)):
            self.db.execute('INSERT INTO balances(asset,account,amount) VALUES(?,?,?) '
              'ON CONFLICT(asset,account) DO UPDATE SET amount=amount+excluded.amount',(asset,account,delta))
        self.db.execute('INSERT INTO transfers VALUES (?,?,?,?,?)',(tx,asset,source,dest,amount))
        return True

    def operation(self, op_id: str, kind: str, inputs: dict, work):
        op_id=normalized_id(op_id)
        h=digest({'kind':kind,'inputs':inputs})
        with self.atomic():
            old=self.db.execute('SELECT kind,input_hash,result_json FROM operations WHERE op_id=?',(op_id,)).fetchone()
            if old:
                if old['kind']!=kind or old['input_hash']!=h:
                    raise IntegrationError('conflicting operation replay '+op_id)
                return json.loads(old['result_json'])
            result=work()
            self.db.execute('INSERT INTO operations VALUES (?,?,?,?)',(op_id,kind,h,canonical(result)))
            return result

    def add_founder(self, founder_id: str):
        founder_id=normalized_id(founder_id)
        with self.atomic():
            self.db.execute('INSERT OR IGNORE INTO founders(founder_id) VALUES (?)',(founder_id,))
        return {'founder_id':founder_id}

    def add_tree(self, tree_id: str, config: dict, *, parent_attempt=None, native_status='virtual_pending'):
        tree_id=normalized_id(tree_id)
        config=validate_tree_config(config)
        def work():
            if self.db.execute('SELECT 1 FROM trees WHERE tree_id=?',(tree_id,)).fetchone():
                raise IntegrationError('tree ID already exists')
            self.db.execute('INSERT INTO trees(tree_id,config_json,parent_attempt,native_status) VALUES(?,?,?,?)',
                            (tree_id,canonical(config),parent_attempt,native_status))
            return {'tree_id':tree_id,'native_status':native_status,'habitats':[h['id'] for h in config['habitats']]}
        return self.operation('add_tree:'+tree_id,'add_tree',{'config':config,'parent':parent_attempt},work)

    def _allocate_river(self, requests: dict[str,int], supply: int, period: int):
        """Deterministic water-filling with rotating remainder priority."""
        alloc={k:0 for k in requests}
        left=min(supply,sum(requests.values()))
        keys=sorted(requests)
        if not keys:return alloc
        cursor=period % len(keys)
        while left>0:
            candidates=[k for k in keys if alloc[k]<requests[k]]
            if not candidates: break
            base=left//len(candidates)
            if base:
                for k in candidates:
                    n=min(base,requests[k]-alloc[k]); alloc[k]+=n;left-=n
            if left<=0:break
            advanced=False
            for i in range(len(keys)):
                k=keys[(cursor+i)%len(keys)]
                if alloc[k]<requests[k] and left:
                    alloc[k]+=1;left-=1;advanced=True
            cursor=(cursor+1)%len(keys)
            if not advanced:break
        return alloc

    def cycle(self, period: int, river_supply: int, conditions: dict|None=None):
        """A period is an externally observed ordinal, never WorldBox tick and never spendable time.
        Conditions keyed by tree and habitat; all values scenario inputs until sourced.
        """
        period=positive_int(period,'period')
        river_supply=positive_int(river_supply,'river_supply',True)
        conditions=conditions or {}
        if not isinstance(conditions,dict):raise IntegrationError('conditions must be object')
        normalized=digest({'period':period,'river_supply':river_supply,'conditions':conditions})
        with self.atomic():
            old=self.db.execute('SELECT input_hash,result_json FROM periods WHERE period=?',(period,)).fetchone()
            if old:
                if old['input_hash']!=normalized:raise IntegrationError('conflicting period replay')
                return json.loads(old['result_json'])
            last=int(self.meta('last_period','0'))
            if period != last+1: raise IntegrationError('period must be exactly '+str(last+1)+'; never use WorldBox tick as timeline')
            if river_supply:
                self.transfer('river:'+str(period)+':input',CE,'external:river_source','world:river',river_supply)
            # Fruits have a real lifespan in *observation periods* and decay in the virtual resource ledger.
            expired=[]
            for f in self.db.execute("SELECT * FROM fruits WHERE status='on_tree'").fetchall():
                cfg=json.loads(self.db.execute('SELECT config_json FROM trees WHERE tree_id=?',(f['tree_id'],)).fetchone()['config_json'])
                if period-f['born_period'] >= cfg['fruit_ttl']:
                    b=f['bio'];c=f['ce'];fid=f['fruit_id']
                    self.transfer('decay:'+fid+':bio',BIO,'fruit:'+fid+':matter','sink:decomposition',b)
                    self.transfer('decay:'+fid+':ce',CE,'fruit:'+fid+':charge','world:river',c)
                    self.db.execute("UPDATE fruits SET status='decayed' WHERE fruit_id=?",(fid,))
                    expired.append(fid)
            tree_rows=self.db.execute('SELECT * FROM trees WHERE alive=1 ORDER BY tree_id').fetchall()
            requests={r['tree_id']:json.loads(r['config_json'])['river_request'] for r in tree_rows}
            allocation=self._allocate_river(requests,self.balance(CE,'world:river'),period)
            results={}
            for r in tree_rows:
                tree_id=r['tree_id'];cfg=json.loads(r['config_json']);age=r['age']+1;health=r['health']
                observation=conditions.get(tree_id,{})
                if not isinstance(observation,dict):raise IntegrationError('conditions tree must be an object')
                unknown=set(observation)-{h['id'] for h in cfg['habitats']}
                if unknown:raise IntegrationError('unknown habitat conditions '+str(sorted(unknown)))
                bio_account='tree:'+tree_id+':bio'
                capture=0; habitat_reports=[]; support=0.0
                for h in cfg['habitats']:
                    overrides=observation.get(h['id'],{})
                    if not isinstance(overrides,dict):raise IntegrationError('habitat override must be object')
                    if set(overrides)-{'light','water','nutrients','support'}:
                        raise IntegrationError('unexpected habitat metric')
                    light=proportion(overrides.get('light',h['light']),'light')
                    water=proportion(overrides.get('water',h['water']),'water')
                    nutrients=proportion(overrides.get('nutrients',h['nutrients']),'nutrients')
                    habitat_support=proportion(overrides.get('support',h['support']),'support')
                    support+=h['weight']*habitat_support
                    rate=int(cfg['canopy_capture']*h['weight']*light*water*nutrients*(.35+.65*health))
                    capture+=rate
                    habitat_reports.append({'habitat':h['id'],'capture':rate,'support':habitat_support})
                if capture:
                    self.transfer('tree:'+tree_id+':'+str(period)+':solar',BIO,
                                  'external:solar',bio_account,capture)
                charge=allocation[tree_id]
                if charge:
                    self.transfer('tree:'+tree_id+':'+str(period)+':river',CE,
                                  'world:river','tree:'+tree_id+':charge',charge)
                maintenance=min(cfg['maintenance'],self.balance(BIO,bio_account))
                if maintenance:
                    self.transfer('tree:'+tree_id+':'+str(period)+':maintenance',BIO,bio_account,
                                  'sink:respiration',maintenance)
                food_needed=int(cfg['food_web_provision']*support)
                food=min(self.balance(BIO,bio_account),food_needed)
                if food:
                    self.transfer('tree:'+tree_id+':'+str(period)+':foodweb',BIO,
                                  bio_account,'tree:'+tree_id+':foodweb',food)
                # Previous virtual food-web allocation is metabolized/returned to the boundary,
                # not mirrored into WorldBox native animals.
                food_available=self.balance(BIO,'tree:'+tree_id+':foodweb')
                turnover=min(food_available,max(0,int(food_available*.25)))
                if turnover:
                    self.transfer('tree:'+tree_id+':'+str(period)+':foodturn',BIO,
                                  'tree:'+tree_id+':foodweb','sink:virtual_foodweb_metabolism',turnover)
                scarcity=(cfg['maintenance']-maintenance)/max(1,cfg['maintenance'])
                health=max(0.,min(1.,health+.025*support-.045*(1-support)-.13*scarcity))
                fruits=[]
                healthy=(age>=cfg['mature_at'] and health>=cfg['fruit_health_floor'] and support>=.5
                         and maintenance==cfg['maintenance'] and food>=max(1,int(cfg['food_web_provision']*.5)))
                number=r['fruit_counter']
                if healthy:
                    while (self.balance(BIO,bio_account)>=cfg['reserve_floor']+cfg['fruit_bio']
                         and self.balance(CE,'tree:'+tree_id+':charge')>=cfg['fruit_charge']):
                        number+=1;fid=tree_id+'-F'+str(number).zfill(7)
                        self.transfer('fruit:'+fid+':grow-bio',BIO,bio_account,'fruit:'+fid+':matter',cfg['fruit_bio'])
                        self.transfer('fruit:'+fid+':grow-ce',CE,'tree:'+tree_id+':charge','fruit:'+fid+':charge',cfg['fruit_charge'])
                        self.db.execute('INSERT INTO fruits VALUES (?,?,?,?,?,?,?)',
                                        (fid,tree_id,period,cfg['fruit_bio'],cfg['fruit_charge'],'on_tree',None))
                        fruits.append(fid)
                self.db.execute('UPDATE trees SET age=?,health=?,alive=?,fruit_counter=? WHERE tree_id=?',
                                (age,health,int(health>0),number,tree_id))
                results[tree_id]={'age':age,'health':round(health,4),'alive':health>0,'capture':capture,
                                  'river_allocated':charge,'maintenance':maintenance,'food_web':food,
                                  'habitats':habitat_reports,'fruits':fruits}
            result={'period':period,'source':'hypothetical_conditions_not_native_calibration',
                    'river_supply':river_supply,'river_remaining':self.balance(CE,'world:river'),
                    'trees':results,'expired_fruit':expired}
            self.db.execute('INSERT INTO periods VALUES (?,?,?)',(period,normalized,canonical(result)))
            self.db.execute("UPDATE meta SET v=? WHERE k='last_period'",(str(period),))
            return result

    def harvest(self, fruit_id: str, founder_id: str, op_id: str):
        fruit_id=normalized_id(fruit_id);founder_id=normalized_id(founder_id)
        def work():
            f=self.db.execute('SELECT * FROM fruits WHERE fruit_id=?',(fruit_id,)).fetchone()
            if not f or f['status']!='on_tree':raise IntegrationError('fruit unavailable (harvested, decayed, or unknown)')
            if not self.db.execute('SELECT 1 FROM founders WHERE founder_id=?',(founder_id,)).fetchone():
                raise IntegrationError('founder not registered')
            self.transfer('harvest:'+fruit_id+':bio',BIO,'fruit:'+fruit_id+':matter',
                          'founder:'+founder_id+':matter',f['bio'])
            self.transfer('harvest:'+fruit_id+':ce',CE,'fruit:'+fruit_id+':charge',
                          'founder:'+founder_id+':charge',f['ce'])
            self.db.execute("UPDATE fruits SET status='harvested',founder_id=? WHERE fruit_id=?",(founder_id,fruit_id))
            return {'fruit_id':fruit_id,'owner':founder_id,'bio':f['bio'],'ce':f['ce'],'state':'harvested'}
        return self.operation(op_id,'harvest',{'fruit_id':fruit_id,'founder_id':founder_id},work)

    def create(self, attempt_id: str, founder_id: str, kind: str):
        attempt_id=normalized_id(attempt_id);founder_id=normalized_id(founder_id)
        if kind not in BLUEPRINTS:raise IntegrationError('unknown creation kind')
        def work():
            if not self.db.execute('SELECT 1 FROM founders WHERE founder_id=?',(founder_id,)).fetchone():
                raise IntegrationError('founder not registered')
            bio,ce=BLUEPRINTS[kind]
            enough=(self.balance(BIO,'founder:'+founder_id+':matter')>=bio and
                    self.balance(CE,'founder:'+founder_id+':charge')>=ce)
            state='funded_seed_awaiting_native_execution' if enough else 'unfunded_design'
            if enough:
                self.transfer('create:'+attempt_id+':bio',BIO,'founder:'+founder_id+':matter',
                              'creation:'+attempt_id+':matter',bio)
                self.transfer('create:'+attempt_id+':ce',CE,'founder:'+founder_id+':charge',
                              'creation:'+attempt_id+':charge',ce)
            self.db.execute('INSERT INTO attempts VALUES (?,?,?,?,?,?)',
                            (attempt_id,founder_id,kind,bio,ce,state))
            return {'attempt_id':attempt_id,'founder':founder_id,'kind':kind,'state':state,
                    'native_object_created':False,'requirements':{'bio':bio,'ce':ce}}
        return self.operation('create:'+attempt_id,'create',{'founder_id':founder_id,'kind':kind},work)

    def establish_tree(self, tree_id: str, attempt_id: str, config: dict):
        tree_id=normalized_id(tree_id);attempt_id=normalized_id(attempt_id)
        config=validate_tree_config(config)
        def work():
            attempt=self.db.execute('SELECT kind,state FROM attempts WHERE attempt_id=?',(attempt_id,)).fetchone()
            if not attempt or attempt['kind']!='world_seed' or attempt['state']!='funded_seed_awaiting_native_execution':
                raise IntegrationError('need one unspent funded world_seed')
            if self.db.execute('SELECT 1 FROM trees WHERE parent_attempt=?',(attempt_id,)).fetchone():
                raise IntegrationError('world seed already established')
            self.db.execute('INSERT INTO trees(tree_id,config_json,parent_attempt,native_status) VALUES(?,?,?,?)',
                            (tree_id,canonical(config),attempt_id,'virtual_pending'))
            self.db.execute("UPDATE attempts SET state='virtual_tree_established_native_pending' WHERE attempt_id=?",(attempt_id,))
            return {'tree_id':tree_id,'parent_attempt':attempt_id,'native_status':'virtual_pending',
                    'native_object_created':False}
        return self.operation('establish:'+tree_id,'establish_tree',{'attempt_id':attempt_id,'config':config},work)

    def feed_virtual(self, founder_id: str, tree_id: str, amount: int, event_id: str):
        founder_id=normalized_id(founder_id);tree_id=normalized_id(tree_id)
        amount=positive_int(amount,'amount')
        def work():
            if not self.db.execute('SELECT 1 FROM founders WHERE founder_id=?',(founder_id,)).fetchone():
                raise IntegrationError('founder not registered')
            self.transfer('feed:'+event_id,BIO,'tree:'+tree_id+':foodweb','body:'+founder_id+':gut',amount)
            return {'founder':founder_id,'tree':tree_id,'virtual_ingestion':amount,
                    'worldbox_native_actor_modified':False}
        return self.operation('feed:'+event_id,'virtual_feed',
              {'founder_id':founder_id,'tree_id':tree_id,'amount':amount},work)

    def body_cycle(self, founder_id: str, cycle_id: str, rest_fraction: float, observed_workload: float):
        founder_id=normalized_id(founder_id);cycle_id=normalized_id(cycle_id)
        rest_fraction=proportion(rest_fraction,'rest_fraction')
        if type(observed_workload) not in (int,float) or not math.isfinite(observed_workload) or not 0<=observed_workload<=10:
            raise IntegrationError('workload must be finite and 0–10')
        def work():
            f=self.db.execute('SELECT * FROM founders WHERE founder_id=?',(founder_id,)).fetchone()
            if not f:raise IntegrationError('founder not registered')
            gut='body:'+founder_id+':gut';fuel='body:'+founder_id+':fuel'
            digested=min(self.balance(BIO,gut),int(5+7*rest_fraction))
            assimilated=int(digested*f['efficiency'])
            if assimilated:self.transfer('body:'+cycle_id+':absorb',BIO,gut,fuel,assimilated)
            if digested-assimilated:self.transfer('body:'+cycle_id+':waste',BIO,gut,'sink:digestive_loss',digested-assimilated)
            demand=max(1,int(2+3*observed_workload))
            burned=min(self.balance(BIO,fuel),demand)
            if burned:self.transfer('body:'+cycle_id+':metabolism',BIO,fuel,'sink:metabolic_heat',burned)
            shortage=demand-burned
            fatigue=max(0.,min(1.,f['fatigue']+.11*observed_workload+.12*shortage-.28*rest_fraction))
            integrity=max(0.,min(1.,f['integrity']-.018*shortage+(.012*rest_fraction if burned==demand else 0)))
            self.db.execute('UPDATE founders SET fatigue=?,integrity=? WHERE founder_id=?',(fatigue,integrity,founder_id))
            available=self.balance(BIO,fuel)
            readiness=integrity*(1-.6*fatigue)*(.3+.7*min(1.,available/16))
            return {'founder':founder_id,'cycle':cycle_id,'rest':rest_fraction,'workload':observed_workload,
                    'gut':self.balance(BIO,gut),'fuel':available,'burned':burned,'underfuel':shortage,
                    'fatigue':round(fatigue,5),'integrity':round(integrity,5),
                    'readiness':round(readiness,5),'action_selection_gated':False,
                    'native_worldbox_actor_modified':False}
        return self.operation('body:'+cycle_id,'body',
           {'founder_id':founder_id,'rest':rest_fraction,'workload':observed_workload},work)

    def ingest_events(self, jsonl_path: str):
        """Read-only native event import; all orphaned/malformed rows are quarantined.
        No BIO or CE transfers happen here. Re-import is idempotent.
        """
        self.require_world()
        inserted=duplicates=rejected=conflicts=incomplete_tail=0
        path=Path(jsonl_path)
        # Last unfinished line of actively written file is ignored, never accepted.
        with self.atomic():
            with open(path,'rb') as stream:
                for line_no,line in enumerate(stream,1):
                    if not line.strip():continue
                    if not line.endswith(b'\n'):
                        incomplete_tail+=1  # retry later after writer flushes: not a permanent import defect
                        continue
                    try:
                        event=json.loads(line.decode('utf-8'))
                        if not isinstance(event,dict):raise IntegrationError('not object')
                        if event.get('world_key')!=self.meta('world_key'):
                            raise IntegrationError('world_key mismatch')
                        sid=normalized_id(event.get('session_id',''))
                        seq=positive_int(event.get('seq'),'seq')
                        kind=normalized_id(event.get('kind',''))
                        if event.get('schema')!=1:raise IntegrationError('unexpected native schema')
                        actor=event.get('actor_id',-1)
                        if type(actor) is not int:raise IntegrationError('noninteger actor_id')
                        h=digest(event)
                        old=self.db.execute('SELECT event_hash FROM native_events WHERE session_id=? AND seq=?',(sid,seq)).fetchone()
                        if old:
                            if old['event_hash']!=h:
                                conflicts+=1
                                self.db.execute('INSERT INTO native_issues(code,description) VALUES(?,?)',
                                 ('conflicting_replay',f'{sid}:{seq} differs on line {line_no}'))
                            else:duplicates+=1
                        else:
                            self.db.execute('INSERT INTO native_events VALUES (?,?,?,?,?,?,?)',
                             (sid,seq,self.meta('world_key'),kind,str(actor),h,canonical(event)))
                            inserted+=1
                    except (UnicodeDecodeError,ValueError,TypeError,KeyError) as exc:
                        rejected+=1
                        self.db.execute('INSERT INTO native_issues(code,description) VALUES(?,?)',
                                        ('rejected_native_line',f'{path.name} line {line_no}: {str(exc)[:140]}'))
        return {'imported':inserted,'duplicates':duplicates,'rejected':rejected,
                'conflicts':conflicts,'incomplete_tail':incomplete_tail,'native_book_writes':0}

    def import_snapshot(self, path: str):
        """Import explicitly normalized snapshots, NOT an undocumented M02 raw schema.
        WorldBox ticks and population deltas are never used as births or deaths.
        """
        data=json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(data,dict) or data.get('schema')!='founders-native-snapshot-1':
            raise IntegrationError('snapshot requires normalized founders-native-snapshot-1 schema')
        if data.get('world_key')!=self.require_world():
            raise IntegrationError('snapshot world identity mismatch')
        capture_id=normalized_id(data.get('capture_id'))
        session_id=normalized_id(data.get('session_id'))
        actors=data.get('actors')
        if not isinstance(actors,list) or len(actors)>500000:
            raise IntegrationError('actors must be an array of at most 500000 entries')
        tick=data.get('native_tick')
        if tick is not None and type(tick) not in (str,int):raise IntegrationError('bad native_tick')
        h=digest(data)
        with self.atomic():
            prior=self.db.execute('SELECT source_hash,actor_count FROM snapshots WHERE capture_id=?',(capture_id,)).fetchone()
            if prior:
                if prior['source_hash']!=h:raise IntegrationError('conflicting snapshot replay')
                return {'capture_id':capture_id,'actors':prior['actor_count'],'replay':True}
            self.db.execute('INSERT INTO snapshots VALUES (?,?,?,?,?,?)',
                            (capture_id,self.require_world(),session_id,h,str(tick) if tick is not None else None,len(actors)))
            seen=set()
            for idx,a in enumerate(actors):
                if not isinstance(a,dict) or not isinstance(a.get('id'),(str,int)) or type(a.get('id')) is bool:
                    raise IntegrationError('actor must contain string or numeric id at index '+str(idx))
                actor_id=normalized_id(str(a['id']))
                if actor_id in seen:raise IntegrationError('duplicate actor identity '+actor_id)
                seen.add(actor_id)
                def field(key):
                    v=a.get(key)
                    if v is None:return None
                    if not isinstance(v,(str,int)) or isinstance(v,bool):raise IntegrationError('invalid actor '+key)
                    return str(v)
                self.db.execute('INSERT INTO snapshot_actors VALUES (?,?,?,?,?,?,?)',
                  (capture_id,actor_id,field('species'),field('generation'),field('creation_marker'),field('parent_1'),field('parent_2')))
        return {'capture_id':capture_id,'actors':len(actors),'replay':False,
                'physical_births_inferred':0,'physical_deaths_inferred':0}

    def compare_snapshots(self, earlier: str, later: str):
        earlier=normalized_id(earlier);later=normalized_id(later)
        for capture in (earlier,later):
            if not self.db.execute('SELECT 1 FROM snapshots WHERE capture_id=?',(capture,)).fetchone():
                raise IntegrationError('unknown snapshot '+capture)
        a={r['actor_id']:tuple(r[k] for k in ('species','generation','creation_marker','parent_1','parent_2'))
           for r in self.db.execute('SELECT * FROM snapshot_actors WHERE capture_id=?',(earlier,))}
        b={r['actor_id']:tuple(r[k] for k in ('species','generation','creation_marker','parent_1','parent_2'))
           for r in self.db.execute('SELECT * FROM snapshot_actors WHERE capture_id=?',(later,))}
        common=set(a)&set(b)
        mismatched=[key for key in common if a[key]!=b[key]]
        return {'earlier':earlier,'later':later,'earlier_count':len(a),'later_count':len(b),
                'shared_ids':len(common),'exact_identity_matches':len(common)-len(mismatched),
                'identity_conflicts':len(mismatched),'conflicting_ids_sample':sorted(mismatched)[:15],
                'earlier_only':len(set(a)-set(b)),'later_only':len(set(b)-set(a)),
                'confirmed_births':None,'confirmed_deaths':None,
                'warning':'Changes in observed ID membership are NOT proof of births or deaths. Native ticks may reset.'}

    def native_audit(self):
        sessions=[]
        for (sid,) in self.db.execute('SELECT DISTINCT session_id FROM native_events ORDER BY session_id'):
            rows=self.db.execute('SELECT seq,kind,data_json FROM native_events WHERE session_id=? ORDER BY seq',(sid,)).fetchall()
            kinds={};seqs=[];hooks=[];lost=0
            for row in rows:
                kinds[row['kind']]=kinds.get(row['kind'],0)+1;seqs.append(row['seq'])
                if row['kind']=='session_open':hooks+=json.loads(row['data_json']).get('active_hooks',[])
                if row['kind']=='bridge_loss':lost+=json.loads(row['data_json']).get('dropped',0)
            gaps=(max(seqs)-min(seqs)+1-len(seqs))+(1 if min(seqs)!=1 else 0) if seqs else 0
            open_events=[json.loads(r['data_json']) for r in rows if r['kind']=='session_open']
            sha_ok=bool(open_events) and all(r.get('assembly_sha256')==EXPECTED_ASSEMBLY_SHA for r in open_events)
            sessions.append({'session_id':sid,'events':len(rows),'first_seq':min(seqs),'last_seq':max(seqs),
               'gaps':gaps,'loss_reported':lost,'opened':'session_open' in kinds,
               'closed':'session_close' in kinds,'assembly_fingerprint_verified':sha_ok,
               'active_hooks':sorted(set(hooks)),
               'native_amounts_are_BIO':False,'usable_for_book':False,'kinds':kinds})
        issues={r['code']:r['n'] for r in self.db.execute('SELECT code,COUNT(*) n FROM native_issues GROUP BY code')}
        clean=bool(sessions) and not issues and all(s['gaps']==0 and s['loss_reported']==0 and s['opened']
                  and s['closed'] and s['assembly_fingerprint_verified'] and EXPECTED_HOOKS.issubset(set(s['active_hooks'])) for s in sessions)
        unique_actors=self.db.execute("SELECT COUNT(DISTINCT actor_id) FROM native_events WHERE actor_id IS NOT NULL AND actor_id != '-1'").fetchone()[0]
        return {'world_key':self.meta('world_key'),'observed_unique_actor_ids':unique_actors,
         'sessions':sessions,'issues':issues,'native_capture_integrity_ok':clean,
         'native_nutrition_calibrated':False,'native_to_book_transfers':0}

    def audit(self):
        balances={(r['asset'],r['account']):r['amount'] for r in self.db.execute('SELECT * FROM balances')}
        reconstructed={}
        journal=[]
        for r in self.db.execute('SELECT * FROM transfers ORDER BY rowid'):
            journal.append([r['tx'],r['asset'],r['source'],r['dest'],r['amount']])
            for account,delta in [(r['source'],-r['amount']),(r['dest'],r['amount'])]:
                key=(r['asset'],account)
                reconstructed[key]=reconstructed.get(key,0)+delta
        violations=[]
        if balances!={k:v for k,v in reconstructed.items()}:violations.append('balances_mismatch_journal')
        for (asset,account),value in balances.items():
            if value<0 and not account.startswith('external:'):violations.append('negative:'+asset+':'+account)
        total={a:sum(v for (asset,_),v in balances.items() if asset==a) for a in (BIO,CE)}
        if any(total.values()):violations.append('asset_imbalance')
        fruit_mismatches=[]
        for f in self.db.execute('SELECT * FROM fruits'):
            owner=('fruit:'+f['fruit_id']+':matter' if f['status']=='on_tree' else
                   ('founder:'+f['founder_id']+':matter' if f['status']=='harvested' else None))
            if f['status']=='on_tree' and (self.balance(BIO,'fruit:'+f['fruit_id']+':matter')!=f['bio']
                  or self.balance(CE,'fruit:'+f['fruit_id']+':charge')!=f['ce']):
                fruit_mismatches.append(f['fruit_id'])
        if fruit_mismatches:violations.append('fruit_stock_mismatch')
        return {'book_balanced':not violations,'violations':violations,'totals_including_boundary_accounts':total,
         'transfer_count':len(journal),'book_fingerprint':digest(journal),'unharvested_fruit_mismatches':fruit_mismatches,
         'last_period':int(self.meta('last_period','0')),'world_key':self.meta('world_key'),
         'native_write_enabled':False,'core151_book_connected':False}

    def status(self):
        trees=[]
        for r in self.db.execute('SELECT * FROM trees ORDER BY tree_id'):
            trees.append({'tree_id':r['tree_id'],'age':r['age'],'health':round(r['health'],5),
                          'alive':bool(r['alive']),'native_status':r['native_status'],
                          'unharvested_fruit':self.db.execute("SELECT COUNT(*) FROM fruits WHERE tree_id=? AND status='on_tree'",(r['tree_id'],)).fetchone()[0],
                          'fruit_total':r['fruit_counter']})
        founders=[]
        for f in self.db.execute('SELECT * FROM founders ORDER BY founder_id'):
            founders.append({'id':f['founder_id'],'fatigue':round(f['fatigue'],5),'integrity':round(f['integrity'],5),
                'gut':self.balance(BIO,'body:'+f['founder_id']+':gut'),
                'fuel':self.balance(BIO,'body:'+f['founder_id']+':fuel'),
                'creation_charge':self.balance(CE,'founder:'+f['founder_id']+':charge')})
        return {'world_key':self.meta('world_key'),'period':int(self.meta('last_period','0')),
         'shared_river_remaining':self.balance(CE,'world:river'),
         'trees':trees,'founders':founders,
         'funded_creations':self.db.execute("SELECT COUNT(*) FROM attempts WHERE state LIKE 'funded%' OR state LIKE 'virtual_tree%'").fetchone()[0],
         'real_worldbox_worlds_created':0,'core151_book_connected':False}

    def journal_export(self):
        """Review-only migration plan. NEVER apply automatically or create a second authoritative Book."""
        return {'schema':'founders-civ-m05-export-1','world_key':self.require_world(),
         'mode':'REVIEW_ONLY_DO_NOT_AUTO_APPLY','assets':[BIO,CE],
         'core151_book_connected':False,
         'transactions':[dict(r) for r in self.db.execute('SELECT tx,asset,source,dest,amount FROM transfers ORDER BY rowid')],
         'book_fingerprint':self.audit()['book_fingerprint']}


def validate_tree_config(config: dict) -> dict:
    if not isinstance(config,dict):raise IntegrationError('tree config must be object')
    allowed={'habitats','canopy_capture','maintenance','food_web_provision','reserve_floor',
             'fruit_bio','fruit_charge','fruit_ttl','mature_at','fruit_health_floor','river_request','anchor'}
    if set(config)-allowed: raise IntegrationError('unknown tree config fields '+str(set(config)-allowed))
    d={'canopy_capture':48,'maintenance':8,'food_web_provision':8,'reserve_floor':35,
       'fruit_bio':10,'fruit_charge':30,'fruit_ttl':6,'mature_at':12,
       'fruit_health_floor':.65,'river_request':30,'anchor':None}
    d.update(config)
    for k in ('canopy_capture','maintenance','food_web_provision','reserve_floor','fruit_bio','fruit_charge','fruit_ttl','mature_at','river_request'):
        positive_int(d[k],k,k in ('canopy_capture','maintenance','food_web_provision','reserve_floor','river_request'))
    d['fruit_health_floor']=proportion(d['fruit_health_floor'],'fruit_health_floor')
    if d['anchor'] is not None:
        anchor=d['anchor']
        if not isinstance(anchor,dict) or set(anchor)-{'x','y','radius'} or set(anchor)!={'x','y','radius'}:
            raise IntegrationError('anchor must be {x,y,radius}; map anchoring is manual until native mapping is available')
        if any(type(anchor[k]) is not int or anchor[k]<0 for k in ('x','y','radius')):
            raise IntegrationError('anchor values must be nonnegative integer tile coordinates')
        if anchor['radius']<=0:raise IntegrationError('anchor radius must exceed zero')
    habitats=d.get('habitats')
    if not isinstance(habitats,list) or len(habitats)!=4:
        raise IntegrationError('exactly four habitat definitions required')
    names=[];sum_weight=0.0
    for h in habitats:
        if not isinstance(h,dict) or set(h)!={'id','weight','light','water','nutrients','support'}:
            raise IntegrationError('habitats require id, weight, light, water, nutrients, support')
        names.append(normalized_id(h['id']))
        h['weight']=proportion(h['weight'],'habitat weight')
        if h['weight']<=0:raise IntegrationError('habitat weight must be >0')
        sum_weight+=h['weight']
        for key in ('light','water','nutrients','support'):h[key]=proportion(h[key],key)
    if len(set(names))!=4 or abs(sum_weight-1)>1e-8:
        raise IntegrationError('four unique habitats with weights totaling 1 required')
    return d
