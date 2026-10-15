// T11 | Responsable: Ashley | Generador de números aleatorios indexado (Philox4x32-10).
#include "simulacion.hpp"

namespace pp {

namespace {
constexpr uint32_t M0 = 0xD2511F53u;
constexpr uint32_t M1 = 0xCD9E8D57u;
constexpr uint32_t W0 = 0x9E3779B9u;  // parte dorada
constexpr uint32_t W1 = 0xBB67AE85u;  // sqrt(3) - 1

inline void mulhilo32(uint32_t a, uint32_t b, uint32_t& hi, uint32_t& lo) {
    const uint64_t p = static_cast<uint64_t>(a) * static_cast<uint64_t>(b);
    hi = static_cast<uint32_t>(p >> 32);
    lo = static_cast<uint32_t>(p);
}

inline uint64_t splitmix64(uint64_t x) {
    x += 0x9E3779B97F4A7C15ull;
    x = (x ^ (x >> 30)) * 0xBF58476D1CE4E5B9ull;
    x = (x ^ (x >> 27)) * 0x94D049BB133111EBull;
    return x ^ (x >> 31);
}
}  // namespace

Bloque4 philox4x32_10(Bloque4 c, uint32_t k0, uint32_t k1) {
    for (int ronda = 0; ronda < 10; ++ronda) {
        uint32_t hi0, lo0, hi1, lo1;
        mulhilo32(M0, c.v[0], hi0, lo0);
        mulhilo32(M1, c.v[2], hi1, lo1);
        const Bloque4 s = {{hi1 ^ c.v[1] ^ k0, lo1, hi0 ^ c.v[3] ^ k1, lo0}};
        c = s;
        k0 += W0;
        k1 += W1;
    }
    return c;
}

uint64_t derivar_clave(uint64_t semilla, uint64_t config_id) {
    // Mezcla determinista de semilla global y configuración; no depende de hilos ni procesos.
    return splitmix64(splitmix64(semilla) ^ (config_id * 0xD6E8FEB86659FD93ull + 0x2545F4914F6CDD1Dull));
}

double uniforme32(uint32_t w) {
    return (static_cast<double>(w) + 0.5) * (1.0 / 4294967296.0);
}

}  // namespace pp
