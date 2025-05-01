from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout
from qfluentwidgets import ScrollArea

from src.frontend.home_window.banner import Banner
from src.frontend.home_window.lib_info_card import LibInfoCardView
from src.locales.locales import Locales
from src.frontend.style_sheets.style_sheets import StyleSheet


class HomeWindow(ScrollArea):
    def __init__(self, name: str, parent=None):
        super().__init__(parent=parent)
        self.setObjectName(name.replace(' ', '-'))
        self._locales: Locales = Locales()

        self._banner: Banner = Banner(self)
        self._lib_info_cards: LibInfoCardView = LibInfoCardView(self._locales.get_string('lib_status'), self)

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

        self._vl_view_layout.setContentsMargins(0, 0, 28, 40)
        self._vl_view_layout.setSpacing(40)
        self._vl_view_layout.setAlignment(Qt.AlignTop)

        self._vl_view_layout.addWidget(self._banner)
        self._vl_view_layout.addWidget(self._lib_info_cards, 1)

    def _connect_widget_actions(self):
        for i in range(10):
            self._lib_info_cards.add_card(
                f'lib_status_{i}',
                '12313e12312123123123',
                i % 2 == 0
            )
