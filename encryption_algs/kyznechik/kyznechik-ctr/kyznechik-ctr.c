#include "kyznechik-ctr.h"

#include <stdio.h>
#include <iso646.h>

#include "kyznechik.h"
#include "utils.h"


uint8_t encrypt_kyznechik_ctr(
    const WCHAR *file_in_path,
    const WCHAR *disk_out_name,
    const WCHAR *file_out_path,
    const uint8_t *key,
    uint16_t const num_threads,
    uint64_t *current_step,
    uint64_t *total_steps
) {
    return 0;
}

uint8_t decrypt_kyznechik_ctr(
    const WCHAR *file_in_path,
    const WCHAR *disk_out_name,
    const WCHAR *file_out_path,
    const uint8_t *key,
    uint16_t const num_threads,
    uint64_t *current_step,
    uint64_t *total_steps
) {
    return 0;
}
