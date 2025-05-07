import sys

from src.frontend.hmi import create_ui
from src.singleton_storage import SingletonStorage
from src.sub_threads.loader_thread import LoaderThread


def main():
    singleton_storage = SingletonStorage()

    loader_thread = LoaderThread()
    loader_thread.start()

    app, window = create_ui()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
