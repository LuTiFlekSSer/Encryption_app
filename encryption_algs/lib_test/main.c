#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <stdint.h>

#include "kyznechik.h"
#include "kyznechik-ecb.h"
#include "kyznechik-cbc.h"
#include "kyznechik-ctr.h"

#include "magma.h"
#include "magma-ecb.h"
#include "magma-cbc.h"
#include "magma-ctr.h"

int main() {
    uint8_t const kyznechik_key[] = {
                      67, 75, 124, 44, 92, 224, 225, 118, 159, 17, 61, 45, 207, 201, 94, 9, 101, 254, 218, 15, 204, 136,
                      206, 25, 232, 158, 188, 64, 154, 12, 120, 208
                  },
                  magma_key[] = {
                      251, 157, 155, 99, 20, 27, 45, 16, 33, 120, 134, 41, 229, 193, 10, 19, 175, 80, 210, 115, 223, 31,
                      56, 111, 187, 8, 18, 118, 137, 124, 120, 54
                  };


    uint64_t curr = 0, total = 0;
    int result = 0;

    result = encrypt_kyznechik_cbc(
        L"C:\\Users\\boris\\Downloads\\input.txt",
        L"C:\\",
        L"C:\\Users\\boris\\Downloads\\input.txt",
        kyznechik_key,
        6,
        &curr,
        &total
    );

    printf("%d\n", result);
    printf("%llu %llu\n", curr, total);

    // result = decrypt_kyznechik_cbc(
    //     L"C:\\Users\\boris\\Downloads\\input.txt",
    //     L"C:\\",
    //     L"C:\\Users\\boris\\Downloads\\input.txt",
    //     kyznechik_key,
    //     6,
    //     &curr,
    //     &total
    // );

    printf("%d\n", result);
    printf("%llu %llu\n", curr, total);

    return 0;
}
