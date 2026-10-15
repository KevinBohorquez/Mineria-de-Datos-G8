// T12 | Responsable: Ashley | Histograma de 512 clases de 1 mm y acumulador.
#include <cmath>

#include "resultados.hpp"

namespace pp {

int clase_histograma(double amax) {
    if (!(amax > 0.0)) return 0;  // 0, negativos y NaN
    const double f = std::floor(amax);
    return f >= static_cast<double>(NBINS - 1) ? NBINS - 1 : static_cast<int>(f);
}

void Acumulador::agregar(const Resultado& r) {
    k += r.inundacion ? 1u : 0u;
    n += 1u;
    hist[static_cast<size_t>(clase_histograma(r.amax))] += 1u;
}

void Acumulador::combinar(const Acumulador& o) {
    k += o.k;
    n += o.n;
    for (size_t i = 0; i < hist.size(); ++i) hist[i] += o.hist[i];
}

}  // namespace pp
