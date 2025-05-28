import sys

from src.frontend.hmi import create_ui
from src.frontend.instance_manager import InstanceManager
from src.singleton_storage import SingletonStorage
from src.sub_threads.loader_thread import LoaderThread


def except_hook(exc_type, exc_value, traceback):
    with open('error_log.txt', 'a') as f:
        f.write(f'Exception type: {exc_type}\n')
        f.write(f'Exception value: {exc_value}\n')
        f.write('Traceback:\n')
        f.write(''.join(traceback.format_exception(exc_type, exc_value, traceback)))


def check_instance() -> InstanceManager:
    instance_manager = InstanceManager()

    if instance_manager.is_running():
        if len(sys.argv) > 2:
            instance_manager.send(sys.argv[1], sys.argv[2])
        elif len(sys.argv) > 1:
            instance_manager.send('decrypt', sys.argv[1])

        sys.exit(0)

    return instance_manager


def main():
    # sys.excepthook = except_hook
    instance_manager = check_instance()
    singleton_storage = SingletonStorage()

    loader_thread = LoaderThread()
    loader_thread.start()

    app, window = create_ui()

    instance_manager.start_server()
    instance_manager.sig_external_command.connect(window.sig_external_command.emit)
    # todo если это первый экземпляр, то добавить в очередь какую нибудь

    sys.exit(app.exec())


if __name__ == '__main__':
    main()
