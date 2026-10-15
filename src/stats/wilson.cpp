// T12 | Responsable: Ashley | Intervalo de Wilson.
#include <algorithm>
#include <cmath>

#include "resultados.hpp"

namespace pp {

Intervalo wilson(uint64_t k, uint64_t n, double z) {
    if (n == 0) return {0.0, 1.0};
    const double nn = static_cast<double>(n);
    const double p = static_cast<double>(k) / nn;
    const double z2 = z * z;
    const double den = 1.0 + z2 / nn;
    const double centro = (p + z2 / (2.0 * nn)) / den;
    const double mitad = z * std::sqrt(p * (1.0 - p) / nn + z2 / (4.0 * nn * nn)) / den;
    Intervalo r{std::max(0.0, centro - mitad), std::min(1.0, centro + mitad)};
    if (k == 0) r.inf = 0.0;  // exacto, sin ruido de redondeo
    if (k == n) r.sup = 1.0;
    return r;
}

}  // namespace pp
