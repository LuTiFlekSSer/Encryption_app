from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea

from src.backend.encrypt_libs.encrypt_lib import LibStatus
from src.backend.encrypt_libs.loader import Loader
from src.frontend.home_window.banner import Banner
from src.frontend.home_window.lib_info_card import LibInfoCardView
from src.frontend.style_sheets.style_sheets import StyleSheet
from src.locales.locales import Locales

locales = Locales()
map_status_to_description: dict[LibStatus, str] = {
    LibStatus.SUCCESS: locales.get_string('success'),
    LibStatus.LOAD_FUNCS_ERROR: locales.get_string('lib_load_funcs_error'),
    LibStatus.TEST_ERROR: locales.get_string('lib_test_error'),
}


class HomeWindow(ScrollArea):
    def __init__(self, name: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(name.replace(' ', '-'))
        self._locales: Locales = Locales()

        self._banner: Banner = Banner(self)
        self._lib_info_cards: LibInfoCardView = LibInfoCardView(self._locales.get_string('lib_status'), self)
        self._loader: Loader = Loader()

        self.__initWidget()

        self._connect_widget_actions()

    def __initWidget(self):
        StyleSheet.HOME_WINDOW.apply(self)

        self._w_view: QWidget = QWidget(self)
        self._w_view.setObjectName('w_view')

        self._vl_view_layout: QVBoxLayout = QVBoxLayout(self._w_view)

        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setWidget(self._w_view)
        self.setWidgetResizable(True)

        self._vl_view_layout.setContentsMargins(0, 0, 28, 28)
        self._vl_view_layout.setSpacing(40)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._vl_view_layout.addWidget(self._banner)
        self._vl_view_layout.addWidget(self._lib_info_cards, 1)

    def _connect_widget_actions(self):
        for mode, status in self._loader.status.items():
            self._lib_info_cards.add_card(
                mode,
                map_status_to_description[status],
                status == LibStatus.SUCCESS
            )
