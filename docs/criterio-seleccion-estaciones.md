# Criterio de selección de estaciones SENAMHI (T06)

**Responsable:** Angela

La definición del proyecto ([`definicion-proyecto.docx`](definicion-proyecto.docx)) fija dos cosas que acotan la selección y no son una elección libre del equipo:

> "Zonas (estaciones SENAMHI): 3 a 5 estaciones de la **costa norte y Lima**."

> "Si una llovizna moderada puede inundar un distrito de Lima mientras lluvias mucho más intensas no causan daños en otras ciudades, la variable determinante no es solo la cantidad de lluvia sino la relación entre el agua que cae y el agua que el sistema de drenaje puede evacuar" (sección 3.2, citando las inundaciones de agosto de 2026 en Villa El Salvador, Villa María del Triunfo y Chorrillos).

Es decir: el proyecto compara dos mecanismos de inundación distintos y necesita al menos una estación de cada uno para que la comparación normal/El Niño tenga sentido:

1. **Costa norte (Piura, Tumbes, Lambayeque):** lluvia extrema por El Niño costero (calentamiento del mar que dispara convección en la llanura costera baja de esos departamentos). Riesgo dominado por la *cantidad* de lluvia.
2. **Lima:** lluvia casi nula en año normal, pero drenaje tan limitado que una llovizna moderada ya inunda. Riesgo dominado por la *capacidad de drenaje*, no por la cantidad de lluvia.

## Reglas de selección (aplicadas a cada estación candidata)

| Regla | Razón |
| --- | --- |
| Región costa (llanura costera, altitud baja, no sierra/selva del mismo departamento) | El Niño costero actúa por calentamiento del mar frente a la costa; la sierra de Piura/Tumbes/Lambayeque tiene otra dinámica de lluvias, a veces desacoplada del fenómeno. Una estación serrana no mostraría el contraste normal/El Niño que exige OE1. |
| Zona urbana (no un puesto rural) | El proyecto modela riesgo de inundación **urbana** por capacidad de drenaje, no precipitación de campo abierto (supuesto 5.3: "las estaciones SENAMHI seleccionadas son representativas de la zona urbana analizada"). |
| Capital de departamento o ciudad con mayor población | Son las ciudades que aparecen en los reportes reales de emergencia (INDECI, prensa) citados en la definición, lo que permite contrastar el resultado simulado contra eventos conocidos (p. ej. Piura/Tumbes/Chiclayo en El Niño 1997-98, 2017 y 2023-24). |
| ≥ 20 años de registro y < 10 % de faltantes en la temporada (T06/T08) | Restricción dura de la tarea; filtra estaciones automáticas recientes sin historia suficiente. |

## Estaciones seleccionadas

| Ciudad | Departamento | Zona (mecanismo) | Estado |
| --- | --- | --- | --- |
| Miraflores (Castilla) | Piura | Costa norte — El Niño costero | Descargada, 1973–2015 (42 años) |
| Chulucanas | Piura | Costa norte — El Niño costero | Descargada, 1972–2014 (42 años) |
| Bernal | Piura | Costa norte — El Niño costero | Descargada, 1963–2014 (51 años); pueblo muy citado por el desborde del río Piura en 2017 |
| Puerto Pizarro | Tumbes | Costa norte — El Niño costero | Descargada, 1963–2015 (52 años). **Sustituye** a "Tumbes ciudad": no hay estación listada con ese nombre en el portal; Puerto Pizarro es la zona costera a ~13 km del centro, misma llanura y mecanismo |
| El Tigre | Tumbes | Costa norte — refuerzo/contraste | Descargada, 1963–2013 (50 años); zona arrocera con desborde del río Zarumilla, más rural que urbana |
| Lambayeque | Lambayeque | Costa norte — El Niño costero | Descargada, 1928–2014 (86 años). Capital provincial conurbada con Chiclayo (no listado en el portal) |
| Chosica | Lima | Lima — drenaje/quebrada insuficiente | Descargada, 1989–2014 (24 años). **Sustituye** a Villa El Salvador/VMT/Chorrillos (no disponibles en el portal); único distrito de Lima Metropolitana en la lista. Mecanismo real es huaico de quebrada (marzo 2017, afectó la planta de agua de SEDAPAL), no alcantarillado plano — se documenta la diferencia |
| Cañete | Lima | Costa sur — refuerzo/contraste | Descargada, 1936–2010 (74 años); valle costero con desborde de río en El Niño, mecanismo más parecido al de la costa norte que al de drenaje urbano |

8 estaciones en total, por encima del mínimo de 3–5. Ver el detalle de faltantes y elegibilidad por año en [`auditoria-datos.md`](auditoria-datos.md): 5 de 8 son elegibles como estación completa; las 3 restantes (Chulucanas, Lambayeque, Cañete) igual aportan años individuales elegibles a la calibración de T10.

Si una estación propuesta no cumple el umbral de 20 años o de faltantes, se documenta aquí el reemplazo y la razón, no se oculta la estación descartada.
