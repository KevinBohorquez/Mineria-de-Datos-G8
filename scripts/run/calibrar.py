#!/usr/bin/env python3
"""T10 | Calibración de la cadena de Markov de ocurrencia y de la gamma de montos por estación y régimen.

Método (docs/definicion-proyecto.docx §7.6):
  * Solo temporadas elegibles (auditoria_calidad.csv, elegible = 1) de las estaciones seleccionadas.
    Temporada = 1 de enero a 30 de abril sin el 29 de febrero (D = 120; 28-feb y 1-mar consecutivos).
  * Día lluvioso: precipitación >= 0,1 mm; valores en (0; 0,1) son trazas y cuentan como secos.
    Días faltantes (celda vacía, fecha ausente o valor negativo) se excluyen.
  * p01 = n01 / n0·  y  p11 = n11 / n1·, contando transiciones solo entre días calendario consecutivos
    de la misma temporada y omitiendo toda transición que toque un día faltante.
  * Gamma por el estimador de Thom sobre los montos de días lluviosos:
        A = ln(media) - media(ln x);  alfa = (1 + sqrt(1 + 4A/3)) / (4A);  theta = media / alfa.
    Si hay menos de 2 días lluviosos o A <= 0, alfa = theta = NaN y gamma_invalida = 1.
  * Banderas: muestra_insuficiente = 1 si n_temporadas < 2; muestra_pequena = 1 si n_temporadas < 5.
  * Bootstrap: R réplicas por estación × régimen remuestreando TEMPORADAS con reemplazo (mismo número que
    las disponibles) y recalculando p01, p11, alfa y theta sobre las temporadas remuestreadas agrupadas.
    Semilla de cada réplica: SeedSequence(semilla_maestra, spawn_key=(crc32("estacion|regimen"), replica))
    reducida a un entero de 64 bits; ese entero reproduce por sí solo la réplica (remuestrear()).
    La misma semilla maestra produce CSV idénticos byte a byte.

Entradas (producidas por T06/T08/T09): data/raw/<estacion>.csv, data/processed/estaciones_seleccionadas.csv,
data/processed/auditoria_calidad.csv y data/processed/regimenes.csv.
Salidas: <salida-dir>/parametros.csv y <salida-dir>/bootstrap_parametros.csv.

Nota: leer_serie(), temporada_ene_abr() y es_lluvioso() vienen de scripts/run/datos_comunes.py (T06)
cuando está junto a este script; si falta, se usan copias privadas con la misma semántica que deben
deduplicarse al integrar.

Uso:
  python3 scripts/run/calibrar.py --raw-dir data/raw --seleccion data/processed/estaciones_seleccionadas.csv \\
      --auditoria data/processed/auditoria_calidad.csv --regimenes data/processed/regimenes.csv \\
      --salida-dir data/processed --semilla 20261015 --replicas 100
"""
import argparse
import csv
import math
import re
import sys
import zlib
from datetime import date, timedelta
from pathlib import Path

import numpy as np

SEMILLA_POR_DEFECTO = 20261015
REPLICAS_POR_DEFECTO = 100

COLUMNAS_PARAMETROS = [
    "estacion", "regimen", "n_temporadas", "temporadas", "n_dias", "n_lluvia",
    "n00", "n01", "n10", "n11", "p01", "p11", "alfa", "theta",
    "gamma_invalida", "muestra_insuficiente", "muestra_pequena",
]
COLUMNAS_BOOTSTRAP = ["estacion", "regimen", "replica", "semilla", "temporadas_muestreadas",
                      "p01", "p11", "alfa", "theta"]


# ---------------------------------------------------------------- lectura y temporada
# Contrato de scripts/run/datos_comunes.py (T06): si el módulo está junto a este script se usa tal cual;
# si no, se usan las copias privadas de abajo, con la misma semántica (deduplicar al integrar).

def _es_lluvioso(mm):
    """Día lluvioso: precipitación >= 0,1 mm. Trazas, ceros y faltantes no lo son."""
    return mm is not None and mm >= _UMBRAL_LLUVIA_MM


def _a_valor(texto):
    texto = (texto or "").strip()
    if not texto:
        return None
    try:
        return float(texto)
    except ValueError:
        return None


def _leer_serie(ruta):
    """Lee `fecha,precipitacion_mm` -> [(date, float|None)]; vacío o no numérico = None."""
    with open(ruta, newline="", encoding="utf-8") as f:
        return [(date.fromisoformat(r["fecha"].strip()), _a_valor(r.get("precipitacion_mm")))
                for r in csv.DictReader(f)]


def _temporada_ene_abr(serie, anio, indice=None):
    """[(date, float|None)] con los 120 días 1-ene..30-abr sin el 29-feb; sin fila o negativo = None.

    Con fechas duplicadas manda la primera fila. El 28-feb y el 1-mar quedan consecutivos.
    """
    if indice is None:
        indice = {}
        for f, mm in serie:
            indice.setdefault(f, mm)
    salida, dia = [], date(anio, 1, 1)
    while dia <= date(anio, 4, 30):
        if not (dia.month == 2 and dia.day == 29):
            mm = indice.get(dia)
            salida.append((dia, mm if mm is not None and mm >= 0.0 else None))
        dia += timedelta(days=1)
    return salida


_UMBRAL_LLUVIA_MM = 0.1
sys.path.insert(0, str(Path(__file__).resolve().parent))
try:
    from datos_comunes import UMBRAL_LLUVIA_MM, es_lluvioso, leer_serie, temporada_ene_abr
except ImportError:
    UMBRAL_LLUVIA_MM = _UMBRAL_LLUVIA_MM
    es_lluvioso, leer_serie, temporada_ene_abr = _es_lluvioso, _leer_serie, _temporada_ene_abr
finally:
    sys.path.pop(0)


# ---------------------------------------------------------------- estadísticos

def contar_transiciones(temporadas):
    """(n00, n01, n10, n11) entre días consecutivos de cada temporada, sin cruzar temporadas ni faltantes."""
    n = [[0, 0], [0, 0]]
    for t in temporadas:
        for ayer, hoy in zip(t, t[1:]):
            if ayer is None or hoy is None:
                continue
            n[int(es_lluvioso(ayer))][int(es_lluvioso(hoy))] += 1
    return n[0][0], n[0][1], n[1][0], n[1][1]


def ajustar_gamma_thom(montos):
    """Estimador de Thom. Devuelve (alfa, theta, valido); NaN si hay < 2 montos o A <= 0."""
    x = [float(m) for m in montos]
    if len(x) < 2:
        return math.nan, math.nan, False
    media = sum(x) / len(x)
    a = math.log(media) - sum(math.log(v) for v in x) / len(x)
    if not a > 1e-12:
        return math.nan, math.nan, False
    alfa = (1.0 + math.sqrt(1.0 + 4.0 * a / 3.0)) / (4.0 * a)
    return alfa, media / alfa, True


def _cociente(num, den):
    return num / den if den > 0 else math.nan


def estadisticos(temporadas):
    """p01, p11, alfa, theta y conteos sobre un conjunto de temporadas (lista de listas de float|None)."""
    n00, n01, n10, n11 = contar_transiciones(temporadas)
    observados = [v for t in temporadas for v in t if v is not None]
    montos = [v for v in observados if es_lluvioso(v)]
    alfa, theta, valido = ajustar_gamma_thom(montos)
    return {
        "n_dias": len(observados), "n_lluvia": len(montos),
        "n00": n00, "n01": n01, "n10": n10, "n11": n11,
        "p01": _cociente(n01, n00 + n01), "p11": _cociente(n11, n10 + n11),
        "alfa": alfa, "theta": theta, "gamma_invalida": 0 if valido else 1,
    }


# ---------------------------------------------------------------- carga de insumos

def _anio(texto):
    m = re.search(r"\d{4}", str(texto))
    if not m:
        raise ValueError(f"temporada sin año reconocible: {texto!r}")
    return int(m.group(0))


def _verdadero(texto):
    return str(texto).strip().lower() in {"1", "true", "si", "sí", "yes"}


def _leer_csv(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def cargar_grupos(raw_dir, seleccion, auditoria, regimenes, leer=leer_serie):
    """{(estacion, regimen): {anio: temporada}} solo con temporadas elegibles de estaciones seleccionadas."""
    archivos = {}
    for fila in _leer_csv(seleccion):
        est = fila["estacion"].strip()
        nombre = Path((fila.get("archivo") or "").strip() or f"{est}.csv").name
        archivos[est] = Path(raw_dir) / nombre
    elegibles = {(f["estacion"].strip(), _anio(f["temporada"]))
                 for f in _leer_csv(auditoria) if _verdadero(f["elegible"])}
    regimen = {}
    for f in _leer_csv(regimenes):
        clave = (f["estacion"].strip(), _anio(f["temporada"]))
        regimen[clave] = f["regimen"].strip()

    grupos = {}
    for est in sorted(archivos):
        anios = sorted(a for (e, a) in elegibles if e == est)
        if not anios:
            continue
        serie = leer(archivos[est])
        for anio in anios:
            reg = regimen.get((est, anio))
            if reg is None:
                print(f"aviso: {est} {anio} elegible sin régimen en regimenes.csv; se omite", file=sys.stderr)
                continue
            grupos.setdefault((est, reg), {})[anio] = [mm for _, mm in temporada_ene_abr(serie, anio)]
    return grupos


# ---------------------------------------------------------------- calibración y bootstrap

def calibrar(grupos):
    filas = []
    for (est, reg) in sorted(grupos):
        por_anio = grupos[(est, reg)]
        anios = sorted(por_anio)
        e = estadisticos([por_anio[a] for a in anios])
        filas.append({"estacion": est, "regimen": reg, "n_temporadas": len(anios),
                      "temporadas": ";".join(str(a) for a in anios), **e,
                      "muestra_insuficiente": int(len(anios) < 2), "muestra_pequena": int(len(anios) < 5)})
    return filas


def semilla_replica(semilla_maestra, estacion, regimen, replica):
    """Entero de 64 bits derivado de forma estable de (semilla maestra, grupo, réplica)."""
    grupo = zlib.crc32(f"{estacion}|{regimen}".encode("utf-8"))
    ss = np.random.SeedSequence(semilla_maestra, spawn_key=(grupo, replica))
    return int(ss.generate_state(1, dtype=np.uint64)[0])


def remuestrear(anios, semilla):
    """Remuestreo con reemplazo de len(anios) temporadas (anios en orden ascendente)."""
    anios = sorted(anios)
    rng = np.random.default_rng(semilla)
    return [anios[i] for i in rng.integers(0, len(anios), size=len(anios))]


def bootstrap(grupos, semilla_maestra, replicas):
    filas = []
    for (est, reg) in sorted(grupos):
        por_anio = grupos[(est, reg)]
        for r in range(1, replicas + 1):
            s = semilla_replica(semilla_maestra, est, reg, r)
            muestra = remuestrear(list(por_anio), s)
            e = estadisticos([por_anio[a] for a in muestra])
            filas.append({"estacion": est, "regimen": reg, "replica": r, "semilla": s,
                          "temporadas_muestreadas": ";".join(str(a) for a in muestra),
                          "p01": e["p01"], "p11": e["p11"], "alfa": e["alfa"], "theta": e["theta"]})
    return filas


def _formato(v):
    if isinstance(v, float):
        return "nan" if math.isnan(v) else repr(round(v, 10))
    return str(v)


def escribir_csv(ruta, columnas, filas):
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(columnas)
        for fila in filas:
            w.writerow([_formato(fila[c]) for c in columnas])


def main(argv=None):
    ap = argparse.ArgumentParser(description="Calibra Markov + gamma (Thom) por estación y régimen (T10).")
    ap.add_argument("--raw-dir", default="data/raw")
    ap.add_argument("--seleccion", default="data/processed/estaciones_seleccionadas.csv")
    ap.add_argument("--auditoria", default="data/processed/auditoria_calidad.csv")
    ap.add_argument("--regimenes", default="data/processed/regimenes.csv")
    ap.add_argument("--salida-dir", default="data/processed")
    ap.add_argument("--semilla", type=int, default=SEMILLA_POR_DEFECTO)
    ap.add_argument("--replicas", type=int, default=REPLICAS_POR_DEFECTO)
    a = ap.parse_args(argv)
    if a.replicas < 1:
        ap.error("--replicas debe ser >= 1")

    grupos = cargar_grupos(a.raw_dir, a.seleccion, a.auditoria, a.regimenes)
    if not grupos:
        print("error: no hay temporadas elegibles con régimen asignado", file=sys.stderr)
        return 1
    parametros = calibrar(grupos)
    salida = Path(a.salida_dir)
    escribir_csv(salida / "parametros.csv", COLUMNAS_PARAMETROS, parametros)
    escribir_csv(salida / "bootstrap_parametros.csv", COLUMNAS_BOOTSTRAP, bootstrap(grupos, a.semilla, a.replicas))
    for p in parametros:
        avisos = [k for k in ("gamma_invalida", "muestra_insuficiente", "muestra_pequena") if p[k]]
        print(f"{p['estacion']:<20} {p['regimen']:<8} T={p['n_temporadas']:>2} p01={_formato(p['p01'])} "
              f"p11={_formato(p['p11'])} alfa={_formato(p['alfa'])} theta={_formato(p['theta'])}"
              + (f"  [{', '.join(avisos)}]" if avisos else ""))
    print(f"escrito: {salida / 'parametros.csv'} y {salida / 'bootstrap_parametros.csv'} "
          f"({a.replicas} réplicas, semilla {a.semilla})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
