#ifndef MAGMA_CTR_H
#define MAGMA_CTR_H

#include <stdint.h>
#include <windows.h>

uint8_t encrypt_magma_ctr(
    const WCHAR *file_in_path,
    const WCHAR *disk_out_name,
    const WCHAR *file_out_path,
    const uint8_t *key,
    uint16_t num_threads,
    uint64_t *current_step,
    uint64_t *total_steps
);

uint8_t decrypt_magma_ctr(
    const WCHAR *file_in_path,
    const WCHAR *disk_out_name,
    const WCHAR *file_out_path,
    const uint8_t *key,
    uint16_t num_threads,
    uint64_t *current_step,
    uint64_t *total_steps
);

#endif
