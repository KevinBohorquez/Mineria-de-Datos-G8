# Simulación paralela del riesgo de inundación urbana

Proyecto 8 del curso Programación Concurrente y Paralela, UNMSM 2026-II. El simulador **aún no tiene implementación ni resultados de ejecución**. Este repositorio contiene la estructura, archivos reservados por tarea, la definición ajustada, los cronogramas y los planes de desarrollo para seis integrantes.

## Propósito

Estimar mediante Monte Carlo la probabilidad de que el agua acumulada supere un umbral durante una temporada de lluvias. El diseño usa precipitación diaria calibrada con series SENAMHI, ocurrencia de lluvia con cadena de Markov, montos gamma y un balance hídrico simplificado. Se compararán versiones secuencial, OpenMP, MPI y MPI + OpenMP. CUDA y un nodo GPU son extensiones condicionadas a la decisión de la semana 10.

La definición y los criterios de aceptación están en [docs/definicion-proyecto.docx](docs/definicion-proyecto.docx). El estado de las tareas se registra en [cronograma/cronograma-interno.xlsx](cronograma/cronograma-interno.xlsx). El resumen de entregables está en [cronograma/cronograma-presentacion.xlsx](cronograma/cronograma-presentacion.xlsx).

La [revisión interna de la definición](docs/acta-revision-definicion.md) registra las decisiones vigentes y las aprobaciones individuales que aún faltan para acreditar T01.

La [validación del tablero T07](scripts/validar_cronograma.py) comprueba los 53 IDs y sus campos obligatorios. El [protocolo de gráficos OpenMP T18](docs/protocolo-graficos-openmp.md) define las entradas y salidas del generador; los resultados se crearán cuando existan las mediciones T14 y T16.

## Equipo

| Rol | Integrante | Responsabilidad principal |
| --- | --- | --- |
| R1 | David | Integración, MPI, coordinación y entregas |
| R2 | Angela | Series SENAMHI, calibración y análisis de riesgo |
| R3 | Ashley | Núcleo secuencial, OpenMP, pruebas y CI |
| R4 | Lita | Pruebas de correctitud, barridos de recursos y CUDA si se activa |
| R5 | Miguel | Docker, clúster, automatización y mediciones |
| R6 | Rhamses | Documentación, gráficos, informe y exposición |

Los roles se asignaron en el orden en que se proporcionaron los nombres. Cualquier cambio de responsables debe reflejarse en ambos cronogramas y en los planes.

## Plan de trabajo

- [Plan de desarrollo hasta la semana 8](docs/plan-desarrollo-semana-8.md): definición, datos, entorno, referencia secuencial y OpenMP.
- [Plan de desarrollo hasta la semana 15](docs/plan-desarrollo-semana-15.md): MPI, híbrido, campañas de rendimiento y científicas, informe y exposición. CUDA se ejecuta solo si se activa la extensión.

Las rutas reservadas para programar y los formatos de cada entrega están en las columnas **V–W** de la hoja `Tareas` del [cronograma interno](cronograma/cronograma-interno.xlsx).

**Estado de seguimiento al 12/10/2026:** el equipo pidió marcar E1–E3 y sus tareas como completados en los cronogramas. Esa marca administrativa no acredita código, datos, pruebas ni mediciones; esas evidencias siguen pendientes de adjuntar. Las fechas académicas originales se conservan.

## Estructura prevista

| Ruta | Qué deberá contener cuando empiece el desarrollo |
| --- | --- |
| `docs/` | Definición vigente, planes, decisiones técnicas, bitácora y protocolo experimental. |
| `cronograma/` | Cronograma interno con tareas y estado, y cronograma resumido para presentar. |
| `include/` | Interfaces públicas de los tipos de simulación, parámetros, RNG y acumuladores. |
| `src/core/` | Generador Markov + gamma, Philox, balance hídrico y lógica compartida de escenarios. |
| `src/backends/serial/` | Implementación secuencial de referencia. |
| `src/backends/openmp/` | Paralelización por hilos y reducciones. |
| `src/backends/mpi/` | Reparto estático y maestro–trabajador dinámico. |
| `src/backends/hybrid/` | Integración MPI + OpenMP. |
| `src/backends/cuda/` | Extensión CUDA, solo si se activa en S10. |
| `src/io/` | Lectura de parámetros y escritura de resultados CSV con metadatos. |
| `src/stats/` | Intervalo de Wilson, histogramas y resumen de resultados. |
| `tests/unit/` | Pruebas del RNG, balance, estimadores y casos analíticos. |
| `tests/integration/` | Equivalencia entre versiones y conservación del número de escenarios. |
| `tests/concurrency/` | Reproducibilidad, carreras y comprobaciones de MPI/OpenMP/CUDA. |
| `config/` | Configuraciones reproducibles de estaciones, semilla, carga y barridos. |
| `data/raw/` | Datos SENAMHI originales; no se versionan datos grandes. |
| `data/processed/` | Series limpias y parámetros calibrados, generados de forma reproducible. |
| `data/metadata/` | Inventario, procedencia, licencias y criterios de exclusión. |
| `scripts/build/` | Instrucciones y scripts de compilación. |
| `scripts/run/` | Ejecución local y distribuida. |
| `scripts/bench/` | Barridos de recursos, cinco repeticiones, calentamiento y captura de hardware. |
| `scripts/deploy/` | Preparación y comprobación del clúster. |
| `docker/` | Imagen base, Compose y Swarm cuando estén implementados. |
| `results/raw/` | CSV originales de corridas y logs; no se versionan resultados grandes. |
| `results/processed/` | Tablas agregadas y análisis con trazabilidad. |
| `results/figures/` | Gráficos de rendimiento y riesgo. |
| `reports/` | Informe IEEE, anexos y presentación final. |

Los archivos reservados para código, pruebas, configuración y scripts contienen solo un comentario con su tarea y propietario. Todavía no compilan ni ejecutan. Las carpetas de datos y resultados conservan `.gitkeep` hasta que se generen salidas reales.

## Criterio de comparación de recursos

Se fija el mismo problema y la misma semilla por comparación. Se ejecuta una corrida de calentamiento y cinco repeticiones por punto; se guardan tiempos, resultados, commit y hardware. OpenMP se compara con 2, 4, 8 y 16 hilos; MPI con 2, 4, 8 y 16 procesos; el híbrido con esos presupuestos de núcleos CPU distribuidos entre procesos e hilos. Si se activa CUDA, se comparan 2, 4, 8 y 16 bloques y 128/256/512 hilos por bloque, con ocupación observada. Los bloques CUDA no equivalen a núcleos físicos de GPU. Se reportarán tiempo, speedup, eficiencia cuando corresponda y throughput tras comprobar la equivalencia de resultados.
