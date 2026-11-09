"""Optional one-way graph projection. SQLite is the editing source; no DELETE."""
import os,json,urllib.request,base64,sys,collections,argparse
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from backend import storage

def main():
 from backend.config import load
 load()
 if os.environ.get("CAIHUA_KNOWLEDGE_STORE")=="neo4j":raise SystemExit("现已使用Neo4j作为知识主库，无需再次执行旧投影同步。")
 p=argparse.ArgumentParser();p.add_argument('--apply',action='store_true');p.add_argument('--database',default='caihuafull');a=p.parse_args()
 url=os.environ.get('NEO4J_HTTP','http://127.0.0.1:17474').rstrip('/')+'/db/'+a.database+'/tx/commit'
 def query(q,params=None):
  headers={'Content-Type':'application/json'};user=os.environ.get('NEO4J_USER');password=os.environ.get('NEO4J_PASSWORD','')
  if user:headers['Authorization']='Basic '+base64.b64encode((user+':'+password).encode()).decode()
  body={'statements':[{'statement':q,'parameters':params or {},'resultDataContents':['row']}]}
  with urllib.request.urlopen(urllib.request.Request(url,data=json.dumps(body,ensure_ascii=False).encode(),headers=headers),timeout=120) as f:r=json.load(f)
  if r.get('errors'):raise RuntimeError(str(r['errors']))
  return r['results'][0]
 g=storage.graph();full=storage.graph(True);package={'database':a.database,'nodes':full['nodes'],'edges':full['edges'],'source':'SQLite editable source; inactive records retained','query_note':'Use WHERE coalesce(n.active,true) AND coalesce(r.active,true) for active graph.'}
 (ROOT/'data/reports/neo4j_projection.json').write_text(json.dumps(package,ensure_ascii=False))
 if not a.apply:print('已导出 data/reports/neo4j_projection.json。使用 --apply 才会写入 Neo4j。');return
 existing=query('MATCH(n:CaihuaEntity) RETURN count(n) AS count')['data'][0]['row'][0]
 if a.database not in ['caihuafull','caihuaplatform']:raise SystemExit('仅允许显式命名的彩画专用数据库，避免混入其他数据。')
 ids={n['id'] for n in full['nodes']};oldids={x['row'][0] for x in query('MATCH(n:CaihuaEntity) RETURN n.id')['data']}
 if oldids-ids:raise SystemExit('目标库包含不属于本项目的实体，已拒绝覆盖；请使用空的 caihuaplatform。')
 query('CREATE CONSTRAINT portable_id IF NOT EXISTS FOR(n:ExplorerNode) REQUIRE n.id IS UNIQUE')
 for i in range(0,len(full['nodes']),80):
  rows=[]
  for n in full['nodes'][i:i+80]:rows.append({'id':n['id'],'props':{'id':n['id'],'name':n['name'],'group':n['group'],'subtype':n['subtype'],'active':n.get('active',True),'sids':n['sids'],'payload':json.dumps(n,ensure_ascii=False),'dataset':'full-review-v1'}})
  query('UNWIND $rows AS row MERGE(n:ExplorerNode {id:row.id}) SET n:CaihuaEntity SET n += row.props',{'rows':rows})
 all_assertions=full['edges']+[a for n in full['nodes'] for a in n['attributes']]
 for i in range(0,len(all_assertions),80):
  rows=[]
  for v in all_assertions[i:i+80]:rows.append({'id':v['id'],'source':v['source'],'props':{'id':v['id'],'kind':v['kind'],'sid':v['sid'],'predicate':v['predicate'],'value':v.get('value',''),'status':v['status'],'active':v.get('active',True),'payload':json.dumps(v,ensure_ascii=False)}})
  query('UNWIND $rows AS row MERGE(a:ExplorerNode {id:row.id}) SET a:CaihuaAssertion SET a += row.props WITH a,row MATCH(n:CaihuaEntity {id:row.source}) MERGE(n)-[:HAS_ASSERTION]->(a)',{'rows':rows})
 # Existing edge versions remain archived, including former endpoints changed by review.
 query('MATCH(:CaihuaEntity)-[r]->(:CaihuaEntity) SET r.active=false')
 groups=collections.defaultdict(list)
 for e in g['edges']:groups[e['predicate']].append({'id':e['id'],'source':e['source'],'target':e['target'],'props':{'id':e['id'],'sid':e['sid'],'active':True,'status':e['status'],'payload':json.dumps(e,ensure_ascii=False)}})
 for typ,arr in groups.items():
  for i in range(0,len(arr),100):query('UNWIND $rows AS row MATCH(s:CaihuaEntity {id:row.source}),(t:CaihuaEntity {id:row.target}) MERGE(s)-[r:`'+typ.replace('`','``')+'` {id:row.id}]->(t) SET r += row.props',{'rows':arr[i:i+100]})
 result=query('MATCH(n:CaihuaEntity) WHERE n.active=true RETURN count(n) AS count')['data'][0]['row'][0];assert result==len(g['nodes']);print(json.dumps({'active_entities':result,'database':a.database,'raw_records_preserved':True},ensure_ascii=False))
if __name__=='__main__':main()
