# T15 | Responsable: Ashley | Objetivo OpenMP: biblioteca (la reutiliza el híbrido, T24) y ejecutable.
find_package(OpenMP REQUIRED COMPONENTS CXX)
add_library(pp_openmp_lib STATIC ejecutor.cpp)
target_link_libraries(pp_openmp_lib PUBLIC pp_io pp_stats pp_core OpenMP::OpenMP_CXX)
add_executable(pp_openmp main.cpp)
target_link_libraries(pp_openmp PRIVATE pp_openmp_lib)
