import sys

from src.frontend.hmi import create_ui
from src.singleton_storage import SingletonStorage
from src.sub_threads.loader_thread import LoaderThread


def except_hook(exc_type, exc_value, traceback):
    with open('error_log.txt', 'a') as f:
        f.write(f'Exception type: {exc_type}\n')
        f.write(f'Exception value: {exc_value}\n')
        f.write('Traceback:\n')
        f.write(''.join(traceback.format_exception(exc_type, exc_value, traceback)))


def main():
    singleton_storage = SingletonStorage()

    loader_thread = LoaderThread()
    loader_thread.start()
    # sys.excepthook = except_hook
    app, window = create_ui()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
