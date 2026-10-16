# Fuentes de datos SENAMHI (T06)

Series diarias de precipitación copiadas a `data/raw/` desde la carpeta `senamhi_data/raw/` del equipo, con los mismos nombres de archivo y finales de línea normalizados a LF. Formato: `fecha,precipitacion_mm` (fecha `AAAA-MM-DD`; valor vacío = día faltante).

La carpeta `senamhi_data/processed/` previa **no se usa**: su auditoría encontró umbral de lluvia `> 0` (no `>= 0.1 mm`), año completo en lugar de la temporada enero–abril, regímenes "hipotéticos" que etiquetaban 1982–83 como normal y una sola semilla de bootstrap.

## Procedencia por estación

Los campos marcados PENDIENTE no figuran en los archivos recibidos y no se deben inventar.

| Archivo | Región | Código SENAMHI | Coordenadas (lat, lon, alt) | URL de descarga | Fecha de descarga |
|---|---|---|---|---|---|
| `lambayeque_lambayeque.csv` | Lambayeque | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo |
| `lima_canete.csv` | Lima | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo |
| `lima_chosica.csv` | Lima | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo |
| `piura_bernal.csv` | Piura | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo |
| `piura_chulucanas.csv` | Piura | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo |
| `piura_miraflores.csv` | Piura | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo |
| `tumbes_eltigre.csv` | Tumbes | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo |
| `tumbes_puertopizarro.csv` | Tumbes | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo | PENDIENTE — dato a confirmar por el equipo |

Rango de fechas, faltantes, máximo diario y trazas por estación: `data/metadata/inventario_senamhi.csv` (generado por `scripts/run/inventario.py`).

## Reglas de procesamiento

Implementadas en `scripts/run/datos_comunes.py`; resumen y resultados en `docs/auditoria-datos.md`.

- **Temporada:** 1 de enero a 30 de abril, D = 120 días; se excluye el 29 de febrero (28 de febrero y 1 de marzo se tratan como consecutivos). Solo cuentan las temporadas completas dentro del rango de fechas del archivo.
- **Día lluvioso:** precipitación `>= 0.1 mm`. Valores en `(0, 0.1)` son **trazas** y cuentan como día seco.
- **Faltante:** fecha sin fila, valor vacío, no numérico o negativo.
- **Duplicados:** se conserva la primera fila de la fecha y se marca.
- **Atípicos:** `> 150 mm/día`; se marcan y se conservan.
- **Temporada elegible:** menos del 10 % de días faltantes (como máximo 11 de 120).
- **Estación calificada:** al menos 20 temporadas elegibles. Se seleccionan hasta 5 calificadas con menor % faltante enero–abril; si ninguna de Lima entra y alguna de Lima califica, la mejor de Lima ocupa la última plaza.
- **Régimen:** `data/metadata/enfen_eventos.csv`; un evento Y–Y+1 afecta la temporada de Y+1.

Pipeline (en la imagen `pp-g8`): `inventario.py` → `auditar.py` → `clasificar_regimenes.py`.
