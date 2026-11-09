from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from backend import storage
p=ROOT/'frontend';s=(p/'index.html').read_text();s=s[:s.index('<script>fetch(')];s=s.replace('<link rel="stylesheet" href="/style.css">','<style>'+(p/'style.css').read_text()+'</style>');js=(p/'app.js').read_text().replace('async function ask(i){askLocal(i);try{',"async function ask(i){askLocal(i);if(location.protocol==='file:')return;try{");s+='<script>window.__CAIHUA_DATA__='+json.dumps(storage.graph(),ensure_ascii=False).replace('</','<\\/')+';</script><script>'+js+'</script></html>';out=ROOT/'data/reports/知识图谱_离线修订版.html';out.write_text(s);print(out)
