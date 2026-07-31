from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Self

from src.lib.common.artifact import Artifact
from src.lib.assembly.artifact.flags import Flags
from src.lib.assembly.artifact.memory_map import MemoryMap
from src.lib.assembly.artifact.variable import Label, Variable
from src.lib.common.bytes import Bytes
from src.lib.assembly.data_structure.array import Array
from src.lib.assembly.data_structure.blob import Blob
from src.lib.common.data_structure import DataStructure
from src.lib.assembly.data_structure.instruction.instruction import Instruction
from src.lib.assembly.data_structure.pointer import Pointer
from src.lib.assembly.data_structure.regex import InstructionRegex, ArtifactRegex, DataStructureRegex
from src.lib.assembly.data_structure.string.string import String, StringType
from src.lib.pseudo_languages.animation.animation_instruction import AnimationInstruction
from src.lib.pseudo_languages.animation.thread_counter import ThreadCounter
from src.lib.misc.exception import MissingSectionAttribute, UndefinedThreads

Component = Artifact | DataStructure


class ScriptMode:
    """
    Script modes allows the disassembler to correctly interpret data it reads on the ROM.
    """

    ANIMATION_INSTRUCTIONS = "AnimationInstructions"
    INSTRUCTIONS = "Instructions"
    POINTERS = "Pointers"
    BLOBS = "Blobs"
    STRINGS = "Strings"
    ARRAYS = "Arrays"


class ArrayPattern:
    """
    ArrayPatterns are used to disassemble known structures and pre-filled the Script with related variables.
    """

    TREASURE_CHESTS = "treasure_chests"


def clean_line(line: str) -> str:
    """
    Removes the white spaces and the comment of the script line, if it exists.
    :param line: The script line.
    :return: The cleaned script line.
    """
    parts = line.split("|")
    last_part = parts[-1]

    if ";" not in last_part:
        return line.strip()

    match = re.match(r'[^";]*("[^"]+"[^";]*)?(?P<comment>;\.*)?', last_part)
    if match and match.group("comment"):
        line = line[: match.start("comment")]

    return line.strip()


class ScriptSection:
    """
    Script sections are used to define how to interpret a specific section of the ROM when disassembling.
    """

    def __init__(
        self,
        start: int,
        end: int,
        mode: ScriptMode,
        variables: dict[str, dict[int, Variable]] | None = None,
        **attributes: Any,
    ):
        self.variables = variables or dict()
        self.start = start
        self.end = end
        self.mode = mode
        self.attributes = attributes

    def __eq__(self, other: Self) -> bool:
        return self.start == other.start

    def __lt__(self, other: Self) -> bool:
        return self.start < other.start


class SubSection:
    """
    Subsections are used to define each individual subsection inside a blob group.
    """

    def __init__(
        self,
        mode: ScriptMode,
        length: int | None = None,
        delimiter: Bytes | None = None,
        string_type: StringType | None = None,
    ):
        """
        :param mode: The script mode of the subsection.
        :param length: An integer. If defined, will be used to determine the number of bytes shall be contained in the
        subsection.
        :param delimiter: A specific byte. If defined, will be used to determine the end of the blob.
        :param string_type: For String subsections. Indicates the type of string to disassemble.
        :raises MissingSectionAttribute: Raised when neither the length nor the delimiter is used.
        """
        if length is None and delimiter is None:
            message = "Please provide either the length or the delimiter."
            logging.error(message)
            raise MissingSectionAttribute(message)
        self.mode = mode
        self.length = length
        self.delimiter = delimiter
        self.string_type = string_type


@dataclass
class ComponentInfo:
    """
    ComponentInfos are named tuples that assemble info about a particular type of Component.
    """

    name: str
    cls: type[Component] | None
    regex: str | None
    regex_groups: tuple[str, ...]


class LineType:
    """
    LineType contains all the ComponentInfos.
    """

    ANCHOR = ComponentInfo("Anchor", None, ArtifactRegex.ANCHOR, ("value",))
    ANIMATION_INSTRUCTION = ComponentInfo(
        "AnimationInstruction", AnimationInstruction, DataStructureRegex.ANIMATION_INSTRUCTION, ("command", "operands")
    )
    ARRAY = ComponentInfo("Array", Array, DataStructureRegex.ARRAY, tuple())
    BLOB = ComponentInfo("Blob", Blob, DataStructureRegex.BLOB, ("operand", "delimiter"))
    FLAGS = ComponentInfo("Flags", Flags, ArtifactRegex.FLAGS, ("m_flag", "x_flag"))
    INSTRUCTION = ComponentInfo("Instruction", Instruction, InstructionRegex.INSTRUCTION, ("command", "operand"))
    LABEL = ComponentInfo("Label", Label, ArtifactRegex.LABEL, ("name", "snes_address"))
    MEMORY_MAP = ComponentInfo("MemoryMap", MemoryMap, ArtifactRegex.MEMORY_MAP, ("mapping_mode",))
    POINTER = ComponentInfo("Pointer", Pointer, DataStructureRegex.POINTER, ("operand",))
    STRING = ComponentInfo("String", String, DataStructureRegex.STRING, ("string_type", "string", "delimiter"))
    THREAD_COUNTER = ComponentInfo("ThreadCounter", ThreadCounter, ArtifactRegex.THREAD_COUNTER, ("threads",))
    VARIABLE_DECLARATION = ComponentInfo(
        "Variable", Variable, ArtifactRegex.VARIABLE_DECLARATION, ("length", "name", "operand")
    )

    @classmethod
    def list(cls) -> list[ComponentInfo]:
        """
        :return: Every ComponentInfo as a list.
        """
        return [line_info for line_info in cls.__dict__.values() if isinstance(line_info, ComponentInfo)]


@dataclass
class Line:
    """
    A Line contains all the info related to a script line.
    """

    filename: str | Path | None = None
    raw_line: str | None = None
    clean_line: str | None = None
    address: Bytes | None = None
    component_info: ComponentInfo | None = None
    regex_groups: dict[str, str | None] | None = None
    component: Component | None = None

    def __repr__(self) -> str:
        raw_line = self.raw_line.strip("\n")
        return (
            "Line("
            f"raw_line='{raw_line}', "
            f"clean_line='{self.clean_line}', "
            f"address=0x{self.address}, "
            f"component_info={'ComponentInfo.' + self.component_info.name if self.component_info else None}, "
            f"regex_groups={self.regex_groups}, "
            f"component={repr(self.component)}, "
            f"filename='{self.filename}', "
            ")"
        )

    def __eq__(self, other: Self) -> bool:
        return self.component == other.component and self.address == other.address

    @classmethod
    def from_component(cls, component: Component, address: Bytes | None = None) -> Self:
        """
        Converts a Component into a Line.
        :param address:
        :param component: An Artifact or DataStructure.
        :return: A Line.
        :note: The Line being returned won't have all its fields filled. This method is used mostly to wrap a Component
        in a line.
        """
        line = cls()
        line.component = component
        line.address = address
        line_types = [
            line_type for line_type in LineType.list() if line_type.cls and type(line.component) is line_type.cls
        ]
        if line_types:
            line.component_info = line_types[0]
        line.raw_line = line.component.to_line()
        return line


def find_closest_n_threads(threads_dict: dict[int, int], cursor: int) -> int:
    are_before_cursor = [k for k, v in threads_dict.items() if v <= cursor]
    if not are_before_cursor:
        message = f"Can't find the number of threads set prior to address 0x{str(Bytes.from_address(cursor))}."
        logging.error(message)
        raise UndefinedThreads(message)
    return are_before_cursor[-1]
