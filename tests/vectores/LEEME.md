# Vectores de prueba del formato de paquetes 2

Casos con su resultado esperado, para que todas las implementaciones (el servicio en Rust, el cliente en Dash, Paq)
digan lo mismo. Texto plano, UTF-8. Las líneas que empiezan por `#` son comentarios.

- `versiones.txt`: una comparación por línea, `A OP B` con OP `<`, `=` o `>`. `E:V` es la versión V con epoch E.
- `requisitos.txt`: bloques separados por una línea en blanco. La primera línea, `> texto`, es el valor de un campo
  `Requires` de un manifiesto con `Format: 2`; las siguientes, la forma canónica de cada elemento, en orden. Un
  elemento que no se entiende sale como `! texto` (en `Format: 2` es un error del validador).
- `requisitos_aminet.txt`: lo mismo para el texto libre de los `.readme` de siempre (sin `Format`), que se lee por
  palabras. Lo que no se entiende se calla.
- `manifiestos/x.readme` y `manifiestos/x.esperado`: un manifiesto y lo que debe salir de él (abajo).
- `resolver.txt`: casos del resolutor de dependencias (abajo).

## Forma canónica de un requisito

Las opciones de una alternativa, separadas por ` | `. Cada opción:

| Canónica | Qué es | De |
|---|---|---|
| `os N` | Versión de exec del sistema | `OS 3.1` → `os 40`, `V39` → `os 39` |
| `cpu N` | Ese procesador o mejor | `68020` → `cpu 68020` |
| `fpu`, `mmu`, `rtg`, `tcpip` | | `FPU`, `MMU`, `RTG`, `TCP/IP` |
| `chipset aga`, `chipset ecs` | | `AGA`, `ECS` |
| `mem KB`, `chip KB` | Memoria total o chip, en KB | `2MB` → `mem 2048`, `1MB chip` → `chip 1024` |
| `has NOMBRE [VERSIÓN]` | Librería, device, datatype, clase MUI o fuente, en minúsculas | `MUI 3.8` → `has muimaster.library 19` |
| `pkg NOMBRE [OP VERSIÓN]` | Un paquete | `pkg:x >= 1:2.0` → `pkg x >= 1:2.0` |
| `aminet RUTA` | El paquete de un fichero de Aminet, ruta en minúsculas | `util/libs/ReqToolsUsr.lha` |

MUI: `MUI 3.8` es `has muimaster.library 19`, `MUI 4` la 20 y `MUI 5` la 21.

## Lo que sale de un manifiesto (`.esperado`)

Una línea por dato, en este orden: `format`, `name`, `version` (siempre `epoch:versión-release`), `arch` (una por
arquitectura), `req`, `rec`, `prov`, `conf`, `repl` (una por elemento, en forma canónica), `install`, `variant`
(`DESTINO = ORIGEN ; requisitos canónicos separados por comas`), `run`, `assign`, `startup`, `config`, `perm`,
`license`, `charset`. Lo que no lleva el manifiesto no sale. La versión del sistema de `Architecture`
(`m68k-amigaos >= 3.1`) va como `req os N` la primera; si `Requires` pide otra, queda solo la más alta, en ese primer
sitio. Si el manifiesto no vale, solo líneas `error CÓDIGO
[detalle]`:

- `name-missing`, `name-invalid NOMBRE`, `version-missing`, `version-invalid VERSIÓN`
- `repeated CAMPO` (un campo repetido que no es `Variant` ni `Startup`), `format-unsupported N`, `number CAMPO VALOR`
- `requirement TEXTO` (no se entiende, con `Format: 2`; también una opción vacía y un `|` fuera de `Requires` y
  `Recommends`; el texto es el elemento entero)
- `permission NOMBRE` (permiso desconocido: falla cerrado, con o sin `Format`)
- `path RUTA` (con volumen, con `..` o que empieza por `/`, que en AmigaDOS es el cajón de arriba, en `Run`, `Assigns`, `Config`, `Variant` o el origen de `Install`)
- `short-too-long`

Los errores salen en el orden de los campos (un repetido, en el segundo); los de lo que falta (`name-missing`,
`version-missing`), al final.

## El resolutor (`resolver.txt`)

Cada caso empieza por `== título` y lleva:

- `machine: ...`: lo que tiene la máquina, en forma canónica (`os 40, cpu 68030, has muimaster.library 19`).
- `repo: NOMBRE PRIORIDAD [protected]`, y debajo sus `pkg: NOMBRE VERSIÓN[; Campo: valor]...` (campos del manifiesto; `Epoch`,
  `Release` e `Id` también).
- `installed: NOMBRE VERSIÓN REPO [explicit|dependency] [hold]` (uno por línea).
- `do: install NOMBRE[@REPO]` o `do: upgrade` (todo al día).
- `plan:` y una línea por paso, en el orden en que se hacen: `+ NOMBRE VERSIÓN REPO [#Id] (explicit|dependency|
  recommended)`, `^ NOMBRE VIEJA -> NUEVA REPO`, `- NOMBRE`. O `error CÓDIGO detalle`.
- Las versiones del plan: `[epoch:]versión`, con el epoch solo si no es 0, y `-release` cuando no es 1 (en un `^`, si
  una de las dos lo lleva, las dos). `installed:` sin release es release 1.
- `aminet RUTA` es, en el repositorio `aminet`, el paquete cuyo nombre es el del fichero sin extensión y en
  minúsculas (`util/misc/foo12.lha` es `foo12`).
- Errores: `machine REQUISITO`, `missing REQUISITO`, `conflict A B` (en forma canónica), `ambiguous NOMBRE REPO1
  REPO2` (empate de prioridad).

Las reglas que fijan los casos: la alternativa ya cumplida no instala nada; si ninguna se cumple, la primera que se
pueda instalar; entre repositorios manda la prioridad, no la versión, y un empate es un error; un repositorio protegido
no lo tapa ninguno (ni sus nombres ni lo que ofrecen); las dependencias se buscan primero en el repositorio de quien
las pide; lo instalado se actualiza desde su repositorio; entre entradas de la misma versión, la de `Rank` más bajo
que la máquina cumpla; `Replaces` solo dentro del repositorio y, en `aminet`, con el mismo `Author` y `Uploader`; las
dependencias van antes que quien las pide; en un ciclo, se instala primero lo que pide el paquete pedido.
