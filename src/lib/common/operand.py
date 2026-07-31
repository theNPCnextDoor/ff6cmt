import logging
import re
from dataclasses import dataclass
from enum import Enum, auto
from typing import Self

from src.lib.assembly.artifact.variable import Label, Variable
from src.lib.assembly.artifact.variables import Variables
from src.lib.common.bytes import Bytes
from src.lib.misc.exception import NoVariableException, ImpossibleDestination, UndefinedDestination


class OperandType(Enum):
    """
    The operand type is used to define how to convert the destination associated to the label (when there is one)
    to the value of the operand and vice versa.
    """

    DEFAULT = auto()
    JUMPING = auto()
    LONG_JUMPING = auto()
    BRANCHING = auto()
    LONG_BRANCHING = auto()


@dataclass(order=True)
class Operand:
    """
    The operand is the part of a data structure containing the data.
    :param value: A Bytes object containing the data.
    :param mode: Only used in instructions. The mode is used by the processor in order to understand how to interpret
    the data of the instruction.
    :param operand_type: The OperandType. It is used to understand how to convert the value into the destination of the
    label, when there is one.
    """

    value: Bytes
    mode: str = "_"
    operand_type: OperandType = OperandType.DEFAULT
    variable: Variable | None = None

    @classmethod
    def from_line(
        cls,
        value: str,
        parent_address: Bytes | None = None,
        operand_type: OperandType = OperandType.DEFAULT,
        variables: Variables | None = None,
    ) -> Self:
        """
        Converts a string into an operand.
        :param value: The string to convert. It can represent a hexadecimal value or a variable, both encapsulated in
        the operand mode.
        :param parent_address: The address of the instruction containing the operand.
        :param operand_type: The type of the operand.
        :param variables: A list of existing variables and labels.
        :return: An operand.
        :raises NoVariableException: Raised when no variable can be found with the given name.
        :raises ImpossibleDestination: Raised when the destination can't be reached from the parent address.
        """
        parent_address = parent_address or Bytes.from_address(0)
        variables = variables or Variables()
        mode = cls._to_mode(value, operand_type)
        stripped_value = re.sub(r"[$.!#()\[\],SXY]", "", value)
        match = re.findall(r"[$.!]", value)

        value_type = match[0] if match else None

        if value_type == "$":
            return cls(value=Bytes.from_str(stripped_value), mode=mode, operand_type=operand_type)

        variable = variables.find_by_name(stripped_value)

        if variable is None:
            message = f"Can't find variable named '{stripped_value}'."
            logging.error(message)
            raise NoVariableException(message)

        if not isinstance(variable, Label):
            return cls(value=variable.value, mode=mode, operand_type=operand_type, variable=variable)

        if value_type == ".":
            length = 1
        elif value_type == "!":
            length = 2
        else:
            length = 3

        destination = variable.value
        if (
            length != 1
            and operand_type != OperandType.DEFAULT
            and not cls._is_destination_possible(parent_address=parent_address, destination=destination, length=length)
        ):
            message = f"Destination {repr(destination)} impossible from parent address {repr(parent_address)}."
            logging.error(message)
            raise ImpossibleDestination(message)

        operand_value = cls._destination_to_value(
            parent_address=parent_address, operand_type=operand_type, length=length, destination=destination
        )

        operand = cls(value=operand_value, mode=mode, operand_type=operand_type, variable=variable)
        logging.debug(f"Created {repr(operand)}.")
        return operand

    @classmethod
    def from_bytes(
        cls,
        value: bytes,
        mode: str = "_",
        operand_type: OperandType = OperandType.DEFAULT,
        parent_address: Bytes = Bytes.from_address(0),
        variables: Variables | None = None,
    ) -> Self:
        """
        Converts bytes into an operand.
        :param value: A bytes array representing the data of the operand.
        :param mode: The mode is used by the processor in order to understand how to interpret the data of the
        instruction.
        :param operand_type: The type of the operand.
        :param parent_address: The address of the instruction containing the operand.
        :param variables: A list of existing variables and labels.
        :return: An operand.
        """
        variables = variables or Variables()
        value = Bytes.from_bytes(value)

        if operand_type == OperandType.DEFAULT and len(value) != 3:
            return cls(value=value, operand_type=operand_type, mode=mode)

        operand = cls(value=value, operand_type=operand_type, mode=mode)
        destination = operand.value_to_destination(parent_address=parent_address)

        operand.variable = variables.find_by_address(destination)
        if operand.variable is None:
            operand.variable = Label(destination)

        return operand

    @staticmethod
    def _to_mode(value: str, operand_type: OperandType) -> str:
        """
        Extracts the mode out of the operand string, except for branching and long branching operands, where it is fixed
        to "_".
        :param value: The operand string.
        :param operand_type: The operand type.
        :return: The mode.
        """
        if operand_type in (OperandType.BRANCHING, OperandType.LONG_BRANCHING):
            return "_"
        return re.sub(r"[$.!A-F0-9a-z_]+", "_", value)

    @staticmethod
    def _destination_to_value(
        parent_address: Bytes, operand_type: OperandType, length: int, destination: Bytes
    ) -> Bytes:
        """
        Converts the destination of the operand into its value.
        :param parent_address: The address of the DataStructure containing the Operand.
        :param operand_type: The type of operand in order to determine the calculation.
        :param length: The length of the operand.
        :param destination: The target address of the operand.
        :return: The value of the operand.
        """
        if operand_type == OperandType.BRANCHING:
            return Bytes.from_int((int(destination) - int(parent_address) - 2) % 0x0100)
        if operand_type == OperandType.LONG_BRANCHING:
            return Bytes.from_int(((int(destination) - int(parent_address) - 3) % 0x010000), length=2)
        if length == 1:
            return destination[0:1]

        if length == 2:
            return Bytes.from_other(destination, length=2)

        return Bytes.from_other(destination)

    def value_to_destination(self, parent_address: Bytes) -> Bytes:
        """
        Converts the value of the Operand into its destination.
        :param parent_address: The address of the DataStructure containing the Operand.
        :return: The destination of the Operand.
        :raises UndefinedDestination: Raised when the operand type is not branching or long branching and the length of
        the length is 1 because the exact destination can't be inferred.
        """
        if self.operand_type == OperandType.BRANCHING:
            return Bytes.from_address((int(self.value) + 0x80) % 0x0100 + int(parent_address) - 0x7E)
        if self.operand_type == OperandType.LONG_BRANCHING:
            return Bytes.from_address(
                int(parent_address.bank()) + (int(parent_address) + int(self.value) + 3) % 0x010000
            )

        if len(self) == 3:
            return self.value
        if len(self) == 2:
            bank = parent_address.bank()
            return Bytes.from_address(int(self.value) + bank)

        message = f"Can't find the destination. {repr(self)}, parent_address: {parent_address}"
        logging.error(message)
        raise UndefinedDestination(message)

    def __len__(self) -> int:
        return len(self.value)

    def __bytes__(self) -> bytes:
        value = self.value[:]
        return bytes(value)

    def __str__(self) -> str:
        if self.variable is None:
            value = self.value[:]
            if len(self.value) == 3 and 0 <= int(self.value) <= 0x3FFFFF:
                value += 0xC00000
            return self.mode.replace("_", f"${str(value)}")
        if (
            isinstance(self.variable, Label)
            and self.operand_type not in (OperandType.BRANCHING, OperandType.LONG_BRANCHING)
            and len(self.value) != 3
        ):
            prefix = "." if len(self.value) == 1 else "!"
            return self.mode.replace("_", f"{prefix}{self.variable.name}")
        return self.mode.replace("_", f"{self.variable.name}")

    def __repr__(self):
        output = f"Operand(value=0x{str(self.value)}, mode='{self.mode}', operand_type={self.operand_type}"
        if self.variable:
            output += f", variable={repr(self.variable)}"
        output += ")"
        return output

    @staticmethod
    def _is_destination_possible(parent_address: Bytes, length: int, destination: Bytes) -> bool:
        """
        Determines if the destination can be reached.
        If the length of the operand is 3, the instruction containing the operand can jump to anywhere in the code so
        it's always possible. If the length is 2, then the DataStructure containing the Operand must be in the same bank
        as the destination. This is the case for Pointers and some Instructions. In the length is 1, it is assumed in
        this function that the DataStructure containing the Operand is a branching Instruction. Therefore, it checks if
        the destination is in the immediate vicinity [-127, 129] of the Instruction.

        :param parent_address: The address of the DataStructure containing the Operand.
        :param length: The length of the Operand.
        :param destination: The destination of the Operand.
        :return: True is the destination is reachable.
        """
        if length == 3:
            return True
        if length == 2:
            return parent_address.bank() == destination.bank()
        return int(parent_address) - 0x7E <= int(destination) <= int(parent_address) + 0x81
