import logging
from abc import ABC
from typing import Self, Any

from src.lib.common.artifact import Artifact
from src.lib.common.bytes import Bytes
from src.lib.misc.exception import ForbiddenVarName, IllegalConstantLength

VAR_LENGTH = {"b": 1, "w": 2}
FORBIDDEN_NAMES = ["desc", "let", "m", "map", "ptr", "rptr", "x"]


class Variable(Artifact, ABC):
    """
    Variables are Artifact in a script where a specific value is represented by a name.
    """

    def __init__(self, value: Bytes, name: str):
        self.value = value
        self.name = name

    def __str__(self):
        return self.name

    def __repr__(self):
        return f"{self.__class__.__name__}(name='{self.name}', value=0x{str(self.value)})"

    def __eq__(self, other: Self):
        if other is None:
            return False
        return self.value == other.value and self.name == other.name

    @staticmethod
    def is_name_forbidden(name: str) -> bool:
        return name in FORBIDDEN_NAMES


class Constant(Variable):
    """
    Used to store a value in order to raise readability and/or use it in multiple places at once.
    """

    @classmethod
    def from_line(cls, name: str, operand: str) -> Self:
        """
        Creates a Constant out of successful regex match.
        :param name: The name of the constant.
        :param operand: The value of the constant.
        :return: A Constant.
        :raises IllegalConstantLength: Raised when the expected length of the Constant is neither 1 nor 2.
        """
        if cls.is_name_forbidden(name):
            message = f"Variable name '{name}' is forbidden. All forbidden names: {FORBIDDEN_NAMES}"
            logging.error(message)
            raise ForbiddenVarName(message)

        _operand = Bytes.from_str(operand.replace("$", ""))

        if len(_operand) not in range(1, 3):
            message = f"Length of value '{operand}' must be 1 or 2."
            logging.error(message)
            raise IllegalConstantLength(message)

        constant = cls(_operand, name)
        logging.debug(f"Created {repr(constant)}.")
        return cls(_operand, name)

    def to_line(self, **kwargs: Any) -> str:
        """
        Converts a Constant into the exact string which will be put in a script to declare it.
        :return: A script line.
        """

        return f"let {self.name} = ${self.value}"


class Label(Constant):
    """
    A Label is a 24-bit Variable that is used to define an address in the ROM.
    """

    def __init__(self, value: Bytes, name: str | None = None):
        """
        :param value: The value, or the address, of the Label.
        :param name: The name of the Label.
        """
        name = (name or f"label_{str(value)}").lower()
        super().__init__(name=name, value=value)

    @classmethod
    def from_line(cls, name: str, snes_address: str | None = None, address: Bytes | None = None) -> Self:
        """
        Converts a string into a Label.
        :param name: The name of the Label.
        :param snes_address: The SNES address of the Label. When omitted, will use the current address in the script
        as the Label value.
        :param address: The current address of the Label in the script.
        :return: A Label.
        :raises ForbiddenVarName: Raised when we are trying to assign a forbidden name to a Variable.
        """
        if cls.is_name_forbidden(name):
            message = f"Variable name '{name}' is forbidden. All forbidden names: {FORBIDDEN_NAMES}"
            logging.error(message)
            raise ForbiddenVarName(message)

        address = Bytes.from_str(snes_address.replace("$", "")) if snes_address else address

        label = cls(value=address, name=name)
        logging.debug(f"Created {repr(label)}.")
        return label

    def to_line(self, show_address: bool = False, **kwargs: Any) -> str:
        """
        Converts a Label into the exact string which will be put in a script to declare it.
        :param show_address: Whether the address of the label should be added. Usually added when there is a skip
        happening in the script.
        :return: A script line.
        """
        output = ""
        if show_address:
            output += "\n"
        output += f"@{str(self)}"
        output += f" = ${self.value}" if show_address else ""
        return output
