# T15 | Responsable: Ashley | Objetivo OpenMP.
find_package(OpenMP REQUIRED COMPONENTS CXX)
add_executable(pp_openmp main.cpp)
target_link_libraries(pp_openmp PRIVATE pp_io pp_stats pp_core OpenMP::OpenMP_CXX)
