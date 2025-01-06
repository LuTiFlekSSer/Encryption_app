#include "stdio.h"
#include "kyznechik.h"
#include "stdint.h"

int main() {
    uint8_t key[] = {
                67, 75, 124, 44, 92, 224, 225, 118, 159, 17, 61, 45, 207, 201, 94, 9, 101, 254, 218, 15, 204, 136, 206,
                25, 232, 158, 188, 64, 154, 12, 120, 208
            },
            text[] = {
                80, 69, 78, 68, 79, 68, 83, 73, 32, 83, 79, 83, 65, 84, 33, 33
            };

    encrypt_data(key, text, text);

    for (int i = 0; i < 16; ++i) {
        printf("%02X", text[i]);
    }
    return 0;
}
