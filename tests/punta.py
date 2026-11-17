#!/usr/bin/env python3
"""Pruebas de punta a punta del cliente (docs/PAQUETES_LOOP.md del servicio, K14): el Hangar de verdad, desde el Shell,
contra un repositorio falso con paquetes de verdad (tests/servers/falso.py: .lha, SHA-256 y fichas firmadas con una
clave de prueba), todo en un solo arranque del A1200 emulado:

    flock /run/user/1000/dash-emu-red.lock python3 tests/punta.py

Instalar con dependencias (C, luego B, luego A), una descarga que no cuadra con su SHA-256 (no se instala nada),
Config y Assigns, Verificar y reparar, reinstalar con los ajustes del usuario cambiados (.new), quitar con los
huérfanos y deshacerlo. Necesita $DASH (con sha256 y ed25519_verify) y el entorno del emulador.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parent.parent
DASH = Path(os.environ.get("DASH", Path.home() / "Projects" / "FreeMEMLang"))
PUERTO = 47131
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
    b = R / "build" / "punta"
    b.mkdir(parents=True, exist_ok=True)
    compilar(R / "src" / "hangar.dash", b / "Hangar")
    compilar(R / "tests" / "punta" / "tocar.dash", b / "tocar")
    compilar(R / "tests" / "punta" / "ver.dash", b / "ver")
    # la clave pública de prueba del servidor falso
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    publica = Ed25519PrivateKey.from_private_bytes(bytes([3]) * 32).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    servidor = subprocess.Popen([sys.executable, str(R / "tests" / "servers" / "falso.py"), str(PUERTO)],
                                cwd=R / "tests" / "servers", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    pasos = [
        ("Hangar", "INSTALA A SI DESTINO=RAM:P/"),
        ("Hangar", "LISTA"),
        ("Hangar", "INSTALA T SI DESTINO=RAM:P/"),
        ("Hangar", "INSTALA K SI DESTINO=RAM:P/"),
        ("tocar", ""),
        ("Hangar", "VERIFICA SI"),
        ("Hangar", "INSTALA K SI DESTINO=RAM:P/"),
        ("ver", ""),
        ("Hangar", "QUITA A SI"),
        ("Hangar", "LISTA"),
        ("Hangar", "DESHAZ SI"),
        ("Hangar", "LISTA"),
        ("ver", ""),
    ]

    def en_disco(hd):
        ss = hd / "S" / "Startup-Sequence"
        lineas = ss.read_text(encoding="latin-1").splitlines()
        i = next(k for k, l in enumerate(lineas) if l.startswith("DH0:p0"))
        lineas[i:i] = [f"SetEnv Hangar/servidor http://127.0.0.1:{PUERTO}/amiga/v1",
                       f"SetEnv Hangar/clave prueba0000000000 {publica}"]
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
    # desde el 0.13.2 todo se instala por el formato 2 con el plan del resolutor; desde el 0.14.3 lo pedido lleva su
    # nombre del catálogo (A, K) y las dependencias el del índice (b, c)
    esperado = [
        (0, 0, ["instalar c 1.2 (lo necesita)", "instalar b 1.0 (lo necesita)", "A 1.0 instalado"]),
        (1, 0, ["* A 1.0", "+ b 1.0", "+ c 1.2"]),
        (2, 5, ["SHA-256 distinto"]),
        (3, 0, ["K 1.0 instalado"]),
        (5, 0, ["1 programa reparado"]),
        (6, 0, ["ajustes tuyos se quedan"]),
        (7, None, ["A=si B=si C=si T=no", "prefs=mis ajustes nuevo=si", ";BEGIN pkg k|Assign KAS: \"RAM:P/K\"|;END pkg k", "A arreglado=si"]),
        (8, 0, ["A quitado, y 2 más"]),
        (9, 0, ["* K 1.0"]),
        (11, 0, ["* A 1.0", "+ b 1.0", "+ c 1.2", "* K 1.0"]),
        (12, None, ["A=si B=si C=si T=no"]),
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
