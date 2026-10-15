# T19,T20 | Responsable: David | Objetivos MPI estático (E1) y dinámico (E2).
# El CMakeLists raíz lo incluye con -DPP_BUILD_MPI=ON.
find_package(MPI REQUIRED COMPONENTS CXX)

add_library(pp_mpi_comun STATIC comun.cpp)
target_include_directories(pp_mpi_comun PUBLIC ${PROJECT_SOURCE_DIR}/include)
target_link_libraries(pp_mpi_comun PUBLIC MPI::MPI_CXX pp_io pp_stats pp_core)

# Esquemas de reparto como biblioteca: los reutiliza el híbrido (T24).
add_library(pp_mpi_esquemas STATIC estatico.cpp dinamico.cpp)
target_link_libraries(pp_mpi_esquemas PUBLIC pp_mpi_comun)

add_executable(pp_mpi_estatico main_estatico.cpp)
target_link_libraries(pp_mpi_estatico PRIVATE pp_mpi_esquemas)

add_executable(pp_mpi_dinamico main_dinamico.cpp)
target_link_libraries(pp_mpi_dinamico PRIVATE pp_mpi_esquemas)

# Pruebas V1 (referencia secuencial), V3 (suma = N) y V4 (reproducibilidad) con 1/2/4/8/16 procesos.
# N = 10007 es primo: no es divisible entre ningún número de procesos probado.
set(MPI_ARGS_PRUEBA --config ${PROJECT_SOURCE_DIR}/config/sintetico.yaml
    --n 10007 --dias 30 --lote 100 --verificar --silencioso)
set(MPI_NP_PRUEBA 1 2 4 8 16)
execute_process(COMMAND ${MPIEXEC_EXECUTABLE} --version OUTPUT_VARIABLE MPIEXEC_VERSION ERROR_QUIET)
if(MPIEXEC_VERSION MATCHES "Open MPI|OpenRTE")
  set(MPI_EXTRA_PRUEBA --oversubscribe)
endif()
foreach(esquema pp_mpi_estatico pp_mpi_dinamico)
  foreach(np ${MPI_NP_PRUEBA})
    add_test(NAME ${esquema}_np${np}
             COMMAND ${MPIEXEC_EXECUTABLE} ${MPIEXEC_NUMPROC_FLAG} ${np} ${MPI_EXTRA_PRUEBA}
                     $<TARGET_FILE:${esquema}> ${MPI_ARGS_PRUEBA}
                     --salida ${CMAKE_BINARY_DIR}/pruebas/${esquema}_np${np}.csv)
    set_tests_properties(${esquema}_np${np} PROPERTIES PASS_REGULAR_EXPRESSION "estado=OK.*v1_referencia=OK"
                         TIMEOUT 120)
  endforeach()
endforeach()
