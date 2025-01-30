#include <stdio.h>

#include "kyznechik-ecb.h"
#include "kyznechik.h"
#include "stdint.h"
#include "time.h"

#include "utils.h"

int main() {
    init();
    uint8_t const key[] = {
                67, 75, 124, 44, 92, 224, 225, 118, 159, 17, 61, 45, 207, 201, 94, 9, 101, 254, 218, 15, 204, 136, 206,
                25, 232, 158, 188, 64, 154, 12, 120, 208
            };
    uint8_t **Ks = NULL;
    generate_keys(key, &Ks);
    uint64_t curr, total;

    int result = encrypt_kyznechik_ecb(
        L"../../../input.txt",
        L"C:\\",
        L"../../../output.txt",
        key,
        1,
        &curr,
        &total
    );

    printf("%d\n", result);

    //
    // clock_t start = clock();
    // int const iters = 10000000;
    // for (int i = 0; i < iters; ++i) {
    //     encrypt_data(Ks, text, text);
    // }
    // clock_t end = clock();
    // double seconds = (double)(end - start) / CLOCKS_PER_SEC;
    // printf("%lf\n", 16 * iters / seconds / 1024 / 1024);
    //
    // start = clock();
    // for (int i = 0; i < iters; ++i) {
    //     decrypt_data(Ks, text, text);
    // }
    // end = clock();
    // seconds = (double)(end - start) / CLOCKS_PER_SEC;
    // printf("%lf\n", 16 * iters / seconds / 1024 / 1024);

    finalize(Ks);
    return 0;
}
