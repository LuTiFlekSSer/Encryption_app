from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import QVBoxLayout, QHBoxLayout, QWidget
from qfluentwidgets import InfoBarIcon, IconWidget, StrongBodyLabel, CaptionLabel, TitleLabel, FlowLayout, \
    SimpleCardWidget

from src.utils.config import Config


class LibInfoCard(SimpleCardWidget):
    def __init__(self,
                 title: str,
                 description: str,
                 status: bool,
                 parent=None):
        super().__init__(parent=parent)
        self.setFixedSize(280, 80)

        self._h_layout: QHBoxLayout = QHBoxLayout(self)
        self._h_layout.setContentsMargins(20, 12, 12, 12)
        self._h_layout.setSpacing(16)

        self._v_layout: QVBoxLayout = QVBoxLayout()
        self._v_layout.setContentsMargins(0, 0, 0, 0)
        self._v_layout.setSpacing(0)
        self._v_layout.setAlignment(Qt.AlignVCenter)

        self._iw_icon: IconWidget = IconWidget(self)
        self._iw_icon.setIcon(InfoBarIcon.SUCCESS if status else InfoBarIcon.ERROR)
        self._iw_icon.setFixedSize(32, 32)

        self._l_title: StrongBodyLabel = StrongBodyLabel(self)
        self._l_title.setText(title)
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._l_description: CaptionLabel = CaptionLabel(self)
        self._l_description.setText(description)
        self._l_description.setTextColor(QColor(Config.GRAY_COLOR_700), QColor(Config.GRAY_COLOR_200))

        self._h_layout.addWidget(self._iw_icon)
        self._h_layout.addLayout(self._v_layout)

        self._v_layout.addWidget(self._l_title)
        self._v_layout.addWidget(self._l_description)


class LibInfoCardView(QWidget):
    def __init__(self, title: str, parent=None):
        super().__init__(parent=parent)
        self._v_layout: QVBoxLayout = QVBoxLayout(self)
        self._v_layout.setContentsMargins(28, 0, 0, 0)
        self._v_layout.setSpacing(8)

        self._flow_layout: FlowLayout = FlowLayout()
        self._flow_layout.setContentsMargins(0, 0, 0, 0)
        self._flow_layout.setSpacing(16)

        self._l_title: TitleLabel = TitleLabel(self)
        self._l_title.setText(title)
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self._v_layout.addWidget(self._l_title)
        self._v_layout.addLayout(self._flow_layout, 1)

    def add_card(self, title: str, description: str, status: bool):
        card = LibInfoCard(title, description, status, self)
        self._flow_layout.addWidget(card)
