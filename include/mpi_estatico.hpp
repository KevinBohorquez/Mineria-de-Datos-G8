// T19 | Responsable: David | Interfaz del reparto MPI estático (E1).
#pragma once

#include <cstdint>
#include <utility>

#include "mpi_comun.hpp"

namespace mpi_pi {

// Intervalo contiguo [inicio, fin) del rango `rango` entre `procesos`: reparte el residuo N mod P
// entre los primeros rangos, sin solape ni huecos aunque N no sea divisible.
std::pair<std::uint64_t, std::uint64_t> intervalo_estatico(std::uint64_t n, int rango, int procesos);

// Esquema E1: cada rango procesa su intervalo; la reducción MPI_Reduce la hace ejecutar_mpi.
ResumenRango esquema_estatico(MPI_Comm comm, const Opciones& o, const FuncionEscenario& escenario, Acumulador& local);

}  // namespace mpi_pi
