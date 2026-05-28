import asyncio, os, sys, threading

app_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(app_dir)
sys.path.insert(0, app_dir)

_app = None
_load_error = None
_done = threading.Event()

def _load():
    global _app, _load_error
    try:
        from main import app
        from database import engine, Base
        import models
        try:
            Base.metadata.create_all(bind=engine)
        except Exception:
            pass
        _app = app
    except Exception:
        import traceback
        _load_error = traceback.format_exc()
    finally:
        _done.set()

threading.Thread(target=_load, daemon=True).start()
_done.wait(timeout=30)

def _run(environ):
    headers = []
    for k, v in environ.items():
        if k.startswith('HTTP_'):
            headers.append((k[5:].lower().replace('_','-').encode(), v.encode('latin-1')))
    if environ.get('CONTENT_TYPE'):
        headers.append((b'content-type', environ['CONTENT_TYPE'].encode('latin-1')))
    if environ.get('CONTENT_LENGTH'):
        headers.append((b'content-length', environ['CONTENT_LENGTH'].encode('latin-1')))

    scope = {
        'type': 'http', 'asgi': {'version': '3.0'},
        'http_version': environ.get('SERVER_PROTOCOL','HTTP/1.1').split('/')[-1],
        'method': environ.get('REQUEST_METHOD','GET').upper(),
        'path': environ.get('PATH_INFO', '/'),
        'query_string': environ.get('QUERY_STRING','').encode(),
        'root_path': environ.get('SCRIPT_NAME',''),
        'scheme': environ.get('wsgi.url_scheme','http'),
        'server': (environ.get('SERVER_NAME','localhost'), int(environ.get('SERVER_PORT',80))),
        'headers': headers,
    }
    content_length = int(environ.get('CONTENT_LENGTH') or 0)
    body = environ['wsgi.input'].read(content_length) if content_length > 0 else b''

    resp = {'status': None, 'headers': [], 'body': []}

    async def receive():
        return {'type': 'http.request', 'body': body, 'more_body': False}

    async def send(msg):
        if msg['type'] == 'http.response.start':
            codes = {200:'OK',201:'Created',204:'No Content',400:'Bad Request',
                     401:'Unauthorized',403:'Forbidden',404:'Not Found',
                     422:'Unprocessable Entity',500:'Internal Server Error'}
            c = msg['status']
            resp['status'] = f"{c} {codes.get(c,'Unknown')}"
            resp['headers'] = [(k.decode('latin-1'), v.decode('latin-1'))
                               for k, v in msg.get('headers', [])]
        elif msg['type'] == 'http.response.body':
            if msg.get('body'):
                resp['body'].append(msg['body'])

    loop = asyncio.new_event_loop()
    try:
        loop.run_until_complete(_app(scope, receive, send))
    finally:
        loop.close()
    return resp

def application(environ, start_response):
    if _load_error:
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [_load_error.encode()]
    if not _app:
        start_response('200 OK', [('Content-Type', 'text/plain')])
        return [b'Uygulama yuklenemedi']
    try:
        r = _run(environ)
        start_response(r['status'], r['headers'])
        return [b''.join(r['body'])]
    except Exception:
        import traceback, json
        err = traceback.format_exc()
        body = json.dumps({'error': err}).encode()
        start_response('200 OK', [('Content-Type', 'application/json')])
        return [body]
