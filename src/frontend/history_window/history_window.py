from PyQt5.QtWidgets import QFrame

from src.frontend.history_window.widget_container import WidgetContainer


class HistoryWindow(QFrame):
    def __init__(self, name: str, parent=None):
        super().__init__(parent)

        self.wdg: WidgetContainer = WidgetContainer(self)

        self.setObjectName(name.replace(' ', '-'))

        self._connect_widget_actions()

    def _connect_widget_actions(self):
        pass
