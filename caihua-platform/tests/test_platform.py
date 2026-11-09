import unittest,tempfile,threading,urllib.request,urllib.error,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend import storage
from backend.query import run
from backend.server import App,ThreadingHTTPServer
class PlatformTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.tmp=tempfile.TemporaryDirectory();cls.old=storage.DB;storage.DB=Path(cls.tmp.name)/'fresh.sqlite3';storage.initialize();cls.server=ThreadingHTTPServer(('127.0.0.1',0),App);cls.url='http://127.0.0.1:'+str(cls.server.server_port);cls.thread=threading.Thread(target=cls.server.serve_forever,daemon=True);cls.thread.start()
 @classmethod
 def tearDownClass(cls):cls.server.shutdown();cls.server.server_close();storage.DB=cls.old;cls.tmp.cleanup()
 def request(self,path,body=None,method=None,origin=None):
  headers={'Content-Type':'application/json'}
  if origin:headers['Origin']=origin
  req=urllib.request.Request(self.url+path,data=json.dumps(body).encode() if body is not None else None,headers=headers,method=method)
  with urllib.request.urlopen(req) as r:return json.load(r)
 def test_01_graph_endpoints(self):
  g=self.request('/api/graph');ids={n['id'] for n in g['nodes']};self.assertTrue(all(e['source'] in ids and e['target'] in ids for e in g['edges']))
 def test_02_colors_are_contextual(self):
  r=self.request('/api/query',{'preset':0,'level':'verified'});nm={n['id']:n for n in r['nodes']};self.assertEqual({nm[p[-1]['target']]['name'] for p in r['paths']},{'青','绿','朱'});self.assertEqual(len(r['paths']),6);self.assertTrue(all(len({e['sid'] for e in p})==1 for p in r['paths']))
 def test_03_zhebi_withdrawn_not_deleted(self):
  g=storage.graph();self.assertFalse(any(n['name']=='赭笔' for n in g['nodes']));self.assertTrue(any(n['name']=='赭笔' and not n['active'] for n in storage.graph(True)['nodes']))
 def test_04_zhe_split_all_mentions(self):
  g=storage.graph();nm={n['id']:n for n in g['nodes']};es=[e for e in g['edges'] if e['predicate']=='使用色彩' and nm[e['target']]['name']=='赭'];self.assertEqual({e['sid'] for e in es},{'CH-009','CH-031','CH-045'})
 def test_05_relative_measurement_not_invented(self):
  n=next(n for n in storage.graph()['nodes'] if n['name']=='空缘宽度减外缘道三分之一规定');a={x['predicate']:x['value'] for x in n['attributes']};self.assertEqual(a['运算词'],'减');self.assertEqual(a['原文比例'],'三分之一');self.assertNotIn('最终比例',a)
 def test_06_questions_and_all_presets(self):
  self.assertEqual(len(self.request('/api/questions')),10)
  for i in range(10):self.assertIn('summary',self.request('/api/query',{'preset':i}))
 def test_07_persistent_edit_and_log(self):
  n=storage.graph()['nodes'][0];old=n['name'];self.request('/api/records/node/'+n['id'],{'changes':{'name':old+'测试'},'reason':'自动测试临时数据库'},'PATCH');self.assertEqual(next(x for x in storage.graph()['nodes'] if x['id']==n['id'])['name'],old+'测试');self.assertEqual(storage.history()[0]['before']['name'],old);storage.update('node',n['id'],{'name':old},'测试回退')
 def test_08_reason_required(self):
  with self.assertRaises(urllib.error.HTTPError) as cm:self.request('/api/records/node/'+storage.graph()['nodes'][0]['id'],{'changes':{'name':'bad'},'reason':''},'PATCH')
  self.assertEqual(cm.exception.code,400)
 def test_09_cross_origin_rejected(self):
  with self.assertRaises(urllib.error.HTTPError) as cm:self.request('/api/query',{'preset':0},origin='http://foreign.invalid')
  self.assertEqual(cm.exception.code,403)
 def test_10_traversal_rejected(self):
  with self.assertRaises(urllib.error.HTTPError) as cm:self.request('/../../data/raw/graph.original.json')
  self.assertEqual(cm.exception.code,404)
 def test_11_audit_index(self):self.assertEqual(len(self.request('/api/reviews')['historical_issues']),229)
 def test_12_absolute_measurement_scope(self):
  g=storage.graph();nm={n['id']:n for n in g['nodes']};n=next(n for n in g['nodes'] if n['name']=='梁栿缘道宽度二分规定');es=[e for e in g['edges'] if e['source']==n['id']];self.assertFalse(any(e['predicate']=='参照对象' for e in es));self.assertTrue(any(e['predicate']=='约束对象' and nm[e['target']]['name']=='外缘道' and '梁栿' in e['qualifiers']['scope'] for e in es))
 def test_13_role_mismatches_are_pending(self):
  g=storage.graph();nm={n['id']:n for n in g['nodes']};bad=[e for e in g['edges'] if e['predicate']=='采用设色方法' and nm[e['target']]['subtype']!='设色方法'];self.assertTrue(bad);self.assertTrue(all(e['status']=='待确认' for e in bad))
if __name__=='__main__':unittest.main()
