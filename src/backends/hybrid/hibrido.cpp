// T24 | Responsable: David | Esquema híbrido: reparto estático entre procesos y OpenMP dentro de cada uno.
#include "hibrido.hpp"

#include "mpi_estatico.hpp"
#include "openmp.hpp"
#include "simulacion.hpp"

namespace mpi_pi {

ResumenRango esquema_hibrido(MPI_Comm comm, const pp::Configuracion& cfg, const FuncionEscenario& /*escenario*/,
                             pp::Acumulador& local) {
    int rango = 0, procesos = 1;
    MPI_Comm_rank(comm, &rango);
    MPI_Comm_size(comm, &procesos);

    const auto [inicio, fin] = intervalo_estatico(cfg.n, rango, procesos);
    const std::uint64_t clave = pp::derivar_clave(cfg.semilla, cfg.config_id);
    // Las llamadas MPI quedan fuera de las regiones paralelas (MPI_THREAD_FUNNELED).
    local = pp::ejecutar_openmp(cfg.params, clave, cfg.config_id, cfg.n, inicio, fin, cfg.hilos, cfg.schedule);

    ResumenRango res;
    res.inicio = inicio;
    res.fin = fin;
    res.bloques = fin > inicio ? 1 : 0;
    res.n_local = local.n;
    res.hilos = static_cast<std::uint64_t>(pp::hilos_efectivos());
    res.schedule = pp::schedule_actual();
    return res;
}

}  // namespace mpi_pi
