"""T06/T08 (apoyo): convierte un archivo de descarga oficial de SENAMHI
(formato `Anio Mes Dia Precipitacion TempMax TempMin`, separado por espacios,
`-99.9` = faltante) al formato interno `fecha,precipitacion_mm` que usan
auditoria_datos.py y calibrar.py.

El codigo de estacion se infiere del nombre del archivo que entrega el portal
de SENAMHI (`qc00000247.txt` -> id `000247`), salvo que se pase --id.

Uso:
    python scripts/run/importar_senamhi.py "C:/Users/Angela/Downloads/qc00000247.txt"
    python scripts/run/importar_senamhi.py ruta.txt --id 000247 --salida data/raw/000247.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
RAW_DIR = RAIZ / "data" / "raw"
FALTANTE = "-99.9"


def inferir_id(ruta: Path) -> str:
    m = re.search(r"(\d+)", ruta.stem)
    if not m:
        raise ValueError(f"No se pudo inferir el codigo de estacion de {ruta.name}; usar --id.")
    return m.group(1)


def convertir(ruta_entrada: Path) -> tuple[list[tuple[str, str]], dict]:
    filas: list[tuple[str, str]] = []
    n_faltantes = 0
    n_total = 0
    with ruta_entrada.open(encoding="utf-8", errors="replace") as f:
        for linea in f:
            partes = linea.split()
            if len(partes) < 4:
                continue
            anio, mes, dia, precip = partes[0], partes[1], partes[2], partes[3]
            fecha = f"{int(anio):04d}-{int(mes):02d}-{int(dia):02d}"
            n_total += 1
            if precip == FALTANTE:
                filas.append((fecha, ""))
                n_faltantes += 1
            else:
                valor = float(precip)
                if valor < 0:
                    # Dato invalido que no es el codigo de faltante: se trata
                    # como faltante y se deja constancia (no se inventa un valor).
                    filas.append((fecha, ""))
                    n_faltantes += 1
                else:
                    filas.append((fecha, f"{valor:.2f}"))
    stats = {
        "n_total": n_total,
        "n_faltantes": n_faltantes,
        "pct_faltantes": (n_faltantes / n_total * 100) if n_total else 0.0,
        "fecha_inicio": filas[0][0] if filas else None,
        "fecha_fin": filas[-1][0] if filas else None,
    }
    return filas, stats


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("entrada", type=Path, help="Archivo .txt descargado del portal de SENAMHI.")
    parser.add_argument("--id", dest="id_estacion", default=None, help="Codigo de estacion (por defecto, se infiere del nombre del archivo).")
    parser.add_argument("--salida", type=Path, default=None, help="Ruta de salida (por defecto data/raw/<id>.csv).")
    args = parser.parse_args()

    if not args.entrada.exists():
        print(f"No existe {args.entrada}")
        return 2

    id_estacion = args.id_estacion or inferir_id(args.entrada)
    salida = args.salida or (RAW_DIR / f"{id_estacion}.csv")

    filas, stats = convertir(args.entrada)
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", newline="", encoding="utf-8") as out:
        escritor = csv.writer(out)
        escritor.writerow(["fecha", "precipitacion_mm"])
        escritor.writerows(filas)

    print(f"Estacion {id_estacion}: {stats['n_total']} dias ({stats['fecha_inicio']} a {stats['fecha_fin']})")
    print(f"Faltantes: {stats['n_faltantes']} ({stats['pct_faltantes']:.2f}%)")
    print(f"Escrito en {salida.relative_to(RAIZ)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
