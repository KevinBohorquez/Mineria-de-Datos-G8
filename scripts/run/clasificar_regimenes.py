"""T09 | Responsable: Angela.

Clasifica cada combinacion estacion/anio elegible (T08) como regimen "normal"
o "el_nino" usando la definicion operacional oficial del ENFEN (2012), sobre
el Indice Costero El Nino (ICEN) real descargado de met.igp.gob.pe, y la
escribe en data/processed/regimenes.csv.

Regla (ENFEN, Nota Tecnica "Definicion operacional de los eventos El Nino y
La Nina...", Lima, 9/4/2012, tabla 1 y seccion 3):
    - Categoria mensual "Calida" si ICEN > 0.4.
    - "Evento El Nino en la costa de Peru" = racha de >= 3 meses consecutivos
      en categoria Calida.
Un anio queda clasificado "el_nino" si alguno de sus meses de la temporada
enero-abril (D=120, ver docs/definicion-proyecto.docx 6.2) cae dentro de un
evento El Nino asi identificado; en caso contrario, "normal".

Fuente de datos: data/external/icen.txt (ICEN mensual 1950-2024, ENFEN 2024,
descargado el 2026-10-15 de http://met.igp.gob.pe/datos/ICEN.txt). Umbral
oficial: http://met.igp.gob.pe/elnino/enfen/ICEN-Nota_Tecnica.pdf

Uso:
    python scripts/run/clasificar_regimenes.py
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
AUDITORIA = RAIZ / "data" / "processed" / "auditoria_calidad.csv"
ICEN = RAIZ / "data" / "external" / "icen.txt"
SALIDA = RAIZ / "data" / "processed" / "regimenes.csv"

MESES_TEMPORADA = (1, 2, 3, 4)
UMBRAL_CALIDA = 0.4
MIN_MESES_EVENTO = 3
FUENTE = (
    "ENFEN (2012), Definicion operacional de los eventos El Nino y La Nina en la costa "
    "del Peru (ICEN > 0.4 durante >= 3 meses consecutivos); ICEN mensual 1950-2024 de "
    "met.igp.gob.pe/datos/ICEN.txt, consultado 2026-10-15"
)


def cargar_icen() -> dict[tuple[int, int], float]:
    valores: dict[tuple[int, int], float] = {}
    with ICEN.open(encoding="utf-8") as f:
        for linea in f:
            linea = linea.strip()
            if not linea or linea.startswith("%"):
                continue
            anio_s, mes_s, icen_s = linea.split()
            valores[(int(anio_s), int(mes_s))] = float(icen_s)
    return valores


def meses_en_evento_el_nino(icen: dict[tuple[int, int], float]) -> set[tuple[int, int]]:
    """Aplica la regla ENFEN: racha de >= 3 meses consecutivos con ICEN > 0.4."""
    meses_ordenados = sorted(icen)
    en_evento: set[tuple[int, int]] = set()
    racha: list[tuple[int, int]] = []

    def cerrar_racha():
        if len(racha) >= MIN_MESES_EVENTO:
            en_evento.update(racha)

    anterior = None
    for clave in meses_ordenados:
        anio, mes = clave
        consecutivo = anterior is not None and (
            (anio == anterior[0] and mes == anterior[1] + 1)
            or (anio == anterior[0] + 1 and anterior[1] == 12 and mes == 1)
        )
        if icen[clave] > UMBRAL_CALIDA:
            if consecutivo and racha:
                racha.append(clave)
            else:
                cerrar_racha()
                racha = [clave]
        else:
            cerrar_racha()
            racha = []
        anterior = clave
    cerrar_racha()
    return en_evento


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()

    if not AUDITORIA.exists():
        print(f"No existe {AUDITORIA}; ejecutar scripts/run/auditoria_datos.py primero.")
        return 2
    if not ICEN.exists():
        print(f"No existe {ICEN}; descargar met.igp.gob.pe/datos/ICEN.txt primero.")
        return 2

    icen = cargar_icen()
    meses_nino = meses_en_evento_el_nino(icen)

    with AUDITORIA.open(newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    salida_filas = []
    for fila in filas:
        if fila["elegible"] != "True":
            continue
        anio = int(fila["anio"])
        es_nino = any((anio, mes) in meses_nino for mes in MESES_TEMPORADA)
        regimen = "el_nino" if es_nino else "normal"
        salida_filas.append(
            {
                "estacion": fila["estacion"],
                "anio": anio,
                "regimen": regimen,
                "regla": "ICEN > 0.4 en >= 3 meses consecutivos (ENFEN 2012), evaluado en enero-abril",
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
