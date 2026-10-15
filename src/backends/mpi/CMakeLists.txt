# T19,T20 | Responsable: David | Objetivos MPI estático (E1) y dinámico (E2).
# Se incluye desde el CMakeLists raíz con add_subdirectory(src/backends/mpi).
find_package(MPI REQUIRED COMPONENTS CXX)

set(MPI_INCLUDE_PIEZAS ${CMAKE_CURRENT_LIST_DIR}/../../../include)

execute_process(COMMAND git rev-parse --short HEAD
                WORKING_DIRECTORY ${CMAKE_CURRENT_LIST_DIR}
                OUTPUT_VARIABLE GIT_COMMIT_CORTO OUTPUT_STRIP_TRAILING_WHITESPACE ERROR_QUIET)

add_library(mpi_comun STATIC comun.cpp)
target_compile_features(mpi_comun PUBLIC cxx_std_17)
target_include_directories(mpi_comun PUBLIC ${MPI_INCLUDE_PIEZAS})
target_link_libraries(mpi_comun PUBLIC MPI::MPI_CXX)
target_compile_definitions(mpi_comun PRIVATE GIT_COMMIT_CORTO="${GIT_COMMIT_CORTO}")

add_executable(mpi_estatico estatico.cpp)
target_link_libraries(mpi_estatico PRIVATE mpi_comun)

add_executable(mpi_dinamico dinamico.cpp)
target_link_libraries(mpi_dinamico PRIVATE mpi_comun)

# Pruebas V1 (referencia secuencial), V3 (suma = N) y V4 (reproducibilidad) con 1/2/4/8/16 procesos.
# N = 10007 es primo: no es divisible entre ningún número de procesos probado.
set(MPI_ARGS_PRUEBA --estacion prueba --regimen normal --capacidad_mm_dia 30 --umbral_mm 50
    --semilla 1 --escenarios 10007 --dias 30 --lote 100 --verificar)
set(MPI_NP_PRUEBA 1 2 4 8 16)
execute_process(COMMAND ${MPIEXEC_EXECUTABLE} --version OUTPUT_VARIABLE MPIEXEC_VERSION ERROR_QUIET)
if(MPIEXEC_VERSION MATCHES "Open MPI|OpenRTE")
  set(MPI_EXTRA_PRUEBA --oversubscribe)
endif()
foreach(esquema mpi_estatico mpi_dinamico)
  foreach(np ${MPI_NP_PRUEBA})
    add_test(NAME ${esquema}_np${np}
             COMMAND ${MPIEXEC_EXECUTABLE} ${MPIEXEC_NUMPROC_FLAG} ${np} ${MPI_EXTRA_PRUEBA}
                     $<TARGET_FILE:${esquema}> ${MPI_ARGS_PRUEBA}
                     --salida ${CMAKE_BINARY_DIR}/pruebas/${esquema}_np${np}.csv)
    set_tests_properties(${esquema}_np${np} PROPERTIES PASS_REGULAR_EXPRESSION "estado=OK.*v1_referencia=OK"
                         TIMEOUT 120)
  endforeach()
endforeach()
