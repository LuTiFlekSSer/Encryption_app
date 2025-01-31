cmake_minimum_required(VERSION 3.20)
project(utils C)

set(CMAKE_C_STANDARD 11)

add_library(
        utils
        SHARED
        utils.c
        utils.h
)

#set(LIBRARY_OUTPUT_PATH "${CMAKE_HOME_DIRECTORY}/../libs")