#include "magma.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

const uint8_t PI_TABLE[8][16] = {
    12, 4, 6, 2, 10, 5, 11, 9, 14, 8, 13, 7, 0, 3, 15, 1,
    6, 8, 2, 3, 9, 10, 5, 12, 1, 14, 4, 7, 1, 13, 0, 15,
    11, 3, 5, 8, 2, 15, 10, 13, 14, 1, 7, 4, 12, 9, 6, 0,
    12, 8, 2, 1, 13, 4, 15, 6, 7, 0, 10, 5, 3, 14, 9, 11,
    7, 15, 5, 10, 8, 1, 6, 13, 0, 9, 3, 14, 11, 4, 2, 12,
    5, 13, 15, 6, 9, 2, 12, 10, 11, 7, 8, 1, 4, 3, 14, 0,
    8, 14, 2, 5, 6, 9, 1, 12, 15, 4, 11, 0, 13, 10, 3, 7,
    1, 7, 14, 13, 0, 5, 8, 3, 4, 15, 10, 6, 9, 12, 11, 2
};
uint8_t S_TABLE[4][256], Z_TABLE[4][4] = {0};
uint32_t LUT_TABLE[4][256];
uint8_t SHIFT = 11, INITED = 0;

void magma_init() {
    if (INITED) {
        return;
    }
    INITED = 1;

    for (int i = 0; i < 4; ++i) {
        for (int j = 0; j < 256; ++j) {
            S_TABLE[i][j] = PI_TABLE[2 * i + 1][j / 16] * 16 + PI_TABLE[2 * i][j % 16];
        }
    }
    for (int i = 0; i < 4; ++i) {
        Z_TABLE[i][i] = 1;
        *((uint32_t*)Z_TABLE[i]) = (*((uint32_t*)Z_TABLE[i]) << SHIFT) | (*((uint32_t*)Z_TABLE[i]) >> (32 - SHIFT));
    }

    for (int i = 0; i < 4; ++i) {
        for (int j = 0; j < 256; ++j) {
            LUT_TABLE[i][j] =
                (uint32_t)(S_TABLE[i][j] * Z_TABLE[i][3]) << 24 |
                (uint32_t)(S_TABLE[i][j] * Z_TABLE[i][2]) << 16 |
                (uint32_t)(S_TABLE[i][j] * Z_TABLE[i][1]) << 8 |
                (uint32_t)(S_TABLE[i][j] * Z_TABLE[i][0]);
        }
    }
}

void LS_map(uint8_t *vec) {
    uint32_t ans = 0;

    for (int i = 0; i < 4; ++i) {
        ans ^= LUT_TABLE[i][vec[i]];
    }

    memcpy(vec, &ans, 4 * sizeof(uint8_t));
}

int magma_generate_keys(uint8_t const *key, uint8_t ***Ks) {
    *Ks = malloc(32 * sizeof(uint8_t*));
    if (*Ks == NULL) {
        return -1;
    }

    for (int i = 0; i < 32; ++i) {
        (*Ks)[i] = malloc(4 * sizeof(uint8_t));

        if ((*Ks)[i] == NULL) {
            for (int j = 0; j < i; ++j) {
                free((*Ks)[j]);
            }
            free(*Ks);

            return -1;
        }
    }

    for (int i = 0; i < 24; ++i) {
        memcpy((*Ks)[i], key + 4 * (7 - i % 8), 4 * sizeof(uint8_t));
    }

    for (int i = 24; i < 32; ++i) {
        memcpy((*Ks)[i], key + 4 * (i % 8), 4 * sizeof(uint8_t));
    }

    return 0;
}

void magma_encrypt_data(uint8_t const **Ks, uint8_t const *data_in, uint8_t *data_out) {
    uint32_t lower = *((uint32_t*)data_in), higher = *((uint32_t*)(data_in + 4));

    for (int i = 0; i < 32; ++i) {
        uint32_t const buf = lower;
        lower += *((uint32_t*)Ks[i]);

        LS_map((uint8_t*)&lower);

        lower ^= higher;
        higher = buf;
    }

    *((uint64_t*)data_out) = (uint64_t)lower << 32 | higher;
}

void magma_decrypt_data(uint8_t const **Ks, uint8_t const *data_in, uint8_t *data_out) {
    uint32_t lower = *((uint32_t*)data_in), higher = *((uint32_t*)(data_in + 4));

    for (int i = 0; i < 32; ++i) {
        uint32_t const buf = lower;
        lower += *((uint32_t*)Ks[31 - i]);

        LS_map((uint8_t*)&lower);

        lower ^= higher;
        higher = buf;
    }

    *((uint64_t*)data_out) = (uint64_t)lower << 32 | higher;
}

void magma_finalize(uint8_t **Ks) {
    for (int i = 0; i < 32; ++i) {
        free(Ks[i]);
    }
    free(Ks);
}
