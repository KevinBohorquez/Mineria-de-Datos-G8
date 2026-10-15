// T19,T20 | Responsable: David | Piezas comunes de los ejecutables MPI (contrato docs/contratos.md).
#pragma once

#include <mpi.h>

#include <cstdint>
#include <functional>
#include <string>

namespace mpi_pi {

constexpr int NBINS = 512;
constexpr int VERSION_CONTRATO = 1;

// Acumulador de una configuración; se suma con MPI_SUM (contrato §3).
struct Acumulador {
    std::uint64_t k = 0;
    std::uint64_t n = 0;
    std::uint64_t hist[NBINS] = {0};
};

// Opciones de la CLI/YAML (contrato §4 y §5).
struct Opciones {
    std::string config;
    std::string backend = "serial";
    std::string estacion = "sin_estacion";
    std::string regimen = "normal";
    double capacidad_mm_dia = 30.0;
    double umbral_mm = 50.0;
    std::uint64_t dias = 120;
    std::uint64_t semilla = 0;
    std::uint64_t escenarios = 0;
    std::uint64_t configuracion_id = 0;
    std::uint64_t hilos = 1;
    std::uint64_t lote = 62500;
    std::string salida;
    int repeticion = 1;
    bool calentamiento = false;
    bool verificar = false;
};

// Procesa los escenarios con índice global i y los suma en el acumulador.
using FuncionEscenario = std::function<void(std::uint64_t indice, Acumulador&)>;

// Resumen de lo que hizo un rango, para el log de verificación.
struct ResumenRango {
    std::uint64_t inicio = 0;
    std::uint64_t fin = 0;
    std::uint64_t bloques = 0;
    std::uint64_t n_local = 0;
    bool coherente = true;
};

// Esquema de reparto: procesa su parte y devuelve el acumulador local y su resumen.
using Esquema = std::function<ResumenRango(MPI_Comm, const Opciones&, const FuncionEscenario&, Acumulador&)>;

// Clase del histograma: min(floor(maximo_mm), 511), contrato §3.
int clase_histograma(double maximo_mm);

// Clave del contrato §1: splitmix64(semilla + c * 0x9E3779B97F4A7C15).
std::uint64_t clave_configuracion(std::uint64_t semilla, std::uint64_t configuracion_id);

// Núcleo PROVISIONAL: sustituye a simular_escenario (T11, Ashley) hasta que exista.
// Mismo contrato (función pura de clave e índice global); no es el modelo Markov + gamma.
FuncionEscenario escenario_provisional(const Opciones& o);

// Lee el YAML plano y las opciones de la CLI. Devuelve false y deja el motivo en `error`.
bool leer_opciones(int argc, char** argv, Opciones& o, std::string& error);

// Punto de entrada común: MPI_Init_thread, opciones, esquema, reducción, verificación y CSV.
// Devuelve el código de salida del contrato §5.
int ejecutar_mpi(int argc, char** argv, const char* backend_por_defecto, const Esquema& esquema);

}  // namespace mpi_pi
