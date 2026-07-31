from __future__ import annotations

import pytest

from src.lib.common.operand import Operand
from src.lib.common.bytes import Bytes
from src.lib.assembly.data_structure.blob import Blob
from test.lib.conftest import TEST_BYTE, BRAVO, ALFA, VARIABLES, addr


class TestBlob:
    @pytest.mark.parametrize(
        ["blob", "data"],
        [
            (
                Blob(operand=Operand(Bytes([0x12, 0x34, 0x56, 0x78]))),
                Operand(Bytes([0x12, 0x34, 0x56, 0x78])),
            ),
            (
                Blob(operand=Operand(Bytes([0x9A, 0xBC, 0xDE, 0xF0]))),
                Operand(Bytes([0x9A, 0xBC, 0xDE, 0xF0])),
            ),
        ],
    )
    def test_init(self, blob: Blob, data: Bytes):
        assert blob.operand == data

    @pytest.mark.parametrize(
        ["operand", "delimiter", "blob"],
        [
            ("$12", None, Blob(operand=Operand(TEST_BYTE))),
            ("$0123456789ABCDEF", None, Blob(operand=Operand(Bytes([0x01, 0x23, 0x45, 0x67, 0x89, 0xAB, 0xCD, 0xEF])))),
        ],
    )
    def test_from_line(self, operand: str, delimiter: str | None, blob: Blob):
        assert Blob.from_line(operand, delimiter) == blob

    @pytest.mark.parametrize(
        ["data", "blob"],
        [
            (b"\x12", Blob(operand=Operand(TEST_BYTE))),
            (
                b"\x01\x23\x45\x67\x89\xab\xcd\xef",
                Blob(operand=Operand(Bytes([0xEF, 0xCD, 0xAB, 0x89, 0x67, 0x45, 0x23, 0x01]))),
            ),
            (b"\xff\xff", Blob(operand=Operand(Bytes([0xFF, 0xFF])))),
        ],
    )
    def test_from_bytes(self, data: bytes, blob: Blob):
        assert Blob.from_bytes(data) == blob

    @pytest.mark.parametrize(
        ["blob", "expected"],
        [
            (Blob(operand=Operand(Bytes([0x12, 0x34, 0x56, 0x78]))), "$12345678"),
            (
                Blob(
                    operand=Operand(Bytes([0x12, 0x34]), variable=BRAVO),
                    delimiter=Operand(Bytes([0x12]), variable=ALFA),
                ),
                "bravo,alfa",
            ),
        ],
    )
    def test_str(self, blob: Blob, expected: str):
        assert str(blob) == expected

    @pytest.mark.parametrize(
        ["blob", "expected"],
        [
            (
                Blob(operand=Operand(Bytes([0x12, 0x34, 0x56, 0x78]))),
                "Blob(as_str='$12345678', as_bytes=b'xV4\\x12', as_hexa=0x12345678)",
            ),
            (
                Blob(
                    operand=Operand(Bytes([0x12, 0x34]), variable=BRAVO),
                    delimiter=Operand(Bytes([0x12]), variable=ALFA),
                ),
                "Blob(as_str='bravo,alfa', as_bytes=b'4\\x12\\x12', as_hexa=0x123412, operand_var=Constant(name='bravo', value=0x1234), delimiter_var=Constant"
                "(name='alfa', value=0x12))",
            ),
        ],
    )
    def test_repr(self, blob: Blob, expected: str):
        assert repr(blob) == expected

    @pytest.mark.parametrize(
        ["address", "expected"], [(None, "  $12345678"), (addr(0xC01234), "  $12345678 ; $C01234")]
    )
    def test_to_line(self, address: Bytes | None, expected: str):
        assert (
            Blob(operand=Operand(Bytes([0x12, 0x34, 0x56, 0x78]))).to_line(
                show_address=address is not None, address=address
            )
            == expected
        )

    @pytest.mark.parametrize(
        ["blob", "length"],
        [
            (Blob(operand=Operand(Bytes([0x12, 0x34, 0x56, 0x78]))), 4),
        ],
    )
    def test_len(self, blob: Blob, length: int):
        assert len(blob) == length

    @pytest.mark.parametrize(
        ["blob", "output"],
        [
            (Blob(operand=Operand(Bytes([0x12, 0x34, 0x56, 0x78]))), b"\x78\x56\x34\x12"),
            (
                Blob(operand=Operand(Bytes([0x12, 0x34, 0x56, 0x78])), delimiter=Operand(Bytes([0x00]))),
                b"\x78\x56\x34\x12\x00",
            ),
            (
                Blob(operand=Operand(Bytes([0x12, 0x34, 0x56, 0x78])), delimiter=Operand(Bytes([0xFF]))),
                b"\x78\x56\x34\x12\xff",
            ),
        ],
    )
    def test_bytes(self, blob: Blob, output: Bytes):
        assert bytes(blob) == output

    @pytest.mark.parametrize("delimiter", [None, "$00", "alfa"])
    @pytest.mark.parametrize(
        ["operand", "length"],
        [
            ("$12", 1),
            ("$1234", 2),
            ("$123456", 3),
            ("alfa", 1),
            ("bravo", 2),
            ("charlie", 3),
            (".charlie", 1),
            ("!charlie", 2),
            ("unrecognized_variable", 3),
        ],
    )
    def test_find_length(self, operand: str, delimiter: str | None, length: int):
        assert Blob.find_length(operand, VARIABLES, delimiter) == length + int(bool(delimiter))
