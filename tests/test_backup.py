import unittest,tempfile,sqlite3
from pathlib import Path
from scripts.backup import backup
class Backups(unittest.TestCase):
 def test_backup_preserves_data_and_refuses_overwrite(self):
  with tempfile.TemporaryDirectory() as d:
   src=Path(d)/'a.db';dst=Path(d)/'b.db'
   with sqlite3.connect(src) as c:c.execute('CREATE TABLE records(value TEXT)');c.execute('INSERT INTO records VALUES(?)',('retained',))
   backup(src,dst)
   with sqlite3.connect(dst) as c:self.assertEqual(c.execute('SELECT value FROM records').fetchone()[0],'retained')
   self.assertEqual(dst.stat().st_mode&0o777,0o600)
   with self.assertRaises(FileExistsError):backup(src,dst)
 def test_missing_source_does_not_create_empty_backup(self):
  with tempfile.TemporaryDirectory() as d:
   dst=Path(d)/'backup.db'
   with self.assertRaises(ValueError):backup(Path(d)/'missing.db',dst)
   self.assertFalse(dst.exists())
