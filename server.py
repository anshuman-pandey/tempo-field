import os,secrets,sqlite3
from flask import Flask,request,jsonify,send_from_directory,Response
from tracker import Ledger,Invalid

def create_app(path,key):
 if len(key)<32:raise ValueError('TEMPO_OWNER_KEY must be at least 32 characters.')
 app=Flask(__name__);app.config['MAX_CONTENT_LENGTH']=8192;ledger=Ledger(path)
 @app.before_request
 def auth():
  if request.path.startswith('/api/') and not secrets.compare_digest(request.headers.get('Authorization','').encode(),('Bearer '+key).encode()):return jsonify(error='Owner access denied.'),401
  if request.path.startswith('/api/') and request.method in ('POST','PUT') and not request.is_json:return jsonify(error='Send a JSON object.'),400
 @app.after_request
 def headers(r):
  r.headers['Cache-Control']='no-store';r.headers['X-Content-Type-Options']='nosniff';r.headers['Referrer-Policy']='no-referrer';r.headers['Content-Security-Policy']="default-src 'self'; script-src 'self'; style-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'";return r
 @app.errorhandler(Invalid)
 def invalid(e):return jsonify(error=str(e)),400
 @app.errorhandler(sqlite3.Error)
 def storage(e):return jsonify(error='Storage unavailable. Please retry.'),503
 @app.errorhandler(400)
 @app.errorhandler(413)
 def bad(e):return jsonify(error='Send a valid JSON object smaller than 8 KiB.'),e.code
 def body():
  b=request.get_json()
  if not isinstance(b,dict):raise Invalid('Send a JSON object.')
  return b
 @app.get('/')
 def index():return send_from_directory('static','index.html')
 @app.get('/api/state')
 def state():return jsonify(ledger.snapshot())
 @app.post('/api/projects')
 def project():return jsonify(id=ledger.project(body().get('name'))),201
 @app.post('/api/entries')
 def entry():
  b=body();return jsonify(id=ledger.entry(b.get('project'),b.get('note'),b.get('start'),b.get('end'))),201
 @app.post('/api/entries/<int:id>/stop')
 def stop(id):ledger.stop(id);return jsonify(ok=True)
 @app.put('/api/entries/<int:id>')
 def edit(id):
  b=body();ledger.edit(id,b.get('start'),b.get('end'),b.get('note'));return jsonify(ok=True)
 @app.delete('/api/entries/<int:id>')
 def delete(id):ledger.delete(id);return jsonify(ok=True)
 @app.get('/api/export.json')
 def export():
  r=jsonify(ledger.snapshot());r.headers['Content-Disposition']='attachment; filename="tempo-field.json"';return r
 @app.get('/api/export.csv')
 def csv():return Response(ledger.csv(),mimetype='text/csv',headers={'Content-Disposition':'attachment; filename="tempo-field.csv"'})
 return app
if __name__=='__main__':
 os.umask(0o077)
 create_app(os.environ.get('TEMPO_DATABASE','tempo.sqlite3'),os.environ.get('TEMPO_OWNER_KEY','')).run(host='127.0.0.1',port=8118)
