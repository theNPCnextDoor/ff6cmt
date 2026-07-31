from typing import Self

from src.lib.common.artifact import Artifact


class ThreadCounter(Artifact):
    def __init__(self, threads: int):
        self.threads = threads

    @classmethod
    def from_line(cls, threads: str) -> Self:
        return ThreadCounter(int(threads))

    def to_line(self, *args, **kwargs) -> str:
        return str(self)

    def __repr__(self) -> str:
        return f"ThreadCounter(n_threads={self.threads})"

    def __str__(self) -> str:
        return f"n_threads: {self.threads}"
