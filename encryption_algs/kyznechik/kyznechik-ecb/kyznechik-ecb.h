#ifndef KYZNECHIK_ECB_H
#define KYZNECHIK_ECB_H
#include <stdint.h>

uint8_t encrypt_kyznechik_ecb(
    const uint8_t *file_path,
    const uint8_t *disk_name,
    const uint8_t *key,
    uint16_t threads
);

#endif
