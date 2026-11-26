import os,secrets
fd=os.open('.env',os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
with os.fdopen(fd,'w') as f:f.write('TEMPO_OWNER_KEY='+secrets.token_urlsafe(48)+'\n')
print('Created private .env. Read the owner key locally. Keep it private.')
