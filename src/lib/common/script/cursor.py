from src.lib.assembly.artifact.flags import RegisterWidth, Flags
from src.lib.assembly.artifact.memory_map import MemoryMap
from src.lib.common.bytes import Bytes
from src.lib.common.operand import Operand


class Cursor:

    def __init__(self):
        self.rom_position = 0
        self.memory_map = None
        self.flags = Flags(m=RegisterWidth.INVALID, x=RegisterWidth.INVALID)
        self.threads = 0
        self.new_animation = True
        self.anchor = None
        self.animation_depth = 0

    @property
    def address(self) -> Bytes:
        return self.memory_map.to_address(self.rom_position)

    def reset(self) -> None:
        self.rom_position = 0
        self.flags = Flags(m=RegisterWidth.INVALID, x=RegisterWidth.INVALID)
        self.threads = 0
        self.new_animation = True
        self.anchor = None
        self.animation_depth = 0
