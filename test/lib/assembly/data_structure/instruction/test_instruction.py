import pytest

from src.lib.assembly.artifact.flags import Flags
from src.lib.assembly.data_structure.instruction.instruction import Instruction
from src.lib.common.operand import Operand, OperandType
from src.lib.assembly.artifact.variable import Label
from src.lib.common.bytes import Bytes
from src.lib.misc.exception import NoCandidateException
from test.lib.conftest import (
    TEST_BYTE,
    TEST_WORD,
    TEST_ADDRESS,
    VARIABLES,
    CHARLIE,
    ALFA,
    DELTA,
    BRAVO,
    DEFAULT_ADDRESS,
    addr,
)


class TestInstruction:
    @pytest.mark.parametrize(
        ["command", "operand", "flags", "opcode", "operands"],
        [
            ("BRK", None, Flags(), Bytes([0x00]), list()),
            ("COP", "#$FF", Flags(), Bytes([0x02]), [Operand(Bytes([0xFF]), "#_")]),
            ("COP", "#alfa", Flags(), Bytes([0x02]), [Operand(TEST_BYTE, "#_", OperandType.DEFAULT, ALFA)]),
            ("COP", "#.charlie", Flags(), Bytes([0x02]), [Operand(Bytes([0xD2]), "#_", OperandType.DEFAULT, CHARLIE)]),
            ("MVP", "#$ED,#$CB", Flags(), Bytes([0x44]), [Operand(Bytes([0xED]), "#_"), Operand(Bytes([0xCB]), "#_")]),
            (
                "MVP",
                "#.charlie,#delta",
                Flags(),
                Bytes([0x44]),
                [
                    Operand(Bytes([0xD2]), "#_", OperandType.DEFAULT, CHARLIE),
                    Operand(Bytes([0x00]), "#_", OperandType.DEFAULT, DELTA),
                ],
            ),
            ("ORA", "$8877,Y", Flags(), Bytes([0x19]), [Operand(Bytes([0x88, 0x77]), "_,Y")]),
            ("ORA", "bravo,Y", Flags(), Bytes([0x19]), [Operand(TEST_WORD, "_,Y", OperandType.DEFAULT, BRAVO)]),
            (
                "ORA",
                "!charlie,Y",
                Flags(),
                Bytes([0x19]),
                [Operand(Bytes([0x34, 0x56]), "_,Y", OperandType.DEFAULT, CHARLIE)],
            ),
            ("BRA", "$05", Flags(), Bytes([0x80]), [Operand(Bytes([0x05]), "_", OperandType.BRANCHING)]),
            ("BRA", "charlie", Flags(), Bytes([0x80]), [Operand(Bytes([0xFE]), "_", OperandType.BRANCHING, CHARLIE)]),
            ("BRL", "$0005", Flags(), Bytes([0x82]), [Operand(Bytes([0x00, 0x05]), "_", OperandType.LONG_BRANCHING)]),
            (
                "BRL",
                "charlie",
                Flags(),
                Bytes([0x82]),
                [Operand(Bytes([0xFF, 0xFD]), "_", OperandType.LONG_BRANCHING, CHARLIE)],
            ),
            ("JMP", "$1234", Flags(), Bytes([0x4C]), [Operand(TEST_WORD, "_", OperandType.JUMPING)]),
            (
                "JMP",
                "!charlie",
                Flags(),
                Bytes([0x4C]),
                [Operand(Bytes([0x34, 0x56]), "_", OperandType.JUMPING, CHARLIE)],
            ),
            (
                "JML",
                "$D23456",
                Flags(),
                Bytes([0x5C]),
                [Operand(Bytes([0xD2, 0x34, 0x56]), "_", OperandType.LONG_JUMPING)],
            ),
            (
                "JML",
                "charlie",
                Flags(),
                Bytes([0x5C]),
                [Operand(TEST_ADDRESS, "_", OperandType.LONG_JUMPING, CHARLIE)],
            ),
        ],
        ids=[
            "No operand",
            "Operand has 1 byte and no variable",
            "Operand has 1 byte and a variable",
            "Operand has 1 byte and a label",
            "Moving block instruction and none of the operands have a variable",
            "Moving block instruction and both operands have a variable",
            "Operand has 2 bytes and no variable",
            "Operand has 2 bytes and a variable",
            "Operand has 2 bytes and a label",
            "OperandType is branching and operand has no label",
            "OperandType is branching and operand has a label",
            "OperandType is long branching and operand has no label",
            "OperandType is long branching and operand has a label",
            "OperandType is jumping and operand has no label",
            "OperandType is jumping and operand has a label",
            "OperandType is long jumping and operand has no label",
            "OperandType is long jumping and operand has a label",
        ],
    )
    def test_from_line(self, command: str, operand: str | None, flags: Flags, opcode: Bytes, operands: list[Operand]):
        instruction = Instruction.from_line(command, TEST_ADDRESS, flags, operand, VARIABLES)
        assert instruction.opcode == opcode
        assert instruction.operands == operands

    @pytest.mark.parametrize(
        ["value", "expected", "flags", "address"],
        [
            (
                b"\x00",
                Instruction(opcode=Bytes([0x00]), operands=list()),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x01\x02",
                Instruction(opcode=Bytes([0x01]), operands=[Operand(Bytes([0x02]), "(_,X)")]),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x09\x03\x04",
                Instruction(opcode=Bytes([0x09]), operands=[Operand(Bytes([0x04, 0x03]), "#_")]),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x09\x05",
                Instruction(opcode=Bytes([0x09]), operands=[Operand(Bytes([0x05]), "#_")]),
                Flags(m=8),
                DEFAULT_ADDRESS,
            ),
            (
                b"\xa0\x08",
                Instruction(opcode=Bytes([0xA0]), operands=[Operand(Bytes([0x08]), "#_")]),
                Flags(x=8),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x1f\x06\x07\xc8",
                Instruction(
                    opcode=Bytes([0x1F]),
                    operands=[
                        Operand(
                            Bytes([0xC8, 0x07, 0x06]),
                            "_,X",
                            variable=Label(addr(0xC80706), "label_c80706"),
                        )
                    ],
                ),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x44\x09\x0a",
                Instruction(
                    opcode=Bytes([0x44]),
                    operands=[Operand(Bytes([0x09]), "#_"), Operand(Bytes([0x0A]), "#_")],
                ),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x80\x0b",
                Instruction(
                    opcode=Bytes([0x80]),
                    operands=[
                        Operand(Bytes([0x0B]), "_", OperandType.BRANCHING, Label(addr(0xC0000D), "label_c0000d"))
                    ],
                ),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x82\x0c\x0d",
                Instruction(
                    opcode=Bytes([0x82]),
                    operands=[
                        Operand(
                            Bytes([0x0D, 0x0C]),
                            "_",
                            OperandType.LONG_BRANCHING,
                            Label(addr(0xC00D0F), "label_c00d0f"),
                        )
                    ],
                ),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\xdc\x0e\x0f",
                Instruction(
                    opcode=Bytes([0xDC]),
                    operands=[
                        Operand(
                            Bytes([0x0F, 0x0E]),
                            "[_]",
                            OperandType.JUMPING,
                            Label(addr(0xC00F0E), "label_c00f0e"),
                        )
                    ],
                ),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x22\x10\x11\xd2",
                Instruction(
                    opcode=Bytes([0x22]),
                    operands=[
                        Operand(
                            Bytes([0xD2, 0x11, 0x10]),
                            "_",
                            OperandType.LONG_JUMPING,
                            Label(addr(0xD21110), "label_d21110"),
                        )
                    ],
                ),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x1f\x56\x34\xd2",
                Instruction(
                    opcode=Bytes([0x1F]),
                    operands=[Operand(Bytes([0xD2, 0x34, 0x56]), "_,X", OperandType.DEFAULT, variable=CHARLIE)],
                ),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x4c\x56\x34",
                Instruction(
                    opcode=Bytes([0x4C]),
                    operands=[Operand(Bytes([0x34, 0x56]), "_", OperandType.JUMPING, variable=CHARLIE)],
                ),
                Flags(),
                addr(0xD20000),
            ),
            (
                b"\x5c\x56\x34\xd2",
                Instruction(
                    opcode=Bytes([0x5C]),
                    operands=[Operand(Bytes([0xD2, 0x34, 0x56]), "_", OperandType.LONG_JUMPING, variable=CHARLIE)],
                ),
                Flags(),
                DEFAULT_ADDRESS,
            ),
            (
                b"\x80\x04",
                Instruction(
                    opcode=Bytes([0x80]),
                    operands=[Operand(Bytes([0x04]), "_", OperandType.BRANCHING, CHARLIE)],
                ),
                Flags(),
                addr(0xD23450),
            ),
            (
                b"\x82\x03\x00",
                Instruction(
                    opcode=Bytes([0x82]),
                    operands=[Operand(Bytes([0x00, 0x03]), "_", OperandType.LONG_BRANCHING, CHARLIE)],
                ),
                Flags(),
                addr(0xD23450),
            ),
        ],
        ids=[
            "No operand",
            "Operand has 1 byte",
            "Operand has 2 bytes",
            "Operand has 1 byte due to m flag",
            "Operand has 1 byte due to x flag",
            "Operand has 3 bytes and no pre-existing label",
            "Moving block instruction and no pre-existing label",
            "Branching instruction and no pre-existing label",
            "Long branching instruction and no pre-existing label",
            "Jumping instruction and no pre-existing label",
            "Long jumping instruction and no pre-existing label",
            "Operand has 3 bytes and pre-existing label",
            "Branching instruction with pre-existing label",
            "Long branching instruction with pre-existing label",
            "Jumping instruction with pre-existing label",
            "Long jumping instruction with pre-existing label",
        ],
    )
    def test_from_bytes(self, value: bytes, expected: Instruction, flags: Flags, address: Bytes):
        instruction = Instruction.from_bytes(value=value, flags=flags, address=address, variables=VARIABLES)
        assert instruction == expected

    @pytest.mark.parametrize(
        ["expected", "instruction"],
        [
            (b"\x00", Instruction(opcode=Bytes([0x00]), operands=list())),
            (
                b"\x01\x02",
                Instruction(opcode=Bytes([0x01]), operands=[Operand(Bytes([0x02]), "(_,X)")]),
            ),
            (
                b"\x09\x03\x04",
                Instruction(opcode=Bytes([0x09]), operands=[Operand(Bytes([0x04, 0x03]), "#_")]),
            ),
            (
                b"\xa0\x06\x07",
                Instruction(opcode=Bytes([0xA0]), operands=[Operand(Bytes([0x07, 0x06]), "#_")]),
            ),
            (
                b"\xa0\x08",
                Instruction(opcode=Bytes([0xA0]), operands=[Operand(Bytes([0x08]), "#_")]),
            ),
            (
                b"\x1f\x06\x07\xc8",
                Instruction(
                    opcode=Bytes([0x1F]),
                    operands=[
                        Operand(
                            Bytes([0xC8, 0x07, 0x06]),
                            "_,X",
                            variable=Label(addr(0xC80706), "label_c80706"),
                        )
                    ],
                ),
            ),
            (
                b"\x44\x09\x0a",
                Instruction(
                    opcode=Bytes([0x44]), operands=[Operand(Bytes([0x09]), "#_"), Operand(Bytes([0x0A]), "#_")]
                ),
            ),
            (
                b"\x80\x0b",
                Instruction(
                    opcode=Bytes([0x80]),
                    operands=[Operand(Bytes([0x0B]), "_", OperandType.BRANCHING, Label(addr(0x0D), "label_c0000d"))],
                ),
            ),
            (
                b"\x82\x0c\x0d",
                Instruction(
                    opcode=Bytes([0x82]),
                    operands=[
                        Operand(
                            Bytes([0x0D, 0x0C]),
                            "_",
                            OperandType.LONG_BRANCHING,
                            Label(addr(0x0D0F), "label_c00d0f"),
                        )
                    ],
                ),
            ),
            (
                b"\xdc\x0e\x0f",
                Instruction(
                    opcode=Bytes([0xDC]),
                    operands=[
                        Operand(
                            Bytes([0x0F, 0x0E]),
                            "[_]",
                            OperandType.JUMPING,
                            Label(addr(0x0F0E), "label_c00f0e"),
                        )
                    ],
                ),
            ),
            (
                b"\x22\x10\x11",
                Instruction(
                    opcode=Bytes([0x22]),
                    operands=[
                        Operand(
                            Bytes([0x11, 0x10]),
                            "_",
                            OperandType.LONG_JUMPING,
                            Label(addr(0x1110), "label_c01110"),
                        )
                    ],
                ),
            ),
            (
                b"\x1f\x56\x34\xd2",
                Instruction(
                    opcode=Bytes([0x1F]),
                    operands=[Operand(Bytes([0xD2, 0x34, 0x56]), "_,X", OperandType.DEFAULT, variable=CHARLIE)],
                ),
            ),
            (
                b"\x4c\x56\x34",
                Instruction(
                    opcode=Bytes([0x4C]),
                    operands=[Operand(Bytes([0x34, 0x56]), "_", OperandType.JUMPING, variable=CHARLIE)],
                ),
            ),
            (
                b"\x5c\x56\x34\xd2",
                Instruction(
                    opcode=Bytes([0x5C]),
                    operands=[Operand(Bytes([0xD2, 0x34, 0x56]), "_", OperandType.LONG_JUMPING, variable=CHARLIE)],
                ),
            ),
            (
                b"\x80\x04",
                Instruction(
                    opcode=Bytes([0x80]),
                    operands=[Operand(Bytes([0x04]), "_", OperandType.BRANCHING, CHARLIE)],
                ),
            ),
            (
                b"\x82\x03\x00",
                Instruction(
                    opcode=Bytes([0x82]),
                    operands=[Operand(Bytes([0x00, 0x03]), "_", OperandType.LONG_BRANCHING, CHARLIE)],
                ),
            ),
        ],
        ids=[
            "No operand",
            "Operand has 1 byte",
            "Operand has 2 bytes",
            "Operand has 1 byte due to m flag",
            "Operand has 1 byte due to x flag",
            "Operand has 3 bytes and no pre-existing label",
            "Moving block instruction and no pre-existing label",
            "Branching instruction and no pre-existing label",
            "Long branching instruction and no pre-existing label",
            "Jumping instruction and no pre-existing label",
            "Long jumping instruction and no pre-existing label",
            "Operand has 3 bytes and pre-existing label",
            "Branching instruction with pre-existing label",
            "Long branching instruction with pre-existing label",
            "Jumping instruction with pre-existing label",
            "Long jumping instruction with pre-existing label",
        ],
    )
    def test_bytes(self, instruction: Instruction, expected: bytes):
        assert bytes(instruction) == expected

    @pytest.mark.parametrize(
        ["command", "mode", "length", "flags", "opcode"],
        [
            ("BRK", "", 0, Flags(), Bytes([0x00])),
            ("COP", "#_", 1, Flags(), Bytes([0x02])),
            ("EOR", "_", 2, Flags(), Bytes([0x4D])),
            ("MVP", "#_,#_", 2, Flags(), Bytes([0x44])),
            ("ORA", "#_", 2, Flags(m=16), Bytes([0x09])),
            ("LDY", "#_", 2, Flags(x=16), Bytes([0xA0])),
            ("ORA", "_", 3, Flags(), Bytes([0x0F])),
        ],
        ids=[
            "No operand",
            "Operand has 1 byte",
            "Operand has 2 bytes",
            "Moving block instruction",
            "Operand has 2 bytes due to m flag",
            "Operand has 2 bytes due to x flag",
            "Operand has 3 bytes",
        ],
    )
    def test_find_opcode(self, command: str, mode: str, length: int, flags: Flags, opcode: Bytes):
        assert Instruction._find_opcode(command=command, mode=mode, length=length, flags=flags) == opcode

    @pytest.mark.parametrize(
        ["command", "mode", "length", "flags"],
        [
            ("BRK", "_", 1, Flags()),
            ("BRK", "#$_", 1, Flags(m=8)),
            ("MVP", "$_,$_", 2, Flags(x=8)),
            ("TSB", "$_", 4, Flags()),
            ("ROR", "$_", 0, Flags()),
            ("ORA", "$_,S", 2, Flags()),
            ("ORA", "#$_", 1, Flags(m=16)),
            ("ORA", "#$_", 2, Flags(m=8)),
            ("LDY", "#$_", 1, Flags(x=16)),
            ("LDY", "#$_", 2, Flags(x=8)),
        ],
        ids=[
            "Forbidden length for command with mode _",
            "Forbidden mode for command",
            "Non-existing mode",
            "Length is 4",
            "Length is 0 when mode is not _",
            "Bad length for command when mode is not _",
            "Bad length when flag m is false",
            "Bad length when flag m is true",
            "Bad length when flag x is false",
            "Bad length when flag x is true",
        ],
    )
    def test_find_opcode_but_raises_no_candidate_exception(self, command: str, mode: str, length: int, flags: Flags):
        with pytest.raises(NoCandidateException):
            Instruction._find_opcode(command=command, mode=mode, length=length, flags=flags)

    @pytest.mark.parametrize(
        ["instruction", "is_flag_setter"],
        [
            (Instruction(opcode=Bytes([0x00]), operands=None), False),
            (Instruction(opcode=Bytes([0xC3]), operands=[Operand(Bytes([0x13]))]), False),
            (Instruction(opcode=Bytes([0xC2]), operands=[Operand(Bytes([0x13]))]), True),
            (Instruction(opcode=Bytes([0xE2]), operands=[Operand(Bytes([0x13]))]), True),
        ],
        ids=[
            "BRK is not a flag setter and has no operand",
            "CMP is not a flag setter and has an operand",
            "REP is a flag setter",
            "SEP is a flag setter",
        ],
    )
    def test_is_flag_setter(self, instruction: Instruction, is_flag_setter: bool):
        assert instruction.is_flag_setter() == is_flag_setter

    @pytest.mark.parametrize(
        ["instruction", "_input", "output"],
        [
            (Instruction(opcode=Bytes([0xC2]), operands=[Operand(Bytes([0x00]))]), Flags(m=8, x=8), Flags(m=8, x=8)),
            (Instruction(opcode=Bytes([0xC2]), operands=[Operand(Bytes([0x10]))]), Flags(m=8, x=8), Flags(m=8, x=16)),
            (Instruction(opcode=Bytes([0xC2]), operands=[Operand(Bytes([0x20]))]), Flags(m=8, x=8), Flags(m=16, x=8)),
            (Instruction(opcode=Bytes([0xC2]), operands=[Operand(Bytes([0x3F]))]), Flags(m=8, x=8), Flags(m=16, x=16)),
            (
                Instruction(opcode=Bytes([0xE2]), operands=[Operand(Bytes([0x00]))]),
                Flags(m=16, x=16),
                Flags(m=16, x=16),
            ),
            (
                Instruction(opcode=Bytes([0xE2]), operands=[Operand(Bytes([0x10]))]),
                Flags(m=16, x=16),
                Flags(m=16, x=8),
            ),
            (
                Instruction(opcode=Bytes([0xE2]), operands=[Operand(Bytes([0x20]))]),
                Flags(m=16, x=16),
                Flags(m=8, x=16),
            ),
            (Instruction(opcode=Bytes([0xE2]), operands=[Operand(Bytes([0x3F]))]), Flags(m=16, x=16), Flags(m=8, x=8)),
        ],
        ids=[
            "Set no flags",
            "Set x flag",
            "Set m flag",
            "Set both flags",
            "Reset no flags",
            "Reset x flag",
            "Reset m flag",
            "Reset both flags",
        ],
    )
    def test_set_flags(self, instruction: Instruction, _input: Flags, output: Flags):
        assert instruction.set_flags(_input) == output

    @pytest.mark.parametrize(
        ["expected", "instruction"],
        [
            ("BRK", Instruction(opcode=Bytes([0x00]))),
            ("COP #$FF", Instruction(opcode=Bytes([0x02]), operands=[Operand(Bytes([0xFF]), "#_")])),
            (
                "COP #alfa",
                Instruction(opcode=Bytes([0x02]), operands=[Operand(TEST_BYTE, "#_", OperandType.DEFAULT, ALFA)]),
            ),
            (
                "COP #.charlie",
                Instruction(opcode=Bytes([0x02]), operands=[Operand(TEST_BYTE, "#_", OperandType.DEFAULT, CHARLIE)]),
            ),
            (
                "MVP #$ED,#$CB",
                Instruction(
                    opcode=Bytes([0x44]), operands=[Operand(Bytes([0xED]), "#_"), Operand(Bytes([0xCB]), "#_")]
                ),
            ),
            (
                "MVP #.charlie,#delta",
                Instruction(
                    opcode=Bytes([0x44]),
                    operands=[
                        Operand(TEST_BYTE, "#_", OperandType.DEFAULT, CHARLIE),
                        Operand(Bytes([0xFF]), "#_", OperandType.DEFAULT, DELTA),
                    ],
                ),
            ),
            ("ORA $8877,Y", Instruction(opcode=Bytes([0x19]), operands=[Operand(Bytes([0x88, 0x77]), "_,Y")])),
            (
                "ORA bravo,Y",
                Instruction(opcode=Bytes([0x19]), operands=[Operand(TEST_WORD, "_,Y", OperandType.DEFAULT, BRAVO)]),
            ),
            (
                "ORA !charlie,Y",
                Instruction(
                    opcode=Bytes([0x19]), operands=[Operand(Bytes([0x34, 0x56]), "_,Y", OperandType.DEFAULT, CHARLIE)]
                ),
            ),
            (
                "BRA $05",
                Instruction(opcode=Bytes([0x80]), operands=[Operand(Bytes([0x05]), "_", OperandType.BRANCHING)]),
            ),
            (
                "BRA charlie",
                Instruction(
                    opcode=Bytes([0x80]), operands=[Operand(Bytes([0xFE]), "_", OperandType.BRANCHING, CHARLIE)]
                ),
            ),
            (
                "BRL $0005",
                Instruction(
                    opcode=Bytes([0x82]), operands=[Operand(Bytes([0x00, 0x05]), "_", OperandType.LONG_BRANCHING)]
                ),
            ),
            (
                "BRL charlie",
                Instruction(
                    opcode=Bytes([0x82]),
                    operands=[Operand(Bytes([0xFF, 0xFD]), "_", OperandType.LONG_BRANCHING, CHARLIE)],
                ),
            ),
            ("JMP $1234", Instruction(opcode=Bytes([0x4C]), operands=[Operand(TEST_WORD, "_", OperandType.JUMPING)])),
            (
                "JMP !charlie",
                Instruction(
                    opcode=Bytes([0x4C]), operands=[Operand(Bytes([0x34, 0x56]), "_", OperandType.JUMPING, CHARLIE)]
                ),
            ),
            (
                "JML $D23456",
                Instruction(opcode=Bytes([0x5C]), operands=[Operand(TEST_ADDRESS, "_", OperandType.LONG_JUMPING)]),
            ),
            (
                "JML charlie",
                Instruction(
                    opcode=Bytes([0x5C]), operands=[Operand(TEST_ADDRESS, "_", OperandType.LONG_JUMPING, CHARLIE)]
                ),
            ),
        ],
        ids=[
            "No operand",
            "Operand has 1 byte and no variable",
            "Operand has 1 byte and a variable",
            "Operand has 1 byte and a label",
            "Moving block instruction and none of the operands have a variable",
            "Moving block instruction and both operands have a variable",
            "Operand has 2 bytes and no variable",
            "Operand has 2 bytes and a variable",
            "Operand has 2 bytes and a label",
            "OperandType is branching and operand has no label",
            "OperandType is branching and operand has a label",
            "OperandType is long branching and operand has no label",
            "OperandType is long branching and operand has a label",
            "OperandType is jumping and operand has no label",
            "OperandType is jumping and operand has a label",
            "OperandType is long jumping and operand has no label",
            "OperandType is long jumping and operand has a label",
        ],
    )
    def test_str(self, instruction: Instruction, expected: str):
        assert str(instruction) == expected

    @pytest.mark.parametrize(
        ["expected", "instruction"],
        [
            (
                "Instruction(as_str='BRK', as_bytes=b'\\x00', as_hexa=0x00)",
                Instruction(opcode=Bytes([0x00])),
            ),
            (
                "Instruction(as_str='COP #$FF', as_bytes=b'\\x02\\xff', as_hexa=0x02FF)",
                Instruction(opcode=Bytes([0x02]), operands=[Operand(Bytes([0xFF]), "#_")]),
            ),
            (
                "Instruction(as_str='COP #alfa', as_bytes=b'\\x02\\x12', as_hexa=0x0212, operand_var_1=Constant(name='alfa', value=0x12))",
                Instruction(opcode=Bytes([0x02]), operands=[Operand(TEST_BYTE, "#_", OperandType.DEFAULT, ALFA)]),
            ),
            (
                "Instruction(as_str='MVP #.charlie,#delta', as_bytes=b'D\\xd2\\x00', as_hexa=0x44D200, operand_var_1=Label(name='charlie', value=0xD23456), operand_var_2=Constant(name='delta', value=0x00))",
                Instruction(
                    opcode=Bytes([0x44]),
                    operands=[
                        Operand(Bytes([0xD2]), "#_", OperandType.DEFAULT, CHARLIE),
                        Operand(Bytes([0x00]), "#_", OperandType.DEFAULT, DELTA),
                    ],
                ),
            ),
        ],
        ids=[
            "No operand",
            "Operand has 1 byte and no variable",
            "Operand has 1 byte and a variable",
            "Moving block instruction and both operands have a variable",
        ],
    )
    def test_repr(self, instruction: Instruction, expected: str):
        assert repr(instruction) == expected

    @pytest.mark.parametrize(
        ["instruction", "address", "expected"],
        [
            (Instruction(opcode=Bytes([0xAA])), None, "  TAX"),
            (Instruction(opcode=Bytes([0xAA])), addr(0xC01234), "  TAX ; $C01234"),
            (Instruction(opcode=Bytes([0xA9]), operands=[Operand(TEST_WORD, "#_")]), None, "  LDA #$1234"),
            (
                Instruction(
                    opcode=Bytes([0x44]), operands=[Operand(TEST_BYTE, "#_"), Operand(Bytes.from_int(0x34), "#_")]
                ),
                None,
                "  MVP #$12,#$34",
            ),
        ],
    )
    def test_to_line(self, instruction: Instruction, address: Bytes | None, expected: str):
        assert instruction.to_line(show_address=address is not None, address=address) == expected

    @pytest.mark.parametrize(
        ["command", "operand", "length"],
        [
            ("BRK", None, 1),
            ("MVP", "#$12,#alfa", 3),
            ("BRA", "$12", 2),
            ("BRL", "$1234", 3),
            ("LDA", "$12", 2),
            ("LDA", "$1234", 3),
            ("LDA", "$123456", 4),
            ("LDA", "alfa", 2),
            ("LDA", "bravo", 3),
            ("LDA", "charlie", 4),
            ("LDA", ".charlie", 2),
            ("LDA", "!charlie", 3),
            ("LDA", "unrecognized_label", 4),
        ],
    )
    def test_find_length(self, command: str, operand: str, length: int):
        Instruction.find_length(command, operand, VARIABLES)
