#include "kyznechik.h"

#include <stdint.h>
#include <stdlib.h>
#include <string.h>

const custom_uint8_t POLYNOM = {.bit = 1, 1, 0, 0, 0, 0, 1, 1};
const uint8_t L_SERIES[16] = {148, 32, 133, 16, 194, 192, 1, 251, 1, 192, 194, 16, 133, 32, 148, 1};
const uint8_t PI_TABLE[256] = {
    252, 238, 221, 17, 207, 110, 49, 22, 251, 196, 250, 218, 35, 197, 4, 77,
    233, 119, 240, 219, 147, 46, 153, 186, 23, 54, 241, 187, 20, 205, 95, 193,
    249, 24, 101, 90, 226, 92, 239, 33, 129, 28, 60, 66, 139, 1, 142, 79,
    5, 132, 2, 174, 227, 106, 143, 160, 6, 11, 237, 152, 127, 212, 211, 31,
    235, 52, 44, 81, 234, 200, 72, 171, 242, 42, 104, 162, 253, 58, 206, 204,
    181, 112, 14, 86, 8, 12, 118, 18, 191, 114, 19, 71, 156, 183, 93, 135,
    21, 161, 150, 41, 16, 123, 154, 199, 243, 145, 120, 111, 157, 158, 178, 177,
    50, 117, 25, 61, 255, 53, 138, 126, 109, 84, 198, 128, 195, 189, 13, 87,
    223, 245, 36, 169, 62, 168, 67, 201, 215, 121, 214, 246, 124, 34, 185, 3,
    224, 15, 236, 222, 122, 148, 176, 188, 220, 232, 40, 80, 78, 51, 10, 74,
    167, 151, 96, 115, 30, 0, 98, 68, 26, 184, 56, 130, 100, 159, 38, 65,
    173, 69, 70, 146, 39, 94, 85, 47, 140, 163, 165, 125, 105, 213, 149, 59,
    7, 88, 179, 64, 134, 172, 29, 247, 48, 55, 107, 228, 136, 217, 231, 137,
    225, 27, 131, 73, 76, 63, 248, 254, 141, 83, 170, 144, 202, 216, 133, 97,
    32, 113, 103, 164, 45, 43, 9, 91, 203, 155, 37, 208, 190, 229, 108, 82,
    89, 166, 116, 210, 230, 244, 180, 192, 209, 102, 175, 194, 57, 75, 99, 182
};
uint8_t MASK = (uint8_t)1 << 7;
uint8_t MULT_TABLE[256][256],
        Z_TABLE[16][16] = {0};

uint8_t mult(uint8_t a, uint8_t b) {
    uint8_t prod = 0;

    for (int i = 0; i < 8; ++i) {
        if (b & 1) {
            prod ^= a;
        }

        uint8_t const hi_bit_set = a & MASK;

        a <<= 1;
        if (hi_bit_set) {
            a ^= POLYNOM.value;
        }

        b >>= 1;
    }

    return prod;
}


void init() {
    for (int i = 0; i < 256; ++i) {
        for (int j = 0; j < 256; ++j) {
            MULT_TABLE[i][j] = mult(i, j);
        }
    }

    for (int i = 0; i < 15; ++i) {
        Z_TABLE[i][i + 1] = 1;
    }

    for (int i = 0; i < 16; ++i) {
        Z_TABLE[i][0] = L_SERIES[i];
    }
    //todo возвезсти в 16 степень
}

void L_map(uint8_t *vec) {
    for (int i = 0; i < 16; ++i) {
        uint8_t last_byte = mult(vec[15], L_SERIES[15]);

        for (int j = 14; j >= 0; --j) {
            vec[j + 1] = vec[j];
            last_byte ^= mult(vec[j], L_SERIES[j]);
        }

        vec[0] = last_byte;
    }
}

void S_map(uint8_t *vec) {
    for (int i = 0; i < 16; ++i) {
        vec[i] = PI_TABLE[vec[i]];
    }
}

void X_map(uint64_t const *a, uint64_t *b) {
    b[0] ^= a[0];
    b[1] ^= a[1];
}

void LS_map(const uint8_t *vec, uint8_t *vec_out) {
    uint8_t buf[16];

    for (int i = 0; i < 16; ++i) {
        vec_out[i] = MULT_TABLE[PI_TABLE[vec[0]]][Z_TABLE[0][15 - i]];
    }

    for (int i = 1; i < 16; ++i) {
        for (int j = 0; j < 16; ++j) {
            buf[j] = MULT_TABLE[PI_TABLE[vec[i]]][Z_TABLE[i][15 - j]];
        }
        X_map((uint64_t*)buf, (uint64_t*)vec_out);
    }
}


int generate_keys(uint8_t const *key, uint8_t ***Ks) {
    *Ks = malloc(10 * sizeof(uint8_t*));
    if (*Ks == NULL) {
        return -1;
    }

    uint8_t const size = 16 * sizeof(uint8_t);

    for (int i = 0; i < 10; ++i) {
        (*Ks)[i] = malloc(size);

        if ((*Ks)[i] == NULL) {
            for (int j = 0; j < i; ++j) {
                free((*Ks)[j]);
            }
            free(*Ks);

            return -1;
        }
    }

    uint8_t Cs[32][16] = {0};

    for (int i = 0; i < 32; ++i) {
        Cs[i][15] = i + 1;
        L_map(Cs[i]);
    }

    uint8_t K_left[16], K_right[16];

    memcpy(K_left, key, size);
    memcpy(K_right, key + size, size);

    for (int i = 0; i < 32; ++i) {
        uint8_t K_buf[16];

        if (i % 8 == 0) {
            memcpy((*Ks)[i / 4], K_left, size);
            memcpy((*Ks)[i / 4 + 1], K_right, size);
        }

        memcpy(K_buf, K_right, size);

        X_map((uint64_t*)K_left, (uint64_t*)Cs[i]);
        S_map(Cs[i]);
        L_map(Cs[i]);
        X_map((uint64_t*)K_right, (uint64_t*)Cs[i]);

        memcpy(K_right, K_left, size);
        memcpy(K_left, Cs[i], size);
    }

    memcpy((*Ks)[8], K_left, size);
    memcpy((*Ks)[9], K_right, size);

    return 0;
}


void encrypt_data(uint8_t const **Ks, uint8_t const *data_in, uint8_t *data_out) {
    uint8_t const size = 16 * sizeof(uint8_t);

    memcpy(data_out, data_in, size);

    for (int i = 0; i < 9; ++i) {
        X_map((uint64_t*)Ks[i], (uint64_t*)data_out);
        S_map(data_out);
        L_map(data_out);
    }
    X_map((uint64_t*)Ks[9], (uint64_t*)data_out);
}

void finalize(uint8_t ***Ks) {
    for (int i = 0; i < 10; ++i) {
        free((*Ks)[i]);
    }
    free(*Ks);
}
