"""Servidor falso de la API de Hangar para los tests del Amiga: respuestas fijas en Latin-1.

python3 falso.py PUERTO [DIRECTORIO]: además sirve los ficheros de DIRECTORIO (los .lha de las pruebas).
"""
import http.server
import sys
import urllib.parse
from pathlib import Path

PUERTO = int(sys.argv[1])
FICHEROS = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).parent / "ficheros"
B = f"http://127.0.0.1:{PUERTO}"
EXTRA_FICHA = ""

LISTA = ("LISTA\t2\t0\t50\n"
         "4050\tTuneFinder\t1.5\tcomm/misc\t88064\t2026-11-02\t0\tSearch and play online radio stations\n"
         "61412\tmodplayer\t\tmus/play\t75776\t\t0\tMOD Player 2.2\n")
FICHA = ("FICHA\nid\t4050\nfuente\taminet\nnombre\tTuneFinder\nversion\t1.5\ncajon\tcomm/misc\ntamano\t88064\n"
         "fecha\t2026-11-02\ncorto\tSearch and play online radio stations\nautor\tMarcin\n"
         "arquitectura\tm68k-amigaos >= 3.0\nrequiere\tTCP/IP stack\nweb\t\n"
         f"descarga\t{B}/comm/misc/TuneFinder.lha\n{EXTRA_FICHA}\n"
         "Short:        Search and play online radio stations\nAuthor: Marcin\n\nTexto del readme.\nFin.\n")



# El repositorio de punta a punta (tests/punta.py): paquetes .lha de verdad, hechos al arrancar, con su SHA-256 y sus
# fichas firmadas. A pide b, B pide c >= 1.0; T llega con un SHA-256 que no cuadra; K tiene Config y Assigns.
import hashlib as _hashlib
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools"))
import lha as _lha
def _paquete(nombre, ficheros):
    datos = b"".join(_lha.entry(n, d, 1700000000, True) for n, d in ficheros) + b"\0"
    return datos
PUNTA = {}
PUNTA_V2 = {}      # nombre en minúsculas -> la entrada del formato 2 (repositorio main)
def _punta(ident, nombre, version, ficheros, extra="", sha_malo=False, v2=""):
    d = _paquete(nombre, ficheros)
    sha = _hashlib.sha256(d).hexdigest()
    if sha_malo:
        sha = "0" * 64
    PUNTA[ident] = (nombre, version, d, sha, extra)
    # lo mismo en el formato 2: la única forma de instalar desde el 0.13.2
    PUNTA_V2[nombre.lower()] = (f"Name: {nombre.lower()}\nVersion: {version}\nRelease: 1\nId: 9{ident}\n"
                                f"Url: {B}/punta/{ident}.lha\nSize: {len(d)}\nSha256: {sha}\n{v2}")
_hunk = b"\0\0\x03\xf3" + b"programa " * 20
_punta("7001", "A", "1.0", [("A/A", _hunk + b"A"), ("A/A.info", b"icono A")], "requiere\tpkg:b\nnec\tpaquete\tb\t\t7002\n",
       v2="Requires: pkg:b\n")
_punta("7002", "B", "1.0", [("B/B", _hunk + b"B")], "requiere\tpkg:c >= 1.0\nnec\tpaquete\tc\t>= 1.0\t7003\n",
       v2="Requires: pkg:c >= 1.0\n")
_punta("7003", "C", "1.2", [("C/C", _hunk + b"C")])
_punta("7004", "T", "1.0", [("T/T", _hunk + b"T")], sha_malo=True)
_punta("7005", "K", "1.0", [("K/K", _hunk + b"K"), ("K/K.prefs", b"ajustes de fabrica")], "config\tK/K.prefs\nasigna\tKAS: K\n",
       v2="Config: K/K.prefs\nAssigns: KAS: K\n")
GRAFO = {
    "5001": ("A", "1.0", [("paquete", "b", "", 5002), ("paquete", "c", "", 5003)]),
    "5002": ("B", "1.0", [("paquete", "c", ">= 2.0", 5003)]),
    "5003": ("C", "2.1", []),
    "5004": ("D", "1.0", [("paquete", "e", "", 5005)]),
    "5005": ("E", "1.0", [("paquete", "d", "", 5004)]),
    "5006": ("F", "1.0", [("lib", "rara.library", "3", 0), ("sistema", "AmigaOS 4", "", 0)]),
}
# la clave de prueba de las firmas (en el cliente, clave_hangar y clave_hangar_id la cambian en el test)
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
CLAVE = Ed25519PrivateKey.from_private_bytes(bytes([3]) * 32)
CLAVE_ID = "prueba0000000000"


# El formato 2 (tests/test_api2.dash): respuestas firmadas con la etiqueta, el Nonce y la Query de la petición
import hashlib
from cryptography.hazmat.primitives import serialization as _ser
_PUB2 = CLAVE.public_key().public_bytes(_ser.Encoding.Raw, _ser.PublicFormat.Raw)
CLAVE2_ID = hashlib.sha256(_PUB2).hexdigest()[:16]
# El fichero keys (docs/FORMATO_PAQUETES.md, 5): firmado por la raíz de prueba (5); vale la clave de siempre (3) y la
# nueva (6); la 7 está y está anulada. "rot" responde con la 6 y "anulada" con la 7.
RAIZ = Ed25519PrivateKey.from_private_bytes(bytes([5]) * 32)
RAIZ_PUB = RAIZ.public_key().public_bytes(_ser.Encoding.Raw, _ser.PublicFormat.Raw).hex()
CLAVE_NUEVA = Ed25519PrivateKey.from_private_bytes(bytes([6]) * 32)
CLAVE_MALA = Ed25519PrivateKey.from_private_bytes(bytes([7]) * 32)


def _pub_id(k):
    pub = k.public_key().public_bytes(_ser.Encoding.Raw, _ser.PublicFormat.Raw)
    return pub.hex(), hashlib.sha256(pub).hexdigest()[:16]


def keys(repo):
    lineas = ["PKG-KEYS 2", f"Repository: {repo}", "Serial: 2", "Expires: 2036-01-01T00:00:00Z"]
    for k in (CLAVE, CLAVE_NUEVA, CLAVE_MALA):
        h, i = _pub_id(k)
        lineas.append(f"Key: response {i} {h}")
    lineas.append(f"Revoked: {_pub_id(CLAVE_MALA)[1]}")
    texto = ("\n".join(lineas) + "\n").encode()
    firma = RAIZ.sign(b"PKG-KEYS-2" + bytes([0]) + texto).hex()
    return texto, f"ed25519 {_pub_id(RAIZ)[1]} {firma}\n".encode()


REPO2 = {
    "aminet": {
        "tunefinder": "Name: tunefinder\nVersion: 1.6\nRelease: 1\nId: 11\nUrl: http://x/TuneFinder.lha\nSize: 100\n"
                      "Sha256: aa\nRequires: reqtools.library 38\nShort: Radio por internet, café\n",
        "reqtoolsusr": "Name: reqtoolsusr\nVersion: 38.1\nRelease: 1\nId: 12\nUrl: http://x/R.lha\nSize: 90\n"
                       "Sha256: bb\nProvides: reqtools.library 38\n",
    },
    "main": {"sintonia": "Name: sintonia\nVersion: 1.0\nEpoch: 1\nRelease: 2\nId: 21\nUrl: http://x/S.lha\nSize: 5\nSha256: cc\n"},
}

# El repositorio de punta a punta del formato 2 (tests/punta2.py): paquetes que solo se instalan con las respuestas 2.
# ident: (repo, nombre, versión, ficheros, campos de más). La ficha del API 1 dice pkg y repo.
PUNTA2 = {}
PUNTA2_NUEVA = {}      # lo que da "updates": uu 1.1


def _punta2(ident, repo, nombre, version, ficheros, extra="", nueva=False, antes=""):
    d = _paquete(nombre, ficheros)
    sha = _hashlib.sha256(d).hexdigest()
    e = (f"Name: {nombre}\nVersion: {version}\nRelease: 1\nId: 9{ident}\n{antes}Url: {B}/punta2/{ident}.lha\nSize: {len(d)}\n"
         f"Sha256: {sha}\n{extra}")
    if nueva:
        PUNTA2_NUEVA[nombre] = (repo, e, d, ident)
    else:
        PUNTA2[ident] = (repo, nombre, version, d, e)
        REPO2.setdefault(repo, {})[nombre] = e


_punta2("8001", "main", "xprog", "1.0", [("X/X.020", b"hunk 020"), ("X/X.000", b"hunk 000")],
        "Requires: pkg:yy | pkg:ww\nRecommends: pkg:rr\nVariant: X/X = X/X.020; 68020\nVariant: X/X = X/X.000\n")
_punta2("8002", "aminet", "yy", "1.0", [("Y/Y", b"yy")])
_punta2("8003", "main", "ww", "1.0", [("W/W", b"ww")])
_punta2("8004", "main", "rr", "1.0", [("R/R", b"rr")])
_punta2("8005", "aminet", "foo12", "1.2", [("F12/F", b"f12")], "Author: Ana\nUploader: ana@example.org\n")
_punta2("8006", "aminet", "foo13", "1.3", [("F13/F", b"f13")],
        "Author: Ana\nUploader: ana@example.org\nReplaces: util/misc/foo12.lha\n")
_punta2("8007", "main", "malo", "1.0", [("M/M", b"malo")])
_punta2("8008", "main", "uu", "1.0", [("U/U", b"uu 1.0")])
_punta2("8009", "main", "uu", "1.1", [("U/U", b"uu 1.1")], nueva=True)
_punta2("8011", "main", "rot", "1.0", [("ROT/R", b"rot")])
_punta2("8012", "main", "anulada", "1.0", [("AN/A", b"an")])
_punta2("8013", "main", "gordo", "1.0", [("G/G", b"gordo")], "Installed-Size: 5000000\n")
_punta2("8014", "main", "adiv", "1.0", [("ADIV/A", b"adiv")], "Declared: no\nRequires: pkg:noexiste\n")
_punta2("8010", "main", "zz", "1.0", [("U/U", b"zz pisa a uu")])
# Url repetible (P6a): el primer sitio no lo tiene (404), el segundo da otra cosa (SHA-256 distinto), el tercero vale
_punta2("8015", "main", "espejo", "1.0", [("ESP/E", b"espejo")], antes=f"Url: {B}/punta2/9999.lha\nUrl: {B}/punta2/roto.lha\n")
# Lo que se pone en el sistema (tests/punta3.py): dos programas con la misma librería en LIBS: y uno con otra
_punta2("8016", "main", "conlib1", "1.0", [("CL1/CL1", b"cl1"), ("CL1/hangarprueba.library", b"lib de conlib1")],
        "Install: system LIBS:hangarprueba.library\n")
_punta2("8017", "main", "conlib2", "1.0", [("CL2/CL2", b"cl2"), ("CL2/hangarprueba.library", b"lib de conlib2")],
        "Install: system LIBS:hangarprueba.library\n")
_punta2("8018", "main", "conlib3", "1.0", [("CL3/CL3", b"cl3"), ("CL3/hangarprueba3.library", b"lib de conlib3")],
        "Install: system LIBS:hangarprueba3.library\n")
# Una librería en varias versiones para elegir (Choice, tests/punta4.py; como IconLib, lo contó Oskis R.P): la de
# serie, la de 68000 y una con sufijo en Bonus; la 1.1 llega por "updates"
def _varlib(compilacion):
    lib = lambda marca: b"\0\0\x03\xf3libreria\0" + f"vprueba 1.0 (1.1.26) #{compilacion} {marca}".encode() + b"\0"
    return [("VL/VL", b"programa"), ("VL/Libs/vprueba.library", lib("STD")), ("VL/Libs/68000/vprueba.library", lib("K68")),
            ("VL/Bonus/vprueba.library_HB", lib("HB"))]
_VARLIB = ("Choice: LIBS:vprueba.library = VL/Libs/vprueba.library\nChoice: LIBS:vprueba.library = VL/Libs/68000/vprueba.library\n"
           "Choice: LIBS:vprueba.library = VL/Bonus/vprueba.library_HB\n")
_punta2("8019", "main", "varlib", "1.0", _varlib(10), _VARLIB)
_punta2("8020", "main", "varlib", "1.1", _varlib(11), _VARLIB, nueva=True)

# Lo de Aminet que su autor publica también en Hangar (tests/test_autor.dash, lo contó Ferrán García): Trasfondo, del
# mismo autor y verificado, pasa a main; mcp no (en main es de otro autor) y fantasma tampoco (su autor no está
# verificado). id: (fuente, nombre, versión, autor, verificado)
FICHAS_AUTOR = {
    "6101": ("aminet", "Trasfondo", "2.9.13", "FreeMEM", False),
    "6102": ("github", "Trasfondo", "2.11.0", "FreeMEM <hola@freemem.space>", True),
    "6103": ("aminet", "MCP", "13.76", "Jorg Sixt", False),
    "6104": ("github", "MCP", "1.49", "Otro", True),
    "6105": ("aminet", "Fantasma", "1.0", "Ana", False),
    "6106": ("github", "Fantasma", "2.0", "Ana", False),
    "6107": ("aminet", "IconPrueba_46.4", "46.4.605", "Peter Keunecke", False),
}
# lo que la de IconPrueba pone en el sistema (Choice), como IconLib
ELIGE_AUTOR = {"6107": "elige\tLIBS:iconprueba.library = IconPrueba_46.4/Libs/iconprueba.library\n"
                       "elige\tLIBS:iconprueba.library = IconPrueba_46.4/Libs/68000/iconprueba.library\n"}
for _i, (_f, _n, _v, _a, _ver) in FICHAS_AUTOR.items():
    if _f == "github":
        REPO2["main"][_n.lower()] = (f"Name: {_n.lower()}\nVersion: {_v}\nRelease: 1\nId: {_i}\nUrl: http://x/{_n}.lha\n"
                                    f"Size: 5\nSha256: cc\nAuthor: {_a}\n")


def respuesta2(ruta, cuerpo_post=None):
    """La respuesta del formato 2 a una ruta /pkg/v2/<repo>/<arq>/<acción>?..., y su firma"""
    u = urllib.parse.urlparse(ruta)
    q = urllib.parse.parse_qs(u.query)
    _, _, _, repo, arq, accion = u.path.split("/", 5)
    nombre = q.get("name", q.get("what", q.get("q", [""])))[0]
    nonce = q.get("nonce", [""])[0]
    serial = 5 if nombre == "viejo" else 100
    query = ruta + (" " + hashlib.sha256(cuerpo_post).hexdigest() if cuerpo_post is not None else "")
    if nombre == "otrononce":
        nonce = "f" * 24
    texto = (f"PKG-RESPONSE 2\nRepository: {'main' if nombre == 'otrorepo' else repo}\nArchitecture: {arq}\n"
             f"Serial: {serial}\nQuery: {query}\nNonce: {nonce}\n")
    entradas = dict(REPO2.get(repo, {}))
    if repo == "main":
        entradas.update(PUNTA_V2)
    if accion == "package":
        # los nombres de los casos malos (tocado, otrononce...) dan tunefinder
        especiales = ("tocado", "otrononce", "viejo", "otrorepo")
        elegidas = [entradas[n] for n in ((nombre, "tunefinder") if nombre in especiales else (nombre,)) if n in entradas][:1]
    elif accion == "provides":
        elegidas = [e for e in entradas.values() if "Provides: " + nombre in e]
    elif accion == "versions":
        elegidas = [e for k, e in entradas.items() if k == nombre]
    elif accion == "updates":
        elegidas = []
        for l in cuerpo_post.decode("latin-1").splitlines():
            w = l.split()
            if w and w[0] in PUNTA2_NUEVA and PUNTA2_NUEVA[w[0]][0] == repo:
                elegidas.append(PUNTA2_NUEVA[w[0]][1])
            elif w and w[0] in entradas:
                elegidas.append(entradas[w[0]])
    elif accion == "identify":
        # como /amiga/v1/reconocer, tras la cabecera
        elegidas = []
        texto += "\n"
        for l in cuerpo_post.decode("latin-1").splitlines():
            p = l.split("\t")
            if p[0].lower() == "tunefinder" and p[1:2] == ["100"]:
                texto += f"{p[0]}\tnueva\t4050\tTuneFinder\t1.4\t1.5\tTuneFinder/TuneFinder\n"
            else:
                texto += f"{p[0]}\tdesconocido\t\t\t\t\t\n"
    else:
        elegidas = list(REPO2.get(repo, {}).values())   # buscar: sin las de punta a punta
    for e in elegidas:
        texto += "\n" + e
    datos = texto.encode("utf-8")
    k = {"rot": CLAVE_NUEVA, "anulada": CLAVE_MALA}.get(nombre, CLAVE)
    firma = f"{_pub_id(k)[1]} {k.sign(b'PKG-RESPONSE-2' + bytes([0]) + datos).hex()}"
    if nombre == "tocado":
        datos = datos.replace(b"1.6", b"1.7")
    if nombre == "malo":
        datos = datos.replace(b"Version: 1.0", b"Version: 9.9")
    return datos, firma


class Manejador(http.server.BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def responder(self, codigo, texto, tipo="text/plain; charset=iso-8859-1", firma=None, firma2=None):
        datos = texto.encode("latin-1") if isinstance(texto, str) else texto
        self.send_response(codigo)
        self.send_header("Content-Type", tipo)
        if firma is not None:
            self.send_header("X-Hangar-Firma", firma)
        if firma2 is not None:
            self.send_header("X-Pkg-Signature", firma2)
        self.send_header("Content-Length", str(len(datos)))
        self.end_headers()
        self.wfile.write(datos)

    def do_GET(self):
        u = urllib.parse.urlparse(self.path)
        q = urllib.parse.parse_qs(u.query)
        if u.path.startswith("/repo/") and u.path.endswith(("/keys", "/keys.sig")):
            texto, firma = keys(u.path.split("/")[2])
            return self.responder(200, firma if u.path.endswith(".sig") else texto)
        if u.path.startswith("/pkg/v2/"):
            datos, firma = respuesta2(self.path)
            return self.responder(200, datos, "text/plain; charset=utf-8", firma2=firma)
        if u.path == "/amiga/v1/buscar" and q.get("q", [""])[0] in [v[1] for v in PUNTA2.values()]:
            n = q["q"][0]
            filas = [f"{k}\t{v[1]}\t{v[2]}\tutil/misc\t{len(v[3])}\t2026-11-14\t0\tPaquete {v[1]}\n" for k, v in PUNTA2.items() if v[1] == n]
            return self.responder(200, f"LISTA\t{len(filas)}\t0\t50\n" + "".join(filas))
        if u.path.startswith("/amiga/v1/ficha/") and u.path[-4:] in PUNTA2:
            repo, nombre, version, d, e = PUNTA2[u.path[-4:]]
            t = (f"FICHA\nid\t{u.path[-4:]}\nfuente\taminet\nnombre\t{nombre}\nversion\t{version}\ncajon\tutil/misc\n"
                 f"tamano\t{len(d)}\ndescarga\t{B}/punta2/{u.path[-4:]}.lha\n{EXTRA_FICHA}pkg\t{nombre}\nrepo\t{repo}\n\nTexto\n")
            return self.responder(200, t)
        if u.path.startswith("/punta2/"):
            ident = u.path[8:12]
            if ident == "roto":
                # del mismo tamaño que el bueno y otro contenido: lo pilla el SHA-256, no el tamaño
                bueno = PUNTA2["8015"][3]
                return self.responder(200, bytes(b ^ 0x5A for b in bueno), "application/x-lha")
            if ident == "9999":
                return self.responder(404, "no está")
            for repo, e, d, i in PUNTA2_NUEVA.values():
                if i == ident:
                    return self.responder(200, d, "application/x-lha")
            if ident in PUNTA2:
                return self.responder(200, PUNTA2[ident][3], "application/x-lha")
        if u.path == "/amiga/v1/buscar" and q.get("q", [""])[0] in [v[0] for v in PUNTA.values()]:
            n = q["q"][0]
            filas = [f"{k}\t{v[0]}\t{v[1]}\tutil/misc\t{len(v[2])}\t2026-11-10\t0\tPaquete {v[0]}\n" for k, v in PUNTA.items() if v[0] == n]
            return self.responder(200, f"LISTA\t{len(filas)}\t0\t50\n" + "".join(filas))
        # (las capturas de lo de Ferrán García: la ficha de Míos por su repositorio, buscar Trasfondo y una librería
        # que va a LIBS: como IconLib)
        if u.path.startswith("/amiga/v1/ficha-pkg/"):
            _, _, _, _, repo, nombre = u.path.split("/", 5)
            for i, (f, n, v, a, ver) in FICHAS_AUTOR.items():
                if n.lower() == nombre and (f == "aminet") == (repo == "aminet"):
                    u = urllib.parse.urlparse(f"/amiga/v1/ficha/{i}")
                    break
        if u.path == "/amiga/v1/buscar" and q.get("q", [""])[0].lower() in [v[1].lower() for v in FICHAS_AUTOR.values()]:
            n = q["q"][0].lower()
            filas = [f"{k}\t{v[1]}\t{v[2]}\tutil/moni\t5\t2026-11-25\t0\t{'De su autor' if v[0] == 'github' else 'De Aminet'}\n"
                     for k, v in FICHAS_AUTOR.items() if v[1].lower() == n]
            return self.responder(200, f"LISTA\t{len(filas)}\t0\t50\n" + "".join(filas))
        if u.path.startswith("/amiga/v1/ficha/") and u.path[-4:] in FICHAS_AUTOR:
            ident = u.path[-4:]
            fuente, nombre, version, autor, verificado = FICHAS_AUTOR[ident]
            t = (f"FICHA\nid\t{ident}\nfuente\t{fuente}\nnombre\t{nombre}\nversion\t{version}\ncajon\tutil/moni\n"
                 f"tamano\t5\nautor\t{autor}\ndescarga\t{B}/x.lha\n{EXTRA_FICHA}pkg\t{nombre.lower()}\n"
                 f"repo\t{'aminet' if fuente == 'aminet' else 'main'}\n" + ("verificado\tsi\n" if verificado else "")
                 + ELIGE_AUTOR.get(ident, "") + "\nTexto\n")
            return self.responder(200, t)
        if u.path.startswith("/amiga/v1/ficha/") and u.path[-4:] in PUNTA:
            ident = u.path[-4:]
            nombre, version, d, sha, extra = PUNTA[ident]
            t = (f"FICHA\nid\t{ident}\nfuente\thangar\nnombre\t{nombre}\nversion\t{version}\ncajon\tutil/misc\n"
                 f"tamano\t{len(d)}\ndescarga\t{B}/punta/{ident}.lha\n{EXTRA_FICHA}paquete\t{nombre.lower()}\nrelease\t1\n"
                 f"pkg\t{nombre.lower()}\nrepo\tmain\n"
                 f"sha256\t{sha}\ntamano_fichero\t{len(d)}\n{extra}\nTexto de {nombre}\n")
            datos = t.encode("latin-1")
            return self.responder(200, datos, firma=f"{CLAVE_ID} {CLAVE.sign(datos).hex()}")
        if u.path.startswith("/punta/") and u.path[7:11] in PUNTA:
            return self.responder(200, PUNTA[u.path[7:11]][2], "application/x-lha")
        if u.path == "/amiga/v1/buscar":
            # comprueba que la búsqueda llega en UTF-8 bien codificada
            if q.get("q") != ["player ñ"]:
                return self.responder(400, f"ERROR\tq rara: {q.get('q')}\n")
            return self.responder(200, LISTA)
        if u.path in ("/amiga/v1/novedades", "/amiga/v1/autores", "/amiga/v1/todo") or u.path.startswith("/amiga/v1/categoria/"):
            return self.responder(200, LISTA)
        if u.path == "/amiga/v1/categorias":
            return self.responder(200, "CATEGORIAS\t2\ncomm/misc\t1\nmus/play\t1\n")
        if u.path == "/amiga/v1/ficha/4050":
            return self.responder(200, FICHA)
        # la ficha firmada con la clave de prueba (tests/test_api.dash), una tocada por el camino y otra sin firma
        if u.path in ("/amiga/v1/ficha/4060", "/amiga/v1/ficha/4061", "/amiga/v1/ficha/4062"):
            datos = FICHA.replace("id\t4050", "id\t" + u.path[-4:]).encode("latin-1")
            firma = f"{CLAVE_ID} {CLAVE.sign(datos).hex()}"
            if u.path.endswith("4061"):
                datos = datos.replace(b"1.5", b"1.6")
            return self.responder(200, datos, firma=None if u.path.endswith("4062") else firma)
        # un grafo de dependencias (tests/test_dependencias.dash): A pide b y c, B pide c >= 2.0, D y E se piden
        # entre sí (un ciclo), F pide algo que no trae nadie
        if u.path.startswith("/amiga/v1/ficha/50") and u.path[-4:] in GRAFO:
            ident = u.path[-4:]
            nombre, version, necs = GRAFO[ident]
            t = f"FICHA\nid\t{ident}\nfuente\taminet\nnombre\t{nombre}\nversion\t{version}\ncajon\tutil/misc\ntamano\t100\n"
            t += f"descarga\t{B}/x.lha\n{EXTRA_FICHA}"
            for tipo, valor, ver, paq in necs:
                t += f"nec\t{tipo}\t{valor}\t{ver}\t{paq}\n"
            return self.responder(200, t + "\nTexto\n")
        if u.path == "/amiga/v1/historial/4050":
            datos = ("HISTORIAL\t2\n1.5\t1\t88064\taa11\t2026-11-02\t" + B + "/comm/misc/TuneFinder.lha\n"
                     "  Requires: TCP/IP\n1.4\t2\t80000\tbb22\t2026-10-01\t" + B + "/viejo/TuneFinder.lha\n").encode("latin-1")
            return self.responder(200, datos, firma=f"{CLAVE_ID} {CLAVE.sign(datos).hex()}")
        if u.path.startswith("/amiga/v1/ficha/"):
            return self.responder(404, "ERROR\tno existe\n")
        f = FICHEROS / u.path.lstrip("/")
        if f.is_file():
            return self.responder(200, f.read_bytes(), "application/octet-stream")
        self.responder(404, "ERROR\tno existe\n")

    def do_POST(self):
        n = int(self.headers.get("Content-Length", 0))
        crudo = self.rfile.read(n)
        if self.path.startswith("/pkg/v2/"):
            datos, firma = respuesta2(self.path, crudo)
            return self.responder(200, datos, "text/plain; charset=utf-8", firma2=firma)
        cuerpo = crudo.decode("latin-1")
        if self.path == "/amiga/v1/versiones":
            out = []
            for l in cuerpo.splitlines():
                nombre, _, ver = l.partition("\t")
                if nombre.lower() == "tunefinder":
                    out.append(f"{nombre}\t{ver}\tnueva\t4050\t1.5")
                else:
                    out.append(f"{nombre}\t{ver}\tdesconocido\t\t")
            return self.responder(200, f"VERSIONES\t{len(out)}\n" + "".join(o + "\n" for o in out))
        if self.path == "/amiga/v1/reconocer":
            out = []
            for l in cuerpo.splitlines():
                p = l.split("\t")
                if p[0].lower() == "tunefinder" and p[1] == "100":
                    out.append(f"{p[0]}\tnueva\t4050\tTuneFinder\t1.4\t1.5")
                else:
                    out.append(f"{p[0]}\tdesconocido\t\t\t\t")
            return self.responder(200, f"RECONOCER\t{len(out)}\n" + "".join(o + "\n" for o in out))
        self.responder(404, "ERROR\tno existe\n")


http.server.ThreadingHTTPServer(("127.0.0.1", PUERTO), Manejador).serve_forever()
