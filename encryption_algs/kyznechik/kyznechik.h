#ifndef KYZNECHIK_H
#define KYZNECHIK_H

#include <stdint.h>

typedef union custom_uint8_t {
    uint8_t value;

    struct bit {
        unsigned b1 : 1;
        unsigned b2 : 1;
        unsigned b3 : 1;
        unsigned b4 : 1;
        unsigned b5 : 1;
        unsigned b6 : 1;
        unsigned b7 : 1;
        unsigned b8 : 1;
    } bit;
} custom_uint8_t;

extern const custom_uint8_t POLYNOM;
extern const uint8_t L_SERIES[16];
extern const uint8_t PI_TABLE[256];

int encrypt_data(uint8_t const *key, uint8_t const *data_in, uint8_t *data_out);

#endif
