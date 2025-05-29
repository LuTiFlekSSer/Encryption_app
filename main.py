import os
import sys

from src.frontend.instance_manager import InstanceManager


def except_hook(exc_type, exc_value, traceback):
    with open('error_log.txt', 'a') as f:
        f.write(f'Exception type: {exc_type}\n')
        f.write(f'Exception value: {exc_value}\n')
        f.write('Traceback:\n')
        f.write(''.join(traceback.format_exception(exc_type, exc_value, traceback)))


if getattr(sys, 'frozen', False):
    app_dir = os.path.dirname(sys.executable)
else:
    app_dir = os.path.dirname(os.path.abspath(__file__))

os.chdir(app_dir)


def main():
    # sys.excepthook = except_hook
    instance_manager = InstanceManager()

    if not instance_manager.try_acquire_lock():
        if len(sys.argv) > 2:
            instance_manager.send(sys.argv[1], sys.argv[2])
        elif len(sys.argv) > 1:
            instance_manager.send('decrypt', sys.argv[1])
        sys.exit(0)

    from src.frontend.hmi import create_ui
    from src.singleton_storage import SingletonStorage
    from src.sub_threads.loader_thread import LoaderThread
    from src.backend.db.db_records import OperationType

    singleton_storage = SingletonStorage()
    loader_thread = LoaderThread()
    loader_thread.start()

    app, window = create_ui()
    if len(sys.argv) > 2:
        operation_type = OperationType.ENCRYPT if sys.argv[1] == 'encrypt' else OperationType.DECRYPT
        window.sig_external_command.emit(operation_type, sys.argv[2])
    elif len(sys.argv) > 1:
        window.sig_external_command.emit(OperationType.DECRYPT, sys.argv[1])

    instance_manager.start_server()

    def on_about_to_quit():
        instance_manager.release_lock()

    app.aboutToQuit.connect(on_about_to_quit)
    instance_manager.sig_external_command.connect(window.sig_external_command.emit)

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
