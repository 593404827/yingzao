@echo off
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  start "打开知识图谱" /b py -3 scripts\open_browser.py
  py -3 run.py
) else (
  start "打开知识图谱" /b python scripts\open_browser.py
  python run.py
)
pause
