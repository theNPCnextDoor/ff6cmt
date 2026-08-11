import pytest

from src.lib.assembly.artifact.variable import Constant
from src.lib.assembly.artifact.variables import Variables
from src.lib.common.bytes import Bytes
from src.lib.common.operand import Operand
from src.lib.pseudo_languages.animation.animation_settings import AnimationSettings

SLOW = Constant(name="slow", value=Bytes.from_int(0))
FAST = Constant(name="fast", value=Bytes.from_int(0x40))
BOTTOM = Constant(name="bottom", value=Bytes.from_int(0))
CENTER = Constant(name="center", value=Bytes.from_int(0x20))
TOP = Constant(name="top", value=Bytes.from_int(0x40))
VARIABLES = Variables(SLOW, FAST, BOTTOM, CENTER, TOP)

EXAMPLE_SETTINGS = AnimationSettings(speed=Operand(Bytes([0x40])), alignment=Operand(Bytes([0x20])))
EXAMPLE_SETTINGS_WITH_VARIABLES = AnimationSettings(
    speed=Operand(Bytes([0]), variable=SLOW), alignment=Operand(Bytes([0x40]), variable=TOP)
)


class TestAnimationSettings:
    @pytest.mark.parametrize(
        ["speed", "alignment", "anim_settings"],
        [
            ("$40", "$20", EXAMPLE_SETTINGS),
            ("slow", "top", EXAMPLE_SETTINGS_WITH_VARIABLES),
        ],
    )
    def test_from_line(self, speed: str, alignment: str, anim_settings: AnimationSettings):
        assert AnimationSettings.from_line(speed=speed, alignment=alignment, variables=VARIABLES) == anim_settings

    def test_from_bytes(self):
        assert AnimationSettings.from_bytes(value=b"\x40\x20") == EXAMPLE_SETTINGS

    @pytest.mark.parametrize(
        ["anim_settings", "line"],
        [(EXAMPLE_SETTINGS, "anim_settings: $40, $20"), (EXAMPLE_SETTINGS_WITH_VARIABLES, "anim_settings: slow, top")],
    )
    def test_to_line(self, anim_settings: AnimationSettings, line: str):
        assert anim_settings.to_line() == line

    def test_bytes(self):
        assert bytes(EXAMPLE_SETTINGS) == b"\x40\x20"

    def test_find_length(self):
        assert len(EXAMPLE_SETTINGS) == 2
