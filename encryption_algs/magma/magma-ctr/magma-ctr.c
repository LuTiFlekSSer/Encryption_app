#include "magma-ctr.h"

#include <stdio.h>
#include <iso646.h>
#include <time.h>
#include <intrin.h>

#include "magma.h"
#include "utils.h"

uint8_t const S = 64; // можно менять от 8 до 64 кратно 8

char* get_cipher_name() {
    return "magma";
}

char* get_mode_name() {
    return "ctr";
}

uint8_t process_block(
    const uint8_t **Ks,
    file_block_info const *input_file_info,
    file_block_info const *output_file_info,
    uint64_t gamma,
    s_info const *s_data,
    HANDLE event
) {
    func_result result = read_block_from_file(input_file_info, event);
    if (result.error != 0) {
        return 1;
    }

    uint64_t cipher_output = 0, file_output = 0;
    for (uint32_t j = 0; j < input_file_info->data_size; j += s_data->CIPHER_BLOCK_SIZE) {
        magma_encrypt_data(Ks, (uint8_t*)&gamma, (uint8_t*)&cipher_output);
        cipher_output >>= s_data->SHIFT;

        memcpy(&file_output, input_file_info->data + j, s_data->CIPHER_BLOCK_SIZE);
        file_output ^= cipher_output;
        memcpy(output_file_info->data + j, &file_output, s_data->CIPHER_BLOCK_SIZE);

        ++gamma;
    }

    result = write_block_to_file(output_file_info, event);
    if (result.error != 0) { // todo сохранять часть
        return 1;
    }

    return 0;
}

DWORD WINAPI magma_ctr_thread(LPVOID raw_data) {
    thread_data const *data = raw_data;
    uint8_t *buf = malloc(BUF_SIZE * sizeof(uint8_t));

    if (buf == NULL) {
        *(data->error) = 2;
        return 2; // Ошибка при выделении памяти
    }

    HANDLE event = CreateEvent(NULL, TRUE, FALSE, NULL);
    if (event == NULL) {
        *(data->error) = 2;
        free(buf);
        return 2; // Ошибка при выделении памяти
    }

    uint64_t const total = (data->end - data->start) * data->s_data->CIPHER_BLOCK_SIZE / BUF_SIZE,
                   mod = (data->end - data->start) * data->s_data->CIPHER_BLOCK_SIZE % BUF_SIZE;

    file_block_info input_file_info = (file_block_info){.file = data->input_file, .data_size = BUF_SIZE, .data = buf},
                    output_file_info = (file_block_info){.file = data->output_file, .data_size = BUF_SIZE, .data = buf};

    for (uint64_t i = 0; i < total; ++i) {
        if (*(data->error) != 0) {
            free(buf);
            CloseHandle(event);
            return 1; // Ошибка при обработке файла
        }

        input_file_info.offset = output_file_info.offset = BUF_SIZE * i + data->start * data->s_data->CIPHER_BLOCK_SIZE;

        if (process_block((const uint8_t**)data->Ks,
                          &input_file_info,
                          &output_file_info,
                          data->gamma + data->start,
                          data->s_data,
                          event) != 0) {
            *(data->error) = 1;
            free(buf);
            CloseHandle(event);
            return 1; // Ошибка при обработке файла
        }

        EnterCriticalSection(data->lock);
        (*data->current_step) += BUF_SIZE / data->s_data->CIPHER_BLOCK_SIZE;
        LeaveCriticalSection(data->lock);
    }

    if (mod != 0) {
        if (*(data->error) != 0) {
            free(buf);
            CloseHandle(event);
            return 1; // Ошибка при обработке файла
        }

        input_file_info.offset = output_file_info.offset = total * BUF_SIZE + data->start * data->s_data->
            CIPHER_BLOCK_SIZE;
        input_file_info.data_size = output_file_info.data_size = mod;

        if (process_block((const uint8_t**)data->Ks,
                          &input_file_info,
                          &output_file_info,
                          data->gamma,
                          data->s_data,
                          event) != 0) {
            *(data->error) = 1;
            free(buf);
            CloseHandle(event);
            return 1; // Ошибка при обработке файла
        }

        EnterCriticalSection(data->lock);
        (*data->current_step) += mod / data->s_data->CIPHER_BLOCK_SIZE;
        LeaveCriticalSection(data->lock);
    }

    free(buf);
    CloseHandle(event);
    return 0;
}

uint8_t encrypt_last_bytes(const uint8_t **Ks, uint64_t gamma, file_block_info const *block_info) {
    uint64_t cipher_output = 0, file_output = 0;
    magma_encrypt_data(Ks, (uint8_t*)&gamma, (uint8_t*)&cipher_output);
    cipher_output >>= (8 - block_info->data_size) * 8;

    memcpy(&file_output, block_info->data, block_info->data_size);
    file_output ^= cipher_output;
    memcpy(block_info->data, &file_output, block_info->data_size);

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

    magma_encrypt_data(Ks, block_info->data, block_info->data);

    func_result const f_result = write_block_to_file(block_info, NULL);
    if (f_result.error != 0) {
        return 1; // Ошибка при записи в файл
    }

    return 0;
}

uint8_t encrypt_magma_ctr(
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

    uint8_t const mod = 5,
                  after_file[2] = {MAGMA, CTR};
    uint8_t metadata[13];
    for (uint32_t i = mod; i < 13; ++i) {
        metadata[i] = 142;
    }

    uint32_t initial_vector;
    srand(time(NULL));
    if (!_rdrand32_step(&initial_vector)) {
        for (uint8_t i = 0; i < 4; ++i) {
            ((uint8_t*)&initial_vector)[i] = (uint8_t)(rand() % 256);
        }
    }

    uint64_t ctr = (uint64_t)initial_vector << 32;

    memcpy(metadata, &initial_vector, mod - 1);
    metadata[mod - 1] = S;
    s_info s_data;
    initialize_s(S, MAGMA, &s_data);

    *total_steps = file_size.result / s_data.CIPHER_BLOCK_SIZE;
    uint8_t const last_bytes = file_size.result % s_data.CIPHER_BLOCK_SIZE;

    uint8_t result = check_files(input_file, output_file, disk_space.result, file_size.result, mod + 2 + 8);

    if (result == 1) {
        return 4; // Недостаточно места на диске
    }
    if (result == 2) {
        return 5; // Ошибка при увеличении выходного файла
    }

    func_result f_result = write_metadata_to_file(
        output_file,
        file_size.result,
        metadata,
        (uint32_t)mod + 8,
        after_file
    );

    if (f_result.error || f_result.result != mod + 2 + 8) {
        close_files(input_file, output_file);
        return 6; // Не удалось записать метаданные
    }

    f_result = read_block_from_file(
        &(file_block_info){
            .file = input_file,
            .offset = *total_steps * s_data.CIPHER_BLOCK_SIZE,
            .data = metadata,
            .data_size = last_bytes
        },
        NULL
    );

    if (f_result.error != 0) {
        close_files(input_file, output_file);
        return 6; // Не удалось считать метаданные
    }

    thread_data *threads_data;
    DWORD *threads_id;
    HANDLE *threads;

    if (create_threads_data(num_threads, &threads_data, &threads_id, &threads) != 0) {
        close_files(input_file, output_file);
        return 7; // Не удалось создать потоки
    }

    uint8_t **Ks;
    magma_init();
    if (magma_generate_keys(key, &Ks)) {
        close_files(input_file, output_file);
        delete_threads_data(threads_data, threads_id, threads);
        return 8; // Не удалось создать ключи
    }

    CRITICAL_SECTION lock;
    InitializeCriticalSection(&lock);
    uint8_t error = 0;

    uint64_t const length = (*total_steps) / num_threads;
    for (uint16_t i = 0; i < num_threads - 1; ++i) {
        threads_data[i] = (thread_data){
            .start = (uint64_t)i * length,
            .end = (uint64_t)(i + 1) * length,
            .current_step = current_step,
            .lock = &lock,
            .input_file = input_file,
            .output_file = output_file,
            .error = &error,
            .Ks = Ks,
            .gamma = ctr,
            .s_data = &s_data
        };
    }
    threads_data[num_threads - 1] = (thread_data){
        .start = (uint64_t)(num_threads - 1) * length,
        .end = (*total_steps),
        .current_step = current_step,
        .lock = &lock,
        .input_file = input_file,
        .output_file = output_file,
        .error = &error,
        .Ks = Ks,
        .gamma = ctr,
        .s_data = &s_data
    };

    for (uint16_t i = 0; i < num_threads; ++i) {
        threads[i] = CreateThread(
            NULL,
            0,
            magma_ctr_thread,
            &threads_data[i],
            0,
            &threads_id[i]
        );
    }

    WaitForMultipleObjects(num_threads, threads, TRUE, INFINITE);

    result = encrypt_last_bytes((const uint8_t**)Ks, ctr + *total_steps, &(file_block_info){
                                    .file = output_file,
                                    .offset = *total_steps * s_data.CIPHER_BLOCK_SIZE,
                                    .data = metadata,
                                    .data_size = last_bytes
                                });

    uint8_t const read_info = encrypt_check((const uint8_t**)Ks, &(file_block_info){
                                                .file = output_file,
                                                .offset = *total_steps * s_data.CIPHER_BLOCK_SIZE + last_bytes + mod,
                                                .data = metadata,
                                                .data_size = 8
                                            });

    for (uint16_t i = 0; i < num_threads; ++i) {
        CloseHandle(threads[i]);
    }
    magma_finalize(Ks);
    delete_threads_data(threads_data, threads_id, threads);
    DeleteCriticalSection(&lock);
    close_files(input_file, output_file);

    if (error == 1) {
        return 9; // Ошибка при шифровании (обработка файлов)
    }
    if (error == 2) {
        return 10; // Ошибка при шифровании (выделение памяти)
    }
    if (result == 1 || read_info == 1) {
        return 11; // Ошибка при шифровании (запись последних байт)
    }
    return 0;
}

uint8_t remove_last_bytes(HANDLE output_file, uint64_t const file_size) {
    LARGE_INTEGER out_file_size;
    out_file_size.QuadPart = (int64_t)file_size - 7 - 8;

    if (SetFilePointerEx(output_file, out_file_size, NULL, FILE_BEGIN) == 0) {
        return 1; // Ошибка при изменении размера файла
    }

    if (SetEndOfFile(output_file) == 0) {
        return 1; // Ошибка при изменении размера файла
    }
    return 0;
}

uint8_t decrypt_magma_ctr(
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

    uint8_t metadata[8];
    func_result f_result = read_block_from_file(
        &(file_block_info){
            .file = input_file,
            .offset = file_size.result - 7 - 8,
            .data = metadata,
            .data_size = 5
        },
        NULL
    );

    if (f_result.error != 0) {
        close_files(input_file, output_file);
        return 6; // Не удалось считать метаданные
    }

    s_info s_data;
    initialize_s(metadata[4], MAGMA, &s_data);

    uint32_t initial_vector;
    memcpy(&initial_vector, metadata, 4);
    uint64_t const ctr = (uint64_t)initial_vector << 32;

    *total_steps = (file_size.result - 7 - 8) / s_data.CIPHER_BLOCK_SIZE;
    uint8_t const last_bytes = (file_size.result - 7 - 8) % s_data.CIPHER_BLOCK_SIZE;

    thread_data *threads_data;
    DWORD *threads_id;
    HANDLE *threads;

    if (create_threads_data(num_threads, &threads_data, &threads_id, &threads) != 0) {
        close_files(input_file, output_file);
        return 7; // Не удалось создать потоки
    }

    uint8_t **Ks;
    magma_init();
    if (magma_generate_keys(key, &Ks)) {
        close_files(input_file, output_file);
        delete_threads_data(threads_data, threads_id, threads);
        return 8; // Не удалось создать ключи
    }

    func_result const read_info = read_block_from_file(&(file_block_info){
                                                           .file = input_file,
                                                           .offset = file_size.result - 2 - 8,
                                                           .data_size = 8,
                                                           .data = metadata
                                                       }, NULL);
    if (read_info.error != 0) {
        magma_finalize(Ks);
        close_files(input_file, output_file);
        delete_threads_data(threads_data, threads_id, threads);
        return 11; // Ошибка при расшифровании (чтение последних байт)
    }

    magma_decrypt_data((const uint8_t**)Ks, metadata, metadata);
    for (uint8_t i = 0; i < 8; ++i) {
        if (metadata[i] != 142) {
            magma_finalize(Ks);
            close_files(input_file, output_file);
            delete_threads_data(threads_data, threads_id, threads);
            return 12; // Неверный пароль
        }
    }

    uint8_t result = check_files(input_file, output_file, disk_space.result, file_size.result - 7 - 8, 0);
    if (result == 1) {
        magma_finalize(Ks);
        delete_threads_data(threads_data, threads_id, threads);
        return 4; // Недостаточно места на диске
    }
    if (result == 2) {
        magma_finalize(Ks);
        delete_threads_data(threads_data, threads_id, threads);
        return 5; // Ошибка при увеличении выходного файла
    }
    f_result = read_block_from_file(
        &(file_block_info){
            .file = input_file,
            .offset = *total_steps * s_data.CIPHER_BLOCK_SIZE,
            .data = metadata,
            .data_size = last_bytes
        },
        NULL
    );

    if (f_result.error != 0) {
        close_files(input_file, output_file);
        return 6; // Не удалось считать метаданные
    }

    CRITICAL_SECTION lock;
    InitializeCriticalSection(&lock);
    uint8_t error = 0;

    uint64_t const length = (*total_steps) / num_threads;
    for (uint16_t i = 0; i < num_threads - 1; ++i) {
        threads_data[i] = (thread_data){
            .start = (uint64_t)i * length,
            .end = (uint64_t)(i + 1) * length,
            .current_step = current_step,
            .lock = &lock,
            .input_file = input_file,
            .output_file = output_file,
            .error = &error,
            .Ks = Ks,
            .gamma = ctr,
            .s_data = &s_data
        };
    }
    threads_data[num_threads - 1] = (thread_data){
        .start = (uint64_t)(num_threads - 1) * length,
        .end = (*total_steps),
        .current_step = current_step,
        .lock = &lock,
        .input_file = input_file,
        .output_file = output_file,
        .error = &error,
        .Ks = Ks,
        .gamma = ctr,
        .s_data = &s_data
    };

    for (uint16_t i = 0; i < num_threads; ++i) {
        threads[i] = CreateThread(
            NULL,
            0,
            magma_ctr_thread,
            &threads_data[i],
            0,
            &threads_id[i]
        );
    }
    WaitForMultipleObjects(num_threads, threads, TRUE, INFINITE);


    result = encrypt_last_bytes((const uint8_t**)Ks, ctr + *total_steps, &(file_block_info){
                                    .file = output_file,
                                    .offset = *total_steps * s_data.CIPHER_BLOCK_SIZE,
                                    .data = metadata,
                                    .data_size = last_bytes
                                });


    for (uint16_t i = 0; i < num_threads; ++i) {
        CloseHandle(threads[i]);
    }
    magma_finalize(Ks);
    delete_threads_data(threads_data, threads_id, threads);
    DeleteCriticalSection(&lock);
    if (input_file == output_file) {
        if (remove_last_bytes(output_file, file_size.result) != 0) {
            return 5; // Ошибка при изменении размера файла
        }
    }
    close_files(input_file, output_file);

    if (error == 1) {
        return 9; // Ошибка при расшифровании (обработка файлов)
    }
    if (error == 2) {
        return 10; // Ошибка при расшифровании (выделение памяти)
    }
    if (result == 1) {
        return 11; // Ошибка при расшифровании (запись последних байт)
    }
    return 0;
}
