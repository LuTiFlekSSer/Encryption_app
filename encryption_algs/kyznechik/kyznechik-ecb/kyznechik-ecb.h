#ifndef KYZNECHIK_ECB_H
#define KYZNECHIK_ECB_H

#include <stdint.h>

uint8_t encrypt_kyznechik_ecb(
    const uint8_t *file_in_path,
    const uint8_t *disk_out_name,
    const uint8_t *file_out_path,
    const uint8_t *key,
    uint16_t num_threads,
    uint64_t *current_step,
    uint64_t *total_steps
);

#endif
