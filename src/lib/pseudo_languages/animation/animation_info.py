import json
import logging
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Self

from src import ROOT_FOLDER
from src.lib.common.bytes import Bytes, Endian
from src.lib.misc.exception import NoCandidateException, TooManyCandidatesException


class AnimationCommandType(StrEnum):
    DEFAULT = "default"
    JUMPING = "jumping"


@dataclass
class AnimationCommand:
    opcode: Bytes
    name: str
    length: int | str = 0
    type: AnimationCommandType = AnimationCommandType.DEFAULT
    has_subcommands: bool = False
    depth_modifier: int = 0
    is_ending: bool = False

    def __repr__(self) -> str:
        properties = [f"opcode={str(self.opcode)}", f"name='{self.name}'"]
        if self.length:
            properties.append("length=" + (str(self.length) if isinstance(self.length, int) else f"'{self.length}'"))
        if self.type != AnimationCommandType.DEFAULT:
            properties.append(f"type={self.type}")
        if self.has_subcommands:
            properties.append(f"has_subcommands={self.has_subcommands}")
        if self.depth_modifier:
            properties.append(f"depth_modifier={self.depth_modifier}")
        if self.is_ending:
            properties.append(f"is_ending={self.is_ending}")
        return f"AnimationCommand({', '.join(properties)})"

    def __eq__(self, other: Self) -> bool:
        return self.opcode == other.opcode


class AnimationInfo:

    def __init__(self, path: Path = ROOT_FOLDER / "resources" / "animations.json"):
        with open(path) as json_file:
            animations = json.load(json_file)
        self.info = list()
        for opcode, animation in animations.items():
            length = animation.get("length", 0)
            length = int(length) if length != "variable" else length
            self.info.append(
                AnimationCommand(
                    opcode=Bytes.from_int(int(opcode, base=16), endian=Endian.BIG),
                    name=animation.get("command", ""),
                    length=length,
                    has_subcommands=animation.get("has_subcommands", False),
                    type=AnimationCommandType(animation.get("type", "default")),
                    depth_modifier=int(animation.get("depth_modifier", 0)),
                    is_ending=animation.get("ending"),
                )
            )

    def find_from_opcode(self, opcode: int) -> AnimationCommand:
        candidates = [animation for animation in self.info if opcode == int(animation.opcode)]
        if len(candidates) == 0:
            message = f"No candidate was found for animation instruction with opcode 0x{str(Bytes.from_int(opcode))}."
            logging.error(message)
            raise NoCandidateException(message)
        return candidates[0]

    def find_from_name(self, name: str) -> AnimationCommand:
        candidates = [animation for animation in self.info if name == animation.name]
        if len(candidates) == 0:
            message = f"No candidate was found for animation instruction '{name}'."
            logging.error(message)
            raise NoCandidateException(message)
        elif len(candidates) > 1:
            message = (
                f"Found {len(candidates)} animation instruction candidates with name '{name}'. "
                "Command names must be unique."
            )
            logging.error(message)
            raise TooManyCandidatesException(message)
        return candidates[0]
