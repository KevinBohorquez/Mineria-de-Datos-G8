// T19 | Responsable: David | Reparto MPI estático (E1) y reducción.
#include "mpi_estatico.hpp"

namespace mpi_pi {

std::pair<std::uint64_t, std::uint64_t> intervalo_estatico(std::uint64_t n, int rango, int procesos) {
    const std::uint64_t p = static_cast<std::uint64_t>(procesos);
    const std::uint64_t r = static_cast<std::uint64_t>(rango);
    const std::uint64_t base = n / p;
    const std::uint64_t resto = n % p;
    const std::uint64_t inicio = r * base + (r < resto ? r : resto);
    const std::uint64_t cuenta = base + (r < resto ? 1 : 0);
    return {inicio, inicio + cuenta};
}

ResumenRango esquema_estatico(MPI_Comm comm, const Opciones& o, const FuncionEscenario& escenario, Acumulador& local) {
    int rango = 0, procesos = 1;
    MPI_Comm_rank(comm, &rango);
    MPI_Comm_size(comm, &procesos);

    const auto [inicio, fin] = intervalo_estatico(o.escenarios, rango, procesos);
    for (std::uint64_t i = inicio; i < fin; ++i) escenario(i, local);

    ResumenRango res;
    res.inicio = inicio;
    res.fin = fin;
    res.bloques = fin > inicio ? 1 : 0;
    res.n_local = local.n;
    return res;
}

}  // namespace mpi_pi

#ifndef PRUEBA_SIN_MAIN
int main(int argc, char** argv) {
    return mpi_pi::ejecutar_mpi(argc, argv, "mpi_estatico", mpi_pi::esquema_estatico);
}
#endif
