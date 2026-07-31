from __future__ import annotations
from typing import Self

from abc import ABC, abstractmethod


class DataStructure(ABC):
    @classmethod
    @abstractmethod
    def from_line(cls, *args, **kwargs) -> Self:
        pass

    @classmethod
    @abstractmethod
    def from_bytes(cls, *args, **kwargs) -> Self:
        pass

    @abstractmethod
    def __str__(self) -> str:
        pass

    @abstractmethod
    def __repr__(self) -> str:
        pass

    @abstractmethod
    def __bytes__(self) -> bytes:
        pass

    @abstractmethod
    def to_line(self, *args, **kwargs) -> str:
        pass
