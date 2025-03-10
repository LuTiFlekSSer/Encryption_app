cmake_minimum_required(VERSION 3.20)
project(magma-base C)

set(CMAKE_C_STANDARD 11)

add_library(
        magma-base
        SHARED
        magma.c
        magma.h
)
