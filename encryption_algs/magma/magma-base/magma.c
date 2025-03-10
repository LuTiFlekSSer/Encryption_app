#include "magma.h"

#include <stdint.h>
#include <stdio.h>
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

    for (int i = 0; i < 32; ++i) {
        memcpy((*Ks)[i], key + 4 * (7 - i % 8), 4);
    }

    return 0;
}

void S_map(uint8_t *vec) {
    for (int i = 0; i < 4; ++i) {
        vec[i] = PI_TABLE[2 * i + 1][vec[i] / 16] * 16 + PI_TABLE[2 * i][vec[i] % 16];
    }
}

void magma_finalize(uint8_t **Ks) {
    for (int i = 0; i < 32; ++i) {
        free(Ks[i]);
    }
    free(Ks);
}
