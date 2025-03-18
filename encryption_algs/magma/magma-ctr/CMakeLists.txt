cmake_minimum_required(VERSION 3.20)
project(magma-ctr C)

set(CMAKE_C_STANDARD 11)

include_directories(../magma-base)
include_directories(../../utils)

add_library(
        magma-ctr
        SHARED
        magma-ctr.c
        magma-ctr.h
)

target_link_libraries(magma-ctr PRIVATE utils magma-base)
target_compile_options(magma-ctr PRIVATE -msse4.2 -mavx -mrdrnd)