#!/usr/bin/env python3
"""Hangar en Aminet (util/misc): build/aminet/Hangar.lha y Hangar.readme, y con --subir por FTP a main.aminet.net/new.
Usa tools/aminet.py de Tachyon (~/Projects/tachyon: comprobaciones de Aminet, remitente). Sube build/Hangar.lha tal cual:
que sea el publicado (curl http://hangar.freemem.space/cliente/Hangar.lha). Como mucho una subida por semana.

    python3 tools/aminet.py 0.14.6 [--subir]
"""
import sys, shutil, ftplib
from pathlib import Path
sys.path.insert(0, str(Path.home() / "Projects/tachyon/tools"))
import aminet as m
perfil = {
    "nombre": "Hangar",
    "cabecera": [
        ("Short", "Find, install and update Amiga software"),
        ("Author", "FreeMEM"),
        ("Uploader", m.SUBIDOR),
        ("Type", "util/misc"),
        ("Version", None),
        ("Requires", "68020, MUI 3.8 or 5, TCP/IP stack"),
        ("Architecture", "m68k-amigaos >= 3.0.0"),
        ("Distribution", "Aminet"),
        ("Kurz", "Amiga-Software suchen, installieren"),
    ],
    "descripcion": """\
Hangar finds programs, games and demos, shows their details and screenshot,
installs them and keeps them up to date, all from the Amiga itself. Its
catalogue (https://hangar.freemem.space) has the software on Aminet and the
programs their authors publish there.

What it does:
- Installs each program with everything it needs, all at once and in one
  transaction: if something fails or is cut halfway, everything goes back
  as it was. Undo does the same for the last change.
- Checks the Ed25519 signatures of the catalogue's answers and the SHA-256
  of every download; if a download site fails, it tries the next one.
- Records every file it installs: it knows what belongs to what, warns you
  when another program still needs something, and keeps the settings you
  changed.
- Runs a program's own Installer script if it has one, and records what it
  copies, so it can be removed completely.
- Scans your disk, recognises what you installed by hand and tells you
  about new versions.
- Notices when you move a program's drawer by hand.
- Holds a version, goes back to the previous one, verifies what is
  installed and repairs it.
- Unpacks .lha archives itself: no LhA needed.

The program speaks Spanish for now.

Requirements:
- AmigaOS 3.0 or later, a 68020 or better.
- MUI 3.8 or 5.
- A TCP/IP stack (bsdsocket.library): Roadshow, Miami, AmiTCP or your
  emulator's.

Installation: unpack the archive anywhere and double-click Hangar. It keeps
itself up to date from its own catalogue.

Videos: https://youtu.be/mKkdU85AGAQ (English)
        https://youtu.be/--DT377pLzg (Spanish)
Website: https://hangar.freemem.space
""",
}
ver = sys.argv[1]
lha = Path.home() / "Proyectos/hangar/cliente/build/Hangar.lha"
texto = m.readme(perfil, ver, "")
errores = m.comprobar(perfil, texto, lha)
if errores:
    sys.exit("No vale para Aminet:\n  " + "\n  ".join(errores))
dest = Path.home() / "Proyectos/hangar/cliente/build/aminet"
(dest / "Hangar.readme").write_bytes(texto.encode("latin-1"))
shutil.copyfile(lha, dest / "Hangar.lha")
print(texto)
print(dest, (dest / "Hangar.lha").stat().st_size)
if "--subir" in sys.argv:
    with ftplib.FTP(m.SERVIDOR, timeout=120) as ftp:
        ftp.login("anonymous", m.SUBIDOR.split()[0])
        ftp.cwd("new")
        for f in ("Hangar.lha", "Hangar.readme"):
            with open(dest / f, "rb") as h:
                print(ftp.storbinary(f"STOR {f}", h), f)
