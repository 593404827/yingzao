"""Neo4j knowledge store. Standard-library HTTP client; no SQLite fallback."""
import base64,json,os,urllib.request,uuid
from datetime import datetime,timezone

def settings():
 url=os.environ.get('NEO4J_HTTP','http://127.0.0.1:17474').rstrip('/')
 database=os.environ.get('NEO4J_DATABASE','caihuaplatform')
 if database not in ('caihuaplatform','caihuafull','neo4j'):raise ValueError('请使用彩画专用数据库 caihuaplatform 或 caihuafull')
 return url,database

def query(statements,database=None):
 url,db=settings();headers={'Content-Type':'application/json'}
 user=os.environ.get('NEO4J_USER','');password=os.environ.get('NEO4J_PASSWORD','')
 if user:headers['Authorization']='Basic '+base64.b64encode((user+':'+password).encode()).decode()
 payload={'statements':[{'statement':s,'parameters':p,'resultDataContents':['row']} for s,p in statements]}
 req=urllib.request.Request(url+'/db/'+(database or db)+'/tx/commit',data=json.dumps(payload,ensure_ascii=False).encode(),headers=headers)
 with urllib.request.urlopen(req,timeout=120) as r:result=json.load(r)
 if result.get('errors'):raise RuntimeError('; '.join(e['code']+': '+e['message'] for e in result['errors']))
 return [[r['row'] for r in item['data']] for item in result['results']]

def graph(include_inactive=False):
 result=query([('MATCH (m:CaihuaDataset {id:$id}) RETURN m.payload',{'id':'platform-v2'}),('MATCH(n:CaihuaEntity) RETURN n.payload',{}),('MATCH(e:CaihuaRelation) RETURN e.payload',{})])
 if not result[0]:raise RuntimeError('Neo4j尚未导入平台知识；请先执行 migrate_to_neo4j.py')
 g=json.loads(result[0][0][0]);nodes=[json.loads(x[0]) for x in result[1]];edges=[json.loads(x[0]) for x in result[2]]
 if not include_inactive:
  nodes=[n for n in nodes if n.get('active',True)];ids={n['id'] for n in nodes}
  edges=[e for e in edges if e.get('active',True) and e['source'] in ids and e['target'] in ids]
 g['nodes']=nodes;g['edges']=edges;g['meta'].update(node_count=len(nodes),relation_count=len(edges),attribute_count=sum(len(n.get('attributes',[])) for n in nodes),storage='Neo4j',database=settings()[1])
 return g

def apply_change(kind,record_id,changes,reason,event_id):
 label={'node':'CaihuaEntity','edge':'CaihuaRelation'}[kind]
 rows=query([('MATCH(n:'+label+' {id:$id}) RETURN n.payload, coalesce(n.revision,0)',{'id':record_id})])[0]
 if not rows:raise KeyError('记录不存在')
 raw,revision=rows[0];before=json.loads(raw);after={**before,**changes};encoded=json.dumps(after,ensure_ascii=False)
 at=datetime.now(timezone.utc).isoformat()
 event={'id':event_id,'at':at,'kind':kind,'record_id':record_id,'before':before,'after':after,'reason':reason}
 statements=[('MATCH(n:'+label+' {id:$id}) WHERE coalesce(n.revision,0)=$rev SET n.payload=$payload,n.revision=$rev+1,n.active=$active,n.name=$name,n.group=$group,n.subtype=$subtype,n.predicate=$predicate WITH n CREATE(c:CaihuaChange {id:$event,payload:$change}) MERGE(c)-[:CHANGED]->(n) RETURN n.id',{'id':record_id,'rev':revision,'payload':encoded,'active':after.get('active',True),'name':after.get('name',''),'group':after.get('group',''),'subtype':after.get('subtype',''),'predicate':after.get('predicate',''),'event':event_id,'change':json.dumps(event,ensure_ascii=False)})]
 if kind=='edge':
  # The relation record is authoritative. Existing visual edge is retained as history.
  typ=after['predicate'].replace('`','``')
  statements.append(('MATCH(c:CaihuaChange {id:$event}) OPTIONAL MATCH()-[r]->() WHERE r.id=$id SET r.active=false WITH DISTINCT c MATCH(s:CaihuaEntity {id:$src}),(t:CaihuaEntity {id:$dst}) CREATE(s)-[r:`'+typ+'`]->(t) SET r.id=$id,r.active=$active,r.payload=$payload RETURN r.id',{'event':event_id,'id':record_id,'src':after['source'],'dst':after['target'],'active':after.get('active',True),'payload':encoded}))
 result=query(statements)
 if not result[0]:raise ValueError('知识已被其他修改更新，请刷新后重新预览')
 return after,event

def change_events():
 return [json.loads(r[0]) for r in query([('MATCH(c:CaihuaChange) RETURN c.payload',{})])[0]]
