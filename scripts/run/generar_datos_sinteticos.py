"""T06/T08 (respaldo): genera series diarias sinteticas que imitan la descarga
de SENAMHI, para usar solo si alguna estacion real deja de estar disponible.

Las 8 estaciones de data/metadata/inventario_senamhi.csv ya se descargaron
reales del portal de SENAMHI (ver importar_senamhi.py); este generador no se
usa en la corrida vigente. Simula un proceso Markov humedo/seco + monto gamma,
igual al modelo del proyecto, con parametros "verdaderos" distintos por
regimen (normal vs El Nino) y una semilla fija por estacion, e inyecta huecos,
duplicados y valores negativos deliberados para probar T08. Resultado:
data/raw/<id_estacion>.csv (fuera de Git, ver .gitignore) con columnas
fecha,precipitacion_mm.

Uso:
    python scripts/run/generar_datos_sinteticos.py
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import math
import random
import zlib
from pathlib import Path


def hash_estable(texto: str) -> int:
    """hash() de Python varia entre ejecuciones (PYTHONHASHSEED aleatorio);
    crc32 es determinista entre corridas, maquinas y versiones de Python."""
    return zlib.crc32(texto.encode("utf-8"))

RAIZ = Path(__file__).resolve().parents[2]
INVENTARIO = RAIZ / "data" / "metadata" / "inventario_senamhi.csv"
SALIDA_DIR = RAIZ / "data" / "raw"

# Anios clasificados como El Nino (DJF, umbral ONI >= 0.5 o El Nino costero
# declarado por ENFEN). Lista simplificada de referencia publica, usada aqui
# como insumo hipotetico de calibracion, no como fuente oficial verificada.
ANIOS_EL_NINO = {
    1994, 1997, 1998, 2002, 2004, 2006, 2009, 2014, 2015, 2016, 2017, 2018, 2023, 2024,
}

PARAMS_VERDADEROS = {
    "normal": {"p01": 0.10, "p11": 0.45, "alfa": 0.55, "theta": 5.5},
    "el_nino": {"p01": 0.22, "p11": 0.68, "alfa": 0.85, "theta": 11.0},
}


def regimen_de(anio: int) -> str:
    return "el_nino" if anio in ANIOS_EL_NINO else "normal"


def generar_serie(id_estacion: str, fecha_inicio: dt.date, fecha_fin: dt.date, semilla: int) -> list[tuple[str, str]]:
    rng = random.Random(semilla)
    filas: list[tuple[str, str]] = []
    llovio_ayer = False
    fecha = fecha_inicio
    while fecha <= fecha_fin:
        parametros = PARAMS_VERDADEROS[regimen_de(fecha.year)]
        p = parametros["p11"] if llovio_ayer else parametros["p01"]
        llueve = rng.random() < p
        if llueve:
            monto = rng.gammavariate(parametros["alfa"], parametros["theta"])
            valor = f"{monto:.1f}"
        else:
            valor = "0.0"
        filas.append((fecha.isoformat(), valor))
        llovio_ayer = llueve
        fecha += dt.timedelta(days=1)

    # Defectos deliberados para que T08 los detecte (no se simula un año
    # perfecto: SENAMHI real tiene vacios de mantenimiento de sensores).
    rng_defectos = random.Random(semilla ^ 0x5EED)
    n = len(filas)
    n_huecos = max(1, int(n * 0.03))
    indices_huecos = set(rng_defectos.sample(range(n), n_huecos))
    filas = [(f, "") if i in indices_huecos else (f, v) for i, (f, v) in enumerate(filas)]

    # Un par de valores negativos (error de sensor) y una fecha duplicada.
    if n > 100:
        i_neg = rng_defectos.randrange(50, n - 50)
        fecha_i, _ = filas[i_neg]
        filas[i_neg] = (fecha_i, "-1.0")
        i_dup = rng_defectos.randrange(50, n - 50)
        filas.insert(i_dup, filas[i_dup])

    return filas


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--semilla", type=int, default=20261015, help="Semilla base (se combina con cada estacion).")
    args = parser.parse_args()

    if not INVENTARIO.exists():
        print(f"No existe {INVENTARIO}; ejecutar T06 primero.")
        return 2

    SALIDA_DIR.mkdir(parents=True, exist_ok=True)
    with INVENTARIO.open(newline="", encoding="utf-8") as f:
        lector = csv.DictReader(f)
        estaciones = list(lector)

    for fila in estaciones:
        id_est = fila["id_estacion"]
        inicio = dt.date.fromisoformat(fila["fecha_inicio"])
        fin = dt.date.fromisoformat(fila["fecha_fin"])
        semilla_estacion = args.semilla ^ hash_estable(id_est)
        serie = generar_serie(id_est, inicio, fin, semilla_estacion)
        ruta = SALIDA_DIR / f"{id_est}.csv"
        with ruta.open("w", newline="", encoding="utf-8") as out:
            escritor = csv.writer(out)
            escritor.writerow(["fecha", "precipitacion_mm"])
            escritor.writerows(serie)
        print(f"{id_est}: {len(serie)} filas -> {ruta.relative_to(RAIZ)}")

    print("Datos sinteticos generados. Son hipoteticos: sustituir por la descarga real de SENAMHI cuando este disponible.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
