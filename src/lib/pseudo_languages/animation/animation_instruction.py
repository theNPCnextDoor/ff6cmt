import logging
from typing import Self

from src.lib.assembly.artifact.variable import Label
from src.lib.assembly.artifact.variables import Variables
from src.lib.common.data_structure import DataStructure
from src.lib.common.operand import Operand, OperandType
from src.lib.common.bytes import Bytes, Endian
from src.lib.pseudo_languages.animation.animation_info import AnimationInfo, AnimationCommandType, AnimationCommand
from src.lib.misc.exception import OperandLengthException


class AnimationInstruction(DataStructure):
    INFO = AnimationInfo()

    def __init__(self, command: AnimationCommand, operands: list[Operand] | None = None, depth: int = 0):
        self.command = command
        self.operands = operands or list()
        self.depth = depth

    @classmethod
    def from_line(
        cls,
        command: str,
        operands: str,
        address: Bytes | None = None,
        threads: int = 0,
        depth: int = 0,
        variables: Variables | None = None,
    ) -> Self:
        variables = variables or Variables()
        address = address or Bytes.from_address(0)
        command = cls.INFO.find_from_name(command)
        operand_type = OperandType.JUMPING if command.type == AnimationCommandType.JUMPING else OperandType.DEFAULT
        if operands:
            operands = [
                Operand.from_line(operand, parent_address=address, operand_type=operand_type, variables=variables)
                for operand in operands.split(" ")
            ]
        else:
            operands = None

        actual_length = sum([len(operand) for operand in operands]) if operands else 0
        expected_length = command.length if command.length != "variable" else threads * 2

        if actual_length != expected_length:
            message = f"Length of animation instruction {command} is {actual_length}. Expected: {expected_length}."
            logging.error(message)
            raise OperandLengthException(message)

        return AnimationInstruction(command=command, operands=operands)

    @classmethod
    def from_bytes(
        cls,
        value: bytes,
        threads: int = 0,
        depth: int = 0,
        address: Bytes | None = None,
        variables: Variables | None = None,
    ) -> Self:
        opcode = Bytes.from_bytes(value, endian=Endian.BIG)
        command = cls.INFO.find_from_opcode(int(opcode[0:1]))
        if command.has_subcommands:
            command = cls.INFO.find_from_opcode(int(opcode[0:2]))
            remaining_value = value[2:]
        else:
            remaining_value = value[1:]
        length = command.length if command.length != "variable" else threads * 2

        instruction = AnimationInstruction(command=command, depth=depth)

        if command.type == AnimationCommandType.JUMPING:
            for i in range(length // 2):
                instruction.operands.append(
                    Operand.from_bytes(
                        value=remaining_value[i * 2 : i * 2 + 2],
                        parent_address=address,
                        operand_type=OperandType.JUMPING,
                        variables=variables,
                    )
                )
        else:
            for i in range(length):
                instruction.operands.append(Operand.from_bytes(value=remaining_value[i : i + 1]))

        return instruction

    def __str__(self) -> str:
        output = " ".join([str(operand) for operand in self.operands])
        return f"{self.command.name} {output}".strip()

    def to_line(self, *args, **kwargs) -> str:
        return f"{' ' * self.depth * 2}  {str(self)}"

    def __bytes__(self) -> bytes:
        output = b"".join([bytes(operand) for operand in self.operands])
        return bytes(self.command.opcode) + output

    def __repr__(self) -> str:
        return f"AnimationInstruction(command={repr(self.command)}, operands={self.operands}, depth={self.depth})"

    def __eq__(self, other: Self) -> bool:
        return self.command == other.command and self.operands == other.operands and self.depth == other.depth

    def __len__(self) -> int:
        return len(self.command.opcode) + sum([len(operand) for operand in self.operands])

    @property
    def labels(self) -> list[Label]:
        output = list()
        if self.command.type == AnimationCommandType.JUMPING:
            for operand in self.operands:
                output.append(operand.variable)
        return output

    @classmethod
    def find_length(cls, command: str, threads: int) -> int:
        command = cls.INFO.find_from_name(command)
        if command.length == "variable":
            return len(command.opcode) + 2 * threads
        return len(command.opcode) + command.length
