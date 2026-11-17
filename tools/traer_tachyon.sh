#!/bin/sh
# Vuelve a copiar los módulos de red de Tachyon (MIT) a lib/tachyon/. Tachyon: ~/Projects/tachyon o $TACHYON.
set -e
T=${TACHYON:-$HOME/Projects/tachyon}
D=$(dirname "$0")/../lib/tachyon
for f in url idioma red texto entidades traza cookies http; do cp "$T/lib/$f.dash" "$D/"; done
cp "$T/LICENSE" "$D/LICENSE"
echo "Copiados de FreeMEM/tachyon $(git -C "$T" rev-parse --short HEAD) ($(git -C "$T" log -1 --format=%cs)), licencia MIT (LICENSE). No se editan aquí: se vuelven a copiar con tools/traer_tachyon.sh." > "$D/ORIGEN.txt"
