from PyQt5.QtGui import QColor
from qfluentwidgets import MessageBoxBase, BodyLabel, SubtitleLabel

from src.utils.config import Config


class MessageBox(MessageBoxBase):
    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent=parent)
        self.widget.setMinimumWidth(480)

        self._l_title: SubtitleLabel = SubtitleLabel(title, self)
        self._l_description: BodyLabel = BodyLabel(description, self)

        self.__init_widgets()

    def __init_widgets(self):
        self._l_title.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))
        self._l_description.setTextColor(QColor(Config.GRAY_COLOR_900), QColor(Config.GRAY_COLOR_50))

        self.viewLayout.addWidget(self._l_title)
        self.viewLayout.addWidget(self._l_description)
