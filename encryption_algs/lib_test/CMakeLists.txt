cmake_minimum_required(VERSION 3.20)
project(lib_test C)

set(CMAKE_C_STANDARD 11)

include_directories(../kyznechik/kyznechik-ecb)

add_executable(
        lib_test
        main.c
)

target_link_libraries(lib_test PRIVATE kyznechik-ecb)
target_link_libraries(lib_test PRIVATE kyznechik-ctr)