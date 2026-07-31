import pytest

from src.lib.assembly.artifact.variable import Label
from src.lib.assembly.artifact.variables import Variables
from src.lib.common.bytes import Bytes
from src.lib.common.operand import Operand, OperandType
from src.lib.misc.exception import NoVariableException, UndefinedDestination
from test.lib.conftest import VARIABLES, CHARLIE, BRAVO, ALFA, ECHO, addr


class TestOperand:

    @pytest.mark.parametrize(
        ["value", "parent_address", "operand_type", "expected"],
        [
            (
                "#$12",
                addr(0),
                OperandType.DEFAULT,
                Operand(value=Bytes.from_int(0x12), mode="#_", operand_type=OperandType.DEFAULT),
            ),
            (
                "$1234,X",
                addr(0),
                OperandType.DEFAULT,
                Operand(value=Bytes.from_int(0x1234), mode="_,X", operand_type=OperandType.DEFAULT),
            ),
            (
                "($123456),Y",
                addr(0),
                OperandType.DEFAULT,
                Operand(value=Bytes.from_int(0x123456), mode="(_),Y", operand_type=OperandType.DEFAULT),
            ),
            (
                "#alfa",
                addr(0),
                OperandType.DEFAULT,
                Operand(value=Bytes.from_int(0x12), mode="#_", operand_type=OperandType.DEFAULT, variable=ALFA),
            ),
            (
                "bravo,X",
                addr(0),
                OperandType.DEFAULT,
                Operand(value=Bytes.from_int(0x1234), mode="_,X", operand_type=OperandType.DEFAULT, variable=BRAVO),
            ),
            (
                "(.charlie),Y",
                addr(0xD20000),
                OperandType.DEFAULT,
                Operand(value=Bytes.from_int(0xD2), mode="(_),Y", operand_type=OperandType.DEFAULT, variable=CHARLIE),
            ),
            (
                "(!charlie),Y",
                addr(0x120000),
                OperandType.DEFAULT,
                Operand(value=Bytes.from_int(0x3456), mode="(_),Y", operand_type=OperandType.DEFAULT, variable=CHARLIE),
            ),
            (
                "(charlie),Y",
                addr(0xD20000),
                OperandType.DEFAULT,
                Operand(value=addr(0xD23456), mode="(_),Y", operand_type=OperandType.DEFAULT, variable=CHARLIE),
            ),
            (
                "echo",
                addr(0x7E0123),
                OperandType.DEFAULT,
                Operand(value=addr(0x7E0123), variable=ECHO),
            ),
        ],
    )
    def test_from_line(self, value: str, parent_address: Bytes, operand_type: OperandType, expected: Operand):
        assert Operand.from_line(value, parent_address, operand_type, VARIABLES) == expected

    def test_from_line_raises_value_error(self):
        with pytest.raises(NoVariableException):
            Operand.from_line(
                value="zebra,X",
                parent_address=addr(0),
                operand_type=OperandType.DEFAULT,
                variables=Variables(*VARIABLES),
            )

    @pytest.mark.parametrize(
        ["value", "mode", "operand_type", "parent_address", "expected"],
        [
            (
                b"\x12",
                "_",
                OperandType.DEFAULT,
                addr(0x123456),
                Operand(value=Bytes.from_int(0x12), mode="_", operand_type=OperandType.DEFAULT),
            ),
            (
                b"\x56\x34",
                "_,X",
                OperandType.JUMPING,
                addr(0xD20000),
                Operand(
                    value=Bytes.from_int(0x3456),
                    mode="_,X",
                    operand_type=OperandType.JUMPING,
                    variable=Label(addr(0xD23456), "charlie"),
                ),
            ),
            (
                b"\x11\x11",
                "_,X",
                OperandType.JUMPING,
                addr(0xD20000),
                Operand(
                    value=Bytes.from_int(0x1111),
                    mode="_,X",
                    operand_type=OperandType.JUMPING,
                    variable=Label(addr(0xD21111), "label_d21111"),
                ),
            ),
            (
                b"\x23\x01\x7e",
                "_",
                OperandType.JUMPING,
                addr(0x7E0123),
                Operand(value=addr(0x7E0123), mode="_", operand_type=OperandType.JUMPING, variable=ECHO),
            ),
            (
                b"\x56\x34\xd2",
                "_",
                OperandType.JUMPING,
                addr(0xD23457),
                Operand(value=addr(0xD23456), mode="_", operand_type=OperandType.JUMPING, variable=CHARLIE),
            ),
        ],
    )
    def test_from_bytes(
        self, value: bytes, mode: str, operand_type: OperandType, parent_address: Bytes, expected: Operand
    ):
        operand = Operand.from_bytes(
            value=value,
            mode=mode,
            operand_type=operand_type,
            parent_address=parent_address,
            variables=VARIABLES,
        )
        assert operand == expected

    @pytest.mark.parametrize(
        ["operand", "mode"],
        [
            ("", ""),
            ("*", "_"),
            ("#*", "#_"),
            ("*,S", "_,S"),
            ("*,X", "_,X"),
            ("*,Y", "_,Y"),
            ("(*)", "(_)"),
            ("(*),Y", "(_),Y"),
            ("(*,S),Y", "(_,S),Y"),
            ("(*,X)", "(_,X)"),
            ("[*]", "[_]"),
            ("[*],Y", "[_],Y"),
        ],
    )
    @pytest.mark.parametrize("value", ["$01", ".alice", "!bob", "charlie"])
    def test_to_mode(self, operand: str, mode: str, value: str):
        operand = operand.replace("*", value)
        assert Operand._to_mode(operand, OperandType.DEFAULT) == mode

    @pytest.mark.parametrize("operand_type", [OperandType.BRANCHING, OperandType.LONG_BRANCHING])
    def test_to_mode_with_branching_operand_types(self, operand_type: OperandType):
        assert Operand._to_mode("charlie", operand_type) == "_"

    @pytest.mark.parametrize(
        ["parent_address", "operand_type", "length", "destination", "expected"],
        [
            (addr(0x010000), OperandType.JUMPING, 2, addr(0x011234), Bytes([0x12, 0x34])),
            (
                addr(0x010000),
                OperandType.LONG_JUMPING,
                3,
                addr(0x023456),
                Bytes([0x02, 0x34, 0x56]),
            ),
            (addr(0x010000), OperandType.DEFAULT, 1, addr(0xC23456), Bytes([0xC2])),
            (addr(0x010000), OperandType.DEFAULT, 2, addr(0xC23456), Bytes([0x34, 0x56])),
            (
                addr(0x010000),
                OperandType.DEFAULT,
                3,
                addr(0xC23456),
                Bytes([0xC2, 0x34, 0x56]),
            ),
            (addr(0x013456), OperandType.BRANCHING, 1, addr(0x013458), Bytes([0x00])),
            (addr(0x013456), OperandType.BRANCHING, 1, addr(0x013459), Bytes([0x01])),
            (addr(0x013456), OperandType.BRANCHING, 1, addr(0x013457), Bytes([0xFF])),
            (addr(0x013456), OperandType.BRANCHING, 1, addr(0x0134D7), Bytes([0x7F])),
            (addr(0x013456), OperandType.BRANCHING, 1, addr(0x0133D8), Bytes([0x80])),
            (
                Bytes.from_int(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x013459),
                Bytes([0x00, 0x00]),
            ),
            (
                Bytes.from_int(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x01345A),
                Bytes([0x00, 0x01]),
            ),
            (
                Bytes.from_int(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x013458),
                Bytes([0xFF, 0xFF]),
            ),
            (
                Bytes.from_int(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x01B458),
                Bytes([0x7F, 0xFF]),
            ),
            (
                Bytes.from_int(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x01B459),
                Bytes([0x80, 0x00]),
            ),
        ],
    )
    def test_destination_to_value(
        self, parent_address: Bytes, operand_type: OperandType, length: int, destination: Bytes, expected: Bytes
    ):
        value = Operand._destination_to_value(
            parent_address=parent_address, operand_type=operand_type, length=length, destination=destination
        )
        assert value == expected

    @pytest.mark.parametrize(
        ["parent_address", "operand_type", "length", "expected", "value"],
        [
            (Bytes.from_address(0x000000), OperandType.JUMPING, 2, Bytes.from_address(0x001234), Bytes([0x12, 0x34])),
            (Bytes.from_address(0x010000), OperandType.JUMPING, 2, Bytes.from_address(0x011234), Bytes([0x12, 0x34])),
            (
                Bytes.from_address(0x010000),
                OperandType.LONG_JUMPING,
                3,
                Bytes.from_address(0x023456),
                Bytes([0x02, 0x34, 0x56]),
            ),
            (Bytes.from_address(0x010000), OperandType.DEFAULT, 2, Bytes.from_address(0x013456), Bytes([0x34, 0x56])),
            (
                Bytes.from_address(0x010000),
                OperandType.DEFAULT,
                3,
                Bytes.from_address(0x023456),
                Bytes([0x02, 0x34, 0x56]),
            ),
            (Bytes.from_address(0x013456), OperandType.BRANCHING, 1, Bytes.from_address(0x013458), Bytes([0x00])),
            (Bytes.from_address(0x013456), OperandType.BRANCHING, 1, Bytes.from_address(0x013459), Bytes([0x01])),
            (Bytes.from_address(0x013456), OperandType.BRANCHING, 1, Bytes.from_address(0x013457), Bytes([0xFF])),
            (Bytes.from_address(0x013456), OperandType.BRANCHING, 1, Bytes.from_address(0x0134D7), Bytes([0x7F])),
            (Bytes.from_address(0x013456), OperandType.BRANCHING, 1, Bytes.from_address(0x0133D8), Bytes([0x80])),
            (
                Bytes.from_address(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x013459),
                Bytes([0x00, 0x00]),
            ),
            (
                Bytes.from_address(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x01345A),
                Bytes([0x00, 0x01]),
            ),
            (
                Bytes.from_address(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x013458),
                Bytes([0xFF, 0xFF]),
            ),
            (
                Bytes.from_address(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x01B458),
                Bytes([0x7F, 0xFF]),
            ),
            (
                Bytes.from_address(0x013456),
                OperandType.LONG_BRANCHING,
                2,
                Bytes.from_address(0x01B459),
                Bytes([0x80, 0x00]),
            ),
        ],
    )
    def test_value_to_destination(
        self, parent_address: Bytes, operand_type: OperandType, length: int, expected: Bytes, value: Bytes
    ):
        operand = Operand(value=value, mode="", operand_type=operand_type)
        destination = operand.value_to_destination(parent_address=parent_address)
        assert destination == expected

    def test_value_to_destination_raises_undefined_destination(self):
        operand = Operand(value=Bytes.from_int(0x12), mode="_", operand_type=OperandType.DEFAULT)
        with pytest.raises(UndefinedDestination):
            operand.value_to_destination(parent_address=Bytes.from_address(0x123456))

    def test_len(self):
        assert len(Operand(value=Bytes.from_address(0x123456), mode="", operand_type=OperandType.DEFAULT)) == 3

    def test_bytes(self):
        assert (
            bytes(
                Operand(value=Bytes.from_address(0xD23456), mode="", operand_type=OperandType.DEFAULT, variable=CHARLIE)
            )
            == b"\x56\x34\xd2"
        )

    @pytest.mark.parametrize(
        ["operand", "expected"],
        [
            (Operand(value=Bytes([0x12]), mode="_", operand_type=OperandType.DEFAULT), "$12"),
            (Operand(value=Bytes([0x12, 0x34]), mode="#_", operand_type=OperandType.DEFAULT), "#$1234"),
            (Operand(value=Bytes([0x12, 0x34, 0x56]), mode="(_,S)", operand_type=OperandType.DEFAULT), "($D23456,S)"),
            (Operand(value=Bytes([0x12]), mode="_", operand_type=OperandType.DEFAULT, variable=ALFA), "alfa"),
            (
                Operand(value=Bytes([0x12, 0x34]), mode="_,Y", operand_type=OperandType.DEFAULT, variable=BRAVO),
                "bravo,Y",
            ),
            (
                Operand(value=Bytes([0x12]), mode="_,S", operand_type=OperandType.DEFAULT, variable=CHARLIE),
                ".charlie,S",
            ),
            (
                Operand(value=Bytes([0x34, 0x56]), mode="[_]", operand_type=OperandType.DEFAULT, variable=CHARLIE),
                "[!charlie]",
            ),
            (
                Operand(
                    value=Bytes([0x12]),
                    mode="_,X",
                    operand_type=OperandType.JUMPING,
                    variable=Label(name="label_d23456", value=Bytes([0x12, 0x34, 0x56])),
                ),
                ".label_d23456,X",
            ),
            (
                Operand(
                    value=Bytes([0x34, 0x56]),
                    mode="_,S",
                    operand_type=OperandType.JUMPING,
                    variable=Label(name="label_d23456", value=Bytes([0x12, 0x34, 0x56])),
                ),
                "!label_d23456,S",
            ),
            (
                Operand(
                    value=Bytes([0x12, 0x34, 0x56]),
                    mode="(_,S),Y",
                    operand_type=OperandType.JUMPING,
                    variable=Label(name="label_d23456", value=Bytes([0x12, 0x34, 0x56])),
                ),
                "(label_d23456,S),Y",
            ),
        ],
    )
    def test_str(self, operand: Operand, expected: str):
        assert str(operand) == expected

    @pytest.mark.parametrize(
        ["operand", "expected"],
        [
            (
                Operand(value=Bytes([0x12]), mode="_", operand_type=OperandType.DEFAULT),
                "Operand(value=0x12, mode='_', operand_type=OperandType.DEFAULT)",
            ),
            (
                Operand(value=Bytes([0x12, 0x34, 0x56]), mode="(_,S)", operand_type=OperandType.DEFAULT),
                "Operand(value=0x123456, mode='(_,S)', operand_type=OperandType.DEFAULT)",
            ),
            (
                Operand(value=Bytes([0x12]), mode="_", operand_type=OperandType.DEFAULT, variable=ALFA),
                "Operand(value=0x12, mode='_', operand_type=OperandType.DEFAULT, variable=Constant(name='alfa', value=0x12))",
            ),
        ],
    )
    def test_repr(self, operand: Operand, expected: str):
        assert repr(operand) == expected

    @pytest.mark.parametrize(
        ["parent_address", "length", "destination", "expected"],
        [
            (Bytes.from_address(0x123456), 3, Bytes.from_address(0x12FFFF), True),
            (Bytes.from_address(0x123456), 3, Bytes.from_address(0x00FFFF), True),
            (Bytes.from_address(0x123456), 2, Bytes.from_address(0x12FFFF), True),
            (Bytes.from_address(0x123456), 2, Bytes.from_address(0x00FFFF), False),
            (Bytes.from_address(0x123456), 1, Bytes.from_address(0x1233D8), True),
            (Bytes.from_address(0x123456), 1, Bytes.from_address(0x1233D7), False),
            (Bytes.from_address(0x123456), 1, Bytes.from_address(0x1234D7), True),
            (Bytes.from_address(0x123456), 1, Bytes.from_address(0x1234D8), False),
        ],
    )
    def test_is_destination_possible(self, parent_address: Bytes, length: int, destination: Bytes, expected: bool):
        assert Operand._is_destination_possible(parent_address, length, destination) is expected
