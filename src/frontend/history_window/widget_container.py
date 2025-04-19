class WidgetContainer:
    def __init__(self, parent):
        from src.frontend.history_window.history_window import HistoryWindow
        self.parent: HistoryWindow = parent
