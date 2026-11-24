#!/usr/bin/env python3
"""Una librería que el paquete trae en varias versiones (Choice; IconLib_46.4, lo contó Oskis R.P), desde el Shell,
contra el servidor falso (tests/servers/falso.py), en un arranque del A1200 emulado:

    flock /run/user/1000/dash-emu-red.lock python3 tests/punta4.py

En LIBS: está la HB de una compilación anterior, renombrada (como la icon.library_HB020 de Oskis). INSTALA sin SI
enseña las versiones y propone la HB (la reconoce por su marca), no la copia y no apunta el paquete como instalado de
esa versión; con SI copia la HB y deja la de antes como .old; ACTUALIZA con VARIANTE= pone otra sin preguntar.
"""
import os
import subprocess
import sys
import time
from pathlib import Path

R = Path(__file__).resolve().parent.parent
DASH = Path(os.environ.get("DASH", Path.home() / "Projects" / "FreeMEMLang"))
PUERTO = 47134
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
    b = R / "build" / "punta4"
    b.mkdir(parents=True, exist_ok=True)
    compilar(R / "src" / "hangar.dash", b / "Hangar")
    compilar(R / "tests" / "punta" / "ver4.dash", b / "ver4")
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
        ("ver4", "prep"),
        ("Hangar", "INSTALA varlib DESTINO=RAM:V/"),
        ("ver4", ""),
        ("Hangar", "INSTALA varlib SI DESTINO=RAM:V/"),
        ("ver4", ""),
        ("Hangar", "ACTUALIZA SI VARIANTE=68000/vprueba.library"),
        ("ver4", ""),
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
        (0, None, ["puesta: vprueba 1.0 (1.1.25) #9 HB"]),
        (1, None, ["varlib trae varias versiones de vprueba.library para LIBS:vprueba.library (ahora: vprueba 1.0 (1.1.25) #9 HB)",
                   "   vprueba.library  (de serie)   en VL/Libs", " * vprueba.library_HB  (la que tienes)   en VL/Bonus",
                   "Sin SI: No copiar", "LIBS:vprueba.library no se copió: varlib sigue apuntado como (sin versión)"]),
        (2, None, ["libs [vprueba 1.0 (1.1.25) #9 HB] old [-] recibo (sin versión) [-]"]),
        (3, 0, ["VL/Bonus/vprueba.library_HB copiada a LIBS:vprueba.library", "varlib 1.0 instalado"]),
        (4, None, ["libs [vprueba 1.0 (1.1.26) #10 HB] old [vprueba 1.0 (1.1.25) #9 HB] recibo 1.0 [LIBS:vprueba.library = VL/Bonus/vprueba.library_HB]"]),
        (5, 0, ["(la que tienes)", "Con VARIANTE=68000/vprueba.library: VL/Libs/68000/vprueba.library",
                "VL/Libs/68000/vprueba.library copiada a LIBS:vprueba.library"]),
        (6, None, ["libs [vprueba 1.0 (1.1.26) #11 K68] old [vprueba 1.0 (1.1.26) #10 HB] recibo 1.1 [LIBS:vprueba.library = VL/Libs/68000/vprueba.library]"]),
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
