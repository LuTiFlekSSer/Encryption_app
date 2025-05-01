from os import cpu_count

from qfluentwidgets import QConfig, ConfigItem, BoolValidator, OptionsConfigItem, OptionsValidator, RangeConfigItem, \
    RangeValidator

from src.backend.db.data_base import DataBase, TSettingName
from src.utils.singleton import Singleton


class QConfigMeta(type(QConfig), Singleton):
    pass


class CustomConfig(QConfig, metaclass=QConfigMeta):
    app_theme: OptionsConfigItem = OptionsConfigItem(
        'settings', 'theme', 0, OptionsValidator(['DARK', 'LIGHT', 'AUTO'])
    )
    app_language: OptionsConfigItem = OptionsConfigItem(
        'settings', 'language', 0, OptionsValidator(['ru', 'en'])
    )
    history_size: RangeConfigItem = RangeConfigItem(
        'settings', 'history_size', 0, RangeValidator(0, 99999)
    )
    encryption_threads: RangeConfigItem = RangeConfigItem(
        'settings', 'threads', 0, RangeValidator(1, cpu_count() * 2)
    )
    queue_width: RangeConfigItem = RangeConfigItem(
        'settings', 'queue_size', 0, RangeValidator(1, 999)
    )

    def __init__(self):
        super().__init__()
        self._db: DataBase = DataBase()

        items = {}
        for name in dir(self._cfg.__class__):
            item = getattr(self._cfg.__class__, name)
            if isinstance(item, ConfigItem):
                items[item.key] = item

        for setting_name in TSettingName.__args__:
            if (full_name := f'settings.{setting_name}') not in items:
                continue

            item: ConfigItem = items[full_name]
            if isinstance(item.validator, BoolValidator):
                item.deserializeFrom(self._db.get_setting(setting_name) == 'True')
            elif isinstance(item.validator, RangeValidator):
                item.deserializeFrom(int(self._db.get_setting(setting_name)))
            else:
                item.deserializeFrom(self._db.get_setting(setting_name))

    def save(self):
        cfg = self.toDict()
        settings_values: dict[TSettingName, str] = cfg['settings']

        for key, val in settings_values.items():
            self._db.set_setting(key, str(val))


custom_config = CustomConfig()
