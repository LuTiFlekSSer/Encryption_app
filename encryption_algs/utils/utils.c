#include "utils.h"

#include <windows.h>
#include <iso646.h>

func_result get_disk_free_space(const WCHAR *disk_name) {
    ULARGE_INTEGER free_bytes_available;

    int const result = GetDiskFreeSpaceExW(
        (LPWSTR)disk_name,
        &free_bytes_available,
        NULL,
        NULL
    );

    if (result) {
        return (func_result){free_bytes_available.QuadPart, 0};
    }

    return (func_result){0, 1};
}

func_result get_file_size(HANDLE file) {
    DWORD fileSizeHigh;
    DWORD const fileSizeLow = GetFileSize(file, &fileSizeHigh);

    if (fileSizeLow == INVALID_FILE_SIZE && GetLastError() != NO_ERROR) {
        return (func_result){0, 1};
    }

    return (func_result){((uint64_t)fileSizeHigh << 32) | fileSizeLow, 0};
}

func_result write_block_to_file(LPCVOID const block_info) {
    file_block_info const *block = (file_block_info*)block_info;

    OVERLAPPED overlapped = {0};
    overlapped.Offset = (DWORD)(block->offset & 0xFFFFFFFF);
    overlapped.OffsetHigh = (DWORD)((block->offset >> 32) & 0xFFFFFFFF);
    overlapped.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);

    DWORD written_bytes;

    int const result = WriteFile(block->file, block->data, block->data_size, NULL, &overlapped);

    if (result == 0) {
        if (GetLastError() != ERROR_IO_PENDING) {
            return (func_result){0, 1};
        }
    }

    WaitForSingleObject(overlapped.hEvent, INFINITE);
    GetOverlappedResult(block->file, &overlapped, &written_bytes, TRUE);
    CloseHandle(overlapped.hEvent);

    return (func_result){written_bytes, 0};
}

func_result read_block_from_file(LPCVOID const block_info) {
    file_block_info const *block = (file_block_info*)block_info;

    OVERLAPPED overlapped = {0};
    overlapped.Offset = (DWORD)(block->offset & 0xFFFFFFFF);
    overlapped.OffsetHigh = (DWORD)((block->offset >> 32) & 0xFFFFFFFF);
    overlapped.hEvent = CreateEvent(NULL, TRUE, FALSE, NULL);

    DWORD read_bytes;

    int const result = ReadFile(block->file, block->data, block->data_size, NULL, &overlapped);

    if (result == 0) {
        if (GetLastError() != ERROR_IO_PENDING) {
            return (func_result){0, 1};
        }
    }

    WaitForSingleObject(overlapped.hEvent, INFINITE);
    GetOverlappedResult(block->file, &overlapped, &read_bytes, TRUE);
    CloseHandle(overlapped.hEvent);

    return (func_result){read_bytes, 0};
}

func_result write_metadata_to_file(
    HANDLE file,
    uint64_t const offset,
    uint8_t const *metadata,
    uint8_t const metadata_size,
    uint8_t const *cipher_info
) {
    uint64_t all_written_bytes = 0;

    file_block_info block_info = {file, offset, (uint8_t*)metadata, metadata_size};
    func_result result = write_block_to_file(&block_info);

    if (result.error) {
        return result;
    }
    all_written_bytes += result.result;

    block_info.offset = offset + metadata_size;
    block_info.data = (uint8_t*)cipher_info;
    block_info.data_size = 2;

    result = write_block_to_file(&block_info);

    if (result.error) {
        return result;
    }

    return (func_result){all_written_bytes + result.result, 0};
}

uint8_t read_cipher_from_file(
    const WCHAR *file_name,
    uint8_t *cipher_type,
    uint8_t *cipher_mode
) {
    HANDLE file;
    open_files(file_name, file_name, &file, &file);

    if (file == INVALID_HANDLE_VALUE) {
        return 1; //Ошибка при работе с файлом
    }
    func_result const size = get_file_size(file);

    if (size.error) {
        return 1; //Ошибка при работе с файлом
    }

    if (size.result < 2) {
        return 2; //Файл не зашифрован
    }

    uint8_t cipher[2];
    file_block_info const block_info = {.file = file, .offset = size.result - 2, .data = cipher, .data_size = 2};
    func_result const result = read_block_from_file(&block_info);

    if (result.error) {
        return 1; //Ошибка при работе с файлом
    }

    if (cipher[0] >= CIPHER_TYPES or cipher[1] >= CIPHER_MODES) {
        return 2; //Файл не зашифрован
    }
    *cipher_type = cipher[0];
    *cipher_mode = cipher[1];

    return 0;
}


void open_files(const WCHAR *file_in_path, const WCHAR *file_out_path, HANDLE *input_file, HANDLE *output_file) {
    *input_file = CreateFileW(
        (LPWSTR)file_in_path,
        GENERIC_READ | GENERIC_WRITE,
        0,
        NULL,
        OPEN_EXISTING,
        FILE_FLAG_OVERLAPPED,
        NULL
    );

    if (lstrcmpW(file_in_path, file_out_path) == 0) {
        *output_file = *input_file;
    } else {
        *output_file = CreateFileW(
            (LPWSTR)file_out_path,
            GENERIC_READ | GENERIC_WRITE,
            0,
            NULL,
            TRUNCATE_EXISTING,
            FILE_FLAG_OVERLAPPED,
            NULL
        );
    }
}

void close_files(HANDLE file1, HANDLE file2) {
    if (file1 == file2) {
        if (file1 != INVALID_HANDLE_VALUE) {
            CloseHandle(file1);
        }
    }

    if (file1 != INVALID_HANDLE_VALUE) {
        CloseHandle(file1);
    }

    if (file2 != INVALID_HANDLE_VALUE) {
        CloseHandle(file2);
    }
}

uint8_t check_files(
    HANDLE input_file,
    HANDLE output_file,
    const uint64_t free_disk_space,
    const uint64_t file_size,
    const uint64_t metadata_size
) {
    if (input_file != output_file) {
        if (free_disk_space < file_size + metadata_size) {
            close_files(input_file, output_file);
            return 1; // Недостаточно места на диске
        }

        LARGE_INTEGER out_file_size;
        out_file_size.QuadPart = (int64_t)file_size;

        int result = SetFilePointerEx(output_file, out_file_size, NULL, FILE_BEGIN);
        if (!result) {
            close_files(input_file, output_file);
            return 2; // ошибка при увеличении выходного файла
        }

        result = SetEndOfFile(output_file);
        if (!result) {
            close_files(input_file, output_file);
            return 2; // ошибка при увеличении выходного файла
        }
    } else {
        if (free_disk_space < metadata_size + file_size) {
            close_files(input_file, output_file);
            return 1; // Недостаточно места на диске
        }
    }

    return 0;
}

uint8_t create_threads_data(uint16_t const num_threads, thread_data **threads_data, DWORD **threads_id,
                            HANDLE **threads) {
    *threads_data = calloc(num_threads, sizeof(thread_data));
    *threads_id = calloc(num_threads, sizeof(DWORD));
    *threads = calloc(num_threads, sizeof(HANDLE));

    if (*threads_data == NULL or *threads_id == NULL or *threads == NULL) {
        if (*threads_data != NULL) {
            free(*threads_data);
        }

        if (*threads_id != NULL) {
            free(*threads_id);
        }

        if (*threads != NULL) {
            free(*threads);
        }

        return 1;
    }

    return 0;
}

void delete_threads_data(thread_data *threads_data, DWORD *threads_id, HANDLE *threads) {
    free(threads_data);
    free(threads);
    free(threads_id);
}
