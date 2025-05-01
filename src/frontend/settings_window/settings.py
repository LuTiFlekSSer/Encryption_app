from typing import Union

from PyQt5.QtCore import QUrl, QObject, Qt, pyqtSignal
from PyQt5.QtGui import QDesktopServices, QColor, QIcon
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import TitleLabel, FluentIcon, PrimaryPushSettingCard, SwitchSettingCard, ComboBoxSettingCard, \
    InfoBar, InfoBarPosition, setTheme, Theme, SettingCard, FluentIconBase, SpinBox, setCustomStyleSheet

from src.frontend.settings_window.custom_config import custom_config
from src.locales.locales import Locales
from src.utils.config import Config
from src.utils.utils import find_mega_parent
from src.version import __version__

qss_light = f'''#sosal-label{{color: {Config.GRAY_COLOR_700}; font-size: 12px;}}
QLabel{{color: {Config.GRAY_COLOR_900};}}
'''
qss_dark = f'''#sosal-label{{color: {Config.GRAY_COLOR_200}; font-size: 12px;}}
QLabel{{color: {Config.GRAY_COLOR_50};}}
'''


class CustomSwitchingCard(SwitchSettingCard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._locales: Locales = Locales()

    def setValue(self, isChecked: bool):
        if self.configItem:
            custom_config.set(self.configItem, isChecked)

        self.switchButton.setChecked(isChecked)
        self.switchButton.setText(
            self._locales.get_string('turn_on') if isChecked else self._locales.get_string('turn_off'))


class CustomComboBoxSettingCard(ComboBoxSettingCard):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._locales: Locales = Locales()
        self._hmi: QObject = find_mega_parent(self)

    def setValue(self, value):
        if value not in self.optionToText:
            return

        self.comboBox.setCurrentText(self.optionToText[value])
        custom_config.set(self.configItem, value)

        if self.configItem == custom_config.app_language:
            InfoBar.info(
                title=self._locales.get_string('notification'),
                content=self._locales.get_string('restart_notification'),
                orient=Qt.Horizontal,
                position=InfoBarPosition.BOTTOM_RIGHT,
                duration=3000,
                isClosable=False,
                parent=self._hmi
            )
        elif self.configItem == custom_config.app_theme:
            setTheme(getattr(Theme, value))

    def _onCurrentIndexChanged(self, index: int):
        custom_config.set(self.configItem, self.comboBox.itemData(index))


class SpinBoxSettingCard(SettingCard):
    valueChanged = pyqtSignal(int)

    def __init__(self, configItem, icon: Union[str, QIcon, FluentIconBase], title, content=None, parent=None):
        super().__init__(icon, title, content, parent)
        self.configItem = configItem
        self.spin_box = SpinBox(self)

        self.contentLabel.setObjectName('sosal-label')
        setCustomStyleSheet(self,
                            qss_light,
                            qss_dark)

        self.spin_box.setRange(*configItem.range)
        self.spin_box.setValue(configItem.value)

        self.hBoxLayout.addStretch(1)
        self.hBoxLayout.addWidget(self.spin_box, 0, Qt.AlignRight)
        self.hBoxLayout.addSpacing(16)

        configItem.valueChanged.connect(self.setValue)
        self.spin_box.valueChanged.connect(self.__onValueChanged)

    def __onValueChanged(self, value: int):
        self.setValue(value)
        self.valueChanged.emit(value)

    def setValue(self, value):
        custom_config.set(self.configItem, value)
        self.spin_box.setValue(value)


class SettingSection(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent=parent)

        self._layout: QVBoxLayout = QVBoxLayout(self)
        self._l_title: TitleLabel = TitleLabel(self)

        self.__init_widgets(title)

    def __init_widgets(self, title: str):
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(4)

        self._l_title.setText(title)
        self._l_title.setObjectName('settings-section-title')
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._layout.addWidget(self._l_title)
        self._layout.addSpacing(12)


class EncryptionSettings(SettingSection):
    def __init__(self, parent=None):
        self._locales: Locales = Locales()
        super().__init__(self._locales.get_string('encryption_params'), parent=parent)

        self._encryption_threads: SpinBoxSettingCard = SpinBoxSettingCard(
            configItem=custom_config.encryption_threads,
            icon=FluentIcon.CALORIES.colored(QColor(Config.GRAY_COLOR_900),
                                             QColor(Config.GRAY_COLOR_50)),
            title=self._locales.get_string('encryption_threads'),
            content=self._locales.get_string('encryption_threads_description'),
            parent=self
        )

        self._queue_width: SpinBoxSettingCard = SpinBoxSettingCard(
            configItem=custom_config.queue_width,
            icon=FluentIcon.TILES.colored(QColor(Config.GRAY_COLOR_900),
                                          QColor(Config.GRAY_COLOR_50)),
            title=self._locales.get_string('queue_width'),
            content=self._locales.get_string('queue_width_description'),
            parent=self
        )

        self._layout.addWidget(self._encryption_threads)
        self._layout.addWidget(self._queue_width)


class AppSettings(SettingSection):
    def __init__(self, parent=None):
        self._locales: Locales = Locales()
        super().__init__(self._locales.get_string('application'), parent=parent)

        self._history_size: SpinBoxSettingCard = SpinBoxSettingCard(
            configItem=custom_config.history_size,
            icon=FluentIcon.HISTORY.colored(QColor(Config.GRAY_COLOR_900),
                                            QColor(Config.GRAY_COLOR_50)),
            title=self._locales.get_string('history_size'),
            content=self._locales.get_string('history_size_description'),
            parent=self
        )

        self._app_theme: CustomComboBoxSettingCard = CustomComboBoxSettingCard(
            configItem=custom_config.app_theme,
            icon=FluentIcon.PALETTE.colored(QColor(Config.GRAY_COLOR_900),
                                            QColor(Config.GRAY_COLOR_50)),
            title=self._locales.get_string('app_theme'),
            content=self._locales.get_string('app_theme_description'),
            texts=[
                self._locales.get_string('dark_theme'),
                self._locales.get_string('light_theme'),
                self._locales.get_string('auto_theme')
            ],
            parent=self
        )
        self._app_theme.contentLabel.setObjectName('sosal-label')
        setCustomStyleSheet(self._app_theme,
                            qss_light,
                            qss_dark)

        self._app_language: CustomComboBoxSettingCard = CustomComboBoxSettingCard(
            configItem=custom_config.app_language,
            icon=FluentIcon.LANGUAGE.colored(QColor(Config.GRAY_COLOR_900),
                                             QColor(Config.GRAY_COLOR_50)),
            title=self._locales.get_string('app_language'),
            content=self._locales.get_string('app_language_description'),
            texts=[
                'Русский',
                'English'
            ],
            parent=self
        )
        self._app_language.contentLabel.setObjectName('sosal-label')
        setCustomStyleSheet(self._app_language,
                            qss_light,
                            qss_dark)

        self._about: PrimaryPushSettingCard = PrimaryPushSettingCard(
            icon=FluentIcon.INFO.colored(QColor(Config.GRAY_COLOR_900),
                                         QColor(Config.GRAY_COLOR_50)),
            title=self._locales.get_string('about'),
            content=self._locales.get_string('about_description').format(version=__version__),
            text=self._locales.get_string('check_for_updates'),
            parent=self
        )
        self._about.contentLabel.setObjectName('sosal-label')
        setCustomStyleSheet(self._about,
                            qss_light,
                            qss_dark)

        self._about.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(Config.GITHUB_RELEASES_URL)))

        self._layout.addWidget(self._history_size)
        self._layout.addWidget(self._app_theme)
        self._layout.addWidget(self._app_language)
        self._layout.addWidget(self._about)
