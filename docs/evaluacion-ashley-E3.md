# Evaluación de las tareas de Ashley (R3) y desarrollo de E3 — corte al 15/10/2026

Fuente: `cronograma/cronograma-interno.xlsx` (hoja `Tareas`), `docs/plan-desarrollo-semana-8.md` y `docs/definicion-proyecto.docx`.
Regla del plan S08: la marca «Completado» del cronograma es administrativa; solo cuenta lo que tiene archivo, prueba o medición.

## 1. Calendario

| Entregable | Revisión (jueves) | Corte interno | Situación |
| --- | --- | --- | --- |
| E3 Versión OpenMP | **15/10/2026 (hoy)** | 14/10/2026 23:59 (vencido) | Marcado 100 %, sin código ni CSV en el repositorio recibido |
| E4 MPI (T21 es de Ashley) | 22/10/2026 | 20/10/2026 23:59 | No iniciado; depende de T19 y T20 (David) |

## 2. Tareas de Ashley como responsable

Estado «repo recibido» = lo que contenía el zip (cada archivo reservado era solo un comentario).
Estado «tras este trabajo» = lo que se verificó en el entorno de desarrollo (1 núcleo, GCC 13.3, Clang 18, CMake 4.4).

| Tarea | Cronograma | Repo recibido | Tras este trabajo | Falta para dar la evidencia por válida |
| --- | --- | --- | --- | --- |
| T04 CMake y CI | Completado | Sin evidencia (solo comentarios; el CI era `ci.yml.example`, que no se ejecuta) | `CMakeLists.txt`, `.github/workflows/ci.yml`, `tests/smoke/smoke.cpp`. Los tres comandos del criterio pasan en un árbol limpio (CTest: 2/2) | Enlace a una corrida verde en GitHub Actions |
| T11 Escenario secuencial | Completado | Sin evidencia | Philox4x32-10 (coincide con los 3 vectores oficiales de Random123), Markov + gamma Marsaglia–Tsang, Lindley. Compila con `-Wall -Wextra` sin avisos; N=10⁶ con semilla fija da `k=106165` en dos corridas | Parámetros calibrados (T10); ahora usa parámetros sintéticos |
| T12 Wilson, histograma, CSV | Completado | Sin evidencia | Wilson (k=0, k=N, n=0 probados), 512 clases, CSV con ida y vuelta probada | Contraste con el contrato T02 (`docs/contratos.md` no existe) |
| **T15 Backend OpenMP** | Completado | Sin evidencia | `pp_openmp` con `reduction(+:k,n)` y `reduction(+:hist[:512])`, índice global `c*N+j`, `schedule(runtime)` | Ejecutarlo en el CI y en la máquina de referencia |
| T21 MPI V1/V3/V4 + barrido | No iniciado | — | No es parte de E3 | Esperar T19/T20 |
| T37, T48 | No iniciado | — | Fuera del alcance actual | S12 y S14 |

## 3. Entregable E3 (T15–T18) frente a su criterio de aceptación

Criterio del cronograma: «V1/V5 y CSV con tiempo, speedup y eficiencia para 2/4/8/16 hilos; identificar sobresuscripción».

| Pieza | Responsable | Estado | Detalle |
| --- | --- | --- | --- |
| T15 código OpenMP | Ashley | **Hecho** | Ver sección 2 |
| T17 V1 | Lita (revisa Ashley) | **Hecho, pendiente de revisión** | `tests/integration/test_openmp_equivalencia.py`: serial vs OpenMP con 1/2/4/8 hilos × `static`, `dynamic`, `dynamic:7`, `guided`, N=5003 (no divisible), `config_id` 0/1/12999; incluye V3 (Σ=N) y V4. 24 pruebas pasan |
| T17 V5 | Lita (revisa Ashley) | **Hecho, pendiente de revisión** | Archer (Clang 18 + libomp) con 2/4/8/16 hilos: **0 reportes**, y un control negativo (carrera deliberada) sí es detectado |
| T16 CSV 2/4/8/16 hilos | Lita | **Script listo, medición pendiente** | `scripts/bench/medir_openmp.py`. Debe correrse en la máquina de referencia con build Release |
| T18 gráficos | Rhamses | **Script listo, gráficos pendientes** | `scripts/bench/graficar_openmp.py` (`--plantilla` genera ejes rotulados «PENDIENTE», sin cifras) |

No se adjunta ningún CSV ni gráfico de rendimiento: el entorno donde se desarrolló tiene **un solo núcleo**, así que cualquier speedup medido allí es 1 y no representa a la máquina del equipo. El pipeline se probó de extremo a extremo con N pequeño y esos resultados se descartaron.

## 4. Hallazgos que afectan al equipo

1. **E3 figura 100 % sin evidencia.** Hoy es el jueves de revisión de E3 y el corte ya pasó. Hasta correr T16/T18 en la máquina de referencia, E3 solo cumple V1/V5 y el código.
2. **`schedule(runtime)` sin `OMP_SCHEDULE` usa `dynamic,1` en GCC/libgomp**, no `static`. Todos los barridos deben fijar el schedule de forma explícita; `pp_openmp` imprime y guarda el schedule efectivo en el CSV y `medir_openmp.py` siempre lo pasa.
3. **Sobresuscripción esperada.** La definición dimensiona 3 equipos de 6 núcleos. En un solo equipo de 6 núcleos físicos, 8 y 16 hilos quedarán sobresuscritos y deben analizarse aparte. El script marca `sobresuscrito` (hilos > núcleos físicos) y `excede_logicos`; el gráfico los dibuja con marcador hueco.
4. **ThreadSanitizer con GCC no sirve para V5.** Con libgomp produce falsos positivos (libgomp no está instrumentado). V5 se hace con Clang + libomp (Archer); el CI instala `clang` y `libomp-dev`.
5. **Contrato T02 ausente.** `docs/contratos.md` no existe y `config/ejemplo.yaml` es un comentario. Los nombres de opciones y columnas CSV de esta implementación son provisionales; David debe confirmarlos. Para no pisar su archivo se creó `config/sintetico.yaml`.
6. **Rutas de evidencia incoherentes.** El cronograma pide `results/bench/*.csv`, `results/analysis/*` y `results/official/*`, pero el README y la estructura solo prevén `results/raw|processed|figures`. Además `.gitignore` excluye `results/figures/*` y `results/processed/*`, de modo que las figuras de T18 (evidencia de E3) no se versionarían. Se usó `results/bench/` para los CSV; falta decidir qué carpeta es la oficial y ajustar `.gitignore`.
7. **Philox propio.** La definición y T05 prevén Random123. Se implementó Philox4x32-10 sin dependencias y se verificó con los vectores oficiales (`tests/smoke`), de modo que puede sustituirse por Random123 sin cambiar resultados. Para EXT1, Lita deberá marcar las funciones `__host__ __device__`.
8. **Tareas que Ashley revisa y siguen sin entrega verificable:** T10 (parámetros, Angela), T13 (V6/V7, Lita), T14 (T1, Miguel), T03 (no hay plantilla de PR ni reglas de ramas en el README). No se pueden aprobar sin evidencia.

## 5. Qué se necesita para cerrar E3

1. **Máquina de referencia** (con ≥ 8 núcleos físicos, ideal 16) para ejecutar T16 con build Release; si no existe, aceptar y documentar los puntos sobresuscritos.
2. **Parámetros calibrados de T10** (`p01, p11, alfa, theta` por estación y régimen) para sustituir los sintéticos, o confirmar que E3 se mide con los sintéticos.
3. **Contrato T02** de David, para alinear CLI y columnas del CSV.
4. **T1 de Miguel (T14)**: si llega en otro formato, adaptar `--t1-csv`; si no, se usa la fila serial que mide T16 con el mismo binario.
5. **Subir a GitHub** para obtener la primera corrida verde del CI y enlazarla como evidencia de T04/T17.
6. Decisión sobre la carpeta oficial de resultados (punto 6 de la sección 4).

## 6. Cómo reproducir

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Debug && cmake --build build --parallel
ctest --test-dir build --output-on-failure            # smoke + V1
python3 -m pytest -v tests/concurrency                # V5 (necesita clang y libomp-dev)

# Una corrida
build/src/backends/openmp/pp_openmp --config config/sintetico.yaml --n 1000000 --hilos 4 --schedule static

# Medición T16 (máquina de referencia, build Release)
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release && cmake --build build --parallel
python3 scripts/bench/medir_openmp.py --n 20000000 --hilos 2,4,8,16 --schedules static,dynamic,64
# Gráficos T18
python3 scripts/bench/graficar_openmp.py --svg
```
