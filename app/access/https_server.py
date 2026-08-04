from __future__ import annotations
import ssl
import json
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from http.cookies import SimpleCookie
from .network import source_allowed
SECURITY_HEADERS={"Content-Security-Policy":"default-src 'self'; frame-ancestors 'none'; object-src 'none'","X-Content-Type-Options":"nosniff","Referrer-Policy":"no-referrer","Cache-Control":"no-store"}
COOKIE_ATTRIBUTES="Secure; HttpOnly; SameSite=Strict; Path=/"
class HttpsCapability:
    @staticmethod
    def context(certificate,private_key):
        context=ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER);context.minimum_version=ssl.TLSVersion.TLSv1_2;context.load_cert_chain(certificate,private_key);return context
    @staticmethod
    def cors(origin,allowed_origin):return origin==allowed_origin and allowed_origin not in {"*","null",""}

class HttpsAccessServer:
    def __init__(self,bind,port,cidr,certificate,private_key,auth,status_provider=lambda:{},allowed_origin=None):
        self.bind,self.port,self.cidr,self.auth,self.status_provider=bind,port,cidr,auth,status_provider;self.allowed_origin=allowed_origin or f"https://{bind}:{port}"
        parent=self
        class Handler(BaseHTTPRequestHandler):
            server_version="LANCTL-HTTPS"
            def log_message(self,format,*args):return
            def _send(self,status,payload,cookie=None):
                body=json.dumps(payload,ensure_ascii=False).encode();self.send_response(status);self.send_header("Content-Type","application/json; charset=utf-8");self.send_header("Content-Length",str(len(body)))
                for key,value in SECURITY_HEADERS.items():self.send_header(key,value)
                if cookie:self.send_header("Set-Cookie",cookie)
                self.end_headers();self.wfile.write(body)
            def _source(self):return source_allowed(self.client_address[0],parent.cidr)
            def _body(self):
                length=min(int(self.headers.get("Content-Length","0")),16384);return json.loads(self.rfile.read(length) or b"{}")
            def _session(self,csrf=False):
                cookie=SimpleCookie(self.headers.get("Cookie",""));session=cookie.get("lanctl_session")
                return parent.auth.validate_session(session.value if session else "",self.client_address[0],self.headers.get("X-CSRF-Token") if csrf else None)
            def do_GET(self):
                if not self._source():return self._send(403,{"error":"source outside managed LAN"})
                if self.path=="/api/status":
                    try:self._session();return self._send(200,parent.status_provider())
                    except PermissionError:return self._send(401,{"error":"authentication required"})
                self._send(404,{"error":"not found"})
            def do_POST(self):
                if not self._source():return self._send(403,{"error":"source outside managed LAN"})
                origin=self.headers.get("Origin")
                if origin and not HttpsCapability.cors(origin,parent.allowed_origin):return self._send(403,{"error":"origin rejected"})
                if self.path=="/api/login":
                    try:
                        body=self._body();user=parent.auth.authenticate_password(str(body.get("username","")),str(body.get("password","")),self.client_address[0]);session,csrf=parent.auth.create_session(user,"web-password",self.client_address[0]);return self._send(200,{"csrfToken":csrf},f"lanctl_session={session.sessionId}; {COOKIE_ATTRIBUTES}")
                    except (ValueError,PermissionError):return self._send(401,{"error":"authentication rejected"})
                try:self._session(csrf=True)
                except PermissionError:return self._send(403,{"error":"invalid session or CSRF"})
                self._send(404,{"error":"not found"})
        server=ThreadingHTTPServer((bind,port),Handler);server.socket=HttpsCapability.context(certificate,private_key).wrap_socket(server.socket,server_side=True);self.server=server
    def serve_forever(self):self.server.serve_forever(poll_interval=.5)
    def stop(self):self.server.shutdown();self.server.server_close()
