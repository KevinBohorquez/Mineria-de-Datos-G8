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
| **David (R1)** | T02, T03 | Especificación de CLI, configuración y CSV; repositorio Git en `main`, reglas de PR y plantilla de revisión. |
| **Angela (R2)** | T06, T08, T09, T10 | Inventario SENAMHI; reporte de calidad con faltantes y exclusiones; tabla ENFEN; parámetros Markov + gamma y 100 remuestreos bootstrap por estación y régimen. |
| **Ashley (R3)** | T04, T11, T12, T15 | CMake y CI; núcleo secuencial con Philox y balance hídrico; estimadores y salida CSV; backend OpenMP con reducciones. Puede usar parámetros sintéticos hasta recibir los calibrados. |
| **Lita (R4)** | T13, T16, T17 | Casos deterministas V6/V7 y comparación V1/V5; matriz OpenMP de **2, 4, 8 y 16 hilos** con carga fija, semilla fija, afinidad y `schedule` registrados. Los casos pequeños se preparan sin esperar datos reales. |
| **Miguel (R5)** | T05, T14 | Docker base con `hello` MPI + OpenMP en dos contenedores; herramienta de medición T1 que guarda cinco tiempos, calentamiento y descripción del hardware. |
| **Rhamses (R6)** | T01, T07, T18 | Definición única y registro de decisiones; tablero de tareas; tabla y gráficos de tiempo, speedup y eficiencia OpenMP para 2/4/8/16 hilos a partir de CSV, con formato y fuentes documentados. Puede preparar el generador de gráficos con CSV de ejemplo. |

## Comparación solicitada de núcleos

La referencia secuencial usa un núcleo. OpenMP se ejecuta con 2, 4, 8 y 16 hilos, que representan ese número de núcleos físicos **solo si el equipo los tiene disponibles**. Si alguna configuración excede los núcleos físicos, se registra como sobresuscrita y se analiza aparte. Mantener `N`, parámetros y semilla constantes dentro del barrido. Guardar por punto: número de hilos, núcleos físicos, CPU, afinidad, `schedule`, cinco tiempos, conteos y CSV. Calcular tiempo medio, desviación estándar, speedup respecto al secuencial y eficiencia.

## Criterios de revisión del trabajo

- **E1:** están localizables la definición, los contratos, la estructura, el inventario de datos y la ejecución mínima de Docker/CI.
- **E2:** el secuencial produce resultados reproducibles; V6/V7 y T1 tienen archivos de evidencia.
- **E3:** OpenMP conserva los conteos; V1/V5 y el barrido 2/4/8/16 muestran CSV y gráficos.
- Si falta evidencia, registrar exactamente cuál archivo, prueba o corrida falta. La marca administrativa del cronograma no debe citarse como resultado experimental.
