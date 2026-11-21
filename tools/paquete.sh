#!/bin/sh
# El paquete de Hangar para el Amiga: build/Hangar.lha con el programa, sus iconos, sus catálogos, el LEEME (Latin-1) y las
# licencias de lo que lleva dentro (Dash y Tachyon, MIT). LHA -lh5- con tools/lha.py (de Tachyon).
#
#   tools/paquete.sh
set -e
R=$(cd "$(dirname "$0")/.." && pwd)
DASH=${DASH:-$HOME/Projects/FreeMEMLang}
B=$R/build/paquete
rm -rf "$B"
mkdir -p "$B/Hangar/Licencias"
# por C y para 68020 (Hangar ya lo pide): la firma Ed25519 tarda 8 s en vez de 23 con el runtime de 68000
"$DASH/dash" --gcc --cpu 68020 "$R/src/hangar.dash" -o "$B/Hangar/Hangar"
iconv -f UTF-8 -t LATIN1 "$R/paquete/LEEME" > "$B/Hangar/LEEME"
python3 "$R/tools/iconos_wb.py" "$B"
# los catálogos (catalogos/*.ct): Catalogs/<idioma>/Hangar.catalog junto al programa; sale en el idioma del sistema
(cd "$B/Hangar" && for ct in "$R"/catalogos/*.ct; do python3 "$DASH/tools/catalogo.py" catalog "$ct" >/dev/null; done)
cp "$DASH/LICENSE" "$B/Hangar/Licencias/Dash"
cp "$R/lib/tachyon/LICENSE" "$B/Hangar/Licencias/Tachyon"
cd "$B"
rm -f "$R/build/Hangar.lha"
# el manifiesto del formato de paquetes 2 en la raíz del .lha, y al lado
iconv -f UTF-8 -t LATIN1 "$R/paquete/Hangar.readme" > "$B/Hangar.readme"
cp "$B/Hangar.readme" "$R/build/Hangar.readme"
python3 "$R/tools/lha.py" "$R/build/Hangar.lha" Hangar Hangar.info Hangar.readme
lha -t "$R/build/Hangar.lha" >/dev/null
ls -l "$R/build/Hangar.lha"
