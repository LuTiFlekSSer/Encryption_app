#include "kyznechik-cbc.h"

#include <stdio.h>
#include <iso646.h>
#include <time.h>
#include <intrin.h>

#include "kyznechik.h"
#include "utils.h"

uint32_t const M = 16; // размер регистра сдвига можно менять кратно 16

char* get_cipher_name() {
    return "kyznechik";
}

char* get_mode_name() {
    return "cbc";
}

uint8_t encrypt_block(
    uint8_t const **Ks,
    file_block_info const *input_file_info,
    file_block_info const *output_file_info,
    uint8_t *r,
    uint32_t const m,
    HANDLE event
) {
    func_result result = read_block_from_file(input_file_info, event);
    if (result.error != 0) {
        return 1;
    }

    __uint128_t register_output, file_output;
    for (uint32_t j = 0; j < input_file_info->data_size; j += 16) {
        memcpy(&register_output, r + m - 16, 16);
        memcpy(&file_output, input_file_info->data + j, 16);

        register_output ^= file_output;
        kyznechik_encrypt_data(Ks, (uint8_t*)&register_output, (uint8_t*)&file_output);
        memcpy(output_file_info->data + j, &file_output, 16);

        for (uint32_t i = m - 1; i >= 16; --i) {
            r[i] = r[i - 16];
        }
        memcpy(r, &file_output, 16);
    }

    result = write_block_to_file(output_file_info, event);
    if (result.error != 0) { // todo сохранять часть
        return 1;
    }

    return 0;
}

uint8_t decrypt_block(
    uint8_t const **Ks,
    file_block_info const *input_file_info,
    file_block_info const *output_file_info,
    uint8_t *r,
    uint32_t const m,
    HANDLE event
) {
    func_result result = read_block_from_file(input_file_info, event);
    if (result.error != 0) {
        return 1;
    }

    __uint128_t register_output, file_output, tmp;
    for (uint32_t j = 0; j < input_file_info->data_size; j += 16) {
        memcpy(&tmp, input_file_info->data + j, 16);
        memcpy(&register_output, r + m - 16, 16);
        kyznechik_decrypt_data(Ks, input_file_info->data + j, (uint8_t*)&file_output);

        file_output ^= register_output;
        memcpy(output_file_info->data + j, &file_output, 16);

        for (uint32_t i = m - 1; i >= 16; --i) {
            r[i] = r[i - 16];
        }
        memcpy(r, &tmp, 16);
    }

    result = write_block_to_file(output_file_info, event);
    if (result.error != 0) { // todo сохранять часть
        return 1;
    }

    return 0;
}

uint8_t kyznechik_cbc_work(
    HANDLE input_file,
    HANDLE output_file,
    uint64_t const total_steps,
    uint64_t *current_step,
    uint8_t **Ks,
    CIPHER_FUNC_TYPE const func_type,
    uint8_t *r,
    uint32_t const m
) {
    uint8_t *buf = malloc(BUF_SIZE * sizeof(uint8_t));

    uint8_t (*cipher_func)(uint8_t const **,
                           file_block_info const *,
                           file_block_info const *,
                           uint8_t *,
                           uint32_t const,
                           HANDLE);
    if (func_type == ENCRYPT) {
        cipher_func = encrypt_block;
    } else {
        cipher_func = decrypt_block;
    }

    if (buf == NULL) {
        return 2; // Ошибка при выделении памяти
    }

    HANDLE event = CreateEvent(NULL, TRUE, FALSE, NULL);
    if (event == NULL) {
        free(buf);
        return 2; // Ошибка при выделении памяти
    }

    uint64_t const total = total_steps * 16 / BUF_SIZE,
                   mod = total_steps * 16 % BUF_SIZE;

    file_block_info input_file_info = (file_block_info){.file = input_file, .data_size = BUF_SIZE, .data = buf},
                    output_file_info = (file_block_info){.file = output_file, .data_size = BUF_SIZE, .data = buf};

    for (uint64_t i = 0; i < total; ++i) {
        input_file_info.offset = output_file_info.offset = BUF_SIZE * i;

        if (cipher_func((const uint8_t**)Ks,
                        &input_file_info,
                        &output_file_info,
                        r,
                        m,
                        event) != 0) {
            free(buf);
            CloseHandle(event);
            return 1; // Ошибка при обработке файла
        }

        *current_step += BUF_SIZE / 16;
    }

    if (mod != 0) {
        input_file_info.offset = output_file_info.offset = total * BUF_SIZE;
        input_file_info.data_size = output_file_info.data_size = mod;

        if (cipher_func((const uint8_t**)Ks,
                        &input_file_info,
                        &output_file_info,
                        r,
                        m,
                        event) != 0) {
            free(buf);
            CloseHandle(event);
            return 1; // Ошибка при обработке файла
        }

        *current_step += mod / 16;
    }
    free(buf);
    CloseHandle(event);
    return 0;
}

uint8_t encrypt_last_bytes(const uint8_t **Ks, uint8_t const *r, uint32_t const m, file_block_info const *block_info) {
    __uint128_t register_output, file_output;
    memcpy(&register_output, r + m - 16, 16);
    memcpy(&file_output, block_info->data, 16);

    register_output ^= file_output;
    kyznechik_encrypt_data(Ks, (uint8_t*)&register_output, block_info->data);

    func_result const f_result = write_block_to_file(block_info, NULL);
    if (f_result.error != 0) {
        return 1; // Ошибка при записи в файл
    }

    return 0;
}

uint8_t encrypt_check(const uint8_t **Ks, file_block_info const *block_info) {
    func_result const result = read_block_from_file(block_info, NULL);
    if (result.error != 0) {
        return 1; // Ошибка при чтении файла
    }

    kyznechik_encrypt_data(Ks, block_info->data, block_info->data);

    func_result const f_result = write_block_to_file(block_info, NULL);
    if (f_result.error != 0) {
        return 1; // Ошибка при записи в файл
    }

    return 0;
}

uint8_t encrypt_kyznechik_cbc(
    const WCHAR *file_in_path,
    const WCHAR *disk_out_name,
    const WCHAR *file_out_path,
    const uint8_t *key,
    uint16_t const num_threads,
    uint64_t *current_step,
    uint64_t *total_steps
) {
    *current_step = 0;
    func_result const disk_space = get_disk_free_space(disk_out_name);
    if (disk_space.error) {
        return 1; // Не удалось получить информацию о диске
    }

    HANDLE input_file, output_file;
    open_files(file_in_path, file_out_path, &input_file, &output_file);

    if (input_file == INVALID_HANDLE_VALUE || output_file == INVALID_HANDLE_VALUE) {
        close_files(input_file, output_file);
        return 2; // Не удалось открыть файл
    }

    func_result const file_size = get_file_size(input_file);
    if (file_size.error == 2) {
        close_files(input_file, output_file);
        return 3; // Не удалось получить размер файла
    }

    uint8_t const mod = file_size.result % 16, after_file[2] = {KYZNECHIK, CBC};
    uint32_t const meta_size = 20 + M + 16;
    uint8_t *metadata = calloc(meta_size, sizeof(uint8_t));
    if (metadata == NULL) {
        close_files(input_file, output_file);
        return 6; // Не удалось считать метаданные
    }
    for (uint32_t i = 20 + M; i < meta_size; ++i) {
        metadata[i] = 142;
    }
    metadata[0] = 128;

    if (mod != 0) {
        func_result const f_result = read_block_from_file(
            &(file_block_info){
                .file = input_file,
                .offset = file_size.result - mod,
                .data = metadata,
                .data_size = mod
            },
            NULL
        );

        if (f_result.error != 0) {
            close_files(input_file, output_file);
            free(metadata);
            return 6; // Не удалось считать метаданные
        }

        metadata[mod] = 128;
    }

    uint8_t *initial_vector = malloc(M * sizeof(uint8_t));
    if (initial_vector == NULL) {
        close_files(input_file, output_file);
        free(metadata);
        return 6; // Не удалось считать метаданные
    }

    srand(time(NULL));
    for (uint32_t i = 0; i < M; i += 8) {
        if (!_rdrand64_step((uint64_t*)(initial_vector + i))) {
            for (uint32_t j = 0; j < 8; ++j) {
                *(initial_vector + i + j) = (uint8_t)(rand() % 256);
            }
        }
    }

    memcpy(metadata + 16, initial_vector, M);
    memcpy(metadata + 16 + M, &M, 4);

    *total_steps = file_size.result / 16;

    uint8_t result = check_files(input_file, output_file, disk_space.result, file_size.result, meta_size - mod + 2);

    if (result == 1) {
        free(metadata);
        free(initial_vector);
        return 4; // Недостаточно места на диске
    }
    if (result == 2) {
        free(metadata);
        free(initial_vector);
        return 5; // Ошибка при увеличении выходного файла
    }

    func_result const f_result = write_metadata_to_file(
        output_file,
        file_size.result - mod,
        metadata,
        meta_size,
        after_file
    );

    if (f_result.error or f_result.result != (uint64_t)meta_size + 2) {
        close_files(input_file, output_file);
        free(metadata);
        free(initial_vector);
        return 6; // Не удалось записать метаданные
    }

    uint8_t **Ks;
    kyznechik_init();
    if (kyznechik_generate_keys(key, &Ks)) {
        close_files(input_file, output_file);
        free(metadata);
        free(initial_vector);
        return 8; // Не удалось создать ключи
    }

    uint8_t error = 0;

    result = kyznechik_cbc_work(
        input_file,
        output_file,
        *total_steps,
        current_step,
        Ks,
        ENCRYPT,
        metadata + 16,
        M
    );

    error = encrypt_last_bytes((const uint8_t**)Ks, metadata + 16, M, &(file_block_info){
                                   .file = output_file,
                                   .offset = *total_steps * 16,
                                   .data = metadata,
                                   .data_size = 16
                               });

    uint8_t const read_info = encrypt_check((const uint8_t**)Ks, &(file_block_info){
                                                .file = output_file,
                                                .offset = *total_steps * 16 + 20 + M,
                                                .data = metadata,
                                                .data_size = 16
                                            });

    kyznechik_finalize(Ks);
    close_files(input_file, output_file);
    free(metadata);
    free(initial_vector);

    if (result == 1) {
        return 9; // Ошибка при шифровании (обработка файлов)
    }
    if (result == 2) {
        return 10; // Ошибка при шифровании (выделение памяти)
    }
    if (error == 1 || read_info == 1) {
        return 11; // Ошибка при шифровании (запись последних байт)
    }
    return 0;
}

uint8_t remove_last_bytes(file_block_info const *block_info) {
    func_result const result = read_block_from_file(block_info, NULL);
    if (result.error != 0) {
        return 1; // Ошибка при чтении файла
    }

    uint8_t strip_size = 0;
    while (block_info->data[15 - strip_size] != 128) {
        ++strip_size;
    }

    LARGE_INTEGER out_file_size;
    out_file_size.QuadPart = (int64_t)block_info->offset - strip_size + 15;

    if (SetFilePointerEx(block_info->file, out_file_size, NULL, FILE_BEGIN) == 0) {
        return 2; // Ошибка при изменении размера файла
    }

    if (SetEndOfFile(block_info->file) == 0) {
        return 2; // Ошибка при изменении размера файла
    }

    return 0;
}

uint8_t decrypt_kyznechik_cbc(
    const WCHAR *file_in_path,
    const WCHAR *disk_out_name,
    const WCHAR *file_out_path,
    const uint8_t *key,
    uint16_t const num_threads,
    uint64_t *current_step,
    uint64_t *total_steps
) {
    *current_step = 0;
    func_result const disk_space = get_disk_free_space(disk_out_name);
    if (disk_space.error) {
        return 1; // Не удалось получить информацию о диске
    }

    HANDLE input_file, output_file;
    open_files(file_in_path, file_out_path, &input_file, &output_file);

    if (input_file == INVALID_HANDLE_VALUE || output_file == INVALID_HANDLE_VALUE) {
        close_files(input_file, output_file);
        return 2; // Не удалось открыть файл
    }

    func_result const file_size = get_file_size(input_file);
    if (file_size.error == 2) {
        close_files(input_file, output_file);
        return 3; // Не удалось получить размер файла
    }

    uint32_t m;
    func_result f_result = read_block_from_file(
        &(file_block_info){
            .file = input_file,
            .offset = file_size.result - 6 - 16,
            .data = (uint8_t*)&m,
            .data_size = 4
        },
        NULL
    );

    if (f_result.error != 0) {
        close_files(input_file, output_file);
        return 6; // Не удалось считать метаданные
    }

    uint8_t *initial_vector = malloc(m * sizeof(uint8_t));
    if (initial_vector == NULL) {
        close_files(input_file, output_file);
        return 6; // Не удалось считать метаданные
    }

    f_result = read_block_from_file(
        &(file_block_info){
            .file = input_file,
            .offset = file_size.result - 6 - m - 16,
            .data = initial_vector,
            .data_size = m
        },
        NULL
    );

    if (f_result.error != 0) {
        close_files(input_file, output_file);
        free(initial_vector);
        return 6; // Не удалось считать метаданные
    }

    *total_steps = (file_size.result - 6 - m) / 16 - 1;

    uint8_t **Ks;
    kyznechik_init();
    if (kyznechik_generate_keys(key, &Ks)) {
        close_files(input_file, output_file);
        free(initial_vector);
        return 8; // Не удалось создать ключи
    }

    uint8_t buf[16];
    func_result const read_info = read_block_from_file(&(file_block_info){
                                                           .file = input_file,
                                                           .offset = *total_steps * 16 + 4 + m,
                                                           .data_size = 16,
                                                           .data = buf
                                                       }, NULL);
    if (read_info.error != 0) {
        kyznechik_finalize(Ks);
        close_files(input_file, output_file);
        free(initial_vector);
        return 11; // Ошибка при расшифровании (чтение последних байт)
    }

    kyznechik_decrypt_data((const uint8_t**)Ks, buf, buf);
    for (uint8_t i = 0; i < 16; ++i) {
        if (buf[i] != 142) {
            kyznechik_finalize(Ks);
            close_files(input_file, output_file);
            free(initial_vector);
            return 12; // Неверный пароль
        }
    }

    uint8_t result = check_files(input_file, output_file, disk_space.result, *total_steps * 16, 0);
    if (result == 1) {
        kyznechik_finalize(Ks);
        free(initial_vector);
        return 4; // Недостаточно места на диске
    }
    if (result == 2) {
        kyznechik_finalize(Ks);
        free(initial_vector);
        return 5; // Ошибка при уменьшении выходного файла
    }

    uint8_t error = 0;

    result = kyznechik_cbc_work(
        input_file,
        output_file,
        *total_steps,
        current_step,
        Ks,
        DECRYPT,
        initial_vector,
        M
    );

    error = remove_last_bytes(&(file_block_info){
        .file = output_file,
        .offset = *total_steps * 16 - 16,
        .data_size = 16,
        .data = buf
    });

    kyznechik_finalize(Ks);
    close_files(input_file, output_file);
    free(initial_vector);

    if (result == 1) {
        return 9; // Ошибка при расшифровании (обработка файлов)
    }
    if (result == 2) {
        return 10; // Ошибка при расшифровании (выделение памяти)
    }
    if (error == 1) {
        return 11; // Ошибка при расшифровании (чтение последних байт)
    }
    if (error == 2) {
        return 5; // Ошибка при уменьшении выходного файла
    }
    return 0;
}
