// T19,T20 | Responsable: David | Piezas comunes de los ejecutables MPI (contrato docs/contratos.md).
#include "mpi_comun.hpp"

#include <algorithm>
#include <cerrno>
#include <cmath>
#include <cstdio>
#include <cstdlib>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <set>
#include <sstream>
#include <stdexcept>
#include <thread>
#include <vector>

#ifndef GIT_COMMIT_CORTO
#define GIT_COMMIT_CORTO ""
#endif

namespace mpi_pi {

namespace {

constexpr std::uint64_t DORADO = 0x9E3779B97F4A7C15ULL;

std::uint64_t splitmix64(std::uint64_t x) {
    x += DORADO;
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ULL;
    x = (x ^ (x >> 27)) * 0x94D049BB133111EBULL;
    return x ^ (x >> 31);
}

double uniforme(std::uint64_t clave, std::uint64_t indice, std::uint64_t dia, std::uint64_t flujo) {
    const std::uint64_t h = splitmix64(clave ^ splitmix64(indice * 4 + flujo + (dia << 40)));
    return static_cast<double>(h >> 11) * (1.0 / 9007199254740992.0);
}

std::string recortar(const std::string& s) {
    const char* esp = " \t\r\n\"'";
    const auto a = s.find_first_not_of(esp);
    if (a == std::string::npos) return "";
    const auto b = s.find_last_not_of(esp);
    return s.substr(a, b - a + 1);
}

bool a_u64(const std::string& s, std::uint64_t& v) {
    if (s.empty() || s[0] == '-' || s[0] == '+') return false;
    char* fin = nullptr;
    errno = 0;
    const unsigned long long r = std::strtoull(s.c_str(), &fin, 10);
    if (errno != 0 || *fin != '\0') return false;
    v = r;
    return true;
}

bool a_real(const std::string& s, double& v) {
    if (s.empty()) return false;
    char* fin = nullptr;
    errno = 0;
    const double r = std::strtod(s.c_str(), &fin);
    if (errno != 0 || *fin != '\0' || !std::isfinite(r)) return false;
    v = r;
    return true;
}

// Aplica un par clave/valor del YAML o de la CLI. Devuelve false si la clave o el valor no son válidos.
bool asignar(Opciones& o, std::set<std::string>& vistas, const std::string& clave, const std::string& valor,
             std::string& error) {
    auto malo = [&](const char* que) {
        error = std::string("valor inválido para '") + clave + "' (" + que + "): " + valor;
        return false;
    };
    std::uint64_t u = 0;
    double r = 0.0;
    vistas.insert(clave);
    if (clave == "estacion") { o.estacion = valor; return !valor.empty() || malo("texto no vacío"); }
    if (clave == "regimen") {
        if (valor != "normal" && valor != "el_nino") return malo("normal | el_nino");
        o.regimen = valor;
        return true;
    }
    if (clave == "capacidad_mm_dia") { if (!a_real(valor, r) || r <= 0) return malo("real > 0"); o.capacidad_mm_dia = r; return true; }
    if (clave == "umbral_mm") { if (!a_real(valor, r) || r <= 0) return malo("real > 0"); o.umbral_mm = r; return true; }
    if (clave == "dias") { if (!a_u64(valor, u) || u < 1) return malo("entero >= 1"); o.dias = u; return true; }
    if (clave == "semilla") { if (!a_u64(valor, u)) return malo("entero sin signo de 64 bits"); o.semilla = u; return true; }
    if (clave == "escenarios") { if (!a_u64(valor, u) || u < 1) return malo("entero >= 1"); o.escenarios = u; return true; }
    if (clave == "configuracion_id") { if (!a_u64(valor, u)) return malo("entero >= 0"); o.configuracion_id = u; return true; }
    if (clave == "hilos") { if (!a_u64(valor, u) || u < 1) return malo("entero >= 1"); o.hilos = u; return true; }
    if (clave == "lote") { if (!a_u64(valor, u) || u < 1) return malo("entero >= 1"); o.lote = u; return true; }
    if (clave == "salida") { o.salida = valor; return true; }
    if (clave == "parametros") { return true; }  // reservado para los parámetros calibrados (T10/T12)
    if (clave == "backend") {
        static const std::set<std::string> validos = {"serial", "openmp", "mpi_estatico", "mpi_dinamico", "hibrido", "cuda"};
        if (!validos.count(valor)) return malo("backend desconocido");
        o.backend = valor;
        return true;
    }
    error = "clave desconocida: " + clave;
    return false;
}

bool leer_yaml(const std::string& ruta, Opciones& o, std::set<std::string>& vistas, std::string& error) {
    std::ifstream f(ruta);
    if (!f) { error = "no se pudo abrir la configuración: " + ruta; return false; }
    std::string linea;
    int numero = 0;
    while (std::getline(f, linea)) {
        ++numero;
        const auto c = linea.find('#');
        if (c != std::string::npos) linea.erase(c);
        linea = recortar(linea);
        if (linea.empty()) continue;
        const auto p = linea.find(':');
        if (p == std::string::npos) { error = ruta + ":" + std::to_string(numero) + ": falta ':'"; return false; }
        if (!asignar(o, vistas, recortar(linea.substr(0, p)), recortar(linea.substr(p + 1)), error)) {
            error = ruta + ":" + std::to_string(numero) + ": " + error;
            return false;
        }
    }
    return true;
}

std::string hardware_nodo() {
    char nombre[MPI_MAX_PROCESSOR_NAME] = {0};
    int len = 0;
    MPI_Get_processor_name(nombre, &len);
    std::string h = std::string(nombre) + " hilos_hw=" + std::to_string(std::thread::hardware_concurrency());
    std::replace(h.begin(), h.end(), ',', ' ');
    return h;
}

std::string commit_actual() {
    if (std::string(GIT_COMMIT_CORTO).size() > 0) return GIT_COMMIT_CORTO;
    if (const char* e = std::getenv("GIT_COMMIT")) return e;
    return "unknown";
}

std::string valor_entorno(const char* nombre, const char* defecto) {
    const char* e = std::getenv(nombre);
    return (e && *e) ? e : defecto;
}

void escribir_csv(const Opciones& o, const Acumulador& a, int procesos, double tiempo_s) {
    namespace fs = std::filesystem;
    const fs::path ruta(o.salida);
    if (ruta.has_parent_path()) fs::create_directories(ruta.parent_path());
    const bool nuevo = !fs::exists(ruta) || fs::file_size(ruta) == 0;
    std::ofstream f(ruta, std::ios::app);
    if (!f) throw std::runtime_error("no se pudo escribir " + o.salida);
    if (nuevo) {
        f << "version_contrato,backend,estacion,regimen,capacidad_mm_dia,umbral_mm,dias,semilla,configuracion_id,"
             "n_solicitado,n_simulado,inundaciones,p_hat,histograma,procesos,hilos,repeticion,calentamiento,"
             "tiempo_s,commit,hardware,afinidad,schedule\n";
    }
    std::ostringstream h;
    for (int b = 0; b < NBINS; ++b) h << (b ? ";" : "") << a.hist[b];
    char num[64];
    f << VERSION_CONTRATO << ',' << o.backend << ',' << o.estacion << ',' << o.regimen << ',';
    std::snprintf(num, sizeof num, "%g", o.capacidad_mm_dia); f << num << ',';
    std::snprintf(num, sizeof num, "%g", o.umbral_mm); f << num << ',';
    f << o.dias << ',' << o.semilla << ',' << o.configuracion_id << ',' << o.escenarios << ',' << a.n << ','
      << a.k << ',';
    std::snprintf(num, sizeof num, "%.10f", a.n ? static_cast<double>(a.k) / static_cast<double>(a.n) : 0.0);
    f << num << ",\"" << h.str() << "\"," << procesos << ',' << o.hilos << ',' << o.repeticion << ','
      << (o.calentamiento ? 1 : 0) << ',';
    std::snprintf(num, sizeof num, "%.6f", tiempo_s);
    f << num << ',' << commit_actual() << ",\"" << hardware_nodo() << "\","
      << valor_entorno("OMP_PROC_BIND", "none") << ',' << valor_entorno("OMP_SCHEDULE", "none") << '\n';
}

}  // namespace

int clase_histograma(double maximo_mm) {
    if (!(maximo_mm > 0.0)) return 0;
    if (maximo_mm >= NBINS) return NBINS - 1;
    return static_cast<int>(std::floor(maximo_mm));
}

std::uint64_t clave_configuracion(std::uint64_t semilla, std::uint64_t configuracion_id) {
    return splitmix64(semilla + configuracion_id * DORADO);
}

FuncionEscenario escenario_provisional(const Opciones& o) {
    const std::uint64_t clave = clave_configuracion(o.semilla, o.configuracion_id);
    const std::uint64_t dias = o.dias;
    const double C = o.capacidad_mm_dia;
    const double U = o.umbral_mm;
    return [=](std::uint64_t indice, Acumulador& acc) {
        double A = 0.0, Amax = 0.0;
        bool lluvioso = false;
        for (std::uint64_t d = 0; d < dias; ++d) {
            lluvioso = uniforme(clave, indice, d, 0) < (lluvioso ? 0.6 : 0.2);
            const double R = lluvioso ? -8.0 * std::log1p(-uniforme(clave, indice, d, 1)) : 0.0;
            A = std::max(0.0, A + R - C);
            Amax = std::max(Amax, A);
        }
        acc.k += (Amax > U) ? 1 : 0;
        acc.n += 1;
        acc.hist[clase_histograma(Amax)] += 1;
    };
}

bool leer_opciones(int argc, char** argv, Opciones& o, std::string& error) {
    std::set<std::string> vistas;
    // Primero el YAML, para que la CLI tenga prioridad.
    for (int i = 1; i + 1 < argc; ++i) {
        if (std::string(argv[i]) == "--config") { o.config = argv[i + 1]; break; }
    }
    if (!o.config.empty() && !leer_yaml(o.config, o, vistas, error)) return false;

    for (int i = 1; i < argc; ++i) {
        const std::string a = argv[i];
        if (a == "--calentamiento") { o.calentamiento = true; continue; }
        if (a == "--verificar") { o.verificar = true; continue; }
        if (a.rfind("--", 0) != 0) { error = "argumento inesperado: " + a; return false; }
        if (i + 1 >= argc) { error = "falta el valor de " + a; return false; }
        const std::string valor = argv[++i];
        const std::string clave = a.substr(2);
        std::uint64_t u = 0;
        if (clave == "config") continue;
        if (clave == "repeticion") {
            if (!a_u64(valor, u) || u > 1000000) { error = "valor inválido para --repeticion"; return false; }
            o.repeticion = static_cast<int>(u);
        } else if (!asignar(o, vistas, clave, valor, error)) {
            return false;
        }
    }
    if (o.calentamiento) o.repeticion = 0;

    for (const char* req : {"estacion", "regimen", "capacidad_mm_dia", "umbral_mm", "semilla", "escenarios"}) {
        if (!vistas.count(req)) { error = std::string("falta la opción obligatoria '") + req + "'"; return false; }
    }
    return true;
}

int ejecutar_mpi(int argc, char** argv, const char* backend_por_defecto, const Esquema& esquema) {
    int provisto = 0;
    if (MPI_Init_thread(&argc, &argv, MPI_THREAD_FUNNELED, &provisto) != MPI_SUCCESS) return 3;
    int rango = 0, procesos = 1;
    MPI_Comm_rank(MPI_COMM_WORLD, &rango);
    MPI_Comm_size(MPI_COMM_WORLD, &procesos);

    int codigo = 0;
    try {
        Opciones o;
        o.backend = backend_por_defecto;
        std::string error;
        int valido = leer_opciones(argc, argv, o, error) ? 1 : 0;
        if (!valido) {
            if (rango == 0) std::cerr << "error: " << error << '\n';
            MPI_Finalize();
            return 1;
        }
        if (o.backend != backend_por_defecto) {
            if (rango == 0) std::cerr << "aviso: el ejecutable fija backend=" << backend_por_defecto << '\n';
            o.backend = backend_por_defecto;
        }
        if (o.salida.empty()) o.salida = std::string("results/raw/") + o.backend + ".csv";

        const FuncionEscenario escenario = escenario_provisional(o);

        MPI_Barrier(MPI_COMM_WORLD);
        const double t0 = MPI_Wtime();
        Acumulador local;
        const ResumenRango res = esquema(MPI_COMM_WORLD, o, escenario, local);

        // Una sola colectiva: k, n y los bins se suman en el rango 0 (contrato §3).
        std::vector<std::uint64_t> en(2 + NBINS), fuera(2 + NBINS, 0);
        en[0] = local.k;
        en[1] = local.n;
        std::copy(local.hist, local.hist + NBINS, en.begin() + 2);
        MPI_Reduce(en.data(), fuera.data(), 2 + NBINS, MPI_UINT64_T, MPI_SUM, 0, MPI_COMM_WORLD);
        const double tiempo = MPI_Wtime() - t0;

        std::uint64_t mio[5] = {res.inicio, res.fin, res.bloques, res.n_local, res.coherente ? 1ULL : 0ULL};
        std::vector<std::uint64_t> todos(rango == 0 ? 5 * static_cast<size_t>(procesos) : 0);
        MPI_Gather(mio, 5, MPI_UINT64_T, todos.data(), 5, MPI_UINT64_T, 0, MPI_COMM_WORLD);

        if (rango == 0) {
            Acumulador g;
            g.k = fuera[0];
            g.n = fuera[1];
            std::copy(fuera.begin() + 2, fuera.end(), g.hist);

            std::cout << "[verif] backend=" << o.backend << " procesos=" << procesos << " n_solicitado=" << o.escenarios
                      << " nivel_hilos_mpi=" << provisto << " nucleo=provisional\n";
            std::uint64_t suma_local = 0;
            bool coherentes = true;
            for (int r = 0; r < procesos; ++r) {
                const std::uint64_t* t = &todos[5 * static_cast<size_t>(r)];
                std::cout << "[verif] rango=" << r;
                if (o.backend == "mpi_estatico") std::cout << " inicio=" << t[0] << " fin=" << t[1];
                else std::cout << " bloques=" << t[2];
                std::cout << " n_local=" << t[3] << '\n';
                suma_local += t[3];
                coherentes = coherentes && t[4] == 1;
            }
            if (o.backend == "mpi_estatico") {  // intervalos contiguos, sin solape ni huecos
                std::uint64_t esperado = 0;
                for (int r = 0; r < procesos; ++r) {
                    const std::uint64_t* t = &todos[5 * static_cast<size_t>(r)];
                    if (t[0] != esperado || t[1] < t[0]) coherentes = false;
                    esperado = t[1];
                }
                if (esperado != o.escenarios) coherentes = false;
            }
            std::uint64_t suma_hist = 0;
            for (int b = 0; b < NBINS; ++b) suma_hist += g.hist[b];
            const bool ok = coherentes && g.n == o.escenarios && suma_local == o.escenarios && suma_hist == g.n && g.k <= g.n;
            std::cout << "[verif] suma_n=" << g.n << " suma_n_rangos=" << suma_local << " suma_hist=" << suma_hist
                      << " k=" << g.k << " estado=" << (ok ? "OK" : "FALLO") << '\n';
            if (!ok) codigo = 2;

            if (o.verificar && ok) {
                Acumulador ref;
                for (std::uint64_t i = 0; i < o.escenarios; ++i) escenario(i, ref);
                const bool igual = ref.k == g.k && ref.n == g.n && std::equal(ref.hist, ref.hist + NBINS, g.hist);
                std::cout << "[verif] v1_referencia=" << (igual ? "OK" : "FALLO") << " k_ref=" << ref.k << '\n';
                if (!igual) codigo = 2;
            }
            std::cout << "[verif] tiempo_s=" << tiempo << '\n';
            if (codigo == 0) escribir_csv(o, g, procesos, tiempo);
        }
    } catch (const std::exception& e) {
        std::cerr << "error en el rango " << rango << ": " << e.what() << '\n';
        MPI_Abort(MPI_COMM_WORLD, 3);
    }
    MPI_Bcast(&codigo, 1, MPI_INT, 0, MPI_COMM_WORLD);
    MPI_Finalize();
    return codigo;
}

}  // namespace mpi_pi
