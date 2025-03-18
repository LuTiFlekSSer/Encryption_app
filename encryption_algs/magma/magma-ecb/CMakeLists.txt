cmake_minimum_required(VERSION 3.20)
project(magma-ecb C)

set(CMAKE_C_STANDARD 11)

include_directories(../magma-base)
include_directories(../../utils)

add_library(
        magma-ecb
        SHARED
        magma-ecb.c
        magma-ecb.h
)

target_link_libraries(magma-ecb PRIVATE utils magma-base)