# T11 | Responsable: Ashley | Fuentes del núcleo compartido (Philox, Markov + gamma, balance hídrico).
add_library(pp_core STATIC
    philox_rng.cpp
    modelo_lluvia.cpp
    balance_hidrico.cpp)
target_include_directories(pp_core PUBLIC ${PROJECT_SOURCE_DIR}/include)
