import pytest

from src.lib.assembly.data_structure.string.charset import Charset
from src.lib.assembly.data_structure.string.helpers import DESCRIPTION_CHARSET, DUMMY_CHARSET


class TestCharset:

    @pytest.mark.parametrize(
        ["value", "char"], [
            (0x01, "A"),
            (0x02, "<0x02>"),
            (0x03, "<0x03: _>"),
            (0x04, "ab"),
            (0x05, "\n"),
            (0x06, "<PAGE>\n"),
            (0x07, "'"),
            (0x08, "'s"),
            (0x09, "123"),
            (0x0A, "<ARGUMENT: _>"),
            (0x0B, "<0x0B>")
        ],
    )
    def test_get_char(self, value: int, char: str):
        assert Charset(charset=DUMMY_CHARSET).get_char(value=value)["string"] == char

    @pytest.mark.parametrize(
        ["number", "value"], [
            (0x01, "A"),
            (0x02, "<0x02>"),
            (0x03, "<0x03: _>"),
            (0x04, "ab"),
            (0x05, "\n"),
            (0x06, "<PAGE>\n"),
            (0x07, "'"),
            (0x08, "'s"),
            (0x09, "123"),
            (0x0A, "<ARGUMENT: _>"),
            (0x0B, "<0x0B>")
        ],
    )
    def test_get_value(self, value: str, number: int):
        assert Charset(charset=DUMMY_CHARSET).get_value(value=value) == number

    @pytest.mark.parametrize(
        ["value", "char"], [
            (b"\x01", "A"),
            (b"\x02", "<0x02>"),
            (b"\x03\x12", "<0x03: 12>"),
            (b"\x04", "ab"),
            (b"\x05", "\n"),
            (b"\x06", "<PAGE>\n"),
            (b"\x07", "'"),
            (b"\x08", "'s"),
            (b"\x09", "123"),
            (b"\x0A\xFE", "<ARGUMENT: FE>"),
            (b"\x0B", "<0x0B>")
        ],
    )
    def test_get_bytes(self, char: str, value: bytes):
        assert Charset(charset=DUMMY_CHARSET).get_bytes(value=char) == value

    @pytest.mark.parametrize(
        ["value", "number"],
        [
            ("<0x00>", b"\x00"),
            ("A", b"\x80"),
            ("<LINE>", b"\x01"),
            ("<HOLY>", b"\xd6"),
            ("<0xEB>", b"\xeb"),
            (" ", b"\xff"),
        ],
    )
    def test_get_bytes_description_charset(self, value: str, number: bytes):
        assert Charset(charset=DESCRIPTION_CHARSET).get_bytes(value=value) == number

    def test_create_regex(self):
        charset = Charset(DUMMY_CHARSET)
        regex = charset._create_regex()
        assert regex == (
            "(<0x03:\\ [0-9A-F]{2}>|<ARGUMENT:\\ [0-9A-F]{2}>|123|ab|<PAGE>\\\n|'s|A|<0x02>|\\\n|'|<0x[0-9A-F]{2}>)"
        )