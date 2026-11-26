"""Exercise only unique disposable Docker containers/volumes; never user data."""
import http.client,json,os,secrets,subprocess,tempfile,time,urllib.request,urllib.error
from pathlib import Path
from backup import backup
IMAGE=os.environ.get('TEMPO_TEST_IMAGE','tempo-field:acceptance')
tag='tempo-check-'+secrets.token_hex(6);volumes=[tag+'-source',tag+'-restore'];names=[tag+'-a',tag+'-b'];key=secrets.token_urlsafe(40)
def docker(*args):return subprocess.check_output(['docker',*args],text=True).strip()
def start(name,volume):
 docker('run','-d','--name',name,'--read-only','--tmpfs','/tmp','--cap-drop','ALL','--security-opt','no-new-privileges:true','-p','127.0.0.1::8118','-v',volume+':/data','-e','TEMPO_OWNER_KEY='+key,IMAGE)

 for _ in range(50):
  info=json.loads(docker('inspect',name))[0]
  ports=info['NetworkSettings']['Ports'].get('8118/tcp')
  if ports:return 'http://127.0.0.1:'+ports[0]['HostPort']
  if not info['State']['Running']:raise RuntimeError(docker('logs',name))
  time.sleep(.2)
 raise RuntimeError('Port mapping unavailable')
def request(base,path,method='GET',body=None):
 data=None if body is None else json.dumps(body).encode()
 req=urllib.request.Request(base+'/api/'+path,data=data,method=method,headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=3) as r:return r.read()
def ready(base):
 for _ in range(100):
  try:return json.loads(request(base,'state'))
  except (urllib.error.URLError,TimeoutError,ConnectionError,http.client.RemoteDisconnected):time.sleep(.2)
 raise RuntimeError('Container did not become ready')
try:
 for v in volumes:docker('volume','create',v)
 a=start(names[0],volumes[0]);ready(a)
 assert docker('exec',names[0],'id','-u')=='10001'
 for asset in ['/', '/static/app.js', '/static/style.css']:
  with urllib.request.urlopen(a+asset,timeout=3) as response:assert response.status==200
 project=json.loads(request(a,'projects','POST',{'name':'Recovery project'}))['id'];now=int(time.time())
 request(a,'entries','POST',{'project':project,'note':'Completed & portable','start':now-7200,'end':now-3600})
 running=json.loads(request(a,'entries','POST',{'project':project,'note':'Timer survives restart'}))['id']
 before=request(a,'export.json');csv=request(a,'export.csv')
 docker('restart',names[0]);a='http://127.0.0.1:'+json.loads(docker('inspect',names[0]))[0]['NetworkSettings']['Ports']['8118/tcp'][0]['HostPort'];ready(a)
 assert request(a,'export.json')==before and request(a,'export.csv')==csv
 docker('stop',names[0])
 with tempfile.TemporaryDirectory() as folder:
  source=Path(folder)/'source.sqlite3';saved=Path(folder)/'backup.sqlite3'
  docker('cp',names[0]+':/data/tempo.sqlite3',str(source));backup(source,saved)
  assert saved.stat().st_mode&0o777==0o600
  try:backup(source,saved)
  except FileExistsError:pass
  else:raise AssertionError('Backup replaced existing file')
  docker('run','--rm','--user','0','-v',volumes[1]+':/data','-v',folder+':/backup:ro','--entrypoint','python',IMAGE,'-c',"import shutil,os; shutil.copyfile('/backup/backup.sqlite3','/data/tempo.sqlite3'); os.chown('/data',10001,10001); os.chown('/data/tempo.sqlite3',10001,10001); os.chmod('/data/tempo.sqlite3',0o600)")
 b=start(names[1],volumes[1]);ready(b)
 assert request(b,'export.json')==before and request(b,'export.csv')==csv
 request(b,'entries/'+str(running)+'/stop','POST',{})
 new=json.loads(request(b,'entries','POST',{'project':project,'note':'Fresh timer after recovery'}))['id']
 request(b,'entries/'+str(new),'PUT',{'note':'Corrected after restore','start':now-60,'end':now-30})
 state=json.loads(request(b,'state'));assert any(e['note']=='Corrected after restore' for e in state['entries'])
 print('PASS: non-root/read-only container, restart, exact JSON/CSV and active timer recovery, private non-overwriting backup, fresh writes and corrections after clean-volume restore')
finally:
 for name in names:subprocess.run(['docker','rm','-f',name],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 for v in volumes:subprocess.run(['docker','volume','rm',v],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
