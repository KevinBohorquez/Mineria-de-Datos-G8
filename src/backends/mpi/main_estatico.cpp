// T19 | Responsable: David | Ejecutable pp_mpi_estatico.
#include "mpi_estatico.hpp"

int main(int argc, char** argv) {
    return mpi_pi::ejecutar_mpi(argc, argv, "mpi_estatico", mpi_pi::esquema_estatico);
}
