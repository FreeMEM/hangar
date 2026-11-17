#!/usr/bin/env python3
"""Trae los vectores de prueba del formato de paquetes 2 (del servicio) a tests/vectores y genera
tests/test_vectores.dash, que los pasa en el Amiga emulado: comparación de versiones y requisitos en forma canónica.

    python3 tools/vectores.py [CAJÓN_DE_LOS_VECTORES]     # por defecto ../servicio/docs/formato/vectores
"""
import shutil
import sys
from pathlib import Path

R = Path(__file__).resolve().parent.parent
ORIGEN = Path(sys.argv[1]) if len(sys.argv) > 1 else R.parent / "servicio" / "docs" / "formato" / "vectores"
DESTINO = R / "tests" / "vectores"


def texto_dash(s):
    return '"' + s.replace("\\", "\\\\").replace('"', '\\"').replace("#{", "#\\{") + '"'


def main():
    DESTINO.mkdir(exist_ok=True)
    for f in ("versiones.txt", "requisitos.txt", "resolver.txt", "LEEME.md"):
        if ORIGEN.exists():
            shutil.copy(ORIGEN / f, DESTINO / f)
    versiones = []
    for l in (DESTINO / "versiones.txt").read_text(encoding="utf-8").splitlines():
        if not l.strip() or l.startswith("#"):
            continue
        for op in (" < ", " = ", " > "):
            if op in l:
                a, b = l.split(op, 1)
                versiones.append((a, op.strip(), b))
                break
    bloques = []
    for l in (DESTINO / "requisitos.txt").read_text(encoding="utf-8").splitlines():
        if l.startswith("#"):
            continue
        if l.startswith("> "):
            bloques.append((l[2:], []))
        elif l.strip():
            bloques[-1][1].append(l)
    o = []
    o.append("# Test generado por tools/vectores.py (no editar): los vectores del formato de paquetes 2 (tests/vectores,")
    o.append("# copiados del servicio): comparación de versiones con epoch y requisitos en forma canónica.")
    o.append(f"# expect-out: versiones {len(versiones)}/{len(versiones)}")
    o.append(f"# expect-out: requisitos {len(bloques)}/{len(bloques)}")
    o.append('import "../src/formato.dash"')
    o.append("")
    o.append("func signo(k: Int) -> String")
    o.append('    if k < 0')
    o.append('        return "<"')
    o.append('    elif k > 0')
    o.append('        return ">"')
    o.append("    end")
    o.append('    return "="')
    o.append("end")
    o.append("")
    o.append("func inverso(s: String) -> String")
    o.append('    if s == "<"')
    o.append('        return ">"')
    o.append('    elif s == ">"')
    o.append('        return "<"')
    o.append("    end")
    o.append("    return s")
    o.append("end")
    o.append("")
    o.append("Main")
    o.append("    bien = 0")
    for a, op, b in versiones:
        o.append(f"    s = signo(version_comparar_e({texto_dash(a)}, {texto_dash(b)}))")
        o.append(f"    s2 = signo(version_comparar_e({texto_dash(b)}, {texto_dash(a)}))")
        o.append(f'    if s == "{op}" and s2 == inverso("{op}")')
        o.append("        bien = bien + 1")
        o.append("    else")
        o.append(f'        Print "MAL " + {texto_dash(a + " " + op + " " + b)} + " sale " + s')
        o.append("    end")
    o.append(f'    Print "versiones " + str_from_int(bien, 10) + "/{len(versiones)}"')
    o.append("    bien = 0")
    for texto, esperado in bloques:
        o.append(f"    sale = \"\"")
        o.append(f"    for a in formato_lista({texto_dash(texto)}, true, false)")
        o.append('        sale = sale + formato_canonica_alt(a) + "\\n"')
        o.append("    end")
        esp = "".join(e + "\n" for e in esperado)
        o.append(f"    if sale == {texto_dash(esp).replace(chr(10), chr(92) + 'n')}")
        o.append("        bien = bien + 1")
        o.append("    else")
        o.append(f'        Print "MAL > " + {texto_dash(texto)}')
        o.append('        Print sale')
        o.append("    end")
    o.append(f'    Print "requisitos " + str_from_int(bien, 10) + "/{len(bloques)}"')
    o.append("end")
    (R / "tests" / "test_vectores.dash").write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"tests/test_vectores.dash: {len(versiones)} versiones, {len(bloques)} bloques de requisitos")
    resolutor()


def resolutor():
    casos = []
    c = None
    en_plan = False
    for l in (DESTINO / "resolver.txt").read_text(encoding="utf-8").splitlines():
        if l.startswith("#"):
            continue
        if l.startswith("== "):
            c = {"titulo": l[3:], "maquina": "", "repos": [], "instalados": [], "orden": "", "plan": []}
            casos.append(c)
            en_plan = False
            continue
        if not l.strip():
            en_plan = False
            continue
        if en_plan:
            c["plan"].append(l.strip())
            continue
        k, _, v = l.partition(":")
        v = v.strip()
        if k == "machine":
            c["maquina"] = v
        elif k == "repo":
            w = v.split()
            c["repos"].append([w[0], int(w[1]), "protected" in w[2:], []])
        elif k == "pkg":
            partes = [x.strip() for x in v.split(";")]
            nombre, version = partes[0].split()
            campos = f"Name: {nombre}\nVersion: {version}\n" + "".join(x + "\n" for x in partes[1:])
            c["repos"][-1][3].append(campos)
        elif k == "installed":
            c["instalados"].append(v.split())
        elif k == "do":
            c["orden"] = v
        elif k == "plan":
            en_plan = True
    o = []
    o.append("# Test generado por tools/vectores.py (no editar): los casos del resolutor del formato 2 (tests/vectores/")
    o.append("# resolver.txt, copiados del servicio) con src/resolutor.dash.")
    o.append(f"# expect-out: resolutor {len(casos)}/{len(casos)}")
    o.append('import "../src/resolutor.dash"')
    o.append("")
    o.append("func meter(repo: String, campos: String)")
    o.append('    for e in formato_entradas("X\\n\\n" + campos)'.replace("\\\\", "\\"))
    o.append("        resolutor_meter(repo, e)")
    o.append("    end")
    o.append("end")
    o.append("")
    o.append("func comprobar(titulo: String, esperado: String) -> Int")
    o.append('    sale = ""')
    o.append("    for l in resolutor_lineas()")
    o.append('        sale = sale + l + "\\n"'.replace("\\\\", "\\"))
    o.append("    end")
    o.append("    if sale == esperado")
    o.append("        return 1")
    o.append("    end")
    o.append('    Print "MAL " + titulo')
    o.append("    Print sale")
    o.append("    return 0")
    o.append("end")
    o.append("")
    o.append("Main")
    o.append("    bien = 0")
    for c in casos:
        m = {"os": 0, "cpu": 0, "fpu": "false", "mmu": "false", "rtg": "false", "tcpip": "false", "chipset": "", "mem": 0, "chip": 0}
        libs = []
        for el in c["maquina"].split(","):
            w = el.split()
            if not w:
                continue
            if w[0] in ("os", "cpu", "mem", "chip"):
                m[w[0]] = int(w[1])
            elif w[0] == "has":
                libs.append(" ".join(w[1:]))
            elif w[0] == "chipset":
                m["chipset"] = w[1]
            else:
                m[w[0]] = "true"
        o.append("    var libs: [String] = []" if c is casos[0] else "    libs = []")
        for l in libs:
            o.append(f"    libs.push({texto_dash(l)})")
        o.append(f'    resolutor_empezar(Maquina({m["os"]}, {m["cpu"]}, {m["fpu"]}, {m["mmu"]}, {m["rtg"]}, {m["tcpip"]}, "{m["chipset"]}", {m["mem"]}, {m["chip"]}, libs))')
        for nombre, prio, prot, entradas in c["repos"]:
            o.append(f'    resolutor_repo("{nombre}", {prio}, {"true" if prot else "false"})')
            for e in entradas:
                o.append(f"    meter(\"{nombre}\", {texto_dash(e).replace(chr(10), chr(92) + 'n')})")
        for w in c["instalados"]:
            nombre, version, repo = w[0], w[1], w[2]
            motivo = w[3] if len(w) > 3 else "explicit"
            epoch = 0
            if ":" in version:
                epoch, version = version.split(":", 1)
            o.append(f'    resolutor_instalado(PkgInstalado("{nombre}", {epoch}, "{version}", 1, "{repo}", "{motivo}", {"true" if "hold" in w[4:] else "false"}))')
        orden = c["orden"].split()
        if orden[0] == "install":
            o.append(f'    resolutor_instalar("{orden[1]}")')
        else:
            o.append("    resolutor_actualizar()")
        esp = "".join(l + "\\n" for l in c["plan"]).replace("\\\\", "\\")
        o.append(f'    bien = bien + comprobar({texto_dash(c["titulo"])}, "{esp}")')
    o.append(f'    Print "resolutor " + str_from_int(bien, 10) + "/{len(casos)}"')
    o.append("end")
    (R / "tests" / "test_resolutor.dash").write_text("\n".join(o) + "\n", encoding="utf-8")
    print(f"tests/test_resolutor.dash: {len(casos)} casos")


if __name__ == "__main__":
    main()
