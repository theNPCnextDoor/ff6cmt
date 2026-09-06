from pathlib import Path

import pytest

from src.lib.assembly.artifact.flags import Flags
from src.lib.assembly.artifact.memory_map import MappingModes, MemoryMap
from src.lib.assembly.artifact.variable import Label, Constant
from src.lib.assembly.bytes import Bytes, Endian
from src.lib.assembly.data_structure.array import Array
from src.lib.assembly.data_structure.blob import Blob
from src.lib.assembly.data_structure.instruction.instruction import Instruction
from src.lib.assembly.data_structure.instruction.operand import Operand, OperandType
from src.lib.assembly.data_structure.pointer import Pointer
from src.lib.assembly.data_structure.string.charset import Charset
from src.lib.assembly.data_structure.string.string import String
from src.lib.assembly.data_structure.string.helpers import StringTypes, MENU_CHARSET, DESCRIPTION_CHARSET
from src.lib.assembly.script.helpers import (
    ScriptMode,
    ScriptSection,
    SubSection,
    Line,
    LineType,
    Component,
    ArrayPattern,
)
from src.lib.assembly.script.script import (
    Script,
)
from src.lib.misc.exception import LineConflict, UnrecognizedLine, IllegalRomPosition, IllegalAddress
from test import RESOURCES_FOLDER
from test.lib.assembly.conftest import TEST_BYTE, TEST_WORD, TEST_ADDRESS, ALFA, BRAVO, addr, DELTA

CONFLICTING_FILE_1 = Path(RESOURCES_FOLDER, "conflicting_file_1.asm")
CONFLICTING_FILE_2 = Path(RESOURCES_FOLDER, "conflicting_file_2.asm")
CONFLICTING_FLAGS_SCRIPT = Path(RESOURCES_FOLDER, "conflicting_flags.asm")
CONFLICTING_LABELS_SCRIPT = Path(RESOURCES_FOLDER, "conflicting_labels_script.asm")
CONFLICTING_LINES_SCRIPT = Path(RESOURCES_FOLDER, "conflicting_lines_script.asm")
DUMMY_INPUT_SCRIPT_1 = Path(RESOURCES_FOLDER, "dummy_input_script_1.asm")
DUMMY_INPUT_SCRIPT_2 = Path(RESOURCES_FOLDER, "dummy_input_script_2.asm")
DUMMY_ERROR_SCRIPT = Path(RESOURCES_FOLDER, "dummy_error_script.asm")
DUMMY_OUTPUT_SCRIPT = Path(RESOURCES_FOLDER, "dummy_output_script.asm")
DUMMY_INPUT_ROM = Path(RESOURCES_FOLDER, "dummy_input_rom.rom")
DUMMY_OUTPUT_ROM = Path(RESOURCES_FOLDER, "dummy_output_rom.sfc")
ILLEGAL_ADDRESS = Path(RESOURCES_FOLDER, "illegal_address.asm")
ILLEGAL_ROM_POSITION = Path(RESOURCES_FOLDER, "illegal_rom_position.sfc")

LABELS = [
    Label(addr(0xC00001), "start"),
    Label(addr(0xC00005), "archie"),
    Label(addr(0xC01234)),
    Label(addr(0xC0FEDC)),
    Label(addr(0xD20001), "anchor_1"),
    Label(addr(0xD23456), "rptr_1"),
    Label(addr(0xD23457), "rptr_2"),
]


class ScriptImpl:
    def __init__(self):
        self.script = Script()

        self.script.lines = [
            Line(
                raw_line="map: HiROM",
                clean_line="map: HiROM",
                address=None,
                component_info=LineType.MEMORY_MAP,
                regex_groups={"mapping_mode": "HiROM"},
                component=MemoryMap(mapping_mode=MappingModes.HI_ROM),
                filename=DUMMY_INPUT_SCRIPT_1,
            ),
            Line(
                raw_line="m = 8, x = 16",
                clean_line="m = 8, x = 16",
                address=addr(0xC00005),
                component_info=LineType.FLAGS,
                regex_groups={"m_flag": "8", "x_flag": "16"},
                component=Flags(m=8),
                filename=DUMMY_INPUT_SCRIPT_1,
            ),
            Line(
                raw_line="let alfa = $12",
                clean_line="let alfa = $12",
                address=None,
                component_info=LineType.VARIABLE_DECLARATION,
                regex_groups=None,
                component=ALFA,
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="let bravo = $1234",
                clean_line="let bravo = $1234",
                address=None,
                component_info=LineType.VARIABLE_DECLARATION,
                regex_groups=None,
                component=BRAVO,
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="let delta = $00",
                clean_line="let delta = $00",
                address=None,
                component_info=LineType.VARIABLE_DECLARATION,
                regex_groups=None,
                component=DELTA,
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="let item_dummy = $01",
                clean_line="let item_dummy = $01",
                address=None,
                component_info=LineType.VARIABLE_DECLARATION,
                regex_groups=None,
                component=Constant(Bytes([0x01]), "item_dummy"),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="let treasure_miab = $20",
                clean_line="let treasure_miab = $20",
                address=None,
                component_info=LineType.VARIABLE_DECLARATION,
                regex_groups=None,
                component=Constant(Bytes([0x20]), "treasure_miab"),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="let treasure_item = $40",
                clean_line="let treasure_item = $40",
                address=None,
                component_info=LineType.VARIABLE_DECLARATION,
                regex_groups=None,
                component=Constant(Bytes([0x40]), "treasure_item"),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="@start = $C00001",
                clean_line="@start = $C00001",
                address=addr(0xC00001),
                component_info=LineType.LABEL,
                regex_groups={"name": "start", "snes_address": "$C00001"},
                component=LABELS[0],
                filename=DUMMY_INPUT_SCRIPT_1,
            ),
            Line(
                raw_line="  ptr $1234",
                clean_line="ptr $1234",
                address=addr(0xC00001),
                component_info=LineType.POINTER,
                regex_groups={"operand": "$1234"},
                component=Pointer(operand=Operand(Bytes([0x12, 0x34])), destination=addr(0xC01234)),
                filename=DUMMY_INPUT_SCRIPT_1,
            ),
            Line(
                raw_line="  ptr $0005",
                clean_line="ptr $0005",
                address=addr(0xC00003),
                component_info=LineType.POINTER,
                regex_groups={"operand": "$0005"},
                component=Pointer(operand=Operand(Bytes([0x00, 0x05])), destination=addr(0xC00005)),
                filename=DUMMY_INPUT_SCRIPT_1,
            ),
            Line(
                raw_line="@archie = $C00005",
                clean_line="@archie = $C00005",
                address=addr(0xC00005),
                component_info=LineType.LABEL,
                regex_groups={"name": "archie", "snes_address": "$C00005"},
                component=LABELS[1],
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  TAX ; some comment",
                clean_line="TAX",
                address=addr(0xC00005),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "TAX", "operand": None},
                component=Instruction(opcode=Bytes([0xAA]), operands=None),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  LDA (alfa,X)",
                clean_line="LDA(alfa, X)",
                address=addr(0xC00006),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "LDA", "operand": "(alfa, X)"},
                component=Instruction(
                    opcode=Bytes([0xA1]),
                    operands=[Operand(TEST_BYTE, "(_,X)", variable=ALFA)],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  LDX #$FEDC",
                clean_line="LDX #$FEDC",
                address=addr(0xC00008),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "LDX", "operand": "#$FEDC"},
                component=Instruction(opcode=Bytes([0xA2]), operands=[Operand(Bytes([0xFE, 0xDC]), "#_")]),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  REP #$30",
                clean_line="REP #$30",
                address=addr(0xC0000B),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "REP", "operand": "#$30"},
                component=Instruction(opcode=Bytes([0xC2]), operands=[Operand(Bytes([0x30]), "#_")]),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  LDA #bravo",
                clean_line="LDA #bravo",
                address=addr(0xC0000D),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "LDA", "operand": "#bravo"},
                component=Instruction(
                    opcode=Bytes([0xA9]),
                    operands=[Operand(Bytes([0x12, 0x34]), "#_", variable=BRAVO)],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  LDX #$FEDC",
                clean_line="LDX #$FEDC",
                address=addr(0xC00010),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "LDX", "operand": "#$FEDC"},
                component=Instruction(opcode=Bytes([0xA2]), operands=[Operand(Bytes([0xFE, 0xDC]), "#_")]),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  SEP #$30",
                clean_line="SEP #$30",
                address=addr(0xC00013),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "SEP", "operand": "#$30"},
                component=Instruction(opcode=Bytes([0xE2]), operands=[Operand(Bytes([0x30]), "#_")]),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  LDA #.label_c0fedc",
                clean_line="LDA #.label_c0fedc",
                address=addr(0xC00015),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "LDA", "operand": "#.label_c0fedc"},
                component=Instruction(
                    opcode=Bytes([0xA9]),
                    operands=[Operand(Bytes([0xC0]), "#_", variable=LABELS[3])],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  LDX #$CC",
                clean_line="LDX #$CC",
                address=addr(0xC00017),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "LDX", "operand": "#$CC"},
                component=Instruction(opcode=Bytes([0xA2]), operands=[Operand(Bytes([0xCC]), "#_")]),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  MVP #$34,#alfa",
                clean_line="MVP #$34,#alfa",
                address=addr(0xC00019),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "MVP", "operand": "#$34,#alfa"},
                component=Instruction(
                    opcode=Bytes([0x44]),
                    operands=[Operand(Bytes([0x34]), "#_"), Operand(Bytes([0x12]), "#_", variable=ALFA)],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  JMP !archie",
                clean_line="JMP !archie",
                address=addr(0xC0001C),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "JMP", "operand": "!archie"},
                component=Instruction(
                    opcode=Bytes([0x4C]),
                    operands=[Operand(Bytes([0x00, 0x05]), "_", OperandType.JUMPING, LABELS[1])],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  BRA start ; some other comment",
                clean_line="BRA start",
                address=addr(0xC0001F),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "BRA", "operand": "start"},
                component=Instruction(
                    opcode=Bytes([0x80]),
                    operands=[Operand(Bytes([0xE0]), "_", OperandType.BRANCHING, LABELS[0])],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  bravo",
                clean_line="bravo",
                address=addr(0xC00021),
                component_info=LineType.BLOB,
                regex_groups={"operand": "bravo", "delimiter": None},
                component=Blob(operand=Operand(TEST_WORD, variable=BRAVO)),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  $5678,$FF",
                clean_line="$5678,$FF",
                address=addr(0xC00023),
                component_info=LineType.BLOB,
                regex_groups={"operand": "$5678", "delimiter": "$FF"},
                component=Blob(operand=Operand(Bytes([0x56, 0x78])), delimiter=Operand(Bytes([0xFF]))),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  $ABCD,delta",
                clean_line="$ABCD,delta",
                address=addr(0xC00026),
                component_info=LineType.BLOB,
                regex_groups={"operand": "$ABCD", "delimiter": "delta"},
                component=Blob(
                    operand=Operand(Bytes([0xAB, 0xCD])),
                    delimiter=Operand(Bytes([0x00]), variable=DELTA),
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line='  "<0x00>A<KNIFE>_",$88',
                clean_line='"<0x00>A<KNIFE>_",$88',
                address=addr(0xC00029),
                component_info=LineType.STRING,
                regex_groups={"string_type": None, "string": "<0x00>A<KNIFE>_", "delimiter": "$88"},
                component=String(
                    operand=Operand(Bytes([0x00, 0x80, 0xD8, 0xFF], endian=Endian.BIG)),
                    delimiter=Operand(Bytes([0x88])),
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line='  $AA | "a" | $BB,$FF | "b",$00',
                clean_line='$AA | "a" | $BB,$FF | "b",$00',
                address=addr(0xC0002E),
                component_info=LineType.ARRAY,
                regex_groups={},
                component=Array(
                    parts=[
                        Blob(operand=Operand(Bytes([0xAA]))),
                        String(operand=Operand(Bytes([0x9A], endian=Endian.BIG))),
                        Blob(operand=Operand(Bytes([0xBB])), delimiter=Operand(Bytes([0xFF]))),
                        String(
                            operand=Operand(Bytes([0x9B], endian=Endian.BIG)),
                            delimiter=Operand(Bytes([0x00])),
                        ),
                    ],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line='  desc "Bob<LINE><FIRE>",$00',
                clean_line='desc "Bob<LINE><FIRE>",$00',
                address=addr(0xC00034),
                component_info=LineType.STRING,
                regex_groups={"string_type": "desc", "string": "Bob<LINE><FIRE>", "delimiter": "$00"},
                component=String(
                    operand=Operand(Bytes([0x81, 0xA8, 0x9B, 0x01, 0xDC], endian=Endian.BIG)),
                    charset=DESCRIPTION_CHARSET,
                    string_type=StringTypes.DESCRIPTION,
                    delimiter=Operand(Bytes([0x00])),
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="#anchor_1",
                clean_line="#anchor_1",
                address=addr(0xC0003A),
                component_info=LineType.ANCHOR,
                regex_groups={"value": "anchor_1"},
                component=None,
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  rptr !rptr_1",
                clean_line="rptr !rptr_1",
                address=addr(0xC0003A),
                component_info=LineType.POINTER,
                regex_groups={"operand": "!rptr_1"},
                component=Pointer(
                    anchor=Operand(Bytes([0xD2, 0x00, 0x01]), variable=LABELS[4]),
                    operand=Operand(Bytes([0x34, 0x55]), variable=LABELS[5]),
                    destination=addr(0xD23456),
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  rptr !rptr_2",
                clean_line="rptr !rptr_2",
                address=addr(0xC0003C),
                component_info=LineType.POINTER,
                regex_groups={"operand": "!rptr_2"},
                component=Pointer(
                    anchor=Operand(Bytes([0xD2, 0x00, 0x01]), variable=LABELS[4]),
                    operand=Operand(Bytes([0x34, 0x56]), variable=LABELS[6]),
                    destination=addr(0xD23457),
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="m = 8, x = 8",
                clean_line="m = 8, x = 8",
                address=addr(0xC00040),
                component_info=LineType.FLAGS,
                regex_groups={"m": "8", "x": "8"},
                component=Flags(m=8, x=8),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  JSR !archie",
                clean_line="JSR !archie",
                address=addr(0xC00040),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "JSR", "operand": "!archie"},
                component=Instruction(
                    opcode=Bytes([0x20]),
                    operands=[Operand(Bytes([0x00, 0x05]), "_", OperandType.JUMPING, LABELS[1])],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  $12 | $34 | $56 | treasure_item | item_dummy",
                clean_line="$12 | $34 | $56 | treasure_item | item_dummy",
                address=addr(0xC00043),
                component_info=LineType.ARRAY,
                regex_groups={},
                component=Array(
                    parts=[
                        Blob(operand=Operand(Bytes([0x12]))),
                        Blob(operand=Operand(Bytes([0x34]))),
                        Blob(operand=Operand(Bytes([0x56]))),
                        Blob(
                            operand=Operand(Bytes([0x40]), variable=Constant(Bytes([0x40]), "treasure_item")),
                        ),
                        Blob(
                            operand=Operand(Bytes([0x01]), variable=Constant(Bytes([0x01]), "item_dummy")),
                        ),
                    ],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  $78 | $AB | $CD | treasure_miab | $01",
                clean_line="$78 | $AB | $CD | treasure_miab | $01",
                address=addr(0xC00048),
                component_info=LineType.ARRAY,
                regex_groups={},
                component=Array(
                    parts=[
                        Blob(operand=Operand(Bytes([0x78]))),
                        Blob(operand=Operand(Bytes([0x9A]))),
                        Blob(operand=Operand(Bytes([0xBC]))),
                        Blob(
                            operand=Operand(Bytes([0x20]), variable=Constant(Bytes([0x20]), "treasure_miab")),
                        ),
                        Blob(operand=Operand(Bytes([0x01]))),
                    ],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="#$D20002",
                clean_line="# $D20002",
                address=addr(0xD20002),
                component_info=LineType.ANCHOR,
                regex_groups={"value": "$D20002"},
                component=None,
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="  rptr !rptr_2",
                clean_line="rptr !rptr_2",
                address=addr(0xC0003E),
                component_info=LineType.POINTER,
                regex_groups={"operand": "!rptr_2"},
                component=Pointer(
                    anchor=Operand(Bytes([0xD2, 0x00, 0x02])),
                    operand=Operand(Bytes([0x34, 0x55]), variable=LABELS[6]),
                    destination=addr(0xD23457),
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="@anchor_1 = $D20001",
                clean_line="@anchor_1 = $D20001",
                address=addr(0xD20001),
                component_info=LineType.LABEL,
                regex_groups={"name": "anchor_1", "snes_address": "$D20001"},
                component=LABELS[4],
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="@rptr_1 = $D23456",
                clean_line="@rptr_1 = $D23456",
                address=addr(0xD23456),
                component_info=LineType.LABEL,
                regex_groups={"name": "rptr_1", "snes_address": "$D23456"},
                component=LABELS[5],
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="@rptr_2 = $D23457",
                clean_line="@rptr_2 = $D23457",
                address=addr(0xD23457),
                component_info=LineType.LABEL,
                regex_groups={"name": "rptr_2", "snes_address": "$D23457"},
                component=LABELS[6],
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
            Line(
                raw_line="m = 16, x = 16",
                clean_line="m = 16, x = 16",
                address=addr(0xD23457),
                component_info=LineType.FLAGS,
                regex_groups={"m_flag": "16", "x_flag": "16"},
                component=Flags(m=16, x=16),
                filename=DUMMY_INPUT_SCRIPT_1,
            ),
            Line(
                raw_line="  JSL archie",
                clean_line="JSL archie",
                address=addr(0xD23457),
                component_info=LineType.INSTRUCTION,
                regex_groups={"command": "JSL", "operand": "archie"},
                component=Instruction(
                    opcode=Bytes([0x22]),
                    operands=[Operand(Bytes([0xC0, 0x00, 0x05]), "_", OperandType.LONG_JUMPING, LABELS[1])],
                ),
                filename=DUMMY_INPUT_SCRIPT_2,
            ),
        ]

        self.script.memory_map = MemoryMap.from_line("HiROM")
        self.script.sort_lines()


class TestScript:

    def test_parse(self):
        script = Script.parse(DUMMY_INPUT_SCRIPT_1, DUMMY_INPUT_SCRIPT_2)

        labels = script.labels()

        assert len(labels) == 6
        assert labels[0] == Label(addr(0xC00001), "start")
        assert labels[1] == Label(addr(0xC00005), "archie")
        assert labels[2] == Label(addr(0xC0FEDC), "label_c0fedc")
        assert labels[3] == Label(value=Bytes([0xD2, 0x00, 0x01]), name="anchor_1")
        assert labels[4] == Label(value=TEST_ADDRESS, name="rptr_1")
        assert labels[5] == Label(value=Bytes([0xD2, 0x34, 0x57]), name="rptr_2")

        assert len(script.pointer_lines()) == 5
        assert script.pointer_lines()[0].component == Pointer(
            operand=Operand(Bytes([0x12, 0x34])), destination=addr(0xC01234)
        )
        assert script.pointer_lines()[1].component == Pointer(
            operand=Operand(Bytes([0x00, 0x05])), destination=addr(0xC00005)
        )
        assert script.pointer_lines()[2].component == Pointer(
            anchor=Operand(Bytes([0xD2, 0x00, 0x01]), variable=labels[3]),
            operand=Operand(Bytes([0x34, 0x55]), variable=labels[4]),
            destination=addr(0xD23456),
        )
        assert script.pointer_lines()[3].component == Pointer(
            anchor=Operand(Bytes([0xD2, 0x00, 0x01]), variable=labels[3]),
            operand=Operand(Bytes([0x34, 0x56]), variable=labels[5]),
            destination=addr(0xD23457),
        )
        assert script.pointer_lines()[4].component == Pointer(
            anchor=Operand(Bytes([0xD2, 0x00, 0x02])),
            operand=Operand(Bytes([0x34, 0x55]), variable=labels[5]),
            destination=addr(0xD23457),
        )

        assert len(script.instruction_lines()) == 14
        assert script.instruction_lines()[0].component == Instruction(opcode=Bytes([0xAA]), operands=None)
        assert script.instruction_lines()[1].component == Instruction(
            opcode=Bytes([0xA1]),
            operands=[Operand(TEST_BYTE, "(_,X)", variable=ALFA)],
        )
        assert script.instruction_lines()[2].component == Instruction(
            opcode=Bytes([0xA2]), operands=[Operand(Bytes([0xFE, 0xDC]), "#_")]
        )

        assert script.instruction_lines()[3].component == Instruction(
            opcode=Bytes([0xC2]), operands=[Operand(Bytes([0x30]), "#_")]
        )
        assert script.instruction_lines()[4].component == Instruction(
            opcode=Bytes([0xA9]),
            operands=[Operand(Bytes([0x12, 0x34]), "#_", variable=BRAVO)],
        )
        assert script.instruction_lines()[5].component == Instruction(
            opcode=Bytes([0xA2]), operands=[Operand(Bytes([0xFE, 0xDC]), "#_")]
        )

        assert script.instruction_lines()[6].component == Instruction(
            opcode=Bytes([0xE2]), operands=[Operand(Bytes([0x30]), "#_")]
        )
        assert script.instruction_lines()[7].component == Instruction(
            opcode=Bytes([0xA9]),
            operands=[Operand(Bytes([0xC0]), "#_", variable=labels[2])],
        )
        assert script.instruction_lines()[8].component == Instruction(
            opcode=Bytes([0xA2]), operands=[Operand(Bytes([0xCC]), "#_")]
        )

        assert script.instruction_lines()[9].component == Instruction(
            opcode=Bytes([0x44]),
            operands=[Operand(Bytes([0x34]), "#_"), Operand(Bytes([0x12]), "#_", variable=ALFA)],
        )
        assert script.instruction_lines()[10].component == Instruction(
            opcode=Bytes([0x4C]),
            operands=[
                Operand(
                    Bytes([0x00, 0x05]), "_", OperandType.JUMPING, Label(value=Bytes([0xC0, 0x00, 0x05]), name="archie")
                )
            ],
        )
        assert script.instruction_lines()[11].component == Instruction(
            opcode=Bytes([0x80]),
            operands=[
                Operand(Bytes([0xE0]), "_", OperandType.BRANCHING, Label(value=Bytes([0xC0, 0x00, 0x01]), name="start"))
            ],
        )
        assert script.instruction_lines()[12].component == Instruction(
            opcode=Bytes([0x20]),
            operands=[Operand(Bytes([0x00, 0x05]), "_", OperandType.JUMPING, LABELS[1])],
        )
        assert script.instruction_lines()[13].component == Instruction(
            opcode=Bytes([0x22]),
            operands=[Operand(Bytes([0xC0, 0x00, 0x05]), "_", OperandType.LONG_JUMPING, LABELS[1])],
        )

        assert len(script.blob_lines()) == 3

        assert script.blob_lines()[0].component == Blob(operand=Operand(TEST_WORD, variable=BRAVO))
        assert script.blob_lines()[1].component == Blob(
            operand=Operand(Bytes([0x56, 0x78])), delimiter=Operand(Bytes([0xFF]))
        )
        assert script.blob_lines()[2].component == Blob(
            operand=Operand(Bytes([0xAB, 0xCD])),
            delimiter=Operand(Bytes([0x00]), variable=Constant(Bytes.from_int(0), "delta")),
        )

        assert len(script.string_lines()) == 2
        assert script.string_lines()[0].component == String(
            operand=Operand(Bytes([0x00, 0x80, 0xD8, 0xFF], endian=Endian.BIG)),
            delimiter=Operand(Bytes([0x88])),
        )
        assert script.string_lines()[1].component == String(
            operand=Operand(Bytes([0x81, 0xA8, 0x9B, 0x01, 0xDC], endian=Endian.BIG)),
            delimiter=Operand(Bytes([0x00])),
            string_type=StringTypes.DESCRIPTION,
        )

        assert len(script.array_lines()) == 3
        assert len(script.array_lines()[0].component.parts) == 4
        assert script.array_lines()[0].component.parts[0] == Blob(operand=Operand(Bytes([0xAA])))
        assert script.array_lines()[0].component.parts[1] == String(operand=Operand(Bytes([0x9A])))
        assert script.array_lines()[0].component.parts[2] == Blob(
            operand=Operand(Bytes([0xBB])), delimiter=Operand(Bytes([0xFF]))
        )
        assert len(script.array_lines()[1].component.parts) == 5
        assert len(script.array_lines()[2].component.parts) == 5

        assert len(script.flags_lines()) == 4
        assert script.flags_lines()[0].component == Flags(m=8, x=16)
        assert script.flags_lines()[1].component == Flags(m=8, x=16)
        assert script.flags_lines()[2].component == Flags(m=8, x=8)
        assert script.flags_lines()[3].component == Flags(m=16, x=16)

    def test_parse_raises_error_when_line_is_unrecognized(self):
        with pytest.raises(UnrecognizedLine) as e:
            Script.parse(DUMMY_ERROR_SCRIPT)
        assert "is not recognized." in str(e.value)

    def test_parse_raises_error_when_lines_conflict(self):
        with pytest.raises(LineConflict):
            Script.parse(CONFLICTING_LINES_SCRIPT)

    def test_parse_raises_error_when_flags_conflict(self):
        with pytest.raises(LineConflict):
            Script.parse(CONFLICTING_FLAGS_SCRIPT)

    def test_parse_raises_error_when_lines_conflict_in_multiple_files(self):
        with pytest.raises(LineConflict):
            Script.parse(CONFLICTING_FILE_1, CONFLICTING_FILE_2)

    def test_assemble(self):
        with open(DUMMY_OUTPUT_ROM, "wb") as f:
            f.write(b"\x00")

        ScriptImpl().script.assemble(output_path=DUMMY_OUTPUT_ROM)
        with open(DUMMY_OUTPUT_ROM, "rb") as f:
            output = f.read()

        assert output[0x00:0x01] == b"\x00"  # Padding
        assert output[0x01:0x03] == b"\x34\x12"  # ptr !label_c01234
        assert output[0x03:0x05] == b"\x05\x00"  # ptr !archie
        assert output[0x05:0x06] == b"\xaa"  # TAX
        assert output[0x06:0x08] == b"\xa1\x12"  # LDA (alfa,X)
        assert output[0x08:0x0B] == b"\xa2\xdc\xfe"  # LDX #$FEDC
        assert output[0x0B:0x0D] == b"\xc2\x30"  # REP #$30
        assert output[0x0D:0x10] == b"\xa9\x34\x12"  # LDA #bravo
        assert output[0x10:0x13] == b"\xa2\xdc\xfe"  # LDX #!label_c0fedc
        assert output[0x13:0x15] == b"\xe2\x30"  # SEP #$30
        assert output[0x15:0x17] == b"\xa9\xc0"  # LDA #.label_c0fedc
        assert output[0x17:0x19] == b"\xa2\xcc"  # LDX #$CC
        assert output[0x19:0x1C] == b"\x44\x34\x12"  # MVP #$34,#alfa
        assert output[0x1C:0x1F] == b"\x4c\x05\x00"  # JMP !archie
        assert output[0x1F:0x21] == b"\x80\xe0"  # BRA start
        assert output[0x21:0x23] == b"\x34\x12"  # bravo
        assert output[0x23:0x26] == b"\x78\x56\xff"  # $5678,$FF
        assert output[0x26:0x29] == b"\xcd\xab\x00"  # $ABCD,delta
        assert output[0x29:0x2E] == b"\x00\x80\xd8\xff\x88"  # "<0x00>A<KNIFE>_",$88
        assert output[0x2E:0x34] == b"\xaa\x9a\xbb\xff\x9b\x00"  # $AA | "a" | $BB,$FF | "b",$00
        assert output[0x34:0x3A] == b"\x81\xa8\x9b\x01\xdc\x00"  # desc "Bob<LINE><FIRE>",$00
        assert output[0x3A:0x3C] == b"\x55\x34"  # rptr !label_d23456
        assert output[0x3C:0x3E] == b"\x56\x34"  # rptr !label_d23457
        assert output[0x3E:0x40] == b"\x55\x34"  # rptr !label_d23457
        assert output[0x40:0x43] == b"\x20\x05\x00"  # JSR !archie
        assert output[0x123457:0x12345B] == b"\x22\x05\x00\xc0"  # JSL archie

    def test_parse_raises_error_when_illegal_address(self):
        with pytest.raises(IllegalAddress):
            Script.parse(ILLEGAL_ADDRESS)

    def test_disassemble(self):
        sections = [
            ScriptSection(start=0x000001, end=0x000005, mode=ScriptMode.POINTERS),
            ScriptSection(start=0x000005, end=0x000021, mode=ScriptMode.INSTRUCTIONS, flags=Flags(m=8)),
            ScriptSection(start=0x000021, end=0x000023, mode=ScriptMode.BLOBS, length=2),
            ScriptSection(start=0x000023, end=0x000026, mode=ScriptMode.BLOBS, delimiter=b"\xff"),
            ScriptSection(start=0x000026, end=0x000029, mode=ScriptMode.BLOBS, delimiter=b"\x00"),
            ScriptSection(
                start=0x000029,
                end=0x00002E,
                mode=ScriptMode.STRINGS,
                string_type=StringTypes.MENU,
                delimiter=b"\x88",
                charset=Charset(charset=MENU_CHARSET),
            ),
            ScriptSection(
                start=0x00002E,
                end=0x000034,
                mode=ScriptMode.ARRAYS,
                sub_sections=[
                    SubSection(mode=ScriptMode.BLOBS, length=1),
                    SubSection(mode=ScriptMode.STRINGS, string_type=StringTypes.MENU, length=1),
                    SubSection(mode=ScriptMode.BLOBS, delimiter=Bytes([0xFF])),
                    SubSection(mode=ScriptMode.STRINGS, string_type=StringTypes.MENU, delimiter=Bytes([0x00])),
                ],
            ),
            ScriptSection(
                start=0x000034,
                end=0x00003A,
                mode=ScriptMode.STRINGS,
                string_type=StringTypes.DESCRIPTION,
                delimiter=b"\x00",
                charset=Charset(charset=DESCRIPTION_CHARSET),
            ),
            ScriptSection(start=0x00003A, end=0x00003E, mode=ScriptMode.POINTERS, anchor=0xD20001),
            ScriptSection(start=0x00003E, end=0x000040, mode=ScriptMode.POINTERS, anchor=0xD20002),
            ScriptSection(
                start=0x000040,
                end=0x000043,
                mode=ScriptMode.INSTRUCTIONS,
                flags=Flags(m=8, x=8),
            ),
            ScriptSection(
                start=0x000043,
                end=0x00004C,
                mode=ScriptMode.ARRAYS,
                pattern=ArrayPattern.TREASURE_CHESTS,
                sub_sections=[
                    SubSection(mode=ScriptMode.BLOBS, length=1),
                    SubSection(mode=ScriptMode.BLOBS, length=1),
                    SubSection(mode=ScriptMode.BLOBS, length=1),
                    SubSection(mode=ScriptMode.BLOBS, length=1),
                    SubSection(mode=ScriptMode.BLOBS, length=1),
                ],
                variables={
                    "items": {0x01: Constant(Bytes([0x01]), "item_dummy")},
                    "treasure_types": {
                        0x20: Constant(Bytes([0x20]), "treasure_miab"),
                        0x40: Constant(Bytes([0x40]), "treasure_item"),
                    },
                },
            ),
            ScriptSection(
                start=0x123457,
                end=0x12345A,
                mode=ScriptMode.INSTRUCTIONS,
                flags=Flags(m=16, x=16),
            ),
        ]

        test_script = ScriptImpl().script

        script = Script.disassemble(filename=DUMMY_INPUT_ROM, sections=sections, mapping_mode="HiROM")

        assert len(script.memory_map_lines()) == 1
        assert script.memory_map_lines()[0].component == MemoryMap(MappingModes.HI_ROM)

        assert len(script.pointer_lines()) == len(test_script.pointer_lines())

        for i in range(len(script.pointer_lines())):
            assert (
                script.pointer_lines()[i].component.operand.value
                == test_script.pointer_lines()[i].component.operand.value
            )

        # assert len(script.instructions()) == len(test_script.instructions())
        for i in range(len(script.instruction_lines())):
            if i >= 13:
                pass
            assert script.instruction_lines()[i].component.opcode == test_script.instruction_lines()[i].component.opcode
            if test_script.instruction_lines()[i].component.operands:
                assert len(script.instruction_lines()[i].component.operands) == len(
                    test_script.instruction_lines()[i].component.operands
                )
                for j in range(len(test_script.instruction_lines()[i].component.operands)):
                    assert (
                        script.instruction_lines()[i].component.operands[j].value
                        == test_script.instruction_lines()[i].component.operands[j].value
                    )

        assert len(script.blob_lines()) == len(test_script.blob_lines())
        for i in range(len(script.blob_lines())):
            assert script.blob_lines()[i].component.operand.value == test_script.blob_lines()[i].component.operand.value

        assert len(script.string_lines()) == len(test_script.string_lines())
        for i in range(len(script.string_lines())):
            assert (
                script.string_lines()[i].component.operand.value
                == test_script.string_lines()[i].component.operand.value
            )

        test_labels = [LABELS[0], LABELS[1], LABELS[2], LABELS[4], Label(addr(0xD20002)), LABELS[5], LABELS[6]]

        assert len(script.labels()) == len(test_labels)
        for i in range(len(script.labels())):
            assert script.labels()[i].value == test_labels[i].value

        assert len(script.array_lines()) == len(test_script.array_lines())
        for i in range(len(script.array_lines())):
            assert len(script.array_lines()[i].component.parts) == len(test_script.array_lines()[i].component.parts)
            for j in range(len(script.array_lines()[i].component.parts)):
                assert (
                    script.array_lines()[i].component.parts[j].operand
                    == test_script.array_lines()[i].component.parts[j].operand
                )
                assert (
                    script.array_lines()[i].component.parts[j].delimiter
                    == test_script.array_lines()[i].component.parts[j].delimiter
                )
                if script.array_lines()[i].component.parts[j].delimiter:
                    assert (
                        script.array_lines()[i].component.parts[j].delimiter.value
                        == test_script.array_lines()[i].component.parts[j].delimiter.value
                    )
        assert len(script.flags_lines()) == len(test_script.flags_lines())
        for i in range(len(script.flags_lines())):
            assert script.flags_lines()[i].component.m == test_script.flags_lines()[i].component.m
            assert script.flags_lines()[i].component.x == test_script.flags_lines()[i].component.x

    def test_disassemble_raises_error_when_illegal_rom_position(self):
        with open(ILLEGAL_ROM_POSITION, "wb") as f:
            f.write(b"\xea" * 0x400001)
        sections = [
            ScriptSection(start=0x400000, end=0x400001, mode=ScriptMode.INSTRUCTIONS, flags=Flags()),
        ]
        with pytest.raises(IllegalRomPosition):
            Script.disassemble(filename=ILLEGAL_ROM_POSITION, sections=sections, mapping_mode="HiROM")

    def test_dump(self):
        script_impl = ScriptImpl()
        script_impl.script.sort_lines()
        script_impl.script.dump(filename=DUMMY_OUTPUT_SCRIPT)
        with open(DUMMY_OUTPUT_SCRIPT) as f:
            script = f.read()
        assert script == (
            """map: HiROM
let alfa = $12
let bravo = $1234
let delta = $00
let item_dummy = $01
let treasure_miab = $20
let treasure_item = $40

@start = $C00001
  ptr $1234
  ptr $0005
@archie
m = 8, x = 16
  TAX
  LDA (alfa,X)
  LDX #$FEDC
  REP #$30
  LDA #bravo
  LDX #$FEDC
  SEP #$30
  LDA #.label_c0fedc
  LDX #$CC
  MVP #$34,#alfa
  JMP !archie
  BRA start
  bravo
  $5678,$FF
  $ABCD,delta
  "<0x00>A<KNIFE>_",$88
  $AA | "a" | $BB,$FF | "b",$00
  desc "Bob<LINE><FIRE>",$00

#anchor_1
  rptr !rptr_1
  rptr !rptr_2

#$D20002
  rptr !rptr_2
  JSR !archie
  $12 | $34 | $56 | treasure_item | item_dummy
  $78 | $9A | $BC | treasure_miab | $01

@label_c0fedc = $C0FEDC

@anchor_1 = $D20001

@rptr_1 = $D23456

@rptr_2 = $D23457
m = 16, x = 16
  JSL archie"""
        )

    @pytest.mark.parametrize(
        ["component", "expected"],
        [
            (Instruction(opcode=Bytes([0x00])), False),
            (Instruction(opcode=Bytes([0x00])), True),
            (Pointer(operand=Operand(Bytes([0x00, 0x00])), destination=addr(0)), True),
            (Pointer(operand=Operand(Bytes([0x00, 0x00])), destination=addr(0)), False),
            (
                Pointer(
                    operand=Operand(Bytes([0x00, 0x00])), destination=addr(0x400000), anchor=Operand(addr(0x400000))
                ),
                False,
            ),
        ],
    )
    def test_is_component_in_rom_area(self, component: Component, expected: bool):
        script = Script()
        script.memory_map = MemoryMap(MappingModes.HI_ROM)
