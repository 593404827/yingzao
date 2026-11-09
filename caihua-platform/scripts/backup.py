from pathlib import Path
from datetime import datetime
import sys,json
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from backend.config import load
load()
from backend import storage
p=ROOT/'data/backups'/datetime.now().strftime('%Y%m%d-%H%M%S');p.mkdir(parents=True,exist_ok=True)
storage.backup(p/'platform.sqlite3')
# Export formal knowledge as well as the business database. Fail visibly if Neo4j is unavailable.
g=storage.graph(True)
(p/'knowledge.json').write_text(json.dumps(g,ensure_ascii=False),encoding='utf-8')
(p/'README.txt').write_text('包含业务数据库及知识逻辑快照；图片资源需另行复制resources/files。知识恢复需使用专门恢复程序，不覆盖现有非空知识库。',encoding='utf-8')
print(p)
