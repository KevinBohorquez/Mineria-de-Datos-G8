#!/usr/bin/env python3
"""T10 | Genera config/<estacion>_<regimen>.yaml a partir de data/processed/parametros.csv.

Cada YAML usa las claves planas `clave: valor` que lee cargar_archivo_configuracion() en
src/io/configuracion.cpp: estacion, regimen, p01, p11, alfa, theta salen de parametros.csv y el resto
de claves no calibradas (semilla, n, dias, capacidad, umbral, ...) se copian de la plantilla
(config/sintetico.yaml por defecto). config_id se asigna 0, 1, 2, ... en el orden de parametros.csv para
que el índice global c*N + j no se repita entre configuraciones.

Las filas con NaN o fuera de rango (las mismas reglas que validar() de configuracion.cpp: p01 y p11 en
[0,1], alfa > 0, theta > 0) se omiten y se informa por salida estándar. Cada archivo lleva en la
cabecera el CSV de origen y el commit de git.

Uso:
  python3 scripts/run/generar_configs.py --parametros data/processed/parametros.csv \\
      --plantilla config/sintetico.yaml --salida-dir config
"""
import argparse
import csv
import math
import re
import subprocess
import sys
import unicodedata
from pathlib import Path

CALIBRADAS = ("p01", "p11", "alfa", "theta")
# Claves que asignar() de configuracion.cpp acepta; cualquier otra haría fallar la carga.
CLAVES_CONTRATO = {
    "backend", "estacion", "regimen", "config_id", "semilla", "n", "hilos", "schedule", "salida",
    "lote", "repeticion", "p01", "p11", "alfa", "theta", "capacidad", "umbral", "dias",
}


def leer_plantilla(ruta):
    """Pares clave/valor con la misma regla que el lector C++: se descarta desde '#', 'clave: valor'."""
    pares = {}
    for num, linea in enumerate(Path(ruta).read_text(encoding="utf-8").splitlines(), 1):
        linea = linea.split("#", 1)[0].strip()
        if not linea:
            continue
        if ":" not in linea:
            raise ValueError(f"{ruta}:{num}: se esperaba 'clave: valor'")
        k, v = linea.split(":", 1)
        k, v = k.strip(), v.strip()
        if k not in CLAVES_CONTRATO:
            raise ValueError(f"{ruta}:{num}: clave desconocida '{k}'")
        pares[k] = v
    return pares


def validar_parametros(p):
    """Mismas reglas de rango que validar() en src/io/configuracion.cpp; NaN no pasa ninguna."""
    if not (0.0 <= p["p01"] <= 1.0 and 0.0 <= p["p11"] <= 1.0):
        raise ValueError("p01 y p11 deben estar en [0,1]")
    if not (p["alfa"] > 0.0 and p["theta"] > 0.0):
        raise ValueError("alfa y theta deben ser > 0")


def nombre_archivo(estacion, regimen):
    """Nombre seguro: minúsculas ASCII, [a-z0-9_]."""
    base = unicodedata.normalize("NFKD", f"{estacion}_{regimen}").encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "_", base.lower()).strip("_") + ".yaml"


def commit_actual():
    try:
        r = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=10)
        return r.stdout.strip() if r.returncode == 0 and r.stdout.strip() else "desconocido"
    except (OSError, subprocess.SubprocessError):
        return "desconocido"


def _texto(v):
    return repr(v) if isinstance(v, float) else str(v)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Genera YAML por estación y régimen desde parametros.csv (T10).")
    ap.add_argument("--parametros", default="data/processed/parametros.csv")
    ap.add_argument("--plantilla", default="config/sintetico.yaml")
    ap.add_argument("--salida-dir", default="config")
    ap.add_argument("--commit", default=None, help="commit a registrar (por defecto: git rev-parse HEAD)")
    a = ap.parse_args(argv)

    plantilla = leer_plantilla(a.plantilla)
    commit = a.commit or commit_actual()
    destino = Path(a.salida_dir)
    destino.mkdir(parents=True, exist_ok=True)

    with open(a.parametros, newline="", encoding="utf-8") as f:
        filas = list(csv.DictReader(f))

    escritos, omitidos, config_id = 0, 0, 0
    for fila in filas:
        est, reg = fila["estacion"].strip(), fila["regimen"].strip()
        if "#" in est or "#" in reg:
            print(f"omitida {est}/{reg}: '#' no es válido en el formato de configuración")
            omitidos += 1
            continue
        try:
            p = {k: float(fila[k]) for k in CALIBRADAS}
            if any(math.isnan(v) for v in p.values()):
                raise ValueError("parámetro NaN")
            validar_parametros(p)
        except (KeyError, ValueError) as e:
            print(f"omitida {est}/{reg}: {e}")
            omitidos += 1
            continue

        valores = dict(plantilla)
        valores.update({"estacion": est, "regimen": reg, "config_id": str(config_id)})
        valores.update({k: _texto(v) for k, v in p.items()})
        valores.pop("salida", None)  # la ruta de salida la decide cada corrida
        avisos = [k for k in ("muestra_insuficiente", "muestra_pequena") if fila.get(k, "0").strip() == "1"]
        cabecera = [
            f"# T10 | Configuración calibrada: {est} / {reg}.",
            f"# Generado por scripts/run/generar_configs.py desde {a.parametros} (commit {commit}).",
            f"# Claves no calibradas copiadas de {a.plantilla}.",
        ]
        if avisos:
            cabecera.append(f"# ADVERTENCIA: {', '.join(avisos)} (n_temporadas = {fila.get('n_temporadas', '?')}).")
        orden = ["estacion", "regimen", "config_id", "semilla", "n", "dias", *CALIBRADAS, "capacidad", "umbral"]
        claves = [k for k in orden if k in valores] + sorted(k for k in valores if k not in orden)
        texto = "\n".join(cabecera + [f"{k}: {valores[k]}" for k in claves]) + "\n"
        (destino / nombre_archivo(est, reg)).write_text(texto, encoding="utf-8")
        escritos += 1
        config_id += 1
        if avisos:
            print(f"aviso {est}/{reg}: {', '.join(avisos)}")

    print(f"escritos {escritos} YAML en {destino}; omitidas {omitidos} filas (NaN o fuera de rango)")
    return 0 if escritos else 1


if __name__ == "__main__":
    sys.exit(main())
