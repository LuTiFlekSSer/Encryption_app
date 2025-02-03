cmake_minimum_required(VERSION 3.20)
project(kyznechik-ecb C)

set(CMAKE_C_STANDARD 11)

include_directories(../kyznechik-base)
include_directories(../../utils)

add_library(
        kyznechik-ecb
        SHARED
        kyznechik-ecb.c
        kyznechik-ecb.h
)

target_link_libraries(kyznechik-ecb PRIVATE utils kyznechik-base)