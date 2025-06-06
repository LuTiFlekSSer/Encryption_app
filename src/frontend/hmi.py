import sys
import time
from typing import Optional

from PyQt5.QtCore import QSize, QEventLoop, QTimer, Qt, pyqtSignal, QEvent
from PyQt5.QtGui import QIcon, QGuiApplication
from PyQt5.QtWidgets import QApplication
from qfluentwidgets import SplashScreen, FluentIcon, MSFluentWindow, NavigationItemPosition, setTheme, Theme, \
    setThemeColor, SystemThemeListener, InfoBar, InfoBarPosition
from qframelesswindow.utils import getSystemAccentColor

from src.backend.db.data_base import DataBase
from src.backend.db.db_records import OperationType
from src.frontend.encrypt_window.encrypt_window import EncryptWindow
from src.frontend.history_window.history_window import HistoryWindow
from src.frontend.home_window.home_window import HomeWindow
from src.frontend.icons.icons import CustomIcons
from src.frontend.passwords_window.passwords_window import PasswordsWindow
from src.frontend.settings_window.settings_window import SettingsWindow
from src.global_flags import GlobalFlags
from src.locales.locales import Locales
from src.utils.config import Config


class MainWindow(MSFluentWindow):
    sig_check_passwords: pyqtSignal = pyqtSignal()
    sig_passwords_check_completed: pyqtSignal = pyqtSignal(bool)
    sig_add_new_password: pyqtSignal = pyqtSignal(str)
    sig_external_command: pyqtSignal = pyqtSignal(OperationType, str)
    sig_to_front: pyqtSignal = pyqtSignal()

    sig_add_task: pyqtSignal = pyqtSignal()

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
        self.setMinimumHeight(480)

        self.setWindowTitle(Config.APP_NAME)
        self.setWindowIcon(QIcon('res/logo.png'))
        self._center()

        self._splashscreen: SplashScreen = SplashScreen(self.windowIcon(), self)
        self._splashscreen.setIconSize(QSize(120, 120))
        self._splashscreen.titleBar.hide()
        self.show()

        self._operation_type: Optional[str] = None
        self._data: Optional[str] = None

        self._init_screen()

        self._splashscreen.finish()
        self._themeListener.start()

        if self._db.get_setting('window_mode') == 'maximized':
            self.showMaximized()

    def _init_screen(self):
        init_start = time.time()

        self._home_window = HomeWindow(Config.APP_NAME, parent=self)
        self.addSubInterface(self._home_window, FluentIcon.HOME, self._locales.get_string('home'))

        self._encrypt_window = EncryptWindow(self._locales.get_string('encrypt'), parent=self)
        self.addSubInterface(self._encrypt_window, FluentIcon.VPN, self._locales.get_string('encrypt'))

        self._passwords_window = PasswordsWindow(self._locales.get_string('passwords'), parent=self)
        self.addSubInterface(self._passwords_window, CustomIcons.KEY, self._locales.get_string('passwords'))

        self._history_window = HistoryWindow(self._locales.get_string('history'), parent=self)
        self.addSubInterface(self._history_window, FluentIcon.HISTORY, self._locales.get_string('history'))

        self._settings_window = SettingsWindow(self._locales.get_string('settings'), parent=self)
        self.addSubInterface(self._settings_window,
                             FluentIcon.SETTING,
                             self._locales.get_string('settings'),
                             position=NavigationItemPosition.BOTTOM)

        self.sig_to_front.connect(self._on_sig_to_front)

        if (init_time := (time.time() - init_start)) < Config.SPLASH_SCREEN_TIME:
            loop = QEventLoop(self)
            QTimer.singleShot(int((Config.SPLASH_SCREEN_TIME - init_time) * 1000), loop.quit)
            loop.exec()

    def _on_sig_to_front(self):
        self.activateWindow()
        self.raise_()

    def _center(self):
        screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.availableGeometry()
        window_geometry = self.frameGeometry()
        center_point = screen_geometry.center()

        window_geometry.moveCenter(center_point)
        self.move(window_geometry.topLeft())

    def changeEvent(self, event):
        if event.type() == QEvent.Type.WindowStateChange:
            if self.isMaximized():
                desktop_rect = QApplication.desktop().availableGeometry(self)

                if self.width() < desktop_rect.width() * 0.95 or \
                        self.height() < desktop_rect.height() * 0.95:
                    self._db.set_setting('window_size', f'{self.width()} {self.height()}')

                self._db.set_setting('window_mode', 'maximized')

        super().changeEvent(event)

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
