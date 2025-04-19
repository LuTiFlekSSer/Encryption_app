class WidgetContainer:
    def __init__(self, parent):
        from src.frontend.settings_window.settings_window import SettingsWindow
        self.parent: SettingsWindow = parent
