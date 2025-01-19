cmake_minimum_required(VERSION 3.20)
project(main C)

set(CMAKE_C_STANDARD 11)

add_subdirectory(../kyznechik/kyznechik-base ./kyznechik-base)
include_directories(../kyznechik/kyznechik-base)

add_subdirectory(../kyznechik/kyznechik-ecb ./kyznechik-ecb)
include_directories(../kyznechik/kyznechik-ecb)

include_directories(../utils)

add_executable(
        main
        main.c
)

target_link_libraries(main kyznechik-base)
target_link_libraries(main kyznechik-ecb)
target_link_libraries(main utils)