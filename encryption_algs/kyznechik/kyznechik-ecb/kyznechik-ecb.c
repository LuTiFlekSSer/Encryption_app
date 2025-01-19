#include "kyznechik-ecb.h"

#include <stdio.h>

#include "utils.h"

uint8_t encrypt_kyznechik_ecb(
    const uint8_t *file_path,
    const uint8_t *disk_name,
    const uint8_t *key,
    uint16_t threads
) {
    //todo проверка что флешку не вытащили при записи
    // todo аргумент для выходного файла
    func_result const disk_space = get_disk_free_spase(disk_name);
    if (disk_space.error) {
        return 1; // Не удалось получить информацию о диске
    }

    HANDLE file = CreateFile(
        (LPSTR)file_path,
        GENERIC_READ | GENERIC_WRITE,
        0,
        NULL,
        OPEN_EXISTING,
        FILE_FLAG_OVERLAPPED,
        NULL
    );

    if (file == INVALID_HANDLE_VALUE) {
        return 2; // Не удалось открыть файл
    }

    func_result const file_size = get_file_size(file);
    if (file_size.error == 2) {
        CloseHandle(file);
        return 3; // Не удалось получить размер файла
    }

    uint8_t const mod = file_size.result % 16,
                  delta[16] = {1},
                  after_file[2] = {KYZNECHIK, ECB};

    uint64_t const div = file_size.result / 16 + 1;

    if (disk_space.result - file_size.result < 16 - mod + 2) {
        CloseHandle(file);
        return 4; // Недостаточно места на диске
    }

    func_result f_result = write_metadata_to_file(
        file,
        file_size.result,
        delta,
        16 - mod,
        after_file
    );

    if (f_result.error || f_result.result != 16 - mod + 2) {
        CloseHandle(file);
        return 5; // Не удалось записать метаданные
    }

    CloseHandle(file);

    return 0;
}
