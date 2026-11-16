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
        except error.HTTPError as e:
            # urllib raises on 4xx/5xx *before* we can inspect the bridge's
            # standard {ok:false,error:{code,message}} response envelope.
            # Keep the status and safe structured reason, not response bodies,
            # request headers, authentication tokens or exception stack traces.
            try:
                reply=json.loads(e.read(16384).decode('utf-8'))
            except (ValueError,UnicodeDecodeError):
                reply=None
            detail=reply.get('error') if isinstance(reply,dict) else None
            if not isinstance(detail,dict):
                detail={}
            code=str(detail.get('code') or 'HTTP_ERROR')[:96]
            message=str(detail.get('message') or 'bridge returned no structured error')[:400]
            # No token or credentials should appear even if an unexpected
            # upstream error message includes the caller's credential.
            if self.token:
                code=code.replace(self.token,'[redacted]')
                message=message.replace(self.token,'[redacted]')
            raise RuntimeError(f'WorldBox read rejected: HTTP {e.code} {code}: {message}') from None
        except (error.URLError,TimeoutError) as e:
            raise ConnectionError(f'WorldBox bridge unavailable: {type(e).__name__}') from e
        if not isinstance(result,dict):
            raise RuntimeError('WorldBox read returned a non-object JSON response')
        # The pinned WorldBox MCP bridge intentionally returns a bare JSON
        # capabilities document, unlike /health and /cmd success envelopes.
        # Accept that exception only on /capabilities and never ignore an
        # explicit error response or a malformed capabilities document.
        if route=='/capabilities' and 'ok' not in result:
            if (isinstance(result.get('commands'),list)
                and isinstance(result.get('mod_version'),str)
                and isinstance(result.get('assembly_csharp_sha256'),str)):
                return result
            raise RuntimeError('WorldBox capabilities response missing required schema')
        if result.get('ok') is not True:
            error_data=result.get('error')
            if not isinstance(error_data,dict):error_data={}
            raise RuntimeError(f'WorldBox read rejected: {error_data.get("code","unknown")} {error_data.get("message","")}')
        payload=result.get('result')
        return payload if isinstance(payload,dict) else result
    def health(self):return self._call('/health')
    def capabilities(self):return self._call('/capabilities')
    def command(self,name,args=None):
        if name not in self.READ_COMMANDS:raise PermissionError('M01 is read-only: no mutating WorldBox commands')
        return self._call('/cmd',{'name':name,'args':args or {}})
