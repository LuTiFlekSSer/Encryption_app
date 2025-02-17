#ifndef UTILS_H
#define UTILS_H

#include <stdint.h>
#include <windows.h>

#define CIPHER_TYPES 3

typedef enum {
    KYZNECHIK = 0,
    MAGMA = 1,
    GOST_89 = 2
} CIPHER_TYPE;

#define CIPHER_MODES 4

typedef enum {
    ECB = 0,
    CBC = 1,
    CTR = 2,
    XTS = 3
} CIPHER_MODE;

typedef enum {
    ENCRYPT = 0,
    DECRYPT = 1
} CIPHER_FUNC_TYPE;

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
    uint8_t *error, **Ks;
    CIPHER_FUNC_TYPE func_type;
    __uint128_t gamma;
} thread_data;

uint32_t const BUF_SIZE = 1024 * 256 * 4 * 4;

func_result get_disk_free_space(const WCHAR *disk_name);
func_result get_file_size(HANDLE file);

func_result write_block_to_file(LPCVOID block_info, HANDLE event);
func_result read_block_from_file(LPCVOID block_info, HANDLE event);

func_result write_metadata_to_file(
    HANDLE file,
    uint64_t offset,
    uint8_t const *metadata,
    uint8_t metadata_size,
    uint8_t const *cipher_info
);

uint8_t read_cipher_from_file(
    const WCHAR *file_name,
    uint8_t *cipher_type,
    uint8_t *cipher_mode
);

void open_files(const WCHAR *file_in_path, const WCHAR *file_out_path, HANDLE *input_file, HANDLE *output_file);
void close_files(HANDLE file1, HANDLE file2);
uint8_t check_files(HANDLE input_file, HANDLE output_file, uint64_t free_disk_space, uint64_t file_size,
                    uint64_t metadata_size);

uint8_t create_threads_data(uint16_t num_threads, thread_data **threads_data, DWORD **threads_id, HANDLE **threads);
void delete_threads_data(thread_data *threads_data, DWORD *threads_id, HANDLE *threads);

#endif
