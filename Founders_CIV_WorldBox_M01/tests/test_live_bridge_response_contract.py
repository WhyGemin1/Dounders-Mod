"""Offline contract tests for the pinned WorldBox MCP HTTP response formats.

The /capabilities route returns bare JSON; /health and /cmd use an
{ok,result,tick} envelope. These fixtures are not live WorldBox tests.
"""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from founders_worldbox.client import BridgeClient


class HttpReply:
    def __init__(self,payload):
        self.payload=json.dumps(payload).encode("utf8")
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self):return self.payload


class BridgeResponseTests(unittest.TestCase):
    def setUp(self):
        self.client=BridgeClient(token="test-only-fake-token")

    def receive(self,method,payload):
        seen=[]
        def transport(req,timeout):
            seen.append(req)
            return HttpReply(payload)
        with patch('founders_worldbox.client.request.urlopen',side_effect=transport):
            value=getattr(self.client,method)()
        return value,seen[0]

    def test_health_success_envelope(self):
        data,request=self.receive('health',{'ok':True,'result':{'healthy':True},'tick':8})
        self.assertEqual(data,{'healthy':True})
        self.assertEqual(request.full_url,'http://127.0.0.1:8723/health')
        self.assertEqual(request.get_header('Authorization'),'Bearer test-only-fake-token')

    def test_capabilities_is_valid_bare_json(self):
        document={'mod_version':'0.8','worldbox_version':'0.51.2',
                  'assembly_csharp_sha256':'signed-fingerprint',
                  'commands':[{'name':'query_actor_identities','category':'read'}]}
        data,request=self.receive('capabilities',document)
        self.assertEqual(data,document)
        self.assertEqual(request.full_url,'http://127.0.0.1:8723/capabilities')

    def test_capabilities_explicit_error_never_accepted(self):
        with self.assertRaisesRegex(RuntimeError,'UNAUTHORIZED'):
            self.receive('capabilities',{'ok':False,'error':{
                'code':'UNAUTHORIZED','message':'not authenticated'}})

    def test_capabilities_missing_schema_fails_closed(self):
        for document in ({}, {'commands':[]},
                         {'commands':[], 'mod_version':'0.8'},
                         {'commands':'bad', 'mod_version':'0.8',
                          'assembly_csharp_sha256':'hash'}):
            with self.subTest(document=document),self.assertRaisesRegex(RuntimeError,'capabilities response missing required schema'):
                self.receive('capabilities',document)

    def test_health_bare_document_still_rejected(self):
        with self.assertRaisesRegex(RuntimeError,'read rejected: unknown'):
            self.receive('health',{'healthy':True})

    def test_non_object_json_fails_closed(self):
        with self.assertRaisesRegex(RuntimeError,'non-object'):
            self.receive('capabilities',['query_actor_identities'])

    def test_read_only_command_rejects_mutation(self):
        with self.assertRaisesRegex(PermissionError,'read-only'):
            self.client.command('spawn_unit')

    def test_command_uses_envelope(self):
        seen=[]
        def transport(req,timeout):
            seen.append(req)
            return HttpReply({'ok':True,'result':{'items':[],'paused':True},'tick':19})
        with patch('founders_worldbox.client.request.urlopen',side_effect=transport):
            data=self.client.command('query_actor_identities')
        self.assertTrue(data['paused'])
        self.assertEqual(json.loads(seen[0].data)['name'],'query_actor_identities')
        self.assertEqual(seen[0].get_method(),'POST')

if __name__=='__main__':
    unittest.main()
