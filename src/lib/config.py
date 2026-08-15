import json
from enum import StrEnum, auto
from pathlib import Path

from src import ROOT_FOLDER


class ConfigEnum(StrEnum):
    INSTRUCTIONS_65C816: str = auto()
    ANIMATIONS: str = auto()
    ENEMY_AI: str = auto()
    BATTLE_EVENTS: str = auto()
    FIELD_EVENTS: str = auto()
    MENU_DTE: str = auto()
    DESCRIPTION_DTE: str = auto()
    DIALOG_DTE: str = auto()
    CREDITS_DTE: str = auto()


class Config:
    def __init__(self, configs: dict):
        for config_name in ConfigEnum:
            if configs.get(config_name, None):
                path = Path(configs[config_name])
            else:
                path = ROOT_FOLDER / "resources" / f"{config_name}.json"
            with open(path) as f:
                elements = {int(k, 16): v for k, v in json.load(f).items()}
                setattr(self, config_name, elements)


if __name__ == "__main__":
    Config(dict())
