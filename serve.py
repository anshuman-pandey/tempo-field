import os
from waitress import serve
from server import create_app
os.umask(0o077)
serve(create_app(os.environ.get('TEMPO_DATABASE','/data/tempo.sqlite3'),os.environ.get('TEMPO_OWNER_KEY','')),host='0.0.0.0',port=8118)
