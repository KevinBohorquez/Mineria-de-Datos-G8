// T24 | Responsable: David | Ejecutable pp_hibrido (MPI + OpenMP).
#include "hibrido.hpp"

int main(int argc, char** argv) {
    return mpi_pi::ejecutar_mpi(argc, argv, "hibrido", mpi_pi::esquema_hibrido);
}
