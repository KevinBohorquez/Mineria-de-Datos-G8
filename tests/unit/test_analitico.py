# T13 | Responsable: Lita (ejecutado por Miguel por acuerdo del equipo) | Caso analítico V7.
#
# V7 (definición §9.3): con D = 1 la temporada parte de un día previo seco, así que llueve con
# probabilidad p01 y el monto es Gamma(α, θ). Con A = max(0, R − C) hay inundación si A > U, es decir,
#     P = p01 · Q(α, (C + U) / θ),
# con Q la gamma incompleta regularizada superior. La P analítica debe caer dentro del IC de Wilson
# al 95 % que reporta el simulador secuencial. Se prueban α < 1 (camino potenciado de Marsaglia–Tsang),
# α = 1 (exponencial, Q cerrada) y α > 1, con semilla fija: la prueba es determinista.
#
# Uso (tras compilar):   pytest -q tests/unit/test_analitico.py
# Variable opcional:     PP_BIN_DIR=<carpeta con serial/pp_serial>  (por defecto build/src/backends)
import csv
import math
import os
import subprocess
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parents[2]
BIN = Path(os.environ.get("PP_BIN_DIR", RAIZ / "build" / "src" / "backends"))
SERIAL = BIN / "serial" / "pp_serial"

N = 1_000_000
SEMILLA = 20261015


def q_python(a, x):
    """Gamma incompleta regularizada superior Q(a, x) (serie / fracción continua de Lentz)."""
    if x <= 0.0:
        return 1.0
    prefactor = math.exp(-x + a * math.log(x) - math.lgamma(a))
    if x < a + 1.0:  # serie de P(a, x); Q = 1 − P
        termino = suma = 1.0 / a
        ap = a
        for _ in range(10_000):
            ap += 1.0
            termino *= x / ap
            suma += termino
            if abs(termino) < abs(suma) * 1e-16:
                break
        return 1.0 - suma * prefactor
    minimo = 1e-300  # fracción continua de Q(a, x), algoritmo de Lentz modificado
    b = x + 1.0 - a
    c, d = 1.0 / minimo, 1.0 / b
    h = d
    for i in range(1, 10_000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        d = minimo if abs(d) < minimo else d
        c = b + an / c
        c = minimo if abs(c) < minimo else c
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    return prefactor * h


try:  # scipy si está (imagen Docker); si no (CI con solo python3-pytest), la versión en Python
    from scipy.special import gammaincc as Q
except ImportError:  # pragma: no cover - depende del entorno
    Q = q_python


# (nombre, p01, alfa, theta, capacidad C, umbral U). U pequeño para que P ~ 1e-2 y N = 10⁶ baste.
CASOS = [
    ("alfa<1", 0.15, 0.7, 9.0, 6.0, 10.0),
    ("alfa=1", 0.20, 1.0, 8.0, 5.0, 15.0),
    ("alfa>1", 0.30, 2.5, 5.0, 6.0, 10.0),
]


@pytest.mark.parametrize("a,x", [(0.5, 0.3), (0.7, 16 / 9), (1.0, 2.5), (2.5, 3.2), (3.0, 7.0), (10.0, 4.0)])
def test_q_python_coincide_con_formas_cerradas(a, x):
    # Q(1, x) = e^−x; Q(1/2, x) = erfc(√x); Q(n, x) = e^−x Σ_{j<n} x^j / j!
    if a == 0.5:
        esperado = math.erfc(math.sqrt(x))
    elif float(a).is_integer():
        esperado = math.exp(-x) * sum(x ** j / math.factorial(j) for j in range(int(a)))
    else:
        esperado = Q(a, x)  # scipy, o la propia versión si no hay scipy (entonces la prueba es trivial)
    assert q_python(a, x) == pytest.approx(esperado, rel=1e-10)


@pytest.mark.skipif(not SERIAL.exists(), reason=f"compile primero (cmake --build build); no se encontró {SERIAL}")
@pytest.mark.parametrize("nombre,p01,alfa,theta,capacidad,umbral", CASOS, ids=[c[0] for c in CASOS])
def test_v7_p_analitica_dentro_de_wilson(tmp_path, nombre, p01, alfa, theta, capacidad, umbral):
    salida = tmp_path / f"{nombre}.csv"
    cmd = [str(SERIAL), "--n", str(N), "--semilla", str(SEMILLA), "--config-id", "0", "--dias", "1",
           "--p01", str(p01), "--p11", "0", "--alfa", str(alfa), "--theta", str(theta),
           "--capacidad", str(capacidad), "--umbral", str(umbral), "--silencioso", "--salida", str(salida)]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=300)
    with open(salida, newline="") as f:
        fila = next(csv.DictReader(f))

    assert int(fila["n"]) == N and int(fila["dias"]) == 1
    p_analitica = p01 * float(Q(alfa, (capacidad + umbral) / theta))
    p_hat, inf, sup = float(fila["p_hat"]), float(fila["wilson_inf"]), float(fila["wilson_sup"])
    print(f"V7 {nombre}: P analítica={p_analitica:.6f}  P̂={p_hat:.6f}  Wilson95=[{inf:.6f}, {sup:.6f}]  k={fila['k']}")
    assert 0 < int(fila["k"]) < N
    assert inf <= p_analitica <= sup, (
        f"V7 falla ({nombre}): P analítica {p_analitica:.6f} fuera del IC de Wilson [{inf:.6f}, {sup:.6f}]")
