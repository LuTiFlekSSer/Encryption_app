cmake_minimum_required(VERSION 3.20)
project(kyznechik C)

set(CMAKE_C_STANDARD 11)

add_library(
        kyznechik
        SHARED
        kyznechik.c
        kyznechik.h
)

set(LIBRARY_OUTPUT_PATH "../../libs")

#if(WIN32)
#    add_custom_command(TARGET kyznechik POST_BUILD
#        COMMAND ${CMAKE_COMMAND} -E remove "${LIBRARY_OUTPUT_PATH}/lib${PROJECT_NAME}.dll.a"
#    )
#endif()