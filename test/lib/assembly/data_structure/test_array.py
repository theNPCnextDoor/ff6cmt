import pytest

from src.lib.assembly.artifact.variable import Constant
from src.lib.assembly.artifact.variables import Variables
from src.lib.assembly.data_structure.blob import Blob
from src.lib.assembly.data_structure.array import Array
from src.lib.assembly.data_structure.instruction.operand import Operand
from src.lib.assembly.data_structure.string.string import String
from src.lib.assembly.data_structure.string.helpers import StringTypes
from src.lib.assembly.bytes import Bytes
from test.lib.assembly.conftest import VARIABLES, addr

GROUP = Array(
    parts=[
        Blob(operand=Operand(Bytes([0xAA]))),
        String(operand=Operand(Bytes([0x9A])), string_type=StringTypes.DESCRIPTION),
        Blob(operand=Operand(Bytes([0xBB])), delimiter=Operand(Bytes([0xFF]))),
        String(
            operand=Operand(Bytes([0x9B])),
            delimiter=Operand(Bytes([0x00]), variable=Constant(Bytes([0x00]), "zero")),
            string_type=StringTypes.MENU,
        ),
    ],
)


class TestArray:
    @pytest.mark.parametrize(
        ["line", "group"],
        [
            ('$AA | desc "a" | $BB,$FF | "b",zero', GROUP),
            (
                '"This is a string # " | $01',
                Array(
                    parts=[
                        String(
                            operand=Operand(
                                Bytes(
                                    [
                                        0x93,
                                        0xA1,
                                        0xA2,
                                        0xAC,
                                        0xFE,
                                        0xA2,
                                        0xAC,
                                        0xFE,
                                        0x9A,
                                        0xFE,
                                        0xAC,
                                        0xAD,
                                        0xAB,
                                        0xA2,
                                        0xA7,
                                        0xA0,
                                        0xFE,
                                        0xC9,
                                        0xFE,
                                    ]
                                )
                            )
                        ),
                        Blob(operand=Operand(Bytes([0x01]))),
                    ]
                ),
            ),
            (
                '$CD78 | "Status",$00',
                Array(
                    parts=[
                        Blob(operand=Operand(Bytes([0xCD, 0x78]))),
                        String(
                            operand=Operand(Bytes([0x92, 0xAD, 0x9A, 0xAD, 0xAE, 0xAC])),
                            delimiter=Operand(Bytes([0x00])),
                        ),
                    ]
                ),
            ),
        ],
    )
    @pytest.mark.parametrize("comment", ["", " ; some comment"])
    def test_from_line(self, line: str, comment: str, group: Array):
        assert (
            Array.from_line(
                line=line + comment,
                address=Bytes([0x00, 0x00, 0x00]),
                variables=Variables(Constant(Bytes.from_int(0), "zero")),
            )
            == group
        )

    @pytest.mark.parametrize(
        ["expected", "group"],
        [
            ('$AA | desc "a" | $BB,$FF | "b",zero', GROUP),
        ],
    )
    def test_str(self, group: Array, expected: str):
        assert str(group) == expected

    @pytest.mark.parametrize(
        ["expected", "group"],
        [
            (
                "Array(as_str='$AA | desc \"a\" | $BB,$FF | \"b\",zero', as_bytes=b'\\xaa\\x9a\\xbb\\xff\\x9b\\x00', as_hexa=0xAA9ABBFF9B00, parts=["
                "Blob(as_str='$AA', as_bytes=b'\\xaa', as_hexa=0xAA), "
                "String(as_str='desc \"a\"', as_bytes=b'\\x9a', as_hexa=0x9A), "
                "Blob(as_str='$BB,$FF', as_bytes=b'\\xbb\\xff', as_hexa=0xBBFF), "
                "String(as_str='\"b\",zero', as_bytes=b'\\x9b\\x00', as_hexa=0x9B00, delimiter_var=Constant(name='zero', value=0x00))])",
                GROUP,
            ),
        ],
    )
    def test_repr(self, group: Array, expected: str):
        assert repr(group) == expected

    @pytest.mark.parametrize(
        ["address", "expected"],
        [
            (None, '  $AA | desc "a" | $BB,$FF | "b",zero'),
            (addr(0xC01234), '  $AA | desc "a" | $BB,$FF | "b",zero ; $C01234'),
        ],
    )
    def test_to_line(self, address: Bytes | None, expected: str):
        assert GROUP.to_line(show_address=address is not None, address=address) == expected

    @pytest.mark.parametrize(
        ["group", "length"],
        [
            (GROUP, 6),
        ],
    )
    def test_len(self, group: Array, length: int):
        assert len(group) == length

    @pytest.mark.parametrize(
        ["group", "expected"],
        [
            (GROUP, b"\xaa\x9a\xbb\xff\x9b\x00"),
        ],
    )
    def test_bytes(self, group: Array, expected: bytes):
        assert bytes(group) == expected

    def test_find_length(self):
        assert Array.find_length('  $AA | desc "a" | $BB,$FF | "b",zero', VARIABLES) == 6
