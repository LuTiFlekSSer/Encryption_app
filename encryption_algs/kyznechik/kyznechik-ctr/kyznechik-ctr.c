#include "kyznechik-ctr.h"

#include <stdio.h>
#include <iso646.h>
#include <time.h>
#include <intrin.h>

#include "kyznechik.h"
#include "utils.h"

uint8_t const S = 128, // можно менять от 8 до 128 кратно 8
              CIPHER_BLOCK_SIZE = S / 8,
              SHIFT = (16 - CIPHER_BLOCK_SIZE) * 8;

uint8_t process_block(
    const uint8_t **Ks,
    file_block_info const *input_file_info,
    file_block_info const *output_file_info,
    __uint128_t gamma,
    void (*cipher_func)(uint8_t const **, uint8_t const *, uint8_t *),
    HANDLE event
) {
    func_result result = read_block_from_file(input_file_info, event);
    if (result.error != 0) {
        return 1;
    }

    __uint128_t cipher_output = 0, file_output = 0;
    for (int j = 0; j < input_file_info->data_size; j += CIPHER_BLOCK_SIZE) {
        cipher_func(Ks, (uint8_t*)&gamma, (uint8_t*)&cipher_output);
        cipher_output >>= SHIFT;

        memcpy(&file_output, input_file_info->data + j, CIPHER_BLOCK_SIZE);
        file_output ^= cipher_output;
        memcpy(output_file_info->data + j, &file_output, CIPHER_BLOCK_SIZE);

        ++gamma;
    }

    result = write_block_to_file(output_file_info, event);
    if (result.error != 0) { // todo сохранять часть
        return 1;
    }

    return 0;
}

DWORD WINAPI kyznechik_ctr_thread(LPVOID raw_data) {
    thread_data const *data = raw_data;
    uint8_t *buf = malloc(BUF_SIZE * sizeof(uint8_t));

    void (*cipher_func)(uint8_t const **, uint8_t const *, uint8_t *);
    if (data->func_type == ENCRYPT) {
        cipher_func = kyznechik_encrypt_data;
    } else {
        cipher_func = kyznechik_decrypt_data;
    }

    if (buf == NULL) {
        *(data->error) = 2;
        return 2;
    }

    HANDLE event = CreateEvent(NULL, TRUE, FALSE, NULL);
    if (event == NULL) {
        *(data->error) = 2;
        free(buf);
        return 2;
    }

    uint64_t const total = (data->end - data->start) * CIPHER_BLOCK_SIZE / BUF_SIZE,
                   mod = (data->end - data->start) * CIPHER_BLOCK_SIZE % BUF_SIZE;

    file_block_info input_file_info = (file_block_info){.file = data->input_file, .data_size = BUF_SIZE, .data = buf},
                    output_file_info = (file_block_info){.file = data->output_file, .data_size = BUF_SIZE, .data = buf};

    for (uint64_t i = 0; i < total; ++i) {
        if (*(data->error) != 0) {
            free(buf);
            CloseHandle(event);
            return 1;
        }

        input_file_info.offset = output_file_info.offset = BUF_SIZE * i + data->start * CIPHER_BLOCK_SIZE;

        if (process_block((const uint8_t**)data->Ks,
                          &input_file_info,
                          &output_file_info,
                          data->gamma + data->start,
                          cipher_func,
                          event) != 0) {
            *(data->error) = 1;
            free(buf);
            CloseHandle(event);
            return 1;
        }

        if ((i + 1) % 256 == 0) {
            EnterCriticalSection(data->lock);
            (*data->current_step) += BUF_SIZE * CIPHER_BLOCK_SIZE;
            LeaveCriticalSection(data->lock);
        }
    }

    EnterCriticalSection(data->lock);
    (*data->current_step) += BUF_SIZE / CIPHER_BLOCK_SIZE * (total % 256);
    LeaveCriticalSection(data->lock);

    if (mod != 0) {
        if (*(data->error) != 0) {
            free(buf);
            CloseHandle(event);
            return 1;
        }

        input_file_info.offset = output_file_info.offset = total * BUF_SIZE + data->start * CIPHER_BLOCK_SIZE;
        input_file_info.data_size = output_file_info.data_size = mod;

        if (process_block((const uint8_t**)data->Ks,
                          &input_file_info,
                          &output_file_info,
                          data->gamma,
                          cipher_func,
                          event) != 0) {
            *(data->error) = 1;
            free(buf);
            CloseHandle(event);
            return 1;
        }

        EnterCriticalSection(data->lock);
        (*data->current_step) += mod / CIPHER_BLOCK_SIZE;
        LeaveCriticalSection(data->lock);
    }

    return 0;
}

uint8_t encrypt_kyznechik_ctr(
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

    uint8_t const mod = 9,
                  after_file[2] = {KYZNECHIK, CTR};
    uint8_t metadata[mod];

    uint64_t initial_vector;
    if (!_rdrand64_step(&initial_vector)) {
        srand(time(NULL));
        initial_vector = ((uint64_t)rand()) << 32 | (uint64_t)rand();
    }

    __uint128_t ctr = (__uint128_t)initial_vector << 64;

    memcpy(metadata, &initial_vector, mod - 1);
    metadata[mod - 1] = S;

    *total_steps = file_size.result / CIPHER_BLOCK_SIZE;

    uint8_t result = check_files(input_file, output_file, disk_space.result, file_size.result, mod + 2);

    if (result == 1) {
        return 4; // недостаточно места на диске
    }
    if (result == 2) {
        return 5; // ошибка при увеличении выходного файла
    }

    func_result const f_result = write_metadata_to_file(
        output_file,
        file_size.result,
        metadata,
        mod,
        after_file
    );

    if (f_result.error || f_result.result != mod + 2) {
        close_files(input_file, output_file);
        return 6; // Не удалось записать метаданные
    }

    thread_data *threads_data;
    DWORD *threads_id;
    HANDLE *threads;

    if (create_threads_data(num_threads, &threads_data, &threads_id, &threads) != 0) {
        return 7; // не удалось создать потоки
    }

    uint8_t **Ks;
    kyznechik_init();
    if (kyznechik_generate_keys(key, &Ks)) {
        return 8; // не удалось создать ключи
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
            .func_type = ENCRYPT,
            .gamma = ctr
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
        .func_type = ENCRYPT,
        .gamma = ctr
    };

    for (uint16_t i = 0; i < num_threads; ++i) {
        threads[i] = CreateThread(
            NULL,
            0,
            kyznechik_ctr_thread,
            &threads_data[i],
            0,
            &threads_id[i]
        );
    }

    WaitForMultipleObjects(num_threads, threads, TRUE, INFINITE);

    for (uint16_t i = 0; i < num_threads; ++i) {
        CloseHandle(threads[i]);
    }
    kyznechik_finalize(Ks);
    delete_threads_data(threads_data, threads_id, threads);
    DeleteCriticalSection(&lock);
    close_files(input_file, output_file);

    if (error != 0 or result != 0) {
        return 9; //ошибка при шифровании
    }

    return 0;
}

uint8_t decrypt_kyznechik_ctr(
    const WCHAR *file_in_path,
    const WCHAR *disk_out_name,
    const WCHAR *file_out_path,
    const uint8_t *key,
    uint16_t const num_threads,
    uint64_t *current_step,
    uint64_t *total_steps
) {
    return 0;
}
