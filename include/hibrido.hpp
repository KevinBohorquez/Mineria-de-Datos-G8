// T24 | Responsable: David | Interfaz del híbrido MPI + OpenMP.
#pragma once

#include "mpi_comun.hpp"

namespace mpi_pi {

// Esquema híbrido: reparto estático de [0, N) entre los procesos MPI y, dentro de cada proceso,
// `ejecutar_openmp` (reducción de k, n e histograma por hilos). Solo el hilo principal llama a MPI,
// por eso se exige MPI_THREAD_FUNNELED (se comprueba en ejecutar_mpi). La reducción entre procesos
// la hace ejecutar_mpi con MPI_Reduce. `cfg.hilos` fija los hilos por proceso (0 = OMP_NUM_THREADS).
ResumenRango esquema_hibrido(MPI_Comm comm, const pp::Configuracion& cfg, const FuncionEscenario& escenario,
                             pp::Acumulador& local);

}  // namespace mpi_pi
