"""Create a private, integrity-checked SQLite backup without replacing files."""
import argparse,os,sqlite3
from pathlib import Path

def backup(source,destination):
 source=Path(source).resolve();destination=Path(destination)
 if not source.is_file():raise ValueError('Source database does not exist.')
 fd=os.open(destination,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600);os.close(fd)
 try:
  with sqlite3.connect(source.as_uri()+'?mode=ro',uri=True) as src,sqlite3.connect(destination) as dst:
   src.backup(dst)
   if dst.execute('PRAGMA integrity_check').fetchone()[0]!='ok':raise ValueError('Backup integrity check failed.')
 except:
  destination.unlink();raise
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('source');p.add_argument('destination');a=p.parse_args();backup(a.source,a.destination);print('Created private, integrity-checked backup.')
