# Hangar — el cliente para el Amiga

*English below.*

Hangar busca programas, juegos y demos, enseña su ficha y su captura, los instala y los tiene al día, todo desde el
propio Amiga. El catálogo está en https://hangar.freemem.space: el software de Aminet y los programas que publican
sus autores.

Este repositorio es el programa del Amiga, escrito en [Dash](https://github.com/FreeMEM/dash). El servicio de
hangar.freemem.space no está aquí.

## Qué hace

- Instala con todo lo que necesita cada programa, de una vez, y en una transacción: si algo falla o se corta, todo
  vuelve a como estaba. Deshacer la última también deja todo como antes.
- Comprueba las firmas (Ed25519) de lo que responde el catálogo y el SHA-256 de lo que baja. Si un sitio de descarga
  no responde o da otra cosa, prueba el siguiente.
- Apunta cada fichero que instala: sabe qué es de quién, avisa si otro programa lo necesita al quitar, y deja los
  ajustes que hayas cambiado.
- Lanza el `Install` de un programa con el Installer si lo trae, y apunta todo lo que copia.
- Mira el disco: reconoce lo que instalaste a mano, te avisa de versiones nuevas y lo apunta si quieres.
- Se entera si mueves a mano el cajón de un programa.
- Retener una versión, volver a la anterior, verificar lo instalado y repararlo.
- Descomprime los `.lha` él solo: no hace falta LhA.

Necesita AmigaOS 3.0 o mejor, un 68020 o mejor, MUI 3.8 o 5 y una pila TCP/IP (`bsdsocket.library`).

## Compilar

Con [Dash](https://github.com/FreeMEM/dash) y su compilador de C para 68k (`m68k-amigaos-gcc`):

```bash
DASH=~/dash
$DASH/dash --gcc --cpu 68020 src/hangar.dash -o build/Hangar   # el programa
DASH=$DASH sh tools/paquete.sh                                 # build/Hangar.lha, como se reparte
```

## Pruebas

Corren en un Amiga emulado (FS-UAE), contra un servidor falso (`tests/servers/falso.py`). Hacen falta una ROM de
Kickstart 3.1 y los ficheros de un Workbench 3.1 con MUI:

```bash
export DASH_KICKSTART=/ruta/kick31.rom DASH_EMU_SYS=/ruta/sys31 DASH_EMU_SYS_MUI=/ruta/sys31mui
export HANGAR_DASH_OPCIONES="--gcc --cpu 68020"
python3 tests/run.py       # las de cada pieza
python3 tests/punta.py     # instalar, quitar, deshacer y reparar, de punta a punta
python3 tests/punta2.py    # el formato 2: planes, firmas, versiones, sitios de descarga
python3 tests/cortes.py    # se corta en cada paso de una instalación y todo vuelve a como estaba
```

`tests/coffin/` es un banco para probar la ventana en Amiberry.

## Licencia

GPL-3.0-or-later (el fichero `LICENSE`). `lib/tachyon/` viene de [Tachyon](https://github.com/FreeMEM/tachyon) y es
MIT (`lib/tachyon/LICENSE`).

---

# Hangar — the Amiga client

Hangar finds programs, games and demos, shows their details and screenshot, installs them and keeps them up to date,
all from the Amiga itself. The catalogue lives at https://hangar.freemem.space: the software on Aminet and the
programs their authors publish there.

This repository is the Amiga program, written in [Dash](https://github.com/FreeMEM/dash). The hangar.freemem.space
service is not part of it. The program speaks Spanish for now.

What it does: installs each program with everything it needs, in one transaction (if something fails or is cut, it
all goes back as it was; Undo does the same); checks the Ed25519 signatures of the catalogue's answers and the
SHA-256 of every download, and tries the next download site if one fails; records every file it installs (who owns
what, what another program still needs, the settings you changed); runs a program's own `Install` script with the
Installer and records what it copies; scans the disk to recognise what you installed by hand; notices when you move
a program's drawer; holds, rolls back, verifies and repairs. It unpacks `.lha` files itself.

It needs AmigaOS 3.0 or later, a 68020 or better, MUI 3.8 or 5 and a TCP/IP stack (`bsdsocket.library`).

Build and test: see the commands above. Licence: GPL-3.0-or-later; `lib/tachyon/` is MIT.
