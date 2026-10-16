"""T08 | Auditoría de calidad por estación y temporada enero–abril, y selección de estaciones.

Lee data/raw/*.csv y data/metadata/inventario_senamhi.csv (salida de inventario.py) y escribe:

- data/processed/auditoria_calidad.csv: una fila por estación × temporada completa en el rango,
  con faltantes, duplicados, negativos, atípicos > 150 mm, trazas y elegibilidad (< 10 %).
- data/processed/estaciones_seleccionadas.csv: hasta 5 estaciones con >= 20 temporadas
  elegibles y menor % faltante enero–abril (regla en datos_comunes.seleccionar_estaciones).

Uso:   python3 scripts/run/auditar.py
"""
import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comunes as dc  # noqa: E402

COLUMNAS = ["estacion", "temporada", "dias_esperados", "dias_observados", "faltantes",
            "pct_faltante", "duplicados", "negativos", "atipicos_gt_150mm", "trazas",
            "elegible", "motivo"]
COLUMNAS_SELECCION = ["estacion", "archivo", "region", "pct_faltante_ene_abr",
                      "temporadas_elegibles", "motivo_seleccion"]


def auditar_estacion(estacion, serie):
    """Una fila (dict) por temporada enero–abril completa dentro del rango de la serie."""
    indice = dc.primera_aparicion(serie)
    filas_por_fecha = Counter(f for f, _ in serie)
    negativos_por_fecha = Counter(f for f, mm in serie if mm is not None and mm < 0)
    salida = []
    for anio in dc.anios_temporada_completos(serie):
        temporada = dc.temporada_ene_abr(serie, anio, indice)
        fechas = [f for f, _ in temporada]
        falt = dc.faltantes(temporada)
        pct = dc.pct_faltante(temporada)
        elegible = dc.temporada_elegible(temporada)
        salida.append({
            "estacion": estacion,
            "temporada": anio,
            "dias_esperados": dc.DIAS_TEMPORADA,
            "dias_observados": dc.DIAS_TEMPORADA - falt,
            "faltantes": falt,
            "pct_faltante": round(pct, 2),
            "duplicados": sum(max(filas_por_fecha[f] - 1, 0) for f in fechas),
            "negativos": sum(negativos_por_fecha[f] for f in fechas),
            "atipicos_gt_150mm": sum(1 for _, mm in temporada
                                     if mm is not None and mm > dc.UMBRAL_ATIPICO_MM),
            "trazas": sum(1 for _, mm in temporada if dc.es_traza(mm)),
            "elegible": int(elegible),
            "motivo": "ok" if elegible else
                      f"faltantes {pct:.1f}% >= {dc.MAX_PCT_FALTANTE:.0f}%",
        })
    return salida


def fechas_ausentes(serie, anio):
    """Días de la temporada sin ninguna fila en el archivo (huecos de fecha)."""
    presentes = {f for f, _ in serie}
    return sum(1 for f in dc.fechas_temporada(anio) if f not in presentes)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", default=str(dc.DIR_RAW))
    ap.add_argument("--inventario", default=str(dc.DIR_METADATOS / "inventario_senamhi.csv"))
    ap.add_argument("--salida", default=str(dc.DIR_PROCESADOS / "auditoria_calidad.csv"))
    ap.add_argument("--seleccion",
                    default=str(dc.DIR_PROCESADOS / "estaciones_seleccionadas.csv"))
    args = ap.parse_args()

    inventario = {f["estacion"]: f for f in dc.leer_csv(args.inventario)}
    auditoria, candidatas = [], []
    print("estacion                 temporadas elegibles huecos_fecha dup neg atip>150 trazas")
    for ruta in sorted(Path(args.raw).glob("*.csv")):
        estacion = ruta.stem
        serie = dc.leer_serie(ruta)
        filas = auditar_estacion(estacion, serie)
        auditoria.extend(filas)
        elegibles = sum(f["elegible"] for f in filas)
        huecos = sum(fechas_ausentes(serie, f["temporada"]) for f in filas)
        print(f"{estacion:24s} {len(filas):10d} {elegibles:9d} {huecos:12d} "
              f"{sum(f['duplicados'] for f in filas):3d} {sum(f['negativos'] for f in filas):3d} "
              f"{sum(f['atipicos_gt_150mm'] for f in filas):8d} "
              f"{sum(f['trazas'] for f in filas):6d}")
        inv = inventario[estacion]
        candidatas.append({"estacion": estacion, "archivo": inv["archivo"],
                           "region": inv["region"],
                           "pct_faltante_ene_abr": float(inv["pct_faltante_ene_abr"]),
                           "temporadas_elegibles": elegibles})

    dc.escribir_csv(args.salida, COLUMNAS, auditoria)
    seleccion = dc.seleccionar_estaciones(candidatas)
    dc.escribir_csv(args.seleccion, COLUMNAS_SELECCION, [
        {**{k: c[k] for k in COLUMNAS_SELECCION[:-1]},
         "pct_faltante_ene_abr": f"{c['pct_faltante_ene_abr']:.2f}",
         "motivo_seleccion": motivo}
        for c, motivo in seleccion])
    print(f"escrito {args.salida} ({len(auditoria)} filas)")
    print("seleccionadas: " + ", ".join(
        f"{c['estacion']} ({c['pct_faltante_ene_abr']:.2f}%, {c['temporadas_elegibles']} temp.)"
        for c, _ in seleccion))
    descartadas = [c for c in candidatas if c["temporadas_elegibles"] < dc.MIN_TEMPORADAS_ELEGIBLES]
    for c in descartadas:
        print(f"no califica: {c['estacion']} ({c['temporadas_elegibles']} temporadas elegibles "
              f"< {dc.MIN_TEMPORADAS_ELEGIBLES})")


if __name__ == "__main__":
    main()
