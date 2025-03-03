cmake_minimum_required(VERSION 3.20)
project(lib_test C)

set(CMAKE_C_STANDARD 11)

include_directories(../kyznechik/kyznechik-ecb)
include_directories(../kyznechik/kyznechik-ctr)
include_directories(../kyznechik/kyznechik-cbc)
include_directories(../kyznechik/kyznechik-base)

add_executable(
        lib_test
        main.c
)

target_link_libraries(lib_test PRIVATE kyznechik-base)
target_link_libraries(lib_test PRIVATE kyznechik-ecb)
target_link_libraries(lib_test PRIVATE kyznechik-ctr)
target_link_libraries(lib_test PRIVATE kyznechik-cbc)
target_compile_options(lib_test PRIVATE -msse4.2 -mavx -mrdrnd)