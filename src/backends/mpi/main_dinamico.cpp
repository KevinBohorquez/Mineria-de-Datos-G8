// T20 | Responsable: David | Ejecutable pp_mpi_dinamico.
#include "mpi_dinamico.hpp"

int main(int argc, char** argv) {
    return mpi_pi::ejecutar_mpi(argc, argv, "mpi_dinamico", mpi_pi::esquema_dinamico);
}
