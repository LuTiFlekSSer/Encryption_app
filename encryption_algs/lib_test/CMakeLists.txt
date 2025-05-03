cmake_minimum_required(VERSION 3.20)
project(lib_test C)

set(CMAKE_C_STANDARD 11)

include_directories(../magma/magma-base)
include_directories(../magma/magma-cbc)
include_directories(../magma/magma-ctr)
include_directories(../magma/magma-ecb)
include_directories(../kyznechik/kyznechik-base)
include_directories(../kyznechik/kyznechik-cbc)
include_directories(../kyznechik/kyznechik-ctr)
include_directories(../kyznechik/kyznechik-ecb)

add_executable(
        lib_test
        main.c
)

target_link_libraries(lib_test PRIVATE magma-base)
target_link_libraries(lib_test PRIVATE magma-cbc)
target_link_libraries(lib_test PRIVATE magma-ctr)
target_link_libraries(lib_test PRIVATE magma-ecb)
target_link_libraries(lib_test PRIVATE kyznechik-base)
target_link_libraries(lib_test PRIVATE kyznechik-cbc)
target_link_libraries(lib_test PRIVATE kyznechik-ctr)
target_link_libraries(lib_test PRIVATE kyznechik-ecb)
target_compile_options(lib_test PRIVATE -msse4.2 -mavx -mrdrnd)