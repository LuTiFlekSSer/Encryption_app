#include "kyznechik-ecb.h"

#include <stdio.h>
#include <iso646.h>

#include "utils.h"


DWORD WINAPI encrypt_kyznechik_ecb_thread(LPVOID raw_data) {
    thread_data const *data = raw_data; // todo не забыть шаг умножить на 16
    file_block_info input_file_info = (file_block_info){.file = data->input_file, .data_size = 16},
                    output_file_info = (file_block_info){.file = data->output_file, .data_size = 16};
    for (uint64_t i = data->start; i < data->end; ++i) {
        input_file_info.offset = output_file_info.offset = i * 16;
        func_result result = read_block_from_file(&input_file_info);
    }
}

uint8_t encrypt_kyznechik_ecb(
    const WCHAR *file_in_path,
    const WCHAR *disk_out_name,
    const WCHAR *file_out_path,
    const uint8_t *key,
    uint16_t const num_threads,
    uint64_t *current_step,
    uint64_t *total_steps
) {
    // todo проверка что флешку не вытащили при записи
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

    uint8_t const mod = file_size.result % 16,
                  delta[16] = {1},
                  after_file[2] = {KYZNECHIK, ECB};

    *total_steps = file_size.result / 16 + 1;

    uint8_t files_check_result = check_files(input_file, output_file, disk_space.result,
                                             file_size.result, 16 - mod + 2);

    if (files_check_result == 1) {
        return 4; // недостаточно места на диске
    }
    if (files_check_result == 2) {
        return 5; // ошибка при увеличении выходного файла
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
        return 6; // Не удалось записать метаданные
    }

    thread_data *threads_data;
    DWORD *threads_id;
    HANDLE *threads;

    create_threads_data(num_threads, &threads_data, &threads_id, &threads);

    CRITICAL_SECTION lock;
    InitializeCriticalSection(&lock);

    uint64_t const length = (*total_steps) / num_threads;
    for (uint16_t i = 0; i < num_threads - 1; ++i) {
        threads_data[i] = (thread_data){
            .start = (uint64_t)i * length, .end = (uint64_t)(i + 1) * length, .current_step = current_step,
            .lock = &lock, .input_file = input_file, .output_file = output_file
        };
    }
    threads_data[num_threads - 1] = (thread_data){
        .start = (uint64_t)(num_threads - 1) * length, .end = (*total_steps), .current_step = current_step,
        .lock = &lock, .input_file = input_file, .output_file = output_file
    };

    for (uint16_t i = 0; i < num_threads; ++i) {
        threads[i] = CreateThread(
            NULL,
            0,
            encrypt_kyznechik_ecb_thread,
            &threads_data[i],
            0,
            &threads_id[i]
        );
    }

    WaitForMultipleObjects(num_threads, threads, TRUE, INFINITE);

    for (uint16_t i = 0; i < num_threads; ++i) {
        CloseHandle(threads[i]);
    }
    delete_threads_data(threads_data, threads_id, threads);
    DeleteCriticalSection(&lock);
    close_files(input_file, output_file);
    return 0;
}
