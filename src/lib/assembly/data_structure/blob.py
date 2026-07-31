from __future__ import annotations

import logging
from typing import Self, Any

from src.lib.assembly.artifact.variables import Variables
from src.lib.common.operand import Operand, OperandType
from src.lib.common.data_structure import DataStructure
from src.lib.common.bytes import Bytes
from src.lib.misc.exception import DelimiterLengthError


class Blob(DataStructure):
    """
    Blobs are segments in a script where bytes are written as is. They may contain a delimiter so that the game knows
    when the Blob ends.
    """

    def __init__(self, operand: Operand, delimiter: Operand | None = None):
        self.operand = operand
        self.delimiter = delimiter

    @classmethod
    def from_line(
        cls,
        operand: str,
        delimiter: str | None = None,
        address: Bytes | None = None,
        variables: Variables | None = None,
    ) -> Self:
        """
        Converts a script line into a Blob.
        :param operand: The actual blob part in the script line.
        :param delimiter: The part of the script line that defines the byte used to let the game know that the Blob
        ended.
        :param address: The address of the Blob.
        :param variables: The list of Variables. Both Constants and Labels can be used to define a Blob value, but only
        the former can be used for the delimiter.
        :return: A Blob.
        :raised DelimiterLengthError: Raised when the length of the delimiter is not 1.
        """
        _operand = Operand.from_line(operand, address, OperandType.DEFAULT, variables)
        _delimiter = (
            Operand.from_line(delimiter, address, OperandType.DEFAULT, variables.constants) if delimiter else None
        )

        if _delimiter and len(_delimiter) != 1:
            message = f"Delimiter '{str(delimiter)}' must have a length of one."
            logging.error(message)
            raise DelimiterLengthError(message)

        blob = cls(operand=_operand, delimiter=_delimiter)
        logging.debug(f"Created {repr(blob)}.")
        return blob

    @classmethod
    def from_bytes(cls, data: bytes, delimiter: bytes | None = None) -> Self:
        """
        Converts bytes into a Blob.
        :param data: The bytes defining the Blob.
        :param delimiter: The byte used to determine the end of the Blob.
        :return: A Blob.
        """
        data = Operand(Bytes.from_bytes(data))
        if delimiter is not None:
            delimiter = Operand(Bytes.from_bytes(delimiter))

        blob = Blob(operand=data, delimiter=delimiter)
        logging.debug(f"Created {repr(blob)}.")
        return blob

    def __str__(self) -> str:
        output = f"{self.operand}"
        if self.delimiter is not None:
            output += f",{self.delimiter}"
        return output

    def __repr__(self) -> str:
        hexa = str(self.operand.value) + (str(self.delimiter.value) if self.delimiter else "")
        output = f"Blob(as_str='{str(self)}', as_bytes={bytes(self)}, as_hexa=0x{hexa}"
        if self.operand.variable:
            output += f", operand_var={repr(self.operand.variable)}"
        if self.delimiter and self.delimiter.variable:
            output += f", delimiter_var={repr(self.delimiter.variable)}"
        output += ")"
        return output

    def to_line(self, show_address: bool = False, address: Bytes | None = None, **kwargs: Any) -> str:
        """
        Converts a Blob into a script line.
        :param show_address: Whether the address of the Blob will be added.
        :param address: The address of the Blob.
        :param kwargs: Unused. Added to prevent errors.
        :return: A script line.
        """
        output = f"  {self}"
        if show_address:
            output += f" ; ${address}"
        return output

    def __len__(self) -> int:
        output = len(self.operand)
        output += 1 if self.delimiter is not None else 0
        return output

    def __bytes__(self) -> bytes:
        output = bytes(self.operand)
        if self.delimiter is not None:
            output += bytes(self.delimiter)
        return output

    def __eq__(self, other: Self) -> bool:
        return self.operand == other.operand and self.delimiter == other.delimiter

    @classmethod
    def find_length(cls, operand: str, variables: Variables, delimiter: str | None = None) -> int:
        """
        Determines the length of the script line during the pre-parsing phase.
        :param operand: The actual Blob part of the script line. When represented by a Variable with no prefix, an
        attempt is made to find the variable. If not found, it is believed that the variable is a Label that has yet to
        be defined and therefore will be considered having a length of 3. If the variable doesn't exist, an error will
        be generated at a later point in the execution of the code.
        :param variables: The list of variables.
        :param delimiter: The delimiter part of the script line, if it exists. Adds one to the length.
        :return: The length of the Blob.
        """
        length = 1 if delimiter else 0
        if "$" in operand:
            length += len(operand) // 2
        elif "." in operand:
            length += 1
        elif "!" in operand:
            length += 2
        elif variable := variables.find_by_name(operand):
            length += len(variable.value)
        else:
            length += 3
            logging.warning(f"Can't find variable named '{operand}'. Assuming it is a label yet to be declared.")

        logging.debug(f"Blob '{operand}{',' + delimiter if delimiter else ''}' length is {length}.")
        return length
