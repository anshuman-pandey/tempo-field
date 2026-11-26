"""SQLite time ledger. UTC seconds; one running timer per database."""
import sqlite3,time,csv,io,json
from contextlib import contextmanager
class Invalid(ValueError): pass
class Ledger:
 def __init__(self,path):
  self.path=path
  with self.db() as c:
   c.executescript('CREATE TABLE IF NOT EXISTS projects(id INTEGER PRIMARY KEY,name TEXT NOT NULL UNIQUE); CREATE TABLE IF NOT EXISTS entries(id INTEGER PRIMARY KEY,project INTEGER NOT NULL REFERENCES projects(id),note TEXT NOT NULL,start INTEGER NOT NULL,end INTEGER); CREATE UNIQUE INDEX IF NOT EXISTS one_timer ON entries((1)) WHERE end IS NULL;')
 @contextmanager
 def db(self):
  c=sqlite3.connect(self.path,timeout=5);c.row_factory=sqlite3.Row;c.execute('PRAGMA foreign_keys=ON')
  try:
   c.execute('BEGIN IMMEDIATE');yield c;c.commit()
  except: c.rollback();raise
  finally:c.close()
 def text(self,value,limit):
  if not isinstance(value,str) or not value.strip() or len(value)>limit or any(ord(x)<32 for x in value):raise Invalid('Enter text without control characters, within the displayed limit.')
  try:value.encode("utf-8")
  except UnicodeEncodeError:raise Invalid("Enter valid Unicode text.")
  return value.strip()
 def identifier(self,value):
  if type(value)!=int or not 1<=value<=9223372036854775807:raise Invalid("Choose a valid project or entry ID.")
  return value
 def project(self,name):
  name=self.text(name,100)
  with self.db() as c:
   if c.execute('SELECT count(*) FROM projects').fetchone()[0]>=200:raise Invalid('Project limit reached (200).')
   try:return c.execute('INSERT INTO projects(name) VALUES(?)',(name,)).lastrowid
   except sqlite3.IntegrityError:raise Invalid('A project with this name already exists.')
 def interval(self,start,end):
  now=int(time.time())
  if type(start)!=int or type(end)!=int or not 0<=start<end<=now or end-start>604800:raise Invalid('Use past times, with an end after the start and a duration of at most seven days.')
 def entry(self,project,note,start=None,end=None):
  self.identifier(project)
  note=self.text(note,500)
  if start is None:
   if end is not None:raise Invalid('Start time is required.')
   start=int(time.time())
  else:self.interval(start,end)
  with self.db() as c:
   if not c.execute('SELECT 1 FROM projects WHERE id=?',(project,)).fetchone():raise Invalid('Project not found.')
   if c.execute('SELECT count(*) FROM entries').fetchone()[0]>=10000:raise Invalid('Entry limit reached (10000). Export your records.')
   try:return c.execute('INSERT INTO entries(project,note,start,end) VALUES(?,?,?,?)',(project,note,start,end)).lastrowid
   except sqlite3.IntegrityError:raise Invalid('Stop the running timer first.')
 def stop(self,id):
  self.identifier(id)
  with self.db() as c:
   row=c.execute('SELECT * FROM entries WHERE id=?',(id,)).fetchone()
   if not row or row['end'] is not None:raise Invalid('Running timer not found. Refresh your workspace.')
   end=int(time.time())
   if end<=row['start']:raise Invalid('Wait at least one second before stopping.')
   if end-row['start']>604800:raise Invalid('Timer exceeds seven days. Edit its start and end manually.')
   c.execute('UPDATE entries SET end=? WHERE id=?',(end,id))
 def edit(self,id,start,end,note):
  self.identifier(id)
  self.interval(start,end);note=self.text(note,500)
  with self.db() as c:
   if not c.execute('UPDATE entries SET start=?,end=?,note=? WHERE id=?',(start,end,note,id)).rowcount:raise Invalid('Entry not found.')
 def delete(self,id):
  self.identifier(id)
  with self.db() as c:
   if not c.execute('DELETE FROM entries WHERE id=?',(id,)).rowcount:raise Invalid('Entry not found.')
 def snapshot(self):
  with self.db() as c:
   return {'version':1,'projects':[dict(r) for r in c.execute('SELECT * FROM projects ORDER BY name')],'entries':[dict(r) for r in c.execute('SELECT e.*,p.name project_name FROM entries e JOIN projects p ON e.project=p.id ORDER BY start DESC,id DESC')]}
 def csv(self):
  out=io.StringIO(newline='');w=csv.writer(out);w.writerow(['id','project','note','start_utc_seconds','end_utc_seconds','duration_seconds'])
  def safe(s):return "'"+s if s.startswith(('=','+','-','@','\t','\r')) else s
  for r in self.snapshot()['entries']:w.writerow([r['id'],safe(r['project_name']),safe(r['note']),r['start'],r['end'] or '',r['end']-r['start'] if r['end'] else ''])
  return out.getvalue()
