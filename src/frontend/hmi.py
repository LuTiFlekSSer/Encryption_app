import sys
import time

from PyQt5.QtCore import QSize, QEventLoop, QTimer, Qt
from PyQt5.QtGui import QIcon, QGuiApplication
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import SplashScreen, FluentIcon, MSFluentWindow, NavigationItemPosition, setTheme, Theme, \
    setThemeColor, SystemThemeListener, InfoBar, InfoBarPosition
from qframelesswindow.utils import getSystemAccentColor

from src.backend.db.data_base import DataBase
from src.frontend.encrypt_window.encrypt_window import EncryptWindow
from src.frontend.history_window.history_window import HistoryWindow
from src.frontend.home_window.home_window import HomeWindow
from src.frontend.settings_window.settings_window import SettingsWindow
from src.global_flags import GlobalFlags
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import resource_path


class MainWindow(MSFluentWindow):
    def __init__(self, app: QApplication):
        super().__init__()

        self.ULTRA_MEGA_PARENT: str = 'parent'

        self._locales: Locales = Locales()
        self._db: DataBase = DataBase()
        self._global_flags: GlobalFlags = GlobalFlags()

        setTheme(getattr(Theme, self._db.get_setting('theme')))
        setThemeColor(getSystemAccentColor(), save=False)
        self._themeListener = SystemThemeListener(self)
        self._themeListener.systemThemeChanged.connect(lambda: setTheme(Theme.AUTO))

        self.resize(*map(int, self._db.get_setting('window_size').split()))
        self.setMinimumWidth(840)
        self.setWindowTitle(Config.APP_NAME)
        self.setWindowIcon(QIcon(resource_path('res/logo.png')))
        self._center()

        self._splashscreen: SplashScreen = SplashScreen(self.windowIcon(), self)
        self._splashscreen.setIconSize(QSize(120, 120))
        self._splashscreen.titleBar.hide()

        if self._db.get_setting('window_mode') == 'normal':
            self.show()
        else:
            self.showMaximized()

            screen = app.primaryScreen()
            available = screen.availableGeometry()

            self._splashscreen.setFixedWidth(available.width())
            self._splashscreen.setFixedHeight(available.height())

        self._init_screen()

        self._splashscreen.finish()
        self._themeListener.start()

    def _init_screen(self):
        init_start = time.time()

        self._home_window = HomeWindow(Config.APP_NAME, parent=self)
        self.addSubInterface(self._home_window, FluentIcon.HOME, self._locales.get_string('home'))

        self._encrypt_window = EncryptWindow(self._locales.get_string('encrypt'), parent=self)
        self.addSubInterface(self._encrypt_window, FluentIcon.VPN, self._locales.get_string('encrypt'))

        self._history_window = HistoryWindow(self._locales.get_string('history'), parent=self)
        self.addSubInterface(self._history_window, FluentIcon.HISTORY, self._locales.get_string('history'))

        self._settings_window = SettingsWindow(self._locales.get_string('settings'), parent=self)
        self.addSubInterface(self._settings_window,
                             FluentIcon.SETTING,
                             self._locales.get_string('settings'),
                             position=NavigationItemPosition.BOTTOM)

        if (init_time := (time.time() - init_start)) < Config.SPLASH_SCREEN_TIME:
            loop = QEventLoop(self)
            QTimer.singleShot(int((Config.SPLASH_SCREEN_TIME - init_time) * 1000), loop.quit)
            loop.exec()

    def _center(self):
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()

        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def closeEvent(self, event):
        if not self._global_flags.is_running.is_set():
            if self.isMaximized():
                self._db.set_setting('window_mode', 'maximized')
            else:
                self._db.set_setting('window_size', f'{self.width()} {self.height()}')
                self._db.set_setting('window_mode', 'normal')

            self._themeListener.terminate()
            self._themeListener.deleteLater()

            self._global_flags.stop_event.set()

            event.accept()
        else:
            InfoBar.error(
                title=self._locales.get_string('error'),
                content=self._locales.get_string('close_error_message'),
                orient=Qt.Horizontal,
                isClosable=False,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                parent=self
            )

            event.ignore()


def create_ui() -> tuple[QApplication, MainWindow]:
    QApplication.setHighDpiScaleFactorRoundingPolicy(Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)

    app = QApplication(sys.argv)
    window = MainWindow(app)
    window.show()

    return app, window
