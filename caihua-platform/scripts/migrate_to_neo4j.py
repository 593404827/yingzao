"""One-time, empty-target migration. SQLite originals are retained, never deleted."""
import argparse,json,sqlite3,sys,os,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.config import load
load()
from backend import neo4j_store as neo

def main():
 p=argparse.ArgumentParser();p.add_argument('--source',default=str(ROOT/'data/platform.sqlite3'));p.add_argument('--create-database',action='store_true');a=p.parse_args()
 src=sqlite3.connect('file:'+str(Path(a.source).resolve())+'?mode=ro',uri=True)
 g={k:json.loads(v) for k,v in src.execute("SELECT key,value FROM meta WHERE key!='initialized'")};g['nodes']=[];g['edges']=[]
 for kind,payload in src.execute('SELECT kind,payload FROM records ORDER BY id'):g['nodes' if kind=='node' else 'edges'].append(json.loads(payload))
 src.close();db=neo.settings()[1]
 if a.create_database:neo.query([('CREATE DATABASE `'+db+'` IF NOT EXISTS WAIT 10 SECONDS',{})],database='system')
 count=neo.query([('MATCH(n) RETURN count(n)',{})])[0][0][0]
 if count:raise SystemExit('目标数据库非空，拒绝重复导入或覆盖。使用新的空数据库。')
 neo.query([('CREATE CONSTRAINT caihua_entity_id IF NOT EXISTS FOR(n:CaihuaEntity) REQUIRE n.id IS UNIQUE',{}),('CREATE CONSTRAINT caihua_relation_id IF NOT EXISTS FOR(n:CaihuaRelation) REQUIRE n.id IS UNIQUE',{}),('CREATE CONSTRAINT caihua_change_id IF NOT EXISTS FOR(n:CaihuaChange) REQUIRE n.id IS UNIQUE',{})])
 statements=[]
 for key,label in [('nodes','CaihuaEntity'),('edges','CaihuaRelation')]:
  rows=[{'id':v['id'],'payload':json.dumps(v,ensure_ascii=False),'active':v.get('active',True),'name':v.get('name',''),'group':v.get('group',''),'subtype':v.get('subtype',''),'predicate':v.get('predicate','')} for v in g[key]]
  statements.append(('UNWIND $rows AS row CREATE(n:'+label+') SET n=row,n.revision=0',{'rows':rows}))
 for typ in sorted({e['predicate'] for e in g['edges']}):
  rows=[{'id':e['id'],'source':e['source'],'target':e['target'],'active':e.get('active',True),'payload':json.dumps(e,ensure_ascii=False)} for e in g['edges'] if e['predicate']==typ]
  statements.append(('UNWIND $rows AS row MATCH(s:CaihuaEntity {id:row.source}),(t:CaihuaEntity {id:row.target}) CREATE(s)-[r:`'+typ.replace('`','``')+'`]->(t) SET r.id=row.id,r.active=row.active,r.payload=row.payload',{'rows':rows}))
 for entry in g.get('corpus',[]):
  if isinstance(entry,dict):statements.append(('CREATE(e:CaihuaSource {sid:$sid,payload:$payload})',{'sid':entry['sid'],'payload':json.dumps(entry,ensure_ascii=False)}))
 meta={k:v for k,v in g.items() if k not in ('nodes','edges')}
 statements.append(('CREATE(m:CaihuaDataset {id:$id,payload:$payload})',{'id':'platform-v2','payload':json.dumps(meta,ensure_ascii=False)}))
 # All data import statements share one transaction; failure cannot leave a partial dataset.
 neo.query(statements)
 actual=neo.graph(True)
 canonical=lambda rows:json.dumps(sorted(rows,key=lambda x:x['id']),ensure_ascii=False,sort_keys=True)
 for key in ('nodes','edges'):
  if canonical(g[key])!=canonical(actual[key]):raise RuntimeError('迁移逐字段核对失败：'+key)
 report={'database':db,'entities_including_history':len(g['nodes']),'relations_including_history':len(g['edges']),'active':neo.graph()['meta'],'nodes_and_edges_exactly_preserved':True,'source_sqlite_retained':True}
 f=ROOT/'data/reports/neo4j_migration.json';f.write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False))
if __name__=='__main__':main()
