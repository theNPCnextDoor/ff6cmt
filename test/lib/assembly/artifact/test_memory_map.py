import pytest

from src.lib.assembly.artifact.memory_map import MappingModes, MappingMode, MemoryMap, Area
from src.lib.common.bytes import Bytes
from src.lib.misc.exception import UnrecognizedMappingMode, IllegalRomPosition, IllegalAddress
from test.lib.conftest import addr


MAPPING_MODE = MappingMode(
    name="DebugROM",
    rom=[Area(0xC00000, 0xFFFFFF), Area(0x400000, 0x7DFFFF), Area(0x3E8000, 0x3FFFFF)],
    ram=[Area(0x7E2000, 0x7EFFFF), Area(0x7F0000, 0x7FFFFF)],
    sram=[Area(0x806000, 0xBF7FFF)],
    low_ram=[Area(0x000000, 0x3F1FFF), Area(0x7E0000, 0x7E1FFF), Area(0x800000, 0xBF1FFF)],
    io=[Area(0x002000, 0x3F5FFF), Area(0x802000, 0xBF5FFF)],
    expansion=[Area(0x006000, 0x3F7FFF), Area(0x806000, 0xBF7FFF)],
    rom_mirror=[Area(0x008000, 0x3DFFFF), Area(0x808000, 0xBFFFFF)],
)
MEMORY_MAP = MemoryMap(MAPPING_MODE)
MAPPING_MODE_2 = MappingMode(
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


class TestArea:
    @pytest.mark.parametrize(
        ["area", "height"],
        [(Area(0x000000, 0x001FFF), 0x2000), (Area(0xC00000, 0xFFFFFF), 0x010000), (Area(0x802000, 0x807FFF), 0x6000)],
    )
    def test_height(self, area: Area, height: int):
        assert area.height() == height

    @pytest.mark.parametrize(
        ["area", "width"],
        [(Area(0x000000, 0x001FFF), 1), (Area(0xC00000, 0xFFFFFF), 64), (Area(0x400000, 0x4F7FFF), 16)],
    )
    def test_width(self, area: Area, width: int):
        assert area.width() == width

    @pytest.mark.parametrize(
        ["area", "surface"],
        [
            (Area(0x000000, 0x001FFF), 0x002000),
            (Area(0xC00000, 0xFFFFFF), 0x400000),
            (Area(0x400000, 0x4F7FFF), 0x080000),
        ],
    )
    def test_surface(self, area: Area, surface: int):
        assert area.surface() == surface

    @pytest.mark.parametrize(
        ["area", "banks"],
        [
            (Area(0x000000, 0x001FFF), range(0x00, 0x01)),
            (Area(0xC00000, 0xFFFFFF), range(0xC0, 0x0100)),
            (Area(0x400000, 0x4F7FFF), range(0x40, 0x50)),
        ],
    )
    def test_banks(self, area: Area, banks: range):
        assert area.banks() == banks

    @pytest.mark.parametrize(["x", "is_in_height"], [(0x0000, False), (0x8000, True), (0xFFFF, False)])
    @pytest.mark.parametrize(["y", "is_in_width"], [(0x00, False), (0x80, True), (0xFF, False)])
    def test_contains(self, x: int, y: int, is_in_height: bool, is_in_width: bool):
        address = Bytes.from_address(y * 0x010000 + x)
        area = Area(0x202000, 0xDDDDDD)
        assert area.contains(address) is (is_in_width and is_in_height)


class TestMemoryMap:
    @pytest.mark.parametrize(
        ["name", "mapping_mode"],
        [("LoROM", MappingModes.LO_ROM), ("HiROM", MappingModes.HI_ROM), ("ExHiROM", MappingModes.EX_HI_ROM)],
    )
    def test_from_line(self, name: str, mapping_mode: MappingMode):
        assert MemoryMap.from_line(name).mapping_mode == mapping_mode

    def test_from_line_non_existing_mapping_mode(self):
        with pytest.raises(UnrecognizedMappingMode):
            MemoryMap.from_line("WrongROM")

    @pytest.mark.parametrize(
        ["name", "mapping_mode"],
        [("LoROM", MappingModes.LO_ROM), ("HiROM", MappingModes.HI_ROM), ("ExHiROM", MappingModes.EX_HI_ROM)],
    )
    def test_str(self, name: str, mapping_mode: MappingMode):
        assert str(MemoryMap(mapping_mode)) == f"map: {name}"

    @pytest.mark.parametrize(
        ["name", "mapping_mode"],
        [("LoROM", MappingModes.LO_ROM), ("HiROM", MappingModes.HI_ROM), ("ExHiROM", MappingModes.EX_HI_ROM)],
    )
    def test_to_line(self, name: str, mapping_mode: MappingMode):
        assert str(MemoryMap(mapping_mode)) == f"map: {name}"

    @pytest.mark.parametrize(["address", "expected"], [(addr(0x3F2000), False), (addr(0x7E0001), True)])
    def test_is_in_area_type(self, address: Bytes, expected: bool):
        assert MEMORY_MAP.is_in_area_type(address, "low_ram") is expected

    @pytest.mark.parametrize(
        ["address", "rom_position"],
        [
            (addr(0xC00000), 0x000000),
            (addr(0xDF1234), 0x1F1234),
            (addr(0xFFFFFF), 0x3FFFFF),
            (addr(0x400000), 0x400000),
            (addr(0x56789A), 0x56789A),
            (addr(0x7DFFFF), 0x7DFFFF),
            (addr(0x3E8000), 0x7E0000),
            (addr(0x3E9234), 0x7E1234),
            (addr(0x3FFFFF), 0x7EFFFF),
        ],
    )
    def test_to_rom_position(self, address: Bytes, rom_position: int):
        assert MEMORY_MAP.to_position(address) == rom_position

    def test_to_rom_position_raises_an_illegal_address(self):
        with pytest.raises(IllegalAddress):
            MEMORY_MAP.to_position(addr(0x000000))

    @pytest.mark.parametrize(
        ["address", "rom_position"],
        [
            (addr(0xC00000), 0x000000),
            (addr(0xDF1234), 0x1F1234),
            (addr(0xFFFFFF), 0x3FFFFF),
            (addr(0x400000), 0x400000),
            (addr(0x56789A), 0x56789A),
            (addr(0x7DFFFF), 0x7DFFFF),
            (addr(0x3E8000), 0x7E0000),
            (addr(0x3E9234), 0x7E1234),
            (addr(0x3FFFFF), 0x7EFFFF),
        ],
    )
    def test_to_address(self, address: Bytes, rom_position: int):
        memory_map = MemoryMap(MAPPING_MODE)
        assert memory_map.to_address(rom_position) == address

    def test_to_address_raises_an_illegal_rom_position(self):
        with pytest.raises(IllegalRomPosition):
            MEMORY_MAP.to_address(0x800000)

    def test_converts(self):
        assert MEMORY_MAP.converts(addr(0xD00001), MAPPING_MODE_2) == addr(0xA08001)
