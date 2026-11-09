"""Run with any Python 3.10+ on Windows/macOS/Linux. No absolute machine paths."""
from pathlib import Path
import os,sys
if sys.version_info<(3,10):raise SystemExit('请安装 Python 3.10 或更高版本。')
os.chdir(Path(__file__).resolve().parent)
from backend.config import load
load()
from backend.server import main
main()
