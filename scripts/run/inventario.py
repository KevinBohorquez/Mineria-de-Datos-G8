"""T06 | Inventario de las series diarias SENAMHI de data/raw/.

Escribe data/metadata/inventario_senamhi.csv con una fila por estación: rango de fechas, días
faltantes (fecha sin fila, vacío, no numérico o negativo), % faltante total y en la temporada
enero–abril, temporadas enero–abril completas en el rango, máximo diario y número de trazas.

Uso:   python3 scripts/run/inventario.py [--raw data/raw] [--salida data/metadata/inventario_senamhi.csv]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comunes as dc  # noqa: E402

COLUMNAS = ["estacion", "archivo", "region", "fecha_inicio", "fecha_fin", "n_dias",
            "n_faltantes", "pct_faltante_total", "pct_faltante_ene_abr", "temporadas_ene_abr",
            "max_mm", "fecha_max", "n_trazas"]


def inventariar(estacion, archivo, serie):
    indice = dc.primera_aparicion(serie)
    inicio, fin = min(indice), max(indice)
    n_dias = (fin - inicio).days + 1
    validos = {f: mm for f, mm in indice.items() if dc.valor_valido(mm)}
    n_faltantes = n_dias - len(validos)
    anios = dc.anios_temporada_completos(serie)
    falt_temp = sum(dc.faltantes(dc.temporada_ene_abr(serie, a, indice)) for a in anios)
    dias_temp = dc.DIAS_TEMPORADA * len(anios)
    fecha_max = max(validos, key=lambda f: (validos[f], -f.toordinal())) if validos else None
    return {
        "estacion": estacion,
        "archivo": archivo,
        "region": dc.region_de(estacion),
        "fecha_inicio": inicio.isoformat(),
        "fecha_fin": fin.isoformat(),
        "n_dias": n_dias,
        "n_faltantes": n_faltantes,
        "pct_faltante_total": f"{100.0 * n_faltantes / n_dias:.2f}",
        "pct_faltante_ene_abr": f"{100.0 * falt_temp / dias_temp:.2f}" if dias_temp else "100.00",
        "temporadas_ene_abr": len(anios),
        "max_mm": f"{validos[fecha_max]:.2f}" if fecha_max else "",
        "fecha_max": fecha_max.isoformat() if fecha_max else "",
        "n_trazas": sum(1 for mm in validos.values() if dc.es_traza(mm)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--raw", default=str(dc.DIR_RAW))
    ap.add_argument("--salida", default=str(dc.DIR_METADATOS / "inventario_senamhi.csv"))
    args = ap.parse_args()
    archivos = sorted(Path(args.raw).glob("*.csv"))
    if not archivos:
        sys.exit(f"no hay CSV en {args.raw}")
    filas = []
    for ruta in archivos:
        filas.append(inventariar(ruta.stem, f"data/raw/{ruta.name}", dc.leer_serie(ruta)))
    dc.escribir_csv(args.salida, COLUMNAS, filas)
    for f in filas:
        print(f"{f['estacion']:24s} {f['fecha_inicio']}..{f['fecha_fin']} "
              f"falt_total={f['pct_faltante_total']}% falt_ene_abr={f['pct_faltante_ene_abr']}% "
              f"temporadas={f['temporadas_ene_abr']} max={f['max_mm']} ({f['fecha_max']})")
    print(f"escrito {args.salida} ({len(filas)} estaciones)")


if __name__ == "__main__":
    main()
