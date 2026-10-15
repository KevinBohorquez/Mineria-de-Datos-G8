# T04 | Responsable: Ashley | Compilación C/C++ del proyecto (C++17) y registro de pruebas CTest.
cmake_minimum_required(VERSION 3.16)
project(simulacion_inundacion VERSION 0.1.0 LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)
if(NOT CMAKE_BUILD_TYPE AND NOT CMAKE_CONFIGURATION_TYPES)
  set(CMAKE_BUILD_TYPE Release CACHE STRING "Tipo de compilación" FORCE)
endif()

option(PP_BUILD_OPENMP "Compilar el backend OpenMP (T15)" ON)
option(PP_BUILD_MPI    "Compilar los backends MPI y híbrido (T19, T20, T24; aún vacíos)" OFF)
option(PP_BUILD_CUDA   "Compilar la extensión CUDA (EXT1; solo si la activa T29)" OFF)
set(PP_SANITIZE "none" CACHE STRING "Instrumentación para V5: none | thread | address")
set_property(CACHE PP_SANITIZE PROPERTY STRINGS none thread address)

if(CMAKE_CXX_COMPILER_ID MATCHES "GNU|Clang")
  # -ffp-contract=off: sin FMA implícito, para que V1 sea bit a bit y no dependa del nivel de optimización.
  add_compile_options(-Wall -Wextra -ffp-contract=off)
  if(PP_SANITIZE STREQUAL "thread")
    add_compile_options(-fsanitize=thread -g -fno-omit-frame-pointer)
    add_link_options(-fsanitize=thread)
  elseif(PP_SANITIZE STREQUAL "address")
    add_compile_options(-fsanitize=address,undefined -g -fno-omit-frame-pointer)
    add_link_options(-fsanitize=address,undefined)
  endif()
endif()

enable_testing()

# Módulos compartidos (orden por dependencias)
add_subdirectory(src/core)
add_subdirectory(src/stats)
add_subdirectory(src/io)

# Backends disponibles
add_subdirectory(src/backends/serial)
if(PP_BUILD_OPENMP)
  add_subdirectory(src/backends/openmp)
endif()
# Los backends MPI, híbrido y CUDA siguen vacíos: no se exigen para compilar el núcleo.
if(PP_BUILD_MPI)
  add_subdirectory(src/backends/mpi)
  add_subdirectory(src/backends/hybrid)
endif()
if(PP_BUILD_CUDA)
  add_subdirectory(src/backends/cuda)
endif()

# Prueba de humo (T04)
add_executable(smoke tests/smoke/smoke.cpp)
target_link_libraries(smoke PRIVATE pp_io pp_stats pp_core)
add_test(NAME smoke COMMAND smoke)

# V1 (equivalencia serial vs OpenMP): pytest sobre los ejecutables compilados (T17)
if(PP_BUILD_OPENMP)
  find_package(Python3 COMPONENTS Interpreter QUIET)
  if(Python3_FOUND)
    add_test(NAME v1_equivalencia_openmp
             COMMAND ${Python3_EXECUTABLE} -m pytest -q ${PROJECT_SOURCE_DIR}/tests/integration/test_openmp_equivalencia.py)
    set_tests_properties(v1_equivalencia_openmp PROPERTIES ENVIRONMENT "PP_BIN_DIR=${CMAKE_BINARY_DIR}/src/backends")
  endif()
endif()
