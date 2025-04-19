class WidgetContainer:
    def __init__(self, parent):
        from src.frontend.home_window.home_window import HomeWindow
        self.parent: HomeWindow = parent
