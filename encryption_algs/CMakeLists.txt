cmake_minimum_required(VERSION 3.20)
project(Encryption_app C)

set(CMAKE_C_STANDARD 11)

set(LIBS_DIR ${CMAKE_SOURCE_DIR}/libs)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${LIBS_DIR})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${LIBS_DIR}/debug)
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${LIBS_DIR}/release)

add_subdirectory(utils)
add_subdirectory(kyznechik/kyznechik-base)
add_subdirectory(kyznechik/kyznechik-ecb)
add_subdirectory(kyznechik/kyznechik-ctr)
add_subdirectory(lib_test)
