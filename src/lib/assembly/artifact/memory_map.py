import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Self, Any

from src.lib.common.artifact import Artifact
from src.lib.common.bytes import Bytes
from src.lib.misc.exception import UnrecognizedMappingMode, IllegalRomPosition, IllegalAddress


@dataclass
class Area:
    """
    An Area represents a region of the memory map dedicated to a specific type of memory. It does not represent a
    contiguous region in the map, but rather a region in each bank between the two least significant two bytes of the
    start and end, inclusively. For example, if 'start' is 0x201234 and 'end' is 0x234567, then the area covers the
    regions 0x201234-0x204567, 0x211234-0x214567, 0x221234-0x224567, 0x231234-0x234567, all inclusively.
    """

    start: int
    end: int

    def height(self) -> int:
        """
        :return: The number of addresses between 'start' and 'end', inclusively.
        """
        return self.end % 0x010000 - self.start % 0x010000 + 1

    def width(self) -> int:
        """
        :return: The number of banks between 'start' and 'end', inclusively.
        """
        return self.end // 0x010000 - self.start // 0x010000 + 1

    def surface(self) -> int:
        """
        :return: The total number of addresses across all banks between 'start' and 'end', inclusively.
        """
        return self.height() * self.width()

    def banks(self) -> range:
        """
        :return: A range of all the banks covered by the area.
        """
        return range(self.start // 0x010000, self.end // 0x010000 + 1)

    def contains(self, address: Bytes) -> bool:
        """
        Determines if an address is located in an Area.
        :param address: The address, as Bytes.
        :return: True if contained in the Area.
        """
        _address = int(address)
        bank = _address // 0x010000
        position = _address % 0x010000
        return (
            self.start // 0x010000 <= bank <= self.end // 0x010000
            and self.start % 0x010000 <= position <= self.end % 0x010000
        )


AreaType = list[Area]


class AreaTypes(StrEnum):
    ROM = "rom"
    RAM = "ram"
    SRAM = "sram"
    LOW_RAM = "low_ram"
    IO = "io"
    EXPANSION = "expansion"
    ROM_MIRROR = "rom_mirror"
    INVALID = "invalid"


@dataclass
class MappingMode:
    name: str
    rom: AreaType
    ram: AreaType
    sram: AreaType
    low_ram: AreaType
    io: AreaType
    expansion: AreaType
    rom_mirror: AreaType
    invalid: AreaType | None = None


class MappingModes:
    LO_ROM = MappingMode(
        name="LoROM",
        rom=[Area(0x808000, 0xFFFFFF)],
        ram=[Area(0x7E2000, 0x7EFFFF), Area(0x7F0000, 0x7FFFFF)],
        sram=[Area(0x700000, 0x7D7FFF)],
        low_ram=[Area(0x000000, 0x3F1FFF), Area(0x7E0000, 0x7E1FFF), Area(0x800000, 0xBF1FFF)],
        io=[Area(0x002000, 0x3F5FFF), Area(0x802000, 0xBF5FFF)],
        expansion=[Area(0x006000, 0x3F7FFF), Area(0x806000, 0xBF7FFF)],
        rom_mirror=[Area(0x008000, 0x7DFFFF)],
        invalid=[Area(0x400000, 0x6F7FFF), Area(0xC00000, 0xFF7FFF)],
    )
    HI_ROM = MappingMode(
        name="HiROM",
        rom=[Area(0xC00000, 0xFFFFFF)],
        ram=[Area(0x7E2000, 0x7EFFFF), Area(0x7F0000, 0x7FFFFF)],
        sram=[Area(0x306000, 0x3F7FFF)],
        low_ram=[Area(0x000000, 0x3F1FFF), Area(0x7E0000, 0x7E1FFF), Area(0x800000, 0xBF1FFF)],
        io=[Area(0x002000, 0x3F5FFF), Area(0x802000, 0xBF5FFF)],
        expansion=[Area(0x006000, 0x2F7FFF), Area(0x806000, 0xBF7FFF)],
        rom_mirror=[Area(0x008000, 0x3FFFFF), Area(0x808000, 0xBFFFFF)],
        invalid=[Area(0x400000, 0x7DFFFF)],
    )
    EX_HI_ROM = MappingMode(
        name="ExHiROM",
        rom=[Area(0xC00000, 0xFFFFFF), Area(0x400000, 0x7DFFFF), Area(0x3E8000, 0x3FFFFF)],
        ram=[Area(0x7E2000, 0x7EFFFF), Area(0x7F0000, 0x7FFFFF)],
        sram=[Area(0x806000, 0xBF7FFF)],
        low_ram=[Area(0x000000, 0x3F1FFF), Area(0x7E0000, 0x7E1FFF), Area(0x800000, 0xBF1FFF)],
        io=[Area(0x002000, 0x3F5FFF), Area(0x802000, 0xBF5FFF)],
        expansion=[Area(0x006000, 0x3F7FFF), Area(0x806000, 0xBF7FFF)],
        rom_mirror=[Area(0x008000, 0x3DFFFF), Area(0x808000, 0xBFFFFF)],
    )


class MemoryMap(Artifact):
    """
    A MemoryMap is an artifact that will determine how to convert addresses to and from ROM positions.
    """

    def __init__(self, mapping_mode: MappingMode):
        self.mapping_mode = mapping_mode

    @classmethod
    def from_line(cls, mapping_mode: str) -> Self:
        """
        Converts a Line into a MemoryMap.
        :param mapping_mode: Can be 'LoROM', 'HiRom', or 'ExHiROM'.
        :return: A MemoryMap.
        :raises UnrecognizedMappingMode: Raised when the mapping_mode is not recognized.
        """
        if mapping_mode == "LoROM":
            return cls(MappingModes.LO_ROM)
        if mapping_mode == "HiROM":
            return cls(MappingModes.HI_ROM)
        if mapping_mode == "ExHiROM":
            return cls(MappingModes.EX_HI_ROM)
        message = f"Unrecognized MappingMode '{mapping_mode}'. Existing mapping modes: LoROM, HiROM, ExHiROM."
        logging.error(message)
        raise UnrecognizedMappingMode(message)

    def __str__(self):
        return f"map: {self.mapping_mode.name}"

    def __repr__(self):
        return f"MemoryMap(mapping_mode={self.mapping_mode.name})"

    def to_line(self, *args: Any, **kwargs: Any) -> str:
        """
        Converts a MemoryMap to a script Line.
        :param args: Unused.
        :param kwargs: Unused.
        :return: A Line.
        """
        return str(self)

    def is_in_area_type(self, address: Bytes, area_type: str) -> bool:
        """
        Determines if an address is contained in any of the Areas of the AreaType.
        :param address: An address, as a Bytes object.
        :param area_type: The type of memory being probed. 'rom' by default.
        :return: True if contained.
        """
        _area_type = getattr(self.mapping_mode, area_type, list())
        return any([area.contains(address) for area in _area_type])

    def to_position(self, address: Bytes, area_type: AreaTypes | None = None) -> int:
        """
        Converts an address to its position in the AreaType as if it was a contiguous area. Used mostly for 'rom' and
        'sram' as they differ drastically between mapping modes.
        :param address: An address, as a Bytes object.
        :param area_type: The type of memory used for the conversion. 'rom' by default.
        :return: The position, as an integer.
        :raises IllegalAddress: Raised when the address is not contained in the AreaType and therefore can't be
        converted into a position.
        """
        area_type = area_type or "rom"
        areas = getattr(self.mapping_mode, area_type)
        if not self.is_in_area_type(address, area_type):
            message = f"Illegal {area_type.upper()} address 0x{address}. Allowed addresses: {areas}."
            logging.error(message)
            raise IllegalAddress(message)

        rom_position = 0
        for area in areas:
            if not area.contains(address):
                rom_position += area.surface()
                continue

            start = area.start % 0x010000
            end = area.end % 0x010000
            _address = int(address)

            for bank in area.banks():
                bank_start = bank * 0x010000 + start
                bank_end = bank * 0x010000 + end

                if not (bank_start <= _address <= bank_end):
                    rom_position += end - start + 1
                    continue

                return rom_position + _address - bank_start

    def to_address(self, position: int, area_type: AreaTypes | None = None) -> Bytes:
        """
        Converts a position with an AreaType to its corresponding address. Used mostly for 'rom' and
        'sram' as they differ drastically between mapping modes.
        :param position: An address, as a Bytes object.
        :param area_type: The type of memory used for the conversion. 'rom' by default.
        :return: The address, as a Bytes object.
        :raises IllegalRomPosition: Raised when the ROM position can't be converted to an address in a
        given MemoryMap because it's value is too high.
        """
        area_type = area_type or "rom"
        areas = getattr(self.mapping_mode, area_type)
        n_addresses = sum(area.surface() for area in areas)
        if position >= n_addresses:
            message = f"Illegal ROM position. Values can go up to 0x{Bytes.from_int(n_addresses)}."
            logging.error(message)
            raise IllegalRomPosition(message)

        for area in self.mapping_mode.rom:
            surface = area.surface()
            if position >= surface:
                position -= surface
                continue

            start = area.start % 0x010000

            for bank in area.banks():
                height = area.height()
                if position >= height:
                    position -= height
                    continue
                return Bytes.from_address(bank * 0x010000 + start + position)

    def converts(self, address: Bytes, new_mapping_mode: MappingMode) -> Bytes:
        """
        Converts an address from a MappingMode to another.
        :param address: An address, as a Bytes object.
        :param new_mapping_mode: A MappingMode.
        :return: A new address, as a Bytes object.
        """
        return MemoryMap(new_mapping_mode).to_address(self.to_position(address))

    def __eq__(self, other: Self) -> bool:
        return self.mapping_mode == other.mapping_mode
