from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Self, BinaryIO

from src.lib.assembly.artifact.memory_map import MemoryMap, AreaTypes
from src.lib.assembly.artifact.variable import Label, Constant
from src.lib.assembly.artifact.variables import Variables
from src.lib.common.operand import Operand
from src.lib.common.script.cursor import Cursor
from src.lib.common.script.helpers import (
    ScriptMode,
    ScriptSection,
    Line,
    LineType,
    clean_line,
    ArrayPattern,
)
from src.lib.pseudo_languages.animation.animation_instruction import AnimationInstruction
from src.lib.pseudo_languages.animation.animation_settings import AnimationSettings
from src.lib.pseudo_languages.animation.thread_counter import ThreadCounter
from src.lib.misc.exception import (
    MissingSectionAttribute,
    LineConflict,
    UnrecognizedLine,
    UnrecognizedSubsectionMode,
    UndefinedFlags,
    MismatchedMappingModes,
    IllegalAddress,
)
from src.lib.assembly.data_structure.blob import Blob
from src.lib.assembly.data_structure.array import Array
from src.lib.assembly.data_structure.pointer import Pointer
from src.lib.assembly.data_structure.instruction.instruction import Instruction
from src.lib.assembly.artifact.flags import Flags, RegisterWidth
from src.lib.common.regex import InstructionRegex, ArtifactRegex, DataStructureRegex
from src.lib.assembly.data_structure.string.string import String, StringTypes
from src.lib.common.data_structure import DataStructure
from src.lib.common.bytes import Bytes


class Script:
    """
    A script contains all the information necessary to either assemble into binary code or disassembly into a text file.
    """

    def __init__(self):
        self.lines = list()
        self.cursor = Cursor()

    @classmethod
    def parse(cls, *filenames: str | Path) -> Self:
        """
        Creates a script out of disassembled text files.
        :param filenames: The paths to the text files.
        :return: A Script.
        """
        logging.info(f"Parsing script files: {filenames}.")
        script = cls()
        for filename in filenames:
            script.lines += cls._append_script_file(filename)

        for line in script.lines:
            logging.debug(f"Pre-parsing {repr(line)}.")
            script._preparse_line(line)
        script._parse_lines()

        script._detect_anomalies()
        return script

    def _detect_anomalies(self):
        """
        Checks if any data structure address conflicts with another.
        :return: None.
        :raises LineConflict: Raised when a line overlaps with the next one, when sorted by address.
        """
        self.sort_lines()
        data_lines = [line for line in self.lines if line.component and line.component_info != LineType.LABEL]

        for i, line in enumerate(data_lines[:-1]):
            length = len(line.component)
            if (
                line.address is not None
                and data_lines[i + 1].address is not None
                and line.address + length > data_lines[i + 1].address
            ):
                message = f"Conflicting lines: '{repr(line)}' and " f"'{repr(data_lines[i + 1])}'."
                logging.error(message)
                raise LineConflict(message)

        flag_lines = [line for line in self.lines if line.component and line.component_info == LineType.FLAGS]
        for i, line in enumerate(flag_lines[:-1]):
            if (
                line.address is not None
                and flag_lines[i + 1].address is not None
                and line.address == flag_lines[i + 1].address
                and line.component != flag_lines[i + 1].component
            ):
                message = (
                    f"Flags lines {repr(line)} and {repr(flag_lines[i + 1])} "
                    f"at address 0x{str(line.address)} are conflicting with one another."
                )
                logging.error(message)
                raise LineConflict(message)

        for line in self.data_structure_lines():
            if not self._is_data_structure_in_rom_area(line):
                message = f"Illegal address for Anchor {repr(line.component)}. Allowed address: {self.cursor.memory_map.mapping_mode.rom}"
                logging.error(message)
                raise IllegalAddress(message)

        if not self.cursor.memory_map.mapping_mode.invalid:
            return

        for line in self._get_lines(LineType.LABEL, LineType.FLAGS):
            address = line.address
            if (
                line.component
                and line.address is not None
                and self.cursor.memory_map.is_in_area_type(address, AreaTypes.INVALID)
            ):
                message = (
                    f"Illegal address for {repr(line)}. Allowed address: {self.cursor.memory_map.mapping_mode.rom}"
                )
                logging.error(message)
                raise IllegalAddress(message)

    def dump(self, filename: str | Path, debug: bool = False) -> None:
        """
        Dumps a script into a text file.
        :param filename: The path of the text file.
        :param debug: When True, will append line address as a comment to any line that doesn't already display it.
        :return: None.
        """
        logging.info(f"Dumping script to file '{filename}'.")
        self._extract_labels()
        self.sort_lines()
        output = []
        self.cursor.anchor = Operand(Bytes.from_address(0))

        first_component_address = self.data_structure_lines()[0].address

        if not self.labels().find_by_address(first_component_address):
            start_label = Label(value=first_component_address)
            logging.info(f"Added {repr(start_label)}.")
            self.lines.append(Line.from_component(start_label, first_component_address))
            self.sort_lines()

        logging.info(f"Dumping {repr(self.cursor.memory_map)}.")
        output.append(self.cursor.memory_map.to_line())

        for line in self.line_with_components():
            component = line.component
            if isinstance(component, MemoryMap):
                continue
            logging.info(f"Dumping {repr(line)}.")
            if isinstance(component, Flags):
                if self.cursor.flags == component:
                    logging.debug("Unnecessary flags redefinition. Skipping.")
                    continue
                self.cursor.flags = component
            if line.address is not None and self.cursor.address != line.address:
                if isinstance(component, Label):
                    output.append(component.to_line(show_address=True))
                    logging.debug(f"Setting cursor at 0x{self.cursor.address}.")
                    self.cursor.rom_position = self.cursor.memory_map.to_position(component.value)
                    continue

                label = Label(value=line.address)
                logging.info(f"Created {repr(label)}.")
                self.lines.append(Line.from_component(label))
                logging.info(f"Writing {repr(label)} to file.")
                output.append(label.to_line(show_address=True))

            if isinstance(component, Instruction) and component.is_flag_setter():
                self.cursor.flags = component.set_flags(self.cursor.flags)

            if isinstance(component, Pointer) and component.is_relative:
                output.append(
                    component.to_line(
                        labels=self.labels(),
                        show_address=debug,
                        address=line.address,
                        current_anchor=self.cursor.anchor,
                    )
                )
                self.cursor.anchor = component.anchor
            else:
                output.append(component.to_line(labels=self.labels(), show_address=debug, address=line.address))

            if line.address is not None:
                self.cursor.rom_position = self.cursor.memory_map.to_position(line.address) + len(component)
                logging.debug(f"Advancing cursor to 0x{self.cursor.address}.")

        with open(filename, "w", encoding="utf-8") as f:
            f.write("\n".join(output))

    def assemble(self, output_path: str | Path, input_path: str | Path | None = None) -> None:
        """
        Assembles a script into a ROM using a source ROM to modify.
        :param output_path: The destination ROM path.
        :param input_path: The source ROM path.
        :return: None.
        """
        logging.info(f"Assembling to ROM '{output_path}'.")
        input_path = input_path or output_path
        with open(input_path, "rb") as input_rom, open(output_path, "wb") as output_rom:
            rom = input_rom.read()
            output_rom.write(rom)
            for line in self.data_structure_lines():
                logging.info(f"Assembling {repr(line)} to ROM.")
                position = self.cursor.memory_map.to_position(line.address)
                output_rom.seek(position)
                output_rom.write(bytes(line.component))

    @classmethod
    def disassemble(cls, filename: str | Path, sections: list[ScriptSection], mapping_mode: str) -> Self:
        """
        Disassembles a ROM into a script.
        :param filename: The path of the ROM.
        :param sections: A list of sections to interpret the ROM data.
        :param mapping_mode: The type of MemoryMap. Can be 'LoROM', 'HiROM', or 'ExHiROM'.
        :return: A script.
        """
        logging.info(f"Disassembling from ROM '{filename}'.")
        script = cls()
        script.cursor.memory_map = MemoryMap.from_line(mapping_mode)
        script.lines.append(Line.from_component(script.cursor.memory_map))
        with open(filename, "rb") as f:
            for section in sections:
                if section.variables:
                    for var_dict in section.variables.values():
                        for var in var_dict.values():
                            script.lines.append(Line.from_component(var))

                logging.info(f"Disassembling {section.mode} section starting at {Bytes.from_address(section.start)}.")

                script.cursor.rom_position = section.start
                f.seek(script.cursor.rom_position)

                if section.mode == ScriptMode.POINTERS:
                    script._disassemble_pointers(f, section)

                elif section.mode == ScriptMode.INSTRUCTIONS:
                    script._disassemble_instructions(f, section)

                elif section.mode in (ScriptMode.BLOBS, ScriptMode.STRINGS):
                    script._disassemble_blobs(f, section)

                elif section.mode == ScriptMode.ARRAYS:
                    script._disassemble_arrays(f, section)

                elif section.mode == ScriptMode.ANIMATION_INSTRUCTIONS:
                    script._disassemble_animation_instructions(f, section)

                script.cursor.reset()

        cls.sort_lines(script)

        return script

    def sort_lines(self) -> None:
        """
        Sorts the script lines by address, with Flags and Labels in priority. Then, it will put the MemoryMap first.
        :return: Nothing.
        """
        self.lines.sort(key=lambda x: x.component_info != LineType.FLAGS)
        self.lines.sort(key=lambda x: x.component_info != LineType.LABEL)
        self.lines.sort(key=lambda x: (x.address is not None, x.address))
        self.lines.sort(key=lambda x: x.component_info != LineType.MEMORY_MAP)

    @classmethod
    def _append_script_file(cls, filename: str | Path) -> list[Line]:
        """
        Parses a text file and return Lines.
        :param filename: The path of the text file.
        :return: A list of Lines.
        """
        lines = list()

        logging.info(f"Appending file '{filename}'.")

        with open(filename, encoding="utf-8") as f:
            for raw_string in f.readlines():
                if clean_string := clean_line(raw_string):
                    lines.append(Line(filename, raw_string, clean_string))

        return lines

    def _parse_lines(self) -> None:
        """
        Parses the script line and finishes filling the Line fields.
        :return: Nothing.
        :raises UnrecognizedLine: Raised when the Component type can't be determined.
        """
        for line in self.lines:
            logging.info(f"Parsing {repr(line)}.")

            if line.component_info in (
                LineType.MEMORY_MAP,
                LineType.ANIMATION_SETTINGS,
                LineType.VARIABLE_DECLARATION,
                LineType.LABEL,
            ):
                continue

            if line.component_info == LineType.ANCHOR:
                self.cursor.anchor = Operand.from_line(
                    **line.regex_groups, parent_address=line.address, variables=self.variables()
                )
                logging.info(f"New anchor: {repr(self.cursor.anchor)}.")
            elif line.component_info == LineType.ARRAY:
                array = Array.from_line(line=line.clean_line, address=line.address, variables=self.constants())
                line.component = array
            elif line.component_info == LineType.BLOB:
                blob = Blob.from_line(**line.regex_groups, address=line.address, variables=self.constants())
                line.component = blob
            elif line.component_info == LineType.FLAGS:
                new_flags = Flags.from_line(**line.regex_groups)
                if new_flags != self.cursor.flags:
                    logging.info(f"New flags have been detected. {repr(new_flags)}")
                self.cursor.flags = new_flags
                line.component = Flags.copy(new_flags)
            elif line.component_info == LineType.INSTRUCTION:
                if self.cursor.flags.is_invalid():
                    message = "Flags have not been defined before the first instruction."
                    logging.error(message)
                    raise UndefinedFlags(message)
                instruction = Instruction.from_line(
                    **line.regex_groups, flags=self.cursor.flags, address=line.address, variables=self.variables()
                )
                if instruction.is_flag_setter():
                    self.cursor.flags = instruction.set_flags(self.cursor.flags)
                    logging.info(f"Instruction is a flag setter. New flags: {repr(self.cursor.flags)}.")
                line.component = instruction
            elif line.component_info == LineType.POINTER:
                pointer = Pointer.from_line(
                    **line.regex_groups, address=line.address, anchor=self.cursor.anchor, labels=self.labels()
                )
                line.component = pointer
            elif line.component_info == LineType.STRING:
                string = String.from_line(**line.regex_groups, address=line.address, variables=self.constants())
                line.component = string
            elif line.component_info == LineType.VARIABLE_DECLARATION:
                continue
            elif line.component_info == LineType.THREAD_COUNTER:
                thread_counter = ThreadCounter.from_line(**line.regex_groups)
                line.component = thread_counter
                self.cursor.threads = line.component.threads
            elif line.component_info == LineType.ANIMATION_INSTRUCTION:
                instruction = AnimationInstruction.from_line(
                    **line.regex_groups,
                    address=line.address,
                    threads=self.cursor.threads,
                    depth=self.cursor.animation_depth,
                    variables=self.variables(),
                )
                self.cursor.animation_depth = max(self.cursor.animation_depth + instruction.command.depth_modifier, 0)
                line.component = instruction
            else:
                raw_line = line.raw_line.strip("\n")
                message = f"Line '{raw_line}' in file '{line.filename}' is not recognized."
                logging.error(message)
                raise UnrecognizedLine(message)

    def _preparse_line(self, line: Line) -> None:
        """
        Prepares the parsing of a script line by filling some of the fields of the Line and determining the Line length.
        :param line: The line being parsed as a string or as the Line object containing it.
        :return: Nothing.
        :raises MismatchedMappingMode: Raised when two different MemoryMaps are set in the files being parsed.
        """

        cleaned_line = line.clean_line

        if match := re.fullmatch(ArtifactRegex.MEMORY_MAP, cleaned_line):
            memory_map = MemoryMap.from_line(match.group("mapping_mode"))
            if self.cursor.memory_map and self.cursor.memory_map.mapping_mode != memory_map.mapping_mode:
                message = (
                    f"MemoryMap '{self.cursor.memory_map.mapping_mode.name}' "
                    f"cannot be redefined to '{memory_map.mapping_mode.name}'."
                )
                logging.error(message)
                raise MismatchedMappingModes(message)
            line.component = memory_map
            line.component_info = LineType.MEMORY_MAP
            self.cursor.memory_map = memory_map
            return

        if match := re.fullmatch(ArtifactRegex.VARIABLE_DECLARATION, cleaned_line):
            line.component = Constant.from_line(name=match.group("name"), operand=match.group("operand"))
            line.component_info = LineType.VARIABLE_DECLARATION
            return

        line.address = self.cursor.address

        if match := re.fullmatch(ArtifactRegex.LABEL, cleaned_line):
            label = Label.from_line(
                name=match.group("name"), snes_address=match.group("snes_address"), address=line.address
            )
            self.cursor.rom_position = self.cursor.memory_map.to_position(label.value)
            logging.debug(f"Cursor set at 0x{self.cursor.address}.")
            line.component_info = LineType.LABEL
            line.component = label

        elif match := re.fullmatch(ArtifactRegex.ANCHOR, cleaned_line):
            line.component_info = LineType.ANCHOR

        elif match := re.fullmatch(ArtifactRegex.FLAGS, cleaned_line):
            line.component_info = LineType.FLAGS

        elif re.fullmatch(DataStructureRegex.ARRAY, cleaned_line):
            self.cursor.rom_position += Array.find_length(cleaned_line, self.variables())
            line.component_info = LineType.ARRAY

        elif match := re.fullmatch(DataStructureRegex.POINTER, cleaned_line):
            self.cursor.rom_position += Pointer.find_length()
            line.component_info = LineType.POINTER

        elif match := re.fullmatch(DataStructureRegex.BLOB, cleaned_line):
            self.cursor.rom_position += Blob.find_length(
                operand=match.group("operand"), variables=self.constants(), delimiter=match.group("delimiter")
            )
            line.component_info = LineType.BLOB

        elif match := re.fullmatch(DataStructureRegex.STRING, cleaned_line):
            self.cursor.rom_position += String.find_length(
                string=match.group("string"), delimiter=match.group("delimiter")
            )
            line.component_info = LineType.STRING

        elif match := re.fullmatch(DataStructureRegex.ANIMATION_INSTRUCTION, cleaned_line):
            self.cursor.rom_position += AnimationInstruction.find_length(
                command=match.group("command"), threads=self.cursor.threads
            )
            line.component_info = LineType.ANIMATION_INSTRUCTION

        elif match := re.match(InstructionRegex.INSTRUCTION, cleaned_line):
            self.cursor.rom_position += Instruction.find_length(
                command=match.group("command"), operand=match.group("operand"), variables=self.variables()
            )
            line.component_info = LineType.INSTRUCTION

        elif match := re.fullmatch(ArtifactRegex.ANIMATION_SETTINGS, cleaned_line):
            self.cursor.rom_position += AnimationSettings.find_length()
            line.component_info = LineType.ANIMATION_SETTINGS

        elif match := re.fullmatch(ArtifactRegex.THREAD_COUNTER, cleaned_line):
            line.component_info = LineType.THREAD_COUNTER
            self.cursor.threads = int(match.group("threads"))

        else:
            raw_line = line.raw_line.strip("\n")
            message = f"Line '{raw_line}' in file '{line.filename}' is not recognized."
            logging.error(message)
            raise UnrecognizedLine(message)

        if match:
            line.regex_groups = {
                group: match.group(group) if line.component_info.regex_groups else None
                for group in line.component_info.regex_groups
            }

        return

    def _disassemble_arrays(self, f: BinaryIO, section: ScriptSection) -> None:
        """
        Disassembles an Array section.
        :param f: The stream being currently opened which is reading the ROM.
        :param section: The blob group section info.
        :return: None.
        :raises MissingSectionAttribute: Raised when the section misses the 'subsections' attribute.
        """
        if not section.attributes.get("sub_sections"):
            message = "Attribute 'sub_sections' is missing." f"Attributes: {section.attributes}"
            logging.error(message)
            raise MissingSectionAttribute(message)

        f.seek(self.cursor.rom_position)
        while self.cursor.rom_position < section.end:
            address = self.cursor.address
            array = Array()

            for sub_section in section.attributes["sub_sections"]:
                data = self._extract_blob_bytes(f=f, length=sub_section.length, delimiter=sub_section.delimiter)
                delimiter = sub_section.delimiter
                if sub_section.mode == ScriptMode.BLOBS:
                    blob = Blob.from_bytes(data=data, delimiter=delimiter)
                elif sub_section.string_type == StringTypes.MENU:
                    blob = String.from_bytes(
                        data=data,
                        delimiter=delimiter,
                        string_type=StringTypes.MENU,
                    )
                elif sub_section.string_type == StringTypes.DESCRIPTION:
                    blob = String.from_bytes(
                        data=data,
                        delimiter=delimiter,
                        string_type=StringTypes.DESCRIPTION,
                    )
                else:
                    message = f"Mode '{sub_section.mode}' unrecognized."
                    logging.error(message)
                    raise UnrecognizedSubsectionMode(message)

                self.cursor.rom_position += len(blob)
                array.parts.append(blob)

            if section.attributes.get("pattern", False) == ArrayPattern.TREASURE_CHESTS:
                value = int(array.parts[3].operand.value)
                array.parts[3].operand.variable = section.variables["treasure_types"].get(value, None)
                if value & 0x40 == 0x40:
                    item_id = int(array.parts[4].operand.value)
                    array.parts[4].operand.variable = section.variables["items"].get(item_id, None)

            self.lines.append(Line.from_component(array, address))

    def _disassemble_blobs(self, f: BinaryIO, section: ScriptSection) -> None:
        """
        Disassembles a blob section.
        :param f: The stream being currently opened which is reading the ROM.
        :param section: The blob section info.
        :return: None.
        :raises MissingSectionAttribute: Raised when the section misses both the 'length' and 'delimiter' attributes.
        """
        if section.attributes.get("length", None) is None and section.attributes.get("delimiter", None) is None:
            message = (
                "Attribute 'length' and 'delimiter' are missing. Please provide either of them."
                f"Attributes: {section.attributes}"
            )
            logging.error(message)
            raise MissingSectionAttribute(message)

        f.seek(self.cursor.rom_position)
        delimiter = section.attributes.get("delimiter", None)
        string_type = section.attributes.get("string_type", None)

        while self.cursor.rom_position < section.end:
            address = self.cursor.address
            data = self._extract_blob_bytes(
                f=f, length=section.attributes.get("length", None), delimiter=section.attributes.get("delimiter", None)
            )

            if data == b"":
                break

            if section.mode == ScriptMode.BLOBS:
                blob = Blob.from_bytes(data=data, delimiter=delimiter)
            elif string_type == StringTypes.MENU:
                blob = String.from_bytes(data=data, delimiter=delimiter, string_type=StringTypes.MENU)
            else:
                blob = String.from_bytes(
                    data=data,
                    delimiter=delimiter,
                    string_type=StringTypes.DESCRIPTION,
                )

            self.lines.append(Line.from_component(blob, address))
            self.cursor.rom_position += len(blob)

    def _disassemble_pointers(self, f: BinaryIO, section: ScriptSection) -> None:
        """
        Disassembles a pointer section.
        :param cursor: The current address being read in the ROM.
        :param f: The stream being currently opened which is reading the ROM.
        :param section: The pointer info.
        :return: None.
        """

        if address := section.attributes.get("anchor", 0):
            self.cursor.anchor = Operand(Bytes.from_address(address))
            label = Label(value=self.cursor.anchor.value)
            if not self.labels().find_by_address(label.value):
                self.lines.append(Line.from_component(label, label.value))

        while self.cursor.rom_position < section.end:
            pointer_bytes = f.read(2)
            address = self.cursor.address
            pointer = Pointer.from_bytes(address=address, value=pointer_bytes, anchor=self.cursor.anchor)
            label = Label(value=pointer.destination)
            if not self.labels().find_by_address(label.value):
                self.lines.append(Line.from_component(label, label.value))
            self.lines.append(Line.from_component(pointer, address))
            self.cursor.rom_position += 2

    def _disassemble_instructions(self, f: BinaryIO, section: ScriptSection) -> None:
        """
        Disassembles an instruction section.
        :param cursor: The current position being read in the ROM.
        :param f: The stream being currently opened which is reading the ROM.
        :param section: The instruction section info.
        :return: None.
        :raises MissingSectionAttribute: Raised when the section misses the 'flags' attribute.
        """
        if "flags" not in section.attributes:
            message = f"Attribute 'flags' is missing. Attributes: {section.attributes}"
            logging.error(message)
            raise MissingSectionAttribute(message)

        self.cursor.flags = section.attributes["flags"]
        logging.info(f"Setting new section Flags: {repr(self.cursor.flags)}")
        self.cursor.rom_position = section.start

        address = self.cursor.address
        self.lines.append(Line.from_component(self.cursor.flags, address))
        while self.cursor.rom_position < section.end:
            address = self.cursor.address
            f.seek(self.cursor.rom_position)
            value = f.read(4)

            instruction = Instruction.from_bytes(
                address=address, value=value, flags=self.cursor.flags, variables=self.variables()
            )

            if instruction.is_flag_setter():
                self.cursor.flags = instruction.set_flags(self.cursor.flags)
                logging.info(f"Instruction is a flag setter. New flags: {repr(self.cursor.flags)}.")
            elif instruction.labels:
                for label in instruction.labels:
                    if not self.labels().find_by_address(label.value):
                        self.lines.append(Line.from_component(label))

            self.lines.append(Line.from_component(instruction, address))
            self.cursor.rom_position += len(instruction)

    def _disassemble_animation_instructions(self, f: BinaryIO, section: ScriptSection) -> None:
        if "threads" not in section.attributes:
            message = f"Attribute 'threads' is missing. Attributes: {section.attributes}"
            logging.error(message)
            raise MissingSectionAttribute(message)

        for cursor, threads in section.attributes["threads"].items():
            line = Line.from_component(ThreadCounter(threads=threads))
            line.component_info = LineType.THREAD_COUNTER
            line.address = self.cursor.address
            self.lines.append(line)

        depth = 0
        while self.cursor.rom_position < section.end:
            address = self.cursor.address

            threads = [v for k, v in section.attributes["threads"].items() if k <= cursor][-1]
            f.seek(self.cursor.rom_position)
            value = f.read(12)

            if self.cursor.new_animation:
                if not self.labels().find_by_address(address):
                    line = Line.from_component(Label(value=address))
                    line.address = address
                    line.component_info = LineType.LABEL
                    self.lines.append(line)
                if value[0] == value[0] & 0xF0 and value[1] == value[1] & 0xF0:
                    anim_settings = AnimationSettings.from_bytes(value=value)
                    line = Line.from_component(anim_settings)
                    line.address = address
                    line.component_info = LineType.ANIMATION_SETTINGS
                    self.lines.append(line)
                    cursor += len(line.component)
                self.cursor.new_animation = False
                continue

            instruction = AnimationInstruction.from_bytes(
                threads=threads, address=address, value=value, variables=self.variables(), depth=depth
            )

            if instruction.labels:
                for label in instruction.labels:
                    if not self.labels().find_by_address(label.value):
                        line = Line.from_component(label)
                        line.address = label.value
                        line.component_info = LineType.LABEL
                        self.lines.append(line)
            if instruction.command.is_ending:
                self.cursor.new_animation = True
                self.cursor.animation_depth = 0
            else:
                self.cursor.animation_depth += instruction.command.depth_modifier

            self.lines.append(Line.from_component(instruction, address))
            self.cursor.rom_position += len(instruction)

    def _extract_labels(self) -> None:
        """
        Extracts all labels from pointers and instructions.
        :return: None.
        """
        for line in self.pointer_lines():
            pointer = line.component
            if pointer.operand.variable:
                label = pointer.operand.variable
                if not self.variables().find_by_address(label.value):
                    self.lines.append(Line.from_component(label))
        for line in self.instruction_lines():
            instruction = line.component
            for label in instruction.labels:
                if not self.variables().find_by_address(label.value):
                    self.lines.append(Line.from_component(label, label.value))

    @staticmethod
    def _extract_blob_bytes(f: BinaryIO, length: int | None = None, delimiter: bytes | None = None) -> bytes:
        """
        Extracts the bytes of a blob.
        :param f: The stream being currently opened which is reading the ROM.
        :param length: The length of the blob.
        :param delimiter: The byte used to determine the end of the blob.
        :return: The blob as a bytes array.
        """
        if length is not None:
            return f.read(length)

        data = b""
        while (_char := f.read(1)) != bytes(delimiter):
            if _char == b"":
                break
            data += _char
        return data

    def variables(self) -> Variables:
        return Variables(*[line.component for line in self._get_lines(LineType.VARIABLE_DECLARATION, LineType.LABEL)])

    def constants(self) -> Variables:
        return Variables(*[line.component for line in self._get_lines(LineType.VARIABLE_DECLARATION)])

    def labels(self) -> Variables:
        return Variables(*[line.component for line in self._get_lines(LineType.LABEL)])

    def flags_lines(self) -> list[Line]:
        return self._get_lines(LineType.FLAGS)

    def pointer_lines(self) -> list[Line]:
        return self._get_lines(LineType.POINTER)

    def instruction_lines(self) -> list[Line]:
        return self._get_lines(LineType.INSTRUCTION)

    def blob_lines(self) -> list[Line]:
        return self._get_lines(LineType.BLOB)

    def string_lines(self) -> list[Line]:
        return self._get_lines(LineType.STRING)

    def array_lines(self) -> list[Line]:
        return self._get_lines(LineType.ARRAY)

    def memory_map_lines(self) -> list[Line]:
        return self._get_lines(LineType.MEMORY_MAP)

    def line_with_components(self) -> list[Line]:
        return [line for line in self.lines if line.component]

    def data_structure_lines(self) -> list[Line]:
        return [line for line in self.lines if isinstance(line.component, DataStructure)]

    def _get_lines(self, *component_infos: LineType) -> list[Line]:
        """
        Obtains the Components inside the Lines.
        :param component_infos: If provided, will filter the results by Component type.
        :return: A list of Components.
        """
        return [line for line in self.lines if line.component_info in component_infos]

    def _is_data_structure_in_rom_area(self, line: Line) -> bool:
        """
        Determines if the entirety of the DataStructure is inside the ROM area in the MemoryMap. Also,
        if the DataStructure is a relative Pointer, it will do the same for the
        :param line: A DataStructure.
        :return: True if the DataStructure and its anchor, if applicable, are contained within the ROM area.
        """
        first_byte = line.address
        last_byte = Bytes.from_address(int(line.address) + len(line.component) - 1)
        for address in first_byte, last_byte:
            if not self.cursor.memory_map.is_in_area_type(address, AreaTypes.ROM):
                return False
        if (
            isinstance(line, Pointer)
            and line.anchor
            and not self.cursor.memory_map.is_in_area_type(line.anchor.value, AreaTypes.ROM)
        ):
            return False
        return True
