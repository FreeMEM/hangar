#!/usr/bin/env python3
"""Los iconos de Workbench del paquete de Hangar (copiado de tools/iconos_wb.py de Tachyon, MIT): ficheros .info clásicos (DiskObject, 4 colores del Workbench:
gris, negro, blanco, azul), que lee cualquier Workbench de 3.0 a 3.2.

    python3 tools/iconos_wb.py DIR        # escribe en DIR los .info del paquete (tools/paquete.sh lo usa)

En DIR deja: Hangar.info (el cajón, junto al cajón Hangar/) y, en DIR/Hangar/, Hangar.info (el programa) y
LEEME.info (se abre con MultiView)."""

import struct
import sys
from pathlib import Path

GRIS, NEGRO, BLANCO, AZUL = 0, 1, 2, 3
WBDISK, WBDRAWER, WBTOOL, WBPROJECT = 1, 2, 3, 4
SIN_SITIO = 0x80000000


class Lienzo:
    def __init__(self, ancho, alto):
        self.ancho, self.alto = ancho, alto
        self.p = [[GRIS] * ancho for _ in range(alto)]

    def punto(self, x, y, c):
        if 0 <= x < self.ancho and 0 <= y < self.alto:
            self.p[y][x] = c

    def rect(self, x0, y0, x1, y1, c):
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1):
                self.punto(x, y, c)

    def marco(self, x0, y0, x1, y1, c):
        for x in range(x0, x1 + 1):
            self.punto(x, y0, c)
            self.punto(x, y1, c)
        for y in range(y0, y1 + 1):
            self.punto(x0, y, c)
            self.punto(x1, y, c)

    def linea(self, x0, y0, x1, y1, c):
        n = max(abs(x1 - x0), abs(y1 - y0), 1)
        for i in range(n + 1):
            self.punto(round(x0 + (x1 - x0) * i / n), round(y0 + (y1 - y0) * i / n), c)

    def elipse(self, cx, cy, rx, ry, c, llena=False):
        for y in range(cy - ry, cy + ry + 1):
            for x in range(cx - rx, cx + rx + 1):
                d = ((x - cx) / rx) ** 2 + ((y - cy) / ry) ** 2
                if (llena and d <= 1.0) or (not llena and 0.75 <= d <= 1.15):
                    self.punto(x, y, c)

    def planos(self):
        """Los dos planos de bits (fila a fila, palabras de 16 bits)"""
        palabras = (self.ancho + 15) // 16
        r = b""
        for plano in range(2):
            for fila in self.p:
                bits = 0
                for x, c in enumerate(fila):
                    if (c >> plano) & 1:
                        bits |= 1 << (palabras * 16 - 1 - x)
                r += bits.to_bytes(palabras * 2, "big")
        return r


def cajon():
    l = Lienzo(40, 20)
    l.rect(2, 4, 37, 18, BLANCO)
    l.marco(2, 4, 37, 18, NEGRO)
    l.rect(4, 6, 35, 9, AZUL)
    l.rect(4, 12, 35, 16, AZUL)
    l.rect(16, 7, 23, 8, NEGRO)
    l.rect(16, 13, 23, 14, NEGRO)
    l.linea(2, 4, 6, 1, NEGRO)
    l.linea(37, 4, 33, 1, NEGRO)
    l.linea(6, 1, 33, 1, NEGRO)
    return l


def hangar():
    """El icono de Hangar: la nave del hangar (bóveda azul) con la puerta abierta y un disquete dentro"""
    l = Lienzo(48, 24)
    # bóveda
    for y in range(2, 22):
        for x in range(4, 44):
            d = ((x - 23.5) / 20.0) ** 2 + ((y - 21.5) / 19.5) ** 2
            if d <= 1.0:
                l.punto(x, y, AZUL)
            if 0.88 <= d <= 1.05:
                l.punto(x, y, NEGRO)
    # nervios de la bóveda
    for x in (12, 35):
        for y in range(6, 21):
            if l.p[y][x] == AZUL:
                l.punto(x, y, NEGRO)
    # suelo
    l.linea(1, 21, 46, 21, NEGRO)
    # puerta abierta
    l.rect(16, 10, 31, 20, BLANCO)
    l.marco(16, 10, 31, 20, NEGRO)
    # un disquete dentro
    l.rect(20, 13, 27, 19, NEGRO)
    l.rect(22, 13, 25, 15, BLANCO)
    l.rect(21, 17, 26, 19, AZUL)
    return l


def documento():
    l = Lienzo(30, 22)
    l.rect(4, 1, 25, 20, BLANCO)
    l.marco(4, 1, 25, 20, NEGRO)
    l.rect(20, 1, 25, 6, GRIS)
    l.linea(20, 1, 25, 6, NEGRO)
    l.linea(20, 1, 20, 6, NEGRO)
    l.linea(20, 6, 25, 6, NEGRO)
    for y in (8, 11, 14, 17):
        l.linea(7, y, 22, y, AZUL)
    return l


def instalador():
    l = Lienzo(34, 22)
    l.rect(4, 11, 29, 20, AZUL)
    l.marco(4, 11, 29, 20, NEGRO)
    l.linea(4, 11, 9, 7, NEGRO)
    l.linea(29, 11, 24, 7, NEGRO)
    l.rect(14, 0, 19, 7, BLANCO)
    l.marco(14, 0, 19, 7, NEGRO)
    for i in range(6):
        l.linea(11 + i, 8 + i, 22 - i, 8 + i, BLANCO)
    l.linea(10, 8, 16, 14, NEGRO)
    l.linea(23, 8, 17, 14, NEGRO)
    return l


def texto_bcpl(s):
    b = s.encode("latin-1") + b"\0"
    return struct.pack(">I", len(b)) + b


def info(lienzo, tipo, herramienta=None, tooltypes=None, pila=0):
    w, h = lienzo.ancho, lienzo.alto
    gadget = struct.pack(">IhhhhHHHIIIIIHI", 0, 0, 0, w, h + 1, 0x0004, 0x0003, 0x0001,
                         1, 0, 0, 0, 0, 0, 1)
    cajonero = tipo in (WBDISK, WBDRAWER)
    disk = struct.pack(">HH", 0xE310, 1) + gadget + struct.pack(
        ">BBIIIIIII", tipo, 0, 1 if herramienta else 0, 1 if tooltypes else 0, SIN_SITIO, SIN_SITIO,
        1 if cajonero else 0, 0, pila)
    r = disk
    if cajonero:
        # NewWindow (48) + CurrentX/Y del cajón abierto
        r += struct.pack(">hhhhbbIIIIIIIhhHHH", 60, 40, 360, 140, -1, -1, 0, 0, 0, 0, 0, 0, 0,
                         90, 40, 0xFFFF, 0xFFFF, 1) + struct.pack(">ii", 0, 0)
    r += struct.pack(">hhhhhIBBI", 0, 0, w, h, 2, 1, 3, 0, 0) + lienzo.planos()
    if herramienta:
        r += texto_bcpl(herramienta)
    if tooltypes:
        r += struct.pack(">I", (len(tooltypes) + 1) * 4)
        for t in tooltypes:
            r += texto_bcpl(t)
    if cajonero:
        r += struct.pack(">IH", 0, 0)       # DrawerData de 2.x: dd_Flags y dd_ViewModes (por iconos)
    return r


def main():
    dest = Path(sys.argv[1] if len(sys.argv) > 1 else "build/paquete")
    (dest / "Hangar").mkdir(parents=True, exist_ok=True)
    (dest / "Hangar.info").write_bytes(info(cajon(), WBDRAWER))
    (dest / "Hangar" / "Hangar.info").write_bytes(info(hangar(), WBTOOL, pila=65536))
    (dest / "Hangar" / "LEEME.info").write_bytes(info(documento(), WBPROJECT, herramienta="SYS:Utilities/MultiView"))


if __name__ == "__main__":
    main()
