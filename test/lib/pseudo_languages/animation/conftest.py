from src.lib.common.bytes import Bytes, Endian
from src.lib.pseudo_languages.animation.animation_info import AnimationCommand, AnimationCommandType

ANIMATION_COMMANDS = {
    0x12: AnimationCommand(opcode=Bytes.from_int(0x12), name="DUMMY", length=2),
    0x34: AnimationCommand(opcode=Bytes.from_int(0x34), name="DUPLICATE", length=1),
    0x56: AnimationCommand(opcode=Bytes.from_int(0x56), name="DUPLICATE", length=3),
    0x80: AnimationCommand(opcode=Bytes.from_int(0x80), name="JUMP", length=2, type=AnimationCommandType.JUMPING),
    0xCC: AnimationCommand(
        opcode=Bytes.from_int(0xCC), name="VARIABLE_LENGTH", length="variable", type=AnimationCommandType.JUMPING
    ),
    0xF000: AnimationCommand(opcode=Bytes.from_int(0xF000, endian=Endian.BIG), name="SUB_00", length=1),
}
