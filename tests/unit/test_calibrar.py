"""Pruebas de T10 (scripts/run/calibrar.py y scripts/run/generar_configs.py) con series sintéticas.

Cubre: extracción de la temporada ene-abr, regla de trazas (< 0,1 mm = seco), conteo de transiciones
solo entre días consecutivos de la misma temporada y sin días faltantes, ajuste gamma de Thom contra
un ejemplo calculado a mano, banderas de muestra insuficiente/pequeña, determinismo y número de
réplicas del bootstrap por temporadas, y generación de YAML con las claves del contrato
(src/io/configuracion.cpp) omitiendo filas con NaN. No usa datos reales.

Uso:   python3 -m pytest -v tests/unit/test_calibrar.py
"""
import csv
import importlib.util
import math
from datetime import date, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
RUN = RAIZ / "scripts" / "run"

# Claves que acepta asignar() en src/io/configuracion.cpp.
CLAVES_CONTRATO = {
    "backend", "estacion", "regimen", "config_id", "semilla", "n", "hilos", "schedule", "salida",
    "lote", "repeticion", "p01", "p11", "alfa", "theta", "capacidad", "umbral", "dias",
}


def cargar(nombre, archivo):
    spec = importlib.util.spec_from_file_location(nombre, RUN / archivo)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def cal():
    return cargar("calibrar", "calibrar.py")


@pytest.fixture(scope="module")
def gen():
    return cargar("generar_configs", "generar_configs.py")


# ---------------------------------------------------------------- temporada y regla de lluvia

def test_regla_de_trazas(cal):
    assert cal.UMBRAL_LLUVIA_MM == 0.1
    assert cal.es_lluvioso(0.1)
    assert cal.es_lluvioso(25.0)
    assert not cal.es_lluvioso(0.05)   # traza: día seco
    assert not cal.es_lluvioso(0.0)
    assert not cal.es_lluvioso(None)   # faltante


def test_temporada_ene_abr_calendario_completo(cal):
    # Contrato de datos_comunes.py (T06): 120 días sin el 29-feb, [(date, float|None)].
    serie = [
        (date(1999, 12, 31), 7.0),          # fuera de la temporada
        (date(2000, 1, 1), 1.0),
        (date(2000, 1, 2), None),           # faltante explícito (celda vacía)
        # 2000-01-03 ausente del archivo: también faltante
        (date(2000, 1, 4), -2.0),           # negativo: faltante
        (date(2000, 2, 29), 8.0),           # 29-feb: fuera de la temporada de 120 días
        (date(2000, 4, 30), 3.0),
        (date(2000, 5, 1), 9.0),            # fuera de la temporada
    ]
    t = cal.temporada_ene_abr(serie, 2000)
    assert len(t) == 120
    assert t[0] == (date(2000, 1, 1), 1.0)
    assert [v for _, v in t[1:4]] == [None, None, None]
    assert date(2000, 2, 29) not in {f for f, _ in t}
    assert t[-1] == (date(2000, 4, 30), 3.0)
    assert len(cal.temporada_ene_abr(serie, 2001)) == 120
    assert all(v is None for _, v in cal.temporada_ene_abr(serie, 2001))


def test_leer_serie_vacio_es_faltante(cal, tmp_path):
    ruta = tmp_path / "X.csv"
    ruta.write_text("fecha,precipitacion_mm\n2000-01-01,0.0\n2000-01-02,\n2000-01-03,4.5\n",
                    encoding="utf-8")
    assert cal.leer_serie(ruta) == [
        (date(2000, 1, 1), 0.0), (date(2000, 1, 2), None), (date(2000, 1, 3), 4.5)]


# ---------------------------------------------------------------- transiciones

def test_transiciones_dentro_de_temporada(cal):
    # S=seco, L=lluvioso. Secuencia S L L S L con una traza (0.05 = S).
    t = [0.0, 2.0, 5.0, 0.05, 1.0]
    n00, n01, n10, n11 = cal.contar_transiciones([t])
    # S->L, L->L, L->S, S->L
    assert (n00, n01, n10, n11) == (0, 2, 1, 1)


def test_transiciones_omiten_faltantes(cal):
    # S L ? L S : se pierden L->? y ?->L; quedan S->L y L->S.
    t = [0.0, 2.0, None, 3.0, 0.0]
    assert cal.contar_transiciones([t]) == (0, 1, 1, 0)


def test_transiciones_no_cruzan_temporadas(cal):
    # Fin de una temporada lluvioso e inicio de la siguiente lluvioso: no hay transición L->L.
    t1 = [0.0, 0.0, 4.0]
    t2 = [6.0, 0.0]
    assert cal.contar_transiciones([t1, t2]) == (1, 1, 1, 0)


def test_estadisticos_probabilidades(cal):
    t = [0.0, 2.0, 5.0, 0.05, 1.0, None, 0.0]
    e = cal.estadisticos([t])
    assert e["n_dias"] == 6                 # sin el faltante
    assert e["n_lluvia"] == 3               # 2, 5, 1 (la traza no cuenta)
    # transiciones válidas: S->L, L->L, L->S, S->L  (1.0->None y None->0.0 se omiten)
    assert e["p01"] == pytest.approx(2 / 2)
    assert e["p11"] == pytest.approx(1 / 2)


# ---------------------------------------------------------------- gamma de Thom

def test_thom_ejemplo_a_mano(cal):
    # x = {1, 4}: media 2,5; A = ln 2,5 - (ln 1 + ln 4)/2 = ln 1,25 = 0,2231436
    # alfa = (1 + sqrt(1 + 4A/3)) / (4A) = 2,13908944 / 0,89257420 = 2,39654
    # theta = 2,5 / alfa = 1,04317
    alfa, theta, valido = cal.ajustar_gamma_thom([1.0, 4.0])
    assert valido
    assert alfa == pytest.approx(2.39654, rel=1e-4)
    assert theta == pytest.approx(1.04317, rel=1e-4)


def test_thom_guardas(cal):
    a, t, v = cal.ajustar_gamma_thom([3.0])           # menos de 2 días lluviosos
    assert not v and math.isnan(a) and math.isnan(t)
    a, t, v = cal.ajustar_gamma_thom([2.0, 2.0, 2.0])  # A = 0
    assert not v and math.isnan(a) and math.isnan(t)


def test_gamma_excluye_trazas(cal):
    e = cal.estadisticos([[1.0, 0.05, 4.0, 0.0]])
    assert e["alfa"] == pytest.approx(2.39654, rel=1e-4)
    assert e["gamma_invalida"] == 0


# ---------------------------------------------------------------- datos sintéticos de extremo a extremo

def _serie_sintetica(anio, patron):
    """Temporada completa con un patrón cíclico de montos (mm)."""
    inicio = date(anio, 1, 1)
    dias = (date(anio, 5, 1) - inicio).days
    return [(inicio + timedelta(d), patron[d % len(patron)]) for d in range(dias)]


def _escribir_csv(ruta, columnas, filas):
    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(columnas)
        w.writerows(filas)


@pytest.fixture
def insumos(tmp_path):
    """Dos estaciones: A con 3 temporadas elegibles normales + 1 no elegible; B con 1 temporada El Niño."""
    raw = tmp_path / "raw"
    raw.mkdir()
    filas_a = []
    patrones = {1998: [0.0, 2.0, 7.0, 0.0, 0.05], 1999: [0.0, 0.0, 12.0, 3.0],
                2000: [1.5, 0.0, 0.0, 9.0, 4.0], 2001: [50.0, 60.0]}
    for anio, p in patrones.items():
        filas_a += [(f.isoformat(), "" if v is None else v) for f, v in _serie_sintetica(anio, p)]
    _escribir_csv(raw / "A.csv", ["fecha", "precipitacion_mm"], filas_a)
    filas_b = [(f.isoformat(), v) for f, v in _serie_sintetica(1998, [0.0, 3.0, 8.0])]
    _escribir_csv(raw / "B.csv", ["fecha", "precipitacion_mm"], filas_b)

    sel = tmp_path / "estaciones_seleccionadas.csv"
    _escribir_csv(sel, ["estacion", "archivo", "region", "pct_faltante_ene_abr",
                        "temporadas_elegibles", "motivo_seleccion"],
                  [["A", "A.csv", "costa", "0", "3", "prueba"], ["B", "B.csv", "sierra", "0", "1", "prueba"]])
    aud = tmp_path / "auditoria_calidad.csv"
    cols_aud = ["estacion", "temporada", "dias_esperados", "dias_observados", "faltantes", "pct_faltante",
                "duplicados", "negativos", "atipicos_gt_150mm", "trazas", "elegible", "motivo"]
    _escribir_csv(aud, cols_aud, [
        ["A", 1998, 120, 120, 0, 0, 0, 0, 0, 0, 1, ""],
        ["A", 1999, 120, 120, 0, 0, 0, 0, 0, 0, 1, ""],
        ["A", 2000, 121, 121, 0, 0, 0, 0, 0, 0, 1, ""],
        ["A", 2001, 120, 120, 0, 0, 0, 0, 0, 0, 0, "faltantes"],
        ["B", 1998, 120, 120, 0, 0, 0, 0, 0, 0, 1, ""],
    ])
    reg = tmp_path / "regimenes.csv"
    _escribir_csv(reg, ["estacion", "temporada", "regimen", "regla", "fuente"], [
        ["A", 1998, "normal", "prueba", "sintetica"],
        ["A", 1999, "normal", "prueba", "sintetica"],
        ["A", 2000, "normal", "prueba", "sintetica"],
        ["A", 2001, "normal", "prueba", "sintetica"],
        ["B", 1998, "el_nino", "prueba", "sintetica"],
    ])
    return {"raw": raw, "sel": sel, "aud": aud, "reg": reg, "tmp": tmp_path}


def _argv(ins, salida, semilla=20261015, replicas=100):
    return ["--raw-dir", str(ins["raw"]), "--seleccion", str(ins["sel"]), "--auditoria", str(ins["aud"]),
            "--regimenes", str(ins["reg"]), "--salida-dir", str(salida),
            "--semilla", str(semilla), "--replicas", str(replicas)]


def _leer(ruta):
    with open(ruta, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def test_parametros_solo_temporadas_elegibles_y_banderas(cal, insumos):
    salida = insumos["tmp"] / "out"
    assert cal.main(_argv(insumos, salida)) == 0
    filas = {(r["estacion"], r["regimen"]): r for r in _leer(salida / "parametros.csv")}
    assert set(filas) == {("A", "normal"), ("B", "el_nino")}
    a = filas[("A", "normal")]
    assert int(a["n_temporadas"]) == 3                 # 2001 no es elegible
    assert a["temporadas"] == "1998;1999;2000"
    assert int(a["n_dias"]) == 3 * 120                 # el 29-feb de 2000 no forma parte de la temporada
    assert int(a["muestra_insuficiente"]) == 0
    assert int(a["muestra_pequena"]) == 1              # 3 < 5
    b = filas[("B", "el_nino")]
    assert int(b["n_temporadas"]) == 1
    assert int(b["muestra_insuficiente"]) == 1         # 1 < 2
    assert int(b["muestra_pequena"]) == 1


def test_bootstrap_determinista_y_replicas(cal, insumos):
    s1, s2, s3 = (insumos["tmp"] / n for n in ("o1", "o2", "o3"))
    cal.main(_argv(insumos, s1))
    cal.main(_argv(insumos, s2))
    cal.main(_argv(insumos, s3, semilla=7))
    b1 = (s1 / "bootstrap_parametros.csv").read_bytes()
    assert b1 == (s2 / "bootstrap_parametros.csv").read_bytes()
    assert (s1 / "parametros.csv").read_bytes() == (s2 / "parametros.csv").read_bytes()
    assert b1 != (s3 / "bootstrap_parametros.csv").read_bytes()

    filas = _leer(s1 / "bootstrap_parametros.csv")
    assert list(filas[0].keys()) == ["estacion", "regimen", "replica", "semilla", "temporadas_muestreadas",
                                      "p01", "p11", "alfa", "theta"]
    por_grupo = {}
    for r in filas:
        por_grupo.setdefault((r["estacion"], r["regimen"]), []).append(r)
    assert {k: len(v) for k, v in por_grupo.items()} == {("A", "normal"): 100, ("B", "el_nino"): 100}
    for r in por_grupo[("A", "normal")]:
        anios = r["temporadas_muestreadas"].split(";")
        assert len(anios) == 3 and set(anios) <= {"1998", "1999", "2000"}
    assert len({r["temporadas_muestreadas"] for r in por_grupo[("A", "normal")]}) > 1


def test_bootstrap_reproducible_por_semilla_de_replica(cal, insumos):
    """La semilla registrada en cada réplica reproduce por sí sola su remuestreo."""
    salida = insumos["tmp"] / "o"
    cal.main(_argv(insumos, salida, replicas=5))
    anios = [1998, 1999, 2000]
    for r in _leer(salida / "bootstrap_parametros.csv"):
        if r["estacion"] != "A":
            continue
        assert cal.remuestrear(anios, int(r["semilla"])) == [int(x) for x in r["temporadas_muestreadas"].split(";")]


# ---------------------------------------------------------------- generar_configs

def test_generar_configs_contrato_y_omite_nan(gen, tmp_path, capsys):
    plantilla = tmp_path / "sintetico.yaml"
    plantilla.write_text(
        "# comentario\nestacion: sintetica\nregimen: normal\nconfig_id: 0\nsemilla: 20261015\n"
        "n: 1000000\ndias: 120\np01: 0.15\np11: 0.60\nalfa: 0.7\ntheta: 9.0\ncapacidad: 6\numbral: 50\n",
        encoding="utf-8")
    params = tmp_path / "parametros.csv"
    _escribir_csv(params, ["estacion", "regimen", "n_temporadas", "p01", "p11", "alfa", "theta",
                           "muestra_insuficiente", "muestra_pequena"], [
        ["Est A", "normal", 6, 0.2, 0.55, 0.8, 7.5, 0, 0],
        ["B", "el_nino", 1, 0.3, 0.6, "nan", "nan", 1, 1],
    ])
    destino = tmp_path / "config"
    assert gen.main(["--parametros", str(params), "--plantilla", str(plantilla),
                     "--salida-dir", str(destino), "--commit", "abc1234"]) == 0
    archivos = sorted(p.name for p in destino.iterdir())
    assert archivos == ["est_a_normal.yaml"]
    texto = (destino / "est_a_normal.yaml").read_text(encoding="utf-8")
    assert "parametros.csv" in texto and "abc1234" in texto     # cabecera con fuente y commit

    # Mismo análisis que cargar_archivo_configuracion(): quitar '#', 'clave: valor'.
    pares = {}
    for linea in texto.splitlines():
        linea = linea.split("#", 1)[0].strip()
        if linea:
            k, v = linea.split(":", 1)
            pares[k.strip()] = v.strip()
    assert set(pares) <= CLAVES_CONTRATO
    assert pares["estacion"] == "Est A" and pares["regimen"] == "normal"
    assert float(pares["p01"]) == 0.2 and float(pares["p11"]) == 0.55
    assert float(pares["alfa"]) == 0.8 and float(pares["theta"]) == 7.5
    assert pares["dias"] == "120" and pares["capacidad"] == "6" and pares["umbral"] == "50"
    assert pares["n"] == "1000000" and pares["semilla"] == "20261015"
    assert "omit" in capsys.readouterr().out.lower()               # avisa de la fila con NaN


def test_generar_configs_rechaza_fuera_de_rango(gen, tmp_path):
    with pytest.raises(ValueError):
        gen.validar_parametros({"p01": 1.2, "p11": 0.5, "alfa": 1.0, "theta": 1.0})
    with pytest.raises(ValueError):
        gen.validar_parametros({"p01": 0.2, "p11": 0.5, "alfa": 0.0, "theta": 1.0})
    gen.validar_parametros({"p01": 0.0, "p11": 1.0, "alfa": 0.1, "theta": 0.1})
