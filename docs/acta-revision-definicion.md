# Revisión interna de la definición del proyecto

**Tarea:** T01 · **Responsable:** Rhamses · **Documento revisado:** [definicion-proyecto.docx](definicion-proyecto.docx)

## Estado y alcance de la revisión

La definición vigente está en un solo archivo. La copia revisada corresponde al commit `79e85d7` (`Initial commit`). El alcance, el modelo Monte Carlo, la arquitectura secuencial/OpenMP/MPI/híbrida, la extensión CUDA condicionada y las entregas hasta la semana 15 aparecen en ese documento. El [README](../README.md) enlaza la definición, los dos planes y ambos cronogramas.

Esta acta prepara la revisión del equipo. **La aprobación de los seis integrantes aún no está documentada.** La marca administrativa «Completado» de T01 en el cronograma no constituye una firma ni una prueba de implementación.

## Decisiones que debe confirmar el equipo

| Tema | Definición actual | Evidencia que faltará revisar durante el desarrollo |
| --- | --- | --- |
| Resultado | Probabilidad de superar el umbral de agua acumulada durante una temporada; intervalo de Wilson y curva riesgo–capacidad. | CSV de simulación y comprobación de estimadores. |
| Lluvia y drenaje | Ocurrencia Markov, monto gamma y balance hídrico simplificado con parámetros calibrados desde SENAMHI. | Inventario, calibración y validación estadística. |
| Paralelismo | Referencia secuencial, OpenMP, MPI y MPI + OpenMP; CUDA condicionada a la decisión interna de S10. | Ejecutables, pruebas de equivalencia y mediciones. |
| Comparación de recursos | 2, 4, 8 y 16 hilos OpenMP o procesos MPI; combinaciones equivalentes en el híbrido. En CUDA se varían bloques e hilos por bloque, que no son núcleos físicos seleccionables. | CSV con carga y semilla constantes, calentamiento, cinco repeticiones, hardware, afinidad y sobresuscripción. |
| Estado del proyecto | E1–E3 tienen una marca administrativa de completado; los resultados técnicos requieren archivos y pruebas propios. | Enlace a cada evidencia antes de exponerla o citarla. |

## Revisión individual

Cada integrante registra fecha, observación concreta o «sin observaciones» y enlace a su comentario o cambio. Rhamses consolida las observaciones resueltas y actualiza esta tabla. No se marca «Aprobado» por silencio.

| Integrante | Estado | Fecha | Observación y evidencia |
| --- | --- | --- | --- |
| David | Pendiente | — | — |
| Angela | Pendiente | — | — |
| Ashley | Pendiente | — | — |
| Lita | Pendiente | — | — |
| Miguel | Pendiente | — | — |
| Rhamses | Pendiente | — | — |

## Cierre de T01

T01 quedará acreditada cuando las seis filas tengan revisión verificable, las observaciones estén resueltas y la definición final conserve un enlace válido desde el README. Si cambia el DOCX, registrar aquí el nuevo commit y repetir la revisión de las secciones afectadas.
