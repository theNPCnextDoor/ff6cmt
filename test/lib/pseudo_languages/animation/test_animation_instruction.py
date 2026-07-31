import pytest

from src import ROOT_FOLDER
from src.lib.assembly.artifact.variable import Label, Constant
from src.lib.common.bytes import Bytes
from src.lib.common.operand import Operand, OperandType
from src.lib.pseudo_languages.animation.animation_info import AnimationInfo
from src.lib.pseudo_languages.animation.animation_instruction import AnimationInstruction
from src.lib.misc.exception import OperandLengthException
from test.lib.conftest import VARIABLES, CHARLIE, ALFA
from test.lib.pseudo_languages.animation.conftest import ANIMATION_COMMANDS


animation_info = AnimationInfo(ROOT_FOLDER / "test" / "resources" / "test_animations.json")
AnimationInstruction.INFO = animation_info


class TestAnimationInstruction:

    @pytest.mark.parametrize(
        ["command", "operands", "expected"],
        [
            (
                "DUMMY",
                "$12 $34",
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x12],
                    operands=[Operand(Bytes.from_int(0x12)), Operand(Bytes.from_int(0x34))],
                ),
            ),
            (
                "DUMMY",
                "alfa delta",
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x12],
                    operands=[
                        Operand(Bytes.from_int(0x12), variable=Constant(name="alfa", value=Bytes.from_int(0x12))),
                        Operand(Bytes.from_int(0x00), variable=Constant(name="delta", value=Bytes.from_int(0x00))),
                    ],
                ),
            ),
            (
                "JUMP",
                "$1234",
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x80],
                    operands=[Operand(Bytes.from_int(0x1234), operand_type=OperandType.JUMPING)],
                ),
            ),
            (
                "VARIABLE_LENGTH",
                "!charlie $5678 $9ABC $DEF0",
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0xCC],
                    operands=[
                        Operand(Bytes.from_int(0x3456), operand_type=OperandType.JUMPING, variable=CHARLIE),
                        Operand(Bytes.from_int(0x5678), operand_type=OperandType.JUMPING),
                        Operand(Bytes.from_int(0x9ABC), operand_type=OperandType.JUMPING),
                        Operand(Bytes.from_int(0xDEF0), operand_type=OperandType.JUMPING),
                    ],
                ),
            ),
        ],
    )
    def test_from_line(self, command: str, operands: str, expected: AnimationInstruction):
        instruction = AnimationInstruction.from_line(
            command=command,
            address=Bytes.from_address(0xD20000),
            operands=operands,
            depth=0,
            threads=4,
            variables=VARIABLES,
        )
        assert instruction == expected

    @pytest.mark.parametrize(["command", "operands"], [("DUMMY", "$12"), ("VARIABLE_LENGTH", "$1234")])
    def test_from_line_but_operand_length_doesnt_match(self, command: str, operands: str):
        with pytest.raises(OperandLengthException):
            AnimationInstruction.from_line(command=command, operands=operands, depth=0, threads=4)

    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            (
                b"\x12\x12\x34\x00\x00\x00\x00",
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x12],
                    operands=[Operand(Bytes.from_int(0x12)), Operand(Bytes.from_int(0x34))],
                ),
            ),
            (
                b"\x80\x34\x12\x00\x00\x00\x00",
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x80],
                    operands=[
                        Operand(
                            Bytes.from_int(0x1234),
                            operand_type=OperandType.JUMPING,
                            variable=Label(value=Bytes.from_address(0xD21234)),
                        )
                    ],
                ),
            ),
            (
                b"\xcc\x34\x12\x56\x34\xbc\x9a\xf0\xde\x00\x00\x00\x00",
                AnimationInstruction(
                    command=AnimationInstruction.INFO.find_from_opcode(0xCC),
                    operands=[
                        Operand(
                            Bytes.from_int(0x1234),
                            operand_type=OperandType.JUMPING,
                            variable=Label(value=Bytes.from_address(0xD21234)),
                        ),
                        Operand(Bytes.from_int(0x3456), operand_type=OperandType.JUMPING, variable=CHARLIE),
                        Operand(
                            Bytes.from_int(0x9ABC),
                            operand_type=OperandType.JUMPING,
                            variable=Label(value=Bytes.from_address(0xD29ABC)),
                        ),
                        Operand(
                            Bytes.from_int(0xDEF0),
                            operand_type=OperandType.JUMPING,
                            variable=Label(value=Bytes.from_address(0xD2DEF0)),
                        ),
                    ],
                ),
            ),
        ],
    )
    def test_from_bytes(self, value: bytes, expected: AnimationInstruction):
        assert (
            AnimationInstruction.from_bytes(
                value=value, threads=4, address=Bytes.from_address(0xD20000), variables=VARIABLES
            )
            == expected
        )

    @pytest.mark.parametrize(
        ["instruction", "expected"],
        [
            (
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x12],
                    operands=[Operand(Bytes.from_int(0x12)), Operand(Bytes.from_int(0x34))],
                ),
                "  DUMMY $12 $34",
            ),
            (
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x80],
                    depth=1,
                    operands=[Operand(Bytes.from_int(0x1234), operand_type=OperandType.JUMPING)],
                ),
                "    JUMP $1234",
            ),
            (
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x80],
                    depth=1,
                    operands=[Operand(Bytes.from_int(0x1234), operand_type=OperandType.JUMPING, variable=CHARLIE)],
                ),
                "    JUMP !charlie",
            ),
            (
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0xF000], depth=2, operands=[Operand(Bytes.from_int(0x12))]
                ),
                "      SUB_00 $12",
            ),
            (
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0xF000], depth=2, operands=[Operand(Bytes.from_int(0x12), variable=ALFA)]
                ),
                "      SUB_00 alfa",
            ),
        ],
    )
    def test_to_line(self, instruction: AnimationInstruction, expected: str):
        assert instruction.to_line() == expected

    @pytest.mark.parametrize(
        ["instruction", "expected"],
        [
            (
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x12],
                    operands=[Operand(Bytes.from_int(0x12)), Operand(Bytes.from_int(0x34))],
                ),
                b"\x12\x12\x34",
            ),
            (
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0x80], depth=1, operands=[Operand(Bytes.from_int(0x1234))]
                ),
                b"\x80\x34\x12",
            ),
            (
                AnimationInstruction(
                    command=ANIMATION_COMMANDS[0xF000], depth=2, operands=[Operand(Bytes.from_int(0x12))]
                ),
                b"\xf0\x00\x12",
            ),
        ],
    )
    def test_bytes(self, instruction: AnimationInstruction, expected: bytes):
        assert bytes(instruction) == expected
