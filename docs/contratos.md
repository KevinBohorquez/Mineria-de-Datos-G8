# Contratos de CLI, configuración y CSV (T02)

**Responsable:** David · **Revisor:** Rhamses · **Versión del contrato:** 1

Este documento fija las interfaces que permiten programar en paralelo. Cada backend (serial, OpenMP, MPI estático, MPI dinámico, híbrido, CUDA) respeta estos contratos; si uno cambia, se edita este archivo en el mismo PR y se sube `version_contrato`.

## 1. Índice global y semilla

Una **configuración** `c` es una combinación de estación, régimen, capacidad `C`, umbral `U` y conjunto de parámetros. Cada configuración simula `N` temporadas.

| Concepto | Definición |
| --- | --- |
| Índice global | `i = c · N + j`, con `c` = identificador de configuración (entero ≥ 0) y `j ∈ [0, N)`. Un backend que ejecuta una sola configuración usa `c = 0` salvo que se indique `configuracion_id`. |
| Reparto | Todo backend procesa rangos semiabiertos `[i0, i1)` de índices. El resultado no depende de quién procesa cada índice. |
| Clave Philox | `clave = splitmix64(semilla + c · 0x9E3779B97F4A7C15)`, de 64 bits; se divide en dos palabras de 32 bits para Philox4x32-10. |
| Contador Philox | Contiene el índice global del escenario y el día `d`. Ningún generador se siembra por rango MPI, hilo o bloque. |
| Aritmética de conteos | Siempre `uint64_t` (`MPI_UINT64_T` en MPI). |

## 2. Función de núcleo

```cpp
struct ResultadoEscenario {
    bool   inundacion;   // Amax > U
    double maximo_mm;    // Amax, máximo acumulado de la temporada
};
ResultadoEscenario simular_escenario(const ParametrosSimulacion& p,
                                     std::uint64_t clave,
                                     std::uint64_t indice_global);
```

Es una función pura: misma entrada, mismo resultado, sin estado compartido. `ParametrosSimulacion` (`include/simulacion.hpp`, T11) contiene `p01, p11, alfa, theta, C, U, D`.

## 3. Acumulador y reducción

Todo backend entrega, por configuración, un acumulador que se suma con `MPI_SUM` / `reduction(+)`:

| Campo | Tipo | Significado |
| --- | --- | --- |
| `k` | `uint64_t` | Escenarios con inundación. |
| `n` | `uint64_t` | Escenarios simulados. |
| `hist[512]` | `uint64_t[512]` | Histograma del máximo acumulado: 512 clases de 1 mm; la clase `b = min(floor(maximo_mm), 511)`. |

**Invariantes** (pruebas V1, V3, V4): `n == N`; `Σ hist == n`; `k` e `hist` son idénticos bit a bit entre backends y para cualquier número de procesos e hilos; dos corridas iguales dan los mismos conteos.

## 4. Configuración (YAML)

Archivo de texto con pares `clave: valor` planos (sin anidar) y `#` para comentarios. Ejemplo en [`config/ejemplo.yaml`](../config/ejemplo.yaml).

| Clave | Tipo / unidad | Obligatoria | Por defecto | Validación |
| --- | --- | --- | --- | --- |
| `estacion` | texto | sí | — | Nombre de estación del inventario SENAMHI. |
| `regimen` | `normal` \| `el_nino` | sí | — | Uno de los dos valores. |
| `capacidad_mm_dia` (`C`) | real, mm/día | sí | — | `> 0`. Rango de diseño 5–65, paso 5. |
| `umbral_mm` (`U`) | real, mm | sí | — | `> 0`. Referencias 30 / 50 / 80. |
| `dias` (`D`) | entero | no | 120 | `≥ 1`. |
| `semilla` | entero sin signo de 64 bits | sí | — | Se registra en cada CSV. |
| `escenarios` (`N`) | entero sin signo de 64 bits | sí | — | `≥ 1`. Oficial 10⁶ por configuración. |
| `configuracion_id` (`c`) | entero | no | 0 | `≥ 0`. |
| `backend` | `serial` \| `openmp` \| `mpi_estatico` \| `mpi_dinamico` \| `hibrido` \| `cuda` | no | el del ejecutable | Uno de los valores; cada ejecutable fija el suyo y avisa si el YAML pide otro. |
| `hilos` | entero | no | 1 | `≥ 1`. Solo OpenMP e híbrido. |
| `lote` (`B`) | entero | no | 62 500 | `≥ 1`. Solo `mpi_dinamico`; tamaño de bloque de la cola. |
| `parametros` | ruta | no | — | CSV de parámetros calibrados (T10). Si falta se usan los de prueba. |
| `salida` | ruta | no | `results/raw/<backend>.csv` | El archivo se crea o se agrega una fila por corrida. |

## 5. Línea de comandos

Todos los ejecutables aceptan las mismas opciones; una opción de la CLI **tiene prioridad** sobre el YAML.

```text
<ejecutable> --config RUTA.yaml [--escenarios N] [--semilla S] [--dias D]
             [--hilos T] [--lote B] [--salida RUTA.csv]
             [--repeticion R] [--calentamiento] [--verificar]
```

- `--repeticion R` y `--calentamiento` etiquetan la fila del CSV (calentamiento = repetición 0, indicador 1; después repeticiones 1–5 con indicador 0).
- `--verificar` recalcula en el rango 0 la referencia secuencial y compara `k` e histograma bit a bit (V1); solo para cargas pequeñas.
- Los ejecutables MPI se lanzan con `mpirun -np P ./ejecutable ...`; el número de procesos lo fija `mpirun`, no el YAML.
- Códigos de salida: `0` correcto; `1` argumentos o configuración inválidos; `2` falló una verificación (suma ≠ N, histograma inconsistente, V1); `3` error de MPI.
- La salida estándar incluye el log de verificación (ver §7); el CSV se escribe solo desde el rango 0.

## 6. CSV de resultados

UTF-8, separador coma, fin de línea `\n`, punto decimal. Una fila por corrida y configuración, con esta cabecera exacta:

```csv
version_contrato,backend,estacion,regimen,capacidad_mm_dia,umbral_mm,dias,semilla,configuracion_id,n_solicitado,n_simulado,inundaciones,p_hat,histograma,procesos,hilos,repeticion,calentamiento,tiempo_s,commit,hardware,afinidad,schedule
```

| Columna | Tipo / unidad | Regla |
| --- | --- | --- |
| `version_contrato` | entero | 1. |
| `backend` | texto | Valor de la clave `backend`. |
| `estacion`, `regimen` | texto | Copia de la configuración. |
| `capacidad_mm_dia`, `umbral_mm` | real, mm/día y mm | Copia de la configuración. |
| `dias`, `semilla`, `configuracion_id` | entero | Copia de la configuración. |
| `n_solicitado`, `n_simulado` | `uint64` | Deben ser iguales (V3). |
| `inundaciones` | `uint64` | `k`. |
| `p_hat` | real | `k / n_simulado`. |
| `histograma` | 512 enteros separados por `;` | `hist[0] … hist[511]`; su suma es `n_simulado`. |
| `procesos`, `hilos` | entero | Procesos MPI (1 si no hay MPI) e hilos OpenMP por proceso (1 si no hay). |
| `repeticion`, `calentamiento` | entero | 0 y 1 para calentamiento; 1–5 y 0 para medidas. |
| `tiempo_s` | real, segundos | Tiempo transcurrido de pared del cómputo y la reducción (sin leer configuración). |
| `commit` | texto | Hash corto de Git (`unknown` si no está disponible). |
| `hardware` | texto | CPU y núcleos físicos del nodo del rango 0, sin comas. |
| `afinidad` | texto | Política (`OMP_PROC_BIND`, reparto por nodo) o `none`. |
| `schedule` | texto | `OMP_SCHEDULE` real o `none`. |

Ejemplo de fila (histograma abreviado para lectura; en el archivo van los 512 valores):

```csv
1,mpi_estatico,piura,normal,30,50,120,12345,0,1000000,1000000,18423,0.018423,"999012;610;...;0",4,1,1,0,0.842,02ba40c,"AMD Ryzen 7 (8 nucleos)",none,none
```

El generador de gráficos OpenMP usa su propio CSV de medición (cabecera definida en [`protocolo-graficos-openmp.md`](protocolo-graficos-openmp.md)); este CSV de resultados lo cubre con las columnas equivalentes y añade `procesos` y los conteos.

## 7. Log de verificación

Cada ejecutable MPI imprime en la salida estándar, desde el rango 0, líneas con prefijo `[verif]` para que los scripts de CI las filtren:

```text
[verif] backend=mpi_estatico procesos=4 n_solicitado=1000000
[verif] rango=0 inicio=0 fin=250000 n_local=250000
[verif] rango=1 inicio=250000 fin=500000 n_local=250000
...
[verif] suma_n=1000000 suma_hist=1000000 k=18423 estado=OK
[verif] v1_referencia=OK
```

Cualquier `estado` distinto de `OK` termina el programa con código 2.
