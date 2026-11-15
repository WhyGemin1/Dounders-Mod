import copy
import json
import tempfile
import unittest
from pathlib import Path
from m05_core import Store, IntegrationError, BIO, CE, EXPECTED_ASSEMBLY_SHA, EXPECTED_HOOKS

ROOT=Path(__file__).resolve().parents[1]
TREE=json.loads((ROOT/'examples/world.json').read_text())['trees'][0]['config']

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=str(Path(self.temp.name)/'state.sqlite')
        self.s=Store(self.path);self.s.initialize('test-save-001')
        self.s.add_founder('Solace');self.s.add_tree('TREE-A',copy.deepcopy(TREE))
    def tearDown(self):self.s.close();self.temp.cleanup()
    def periods(self,n,start=1,supply=90,conditions=None):
        out=None
        for i in range(start,start+n):out=self.s.cycle(i,supply,conditions)
        return out
    def fruit(self):
        self.periods(20)
        row=self.s.db.execute("SELECT fruit_id FROM fruits WHERE status='on_tree' ORDER BY born_period DESC LIMIT 1").fetchone()
        self.assertIsNotNone(row)
        return row[0]
    def test_identity_conflict(self):
        with self.assertRaises(IntegrationError):self.s.initialize('different-world')
    def test_setup_idempotent(self):
        self.assertEqual(self.s.add_tree('TREE-A',copy.deepcopy(TREE))['tree_id'],'TREE-A')
        self.assertEqual(len(self.s.status()['trees']),1)
    def test_conflicting_tree_definition_rejected(self):
        cfg=copy.deepcopy(TREE);cfg['canopy_capture']=17
        with self.assertRaises(IntegrationError):self.s.add_tree('TREE-A',cfg)
    def test_four_unique_habitats(self):
        cfg=copy.deepcopy(TREE);cfg['habitats'][0]['id']='ridge'
        with self.assertRaises(IntegrationError):self.s.add_tree('other',cfg)
    def test_weights_prevent_fourfold_capture(self):
        self.s.cycle(1,0)
        c=self.s.balance(BIO,'tree:TREE-A:bio')+self.s.balance(BIO,'tree:TREE-A:foodweb')
        self.assertLess(c,53)
    def test_no_fruit_without_charge(self):
        self.periods(20,supply=0)
        self.assertEqual(self.s.status()['trees'][0]['fruit_total'],0)
    def test_no_fruit_without_biology(self):
        cond={'TREE-A':{h['id']:{'light':0} for h in TREE['habitats']}}
        self.periods(30,supply=500,conditions=cond)
        self.assertEqual(self.s.status()['trees'][0]['fruit_total'],0)
        self.assertFalse(self.s.status()['trees'][0]['alive'])
    def test_sunlight_is_external_boundary(self):
        self.periods(20)
        a=self.s.audit()
        self.assertTrue(a['book_balanced'],a)
        self.assertEqual(a['totals_including_boundary_accounts'],{BIO:0,CE:0})
    def test_no_time_currency(self):
        r=self.s.cycle(1,50)
        self.assertEqual(r['period'],1)
        self.assertNotIn('time_debit',r)
    def test_period_idempotency(self):
        r=self.s.cycle(1,20)
        n=self.s.audit()['transfer_count']
        self.assertEqual(self.s.cycle(1,20),r)
        self.assertEqual(self.s.audit()['transfer_count'],n)
        with self.assertRaises(IntegrationError):self.s.cycle(1,21)
        with self.assertRaises(IntegrationError):self.s.cycle(3,20)
    def test_persist_reopen(self):
        self.periods(15)
        before=self.s.audit();status=self.s.status()
        self.s.close();self.s=Store(self.path)
        self.assertEqual(self.s.audit()['book_fingerprint'],before['book_fingerprint'])
        self.assertEqual(self.s.status(),status)
    def test_worldbox_native_not_modified(self):
        f=self.fruit()
        self.assertEqual(self.s.harvest(f,'Solace','harvest-1')['state'],'harvested')
        self.assertFalse(self.s.create('design-1','Solace','creation')['native_object_created'])
    def test_harvest_replay_and_conflicts(self):
        f=self.fruit()
        first=self.s.harvest(f,'Solace','harvest-1')
        n=self.s.audit()['transfer_count']
        self.assertEqual(self.s.harvest(f,'Solace','harvest-1'),first)
        self.assertEqual(n,self.s.audit()['transfer_count'])
        self.s.add_founder('Jamun')
        with self.assertRaises(IntegrationError):self.s.harvest(f,'Jamun','harvest-2')
        with self.assertRaises(IntegrationError):self.s.harvest(f,'Jamun','harvest-1')
    def test_fruit_decay_releases_charge(self):
        self.periods(23)
        decayed=self.s.db.execute("SELECT COUNT(*) FROM fruits WHERE status='decayed'").fetchone()[0]
        self.assertGreater(decayed,0)
        self.assertTrue(self.s.audit()['book_balanced'])
    def test_unfunded_creation_is_permitted_design(self):
        r=self.s.create('c1','Solace','world_seed')
        self.assertEqual(r['state'],'unfunded_design')
        self.assertFalse(r['native_object_created'])
        self.assertTrue(self.s.audit()['book_balanced'])
    def test_funded_creation_and_new_virtual_tree(self):
        self.periods(20)
        harvested=[]
        for f in self.s.db.execute("SELECT fruit_id FROM fruits WHERE status='on_tree' LIMIT 4").fetchall():
            harvested.append(self.s.harvest(f[0],'Solace','h-'+f[0]))
        self.assertGreaterEqual(sum(x['ce'] for x in harvested),45)
        r=self.s.create('new-world','Solace','world_seed')
        self.assertEqual(r['state'],'funded_seed_awaiting_native_execution')
        r=self.s.establish_tree('TREE-B','new-world',copy.deepcopy(TREE))
        self.assertEqual(r['native_status'],'virtual_pending')
        self.assertEqual(len(self.s.status()['trees']),2)
        with self.assertRaises(IntegrationError):self.s.establish_tree('TREE-C','new-world',copy.deepcopy(TREE))
        self.assertTrue(self.s.audit()['book_balanced'])
    def test_river_competition_conserves_supply(self):
        self.s.add_tree('TREE-B',copy.deepcopy(TREE))
        self.s.add_tree('TREE-C',copy.deepcopy(TREE))
        for p in range(1,13):
            r=self.s.cycle(p,11)
            self.assertEqual(sum(x['river_allocated'] for x in r['trees'].values()),11)
        self.assertTrue(self.s.audit()['book_balanced'])
    def test_zero_fuel_no_action_gate_and_rest(self):
        result=self.s.body_cycle('Solace','rest-1',1,0)
        self.assertTrue(not result['action_selection_gated'])
        self.assertEqual(result['fuel'],0)
        self.assertEqual(result['burned'],0)
        self.assertLess(result['integrity'],1)
    def test_feed_from_virtual_tree_foodweb(self):
        self.periods(1)
        before=self.s.balance(BIO,'tree:TREE-A:foodweb')
        self.assertGreater(before,0)
        self.s.feed_virtual('Solace','TREE-A',1,'food1')
        b=self.s.body_cycle('Solace','body1',1,0)
        self.assertEqual(b['gut'],0)
        self.assertTrue(self.s.audit()['book_balanced'])
    def test_feed_replay_conflict(self):
        self.periods(1)
        self.s.feed_virtual('Solace','TREE-A',1,'f1')
        self.assertEqual(self.s.feed_virtual('Solace','TREE-A',1,'f1')['virtual_ingestion'],1)
        with self.assertRaises(IntegrationError):self.s.feed_virtual('Solace','TREE-A',2,'f1')
    def test_body_cycle_replay_conflict(self):
        first=self.s.body_cycle('Solace','c1',1,0)
        self.assertEqual(self.s.body_cycle('Solace','c1',1,0),first)
        with self.assertRaises(IntegrationError):self.s.body_cycle('Solace','c1',0,1)
    def test_transaction_rollback(self):
        pre=self.s.audit()['transfer_count']
        with self.assertRaises(IntegrationError):self.s.feed_virtual('Solace','TREE-A',900,'nofood')
        self.assertEqual(self.s.audit()['transfer_count'],pre)
    def test_two_asset_conflict(self):
        with self.s.atomic():self.s.transfer('t1',CE,'external:source','world:river',1)
        with self.s.atomic():self.assertFalse(self.s.transfer('t1',CE,'external:source','world:river',1))
        with self.assertRaises(IntegrationError):
            with self.s.atomic():self.s.transfer('t1',BIO,'external:source','world:river',1)
    def test_360_cycle_stress_audit(self):
        self.s.add_tree('TREE-B',copy.deepcopy(TREE))
        self.periods(360,supply=50)
        self.assertTrue(self.s.audit()['book_balanced'])
        self.assertEqual(self.s.status()['period'],360)
    def test_corrupt_account_detected(self):
        self.periods(1)
        self.s.db.execute("UPDATE balances SET amount=amount+3 WHERE account='world:river'")
        self.assertFalse(self.s.audit()['book_balanced'])

class NativeObservationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=str(Path(self.temp.name)/'state.sqlite')
        self.s=Store(self.path);self.s.initialize('test-save-001')
    def tearDown(self):self.s.close();self.temp.cleanup()
    def write(self,events,name='events.jsonl'):
        path=Path(self.temp.name)/name
        path.write_text(''.join(json.dumps(e)+'\n' for e in events),encoding='utf-8')
        return str(path)
    def events(self,count=1,world='test-save-001',session='s1'):
        events=[{'schema':1,'session_id':session,'world_key':world,'seq':1,'kind':'session_open',
                 'assembly_sha256':EXPECTED_ASSEMBLY_SHA,'active_hooks':sorted(EXPECTED_HOOKS)}]
        for i in range(count):
            events.append({'schema':1,'session_id':session,'world_key':world,'seq':i+2,
                           'kind':'nutrition_call','actor_id':i+1,'native_delta':999})
        events.append({'schema':1,'session_id':session,'world_key':world,'seq':count+2,'kind':'session_close'})
        return events
    def test_native_observations_never_feed_book(self):
        events=self.events(5)
        r=self.s.ingest_events(self.write(events))
        self.assertEqual(r['native_book_writes'],0)
        self.assertEqual(self.s.audit()['transfer_count'],0)
        self.assertTrue(self.s.native_audit()['native_capture_integrity_ok'])
    def test_event_reimport_deduplicated(self):
        path=self.write(self.events(10))
        self.s.ingest_events(path)
        self.assertEqual(self.s.ingest_events(path)['duplicates'],12)
        self.assertEqual(self.s.native_audit()['observed_unique_actor_ids'],10)
    def test_actor_count_above_5000(self):
        r=self.s.ingest_events(self.write(self.events(6001)))
        self.assertEqual(r['imported'],6003)
        self.assertEqual(self.s.native_audit()['observed_unique_actor_ids'],6001)
        self.assertTrue(self.s.native_audit()['native_capture_integrity_ok'])
    def test_wrong_world_is_quarantined(self):
        r=self.s.ingest_events(self.write(self.events(1,world='other-save')))
        self.assertEqual(r['imported'],0)
        self.assertEqual(r['rejected'],3)
        self.assertFalse(self.s.native_audit()['native_capture_integrity_ok'])
    def test_gap_and_missing_hook_fail_audit(self):
        data=self.events(2)
        data.pop(1);data[0]['active_hooks']=['Actor.die']
        self.s.ingest_events(self.write(data))
        self.assertFalse(self.s.native_audit()['native_capture_integrity_ok'])
    def test_assembly_wrong_fails_audit(self):
        data=self.events(1);data[0]['assembly_sha256']='bad'
        self.s.ingest_events(self.write(data))
        self.assertFalse(self.s.native_audit()['native_capture_integrity_ok'])
    def test_conflicting_same_sequence_blocked(self):
        self.s.ingest_events(self.write(self.events(2)))
        events=self.events(2);events[1]['native_delta']=1000
        self.assertEqual(self.s.ingest_events(self.write(events,'rewrite.jsonl'))['conflicts'],1)
        self.assertFalse(self.s.native_audit()['native_capture_integrity_ok'])
    def test_live_incomplete_tail_not_applied(self):
        f=Path(self.temp.name)/'partial.jsonl'
        f.write_bytes((json.dumps(self.events(1)[0])+'\n'+json.dumps(self.events(1)[1])).encode())
        result=self.s.ingest_events(str(f))
        self.assertEqual(result['imported'],1)
        self.assertEqual(result['incomplete_tail'],1)
        self.assertEqual(result['rejected'],0)
        self.assertEqual(self.s.audit()['transfer_count'],0)
        f.write_text(''.join(json.dumps(e)+'\n' for e in self.events(1)),encoding='utf-8')
        self.s.ingest_events(str(f))
        self.assertTrue(self.s.native_audit()['native_capture_integrity_ok'])
    def snapshot(self,capture,ids,world='test-save-001',tick=1):
        data={'schema':'founders-native-snapshot-1','world_key':world,
              'capture_id':capture,'session_id':capture,'native_tick':tick,
              'actors':[{'id':i,'species':'wolf','generation':3,
                        'creation_marker':'native','parent_1':1,'parent_2':2} for i in ids]}
        target=Path(self.temp.name)/(capture+'.json');target.write_text(json.dumps(data))
        return str(target)
    def test_snapshot_replay_and_world_isolation(self):
        file=self.snapshot('c1',range(100))
        self.assertEqual(self.s.import_snapshot(file)['actors'],100)
        self.assertTrue(self.s.import_snapshot(file)['replay'])
        with self.assertRaises(IntegrationError):self.s.import_snapshot(self.snapshot('c2',[1],world='wrong'))
        self.assertEqual(self.s.audit()['transfer_count'],0)
    def test_2293_4900_continuity_not_births_deaths(self):
        first=range(1,2294)
        later=list(range(1,560))+list(range(6000,10341))
        self.s.import_snapshot(self.snapshot('earlier',first,tick=800))
        self.s.import_snapshot(self.snapshot('later',later,tick=10))
        r=self.s.compare_snapshots('earlier','later')
        self.assertEqual([r['earlier_count'],r['later_count'],r['shared_ids']], [2293,4900,559])
        self.assertEqual(r['identity_conflicts'],0)
        self.assertEqual(r['earlier_only'],1734)
        self.assertEqual(r['later_only'],4341)
        self.assertIsNone(r['confirmed_births'])
        self.assertIsNone(r['confirmed_deaths'])
    def test_snapshot_over_5000(self):
        self.assertEqual(self.s.import_snapshot(self.snapshot('big',range(6500)))['actors'],6500)
    def test_native_birth_not_authoritative(self):
        data=self.events(1);data[1]['kind']='baby_factory_call'
        self.s.ingest_events(self.write(data))
        self.assertTrue(self.s.native_audit()['native_capture_integrity_ok'])
        self.assertEqual(self.s.audit()['transfer_count'],0)

if __name__=='__main__':unittest.main()
