from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlsplit,parse_qs
import json,os,argparse,traceback
from . import storage
from .query import run,search,QUESTIONS
ROOT=Path(__file__).resolve().parents[1]
class App(BaseHTTPRequestHandler):
 def send(self,body,status=200,ctype='application/json'):
  if not isinstance(body,bytes):body=json.dumps(body,ensure_ascii=False).encode()
  self.send_response(status);self.send_header('Content-Type',ctype+'; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.send_header('Cache-Control','no-store');self.send_header('X-Content-Type-Options','nosniff');self.end_headers();self.wfile.write(body)
 def do_GET(self):
  u=urlsplit(self.path);p=u.path;q=parse_qs(u.query)
  try:
   if p=='/api/status':return self.send({'connected':True,'storage':('Neo4j' if os.environ.get('CAIHUA_KNOWLEDGE_STORE')=='neo4j' else 'SQLite'),'database':os.environ.get('NEO4J_DATABASE','本机可迁移数据'),'version':'2.0','persistent':True})
   if p=='/api/graph':return self.send(storage.graph())
   if p=='/api/search':return self.send({'nodes':search(storage.graph(),q.get('q',[''])[0])})
   if p=='/api/questions':return self.send([{'id':i,'question':x[0],'kind':x[1]} for i,x in enumerate(QUESTIONS)])
   if p=='/api/history':return self.send(storage.history())
   if p=='/api/reviews':return self.send(json.loads((ROOT/'data/reports/teacher_review.json').read_text()))
   if p=='/api/export':return self.send(storage.graph(include_inactive=True))
   files={'/':'index.html','/index.html':'index.html','/style.css':'style.css','/app.js':'app.js','/review':'review.html'}
   if p in files:
    f=ROOT/'frontend'/files[p];typ='text/css' if f.suffix=='.css' else 'text/javascript' if f.suffix=='.js' else 'text/html';return self.send(f.read_bytes(),ctype=typ)
   return self.send({'error':'接口或文件不存在'},404)
  except Exception:traceback.print_exc();return self.send({'error':'读取失败，请检查服务日志和数据文件。'},500)
 def body(self):
  origin=self.headers.get('Origin')
  # Local deployment: browser writes only from the same origin. No wildcard CORS.
  if origin and urlsplit(origin).netloc!=self.headers.get('Host'):raise PermissionError('拒绝跨站写入')
  if 'application/json' not in self.headers.get('Content-Type',''):raise ValueError('请使用 application/json')
  size=int(self.headers.get('Content-Length','0'))
  if size>1024*1024:raise ValueError('请求过大')
  return json.loads(self.rfile.read(size))
 def do_POST(self):
  try:
   if self.path!='/api/query':return self.send({'error':'接口不存在'},404)
   return self.send(run(storage.graph(),self.body()))
  except PermissionError as e:return self.send({'error':str(e)},403)
  except (ValueError,TypeError,KeyError) as e:return self.send({'error':str(e)},400)
 def do_PATCH(self):
  try:
   parts=self.path.split('/')
   if len(parts)!=5 or parts[1:3]!=['api','records']:return self.send({'error':'接口不存在'},404)
   b=self.body();return self.send(storage.update(parts[3],parts[4],b.get('changes',{}),b.get('reason','')))
  except PermissionError as e:return self.send({'error':str(e)},403)
  except KeyError as e:return self.send({'error':str(e)},404)
  except (ValueError,TypeError) as e:return self.send({'error':str(e)},400)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--port',type=int,default=int(os.environ.get('PORT','18765')));parser.add_argument('--host',default=os.environ.get('HOST','127.0.0.1'));a=parser.parse_args();storage.initialize()
 if os.environ.get('CAIHUA_KNOWLEDGE_STORE')=='neo4j':storage.graph()
 server=ThreadingHTTPServer((a.host,a.port),App);print(f'彩画作平台 http://{a.host}:{a.port} / 数据: {storage.DB}',flush=True)
 try:server.serve_forever()
 except KeyboardInterrupt:server.server_close()
if __name__=='__main__':main()
