import os.path
from enum import Enum

from qfluentwidgets import FluentIconBase, Theme, getIconColor


class CustomIcons(FluentIconBase, Enum):
    LOCK = 'lock'
    UNLOCK = 'unlock'
    KEY = 'key'
    PASSWORD = 'password'

    def path(self, theme=Theme.AUTO):
        if os.path.exists((themed_path := f'res/{self.value}_{getIconColor(theme)}.svg')):
            return themed_path

        return f'res/{self.value}.svg'
