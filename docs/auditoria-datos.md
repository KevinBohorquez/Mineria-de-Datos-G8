# Auditoria de calidad de datos (T08)

**Responsable:** Angela · **Revisor:** David

Series generadas de forma sintetica (ver [`generar_datos_sinteticos.py`](../scripts/run/generar_datos_sinteticos.py)) porque este entorno no tiene acceso a la descarga real de SENAMHI; el procedimiento, las reglas y el script son los mismos que se aplicarian a la serie real cuando este disponible. No se presentan estas cifras como mediciones hidrologicas reales.

## Regla de exclusion

Una combinacion estacion/anio es elegible si tiene menos de 10% de dias faltantes y no tiene valores negativos sin corregir. Una estacion completa es elegible si al menos el 90% de sus anios cumplen la regla anterior.

## Resultado por estacion

| ID | Estacion | Anios auditados | Anios elegibles | % faltantes promedio | Estacion elegible |
| --- | --- | --- | --- | --- | --- |
| 000401 | Piura | 30 | 29 | 2.99% | Si |
| 000402 | Chulucanas | 27 | 26 | 2.99% | Si |
| 000601 | Tumbes | 32 | 31 | 3.00% | Si |
| 000301 | Chiclayo | 25 | 24 | 2.99% | Si |
| 000701 | Talara | 29 | 28 | 2.99% | Si |

**Estaciones elegibles: 5 de 5** (criterio de T08 exige >= 3). Cumple.

## Reproducir

```powershell
python scripts/run/generar_datos_sinteticos.py
python scripts/run/auditoria_datos.py
```

Produce `data/processed/auditoria_calidad.csv` (una fila por estacion/anio; fuera de Git por `.gitignore`, igual que el resto de `data/processed`). Este documento se regenera con cada corrida: si el script cambia, las cifras de arriba deben volver a calcularse con el mismo comando.
