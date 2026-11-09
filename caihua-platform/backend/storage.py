import json,sqlite3,os,threading
from pathlib import Path
from datetime import datetime,timezone
from .corrections import corrected_graph
ROOT=Path(__file__).resolve().parents[1]
DB=Path(os.environ.get('CAIHUA_DB',str(ROOT/'data'/'platform.sqlite3')))
LOCK=threading.RLock()
def connect():
 DB.parent.mkdir(parents=True,exist_ok=True);c=sqlite3.connect(DB,timeout=30);c.execute('PRAGMA journal_mode=WAL');return c
def initialize():
 if os.environ.get("CAIHUA_KNOWLEDGE_STORE","sqlite")=="neo4j":
  with LOCK,connect() as c:
   c.executescript("CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT,kind TEXT,id TEXT,before TEXT,after TEXT,reason TEXT); CREATE TABLE IF NOT EXISTS knowledge_jobs(id TEXT PRIMARY KEY,status TEXT,payload TEXT,error TEXT);")
  return
 with LOCK,connect() as c:
  c.executescript('CREATE TABLE IF NOT EXISTS records(kind TEXT,id TEXT,payload TEXT,PRIMARY KEY(kind,id));CREATE TABLE IF NOT EXISTS meta(key TEXT PRIMARY KEY,value TEXT);CREATE TABLE IF NOT EXISTS history(seq INTEGER PRIMARY KEY AUTOINCREMENT,at TEXT,kind TEXT,id TEXT,before TEXT,after TEXT,reason TEXT);')
  if c.execute("SELECT 1 FROM meta WHERE key='initialized'").fetchone():return
  raw=json.loads((ROOT/'data/raw/graph.original.json').read_text());g=corrected_graph(raw)
  for kind,key in [('node','nodes'),('edge','edges')]:c.executemany('INSERT INTO records VALUES(?,?,?)',[(kind,x['id'],json.dumps(x,ensure_ascii=False)) for x in g[key]])
  for k,v in g.items():
   if k not in ['nodes','edges']:c.execute('INSERT INTO meta VALUES(?,?)',(k,json.dumps(v,ensure_ascii=False)))
  c.execute("INSERT INTO meta VALUES('initialized','true')")
  for x in g['corrections']:c.execute('INSERT INTO history(at,kind,id,before,after,reason) VALUES(?,?,?,?,?,?)',(datetime.now(timezone.utc).isoformat(),'initial-correction',x['subject'],json.dumps(x['before'],ensure_ascii=False),json.dumps(x['after'],ensure_ascii=False),x['reason']))
def graph(include_inactive=False):
 if os.environ.get("CAIHUA_KNOWLEDGE_STORE","sqlite")=="neo4j":
  from .neo4j_store import graph as read_graph
  return read_graph(include_inactive)
 initialize()
 with connect() as c:
  g={k:json.loads(v) for k,v in c.execute("SELECT key,value FROM meta WHERE key!='initialized'")};g['nodes']=[];g['edges']=[]
  for kind,payload in c.execute('SELECT kind,payload FROM records ORDER BY id'):
   x=json.loads(payload)
   if include_inactive or x.get('active',True):g['nodes' if kind=='node' else 'edges'].append(x)
 if not include_inactive:
  ids={n['id'] for n in g['nodes']};g['edges']=[e for e in g['edges'] if e['source'] in ids and e['target'] in ids]
 g['meta'].update({'node_count':len(g['nodes']),'relation_count':len(g['edges']),'attribute_count':sum(len(n['attributes']) for n in g['nodes']),'storage':'SQLite','database':'platform.sqlite3'})
 return g
def update(kind,id,changes,reason):
 if kind not in ['node','edge']:raise ValueError('只支持实体或关系修订')
 if not reason.strip():raise ValueError('请填写修订理由')
 fields={'node':{'name','group','subtype','active','review_note'},'edge':{'predicate','status','qualifiers','active','audit_note'}}[kind]
 if not changes or set(changes)-fields:raise ValueError('包含不支持的字段')
 if 'active' in changes and not isinstance(changes['active'],bool):raise ValueError('active 必须是布尔值')
 for k in ['name','group','subtype','predicate','status','review_note','audit_note']:
  if k in changes and (not isinstance(changes[k],str) or len(changes[k])>1000 or not changes[k].strip()):raise ValueError('名称或状态字段无效')
 if 'qualifiers' in changes and (not isinstance(changes['qualifiers'],dict) or any(not isinstance(v,str) for v in changes['qualifiers'].values())):raise ValueError('限定条件必须为文本对象')
 if os.environ.get("CAIHUA_KNOWLEDGE_STORE","sqlite")=="neo4j":
  from . import neo4j_store
  import uuid
  initialize();event_id=str(uuid.uuid4())
  job={"kind":kind,"record_id":id,"changes":changes,"reason":reason}
  with LOCK,connect() as c:c.execute('INSERT INTO knowledge_jobs VALUES(?,?,?,?)',(event_id,'pending',json.dumps(job,ensure_ascii=False),''))
  try:after,event=neo4j_store.apply_change(kind,id,changes,reason,event_id)
  except Exception as exc:
   with LOCK,connect() as c:c.execute('UPDATE knowledge_jobs SET status=?,error=? WHERE id=?',('needs_reconciliation',type(exc).__name__,event_id))
   raise
  with LOCK,connect() as c:
   c.execute('INSERT INTO history(at,kind,id,before,after,reason) VALUES(?,?,?,?,?,?)',(event['at'],kind,id,json.dumps(event['before'],ensure_ascii=False),json.dumps(after,ensure_ascii=False),reason))
   c.execute('UPDATE knowledge_jobs SET status=? WHERE id=?',('applied',event_id))
  return after
 with LOCK,connect() as c:
  row=c.execute('SELECT payload FROM records WHERE kind=? AND id=?',(kind,id)).fetchone()
  if not row:raise KeyError('记录不存在')
  before=json.loads(row[0]);after={**before,**changes};c.execute('UPDATE records SET payload=? WHERE kind=? AND id=?',(json.dumps(after,ensure_ascii=False),kind,id));c.execute('INSERT INTO history(at,kind,id,before,after,reason) VALUES(?,?,?,?,?,?)',(datetime.now(timezone.utc).isoformat(),kind,id,json.dumps(before,ensure_ascii=False),json.dumps(after,ensure_ascii=False),reason));return after
def history():
 initialize()
 with connect() as c:return [{'seq':a,'at':b,'kind':k,'id':i,'before':json.loads(old),'after':json.loads(new),'reason':r} for a,b,k,i,old,new,r in c.execute('SELECT seq,at,kind,id,before,after,reason FROM history ORDER BY seq DESC')]
def backup(dest):
 with LOCK,connect() as c:
  target=sqlite3.connect(dest);c.backup(target);target.close()
