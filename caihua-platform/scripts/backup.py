from pathlib import Path
from datetime import datetime
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT));from backend import storage
p=ROOT/'data/backups';p.mkdir(exist_ok=True);f=p/(datetime.now().strftime('%Y%m%d-%H%M%S')+'.sqlite3');storage.backup(f);print(f)
