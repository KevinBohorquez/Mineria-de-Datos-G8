# Auditoría de datos SENAMHI (T06, T08, T09)

Series diarias de precipitación de 8 estaciones en `data/raw/`; procedencia y campos pendientes en [`data/metadata/fuentes.md`](../data/metadata/fuentes.md). La carpeta previa `senamhi_data/processed/` se descartó por usar umbral `> 0`, año completo, regímenes hipotéticos y una sola semilla.

## Reglas

Basadas en `docs/definicion-proyecto.docx` §7.5–7.7 e implementadas en `scripts/run/datos_comunes.py`.

| Regla | Valor |
|---|---|
| Temporada | 1 de enero a 30 de abril, D = 120 días; se excluye el 29 de febrero. Solo temporadas completas dentro del rango del archivo. |
| Día lluvioso | `>= 0.1 mm` |
| Traza | `0 < mm < 0.1`; cuenta como día seco, no como faltante |
| Faltante | fecha sin fila, vacío, no numérico o negativo |
| Duplicado | se conserva la primera fila y se marca |
| Atípico | `> 150 mm/día`; se marca y se conserva |
| Temporada elegible | faltantes `< 10 %` (como máximo 11 de 120 días) |
| Estación calificada | `>= 20` temporadas elegibles |
| Selección | hasta 5 calificadas con menor % faltante enero–abril; si ninguna de Lima entra y alguna califica, la mejor de Lima ocupa la última plaza |
| Régimen | evento Y–Y+1 → temporada Y+1; resto `normal` |

## Resumen por estación

Fuente: `data/metadata/inventario_senamhi.csv` y `data/processed/auditoria_calidad.csv`.

| Estación | Rango | % faltante ene–abr | Temporadas completas | Elegibles | Atípicos > 150 mm | Trazas | Seleccionada |
|---|---|---:|---:|---:|---:|---:|---|
| piura_miraflores | 1973-01-01 a 2015-10-31 | 3.49 | 43 | 40 | 0 | 256 | sí |
| tumbes_puertopizarro | 1963-09-01 a 2015-10-31 | 4.05 | 52 | 47 | 1 (1983) | 0 | sí |
| lima_chosica | 1989-12-01 a 2014-01-31 | 4.10 | 24 | 22 | 0 | 0 | sí |
| tumbes_eltigre | 1963-09-01 a 2013-12-31 | 4.53 | 50 | 47 | 1 (1998) | 33 | sí |
| piura_bernal | 1963-11-01 a 2014-06-30 | 6.96 | 51 | 45 | 0 | 246 | sí |
| lambayeque_lambayeque | 1928-11-02 a 2014-07-31 | 8.91 | 86 | 74 | 0 | 635 | no (6.º lugar) |
| piura_chulucanas | 1972-01-02 a 2014-06-30 | 20.46 | 42 | 30 | 3 (1983 ×2, 2012) | 49 | no |
| lima_canete | 1936-07-01 a 2010-07-31 | 47.35 | 74 | 38 | 0 | 511 | no |

En las temporadas auditadas no hay fechas ausentes, duplicados ni negativos: todos los faltantes son valores vacíos, casi siempre en bloques de meses completos (31, 59, 61 o 90 días).

## Selección

Calificaron las 8 estaciones (todas tienen `>= 20` temporadas elegibles). Por menor % faltante enero–abril quedaron: **piura_miraflores, tumbes_puertopizarro, lima_chosica, tumbes_eltigre y piura_bernal** (`data/processed/estaciones_seleccionadas.csv`). Cubren costa norte (Piura, Tumbes) y una estación de Lima sin necesidad de la regla de reemplazo.

## Regímenes

`data/metadata/enfen_eventos.csv` contiene solo los eventos citados en la definición del proyecto: 1982–83 (temporada 1983), 1997–98 (temporada 1998) y el Niño costero 2017 (temporada 2017). `data/processed/regimenes.csv` clasifica las 201 temporadas elegibles de las estaciones seleccionadas.

| Estación | normal | el_nino | Temporadas El Niño elegibles |
|---|---:|---:|---|
| piura_miraflores | 38 | 2 | 1983, 1998 |
| tumbes_puertopizarro | 45 | 2 | 1983, 1998 |
| lima_chosica | 22 | 0 | — (1998 tiene 25.8 % faltante; la serie empieza en 1990) |
| tumbes_eltigre | 45 | 2 | 1983, 1998 |
| piura_bernal | 44 | 1 | 1998 (1983 tiene 50.8 % faltante) |

## Alertas

1. **Cañete:** 47.35 % faltante enero–abril. Califica por número de temporadas elegibles (38) pero queda último en la clasificación; no se usa.
2. **Sin 2017:** ninguna serie llega a enero–abril de 2017 (la más larga termina en octubre de 2015). El Niño costero 2017 no tiene datos.
3. **Muestra El Niño delgada:** como máximo 2 temporadas por estación; piura_bernal tiene 1 y lima_chosica ninguna. Las estimaciones `el_nino` (T10) deben marcarse como muestra insuficiente cuando haya menos de 2 temporadas, y lima_chosica no tiene configuración `el_nino`.
4. **Ampliar eventos** (1972–73, 1987, 1991–92, 2015–16) exige una fuente oficial ENFEN/ICEN y es decisión del equipo; no se agregaron.
5. **Lambayeque** (8.91 % faltante, 74 temporadas elegibles) queda fuera solo por el tope de 5 estaciones.
6. **Procedencia pendiente:** códigos de estación, coordenadas, URL y fecha de descarga no están en los archivos recibidos.
7. **Precisión de registro:** tumbes_puertopizarro y lima_chosica no tienen trazas; probablemente registran con resolución de 0.1 mm o redondean. No cambia la regla de día lluvioso.

## Reproducir

En la imagen `pp-g8`, desde la raíz del repositorio:

```bash
python3 scripts/run/inventario.py
python3 scripts/run/auditar.py
python3 scripts/run/clasificar_regimenes.py
python3 -m pytest -v tests/unit/test_datos.py
```
