#include "utils.h"

#include <windows.h>

func_result get_disk_free_space(const uint8_t *disk_name) {
    ULARGE_INTEGER free_bytes_available;

    int const result = GetDiskFreeSpaceEx(
        (LPSTR)disk_name,
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

    DWORD written_bytes;

    int const result = WriteFile(block->file, block->data, block->data_size, NULL, &overlapped);

    if (result == 0) {
        if (GetLastError() != ERROR_IO_PENDING) {
            return (func_result){0, 1};
        }
    }

    WaitForSingleObject(overlapped.hEvent, INFINITE);
    GetOverlappedResult(block->file, &overlapped, &written_bytes, TRUE);

    return (func_result){written_bytes, 0};
}

func_result read_block_from_file(LPCVOID const block_info) {
    file_block_info const *block = (file_block_info*)block_info;

    OVERLAPPED overlapped = {0};
    overlapped.Offset = (DWORD)(block->offset & 0xFFFFFFFF);
    overlapped.OffsetHigh = (DWORD)((block->offset >> 32) & 0xFFFFFFFF);

    DWORD read_bytes;

    int const result = ReadFile(block->file, block->data, block->data_size, NULL, &overlapped);

    if (result == 0) {
        if (GetLastError() != ERROR_IO_PENDING) {
            return (func_result){0, 1};
        }
    }

    WaitForSingleObject(overlapped.hEvent, INFINITE);
    GetOverlappedResult(block->file, &overlapped, &read_bytes, TRUE);

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
