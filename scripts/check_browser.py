"""Run browser workflows against an isolated disposable time ledger."""
import os,subprocess,tempfile,threading
from pathlib import Path
from werkzeug.serving import make_server
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from server import create_app
with tempfile.TemporaryDirectory(prefix='tempo-browser-') as d:
 app=create_app(d+'/tempo.sqlite3','tempo-browser-test-key-000000000000000')
 server=make_server('127.0.0.1',0,app);thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
 env={**os.environ,'TEMPO_URL':f'http://127.0.0.1:{server.server_port}'}
 try:
  for name in ['browser.cjs','locales.cjs']:subprocess.run(['node','scripts/'+name],env=env,check=True)
 finally:server.shutdown();thread.join();server.server_close()
