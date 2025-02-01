cmake_minimum_required(VERSION 3.20)
project(Encryption_app C)

set(CMAKE_C_STANDARD 11)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY ${CMAKE_SOURCE_DIR}/libs)

set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_DEBUG ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})
set(CMAKE_RUNTIME_OUTPUT_DIRECTORY_RELEASE ${CMAKE_RUNTIME_OUTPUT_DIRECTORY})

add_subdirectory(utils)
add_subdirectory(kyznechik/kyznechik-base)
add_subdirectory(kyznechik/kyznechik-ecb)
add_subdirectory(lib_test)