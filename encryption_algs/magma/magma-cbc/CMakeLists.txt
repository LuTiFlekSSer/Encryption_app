cmake_minimum_required(VERSION 3.20)
project(magma-cbc C)

set(CMAKE_C_STANDARD 11)

include_directories(../magma-base)
include_directories(../../utils)

add_library(
        magma-cbc
        SHARED
        magma-cbc.c
        magma-cbc.h
)

target_link_libraries(magma-cbc PRIVATE utils magma-base)
target_compile_options(magma-cbc PRIVATE -msse4.2 -mavx -mrdrnd)