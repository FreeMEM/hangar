#!/usr/bin/env python3
"""Banco de pruebas de Hangar en Coffin (Amiberry, 68040, RTG a 1280x1024, MUI 3.8, red del PC): para probar la
ventana de verdad, a mano o desde un guion, sin tocar el Coffin del usuario (una copia reflink de su disco).

Lo maneja el socket de control de Amiberry (ratón, capturas, memoria) y un agente dentro del Amiga (teclas, Shell).
Las piezas (amiga.py, amiberry.py, agente.py, piloto.py, teclas.py, agente.c) salen de las herramientas del vídeo de
Trasfondo. Datos y estado en ~/.cache/hangar-coffin; Traspaso: es su carpeta traspaso/ (DH9:).

    banco.py preparar [--sin-copia]   copia el disco, pone Hangar (build/paquete) en SYS:Utilities/Hangar y arranca
    banco.py arrancar                 arranca con la copia que haya y el agente
    banco.py parar
    banco.py shell "orden" [espera]   una orden de Shell en el Amiga (salida: >Traspaso:x.txt y leer)
    banco.py leer x.txt               lo que el Amiga dejó en Traspaso:
    banco.py captura salida.png       la pantalla entera
    banco.py clic X Y [veces]         mueve el puntero (coordenadas de la pantalla del Amiga) y pulsa
    banco.py derecho X Y              pulsa el botón derecho (menús): mantener con "menu X Y X2 Y2"
    banco.py menu X Y X2 Y2           botón derecho en (X, Y), arrastra a (X2, Y2) y suelta
    banco.py tecla [amiga+|shift+|ctrl+|alt+]TECLA   una tecla por el agente (esc, return, z, f1...)
    banco.py escribir "texto"         teclea un texto (el agente)
    banco.py boton N [título]         pulsa el botón N (desde la izquierda) de la petición (por defecto "Hangar")
    banco.py ventanas                 las ventanas de la pantalla de delante (título, x, y, ancho, alto)
    banco.py texto "busca"            dónde se lee ese texto en la pantalla (OCR)
    banco.py pulsa "texto" [x0 y0 x1 y1]   pulsa donde se lee ese texto (OCR; las posiciones a ojo en las capturas
                                      engañan: medir, no estimar)
"""
import glob
import os
import shutil
import subprocess
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import amiga  # noqa: E402
import agente  # noqa: E402
import piloto as p  # noqa: E402
from amiberry import orden  # noqa: E402

V = os.path.expanduser("~/.cache/hangar-coffin")
# el Coffin del usuario (coffin_r65_32GB.img) dio el 16/11 un error de PFS-III (bloque 2386) y System protegido:
# se usa la copia del 14/11 de las pruebas de Tachyon
# (BANCO_DISCO: otro disco de partida, como DashCoffin.hdf, con el que se probaron LumiGram y Trasfondo con su Installer)
ORIGINAL = os.environ.get("BANCO_DISCO") or os.path.expanduser("~/Amiberry/HardDrives/.coffin-comparativa.img")
COPIA = os.path.expanduser("~/Amiberry/HardDrives/.coffin-hangar.img")   # en el btrfs del original: reflink
TRASP = os.path.join(V, "traspaso")
PANTALLA = ":85"
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
TRASPASO = (38, 250)          # el icono del escritorio de Coffin en RTG (medido para el vídeo de Trasfondo)
if os.environ.get("BANCO_TRASPASO"):  # en otro disco está en otro sitio (DashCoffin.hdf: 38,180)
    TRASPASO = tuple(int(x) for x in os.environ["BANCO_TRASPASO"].split(","))


# códigos raw del teclado del Amiga
CRUDAS = {"esc": 0x45, "return": 0x44, "enter": 0x43, "tab": 0x42, "space": 0x40, "backspace": 0x41, "del": 0x46,
          "up": 0x4C, "down": 0x4D, "right": 0x4E, "left": 0x4F, "f1": 0x50, "help": 0x5F}
for _i, _c in enumerate("qwertyuiop"):
    CRUDAS[_c] = 0x10 + _i
for _i, _c in enumerate("asdfghjkl"):
    CRUDAS[_c] = 0x20 + _i
for _i, _c in enumerate("zxcvbnm"):
    CRUDAS[_c] = 0x31 + _i
for _i, _c in enumerate("1234567890"):
    CRUDAS[_c] = 0x01 + _i


def cerrar_amiberry():
    fpid = os.path.join(V, "amiberry.pid")
    if os.path.exists(fpid):
        pid = int(open(fpid).read())
        try:
            orden("QUIT")
        except OSError:
            pass
        for _ in range(60):
            try:
                os.kill(pid, 0)
            except ProcessLookupError:
                break
            time.sleep(0.5)
        else:
            try:
                os.kill(pid, 9)
            except ProcessLookupError:
                pass
        os.remove(fpid)
    for f in glob.glob(os.path.join(V, "run", "amiberry*.sock")):
        os.remove(f)


def xvfb():
    if subprocess.run(["pgrep", "-f", f"Xvfb {PANTALLA} "], capture_output=True).returncode:
        pr = subprocess.Popen(["Xvfb", PANTALLA, "-screen", "0", "2560x1600x24"], stdout=subprocess.DEVNULL,
                              stderr=subprocess.DEVNULL, start_new_session=True)
        open(os.path.join(V, "xvfb.pid"), "w").write(str(pr.pid))
        time.sleep(2)


def hay_agente():
    try:
        agente.buzon()
        return True
    except (RuntimeError, OSError, AssertionError):
        return False


def arrancar():
    cerrar_amiberry()
    xvfb()
    os.makedirs(os.path.join(V, "run"), exist_ok=True)
    for f in ("agente", "agente.info"):
        shutil.copy(os.path.join(V, "agente", f), TRASP)
    env = dict(os.environ, DISPLAY=PANTALLA, SDL_VIDEODRIVER="x11", SDL_AUDIODRIVER="dummy",
               XDG_RUNTIME_DIR=os.path.join(V, "run"))
    pr = subprocess.Popen(["amiberry", "-f", os.path.join(V, "coffin.uae"), "-s", "use_gui=no"], env=env,
                          stdout=open(os.path.join(V, "amiberry.log"), "w"), stderr=subprocess.STDOUT,
                          start_new_session=True)
    open(os.path.join(V, "amiberry.pid"), "w").write(str(pr.pid))
    t = time.time()
    while time.time() - t < 150:
        try:
            amiga._ib = None
            if "Workbench" in amiga.tareas():
                break
        except (OSError, AssertionError, RuntimeError):
            pass
        time.sleep(2)
    time.sleep(25)
    # el agente, desde el cajón Traspaso del escritorio
    p.mover_a(*TRASPASO)
    p.clic(2)
    t = time.time()
    while not amiga.ventana("Traspaso") and time.time() - t < 15:
        time.sleep(0.3)
    time.sleep(2)
    v = amiga.ventana("Traspaso")
    for _ in range(4):
        d = p.buscar_texto("agente", (v[2], v[3], v[2] + v[4], v[3] + v[5])) if v else None
        if d:
            p.mover_a(d[0], d[1] - 12)
        elif v:
            p.mover_a(v[2] + 141, v[3] + 34)      # medido para el vídeo de Trasfondo
        p.clic(2)
        t = time.time()
        while not hay_agente() and time.time() - t < 8:
            time.sleep(0.5)
        if hay_agente():
            break
    p.cerrar("Traspaso")
    for f in ("agente", "agente.info"):
        try:
            os.remove(os.path.join(TRASP, f))
        except FileNotFoundError:
            pass
    print("agente:", hay_agente())


def shell(o, espera=2.0):
    agente.lanzar(o)
    time.sleep(espera)


def leer(nombre, tope=30):
    f = os.path.join(TRASP, nombre)
    t = time.time()
    while not os.path.exists(f) and time.time() - t < tope:
        time.sleep(0.5)
    time.sleep(1)
    return open(f, encoding="latin-1").read() if os.path.exists(f) else ""


def preparar(sin_copia=False):
    cerrar_amiberry()
    if not sin_copia:
        subprocess.run(["cp", "--reflink=always", ORIGINAL, COPIA], check=True)
    shutil.rmtree(os.path.join(TRASP, "Hangar"), ignore_errors=True)
    os.makedirs(TRASP, exist_ok=True)
    paquete = os.path.join(R, "build", "paquete")
    shutil.copytree(os.path.join(paquete, "Hangar"), os.path.join(TRASP, "Hangar"))
    shutil.copy(os.path.join(paquete, "Hangar.info"), TRASP)
    arrancar()
    shell("C:Copy Traspaso:Hangar SYS:Utilities/Hangar ALL CLONE QUIET", 5)
    shell("C:Copy Traspaso:Hangar.info SYS:Utilities/ CLONE QUIET", 2)
    shell("C:List SYS:Utilities/Hangar >Traspaso:lista.txt", 2)
    print(leer("lista.txt")[-600:])


def botones_de(v, ruta):
    """Los centros (x, y) de los botones de una petición MUI (la ventana v), medidos en una captura: la fila más baja
    con el borde de arriba de los botones (casi toda oscura) y, justo debajo, sus bordes verticales."""
    from PIL import Image
    im = Image.open(ruta).convert("RGB")
    _, _, wx, wy, ww, wh = v
    def oscuros(y):
        return [x for x in range(wx, wx + ww) if sum(im.getpixel((x, y))) < 150]
    def tramo(y):
        xs, mejor, n, antes = oscuros(y), 0, 0, -2
        for x in xs:
            n = n + 1 if x == antes + 1 else 1
            mejor, antes = max(mejor, n), x
        return mejor
    filas = [y for y in range(wy + 15, wy + wh - 2) if tramo(y) >= 30]
    if len(filas) < 2:
        return []
    abajo = filas[-1]
    arriba = max(y for y in filas if y < abajo - 6)
    bordes = [x for x in oscuros(arriba + 1) if wx + 4 < x < wx + ww - 4]
    cy = (arriba + abajo) // 2
    return [((bordes[i] + bordes[i + 1]) // 2, cy) for i in range(0, len(bordes) - 1, 2)]


def main():
    a = sys.argv[1:]
    if not a:
        sys.exit(__doc__)
    o = a[0]
    if o == "preparar":
        preparar("--sin-copia" in a)
    elif o == "arrancar":
        arrancar()
    elif o == "parar":
        cerrar_amiberry()
    elif o == "shell":
        shell(a[1], float(a[2]) if len(a) > 2 else 2.0)
    elif o == "leer":
        print(leer(a[1]))
    elif o == "captura":
        p.captura(os.path.abspath(a[1]))
    elif o == "clic":
        p.mover_a(int(a[1]), int(a[2]), 0.3)
        p.clic(int(a[3]) if len(a) > 3 else 1)
    elif o == "derecho":
        p.mover_a(int(a[1]), int(a[2]), 0.3)
        p.clic(1, boton=2)
    elif o == "menu":
        p.mover_a(int(a[1]), int(a[2]), 0.3)
        orden("SEND_MOUSE", 0, 0, 2)
        time.sleep(0.3)
        p.mover_a(int(a[3]), int(a[4]), 0.6, botones=2)
        time.sleep(0.3)
        orden("SEND_MOUSE", 0, 0, 0)
        time.sleep(0.3)
    elif o == "tecla":
        # por el agente (SEND_KEY de Amiberry no llega como tecla al Amiga): NOMBRE o CÓDIGO raw, y calificadores
        # delante: amiga+z, shift+tab, esc, return, c
        qual = 0
        partes = a[1].lower().split("+")
        for q in partes[:-1]:
            qual |= {"shift": 0x01, "ctrl": 0x08, "alt": 0x10, "lamiga": 0x40, "amiga": 0x80}[q]
        agente.tecla(CRUDAS.get(partes[-1], int(partes[-1], 0) if partes[-1][:1].isdigit() else 0), qual)
    elif o == "escribir":
        agente.escribir(a[1])
    elif o == "pulsa":
        # por el texto que se lee en la pantalla (OCR), mejor que a ojo: zona opcional x0 y0 x1 y1
        zona = tuple(int(x) for x in a[2:6]) if len(a) >= 6 else None
        print(p.pulsar(a[1], zona=zona, dur=0.3))
    elif o == "boton":
        # el botón N (1 el de la izquierda) de la petición más pequeña con ese título (por defecto, la de Hangar)
        titulo = a[2] if len(a) > 2 else "Hangar"
        vs = [w for w in amiga.ventanas() if w[1] == titulo]
        if not vs:
            sys.exit("no hay petición " + titulo)
        v = min(vs, key=lambda w: w[4] * w[5])
        ruta = os.path.join(V, "boton.png")
        p.captura(ruta)
        bs = botones_de(v, ruta)
        n = int(a[1])
        if not 1 <= n <= len(bs):
            sys.exit(f"la petición tiene {len(bs)} botones")
        p.mover_a(bs[n - 1][0], bs[n - 1][1], 0.3)
        p.clic()
        print("pulsado", n, "de", len(bs), bs[n - 1])
    elif o == "ventanas":
        for v in amiga.ventanas():
            print(v[1:])
    elif o == "texto":
        print(p.buscar_texto(a[1]))
    else:
        sys.exit(__doc__)


if __name__ == "__main__":
    main()
