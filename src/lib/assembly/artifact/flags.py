import logging
from typing import Self, Any

from src.lib.common.artifact import Artifact


class RegisterWidth:
    INVALID = 0
    EIGHT_BITS = 8
    SIXTEEN_BITS = 16


class Flags(Artifact):
    """
    In 65C816 processors, there are exactly two flags which deal with the width of registers, m and x. m deals with the
    width of the accumulator and x with the width of the X and Y indexes. Because of that, we need to take their state
    into account. In a script, they can be set directly, either at the beginning of it or when there is a jump in the
    code and both sections have a different state for either flag. Alternatively, they can be set with the instructions
    SEP and REP, where m is the 0x10 bit and x is the 0x20 one.
    """

    def __init__(self, m: int = RegisterWidth.SIXTEEN_BITS, x: int = RegisterWidth.SIXTEEN_BITS):
        self.m = m
        self.x = x

    @classmethod
    def from_line(cls, m_flag: str, x_flag: str) -> Self:
        """
        Takes a string that matches ArtifactRegex.FLAGS and will return a Flags object. It will consider either "8" or
        "true" for True and "16" or "false" for False.
        :param m_flag: Width of the accumulator. Either '8' or '16'.
        :param x_flag: Width of the X and Y registers. Either '8' or '16'.
        :return: A Flags object.
        :note: The reason that 8 and 16 are used is that it is more readable to see the width in bits of the accumulator
         and the indexes than having to convert the bool into number of bits.
        """
        flags = cls(m=int(m_flag), x=int(x_flag))
        logging.debug(f"Created {repr(flags)}.")
        return flags

    @classmethod
    def copy(cls, flags: Self) -> Self:
        """
        Creates a deep copy of a Flags object.
        :param flags: The original Flags object.
        :return: The new Flags object.
        """
        return Flags(m=flags.m, x=flags.x)

    def __str__(self) -> str:
        m = str(self.m)
        x = str(self.x)
        return f"m = {m}, x = {x}"

    def __repr__(self) -> str:
        return f"Flags(m={self.m}, x={self.x})"

    def to_line(self, **kwargs: Any) -> str:
        """
        Converts Flags into a script line.
        :param kwargs: Unused. Included to prevent errors.
        :return: A script line.
        """
        return str(self)

    def __eq__(self, other: Self) -> bool:
        return self.m == other.m and self.x == other.x

    def is_invalid(self) -> bool:
        return self.m == RegisterWidth.INVALID or self.x == RegisterWidth.INVALID
