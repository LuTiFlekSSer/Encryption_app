#ifndef MAGMA_H
#define MAGMA_H

#include <stdint.h>

void magma_init();
int magma_generate_keys(uint8_t const *key, uint8_t ***Ks);
void magma_encrypt_data(uint8_t const **Ks, uint8_t const *data_in, uint8_t *data_out);
void magma_decrypt_data(uint8_t const **Ks, uint8_t const *data_in, uint8_t *data_out);
void magma_finalize(uint8_t **Ks);

#endif
