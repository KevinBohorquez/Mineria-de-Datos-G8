# T24 | Responsable: David | Objetivo híbrido MPI + OpenMP (MPI_THREAD_FUNNELED).
# Lo incluye el CMakeLists raíz con -DPP_BUILD_MPI=ON; necesita el backend OpenMP (PP_BUILD_OPENMP=ON).
if(NOT TARGET pp_openmp_lib OR NOT TARGET pp_mpi_esquemas)
  message(FATAL_ERROR "El híbrido necesita pp_openmp_lib (PP_BUILD_OPENMP=ON) y pp_mpi_esquemas (src/backends/mpi).")
endif()

add_executable(pp_hibrido main.cpp hibrido.cpp)
target_link_libraries(pp_hibrido PRIVATE pp_mpi_esquemas pp_openmp_lib)

# V1/V3/V4 con varias factorizaciones procesos x hilos: (1x2), (2x2) y (2x4) son las exigidas por T24.
# N = 10007 es primo: no es divisible entre ningún número de procesos.
set(HIBRIDO_ARGS --config ${PROJECT_SOURCE_DIR}/config/sintetico.yaml --n 10007 --dias 30 --verificar --silencioso)
set(HIBRIDO_PARES "1x2" "2x2" "2x4" "4x2" "4x4" "8x2")
execute_process(COMMAND ${MPIEXEC_EXECUTABLE} --version OUTPUT_VARIABLE MPIEXEC_VERSION ERROR_QUIET)
if(MPIEXEC_VERSION MATCHES "Open MPI|OpenRTE")
  # Sin --bind-to none, Open MPI ancla cada proceso a un núcleo y todos sus hilos comparten ese núcleo.
  set(HIBRIDO_EXTRA --oversubscribe --bind-to none)
endif()
foreach(par ${HIBRIDO_PARES})
  string(REPLACE "x" ";" pt ${par})
  list(GET pt 0 np)
  list(GET pt 1 hilos)
  add_test(NAME pp_hibrido_${np}x${hilos}
           COMMAND ${MPIEXEC_EXECUTABLE} ${MPIEXEC_NUMPROC_FLAG} ${np} ${HIBRIDO_EXTRA}
                   $<TARGET_FILE:pp_hibrido> ${HIBRIDO_ARGS} --hilos ${hilos} --schedule static
                   --salida ${CMAKE_BINARY_DIR}/pruebas/pp_hibrido_${np}x${hilos}.csv)
  set_tests_properties(pp_hibrido_${np}x${hilos} PROPERTIES
                       PASS_REGULAR_EXPRESSION "MPI_THREAD_(FUNNELED|SERIALIZED|MULTIPLE).*estado=OK.*v1_referencia=OK"
                       ENVIRONMENT "OMP_PROC_BIND=close;OMP_PLACES=cores" TIMEOUT 120)
endforeach()
