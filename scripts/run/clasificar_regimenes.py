"""T09 | Responsable: Angela.

Clasifica cada combinacion estacion/anio elegible (T08) como regimen "normal"
o "el_nino" usando una lista de referencia tipo ENFEN/ONI (ver nota de fuente
abajo) y la escribe en data/processed/regimenes.csv.

Regla de clasificacion (fija y reproducible): un anio es "el_nino" si su
diciembre-enero-febrero quedo dentro de un episodio El Nino segun el indice
ONI (umbral +0.5 o superior) o si ENFEN declaro El Nino costero en ese anio;
en caso contrario es "normal". Anios ambiguos (el evento cruza el cambio de
anio) se asignan al anio en que ocurre la temporada de lluvias de la costa
norte de Peru (enero-abril), que es la ventana que usa este proyecto.

Uso:
    python scripts/run/clasificar_regimenes.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AUDITORIA = RAIZ / "data" / "processed" / "auditoria_calidad.csv"
SALIDA = RAIZ / "data" / "processed" / "regimenes.csv"

# Misma lista que generar_datos_sinteticos.py (debe mantenerse igual: es la
# "verdad" con la que se generaron los datos sinteticos y la regla con la que
# T10 debe recuperar parametros distintos por regimen).
ANIOS_EL_NINO = {
    1994, 1997, 1998, 2002, 2004, 2006, 2009, 2014, 2015, 2016, 2017, 2018, 2023, 2024,
}
FUENTE = "ENFEN/ONI (umbral DJF >= 0.5), referencia hipotetica consolidada para este proyecto el 2026-10-01"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    if not AUDITORIA.exists():
        print(f"No existe {AUDITORIA}; ejecutar scripts/run/auditoria_datos.py primero.")
        return 2

    with AUDITORIA.open(newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    salida_filas = []
    for fila in filas:
        if fila["elegible"] != "True":
            continue
        anio = int(fila["anio"])
        regimen = "el_nino" if anio in ANIOS_EL_NINO else "normal"
        salida_filas.append(
            {
                "estacion": fila["estacion"],
                "anio": anio,
                "regimen": regimen,
                "regla": "anio in ANIOS_EL_NINO (ONI DJF >= 0.5 o El Nino costero declarado)",
                "fuente": FUENTE,
            }
        )

    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with SALIDA.open("w", newline="", encoding="utf-8") as out:
        escritor = csv.DictWriter(out, fieldnames=["estacion", "anio", "regimen", "regla", "fuente"])
        escritor.writeheader()
        escritor.writerows(salida_filas)

    n_normal = sum(1 for f in salida_filas if f["regimen"] == "normal")
    n_nino = sum(1 for f in salida_filas if f["regimen"] == "el_nino")
    print(f"{SALIDA.relative_to(RAIZ)}: {len(salida_filas)} filas ({n_normal} normal, {n_nino} el_nino)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
