# T13 | Responsable: Lita | Revisión: Ashley | V6: validación estadística del generador de lluvia.
#
# Definición del proyecto, §7.7: se comparan la frecuencia de días lluviosos, la media y la desviación
# de la lluvia diaria, los percentiles 95 y 99, la longitud media de las rachas lluviosas y el máximo
# diario por temporada. Aceptación: error relativo <= 10 % en cada estadístico y Kolmogorov–Smirnov
# no rechazado al 5 % para los montos.
#
# Mientras no existan los datos observados de T08/T10, la referencia es el valor EXACTO que implica el
# modelo Markov + gamma con los mismos parámetros (calculado aquí, no copiado de una corrida).
#
# Uso (tras compilar):  python3 -m pytest -v -s tests/unit/test_estadistico.py
# Variables opcionales: PP_V6_GENERADOR=<ruta a pp_v6_generador> (por defecto build/pp_v6_generador)
#                       PP_V6_N=<temporadas>  (por defecto 20000; la definición usa 10^8 para la corrida oficial)
import math
import os
import subprocess
from pathlib import Path

import pytest
from scipy import integrate, stats

RAIZ = Path(__file__).resolve().parents[2]
GENERADOR = Path(os.environ.get("PP_V6_GENERADOR", RAIZ / "build" / "pp_v6_generador"))
N = int(os.environ.get("PP_V6_N", "20000"))
SEMILLA = 20261015
TOLERANCIA = 0.10
ALFA_KS = 0.05

# alfa < 1 recorre la rama gamma(a+1)·U^(1/a) de Marsaglia–Tsang; alfa > 1 la rama directa.
CASOS = {
    "sintetico_alfa_menor_1": dict(p01=0.15, p11=0.60, alfa=0.7, theta=9.0, dias=120),
    "alfa_mayor_1": dict(p01=0.25, p11=0.55, alfa=2.5, theta=6.0, dias=120),
    "lluvioso_persistente": dict(p01=0.40, p11=0.80, alfa=1.0, theta=12.0, dias=90),
}

pytestmark = pytest.mark.skipif(not GENERADOR.exists(),
                                reason=f"compile primero (cmake --build build); no existe {GENERADOR}")


def prob_lluvia_por_dia(p01, p11, dias):
    """P(día d lluvioso) con el día previo a la temporada seco, como simular_escenario."""
    p, salida = 0.0, []
    for _ in range(dias):
        p = p01 * (1.0 - p) + p11 * p
        salida.append(p)
    return salida


def esperados(p01, p11, alfa, theta, dias):
    gamma = stats.gamma(alfa, scale=theta)
    pd = prob_lluvia_por_dia(p01, p11, dias)

    # Racha cerrada = transición lluvia→seco dentro de la temporada. Los días que forman rachas cerradas
    # son todos los lluviosos menos los de la racha abierta al final de la temporada.
    cerradas = sum(pd[d] * (1.0 - p11) for d in range(dias - 1))
    abiertas = sum(pd[d] * p11 ** (dias - 1 - d) for d in range(dias))
    racha_media = (sum(pd) - abiertas) / cerradas

    def cdf_maximo(x):  # P(max diario de la temporada <= x); sin lluvia el máximo es 0
        seco, lluvia = 1.0, 0.0
        f = gamma.cdf(x)
        for _ in range(dias):
            seco, lluvia = seco * (1 - p01) + lluvia * (1 - p11), (seco * p01 + lluvia * p11) * f
        return seco + lluvia

    max_medio, _ = integrate.quad(lambda x: 1.0 - cdf_maximo(x), 0.0, math.inf, limit=200)
    return {
        "frecuencia_lluvia": sum(pd) / dias,
        "media_monto": alfa * theta,
        "desviacion_monto": math.sqrt(alfa) * theta,
        "p95_monto": gamma.ppf(0.95),
        "p99_monto": gamma.ppf(0.99),
        "racha_media": racha_media,
        "max_diario_temporada_medio": max_medio,
    }


def correr_generador(params):
    cmd = [str(GENERADOR), "--n", str(N), "--semilla", str(SEMILLA)]
    for clave, valor in params.items():
        cmd += [f"--{clave}", str(valor)]
    r = subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800)
    return dict(linea.split("=", 1) for linea in r.stdout.splitlines() if "=" in linea)


@pytest.fixture(scope="module", params=list(CASOS))
def caso(request):
    params = CASOS[request.param]
    return request.param, params, correr_generador(params), esperados(**params)


def test_v6_estadisticos_dentro_de_10_por_ciento(caso):
    nombre, params, obs, esp = caso
    print(f"\n[V6] caso={nombre} N={N} semilla={SEMILLA} params={params} dias_simulados={obs['dias']}")
    print(f"[V6] {'estadistico':28s} {'esperado':>14s} {'observado':>14s} {'error_rel':>10s}")
    fallos = []
    for clave, valor_esp in esp.items():
        valor_obs = float(obs[clave])
        error = abs(valor_obs - valor_esp) / abs(valor_esp)
        print(f"[V6] {clave:28s} {valor_esp:14.6f} {valor_obs:14.6f} {error:10.4%}")
        if error > TOLERANCIA:
            fallos.append(f"{clave}: esperado {valor_esp:.6g}, observado {valor_obs:.6g} ({error:.2%})")
    assert not fallos, f"{nombre}: error relativo > {TOLERANCIA:.0%} en " + "; ".join(fallos)


def test_v6_kolmogorov_smirnov_montos(caso):
    nombre, params, obs, _ = caso
    muestra = [float(x) for x in obs["muestra"].split(";")]
    resultado = stats.kstest(muestra, "gamma", args=(params["alfa"], 0.0, params["theta"]))
    print(f"\n[V6] caso={nombre} KS n={len(muestra)} D={resultado.statistic:.5f} p={resultado.pvalue:.4f} "
          f"(se rechaza si p < {ALFA_KS})")
    assert len(muestra) >= 1000
    assert resultado.pvalue >= ALFA_KS, f"{nombre}: KS rechaza gamma(alfa, theta) con p={resultado.pvalue:.4g}"


def test_v6_reproducible_con_semilla_fija():
    params = CASOS["sintetico_alfa_menor_1"]
    assert correr_generador(params) == correr_generador(params)


def test_v6_control_negativo_detecta_parametros_equivocados():
    """Si el generador usara otro theta, V6 debe notarlo; si no, un 'pasa' no valdría nada."""
    params = CASOS["alfa_mayor_1"]
    obs = correr_generador(params)
    esp = esperados(**dict(params, theta=params["theta"] * 1.3))
    assert abs(float(obs["media_monto"]) - esp["media_monto"]) / esp["media_monto"] > TOLERANCIA
    muestra = [float(x) for x in obs["muestra"].split(";")]
    assert stats.kstest(muestra, "gamma", args=(params["alfa"], 0.0, params["theta"] * 1.3)).pvalue < ALFA_KS
