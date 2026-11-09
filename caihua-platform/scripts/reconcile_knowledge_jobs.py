"""Recover audit status after a Neo4j commit / SQLite logging interruption."""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.config import load
load()
from backend import storage,neo4j_store
storage.initialize()
events={e['id']:e for e in neo4j_store.change_events()}
recovered=0
with storage.LOCK,storage.connect() as c:
 for job_id,status in c.execute("SELECT id,status FROM knowledge_jobs WHERE status!='applied'").fetchall():
  if job_id not in events:continue
  e=events[job_id]
  c.execute('INSERT INTO history(at,kind,id,before,after,reason) VALUES(?,?,?,?,?,?)',(e['at'],e['kind'],e['record_id'],json.dumps(e['before'],ensure_ascii=False),json.dumps(e['after'],ensure_ascii=False),e['reason']))
  c.execute("UPDATE knowledge_jobs SET status='applied',error='' WHERE id=?",(job_id,));recovered+=1
print(json.dumps({'recovered':recovered},ensure_ascii=False))
