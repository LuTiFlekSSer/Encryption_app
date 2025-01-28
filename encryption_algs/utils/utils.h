#ifndef UTILS_H
#define UTILS_H

#include <stdint.h>
#include <windows.h>

enum CIPHER_TYPE {
    KYZNECHIK = 0,
    MAGMA = 1,
    GOST_89 = 2
};

enum CIPHER_MODE {
    ECB = 0,
    CBC = 1,
    CTR = 2,
    XTS = 3
};

typedef struct {
    HANDLE file;
    uint64_t offset;
    uint8_t *data;
    uint32_t data_size;
} file_block_info;

typedef struct {
    uint64_t result;
    uint8_t error;
} func_result;

typedef struct {
    uint64_t start, end;
    uint64_t *current_step;
    CRITICAL_SECTION *lock;
    HANDLE input_file, output_file;
} thread_data;


func_result get_disk_free_space(const uint8_t *disk_name);
func_result get_file_size(HANDLE file);

func_result write_block_to_file(LPCVOID block_info);
func_result read_block_from_file(LPCVOID block_info);

func_result write_metadata_to_file(
    HANDLE file,
    uint64_t offset,
    uint8_t const *metadata,
    uint8_t metadata_size,
    uint8_t const *cipher_info
);

void close_files(HANDLE file1, HANDLE file2);

#endif
