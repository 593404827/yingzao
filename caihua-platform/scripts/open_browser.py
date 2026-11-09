import os,time,urllib.request,webbrowser
url='http://127.0.0.1:'+os.environ.get('PORT','18765')
for _ in range(30):
 try:
  with urllib.request.urlopen(url+'/api/status',timeout=1) as r:
   if r.status==200:webbrowser.open(url);break
 except Exception:pass
 time.sleep(.5)
