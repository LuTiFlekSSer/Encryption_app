#include "kyznechik-ecb.h"

#include <stdio.h>

#include "utils.h"

uint8_t encrypt_kyznechik_ecb(
    const uint8_t *file_in_path,
    const uint8_t *disk_out_name,
    const uint8_t *file_out_path,
    const uint8_t *key,
    uint16_t threads,
    uint64_t *current_step,
    uint64_t *total_steps
) {
    // todo проверка что флешку не вытащили при записи
    func_result const disk_space = get_disk_free_space(disk_out_name);
    if (disk_space.error) {
        return 1; // Не удалось получить информацию о диске
    }

    HANDLE input_file = CreateFile(
               (LPSTR)file_in_path,
               GENERIC_READ | GENERIC_WRITE,
               0,
               NULL,
               OPEN_EXISTING,
               FILE_FLAG_OVERLAPPED,
               NULL
           ), output_file;

    if (strcmp((const char*)file_in_path, (const char*)file_out_path) == 0) {
        output_file = input_file;
    } else {
        output_file = CreateFile(
            (LPSTR)file_out_path,
            GENERIC_READ | GENERIC_WRITE,
            0,
            NULL,
            TRUNCATE_EXISTING,
            FILE_FLAG_OVERLAPPED,
            NULL
        );
    }

    if (input_file == INVALID_HANDLE_VALUE || output_file == INVALID_HANDLE_VALUE) {
        close_files(input_file, output_file);
        return 2; // Не удалось открыть файл
    }

    func_result const file_size = get_file_size(input_file);
    if (file_size.error == 2) {
        close_files(input_file, output_file);
        return 3; // Не удалось получить размер файла
    }

    uint8_t const mod = file_size.result % 16,
                  delta[16] = {1},
                  after_file[2] = {KYZNECHIK, ECB};

    uint64_t const div = file_size.result / 16 + 1;

    if (input_file != output_file) {
        if (disk_space.result < file_size.result + 16 - mod + 2) {
            close_files(input_file, output_file);
            return 4; // Недостаточно места на диске
        }

        LARGE_INTEGER out_file_size;
        out_file_size.QuadPart = (int64_t)file_size.result;

        int result = SetFilePointerEx(output_file, out_file_size, NULL, FILE_BEGIN);
        if (!result) {
            close_files(input_file, output_file);
            return 6; // ошибка при увеличении выходного файла
        }

        result = SetEndOfFile(output_file);
        if (!result) {
            close_files(input_file, output_file);
            return 6; // ошибка при увеличении выходного файла
        }
    } else {
        if (disk_space.result - file_size.result < 16 - mod + 2) {
            close_files(input_file, output_file);
            return 4; // Недостаточно места на диске
        }
    }

    func_result f_result = write_metadata_to_file(
        output_file,
        file_size.result,
        delta,
        16 - mod,
        after_file
    );

    if (f_result.error || f_result.result != 16 - mod + 2) {
        close_files(input_file, output_file);
        return 5; // Не удалось записать метаданные
    }

    close_files(input_file, output_file);

    return 0;
}
