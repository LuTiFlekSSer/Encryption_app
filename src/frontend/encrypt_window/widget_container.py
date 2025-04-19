class WidgetContainer:
    def __init__(self, parent):
        from src.frontend.encrypt_window.encrypt_window import EncryptWindow
        self.parent: EncryptWindow = parent
