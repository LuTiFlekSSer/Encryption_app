cmake_minimum_required(VERSION 3.20)
project(lib_test C)

set(CMAKE_C_STANDARD 11)

include_directories(../magma/magma-base)

add_executable(
        lib_test
        main.c
)

target_link_libraries(lib_test PRIVATE magma-base)
target_compile_options(lib_test PRIVATE -msse4.2 -mavx -mrdrnd)