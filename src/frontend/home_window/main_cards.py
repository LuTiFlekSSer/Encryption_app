from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QWheelEvent
from PyQt5.QtWidgets import QVBoxLayout, QWidget, QHBoxLayout, QSizePolicy
from qfluentwidgets import CardWidget, FluentIcon, IconWidget, CaptionLabel, SingleDirectionScrollArea, \
    SubtitleLabel

from src.utils.config import Config


class MainCard(CardWidget):
    def __init__(self,
                 title: str,
                 description: str,
                 icon: FluentIcon,
                 link_icon: bool = False,
                 callback: callable = None,
                 parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(180, 240)

        self._layout: QVBoxLayout = QVBoxLayout(self)
        self._layout.setContentsMargins(24, 24, 32, 24)
        self._layout.setSpacing(0)
        self._layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)

        self._iw_icon: IconWidget = IconWidget(self)
        icon = icon.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._iw_icon.setIcon(icon)
        self._iw_icon.setFixedSize(48, 48)

        self._l_title: SubtitleLabel = SubtitleLabel(self)
        self._l_title.setText(title)
        self._l_title.setWordWrap(True)
        self._l_title.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._l_description: CaptionLabel = CaptionLabel(self)
        self._l_description.setText(description)
        self._l_description.setWordWrap(True)
        self._l_description.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        self._l_description.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))

        self._layout.addWidget(self._iw_icon)
        self._layout.addSpacing(12)

        self._layout.addWidget(self._l_title)
        self._layout.addSpacing(8)

        self._layout.addWidget(self._l_description)
        self._layout.addStretch()

        if link_icon:
            self._lw_link_icon: IconWidget = IconWidget(self)
            icon = FluentIcon.LINK.colored(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
            self._lw_link_icon.setIcon(icon)
            self._lw_link_icon.setFixedSize(16, 16)
            self._lw_link_icon.move(152, 212)

        self.clicked.connect(lambda: callback())


class MainCardView(SingleDirectionScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.Horizontal)
        self._w_view = QWidget(self)
        self._w_view.setObjectName('w_view')

        self._layout = QHBoxLayout(self._w_view)

        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(12)
        self._layout.setAlignment(Qt.AlignLeft)

        self.setWidget(self._w_view)
        self.setWidgetResizable(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

    def add_card(self,
                 icon: FluentIcon,
                 title: str,
                 description: str,
                 link_icon: bool = False,
                 callback: callable = None):
        card = MainCard(title, description, icon, link_icon, callback, self)
        self._layout.addWidget(card, 0, Qt.AlignLeft)

    def wheelEvent(self, e: QWheelEvent):
        if self.horizontalScrollBar().maximum() == 0:
            e.ignore()
        else:
            super().wheelEvent(e)
