#include <stdio.h>

#include "kyznechik-ecb.h"
#include "stdint.h"

int main() {
    uint8_t const key[] = {
        67, 75, 124, 44, 92, 224, 225, 118, 159, 17, 61, 45, 207, 201, 94, 9, 101, 254, 218, 15, 204, 136, 206,
        25, 232, 158, 188, 64, 154, 12, 120, 208
    };
    uint64_t curr = 0, total = 0;

    int result = encrypt_kyznechik_ecb(
        L"../../../input.txt",
        L"C:\\",
        L"../../../middle.txt",
        key,
        4,
        &curr,
        &total
    );

    printf("%d\n", result);
    printf("%llu %llu\n", curr, total);

    result = decrypt_kyznechik_ecb(
        L"../../../middle.txt",
        L"C:\\",
        L"../../../output.txt",
        key,
        4,
        &curr,
        &total
    );

    printf("%d\n", result);
    printf("%llu %llu\n", curr, total);

    return 0;
}
