// T15 | Responsable: Ashley | Interfaz del backend OpenMP.
#pragma once

#include <cstdint>
#include <string>

#include "resultados.hpp"
#include "simulacion.hpp"

namespace pp {

// Simula los escenarios con índices globales [config_id*N + j0, config_id*N + j1)
// usando `hilos` hilos y schedule(runtime). Cada hilo acumula en copias privadas de
// k, n y del histograma de 512 clases; la reducción la hace OpenMP al cerrar la región.
// El resultado NO depende de hilos ni del schedule (V1).
// hilos <= 0 deja el valor de OMP_NUM_THREADS. schedule vacío respeta OMP_SCHEDULE.
Acumulador ejecutar_openmp(const Parametros& p, uint64_t clave, uint64_t config_id, uint64_t n_total,
                           uint64_t j0, uint64_t j1, int hilos, const std::string& schedule);

}  // namespace pp
