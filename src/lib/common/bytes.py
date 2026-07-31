from __future__ import annotations

import logging
from enum import Enum, auto
from typing import Self

from src.lib.misc.exception import UnderflowError


class Endian(Enum):
    LITTLE: bool = auto()
    BIG: bool = auto()


class Bytes:
    """
    This class is, at its base, a list of integers between 0 and 255 to act as bytes. The list is always in big endian,
    although the object itself might be in whatever endianness. Deciding upon the endianness only has an impact when we
    convert the object back to a bytes array.
    """

    def __init__(self, value: list[int], endian: Endian = Endian.LITTLE, length: int | None = None):
        """
        :param value: The list of integers representing a bytes array.
        :param endian: The endianness of the Bytes object.
        :param length: Used to give a specific length to the value.
        :raises ValueError: Raised when the value passed is not a list of integers.
        """

        if not isinstance(value, list):
            message = f"Type of value must be list[int]. Actual type: {type(value)}"
            logging.error(message)
            raise ValueError(message)
        self.endian = endian
        self.value = value
        if length:
            self._adjust(length=length)

    def _adjust(self, length: int) -> None:
        """
        Adjusts the length of the value.
        :param length: If longer than the length of the value, 0s will be prepended to the value.
         If shorter, the first few elements of the value will be removed.
        :return: Nothing.
        """
        if len(self.value) < length:
            self.value = [0] * (length - len(self.value)) + self.value
        else:
            self.value = self.value[-length:]

    @classmethod
    def from_int(cls, value: int, length: int | None = None, endian: Endian = Endian.LITTLE) -> Self:
        """
        Converts an integer into a Bytes object.
        :param value: An integer.
        :param length: When set, the value will be adjusted via adjust().
        :return: A Bytes object.
        """
        remainder = value
        _list = list()
        if remainder == 0:
            _list = [0]

        while remainder > 0:
            next_byte = remainder % 256
            _list.insert(0, next_byte)
            remainder //= 256

        return cls(value=_list, length=length, endian=endian)

    @classmethod
    def from_address(cls, value: int) -> Self:
        """
        Converts an integer address into a Bytes object.
        :param value: An integer between 0 and 2 ** 24 - 1.
        :return: A Bytes object with a length of 3.
        """
        return cls.from_int(value=value, length=3)

    @classmethod
    def from_str(cls, value: str, endian: Endian = Endian.LITTLE) -> Self:
        """
        Converts a hexadecimal representation of bytes into a Bytes object. The representation is always considered to
         be in big endian, although the Bytes object itself can be in whatever endianness.
        :param value: The hexadecimal representation of bytes.
        :param endian: The endianness to be considered when converting the Bytes object to a bytes array.
        :return: A Bytes object.
        :raises ValueError: Raised when the value is an empty string or isn't a pair number of characters.
        """
        if len(value) % 2 != 0 or not value:
            message = f"Value '{value}' must be a non-empty string with an even number of characters."
            logging.error(message)
            raise ValueError(message)

        _list = list()
        for i in range(len(value) // 2):
            _hex = value[i * 2 : i * 2 + 2]
            _list.append(int(f"0x{_hex}", 16))
        return cls(value=_list, endian=endian)

    @classmethod
    def from_bytes(cls, value: bytes, endian: Endian = Endian.LITTLE) -> Self:
        """
        Converts bytes into a Bytes object.
        :param value: A bytes array.
        :param endian: The endianness of the bytes array being passed.
        :return: A Bytes object.
        """
        if len(value) == 0:
            message = f"Value '{value}' must be a non-empty bytes object."
            logging.error(message)
            raise ValueError(message)
        _list = list()

        for _byte in value:
            if endian == Endian.BIG:
                _list.append(int(_byte))
            else:
                _list.insert(0, int(_byte))
        return cls(value=_list, endian=endian)

    @classmethod
    def from_other(cls, other: Bytes, length: int | None = None) -> Self:
        """
        Converts a Bytes object into another Bytes object. To be used mostly when we want to copy a Bytes object while
         also changing the length.
        :param other: Another Bytes object.
        :param length: When set, the value will be adjusted via adjust().
        :return: A Bytes object.
        """
        instance = cls(value=other.value)
        if length:
            instance._adjust(length=length)
        return instance

    def __int__(self) -> int:
        """
        :return: An integer considering the order of the elements of the list in the value where the first element is
         the most significant byte. In other words, it converts the value in big endian.
        """
        output = 0
        value = self.value
        for n in value:
            output *= 0x0100
            output += n
        return output

    def __str__(self) -> str:
        """
        :return: A big endian hexadecimal representation of its value.
        """
        output = ""
        for n in self.value:
            output += n.to_bytes(length=1, byteorder="big").hex()
        return output.upper()

    def __repr__(self) -> str:
        """
        :return: A detailed representation of itself to facilitate debugging.
        """
        return (
            f"Bytes(value={self.value}, as_decimal={int(self)}, "
            f"as_hexa=0x{self}, as_bytes={bytes(self)}, endian={self.endian})"
        )

    def __bytes__(self) -> bytes:
        """
        Converts a Bytes object into a bytes array considering its endianness.
        :return: A bytes array.
        """
        output = b""
        for n in self.value:
            output += n.to_bytes(length=1, byteorder="big")
        if self.endian == Endian.LITTLE:
            output = output[::-1]
        return output

    def __len__(self) -> int:
        """
        :return: The number of elements in the value.
        """
        return len(self.value)

    def __eq__(self, other: Self) -> bool:
        """
        :param other: A Bytes object.
        :return: Whether the value of both objects are equal.
        :raises ValueError: Raised when the other object is not a Bytes object.
        """
        if other is None:
            return False

        if not isinstance(other, type(self)):
            message = f"Can't only compare two Bytes together. {other=}"
            logging.error(message)
            raise ValueError(message)

        return self.value == other.value

    def __lt__(self, other) -> bool:
        """
        :param other: A Bytes object.
        :return:  Whether the integer representation of the object is less than the other.
        :raises ValueError: Raised when the other object is not a Bytes object.
        """
        if not isinstance(other, type(self)):
            message = f"Can't only compare two Bytes together. {other=}"
            logging.error(message)
            raise ValueError(message)

        return int(self) < int(other)

    def __getitem__(self, item: slice) -> Self:
        """
        Creates a new Bytes object out of the sliced value of the original object.
        :param item: A slice object
        :return: A Bytes object.
        """
        new_value = self.value[item]
        new_value = new_value if isinstance(new_value, list) else [new_value]
        return type(self)(value=new_value, endian=self.endian)

    def __add__(self, other: Self | int) -> Self:
        """
        Adds the integer representation of the objects and create a new Bytes object out of the sum.
        :param other: A Bytes object or an integer.
        :return: A Bytes object.
        :raises OverflowError: Raised when the sum exceeds maximum allowed value by the length of the left object.
        """
        _sum = int(self) + int(other)
        if _sum > 2 ** (8 * len(self.value)) - 1:
            message = f"Overflow when adding {self} and {other}."
            logging.error(message)
            raise OverflowError(message)

        instance = type(self).from_int(_sum)
        instance.endian = self.endian
        return instance

    def __sub__(self, other: Self | int) -> Self:
        """
        Subtracts the integer representation of the objects and create a new Bytes object out of the difference.
        :param other: A Bytes object or an integer.
        :return: A Bytes object.
        :raises UnderflowError: Raised when the difference is below 0.
        """
        difference = int(self) - int(other)
        if difference < 0:
            message = f"Underflow when subtracting {other} from {self}."
            logging.error(message)
            raise UnderflowError(message)

        instance = type(self).from_int(difference)
        instance.endian = self.endian
        return instance

    def bank(self) -> int:
        """
        :return: An integer representing the value of the most significant byte of an address.
        :raises AttributeError: Raised when the Bytes object length is not 3.
        """
        if len(self) != 3:
            message = f"Can't get the bank of a non-address Bytes object. Actual value: {repr(self)}"
            logging.error(message)
            raise AttributeError(message)

        return self.value[0] * 0x010000
