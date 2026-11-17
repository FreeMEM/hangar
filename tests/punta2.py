#!/usr/bin/env python3
"""Pruebas de punta a punta del formato de paquetes 2 (docs/FORMATO2_LOOP.md del servicio, F9): el Hangar de verdad,
desde el Shell, contra el servidor falso (tests/servers/falso.py) con paquetes que solo existen en el formato 2
(respuestas firmadas con la clave de prueba), todo en un arranque del A1200 emulado:

    flock /run/user/1000/dash-emu-red.lock python3 tests/punta2.py

Instalar con una alternativa (la primera que se puede, de otro repositorio), un recomendado y una variante por
procesador; Replaces del mismo autor (se quita el viejo); una respuesta con la firma tocada (no se instala); Actualizar
todo con una pregunta por repositorio; la base en PKG-DB 2 con su repositorio y su motivo.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parent.parent
DASH = Path(os.environ.get("DASH", Path.home() / "Projects" / "FreeMEMLang"))
PUERTO = 47132
sys.path.insert(0, str(DASH / "tools"))
from emu_run import run_programs  # noqa: E402
sys.path.insert(0, str(R / "tests" / "servers"))


def compilar(src, exe):
    opciones = os.environ.get("HANGAR_DASH_OPCIONES", "").split()
    r = subprocess.run([sys.executable, str(DASH / "dash")] + opciones + [str(src), "-o", str(exe)], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=str(DASH)))
    if r.returncode:
        sys.exit(f"{src}: no compila\n{r.stdout}{r.stderr}")


def main():
    b = R / "build" / "punta2"
    b.mkdir(parents=True, exist_ok=True)
    compilar(R / "src" / "hangar.dash", b / "Hangar")
    compilar(R / "tests" / "punta" / "ver2.dash", b / "ver2")
    # la clave pública de prueba del servidor falso
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    publica = Ed25519PrivateKey.from_private_bytes(bytes([3]) * 32).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    raiz = Ed25519PrivateKey.from_private_bytes(bytes([5]) * 32).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    servidor = subprocess.Popen([sys.executable, str(R / "tests" / "servers" / "falso.py"), str(PUERTO)],
                                cwd=R / "tests" / "servers", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    pasos = [
        ("Hangar", "INSTALA xprog SI DESTINO=RAM:Q/"),
        ("Hangar", "LISTA"),
        ("Hangar", "INSTALA foo12 SI DESTINO=RAM:Q/"),
        ("Hangar", "INSTALA foo13 SI DESTINO=RAM:Q/"),
        ("Hangar", "INSTALA malo SI DESTINO=RAM:Q/"),
        ("Hangar", "INSTALA uu SI DESTINO=RAM:Q/"),
        ("Hangar", "ACTUALIZA SI"),
        ("Hangar", "INSTALA zz SI DESTINO=RAM:Q/"),
        ("Hangar", "INSTALA rot SI DESTINO=RAM:Q/"),
        ("Hangar", "INSTALA anulada SI DESTINO=RAM:Q/"),
        ("ver2", ""),
        ("Hangar", "VUELVE uu SI"),
        ("Hangar", "LISTA"),
        ("Hangar", "VUELVE uu SI"),
        ("ver2", ""),
        ("Hangar", "INSTALA gordo SI DESTINO=DH0:G/ ESPACIO=1000"),
        ("Hangar", "INSTALA gordo SI DESTINO=DH0:G/"),
        ("Hangar", "INSTALA adiv SI DESTINO=RAM:Q/"),
        ("Hangar", "INSTALA espejo SI DESTINO=RAM:Q/"),
    ]

    def en_disco(hd):
        ss = hd / "S" / "Startup-Sequence"
        lineas = ss.read_text(encoding="latin-1").splitlines()
        i = next(k for k, l in enumerate(lineas) if l.startswith("DH0:p0"))
        lineas[i:i] = [f"SetEnv Hangar/servidor http://127.0.0.1:{PUERTO}/amiga/v1",
                       f"SetEnv Hangar/clave prueba0000000000 {publica}",
                       f"SetEnv Hangar/raiz {raiz}"]
        ss.write_text("\n".join(lineas) + "\n", encoding="latin-1")

    try:
        res = run_programs([str(b / p) for p, _ in pasos], args=[a for _, a in pasos], timeout=1500,
                           system=os.environ.get("DASH_EMU_SYS_MUI") or os.environ.get("DASH_EMU_SYS"),
                           extra_config="bsdsocket_library = 1\n", on_disk=en_disco)
    finally:
        servidor.terminate()
    salidas = [(r.output or "", r.rc) for r in res]
    for (p, a), (o, rc) in zip(pasos, salidas):
        print(f"=== {p} {a}  (rc {rc})\n{o.rstrip()}")
    esperado = [
        (0, 0, ["instalar yy 1.0 (lo necesita)", "instalar rr 1.0 (recomendado)", "instalar xprog 1.0"]),
        (1, 0, ["xprog 1.0", "yy 1.0", "rr 1.0"]),
        (2, 0, []),
        (3, 0, ["quitar foo12 (lo sustituye otro)", "instalar foo13 1.3"]),
        (4, 5, ["no viene firmada"]),
        (5, 0, []),
        (6, 0, ["actualizar uu 1.0 -> 1.1"]),
        (7, None, ["RAM:Q/U/U es de uu"]),
        (8, 0, ["rot 1.0 instalado"]),
        (9, None, ["no viene firmada"]),
        (10, None, ["X=hunk 020 X.000=no X.020=no", "yy=si ww=no rr=si", "foo12=no foo13=si malo=no", "uu=uu 1.1",
                   "base xprog: PKG-DB 2|Repository: main|Reason: explicit|", "base yy: dependency aminet"]),
        (11, 0, ["Está en la caché", "uu vuelve a la 1.0 (retenido)"]),
        (12, 0, ["= uu 1.0"]),
        (13, 5, ["No hay ninguna versión de uu anterior"]),
        (14, None, ["uu=uu 1.0"]),
        (15, 5, ["No hay sitio en DH0: hacen falta 9766 KB y quedan 1000 KB"]),
        (16, 0, ["gordo 1.0 instalado"]),
        (17, 0, ["ojo: a adiv puede faltarle noexiste", "adiv 1.0 instalado"]),
        (18, 0, ["No se pudo bajar: el servidor respondió 404. Probando otro sitio",
                 "SHA-256 distinto). Probando otro sitio", "espejo 1.0 instalado"]),
    ]
    fallos = 0
    for i, rc, textos in esperado:
        o, r = salidas[i]
        for t in textos:
            if t not in o:
                print(f"FALLO paso {i} ({pasos[i][1]}): falta [{t}]")
                fallos += 1
        if rc is not None and r != rc:
            print(f"FALLO paso {i} ({pasos[i][1]}): rc {r}, se esperaba {rc}")
            fallos += 1
    print("TODO BIEN" if fallos == 0 else f"{fallos} FALLOS")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
