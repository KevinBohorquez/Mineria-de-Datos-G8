# Tabla y gráficos OpenMP de la tarea T18

**Responsable:** Rhamses. El programa [graficar_openmp.py](../scripts/bench/graficar_openmp.py) está listo para procesar las mediciones T14 y T16. **Aún no existen CSV reales de ambas tareas en el repositorio; por eso no se publican cifras ni figuras de rendimiento.**

## Entradas acordadas

El generador recibe dos CSV UTF-8: uno secuencial de T14 y otro OpenMP de T16. Cada archivo tiene una fila por corrida con esta cabecera exacta:

```csv
modelo,hilos,repeticion,tiempo_s,n,semilla,cpu,nucleos_fisicos,afinidad,schedule,commit,calentamiento
```

| Campo | Regla |
| --- | --- |
| `modelo` | `secuencial` en T14; `openmp` en T16. |
| `hilos` | 1 en T14; 2, 4, 8 y 16 en T16. |
| `repeticion`, `calentamiento` | Una fila con repetición 0 y calentamiento 1; después repeticiones 1 a 5 con calentamiento 0 para **cada** configuración. |
| `tiempo_s` | Segundos de tiempo transcurrido, positivos. El calentamiento no entra en la media. |
| `n`, `semilla`, `cpu`, `nucleos_fisicos`, `commit` | Deben coincidir entre T14 y T16 para comparar la misma carga y ejecución. `n` y núcleos físicos son positivos. |
| `afinidad`, `schedule` | Etiquetas no vacías. Usar `none` para el schedule secuencial; para OpenMP, registrar el valor real (`static`, `dynamic`, etc.) y la política de afinidad usada. |

Una configuración OpenMP es la combinación de `schedule` y `afinidad`; debe contener los cuatro puntos 2/4/8/16. Si se mide más de una configuración, el programa traza una curva por cada combinación. El número de hilos mayor que `nucleos_fisicos` queda marcado como sobresuscrito; no se presenta como uso de esa cantidad de núcleos físicos.

## Ejecución y salidas

Desde la raíz del repositorio:

```powershell
python scripts/bench/graficar_openmp.py --secuencial results/bench/secuencial_t1.csv --openmp results/bench/openmp.csv --salida results
```

Se generan `results/processed/openmp_resumen.csv` y las figuras `results/figures/openmp_tiempo.svg`, `openmp_speedup.svg` y `openmp_eficiencia.svg`. Esos directorios contienen resultados calculados; no se guardan en Git hasta que haya mediciones reales revisadas y se acuerde su publicación. La tabla incluye rutas y SHA-256 de ambos CSV de origen.

La media y la desviación estándar muestral se calculan sobre cinco tiempos por punto. `speedup = media(T1) / media(Tp)` y `eficiencia = speedup / p`. El gráfico de tiempo muestra barras de una desviación estándar; los gráficos de speedup y eficiencia muestran cocientes de medias, no intervalos de confianza. Se deben revisar además las pruebas de equivalencia V1/V5 antes de interpretar un speedup como una mejora válida.

Si el formato final de T14 o T16 usa otros nombres de columnas, se ajustará el lector o se hará una conversión documentada que preserve todas las muestras y metadatos; no se editarán cifras a mano.
