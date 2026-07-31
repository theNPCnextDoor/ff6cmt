from typing import Any

import pytest

from src.lib.misc.exception import UnderflowError
from src.lib.common.bytes import Bytes, Endian


class TestBytes:
    @pytest.mark.parametrize("value", [[], [0x00], [0x12, 0x34, 0x56]])
    @pytest.mark.parametrize("endian", [Endian.BIG, Endian.LITTLE])
    def test_init(self, value: list[int] | None, endian: Endian):
        _input = Bytes(value=value, endian=endian)
        assert _input.value == value
        assert _input.endian == endian

    @pytest.mark.parametrize("value", [0x00, "00", b"\x00"])
    def test_init_raise_value_error_when_value_is_not_list(self, value: Any):
        with pytest.raises(ValueError):
            Bytes(value=value)

    @pytest.mark.parametrize(
        ["value", "length", "expected"],
        [([], 1, [0x00]), ([0x12], 3, [0x00, 0x00, 0x12]), ([0x12, 0x34, 0x56], 2, [0x34, 0x56])],
    )
    def test_adjust(self, value: list[int], length: int, expected: list[int]):
        left = Bytes(value=value)
        left._adjust(length=length)
        assert left.value == expected

    @pytest.mark.parametrize(
        ["value", "length", "expected"],
        [
            (0x00, None, [0x00]),
            (0x00, 2, [0x00, 0x00]),
            (0x1234, None, [0x12, 0x34]),
            (0x1234, 1, [0x34]),
            (0x1234, 3, [0x00, 0x12, 0x34]),
        ],
    )
    def test_from_int(self, value: int, length: int, expected: list[int]):
        assert Bytes.from_int(value=value, length=length).value == expected

    @pytest.mark.parametrize(
        ["value", "expected"],
        [(0x00, [0x00, 0x00, 0x00]), (0x1234, [0x00, 0x12, 0x34]), (0x123456, [0x12, 0x34, 0x56])],
    )
    def test_from_address(self, value: int, expected: list[int]):
        assert Bytes.from_address(value=value).value == expected

    @pytest.mark.parametrize(
        ["value", "expected"], [("00", [0x00]), ("12", [0x12]), ("0000", [0x00, 0x00]), ("1234", [0x12, 0x34])]
    )
    def test_from_str(self, value: str, expected: list[int]):
        assert Bytes.from_str(value=value).value == expected

    @pytest.mark.parametrize("input_value", ["", "C"])
    def test_from_str_malformed_string_raises_error(self, input_value: str):
        with pytest.raises(ValueError):
            Bytes.from_str(value=input_value)

    @pytest.mark.parametrize(
        ["value", "endian", "expected"],
        [
            (b"\x00", Endian.LITTLE, [0x00]),
            (b"\x12", Endian.LITTLE, [0x12]),
            (b"\x00\x00", Endian.LITTLE, [0x00, 0x00]),
            (b"\x12\x34\x56", Endian.BIG, [0x12, 0x34, 0x56]),
            (b"\x12\x34\x56", Endian.LITTLE, [0x56, 0x34, 0x12]),
        ],
    )
    def test_from_bytes(self, value: bytes, endian: Endian, expected: list[int]):
        assert Bytes.from_bytes(value=value, endian=endian).value == expected

    def test_from_bytes_empty_object_raises_error(self):
        with pytest.raises(ValueError):
            Bytes.from_bytes(value=b"")

    @pytest.mark.parametrize(
        ["value", "expected"],
        [([0x00], 0), ([0x12], 0x12), ([0x12, 0x34], 0x1234), ([0x56, 0x34, 0x12], 0x563412)],
    )
    def test_int(self, value: list[int], expected: int):
        assert int(Bytes(value=value)) == expected

    @pytest.mark.parametrize(["value", "expected"], [([0x00], "00"), ([0x12], "12"), ([0x12, 0x34], "1234")])
    def test_str(self, value: list[int], expected: str):
        assert str(Bytes(value=value)) == expected

    @pytest.mark.parametrize(
        ["value", "endian", "expected"],
        [
            (
                [0x00],
                Endian.LITTLE,
                "Bytes(value=[0], as_decimal=0, as_hexa=0x00, as_bytes=b'\\x00', endian=Endian.LITTLE)",
            ),
            (
                [0x12],
                Endian.LITTLE,
                "Bytes(value=[18], as_decimal=18, as_hexa=0x12, as_bytes=b'\\x12', endian=Endian.LITTLE)",
            ),
            (
                [0x12, 0x34],
                Endian.LITTLE,
                "Bytes(value=[18, 52], as_decimal=4660, as_hexa=0x1234, as_bytes=b'4\\x12', endian=Endian.LITTLE)",
            ),
            (
                [0x12, 0x34, 0x56],
                Endian.LITTLE,
                "Bytes(value=[18, 52, 86], as_decimal=1193046, as_hexa=0x123456, as_bytes=b'V4\\x12', endian=Endian.LITTLE)",
            ),
            (
                [0x12, 0x34, 0x56],
                Endian.BIG,
                "Bytes(value=[18, 52, 86], as_decimal=1193046, as_hexa=0x123456, as_bytes=b'\\x124V', endian=Endian.BIG)",
            ),
        ],
    )
    def test_repr(self, value: list[int], endian: Endian, expected: str):
        assert repr(Bytes(value=value, endian=endian)) == expected

    @pytest.mark.parametrize(
        ["value", "endian", "expected"],
        [
            ([0x00], Endian.LITTLE, b"\x00"),
            ([0x12], Endian.LITTLE, b"\x12"),
            ([0x12, 0x34], Endian.LITTLE, b"\x34\x12"),
            ([0x12, 0x34, 0x56], Endian.LITTLE, b"\x56\x34\x12"),
            ([0x12, 0x34, 0x56], Endian.BIG, b"\x12\x34\x56"),
        ],
    )
    def test_bytes(self, value: list[int], endian: Endian.LITTLE, expected: bytes):
        assert bytes(Bytes(value=value, endian=endian)) == expected

    @pytest.mark.parametrize(["value", "expected"], [([0x00], 1), ([0x12], 1), ([0x12, 0x34], 2)])
    def test_len(self, value: list[int], expected: int):
        assert len(Bytes(value=value)) == expected

    @pytest.mark.parametrize(
        ["left", "right", "expected"],
        [
            ([0x00], [0x00], True),
            ([0x12], [0x12], True),
            ([0x00, 0x12], [0x12], False),
            ([0x12, 0x34], [0x12, 0x34], True),
            ([0x12, 0x34], [0x34, 0x12], False),
        ],
    )
    def test_eq(self, left: list[int], right: list[int], expected: bool):
        assert (Bytes(value=left) == Bytes(value=right)) is expected

    @pytest.mark.parametrize(
        ["left", "right", "expected"],
        [
            ([0x00], [0x00], False),
            ([0x12], [0x12], False),
            ([0x00, 0x12], [0x12], False),
            ([0x12, 0x34], [0x12, 0x34], False),
            ([0x34, 0x12], [0x12, 0x34], False),
            ([0x12, 0x34], [0x34, 0x12], True),
        ],
    )
    def test_lt(self, left: list[int], right: list[int], expected: bool):
        assert (Bytes(value=left) < Bytes(value=right)) is expected

    @pytest.mark.parametrize("method", ["__eq__", "__lt__"])
    def test_comparison_when_not_comparing_with_bytes_raises_error(self, method: str):
        with pytest.raises(ValueError):
            getattr(Bytes(value=[0x00]), method)(0x00)

    @pytest.mark.parametrize(
        ["left", "expected"],
        [(Bytes([0x00])[0:1], [0x00]), (Bytes([0x12])[0:1], [0x12]), (Bytes([0x12, 0x34, 0x56])[1:], [0x34, 0x56])],
    )
    def test_get_item(self, left: Bytes, expected: list[int]):
        assert left.value == expected

    @pytest.mark.parametrize("right", [0x34, Bytes(value=[0x34]), Bytes(value=[0x00, 0x34])])
    def test_add(self, right: int | Bytes):
        assert Bytes(value=[0x12]) + right == Bytes(value=[0x46])

    @pytest.mark.parametrize("right", [0xFF, Bytes(value=[0xFF])])
    def test_add_raises_error_when_overflow(self, right: int | Bytes):
        with pytest.raises(OverflowError):
            Bytes(value=[0x01]) + right

    @pytest.mark.parametrize("right", [0x34, Bytes(value=[0x34]), Bytes(value=[0x00, 0x34])])
    def test_sub(self, right: int | Bytes):
        assert Bytes(value=[0x46]) - right == Bytes(value=[0x12])

    @pytest.mark.parametrize("right", [0xFF, Bytes(value=[0xFF])])
    def test_sub_raises_error_when_underflow(self, right: int | Bytes):
        with pytest.raises(UnderflowError):
            Bytes(value=[0x01]) - right

    @pytest.mark.parametrize(["value", "expected"], [([0x00, 0x00, 0x00], 0x000000), ([0x12, 0x34, 0x56], 0x120000)])
    def test_bank(self, value: list[int], expected: int):
        assert Bytes(value=value).bank() == expected

    def test_bank_raises_an_error_when_not_an_address(self):
        with pytest.raises(AttributeError):
            Bytes([0x00]).bank()
