"""Local-only standard-library dashboard server, no network dependencies."""
from __future__ import annotations
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import json, threading, uuid, traceback, mimetypes, argparse, webbrowser
from urllib.parse import urlparse, parse_qs
from .runner import run, write_package
from .canon import SYSTEMS

ROOT=Path(__file__).resolve().parent.parent
WEB=ROOT/'web'
DATA=ROOT/'results'
JOBS={};JOBS_LOCK=threading.Lock()

def response(handler,status,payload):
    b=json.dumps(payload,ensure_ascii=False).encode('utf-8')
    handler.send_response(status)
    handler.send_header('Content-Type','application/json; charset=utf-8')
    handler.send_header('Cache-Control','no-store')
    handler.send_header('Content-Length',str(len(b)))
    handler.end_headers();handler.wfile.write(b)

class Handler(BaseHTTPRequestHandler):
    def log_message(self,fmt,*args):pass
    def do_GET(self):
        p=urlparse(self.path);path=p.path
        if path=='/api/catalog':return response(self,200,{'systems':SYSTEMS})
        if path=='/api/sample':
            f=WEB/'sample_run.json'
            return self.file(f)
        if path=='/api/status':
            job=parse_qs(p.query).get('id',[''])[0]
            with JOBS_LOCK: value=JOBS.get(job)
            if value is None:return response(self,404,{'error':'unknown job'})
            return response(self,200,value)
        if path.startswith('/api/result/'):
            job=path.rsplit('/',1)[-1]
            with JOBS_LOCK: value=JOBS.get(job)
            if value is None or value.get('state')!='complete':return response(self,404,{'error':'not ready'})
            return self.file(DATA/job/'simulation.json')
        if path in ('/','/index.html'):return self.file(WEB/'index.html')
        if path in ('/styles.css','/app.js'):return self.file(WEB/path.lstrip('/'))
        return response(self,404,{'error':'unknown route'})
    def file(self,p):
        if not p.is_file():return response(self,404,{'error':'file missing'})
        ct=mimetypes.guess_type(p.name)[0] or 'application/octet-stream'
        if p.suffix=='.js':ct='application/javascript'
        b=p.read_bytes();self.send_response(200)
        self.send_header('Content-Type',ct+'; charset=utf-8')
        self.send_header('Content-Length',str(len(b)))
        self.send_header('Cache-Control','no-cache')
        self.end_headers();self.wfile.write(b)
    def do_POST(self):
        if self.path!='/api/run':return response(self,404,{'error':'unknown route'})
        try:
            size=int(self.headers.get('Content-Length','0'))
            if size>5000:raise ValueError('request too large')
            payload=json.loads(self.rfile.read(size) or '{}')
            days=int(payload.get('days',30));seed=int(payload.get('seed',42));arm=str(payload.get('arm','1111'))
            if days not in range(1,181):raise ValueError('interactive days must be 1..180; CLI allows up to 720')
            if len(arm)!=4 or any(c not in '01' for c in arm):raise ValueError('arm must be four 0/1 digits')
            if abs(seed)>100000000:raise ValueError('seed out of range')
        except Exception as e:return response(self,400,{'error':str(e)})
        job=uuid.uuid4().hex[:12]
        with JOBS_LOCK:JOBS[job]=dict(state='queued',day=0,total=days)
        def execute():
            def update(day,total):
                with JOBS_LOCK:JOBS[job]=dict(state='running',day=day,total=total)
            try:
                update(0,days)
                data=run(seed,days,arm,progress=update)
                write_package(data,DATA/job)
                with JOBS_LOCK:JOBS[job]=dict(state='complete',day=days,total=days,summary=data['results'])
            except Exception as e:
                with JOBS_LOCK:JOBS[job]=dict(state='failed',day=0,total=days,error=str(e))
                traceback.print_exc()
        threading.Thread(target=execute,daemon=True).start()
        return response(self,202,{'job_id':job})

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--port',type=int,default=8765)
    ap.add_argument('--browser',action='store_true',help='Open dashboard once local server is ready')
    args=ap.parse_args()
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Founders-CIV Observatory: http://127.0.0.1:{args.port}',flush=True)
    print('Open this address in your browser. Press Ctrl+C here to stop.')
    if args.browser:webbrowser.open(f'http://127.0.0.1:{args.port}')
    try:server.serve_forever()
    except KeyboardInterrupt:pass
    finally:server.server_close()
if __name__=='__main__':main()
