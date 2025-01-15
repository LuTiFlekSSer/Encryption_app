#include "stdio.h"
#include "kyznechik.h"
#include "stdint.h"
#include "time.h"

int main() {
    init();
    uint8_t key[] = {
                67, 75, 124, 44, 92, 224, 225, 118, 159, 17, 61, 45, 207, 201, 94, 9, 101, 254, 218, 15, 204, 136, 206,
                25, 232, 158, 188, 64, 154, 12, 120, 208
            },
            text[] = {
                80, 69, 78, 68, 79, 68, 83, 73, 32, 83, 79, 83, 65, 84, 33, 33
            };
//8F34299CE551D1A744F9AD4BA0F3FCD6
    uint8_t **Ks = NULL;
    generate_keys(key, &Ks);
    encrypt_data((uint8_t const **)Ks, text, text);

    for (int i = 0; i < 16; ++i) {
        printf("%02X", text[i]);
    }
    printf("\n");

    // clock_t start = clock();
    // int const iters = 100000;
    // for (int i = 0; i < iters; ++i) {
    //     encrypt_data((uint8_t const **)Ks, text, text);
    // }
    // clock_t end = clock();
    // double seconds = (double)(end - start) / CLOCKS_PER_SEC;
    // printf("%lf\n", seconds);

    finalize(&Ks);
    return 0;
}
