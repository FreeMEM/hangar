#!/usr/bin/env python3
"""Quitar sin romper el sistema (el usuario, 2026-11-20): lo que un programa puso en LIBS:, C:, DEVS:... se queda al
quitarlo, salvo con SISTEMA; otro programa puede usarlo. Contra el servidor falso (tests/servers/falso.py), en un
arranque del A1200 emulado:

    flock /run/user/1000/dash-emu-red.lock python3 tests/punta3.py

conlib1 pone LIBS:hangarprueba.library; conlib2 trae la misma (ya está: se queda la de conlib1). QUITA conlib1 la deja
(conlib2 la usa) y dice por qué; conlib3 con QUITA ... SISTEMA quita la suya.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parent.parent
DASH = Path(os.environ.get("DASH", Path.home() / "Projects" / "FreeMEMLang"))
PUERTO = 47133
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
    b = R / "build" / "punta3"
    b.mkdir(parents=True, exist_ok=True)
    compilar(R / "src" / "hangar.dash", b / "Hangar")
    compilar(R / "tests" / "punta" / "ver3.dash", b / "ver3")
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
        ("Hangar", "INSTALA conlib1 SI DESTINO=RAM:S/"),
        ("Hangar", "INSTALA conlib2 SI DESTINO=RAM:S/"),
        ("ver3", ""),
        ("Hangar", "QUITA conlib1 SI"),
        ("ver3", ""),
        ("Hangar", "INSTALA conlib3 SI DESTINO=RAM:S/"),
        ("Hangar", "QUITA conlib3 SI SISTEMA"),
        ("ver3", ""),
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
        (0, 0, ["conlib1 1.0 instalado"]),
        (1, 0, ["LIBS:hangarprueba.library ya está", "conlib2 1.0 instalado"]),
        (2, None, ["lib=si lib3=no cl1=si"]),
        (3, 0, ["se deja (otros programas pueden usarlo)", "LIBS:hangarprueba.library", "conlib1 quitado"]),
        (4, None, ["lib=si lib3=no cl1=no"]),
        (5, 0, ["conlib3 1.0 instalado"]),
        (6, 0, ["conlib3 quitado"]),
        (7, None, ["lib=si lib3=no cl1=no"]),
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
