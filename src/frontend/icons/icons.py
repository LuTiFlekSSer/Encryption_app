from enum import Enum

from qfluentwidgets import FluentIconBase, Theme


class CustomIcons(FluentIconBase, Enum):
    LOCK = 'lock'
    UNLOCK = 'unlock'
    KEY = 'key'
    PASSWORD = 'password'

    def path(self, theme=Theme.AUTO):
        return f'res/{self.value}.svg'
