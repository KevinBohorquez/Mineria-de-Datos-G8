"""Pruebas de T06/T08/T09 (scripts/run/datos_comunes.py, auditar.py, clasificar_regimenes.py).

Usan series sintéticas pequeñas, nunca los archivos SENAMHI reales.

Uso:   python3 -m pytest -v tests/unit/test_datos.py
"""
import importlib.util
import sys
from datetime import date, timedelta
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
RUN = RAIZ / "scripts" / "run"


def cargar(nombre):
    if str(RUN) not in sys.path:
        sys.path.insert(0, str(RUN))
    spec = importlib.util.spec_from_file_location(nombre, RUN / f"{nombre}.py")
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


@pytest.fixture(scope="module")
def dc():
    return cargar("datos_comunes")


@pytest.fixture(scope="module")
def aud():
    return cargar("auditar")


@pytest.fixture(scope="module")
def clas():
    return cargar("clasificar_regimenes")


def serie_continua(inicio, fin, valor=0.0):
    dia, filas = inicio, []
    while dia <= fin:
        filas.append((dia, valor))
        dia += timedelta(days=1)
    return filas


# ---------------------------------------------------------------- lectura

def test_leer_serie_vacios_crlf_y_duplicados(dc, tmp_path):
    ruta = tmp_path / "x.csv"
    ruta.write_bytes(b"fecha,precipitacion_mm\r\n2001-01-01,1.50\r\n2001-01-02,\r\n"
                     b"2001-01-02,3.0\r\n2001-01-03,-1\r\n")
    serie = dc.leer_serie(ruta)
    assert serie == [(date(2001, 1, 1), 1.5), (date(2001, 1, 2), None),
                     (date(2001, 1, 2), 3.0), (date(2001, 1, 3), -1.0)]


# ---------------------------------------------------------------- temporada

def test_temporada_tiene_120_dias_de_enero_a_abril(dc):
    serie = serie_continua(date(2000, 12, 1), date(2001, 6, 30), 2.0)
    t = dc.temporada_ene_abr(serie, 2001)
    assert len(t) == 120 == dc.DIAS_TEMPORADA
    assert t[0][0] == date(2001, 1, 1) and t[-1][0] == date(2001, 4, 30)
    assert all(mm == 2.0 for _, mm in t)


def test_temporada_bisiesta_excluye_29_febrero(dc):
    serie = serie_continua(date(2000, 1, 1), date(2000, 4, 30), 0.0)
    t = dc.temporada_ene_abr(serie, 2000)
    fechas = [f for f, _ in t]
    assert len(t) == 120 and date(2000, 2, 29) not in fechas


def test_temporada_faltantes_negativos_y_duplicados(dc):
    serie = serie_continua(date(2001, 1, 1), date(2001, 4, 30), 0.0)
    serie = [(f, mm) for f, mm in serie if f != date(2001, 1, 5)]   # fila ausente
    serie[0] = (date(2001, 1, 1), -3.0)                              # negativo -> faltante
    serie[1] = (date(2001, 1, 2), None)                              # vacío -> faltante
    serie.append((date(2001, 1, 3), 99.0))                           # duplicado: manda la 1.ª
    t = dict(dc.temporada_ene_abr(serie, 2001))
    assert t[date(2001, 1, 1)] is None and t[date(2001, 1, 2)] is None
    assert t[date(2001, 1, 5)] is None and t[date(2001, 1, 3)] == 0.0
    assert dc.faltantes(list(t.items())) == 3


def test_anios_temporada_completos_respeta_el_rango(dc):
    serie = serie_continua(date(1989, 12, 1), date(1992, 1, 31))
    assert dc.anios_temporada_completos(serie) == [1990, 1991]


# ---------------------------------------------------------------- umbral y trazas

def test_umbral_de_lluvia_y_trazas(dc):
    assert dc.UMBRAL_LLUVIA_MM == 0.1
    assert dc.es_lluvioso(0.1) and dc.es_lluvioso(25.0)
    assert not dc.es_lluvioso(0.05) and not dc.es_lluvioso(0.0) and not dc.es_lluvioso(None)
    assert dc.es_traza(0.05) and not dc.es_traza(0.1) and not dc.es_traza(0.0)
    assert not dc.es_traza(None)


# ---------------------------------------------------------------- faltantes y elegibilidad

def temporada_con_faltantes(dc, k):
    t = [(f, 0.0) for f in dc.fechas_temporada(2001)]
    return [(f, None) if i < k else (f, mm) for i, (f, mm) in enumerate(t)]


def test_elegibilidad_menos_de_10_por_ciento(dc):
    t11, t12 = temporada_con_faltantes(dc, 11), temporada_con_faltantes(dc, 12)
    assert dc.pct_faltante(t11) == pytest.approx(100 * 11 / 120)
    assert dc.temporada_elegible(t11)
    assert dc.pct_faltante(t12) == pytest.approx(10.0)
    assert not dc.temporada_elegible(t12)


def test_auditar_estacion_cuenta_banderas(dc, aud):
    serie = serie_continua(date(2001, 1, 1), date(2002, 4, 30), 0.0)
    serie = [(f, mm) for f, mm in serie if f != date(2001, 2, 1)]    # fila ausente
    serie.append((date(2001, 1, 10), 0.0))                           # duplicado
    serie.append((date(2001, 3, 1), -2.0))                           # negativo (dup. de fecha)
    i = {f: k for k, (f, _) in enumerate(serie)}
    serie[i[date(2001, 1, 20)]] = (date(2001, 1, 20), 200.0)         # atípico
    serie[i[date(2001, 1, 21)]] = (date(2001, 1, 21), 0.05)          # traza
    serie[i[date(2001, 6, 1)]] = (date(2001, 6, 1), 500.0)           # fuera de temporada
    filas = {f["temporada"]: f for f in aud.auditar_estacion("est_x", serie)}
    a = filas[2001]
    assert a["dias_esperados"] == 120 and a["faltantes"] == 1 and a["dias_observados"] == 119
    assert a["duplicados"] == 2 and a["negativos"] == 1
    assert a["atipicos_gt_150mm"] == 1 and a["trazas"] == 1
    assert a["elegible"] == 1 and a["motivo"] == "ok"
    assert filas[2002]["faltantes"] == 0


def test_auditar_estacion_marca_temporada_no_elegible(aud):
    serie = serie_continua(date(2001, 1, 1), date(2001, 4, 30), 0.0)
    serie = [(f, None if f.month == 1 else mm) for f, mm in serie]
    (a,) = aud.auditar_estacion("est_x", serie)
    assert a["faltantes"] == 31 and a["elegible"] == 0
    assert a["motivo"].startswith("faltantes")


# ---------------------------------------------------------------- selección de estaciones

def cand(nombre, region, pct, temporadas):
    return {"estacion": nombre, "region": region, "pct_faltante_ene_abr": pct,
            "temporadas_elegibles": temporadas}


def test_seleccion_exige_20_temporadas_y_maximo_5(dc):
    cs = [cand(f"piura_{i}", "Piura", float(i), 30) for i in range(7)]
    cs.append(cand("lima_canete", "Lima", 47.0, 5))
    elegidas = [c["estacion"] for c, _ in dc.seleccionar_estaciones(cs)]
    assert elegidas == [f"piura_{i}" for i in range(5)]


def test_seleccion_garantiza_una_de_lima_si_califica(dc):
    cs = [cand(f"piura_{i}", "Piura", float(i), 30) for i in range(6)]
    cs.append(cand("lima_chosica", "Lima", 9.0, 21))
    elegidas = dc.seleccionar_estaciones(cs)
    nombres = [c["estacion"] for c, _ in elegidas]
    assert len(nombres) == 5 and nombres[-1] == "lima_chosica"
    assert "Lima" in elegidas[-1][1]


# ---------------------------------------------------------------- regímenes

def test_evento_mapea_a_la_temporada_siguiente(dc):
    assert dc.temporada_de_evento("1982-1983") == 1983
    assert dc.temporada_de_evento("1997-98") == 1998
    assert dc.temporada_de_evento("2017") == 2017


def test_clasificar_temporada(dc):
    nino = {1983, 1998, 2017}
    assert dc.clasificar_temporada(1983, nino) == "el_nino"
    assert dc.clasificar_temporada(1982, nino) == "normal"
    assert dc.clasificar_temporada(1999, nino) == "normal"


def test_clasificar_regimenes_solo_temporadas_elegibles(clas):
    auditoria = [
        {"estacion": "a", "temporada": "1983", "elegible": "1"},
        {"estacion": "a", "temporada": "1984", "elegible": "1"},
        {"estacion": "a", "temporada": "1998", "elegible": "0"},
        {"estacion": "b", "temporada": "1983", "elegible": "1"},
    ]
    eventos = [{"evento": "1982-1983", "temporada_afectada": "1983", "fuente": "F"}]
    filas = clas.clasificar(auditoria, ["a"], eventos)
    assert [(f["estacion"], f["temporada"], f["regimen"]) for f in filas] == [
        ("a", 1983, "el_nino"), ("a", 1984, "normal")]
    assert filas[0]["fuente"] == "F" and "1982-1983" in filas[0]["regla"]
