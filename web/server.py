"""Local-only HTTP transport. Serves an explicit asset allowlist, never project files."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import json
import os
import secrets
import socket
import numpy as np
from config.settings import ROOT
from connectors.mysql import AppError

STATIC = ROOT/'web'/'static'
ASSETS = {'/': ('index.html', 'text/html; charset=utf-8'),
          '/styles.css': ('styles.css', 'text/css; charset=utf-8'),
          '/app.js': ('app.js', 'text/javascript; charset=utf-8'),
          '/i18n.js': ('i18n.js', 'text/javascript; charset=utf-8'),
          '/charts.js': ('charts.js', 'text/javascript; charset=utf-8'),
          '/favicon.svg': ('favicon.svg', 'image/svg+xml')}


def json_default(value):
    if isinstance(value, np.integer): return int(value)
    if isinstance(value, np.floating): return float(value)
    if isinstance(value, np.bool_): return bool(value)
    raise TypeError(type(value).__name__)


class Handler(BaseHTTPRequestHandler):
    server_version = 'ChinookLocal/1.0'

    def log_message(self, *args):
        # Requests can contain search names. No access/body/config logging.
        pass

    def send(self, status, body, content_type='application/json; charset=utf-8', extra=None):
        if not isinstance(body, bytes):
            body = json.dumps(body, ensure_ascii=False, allow_nan=False, default=json_default).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', content_type)
        self.send_header('Content-Length', str(len(body)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('X-Content-Type-Options', 'nosniff')
        self.send_header('Referrer-Policy', 'no-referrer')
        self.send_header('Content-Security-Policy', "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' blob: data:; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'")
        for key, value in (extra or {}).items(): self.send_header(key, value)
        self.end_headers()
        self.wfile.write(body)

    def allowed_host(self):
        return self.headers.get('Host') in (f'127.0.0.1:{self.server.server_port}', f'localhost:{self.server.server_port}')

    def do_GET(self):
        try:
            if not self.allowed_host():
                return self.send(403, {'error': {'key': 'forbidden'}})
            parsed = urlparse(self.path)
            params = {key: value[0] for key, value in parse_qs(parsed.query).items()}
            if parsed.path == '/api/bootstrap':
                return self.send(200, {'token': self.server.token, **self.server.application.state()})
            if parsed.path.startswith('/api/download/'):
                name = parsed.path.rsplit('/', 1)[-1]
                body, content_type = self.server.application.download(name, params)
                return self.send(200, body, content_type, {'Content-Disposition': f'attachment; filename="chinook-{name}"'})
            if parsed.path.startswith('/api/'):
                return self.send(200, self.server.application.get(parsed.path[5:], params))
            if parsed.path in ASSETS:
                filename, content_type = ASSETS[parsed.path]
                return self.send(200, (STATIC/filename).read_bytes(), content_type)
            self.send(404, {'error': {'key': 'not_found'}})
        except AppError as exc:
            self.send(409, {'error': {'key': exc.key, 'detail': exc.detail}})
        except (ValueError, TypeError, KeyError):
            self.send(400, {'error': {'key': 'invalid_input'}})
        except Exception:
            self.send(500, {'error': {'key': 'unexpected_error'}})

    def do_POST(self):
        try:
            expected = (f'http://127.0.0.1:{self.server.server_port}', f'http://localhost:{self.server.server_port}')
            if (not self.allowed_host() or self.headers.get('Origin') not in expected or
                    not secrets.compare_digest(self.headers.get('X-Chinook-Token', ''), self.server.token)):
                return self.send(403, {'error': {'key': 'forbidden'}})
            length = int(self.headers.get('Content-Length', 0))
            if self.headers.get('Content-Type', '').split(';')[0] != 'application/json' or not 0 < length <= 32*1024*1024:
                return self.send(400, {'error': {'key': 'invalid_input'}})
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError()
            app = self.server.application
            routes = {'/api/connect': app.connect, '/api/filters': app.apply_filters,
                      '/api/refresh': app.refresh,
                      '/api/train': app.train, '/api/forecast': app.predict, '/api/model/load': app.load_model}
            function = routes.get(urlparse(self.path).path)
            if function is None:
                return self.send(404, {'error': {'key': 'not_found'}})
            self.send(202, function(payload))
        except AppError as exc:
            self.send(409, {'error': {'key': exc.key, 'detail': exc.detail}})
        except (ValueError, TypeError, KeyError):
            self.send(400, {'error': {'key': 'invalid_input'}})
        except Exception:
            self.send(500, {'error': {'key': 'unexpected_error'}})


class LocalHTTPServer(ThreadingHTTPServer):
    # Windows SO_REUSEADDR can let two applications bind the same port, causing
    # the browser to reach an older running copy despite the updated files.
    allow_reuse_address = False

    def server_bind(self):
        if os.name == 'nt':
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def create_server(application, port=8765):
    server = LocalHTTPServer(('127.0.0.1', port), Handler)
    server.application = application
    server.token = secrets.token_urlsafe(32)
    server.daemon_threads = True
    return server
