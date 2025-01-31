#include "kyznechik.h"

#include <stdint.h>
#include <stdio.h>
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
              }, PI_TABLE_INVERSE[256] = {
                  165, 45, 50, 143, 14, 48, 56, 192, 84, 230, 158, 57, 85, 126, 82, 145,
                  100, 3, 87, 90, 28, 96, 7, 24, 33, 114, 168, 209, 41, 198, 164, 63,
                  224, 39, 141, 12, 130, 234, 174, 180, 154, 99, 73, 229, 66, 228, 21, 183,
                  200, 6, 112, 157, 65, 117, 25, 201, 170, 252, 77, 191, 42, 115, 132, 213,
                  195, 175, 43, 134, 167, 177, 178, 91, 70, 211, 159, 253, 212, 15, 156, 47,
                  155, 67, 239, 217, 121, 182, 83, 127, 193, 240, 35, 231, 37, 94, 181, 30,
                  162, 223, 166, 254, 172, 34, 249, 226, 74, 188, 53, 202, 238, 120, 5, 107,
                  81, 225, 89, 163, 242, 113, 86, 17, 106, 137, 148, 101, 140, 187, 119, 60,
                  123, 40, 171, 210, 49, 222, 196, 95, 204, 207, 118, 44, 184, 216, 46, 54,
                  219, 105, 179, 20, 149, 190, 98, 161, 59, 22, 102, 233, 92, 108, 109, 173,
                  55, 97, 75, 185, 227, 186, 241, 160, 133, 131, 218, 71, 197, 176, 51, 250,
                  150, 111, 110, 194, 246, 80, 255, 93, 169, 142, 23, 27, 151, 125, 236, 88,
                  247, 31, 251, 124, 9, 13, 122, 103, 69, 135, 220, 232, 79, 29, 78, 4,
                  235, 248, 243, 62, 61, 189, 138, 136, 221, 205, 11, 19, 152, 2, 147, 128,
                  144, 208, 36, 52, 203, 237, 244, 206, 153, 16, 68, 64, 146, 58, 1, 38,
                  18, 26, 72, 104, 245, 129, 139, 199, 214, 32, 10, 8, 0, 76, 215, 116
              };
uint8_t MASK = (uint8_t)1 << 7;
uint8_t MULT_TABLE[256][256],
        Z_TABLE[16][16] = {0}, Z_TABLE_INVERSE[16][16] = {0};
__uint128_t LUT_TABLE[16][256],
            LUT_TABLE_INVERSE[16][256];
uint8_t const BLOCK_SIZE = 16 * sizeof(uint8_t);

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

void sqr_mat(uint8_t mat[16][16]) {
    uint8_t temp[16][16];

    memcpy(temp, mat, 16 * BLOCK_SIZE);

    for (int i = 0; i < 16; i++) {
        for (int j = 0; j < 16; j++) {
            mat[i][j] = 0;
            for (int k = 0; k < 16; k++) {
                mat[i][j] ^= mult(temp[i][k], temp[k][j]);
            }
        }
    }
}

void generate_lut_table() {
    for (int i = 1; i < 256; ++i) {
        if ((mult((uint8_t)148, (uint8_t)i) ^ 1) == 1) {
            printf("%d\n", i);
        }
    }
    for (int i = 0; i < 16; ++i) {
        for (int j = 0; j < 256; ++j) {
            LUT_TABLE[i][j] =
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][15]] << 120 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][14]] << 112 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][13]] << 104 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][12]] << 96 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][11]] << 88 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][10]] << 80 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][9]] << 72 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][8]] << 64 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][7]] << 56 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][6]] << 48 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][5]] << 40 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][4]] << 32 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][3]] << 24 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][2]] << 16 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][1]] << 8 |
                (__uint128_t)MULT_TABLE[PI_TABLE[j]][Z_TABLE[i][0]];

            LUT_TABLE_INVERSE[i][j] =
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][15]] << 120 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][14]] << 112 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][13]] << 104 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][12]] << 96 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][11]] << 88 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][10]] << 80 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][9]] << 72 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][8]] << 64 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][7]] << 56 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][6]] << 48 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][5]] << 40 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][4]] << 32 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][3]] << 24 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][2]] << 16 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][1]] << 8 |
                (__uint128_t)MULT_TABLE[PI_TABLE_INVERSE[j]][Z_TABLE_INVERSE[i][0]];
        }
    }
}

void kyznechik_init() {
    for (int i = 0; i < 256; ++i) {
        for (int j = 0; j < 256; ++j) {
            MULT_TABLE[i][j] = mult((uint8_t)i, (uint8_t)j);
        }
    }

    for (int i = 0; i < 15; ++i) {
        Z_TABLE[i][i + 1] = 1;
        Z_TABLE_INVERSE[i + 1][i] = 1;
    }

    for (int i = 0; i < 16; ++i) {
        Z_TABLE[i][0] = L_SERIES[i];
        Z_TABLE_INVERSE[i][15] = L_SERIES[15 - i];
    }

    sqr_mat(Z_TABLE);
    sqr_mat(Z_TABLE);
    sqr_mat(Z_TABLE);
    sqr_mat(Z_TABLE);

    sqr_mat(Z_TABLE_INVERSE);
    sqr_mat(Z_TABLE_INVERSE);
    sqr_mat(Z_TABLE_INVERSE);
    sqr_mat(Z_TABLE_INVERSE);

    generate_lut_table();
}

void X_map(uint64_t const *a, uint64_t *b) {
    b[0] ^= a[0];
    b[1] ^= a[1];
}

void S_map(uint8_t *vec) {
    for (int i = 0; i < 16; ++i) {
        vec[i] = PI_TABLE[vec[i]];
    }
}

void S_map_inverse(uint8_t *vec) {
    for (int i = 0; i < 16; ++i) {
        vec[i] = PI_TABLE_INVERSE[vec[i]];
    }
}


void L_map(uint8_t *vec) {
    uint8_t buf[16], ans[16] = {0};

    for (int i = 0; i < 16; ++i) {
        for (int j = 0; j < 16; ++j) {
            buf[j] = MULT_TABLE[vec[i]][Z_TABLE[i][j]];
        }
        X_map((uint64_t*)buf, (uint64_t*)ans);
    }

    memcpy(vec, ans, BLOCK_SIZE);
}

void L_map_inverse(uint8_t *vec) {
    uint8_t buf[16], ans[16] = {0};

    for (int i = 0; i < 16; ++i) {
        for (int j = 0; j < 16; ++j) {
            buf[j] = MULT_TABLE[vec[i]][Z_TABLE_INVERSE[i][j]];
        }
        X_map((uint64_t*)buf, (uint64_t*)ans);
    }

    memcpy(vec, ans, BLOCK_SIZE);
}

void LS_map(uint8_t *vec) {
    __uint128_t ans = 0;

    for (int i = 0; i < 16; ++i) {
        X_map((uint64_t*)&LUT_TABLE[i][vec[i]], (uint64_t*)&ans);
    }

    memcpy(vec, &ans, BLOCK_SIZE);
}

void LS_map_inverse(uint8_t *vec) {
    __uint128_t ans = 0;

    for (int i = 0; i < 16; ++i) {
        X_map((uint64_t*)&LUT_TABLE_INVERSE[i][vec[i]], (uint64_t*)&ans);
    }

    memcpy(vec, &ans, BLOCK_SIZE);
}

int kyznechik_generate_keys(uint8_t const *key, uint8_t ***Ks) {
    *Ks = malloc(19 * sizeof(uint8_t*));
    if (*Ks == NULL) {
        return -1;
    }

    for (int i = 0; i < 19; ++i) {
        (*Ks)[i] = malloc(BLOCK_SIZE);

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

    memcpy(K_left, key, BLOCK_SIZE);
    memcpy(K_right, key + BLOCK_SIZE, BLOCK_SIZE);

    for (int i = 0; i < 32; ++i) {
        uint8_t K_buf[16];

        if (i % 8 == 0) {
            memcpy((*Ks)[i / 4], K_left, BLOCK_SIZE);
            memcpy((*Ks)[i / 4 + 1], K_right, BLOCK_SIZE);
        }

        memcpy(K_buf, K_right, BLOCK_SIZE);

        X_map((uint64_t*)K_left, (uint64_t*)Cs[i]);
        LS_map(Cs[i]);
        X_map((uint64_t*)K_right, (uint64_t*)Cs[i]);

        memcpy(K_right, K_left, BLOCK_SIZE);
        memcpy(K_left, Cs[i], BLOCK_SIZE);
    }

    memcpy((*Ks)[8], K_left, BLOCK_SIZE);
    memcpy((*Ks)[9], K_right, BLOCK_SIZE);

    for (int i = 10; i < 19; ++i) {
        memcpy((*Ks)[i], (*Ks)[19 - i], BLOCK_SIZE);
    }

    for (int i = 10; i < 19; ++i) {
        L_map_inverse((*Ks)[i]);
    }

    return 0;
}

void kyznechik_encrypt_data(uint8_t const **Ks, uint8_t const *data_in, uint8_t *data_out) {
    memcpy(data_out, data_in, BLOCK_SIZE);

    for (int i = 0; i < 9; ++i) {
        X_map((uint64_t*)Ks[i], (uint64_t*)data_out);
        LS_map(data_out);
    }
    X_map((uint64_t*)Ks[9], (uint64_t*)data_out);
}

void kyznechik_decrypt_data(uint8_t const **Ks, uint8_t const *data_in, uint8_t *data_out) {
    memcpy(data_out, data_in, BLOCK_SIZE);

    S_map(data_out);
    for (int i = 10; i < 19; ++i) {
        LS_map_inverse(data_out);
        X_map((uint64_t*)Ks[i], (uint64_t*)data_out);
    }
    S_map_inverse(data_out);
    X_map((uint64_t*)Ks[0], (uint64_t*)data_out);
}

void kyznechik_finalize(uint8_t **Ks) {
    for (int i = 0; i < 19; ++i) {
        free(Ks[i]);
    }
    free(Ks);
}
