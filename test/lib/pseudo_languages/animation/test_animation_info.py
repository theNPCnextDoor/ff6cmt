import pytest

from src import ROOT_FOLDER
from src.lib.common.bytes import Bytes, Endian
from src.lib.pseudo_languages.animation.animation_info import AnimationInfo, AnimationCommand
from src.lib.misc.exception import NoCandidateException, TooManyCandidatesException

animation_info = AnimationInfo(ROOT_FOLDER / "test" / "resources" / "test_animations.json")


class TestAnimationInfo:

    def test_find_from_opcode(self):
        assert animation_info.find_from_opcode(0x12) == AnimationCommand(
            name="DUMMY", opcode=Bytes.from_int(0x12, endian=Endian.BIG), length=2
        )

    def test_find_from_opcode_but_opcode_doesnt_exist(self):
        with pytest.raises(NoCandidateException):
            animation_info.find_from_opcode(0xFF)

    def test_find_from_name(self):
        assert animation_info.find_from_name("DUMMY") == AnimationCommand(
            name="DUMMY", opcode=Bytes.from_int(0x12, endian=Endian.BIG), length=2
        )

    def test_find_from_name_but_name_doesnt_exist(self):
        with pytest.raises(NoCandidateException):
            assert animation_info.find_from_name("NON_EXISTING")

    def test_find_from_name_but_name_is_duplicated(self):
        with pytest.raises(TooManyCandidatesException):
            assert animation_info.find_from_name("DUPLICATE")
