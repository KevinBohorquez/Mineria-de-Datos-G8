# Imagen Docker del proyecto (T05)

La imagen `pp-g8` contiene solo la cadena de herramientas (Ubuntu 24.04, igual que la CI):
CMake, g++, clang + libomp (Archer para V5), Open MPI 4.1, Python 3 con pytest, matplotlib y scipy, y git.
El código no se copia: se monta en `/work` al ejecutar, así cada corrida usa el árbol actual.

## Construir

Desde la raíz del repositorio (el contexto queda vacío gracias a `.dockerignore`):

```bash
docker build -t pp-g8 -f docker/Dockerfile .
```

## Ejecutar con el repositorio montado

La ruta del repositorio tiene espacios y tildes: siempre entre comillas.

Git Bash (`MSYS_NO_PATHCONV=1` evita que Git Bash traduzca `/work` a una ruta de Windows):

```bash
MSYS_NO_PATHCONV=1 docker run --rm -it --shm-size=1g -v "$PWD:/work" -w /work pp-g8
```

PowerShell:

```powershell
docker run --rm -it --shm-size=1g -v "${PWD}:/work" -w /work pp-g8
```

Dentro del contenedor, por ejemplo:

```bash
cmake -S . -B build/docker -DCMAKE_BUILD_TYPE=Release   # build/ está en .gitignore
cmake --build build/docker --parallel
```

Opciones necesarias según la tarea:

| Caso | Opción |
|---|---|
| MPI (memoria compartida entre rangos) | `--shm-size=1g` |
| V5 con ThreadSanitizer/Archer | `--security-opt seccomp=unconfined` |

La imagen ya define `OMPI_ALLOW_RUN_AS_ROOT=1` y `OMPI_ALLOW_RUN_AS_ROOT_CONFIRM=1` (se ejecuta como root)
y configura git con `core.autocrlf input` y `safe.directory '*'`: el clon de Windows tiene CRLF
y, sin eso, `git status` dentro del contenedor marcaría todo como modificado.

## Hola híbrido MPI + OpenMP

`hello_hibrido.cpp` inicia MPI con `MPI_THREAD_FUNNELED`, comprueba el nivel provisto y cada rango
abre una región OpenMP. El rango 0 imprime las líneas ordenadas por (rango, hilo).

Un contenedor (2 rangos × 2 hilos):

```bash
MSYS_NO_PATHCONV=1 docker run --rm --shm-size=1g -v "$PWD:/work" -w /work -e OMP_NUM_THREADS=2 pp-g8 \
  bash -c 'mpicxx -fopenmp -O2 -o /tmp/hello_hibrido docker/hello_hibrido.cpp && mpirun -np 2 --bind-to none /tmp/hello_hibrido'
```

Dos contenedores (un rango en `nodo1` y otro en `nodo2`, lanzados por ssh y comunicados por TCP):

```bash
docker compose -f docker/compose-hello.yaml run --rm nodo1
docker compose -f docker/compose-hello.yaml down -v
```

Para regenerar la evidencia de ambas variantes (con comando, fecha, imagen y commit en la cabecera):

```bash
bash docker/hello_hibrido.sh
```

Escribe `results/evidencia/t05_hello_hibrido.log` y `results/evidencia/t05_hello_dos_contenedores.log`.

> `compose-hello.yaml` es solo para T05. Las corridas E1/E2 con Compose son T22 (`compose.yaml`).
> La clave SSH se genera dentro de la imagen y solo sirve para la red interna de compose; no publiques la imagen.

## Advertencia de hardware

El equipo de medición es un Intel Core Ultra 9 275HX: 8 núcleos P + 16 núcleos E, sin SMT.
Docker Desktop corre sobre WSL2 y expone 24 vCPU; `OMP_PROC_BIND`/`OMP_PLACES` y `mpirun --bind-to`
fijan hilos a vCPU de la máquina virtual, no a núcleos físicos. Qué hilo cae en un núcleo P o E
no es controlable desde el contenedor, así que toda medición debe declarar esta limitación.
