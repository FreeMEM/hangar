"""Servidor HTTPS de prueba con un certificado autofirmado (tests/servers/autofirmado.pem, solo para las pruebas):
Hangar no lo puede comprobar y tiene que avisar (src/certificados.dash).

python3 tls.py PUERTO: GET /hola contesta "hola"; /descarga, unos bytes; lo demás, 404.
"""
import http.server
import ssl
import sys
from pathlib import Path

PUERTO = int(sys.argv[1])
PEM = Path(__file__).parent / "autofirmado.pem"


class Manejador(http.server.BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def do_GET(self):
        if self.path.startswith("/hola"):
            cuerpo = b"hola\n"
        elif self.path.startswith("/descarga"):
            cuerpo = bytes(range(256)) * 4
        else:
            self.send_response(404)
            self.send_header("Content-Length", "0")
            self.send_header("Connection", "close")
            self.end_headers()
            return
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Connection", "close")
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, *a):
        pass


contexto = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
contexto.load_cert_chain(PEM)
servidor = http.server.ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador)
servidor.socket = contexto.wrap_socket(servidor.socket, server_side=True)
servidor.serve_forever()
