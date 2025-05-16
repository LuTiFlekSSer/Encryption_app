#include <stdio.h>
#include <stdlib.h>

#include "kyznechik-cbc.h"
#include "kyznechik-ctr.h"
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
                      251, 157, 155, 99, 20, 27, 45, 16, 33, 120, 134, 41, 229, 193, 10, 19, 175, 80, 210, 115, 223, 31,
                      56, 111, 187, 8, 18, 118, 137, 124, 120, 54
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
    int result = 0;
    // result = encrypt_magma_cbc(
    //     L"../../../input.txt",
    //     L"C:\\",
    //     L"../../../input.txt",
    //     magma_key,
    //     1,
    //     &curr,
    //     &total
    // );

    printf("%d\n", result);
    printf("%llu %llu\n", curr, total);

    result = decrypt_kyznechik_ctr(
        L"E:/test",
        L"E:\\",
        L"E:/test",
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
