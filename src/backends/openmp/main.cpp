// T15 | Responsable: Ashley | Backend OpenMP: ejecutable pp_openmp.
#include <chrono>
#include <exception>
#include <iostream>

#include "openmp.hpp"

int main(int argc, char** argv) {
    try {
        pp::Configuracion cfg;
        cfg.backend = "openmp";
        if (!pp::parsear_argumentos(argc, argv, cfg)) return 0;
        cfg.backend = "openmp";  // la etiqueta la fija el ejecutable, no el archivo de configuración

        const uint64_t clave = pp::derivar_clave(cfg.semilla, cfg.config_id);
        const auto t0 = std::chrono::steady_clock::now();
        const pp::Acumulador acc =
            pp::ejecutar_openmp(cfg.params, clave, cfg.config_id, cfg.n, 0, cfg.n, cfg.hilos, cfg.schedule);
        const auto t1 = std::chrono::steady_clock::now();

        pp::FilaResultado fila;
        fila.cfg = cfg;
        fila.acc = acc;
        fila.meta = pp::capturar_metadatos();
        fila.meta.tiempo_s = std::chrono::duration<double>(t1 - t0).count();
        fila.meta.hilos_usados = pp::hilos_efectivos();
        fila.meta.schedule_usado = pp::schedule_actual();

        if (acc.n != cfg.n) {  // V3 mínima: conservación del número de escenarios
            std::cerr << "error: se simularon " << acc.n << " escenarios y se esperaban " << cfg.n << "\n";
            return 3;
        }
        if (!cfg.silencioso) pp::imprimir_resumen(fila);
        if (!cfg.salida.empty()) pp::escribir_csv(cfg.salida, fila);
        return 0;
    } catch (const std::exception& e) {
        std::cerr << "error: " << e.what() << "\n";
        return 2;
    }
}
