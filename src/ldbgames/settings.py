import configparser
from ldbgames import LOCAL_DIR
import os
from pathlib import Path

class DynamicSettings:
    def __init__(self, section, name, getter, default_value, reload):
        self.section = section
        self.name = name
        self.getter = getter
        self.default_value = default_value
        self.reload = reload
        self.value = default_value


SETTINGS_FILE = LOCAL_DIR / "settings.ini"

dynamic_settings = []


def register_setting(section, name, getter, default_value, reload):
    setting = DynamicSettings(section, name, getter, default_value, reload)
    dynamic_settings.append(setting)
    return setting


def get_default_config():
    default_config = configparser.ConfigParser()

    for setting in dynamic_settings:
        if setting.section not in default_config:
            default_config[setting.section] = {}
        default_config[setting.section][setting.name] = str(setting.default_value)

    return default_config


def can_save_settings():
    if not SETTINGS_FILE.exists():
        return True
    with open(SETTINGS_FILE, "r") as f:
        return f.writable()


def save_settings():
    if can_save_settings():
        with open(SETTINGS_FILE, "w") as f:
            settings.write(f)
    else:
        raise PermissionError("Cannot write to settings file.")


def load_settings():
    if not SETTINGS_FILE.exists():
        save_settings()
    else:
        settings.read(SETTINGS_FILE)

    for setting in dynamic_settings:
        setting.value = setting.getter(settings[setting.section][setting.name])
        setting.reload(setting.value)


# Sections
GENERAL_SECTION = "GENERAL"


# Settings
SERVER_URL = register_setting(
    section=GENERAL_SECTION,
    name="ServerUrl",
    getter=lambda value: value,
    default_value="http://ldbgames.com",
    reload=lambda value: None
)

GAMES_DIR = register_setting(
    section=GENERAL_SECTION,
    name="GamesDir",
    getter=lambda value: Path(value),
    default_value=LOCAL_DIR / "games",
    reload=lambda value: os.makedirs(value, exist_ok=True)
)

settings = configparser.ConfigParser()
settings.read_dict(get_default_config())