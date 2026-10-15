// T19,T20 | Responsable: David | Piezas comunes de los ejecutables MPI (contrato docs/contratos.md).
#include "mpi_comun.hpp"

#include <algorithm>
#include <exception>
#include <iostream>
#include <stdexcept>
#include <vector>

#include "simulacion.hpp"

namespace mpi_pi {

FuncionEscenario escenario_del_modelo(const pp::Configuracion& cfg) {
    const pp::Parametros params = cfg.params;
    const std::uint64_t clave = pp::derivar_clave(cfg.semilla, cfg.config_id);
    const std::uint64_t base = cfg.config_id * cfg.n;  // índice global i = c*N + j
    return [=](std::uint64_t j, pp::Acumulador& acc) { acc.agregar(pp::simular_escenario(params, clave, base + j)); };
}

int ejecutar_mpi(int argc, char** argv, const char* backend, const Esquema& esquema) {
    int provisto = 0;
    if (MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provisto) != MPI_SUCCESS) return 2;
    int rango = 0, procesos = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rango);
    MPI_Comm_size(MPI_COMM_WORLD, &procesos);

    pp::Configuracion cfg;
    cfg.backend = backend;
    try {
        if (!pp::parsear_argumentos(argc, argv, cfg)) {  // --ayuda
            MPI_Finalize();
            return 0;
        }
    } catch (const std::exception& e) {
        if (rango == 0) std::cerr << "error: " << e.what() << '\n';
        MPI_Finalize();
        return 2;
    }
    cfg.backend = backend;  // la etiqueta la fija el ejecutable, no el archivo de configuración

    int codigo = 0;
    try {
        const FuncionEscenario escenario = escenario_del_modelo(cfg);

        MPI_Barrier(MPI_COMM_WORLD);
        const double t0 = MPI_Wtime();
        pp::Acumulador local;
        const ResumenRango res = esquema(MPI_COMM_WORLD, cfg, escenario, local);

        // Una sola colectiva: k, n y los bins se suman en el rango 0 (contrato §3).
        std::vector<std::uint64_t> en(2 + pp::NBINS), fuera(2 + pp::NBINS, 0);
        en[0] = local.k;
        en[1] = local.n;
        std::copy(local.hist.begin(), local.hist.end(), en.begin() + 2);
        MPI_Reduce(en.data(), fuera.data(), 2 + pp::NBINS, MPI_UINT64_T, MPI_SUM, 0, MPI_COMM_WORLD);
        const double tiempo = MPI_Wtime() - t0;

        const std::uint64_t mio[5] = {res.inicio, res.fin, res.bloques, res.n_local, res.coherente ? 1ULL : 0ULL};
        std::vector<std::uint64_t> todos(rango == 0 ? 5 * static_cast<size_t>(procesos) : 0);
        MPI_Gather(mio, 5, MPI_UINT64_T, todos.data(), 5, MPI_UINT64_T, 0, MPI_COMM_WORLD);

        if (rango == 0) {
            pp::Acumulador g;
            g.k = fuera[0];
            g.n = fuera[1];
            std::copy(fuera.begin() + 2, fuera.end(), g.hist.begin());

            std::cout << "[verif] backend=" << cfg.backend << " procesos=" << procesos << " n_solicitado=" << cfg.n
                      << " nivel_hilos_mpi=" << provisto << " nucleo=pp_core\n";
            std::uint64_t suma_local = 0;
            bool coherentes = true;
            for (int r = 0; r < procesos; ++r) {
                const std::uint64_t* t = &todos[5 * static_cast<size_t>(r)];
                std::cout << "[verif] rango=" << r;
                if (cfg.backend == "mpi_estatico") std::cout << " inicio=" << t[0] << " fin=" << t[1];
                else std::cout << " bloques=" << t[2];
                std::cout << " n_local=" << t[3] << '\n';
                suma_local += t[3];
                coherentes = coherentes && t[4] == 1;
            }
            if (cfg.backend == "mpi_estatico") {  // intervalos contiguos, sin solape ni huecos
                std::uint64_t esperado = 0;
                for (int r = 0; r < procesos; ++r) {
                    const std::uint64_t* t = &todos[5 * static_cast<size_t>(r)];
                    if (t[0] != esperado || t[1] < t[0]) coherentes = false;
                    esperado = t[1];
                }
                if (esperado != cfg.n) coherentes = false;
            }
            std::uint64_t suma_hist = 0;
            for (std::uint64_t h : g.hist) suma_hist += h;
            const bool ok = coherentes && g.n == cfg.n && suma_local == cfg.n && suma_hist == g.n && g.k <= g.n;
            std::cout << "[verif] suma_n=" << g.n << " suma_n_rangos=" << suma_local << " suma_hist=" << suma_hist
                      << " k=" << g.k << " estado=" << (ok ? "OK" : "FALLO") << '\n';
            if (!ok) codigo = 3;

            if (cfg.verificar && ok) {  // V1: igual a la referencia secuencial, bit a bit
                pp::Acumulador ref;
                for (std::uint64_t j = 0; j < cfg.n; ++j) escenario(j, ref);
                const bool igual = ref == g;
                std::cout << "[verif] v1_referencia=" << (igual ? "OK" : "FALLO") << " k_ref=" << ref.k << '\n';
                if (!igual) codigo = 3;
            }
            std::cout << "[verif] tiempo_s=" << tiempo << '\n';

            if (codigo == 0) {
                pp::FilaResultado fila;
                fila.cfg = cfg;
                fila.acc = g;
                fila.meta = pp::capturar_metadatos();
                fila.meta.tiempo_s = tiempo;
                fila.meta.hilos_usados = 1;
                fila.meta.procesos = procesos;
                if (!cfg.silencioso) pp::imprimir_resumen(fila);
                if (!cfg.salida.empty()) pp::escribir_csv(cfg.salida, fila);
            }
        }
    } catch (const std::exception& e) {
        std::cerr << "error en el rango " << rango << ": " << e.what() << '\n';
        MPI_Abort(MPI_COMM_WORLD, 2);
    }
    MPI_Bcast(&codigo, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return codigo;
}

}  // namespace mpi_pi
