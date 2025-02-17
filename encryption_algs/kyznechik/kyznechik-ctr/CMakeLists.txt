cmake_minimum_required(VERSION 3.20)
project(kyznechik-ctr C)

set(CMAKE_C_STANDARD 11)

include_directories(../kyznechik-base)
include_directories(../../utils)

add_library(
        kyznechik-ctr
        SHARED
        kyznechik-ctr.c
        kyznechik-ctr.h
)

target_link_libraries(kyznechik-ctr PRIVATE utils kyznechik-base)
target_compile_options(kyznechik-ctr PRIVATE -msse4.2 -mavx -mrdrnd)