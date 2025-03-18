#include <stdio.h>
#include <stdlib.h>
#include "time.h"
#include "magma.h"
#include "magma-cbc.h"
#include "stdint.h"

int main() {
    uint8_t const key[] = {
                      67, 75, 124, 44, 92, 224, 225, 118, 159, 17, 61, 45, 207, 201, 94, 9, 101, 254, 218, 15, 204, 136,
                      206, 25, 232, 158, 188, 64, 154, 12, 120, 208
                  },
                  magma_key[] = {
                      255, 254, 253, 252, 251, 250, 249, 248, 247, 246, 245, 244, 243, 242, 241, 240, 0, 17, 34, 51, 68,
                      85, 102, 119, 136, 153, 170, 187, 204, 221, 238, 255
                  };


    magma_init();
    uint8_t **Ks;
    magma_generate_keys(magma_key, &Ks);
    // uint8_t text[8] = {'C', 'L', 'A', 'N', ' ', 'Z', 'O', 'V'};

    // clock_t start = clock();
    // int const iters = 10000000;
    // for (int i = 0; i < iters; ++i) {
    //     magma_encrypt_data((const uint8_t**)Ks, text, text);
    // }
    // clock_t end = clock();
    // double seconds = (double)(end - start) / CLOCKS_PER_SEC;
    //
    // printf("ENC %lf MB/s\n", 8 * iters / seconds / 1024 / 1024);
    //
    // start = clock();
    // for (int i = 0; i < iters; ++i) {
    //     magma_decrypt_data((const uint8_t**)Ks, text, text);
    // }
    // end = clock();
    // seconds = (double)(end - start) / CLOCKS_PER_SEC;
    //
    // printf("DEC %lf MB/s", 8 * iters / seconds / 1024 / 1024);

    uint64_t curr = 0, total = 0;

    int result = encrypt_magma_cbc(
        L"../../../input.txt",
        L"C:\\",
        L"../../../middle.txt",
        magma_key,
        1,
        &curr,
        &total
    );

    printf("%d\n", result);
    printf("%llu %llu\n", curr, total);

    result = decrypt_magma_cbc(
        L"../../../middle.txt",
        L"C:\\",
        L"../../../output.txt",
        magma_key,
        1,
        &curr,
        &total
    );

    printf("%d\n", result);
    printf("%llu %llu\n", curr, total);
    magma_finalize(Ks);
    return 0;
}
