import sys

from src.frontend.hmi import create_ui
from src.singleton_storage import SingletonStorage


def main():
    singleton_storage = SingletonStorage()

    app, window = create_ui()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
