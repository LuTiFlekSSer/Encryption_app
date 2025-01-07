cmake_minimum_required(VERSION 3.20)
project(main C)

set(CMAKE_C_STANDARD 11)

add_subdirectory(../kyznechik ../libs)
include_directories(../kyznechik)

add_executable(
        main
        main.c
)

target_link_libraries(main kyznechik)