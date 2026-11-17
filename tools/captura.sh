#!/bin/sh
# Captura de la ventana de Hangar en el A1200 emulado (MUI 5), contra un servidor del PC:
#   tools/captura.sh http://127.0.0.1:47130/amiga/v1 "Boing" build/captura.png
# Compila una copia que usa ese servidor, busca el texto y elige el primero de la lista. Usa el cerrojo del emulador.
set -e
R=$(cd "$(dirname "$0")/.." && pwd)
DASH=${DASH:-$HOME/Projects/FreeMEMLang}
SERVIDOR=$1; BUSCA=$2; SALIDA=$(realpath -m "$3")
C=$R/build/captura
rm -rf "$C"; mkdir -p "$C"; cp -r "$R/src" "$R/lib" "$C/"
sed -i "s|^var api_base: String = .*|var api_base: String = \"$SERVIDOR\"|" "$C/src/api.dash"
sed -i "s|        consulta = \"n:\"|        consulta = \"b:$BUSCA\"\n        mui_set_text(w_buscar, \"$BUSCA\")|" "$C/src/hangar.dash"
python3 - "$C/src/hangar.dash" <<'PY'
import os, sys
p = sys.argv[1]; s = open(p).read()
s = s.replace("        pagina = 0\n        cargar(false)\n    end\n\n    while abierta", "        pagina = 0\n        cargar(false)\n        mui_set_value(w_lista, " + os.environ.get("INDICE", "0") + ")\n" + os.environ.get("EXTRA", "") + "    end\n\n    while abierta", 1)
open(p, "w").write(s)
PY
export DASH_KICKSTART=${DASH_KICKSTART:?"pon en DASH_KICKSTART la ROM de Kickstart 3.1"}
flock /run/user/1000/dash-emu-red.lock python3 "$DASH/tools/emu_run.py" --system "${DASH_EMU_SYS_MUI:-$HOME/.cache/dash-emu/sys31mui}" \
    --set bsdsocket_library=1 --autoclose 70 --screenshot 60 "$SALIDA" --timeout 150 "$C/src/hangar.dash"
