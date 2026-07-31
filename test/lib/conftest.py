from __future__ import annotations
import pytest

from src.lib.assembly.artifact.variable import Label, Constant
from src.lib.assembly.artifact.variables import Variables
from src.lib.common.bytes import Bytes


def addr(value: int) -> Bytes:
    return Bytes.from_address(value)


DEFAULT_ADDRESS = addr(0xC00000)


TEST_BYTE = Bytes([0x12])
TEST_WORD = Bytes([0x12, 0x34])
TEST_ADDRESS = Bytes([0xD2, 0x34, 0x56])

ALFA = Constant(Bytes.from_int(0x12), "alfa")
BRAVO = Constant(Bytes.from_int(0x1234), "bravo")
CHARLIE = Label(Bytes.from_address(0xD23456), "charlie")
DELTA = Constant(Bytes.from_int(0x00), "delta")
ECHO = Label(addr(0x7E0123), "echo")

VARIABLES = Variables(ALFA, BRAVO, CHARLIE, DELTA, ECHO)


@pytest.fixture
def labels() -> Variables:
    return Variables(
        Label(TEST_ADDRESS, "label_1"),
        Label(addr(0x34FFFE), "label_2"),
    )
