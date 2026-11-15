"""Small authenticated read-only WorldBoxBridge client. Never sends mutating commands."""
from __future__ import annotations
import json, os
from urllib import request, error, parse

class BridgeClient:
    READ_COMMANDS=frozenset({'query_actor_identities','get_world_state','get_ui_state'})
    def __init__(self,base_url='http://127.0.0.1:8723',token=None,timeout=12):
        url=parse.urlsplit(base_url)
        if url.scheme!='http' or url.hostname not in ('127.0.0.1','localhost','::1') or url.path not in ('','/') or url.username or url.password:
            raise ValueError('WorldBox M01 connects to HTTP loopback only')
        self.base=base_url.rstrip('/')
        self.token=token or os.environ.get('WORLDBOX_MCP_TOKEN')
        if not self.token:raise ValueError('Set WORLDBOX_MCP_TOKEN environment variable; never paste token into a report')
        self.timeout=timeout
    def _call(self,route,body=None):
        url=self.base+route
        data=None if body is None else json.dumps(body).encode('utf-8')
        req=request.Request(url,data=data,headers={'Authorization':f'Bearer {self.token}',
                  'Content-Type':'application/json'},method='POST' if data else 'GET')
        try:
            with request.urlopen(req,timeout=self.timeout) as r:
                result=json.loads(r.read())
        except (error.URLError,TimeoutError) as e:
            raise ConnectionError(f'WorldBox bridge unavailable or rejected the request: {type(e).__name__}') from e
        if result.get('ok') is not True:
            error_data=result.get('error',{})
            raise RuntimeError(f'WorldBox read rejected: {error_data.get("code","unknown")} {error_data.get("message","")}')
        return result.get('result') if isinstance(result.get('result'),dict) else result
    def health(self):return self._call('/health')
    def capabilities(self):return self._call('/capabilities')
    def command(self,name,args=None):
        if name not in self.READ_COMMANDS:raise PermissionError('M01 is read-only: no mutating WorldBox commands')
        return self._call('/cmd',{'name':name,'args':args or {}})
