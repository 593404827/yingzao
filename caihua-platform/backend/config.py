from pathlib import Path
import os
def load():
 p=Path(__file__).resolve().parents[1]/'.env'
 if p.exists():
  for line in p.read_text().splitlines():
   line=line.strip()
   if not line or line.startswith('#') or '=' not in line:continue
   k,v=line.split('=',1);os.environ.setdefault(k.strip(),v.strip())
