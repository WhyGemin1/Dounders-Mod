import copy,json,os,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from founders_worldbox.registry import ActorRegistry,BridgeIntegrityError,normalize_snapshot
from founders_worldbox.client import BridgeClient
from founders_worldbox.core151_adapter import shadow_compare,core151_snapshot
SAMPLE=json.loads((Path(__file__).resolve().parents[1]/'fixtures/SYNTHETIC_paused_snapshot.json').read_text())
CORE_SOURCE=os.environ.get('FOUNDER_CIV_CORE151_SOURCE')
class SnapshotValidation(unittest.TestCase):
    def test_fixture(self):self.assertEqual(normalize_snapshot(copy.deepcopy(SAMPLE))[0]['count'],2)
    def test_old_query_rejected(self):
        s=copy.deepcopy(SAMPLE);s['items'][0].pop('native_actor_id')
        with self.assertRaises(BridgeIntegrityError):normalize_snapshot(s)
    def test_duplicate_rejected(self):
        s=copy.deepcopy(SAMPLE);s['items'][1]['native_actor_id']='11001'
        with self.assertRaises(BridgeIntegrityError):normalize_snapshot(s)
    def test_unpaused_rejected(self):
        s=copy.deepcopy(SAMPLE);s['paused']=False
        with self.assertRaises(BridgeIntegrityError):normalize_snapshot(s)
    def test_pagination_rejected(self):
        s=copy.deepcopy(SAMPLE);s['has_more']=True
        with self.assertRaises(BridgeIntegrityError):normalize_snapshot(s)
    def test_bad_matched_rejected(self):
        s=copy.deepcopy(SAMPLE);s['matched']=3
        with self.assertRaises(BridgeIntegrityError):normalize_snapshot(s)
    def test_missing_seed_rejected(self):
        s=copy.deepcopy(SAMPLE);s.pop('world_seed')
        with self.assertRaises(BridgeIntegrityError):normalize_snapshot(s)
    def test_bad_generation_rejected(self):
        s=copy.deepcopy(SAMPLE);s['items'][0]['generation']=-1
        with self.assertRaises(BridgeIntegrityError):normalize_snapshot(s)
    def test_wrong_id_type_rejected(self):
        s=copy.deepcopy(SAMPLE);s['items'][0]['native_actor_id']=True
        with self.assertRaises(BridgeIntegrityError):normalize_snapshot(s)
    def test_missing_bridge_id_indicator(self):
        s=copy.deepcopy(SAMPLE);s['missing_identity_count']=1
        with self.assertRaises(BridgeIntegrityError):normalize_snapshot(s)
class RegistryTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'registry.sqlite3';self.r=ActorRegistry(self.path);self.r.init_world('WORLD-001',9711)
    def tearDown(self):self.r.close();self.temp.cleanup()
    def bind(self):return self.r.enroll('WORLD-001','11001','WTBIO-0000041','rabbit','burrow_rabbit',0)
    def test_registry_initialization(self):self.assertEqual(self.r._world('WORLD-001')['world_seed'],9711)
    def test_seed_collision(self):
        with self.assertRaises(BridgeIntegrityError):self.r.init_world('WORLD-001',12)
    def test_enroll_idempotent(self):self.assertTrue(self.bind());self.assertFalse(self.bind())
    def test_enroll_collision_native(self):
        self.bind()
        with self.assertRaises(BridgeIntegrityError):self.r.enroll('WORLD-001','11001','WTBIO-999','rabbit','burrow_rabbit')
    def test_enroll_collision_core(self):
        self.bind()
        with self.assertRaises(BridgeIntegrityError):self.r.enroll('WORLD-001','11002','WTBIO-0000041','fox','red_fox')
    def test_no_auto_enrollment(self):self.assertEqual(self.r.observe('WORLD-001',SAMPLE)['mapped_count'],0)
    def test_paired_observation(self):
        self.bind();res=self.r.observe('WORLD-001',SAMPLE)
        self.assertEqual(res['mapped_count'],1);self.assertEqual(res['unmapped_count'],1)
        self.assertEqual(len(self.r.snapshots('WORLD-001')),1)
        self.assertEqual(json.loads(self.r.links('WORLD-001')[0]['last_native_json'])['generation'],0)
    def test_replay_idempotency(self):
        self.bind();self.r.observe('WORLD-001',SAMPLE)
        res=self.r.observe('WORLD-001',SAMPLE)
        self.assertTrue(res['replayed']);self.assertEqual(len(self.r.snapshots('WORLD-001')),1)
    def test_same_tick_conflict(self):
        self.bind();self.r.observe('WORLD-001',SAMPLE);s=copy.deepcopy(SAMPLE)
        s['items'][0]['x']=500
        with self.assertRaises(BridgeIntegrityError):self.r.observe('WORLD-001',s)
        self.assertEqual(len(self.r.snapshots('WORLD-001')),1)
    def test_tick_rollback_rejected(self):
        self.r.observe('WORLD-001',SAMPLE);s=copy.deepcopy(SAMPLE);s['tick']=299
        with self.assertRaises(BridgeIntegrityError):self.r.observe('WORLD-001',s)
    def test_epoch_explicit_allows_rewind(self):
        self.bind();self.r.observe('WORLD-001',SAMPLE)
        self.assertEqual(self.r.new_epoch('WORLD-001'),1)
        s=copy.deepcopy(SAMPLE);s['tick']=1;s['items'][0]['x']=200
        self.assertEqual(self.r.observe('WORLD-001',s)['epoch'],1)
        self.assertEqual(len(self.r.links('WORLD-001')),1)
    def test_world_mismatch(self):
        s=copy.deepcopy(SAMPLE);s['world_seed']=2
        with self.assertRaises(BridgeIntegrityError):self.r.observe('WORLD-001',s)
    def test_native_asset_changed_rejected(self):
        self.bind();s=copy.deepcopy(SAMPLE);s['items'][0]['asset_id']='wolf'
        with self.assertRaises(BridgeIntegrityError):self.r.observe('WORLD-001',s)
    def test_changed_name_position_identity_same(self):
        self.bind();self.r.observe('WORLD-001',SAMPLE)
        s=copy.deepcopy(SAMPLE);s['tick']=301;s['items'][0].update(name='Other',x=23,y=4)
        self.assertEqual(self.r.observe('WORLD-001',s)['mapped_count'],1)
        self.assertEqual(self.r.links('WORLD-001')[0]['core_actor_id'],'WTBIO-0000041')
    def test_reused_native_identity_marker_rejected(self):
        self.bind()
        s=copy.deepcopy(SAMPLE);s['items'][0]['native_created_time']='time-25'
        self.r.observe('WORLD-001',s)
        r=copy.deepcopy(s);r['tick']=301;r['items'][0]['native_created_time']='time-99'
        with self.assertRaises(BridgeIntegrityError):self.r.observe('WORLD-001',r)
    def test_changed_lineage_rejected(self):
        self.bind();s=copy.deepcopy(SAMPLE);s['items'][0]['parent_id_1']='123'
        self.r.observe('WORLD-001',s)
        r=copy.deepcopy(s);r['tick']=301;r['items'][0]['parent_id_1']='999'
        with self.assertRaises(BridgeIntegrityError):self.r.observe('WORLD-001',r)
    def test_mapping_survives_new_sqlite_connection(self):
        self.bind();self.r.close()
        with ActorRegistry(self.path) as reopened:self.assertEqual(len(reopened.links('WORLD-001')),1)
        self.r=ActorRegistry(self.path)
    def test_simulated_20_reload_epochs(self):
        self.bind();self.r.observe('WORLD-001',SAMPLE)
        for i in range(20):
            self.r.new_epoch('WORLD-001');s=copy.deepcopy(SAMPLE);s['tick']=1+i
            res=self.r.observe('WORLD-001',s)
            self.assertEqual(res['mapped_count'],1)
        self.assertEqual(len(self.r.snapshots('WORLD-001')),21)
        self.assertEqual(self.r.links('WORLD-001')[0]['core_actor_id'],'WTBIO-0000041')
    def test_core151_shadow_no_mutations(self):
        self.bind()
        core={'actors':[{'civ_actor_id':'WTBIO-0000041','species':'burrow_rabbit','generation':0,'parent_ids':[]}]}
        out=shadow_compare(self.r,'WORLD-001',core)
        self.assertEqual(out['issues'],[])
    def test_shadow_generation_mismatch(self):
        self.bind();self.r.observe('WORLD-001',SAMPLE)
        core={'actors':[{'civ_actor_id':'WTBIO-0000041','species':'burrow_rabbit','generation':1,'parent_ids':[]}]}
        self.assertIn('generation_mismatch',[x['issue'] for x in shadow_compare(self.r,'WORLD-001',core)['issues']])
class BridgeSafety(unittest.TestCase):
    def test_forbid_remote(self):
        with self.assertRaises(ValueError):BridgeClient(base_url='http://example.com:8723',token='demo')
    def test_forbid_mutation(self):
        with self.assertRaises(PermissionError):BridgeClient(token='demo').command('spawn')
    def test_allow_local(self):self.assertTrue(BridgeClient(token='demo').base.startswith('http://127.0.0.1'))
class RealCore151(unittest.TestCase):
    @unittest.skipUnless(CORE_SOURCE,'Specify FOUNDER_CIV_CORE151_SOURCE to test actual Core151')
    def test_actual_core151(self):
        a=core151_snapshot(CORE_SOURCE,100001)
        self.assertEqual(a['actor_count'],68);self.assertEqual(a['founder_count'],100)
        self.assertTrue(a['book_shared']);self.assertEqual(a['book_rejections'],0)
        self.assertEqual(len(a['actors'][0]['traits']),8)
if __name__=='__main__':unittest.main()
