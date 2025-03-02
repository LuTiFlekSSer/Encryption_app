cmake_minimum_required(VERSION 3.20)
project(kyznechik-cbc C)

set(CMAKE_C_STANDARD 11)

include_directories(../kyznechik-base)
include_directories(../../utils)

add_library(
        kyznechik-cbc
        SHARED
        kyznechik-cbc.c
        kyznechik-cbc.h
)

target_link_libraries(kyznechik-cbc PRIVATE utils kyznechik-base)
target_compile_options(kyznechik-cbc PRIVATE -msse4.2 -mavx -mrdrnd)