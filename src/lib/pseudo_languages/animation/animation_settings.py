import logging
from typing import Self

from src.lib.assembly.artifact.variables import Variables
from src.lib.common.data_structure import DataStructure
from src.lib.common.operand import Operand
from src.lib.misc.exception import OperandLengthException


class AnimationSettings(DataStructure):

    def __init__(self, speed: Operand, alignment: Operand):
        self.speed = speed
        self.alignment = alignment

    @classmethod
    def from_line(cls, speed: str, alignment: str, variables: Variables | None = None) -> Self:
        variables = variables or Variables()
        speed = Operand.from_line(value=speed, variables=variables)
        alignment = Operand.from_line(value=alignment, variables=variables)
        if len(speed) != 1 or len(alignment) != 1:
            message = (
                "Improper length for AnimationSetting. Both speed and alignment are one byte. "
                f"Length of speed: {len(speed)}."
                f"Length of alignment: {len(alignment)}."
            )
            logging.error(message)
            raise OperandLengthException(message)
        return AnimationSettings(speed, alignment)

    @classmethod
    def from_bytes(cls, value: bytes) -> Self:
        speed = Operand.from_bytes(value[0:1])
        alignment = Operand.from_bytes(value[1:2])
        return AnimationSettings(speed, alignment)

    def to_line(self, *args, **kwargs) -> str:
        return str(self)

    def __bytes__(self):
        return bytes(self.speed) + bytes(self.alignment)

    def __len__(self):
        return 2

    def __str__(self) -> str:
        return f"anim_settings: {self.speed}, {self.alignment}"

    def __repr__(self) -> str:
        fields = dict()
        fields["speed"] = f"0x{self.speed.value}"
        fields["alignment"] = f"0x{self.alignment.value}"
        if self.speed.variable:
            fields["speed_variable"] = repr(self.speed.variable)
        if self.alignment.variable:
            fields["alignment_variable"] = repr(self.alignment.variable)
        output = ", ".join([f"{k}={v}" for k, v in fields.items()])
        return f"AnimationSetting({output})"

    def find_length(self, *args, **kwargs) -> int:
        return 2

    def __eq__(self, other: Self) -> bool:
        return self.speed == other.speed and self.alignment == other.alignment
