import logging
import re
from typing import Self, Any

from src.lib.assembly.data_structure.string.helpers import StringType, StringTypes, MENU_CHARSET
from src.lib.assembly.artifact.variables import Variables
from src.lib.assembly.data_structure.blob import Blob
from src.lib.assembly.data_structure.instruction.operand import Operand
from src.lib.assembly.bytes import Bytes, Endian
from src.lib.assembly.data_structure.regex import Regex

from src.lib.assembly.data_structure.string.charset import Charset
from src.lib.misc.exception import DelimiterLengthError


class String(Blob):
    def __init__(
        self,
        operand: Operand,
        delimiter: Operand | None = None,
        charset: Charset | None = None,
        string_type: StringType | None = None,
    ):
        super().__init__(operand=operand, delimiter=delimiter)
        self.charset = charset or Charset(charset=MENU_CHARSET)
        self.string_type = string_type or StringTypes.MENU

    @classmethod
    def from_line(
        cls,
        string: str,
        string_type: str | None = None,
        delimiter: str | None = None,
        address: Bytes | None = None,
        variables: Variables | None = None,
    ) -> Self:
        """
        Converts a script line into a String.
        :param string: The actual string part of the line.
        :param string_type: The StringType of the line to determine how to convert the String into bytes.
        :param delimiter: The byte that helps determine where the String ends in-game.
        :param address: The address of the String.
        :param variables: The list of Variables used to determine the value of the delimiter, if needed.
        :return: A String.
        :raises DelimiterLengthError: Raised when there is a variable delimiter, but the variable doesn't have a length of 1.
        """
        _string_type = StringTypes.get_by_prefix(string_type)
        chars = re.findall(_string_type.charset.regex, string)
        data = b""

        constants = variables.constants if variables else None

        _delimiter = (
            Operand.from_line(value=delimiter, variables=constants, parent_address=address) if delimiter else None
        )

        if _delimiter and len(_delimiter) != 1:
            message = f"Delimiter '{str(delimiter)}' must have a length of one."
            logging.error(message)
            raise DelimiterLengthError(message)

        for char in chars:
            data += _string_type.charset.get_bytes(char)
        data_bytes = Operand(Bytes.from_bytes(value=data, endian=Endian.BIG))

        string = cls(operand=data_bytes, delimiter=_delimiter, string_type=_string_type)
        logging.debug(f"Created {repr(string)}.")
        return string

    @classmethod
    def from_bytes(
        cls,
        data: bytes,
        delimiter: bytes | None = None,
        string_type: StringType | None = None,
    ) -> Self:
        """
        Converts bytes into a String.
        :param data: The bytes to be converted.
        :param delimiter: The byte that helps determine where the String ends in-game.
        :param string_type: The StringType of the line to determine how to convert the bytes into a String.
        :return: A String.
        """
        data = Operand(Bytes.from_bytes(value=data, endian=Endian.BIG))
        if delimiter is not None:
            delimiter = Operand(Bytes.from_bytes(value=delimiter))

        string = String(operand=data, delimiter=delimiter, string_type=string_type)
        logging.debug(f"Created {repr(string)}.")
        return string

    def __str__(self) -> str:
        output = ""

        if self.string_type and self.string_type.prefix:
            output = f"{self.string_type.prefix} "

        output += '"'

        i = 0
        while i < len(self.operand.value):
            value = self.operand.value[i: i+1]
            i += 1
            char = self.string_type.charset.get_char(value=int(value))
            if char.get("argument", False):
                argument = self.operand.value[i: i + 1] if i < len(self.operand.value) else None
                i += 1
                char["string"] = char["string"].replace("_", str(argument))
            output += char["string"]

        output += '"'

        if self.delimiter is not None:
            output += f",{self.delimiter}"
        return output

    def __repr__(self) -> str:
        hexa = str(self.operand.value) + (str(self.delimiter.value) if self.delimiter is not None else "")
        output = f"String(as_str='{str(self)}', as_bytes={bytes(self)}, as_hexa=0x{hexa}"
        if self.delimiter is not None and self.delimiter.variable:
            output += f", delimiter_var={repr(self.delimiter.variable)}"
        output += ")"
        return output

    def __eq__(self, other: Self) -> bool:
        return self.operand == other.operand

    def to_line(self, show_address: bool = False, address: Bytes | None = None, **kwargs: Any) -> str:
        """
        Converts a String into a script line.
        :param show_address: Whether the address of the script line will be added as a comment.
        :param address: The address of the String.
        :param kwargs: Unused. Added to prevent errors.
        :return: A script line.
        """
        output = f"  {self}"
        if show_address:
            output += f" ; ${address}"
        return output

    @classmethod
    def find_length(cls, string: str, delimiter: str | None = None, prefix: str | None = None) -> int:
        """
        Determines the length of the script line in number of bytes during the pre-parsing phase.
        :param string: The actual string of the script line.
        :param delimiter: The delimiter part of the script line, if it exists. Adds one to the length.
        :return: The number of bytes contained in the String.
        """
        string_type = StringTypes.get_by_prefix(prefix)
        length = len(re.findall(string_type.charset.regex, string))
        if delimiter:
            length += 1

        logging.debug(f"String '{string}{',' + delimiter if delimiter else ''}' length is {length}.")
        return length
