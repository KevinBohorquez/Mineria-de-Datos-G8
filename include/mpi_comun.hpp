// T19,T20 | Responsable: David | Piezas comunes de los ejecutables MPI (contrato docs/contratos.md).
#pragma once

#include <mpi.h>

#include <cstdint>
#include <functional>

#include "resultados.hpp"

namespace mpi_pi {

// Procesa el escenario de índice local j (0 <= j < N) de la configuración y lo suma en el acumulador.
// El índice global que recibe el núcleo es config_id * N + j (contrato §1).
using FuncionEscenario = std::function<void(std::uint64_t j, pp::Acumulador&)>;

// Resumen de lo que hizo un rango, para el log de verificación.
struct ResumenRango {
    std::uint64_t inicio = 0;
    std::uint64_t fin = 0;
    std::uint64_t bloques = 0;
    std::uint64_t n_local = 0;
    bool coherente = true;
};

// Esquema de reparto: procesa su parte y devuelve el acumulador local y su resumen.
using Esquema = std::function<ResumenRango(MPI_Comm, const pp::Configuracion&, const FuncionEscenario&, pp::Acumulador&)>;

// Escenario del modelo: llama a pp::simular_escenario con la clave de (semilla, config_id).
FuncionEscenario escenario_del_modelo(const pp::Configuracion& cfg);

// Punto de entrada común: MPI_Init_thread, configuración, esquema, reducción, verificación y CSV.
// Devuelve el código de salida del contrato §5.
int ejecutar_mpi(int argc, char** argv, const char* backend, const Esquema& esquema);

}  // namespace mpi_pi
