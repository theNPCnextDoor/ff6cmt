from typing import Type

import pytest

from src.lib.assembly.artifact.variables import Variables
from src.lib.common.bytes import Bytes
from src.lib.assembly.artifact.variable import Label
from src.lib.common.operand import Operand, OperandType
from src.lib.assembly.data_structure.pointer import Pointer
from src.lib.misc.exception import ImpossibleDestination, NoVariableException
from test.lib.conftest import TEST_WORD, CHARLIE, addr


class TestPointer:
    @pytest.mark.parametrize(
        ["operand", "address", "anchor", "pointer"],
        [
            (
                "$1413",
                addr(0x111111),
                None,
                Pointer(operand=Operand(Bytes([0x14, 0x13]), "_", OperandType.DEFAULT), destination=addr(0x111413)),
            ),
            (
                "!label_1",
                addr(0xD2FF00),
                None,
                Pointer(
                    operand=Operand(Bytes([0x34, 0x56]), "_", OperandType.DEFAULT, Label(addr(0xD23456), "label_1")),
                    destination=addr(0xD23456),
                ),
            ),
            (
                "!label_1",
                addr(0x000001),
                Operand(addr(0xD21111)),
                Pointer(
                    operand=Operand(Bytes([0x23, 0x45]), "_", OperandType.DEFAULT, Label(addr(0xD23456), "label_1")),
                    destination=addr(0xD23456),
                    anchor=Operand(addr(0xD21111)),
                ),
            ),
            (
                "$1413",
                addr(0x000001),
                Operand(addr(0x121111)),
                Pointer(
                    operand=Operand(Bytes([0x14, 0x13]), "_", OperandType.DEFAULT, None),
                    destination=addr(0x122524),
                    anchor=Operand(addr(0x121111)),
                ),
            ),
        ],
    )
    def test_from_line(self, operand: str, address: Bytes, anchor: Operand | None, pointer: Pointer, labels: Variables):
        assert Pointer.from_line(operand, address, anchor, labels) == pointer

    @pytest.mark.parametrize(
        ["operand", "address", "anchor", "exception"],
        [
            ("label_3", addr(0x12FF00), None, NoVariableException),
            ("label_1", addr(0x000000), None, ImpossibleDestination),
        ],
    )
    def test_from_line_raise_exception(
        self, operand: str, address: Bytes, anchor: Bytes | None, exception: Type[Exception], labels: Variables
    ):
        with pytest.raises(exception):
            Pointer.from_line(operand, address, anchor, labels)

    @pytest.mark.parametrize(
        ["value", "address", "anchor", "expected", "destination"],
        [
            (
                b"\x00\x01",
                addr(0),
                None,
                Pointer(operand=Operand(Bytes([0x01, 0x00])), destination=addr(0x000100)),
                addr(0x000100),
            ),
            (
                b"\x12\x34",
                addr(0x123456),
                None,
                Pointer(operand=Operand(Bytes([0x34, 0x12])), destination=addr(0x123412)),
                addr(0x123412),
            ),
            (
                b"\x26\x38",
                addr(0x123456),
                Operand(addr(0x300123)),
                Pointer(
                    operand=Operand(Bytes([0x38, 0x26])),
                    destination=addr(0x303949),
                    anchor=Operand(Bytes.from_address(0x300123)),
                ),
                Bytes.from_address(0x303949),
            ),
        ],
    )
    def test_from_bytes(
        self, value: bytes, address: Bytes, anchor: Bytes | None, expected: Pointer, destination: Bytes
    ):
        pointer = Pointer.from_bytes(value=value, address=address, anchor=anchor)
        assert pointer == expected

    @pytest.mark.parametrize(
        ["pointer", "address", "current_anchor", "line"],
        [
            (
                Pointer(operand=Operand(Bytes([0x11, 0x22])), destination=addr(0x270123)),
                None,
                Bytes.from_address(0x270123),
                "  ptr $1122",
            ),
            (
                Pointer(operand=Operand(Bytes([0x34, 0x56]), variable=CHARLIE), destination=addr(0x273456)),
                None,
                Bytes.from_address(0x270123),
                "  ptr !charlie",
            ),
            (
                Pointer(
                    operand=Operand(Bytes([0x01, 0x02])),
                    destination=addr(0x001112),
                    anchor=Operand(Bytes.from_address(0x001010)),
                ),
                None,
                Operand(Bytes.from_address(0x001010)),
                "  rptr $0102",
            ),
            (
                Pointer(
                    operand=Operand(Bytes([0x01, 0x02])),
                    destination=addr(0xC01112),
                    anchor=Operand(Bytes.from_address(0xC01010)),
                ),
                None,
                Operand(Bytes.from_address(0xE789AB)),
                "\n#$C01010\n  rptr $0102",
            ),
            (
                Pointer(
                    operand=Operand(Bytes([0x01, 0x02])),
                    destination=addr(0xD23557),
                    anchor=Operand(addr(0xD23456)),
                ),
                None,
                Operand(Bytes.from_address(0xE789AB)),
                "\n#label_1\n  rptr $0102",
            ),
            (
                Pointer(
                    operand=Operand(Bytes([0x00, 0x00]), variable=CHARLIE),
                    destination=addr(0xD23456),
                    anchor=Operand(Bytes.from_address(0xD23456)),
                ),
                None,
                Operand(Bytes.from_address(0xE789AB)),
                "\n#label_1\n  rptr !charlie",
            ),
            (
                Pointer(
                    operand=Operand(Bytes([0x00, 0x00]), variable=CHARLIE),
                    destination=addr(0xD23456),
                    anchor=Operand(Bytes.from_address(0xD23456)),
                ),
                addr(0xC01234),
                Operand(Bytes.from_address(0xE789AB)),
                "\n#label_1\n  rptr !charlie ; C01234",
            ),
        ],
    )
    def test_to_line(
        self,
        pointer: Pointer,
        address: Bytes | None,
        current_anchor: Bytes,
        line: str,
        labels: Variables,
    ):
        assert (
            pointer.to_line(
                show_address=address is not None, labels=labels, current_anchor=current_anchor, address=address
            )
            == line
        )

    @pytest.mark.parametrize(
        ["pointer", "expected_bytes"],
        [
            (Pointer(operand=Operand(Bytes([0x11, 0x22])), destination=addr(0x001122)), b"\x22\x11"),
            (Pointer(operand=Operand(Bytes([0x44, 0x55])), destination=addr(0x004455)), b"\x55\x44"),
        ],
    )
    def test_bytes(self, pointer: Pointer, expected_bytes: bytes):
        assert bytes(pointer) == expected_bytes

    @pytest.mark.parametrize(
        ["pointer", "expected"],
        [
            (Pointer(operand=Operand(Bytes([0x34, 0x56])), destination=addr(0x003456)), "ptr $3456"),
            (Pointer(operand=Operand(TEST_WORD), destination=addr(0x001234)), "ptr $1234"),
        ],
    )
    def test_str(self, pointer: Pointer, expected: str):
        assert str(pointer) == expected

    @pytest.mark.parametrize(
        ["pointer", "expected"],
        [
            (
                Pointer(operand=Operand(Bytes([0x34, 0x56])), destination=addr(0x123456)),
                "Pointer(as_str='ptr $3456', as_bytes=b'V4', as_hexa=0x3456, destination=0x123456)",
            ),
            (
                Pointer(
                    operand=Operand(TEST_WORD),
                    destination=addr(0x3468AC),
                    anchor=Operand(Bytes([0x34, 0x56, 0x78])),
                ),
                "Pointer(as_str='ptr $1234', as_bytes=b'4\\x12', as_hexa=0x1234, destination=0x3468AC, anchor=0x345678)",
            ),
        ],
    )
    def test_repr(self, pointer: Pointer, expected: str):
        assert repr(pointer) == expected

    def test_len(self):
        assert len(Pointer(operand=Operand(Bytes([0x45, 0x67])), destination=addr(0))) == 2

    def test_find_length(self):
        assert Pointer.find_length() == 2
