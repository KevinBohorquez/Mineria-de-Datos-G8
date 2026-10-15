# T12 | Responsable: Ashley | Fuentes de estadísticas (Wilson, histograma).
add_library(pp_stats STATIC wilson.cpp histograma.cpp)
target_include_directories(pp_stats PUBLIC ${PROJECT_SOURCE_DIR}/include)
target_link_libraries(pp_stats PUBLIC pp_core)
