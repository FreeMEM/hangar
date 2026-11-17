#!/usr/bin/env python3
"""Prueba de cortes: instalar A (con B y C) muriendo en el paso N del
diario para cada N (CORTE=N), y también muriendo a mitad de deshacer (CORTE_DESHAZ=N). Tras cada corte, Hangar
arranca, deshace solo, y no queda nada: ni ficheros, ni cajones, ni recibos. Mismo servidor falso que tests/punta.py.

    flock /run/user/1000/dash-emu-red.lock python3 tests/cortes.py

(Lo de abajo es de tests/punta.py:) Pruebas de punta a punta del cliente (docs/PAQUETES_LOOP.md del servicio, K14): el Hangar de verdad, desde el Shell,
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
    compilar(R / "tests" / "punta" / "vercortes.dash", b / "vercortes")
    compilar(R / "tests" / "punta" / "veract.dash", b / "veract")
    # la clave pública de prueba del servidor falso
    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
    from cryptography.hazmat.primitives import serialization
    publica = Ed25519PrivateKey.from_private_bytes(bytes([3]) * 32).public_key().public_bytes(
        serialization.Encoding.Raw, serialization.PublicFormat.Raw).hex()
    servidor = subprocess.Popen([sys.executable, str(R / "tests" / "servers" / "falso.py"), str(PUERTO)],
                                cwd=R / "tests" / "servers", stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.5)
    N = int(os.environ.get("CORTES", "16"))
    pasos = []
    for n in range(1, N + 1):
        pasos += [("Hangar", f"INSTALA A SI DESTINO=RAM:P/ CORTE={n}"), ("Hangar", "LISTA"),
                  ("Hangar", "QUITA A SI"), ("vercortes", "")]
    # cortes a mitad de deshacer: se corta la instalación en el paso 6 y luego el deshacer en el paso 1, 2 y 3
    for m in (1, 2, 3):
        pasos += [("Hangar", "INSTALA A SI DESTINO=RAM:P/ CORTE=6"), ("Hangar", f"LISTA CORTE_DESHAZ={m}"),
                  ("Hangar", "LISTA"), ("vercortes", "")]

    # cortes al quitar: A (con B y C) instalado entero; se quita cortando en el paso N; tras el corte, al arrancar se
    # deshace y todo sigue instalado (si no hubo corte, se quitó: se vuelve a instalar para el siguiente)
    Q = int(os.environ.get("CORTES_QUITA", "12"))
    inicio_quitar = len(pasos)
    pasos.append(("Hangar", "INSTALA A SI DESTINO=RAM:P/"))
    for n in range(1, Q + 1):
        pasos += [("Hangar", f"QUITA A SI CORTE={n}"), ("Hangar", "LISTA"), ("vercortes", ""),
                  ("Hangar", "INSTALA A SI DESTINO=RAM:P/")]

    # cortes al actualizar: uu 1.0 instalado, el servidor da 1.1; se actualiza cortando en el paso N (y cortando el
    # deshacer de un corte); tras el corte, al arrancar se deshace y queda uu 1.0 entero. Luego se quita y se vuelve a
    # poner la 1.0 para el siguiente.
    U = int(os.environ.get("CORTES_ACT", "5"))
    inicio_act = len(pasos)
    pasos += [("Hangar", "QUITA A SI"), ("Hangar", "INSTALA uu SI DESTINO=RAM:P/")]
    casos_act = [(f"ACTUALIZA SI CORTE={n}", "LISTA") for n in range(1, U + 1)]
    casos_act += [("ACTUALIZA SI CORTE=3", f"LISTA CORTE_DESHAZ={m}") for m in (1, 2, 3)]
    for act, lista in casos_act:
        pasos += [("Hangar", act), ("Hangar", lista), ("Hangar", "LISTA"), ("veract", ""),
                  ("Hangar", "QUITA uu SI"), ("Hangar", "INSTALA uu SI DESTINO=RAM:P/")]

    def en_disco(hd):
        ss = hd / "S" / "Startup-Sequence"
        lineas = ss.read_text(encoding="latin-1").splitlines()
        i = next(k for k, l in enumerate(lineas) if l.startswith("DH0:p0"))
        lineas[i:i] = [f"SetEnv Hangar/servidor http://127.0.0.1:{PUERTO}/amiga/v1",
                       f"SetEnv Hangar/clave prueba0000000000 {publica}"]
        ss.write_text("\n".join(lineas) + "\n", encoding="latin-1")

    try:
        res = run_programs([str(b / p) for p, _ in pasos], args=[a for _, a in pasos], timeout=3600,
                           system=os.environ.get("DASH_EMU_SYS_MUI") or os.environ.get("DASH_EMU_SYS"),
                           extra_config="bsdsocket_library = 1\n", on_disk=en_disco)
    finally:
        servidor.terminate()
    salidas = [(r.output or "", r.rc) for r in res]
    for (p, a), (o, rc) in zip(pasos, salidas):
        print(f"=== {p} {a}  (rc {rc})\n{o.rstrip()}")
    fallos, cortados, enteros = 0, 0, 0
    act_cortados, act_enteros = 0, 0
    for k in range(inicio_act + 2, len(pasos), 6):
        act, lista1, lista, ver = salidas[k:k + 4]
        if "CORTE_DESHAZ" in pasos[k + 1][1] and "CORTE al deshacer" not in lista1[0]:
            print(f"FALLO {pasos[k + 1][1]}: no se cortó el deshacer")
            fallos += 1
        if "CORTE" in act[0]:
            act_cortados += 1
            if "uu 1.0" not in lista[0] or "uu=uu 1.0 base=1.0 cajon=1" not in ver[0]:
                print(f"FALLO {pasos[k][1]}: tras el corte al actualizar no volvió la 1.0: {lista[0].strip()[-60:]} | {ver[0].strip()}")
                fallos += 1
        elif "uu=uu 1.1 base=1.1 cajon=1" in ver[0]:
            act_enteros += 1
        else:
            print(f"FALLO {pasos[k][1]}: sin corte, no quedó la 1.1: {ver[0].strip()}")
            fallos += 1
    print(f"actualizar: {act_cortados} cortes, {act_enteros} enteras")
    if act_enteros == 0:
        print("FALLO: ninguna actualización llegó al final (sube CORTES_ACT)")
        fallos += 1
    for k in range(inicio_quitar + 1, inicio_act, 4):
        quita, lista, ver, _ = salidas[k:k + 4]
        if "CORTE" in quita[0]:
            cortados += 1
            if "3 programas instalados" not in lista[0] or "A=si B=si C=si" not in ver[0]:
                print(f"FALLO {pasos[k][1]}: tras el corte al quitar no volvió todo: {lista[0].strip()[-60:]} | {ver[0].strip()}")
                fallos += 1
        elif "0 programas instalados" not in lista[0]:
            print(f"FALLO {pasos[k][1]}: sin corte, no se quitó")
            fallos += 1
    for k in range(0, inicio_quitar, 4):
        inst, lista, tercero, ver = salidas[k:k + 4]
        cortado = "CORTE" in inst[0]
        cortados += cortado
        enteros += (not cortado) and "instalado" in inst[0]
        if "limpio=si" not in ver[0]:
            print(f"FALLO {pasos[k][1]}: no quedó limpio: {ver[0].strip()}")
            fallos += 1
        if cortado and "se ha deshecho" not in lista[0] and "CORTE al deshacer" not in lista[0]:
            print(f"FALLO {pasos[k][1]}: tras el corte no se deshizo al arrancar")
            fallos += 1
    print(f"{cortados} cortes, {enteros} instalaciones enteras")
    if enteros == 0 and N >= 16:
        print("FALLO: ninguna instalación llegó al final (sube CORTES)")
        fallos += 1
    print("TODO BIEN" if fallos == 0 else f"{fallos} FALLOS")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
