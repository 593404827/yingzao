"""Boot a fresh copy from a different Unicode/space path without the existing DB."""
from pathlib import Path
import tempfile,shutil,subprocess,sys,socket,time,urllib.request,json,os
ROOT=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='caihua-') as tmp:
 target=Path(tmp)/'另一台电脑 portable project';target.mkdir()
 for name in ['backend','frontend','scripts']:shutil.copytree(ROOT/name,target/name,ignore=shutil.ignore_patterns('__pycache__'))
 (target/'data').mkdir();shutil.copytree(ROOT/'data/raw',target/'data/raw');shutil.copytree(ROOT/'data/reports',target/'data/reports',ignore=shutil.ignore_patterns('*.html','neo4j_projection.json'));shutil.copy(ROOT/'run.py',target/'run.py')
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 env=os.environ.copy();env.pop('CAIHUA_DB',None);proc=subprocess.Popen([sys.executable,str(target/'run.py'),'--port',str(port)],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
  url=f'http://127.0.0.1:{port}'
  for _ in range(50):
   try:
    with urllib.request.urlopen(url+'/api/graph',timeout=1) as f:g=json.load(f)
    break
   except OSError:time.sleep(.1)
  else:raise RuntimeError('Fresh project failed to boot')
  assert (target/'data/platform.sqlite3').exists();assert not any(n['name']=='赭笔' for n in g['nodes']);assert len(g['nodes'])==967
  req=urllib.request.Request(url+'/api/query',data=b'{"preset":0,"level":"verified"}',headers={'Content-Type':'application/json'})
  with urllib.request.urlopen(req) as f:r=json.load(f)
  assert len(r['paths'])==6
  result={'fresh_path_boot':True,'unicode_space_path':True,'no_existing_db_required':True,'entities':len(g['nodes']),'color_paths':len(r['paths']),'runtime':sys.version.split()[0],'actual_os':sys.platform,'windows_linux_docker_not_executed':True};(ROOT/'data/reports/portability_smoke.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(result)
 finally:proc.terminate();proc.wait(timeout=8)
