"""T09 | Clasifica cada temporada elegible de las estaciones seleccionadas en `normal` o `el_nino`.

Eventos: data/metadata/enfen_eventos.csv (solo los citados en docs/definicion-proyecto.docx:
1982–83, 1997–98 y el Niño costero 2017). Un evento Y–Y+1 afecta la temporada enero–abril de
Y+1. Toda temporada no listada es `normal`. Agregar eventos exige una fuente oficial ENFEN/ICEN.

Lee data/processed/auditoria_calidad.csv y data/processed/estaciones_seleccionadas.csv
(salidas de auditar.py) y escribe data/processed/regimenes.csv.

Uso:   python3 scripts/run/clasificar_regimenes.py
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import datos_comunes as dc  # noqa: E402

COLUMNAS = ["estacion", "temporada", "regimen", "regla", "fuente"]
FUENTE_NORMAL = "docs/definicion-proyecto.docx (eventos citados)"


def indexar_eventos(eventos):
    """temporada -> fila del evento; verifica que temporada_afectada siga la regla Y-Y+1 -> Y+1."""
    indice = {}
    for e in eventos:
        temporada = int(e["temporada_afectada"])
        if temporada != dc.temporada_de_evento(e["evento"]):
            raise ValueError(f"evento {e['evento']}: temporada_afectada {temporada} no sigue la regla")
        indice[temporada] = e
    return indice


def clasificar(auditoria, estaciones, eventos):
    """Filas de regimenes.csv para las temporadas elegibles de `estaciones`, ordenadas."""
    por_temporada = indexar_eventos(eventos)
    seleccion = set(estaciones)
    filas = []
    for a in auditoria:
        if a["estacion"] not in seleccion or int(a["elegible"]) != 1:
            continue
        anio = int(a["temporada"])
        regimen = dc.clasificar_temporada(anio, por_temporada)
        if regimen == "el_nino":
            e = por_temporada[anio]
            regla, fuente = f"evento El Niño {e['evento']} -> temporada {anio}", e["fuente"]
        else:
            regla, fuente = "sin evento El Niño citado para la temporada", FUENTE_NORMAL
        filas.append({"estacion": a["estacion"], "temporada": anio, "regimen": regimen,
                      "regla": regla, "fuente": fuente})
    filas.sort(key=lambda f: (f["estacion"], f["temporada"]))
    return filas


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--auditoria", default=str(dc.DIR_PROCESADOS / "auditoria_calidad.csv"))
    ap.add_argument("--seleccion", default=str(dc.DIR_PROCESADOS / "estaciones_seleccionadas.csv"))
    ap.add_argument("--eventos", default=str(dc.DIR_METADATOS / "enfen_eventos.csv"))
    ap.add_argument("--salida", default=str(dc.DIR_PROCESADOS / "regimenes.csv"))
    args = ap.parse_args()
    estaciones = [f["estacion"] for f in dc.leer_csv(args.seleccion)]
    filas = clasificar(dc.leer_csv(args.auditoria), estaciones, dc.leer_csv(args.eventos))
    dc.escribir_csv(args.salida, COLUMNAS, filas)
    for est in estaciones:
        propias = [f for f in filas if f["estacion"] == est]
        nino = [f["temporada"] for f in propias if f["regimen"] == "el_nino"]
        print(f"{est:24s} normal={len(propias) - len(nino):3d} el_nino={len(nino)} {nino}")
    print(f"escrito {args.salida} ({len(filas)} filas)")


if __name__ == "__main__":
    main()
