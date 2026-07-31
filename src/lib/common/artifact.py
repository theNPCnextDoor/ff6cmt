from abc import ABC, abstractmethod
from typing import Self


class Artifact(ABC):
    """
    An Artifact represents anything in a script that is used to facilitate scripting as they don't correspond to actual
    code in the ROM.
    """

    def __len__(self):
        """
        :return: 0 as it does not correspond to actual bytes in the ROM.
        """
        return 0

    def __bool__(self):
        """
        :note: When __len__() returns 0, bool(object) returns False, unless we force __bool__() to return True.
        :return: True
        """
        return True

    @classmethod
    @abstractmethod
    def from_line(cls, *args, **kwargs) -> Self:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def to_line(self, *args, **kwargs) -> str:
        pass
