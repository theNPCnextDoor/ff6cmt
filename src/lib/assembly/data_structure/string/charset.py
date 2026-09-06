import logging
import re

from src.lib.assembly.bytes import Bytes
from src.lib.misc.exception import NoCandidateException


class Charset:
    """
    Charsets are sets of characters used throughout the game. Each character corresponds to either one or two bytes and
    are represented by either a single character, two characters, a new-line character or an expression written inside
    '<>'. When a byte value does not correspond to anything is the charset, it is represented by its hexadecimal value
    inside '<>', e.g. <0x01>.
    """
    ARGUMENT_REGEX = r"(<[^:]+: )(?P<argument>[0-9A-F]{2})>"

    def __init__(self, charset: dict[str, int | dict[str, str | int | bool]]):
        self.chars: dict = charset["values"]
        self.max_length: int = charset.get("max_length", 1)
        self.regex = self._create_regex()

    def _create_regex(self):
        chars = [v["string"] for k, v in self.chars.items() if v.get("argument", False)]
        for i in range(self.max_length, 0, -1):
            chars += [v["string"] for k, v in self.chars.items() if v.get("length", 1) == i and not v.get("argument", False)]

        chars = [re.escape(char) for char in chars]
        chars = [re.sub(r"(<[^:]+:\\ )_>", r"\1[0-9A-F]{2}>", char) for char in chars]
        chars.append("<0x[0-9A-F]{2}>")

        return f"({'|'.join(chars)})"

    def get_char(self, value: int) -> dict[str, str | int]:
        """
        Returns the string associated with the byte value.
        :param value: The byte value, as an integer.
        :return: A string.
        """
        return {**self.chars.get(value, {"string": f"<0x{Bytes.from_int(value)}>"})}


    def get_value(self, value: str) -> int:
        """
        Extracts the hexadecimal value of an unrecognized character and returns it as an integer.
        :param value: An unrecognized character of the form '<0x??>'.
        :return: The integer corresponding to the hexadecimal value.
        :raises NoCandidateException: Raised when the character can't be found in the charset.
        """
        string_byte_regex = r"<0x(?P<byte>[0-9A-F]{2})>"
        if match := re.fullmatch(string_byte_regex, value):
            return int(Bytes.from_str((match.group("byte"))))

        candidates = [k for k, v in self.chars.items() if v["string"] == value]
        if len(candidates) == 0:
            message = f"No candidate has been found for char '{value}'."
            logging.error(message)
            raise NoCandidateException(message)

        return candidates[0]

    def get_bytes(self, value: str) -> bytes:
        """
        Extracts the hexadecimal value of an unrecognized character and returns it as bytes.
        :param value: An unrecognized character of the form '<0x??>'.
        :return: The bytes corresponding to the hexadecimal value.
        """
        argument = None
        if match := re.match(self.ARGUMENT_REGEX, value):
            argument = bytes(Bytes.from_str(match.group("argument")))
            value = re.sub(self.ARGUMENT_REGEX, r"\1_>", value)
        output = self.get_value(value=value).to_bytes()
        if argument:
            output += argument
        return output
