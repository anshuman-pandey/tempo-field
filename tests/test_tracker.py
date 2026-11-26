import unittest,tempfile,time,csv,io,concurrent.futures
from tracker import Ledger,Invalid
from server import create_app
class Checks(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.path=self.tmp.name+'/test.db';self.l=Ledger(self.path);self.p=self.l.project('Client work');self.now=int(time.time());self.key='x'*40;self.c=create_app(self.path,self.key).test_client();self.auth={'Authorization':'Bearer '+self.key}
 def tearDown(self):self.tmp.cleanup()
 def test_persistence(self):
  self.l.entry(self.p,'Build',self.now-120,self.now-60);self.assertEqual(Ledger(self.path).snapshot()['entries'][0]['note'],'Build')
 def test_concurrent_start(self):
  def start(_):
   try:return self.l.entry(self.p,'Build')
   except Invalid:return None
  with concurrent.futures.ThreadPoolExecutor(4) as e:results=list(e.map(start,range(4)))
  self.assertEqual(sum(x is not None for x in results),1)
 def test_invalid_intervals(self):
  for a,b in [(self.now,self.now),(self.now+1,self.now+60),(self.now-604801,self.now),('a',self.now),(True,self.now)]:
   with self.assertRaises(Invalid):self.l.entry(self.p,'Build',a,b)
 def test_edit_running_and_stop_idempotence(self):
  id=self.l.entry(self.p,'Build');self.l.edit(id,self.now-120,self.now-60,'Corrected')
  with self.assertRaises(Invalid):self.l.stop(id)
  self.assertEqual(self.l.snapshot()['entries'][0]['end'],self.now-60)
 def test_foreign_project(self):
  with self.assertRaises(Invalid):self.l.entry(999,'Build')
 def test_csv_injection_and_commas(self):
  p=self.l.project('=1+1');self.l.entry(p,'+formula, quotation "',self.now-30,self.now)
  row=list(csv.reader(io.StringIO(self.l.csv())))[1];self.assertEqual(row[1],"'=1+1");self.assertEqual(row[2],"'+formula, quotation \"");self.assertEqual(row[-1],'30')
 def test_delete(self):
  id=self.l.entry(self.p,'Build');self.l.delete(id);self.assertEqual(self.l.snapshot()['entries'],[])
 def test_auth_all_routes(self):
  for path in ['state','export.csv','export.json']:
   self.assertEqual(self.c.get('/api/'+path).status_code,401)
  self.assertEqual(self.c.post('/api/projects',json={'name':'X'}).status_code,401)
 def test_http_workflow(self):
  r=self.c.post('/api/entries',headers=self.auth,json={'project':self.p,'note':'Planning','start':self.now-90,'end':self.now});self.assertEqual(r.status_code,201)
  self.assertEqual(self.c.get('/api/state',headers=self.auth).json['entries'][0]['note'],'Planning')
  self.assertIn('attachment',self.c.get('/api/export.csv',headers=self.auth).headers['Content-Disposition'])
 def test_json_errors_and_headers(self):
  self.assertEqual(self.c.post('/api/projects',headers=self.auth,json=[]).status_code,400)
  self.assertEqual(self.c.post('/api/projects',headers=self.auth,data='bad').status_code,400)
  r=self.c.get('/');self.assertIn("frame-ancestors 'none'",r.headers['Content-Security-Policy']);self.assertEqual(r.headers['Cache-Control'],'no-store');r.close()
 def test_secret_not_exported(self):
  self.assertNotIn(self.key,self.c.get('/api/export.json',headers=self.auth).text)
 def test_names(self):
  for value in ['',None,'x\n','x'*101]:
   with self.assertRaises(Invalid):self.l.project(value)
