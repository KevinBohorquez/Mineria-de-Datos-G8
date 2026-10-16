# Plan de desarrollo hasta la semana 8

## Alcance y estado

Este plan reúne E1, E2 y E3: estructura del repositorio, datos, referencia secuencial y OpenMP. El cronograma marca sus tareas como **Completado por decisión del equipo**. Esa marca administrativa no sustituye los archivos, pruebas y mediciones descritos abajo; cada responsable debe adjuntar su propia evidencia antes de usarla en el informe o la exposición.

El repositorio ya contiene la estructura documental y las carpetas previstas. El código, los datos y los resultados se incorporan a través de tareas independientes con entradas y salidas acordadas.

## Contratos que permiten avanzar en paralelo

| Contrato | Especificación que se fija en el repositorio |
| --- | --- |
| Configuración | Archivo de texto con estación, régimen, capacidad `C`, umbral `U`, días `D`, semilla, número de escenarios y backend. |
| Núcleo | Una función recibe parámetros, clave e índice global de escenario y devuelve inundación y máximo acumulado. |
| Resultados | CSV con configuración, cantidad simulada, inundaciones, histograma, tiempo, semilla, commit y hardware. |
| Datos | Inventario de fuente, estación, fechas, unidades, faltantes y ruta de descarga; datos crudos fuera de Git. |
| Medición | Mismo problema y semilla; una corrida de calentamiento y cinco repeticiones por punto. |

David publica estos contratos como especificación. Los demás pueden desarrollar contra ellos con datos de prueba locales. La integración requiere verificar compatibilidad, pero no deja la preparación de cada artefacto a cargo de otra persona.

## Propietarios y resultados hasta S08

| Responsable | Tareas del cronograma | Resultado propio y verificable |
| --- | --- | --- |
| **David (R1)** | T02, T03 | Especificación de CLI, configuración y CSV; repositorio Git en `master`, reglas de PR y plantilla de revisión. |
| **Angela (R2)** | T06, T08, T09, T10 | Inventario SENAMHI; reporte de calidad con faltantes y exclusiones; tabla ENFEN; parámetros Markov + gamma y 100 remuestreos bootstrap por estación y régimen. |
| **Ashley (R3)** | T04, T11, T12, T15 | CMake y CI; núcleo secuencial con Philox y balance hídrico; estimadores y salida CSV; backend OpenMP con reducciones. Puede usar parámetros sintéticos hasta recibir los calibrados. |
| **Lita (R4)** | T13, T16, T17 | Casos deterministas V6/V7 y comparación V1/V5; matriz OpenMP de **2, 4, 8 y 16 hilos** con carga fija, semilla fija, afinidad y `schedule` registrados. Los casos pequeños se preparan sin esperar datos reales. |
| **Miguel (R5)** | T05, T14 | Docker base con `hello` MPI + OpenMP en dos contenedores; herramienta de medición T1 que guarda cinco tiempos, calentamiento y descripción del hardware. |
| **Rhamses (R6)** | T01, T07, T18 | Definición única y registro de decisiones; tablero de tareas; tabla y gráficos de tiempo, speedup y eficiencia OpenMP para 2/4/8/16 hilos a partir de CSV, con formato y fuentes documentados. Puede preparar el generador de gráficos con CSV de ejemplo. |

**Avance verificable de R6 al 15/10/2026:** T01 tiene [acta de revisión](acta-revision-definicion.md), pero aún faltan las seis revisiones individuales. T07 se comprueba con [`validar_cronograma.py`](../scripts/validar_cronograma.py): 53 IDs únicos con los campos obligatorios. T18 tiene [protocolo](protocolo-graficos-openmp.md), generador y pruebas automatizadas; la tabla y las figuras finales esperan los CSV reales de T14 y T16. No se usan datos sintéticos como evidencia de rendimiento.

**Avance verificable de R2 (Angela) al 15/10/2026:** T06–T10 se trabajaron con **series diarias reales** descargadas del portal oficial de SENAMHI (cuenta registrada), convertidas con [`importar_senamhi.py`](../scripts/run/importar_senamhi.py). La selección de estaciones sigue el criterio documentado en [`criterio-seleccion-estaciones.md`](criterio-seleccion-estaciones.md) (costa norte para El Niño costero + Lima para el caso de drenaje insuficiente, citado literalmente en la definición del proyecto). El generador sintético ([`generar_datos_sinteticos.py`](../scripts/run/generar_datos_sinteticos.py)) queda solo como respaldo si alguna estación deja de estar disponible.

- **T06:** [`data/metadata/inventario_senamhi.csv`](../data/metadata/inventario_senamhi.csv), 8 estaciones reales: Miraflores, Chulucanas y Bernal (Piura); Puerto Pizarro y El Tigre (Tumbes); Lambayeque (Lambayeque); Chosica y Cañete (Lima). Las sustituciones (Puerto Pizarro por "Tumbes ciudad", Chosica por los distritos de Lima citados en la definición) están documentadas con su razón en el inventario y en `criterio-seleccion-estaciones.md`.
- **T08:** [`auditoria-datos.md`](auditoria-datos.md) y `data/processed/auditoria_calidad.csv` (generado por `auditoria_datos.py`, fuera de Git por diseño: ver `data/processed/*` en `.gitignore`). El % de faltantes se mide sobre la temporada enero–abril (120/121 días), no el año completo. 4 de 8 estaciones quedan elegibles a nivel de estación completa (<10 % de faltantes en ≥90 % de sus años); todas aportan años individuales elegibles, por encima del mínimo de 3 que exige T08.
- **T09:** `data/processed/regimenes.csv` (generado por [`clasificar_regimenes.py`](../scripts/run/clasificar_regimenes.py)), 345 filas estación–año clasificadas con la definición operacional oficial del ENFEN (2012): ICEN > 0,4 durante ≥3 meses consecutivos, sobre el índice ICEN real 1950–2024 descargado de [`met.igp.gob.pe`](http://met.igp.gob.pe/datos/ICEN.txt) ([`data/external/icen.txt`](../data/external/icen.txt)).
- **T10:** `data/processed/parametros.csv` y `bootstrap_parametros.csv` (generados por [`calibrar.py`](../scripts/run/calibrar.py) con `--semilla 20261015`): 16 grupos estación×régimen (7–53 años cada uno), 100 réplicas bootstrap por grupo **remuestreando años con reemplazo** (no bloques de días), validación de rango y finitud registrada en `data/processed/calibracion_log.txt`.

**Correcciones 15/10/2026 (auditoría propia contra la definición, tras el hallazgo de V6 de Lita — no de Ashley, como se atribuyó por error en el commit anterior):** la primera versión de T08–T10 no seguía `definicion-proyecto.docx` al pie de la letra en cuatro puntos — los cuatro ya corregidos:
1. T10 calibraba con el año completo en vez de solo enero–abril, contaba cualquier valor > 0 mm como lluvioso en vez de ≥ 0,1 mm, y ajustaba alfa/theta por momentos en vez del método de Thom (1958) — esto desviaba la lluvia simulada 58–84 % por debajo de la observada (hallazgo original de V6 contra lo observado).
2. T08 medía el 10 % de faltantes sobre el año completo; la definición (7.6) pide medirlo sobre la temporada.
3. T09 clasificaba El Niño con una lista aproximada (ONI, de memoria) en vez de "los reportes oficiales del ENFEN" (3.4); se reemplazó por la regla operacional real del ENFEN (ICEN > 0,4, ≥3 meses) sobre datos oficiales descargados.
4. El bootstrap de T10 remuestreaba bloques de 30 días; la definición (6.2/7.6) pide remuestrear años.

V6 contra el modelo (24/24), V7 y CTest no estaban afectadas por ninguno de los cuatro — el núcleo de simulación siempre fue correcto; el error estaba en cómo se preparaban sus parámetros de entrada.

Reproducir en orden: `importar_senamhi.py <archivo> --id <id>` (uno por estación) → `auditoria_datos.py` → `clasificar_regimenes.py` → `calibrar.py --semilla 20261015`.

## Comparación solicitada de núcleos

La referencia secuencial usa un núcleo. OpenMP se ejecuta con 2, 4, 8 y 16 hilos, que representan ese número de núcleos físicos **solo si el equipo los tiene disponibles**. Si alguna configuración excede los núcleos físicos, se registra como sobresuscrita y se analiza aparte. Mantener `N`, parámetros y semilla constantes dentro del barrido. Guardar por punto: número de hilos, núcleos físicos, CPU, afinidad, `schedule`, cinco tiempos, conteos y CSV. Calcular tiempo medio, desviación estándar, speedup respecto al secuencial y eficiencia.

## Criterios de revisión del trabajo

- **E1:** están localizables la definición, los contratos, la estructura, el inventario de datos y la ejecución mínima de Docker/CI.
- **E2:** el secuencial produce resultados reproducibles; V6/V7 y T1 tienen archivos de evidencia.
- **E3:** OpenMP conserva los conteos; V1/V5 y el barrido 2/4/8/16 muestran CSV y gráficos.
- Si falta evidencia, registrar exactamente cuál archivo, prueba o corrida falta. La marca administrativa del cronograma no debe citarse como resultado experimental.
