import re

import pytest as pytest

from src.lib.assembly.data_structure.regex import Regex, InstructionRegex, DataStructureRegex, ArtifactRegex


class TestRegex:
    @pytest.mark.parametrize(
        ["line", "comment"],
        [
            ("$1234", ""),
            ("; The whole line is a comment", "; The whole line is a comment"),
            ('"This is a string without a semi-colon"', ""),
            ('"This is a string containing a semi-colon; yet it is not a comment.', ""),
            ('; This is a comment containing "quotes".', '; This is a comment containing "quotes".'),
            (
                '"This is a string with a semi-colon; this is not a comment but there is one after that" ; This is the comment.',
                "; This is the comment.",
            ),
            (
                '"The string contains a semicolon; but..." ; The comment contains "quotes"',
                '; The comment contains "quotes"',
            ),
            (' desc "There is something before the quote; without comments"', ""),
            (
                ' desc "There is something before the quote; and there is a comment" ; This is the "comment"',
                '; This is the "comment"',
            ),
            (' desc "There is something before the quote; plus a delimiter without comments",$00', ""),
            (
                ' desc "There is something before the quote; plus a delimiter and comments",$00 ; Hi "comment", this is dad',
                '; Hi "comment", this is dad',
            ),
            (" \"Array with a comment containing '|' characters\" ; A | B | C ; | D", "; A | B | C ; | D"),
        ],
    )
    def test_commented_line(self, line: str, comment: str):
        match = re.match(Regex.COMMENTED_LINE, line)
        assert match
        assert match.group("comment") == comment

    @pytest.mark.parametrize(
        "line,is_match",
        [
            ("00", True),
            ("AA", True),
            ("9F", True),
            ("1G", False),
        ],
    )
    def test_byte(self, line: str, is_match: bool):
        assert bool(re.search(Regex.BYTE, line)) == is_match

    @pytest.mark.parametrize(
        "line,is_match",
        [
            ("0000", True),
            ("AAAA", True),
            ("9F9F", True),
            ("1G89", False),
        ],
    )
    def test_word(self, line: str, is_match: bool):
        assert bool(re.fullmatch(Regex.WORD, line)) == is_match

    @pytest.mark.parametrize(
        "line,is_match", [("00", True), ("AAAA", True), ("9F9F9F", True), ("1G89", False), ("$00", False)]
    )
    def test_data(self, line: str, is_match: bool):
        assert bool(re.fullmatch(Regex.DATA, line)) == is_match

    @pytest.mark.parametrize(
        ["line", "is_match"],
        [
            ("", False),
            ("a", True),
            ("abc", False),
            ("<WHITE>", True),
            ("<ATB 0>", True),
            ("abc<BLACK><ATB 4>.   fjj:;+=12345", False),
            ("$", False),
            ("abc", False),
            ("<>", False),
            ("<ATB 0", False),
        ],
    )
    def test_char(self, line: str, is_match: bool):
        assert bool(re.fullmatch(Regex.CHAR, line)) == is_match

    @pytest.mark.parametrize(
        "line,is_match",
        [
            ("abulita", True),
            ("3bulita", False),
            ("Abulita", False),
            ("aBulita", False),
            ("abu_lita", True),
            ("abul1t4", True),
            ("abulita=granma", False),
        ],
    )
    def test_variable(self, line: str, is_match):
        assert bool(re.fullmatch(Regex.VARIABLE, line)) == is_match

    @pytest.mark.parametrize(
        "line,is_match",
        [
            ("C00000", True),
            ("FFFFFF", True),
            ("000000", False),
            ("C00G00", False),
        ],
    )
    def test_snes_address(self, line: str, is_match: bool):
        assert bool(re.fullmatch(Regex.SNES_ADDRESS, line)) == is_match


class TestArtifactRegex:
    def test_memory_map(self):
        match = re.match(ArtifactRegex.MEMORY_MAP, "map: LoROM")
        assert bool(match)
        assert match.group("mapping_mode") == "LoROM"

    @pytest.mark.parametrize(
        ["line", "is_match", "m_flag", "x_flag"],
        [("m=8,x=16", True, "8", "16"), ("m=16,x=8", True, "16", "8"), ("m=True,x=False", False, None, None)],
    )
    def test_flags(self, line: str, is_match: bool, m_flag: bool, x_flag: bool):
        match = re.match(ArtifactRegex.FLAGS, line)
        assert bool(match) == is_match
        if is_match:
            assert match.group("m_flag") == m_flag
            assert match.group("x_flag") == x_flag

    @pytest.mark.parametrize(
        ["line", "name", "snes_address"],
        [
            ("@abulita = $C00000", "abulita", "$C00000"),
            ("@label_c34567 = $C34567", "label_c34567", "$C34567"),
            ("@abulita", "abulita", None),
        ],
    )
    def test_label(self, line: str, name: str, snes_address: str | None):
        match = re.fullmatch(ArtifactRegex.LABEL, line)
        assert match.group("name") == name
        assert match.group("snes_address") == snes_address

    @pytest.mark.parametrize(
        ["line", "is_match", "name", "operand"],
        [
            ("let alfa = $12", True, "alfa", "$12"),
            ("let bravo=$1234", True, "bravo", "$1234"),
            ("let bravo=$123456", False, None, None),
        ],
    )
    def test_variable_declaration(self, line: str, is_match: bool, name: str | None, operand: str | None):
        match = re.fullmatch(ArtifactRegex.VARIABLE_DECLARATION, line)
        assert bool(match) == is_match
        if is_match:
            assert match.group("name") == name
            assert match.group("operand") == operand

    @pytest.mark.parametrize(["line", "is_match"], [("#label1", True), ("#$C12345", True), ("#$GGGGGG", False)])
    def test_anchor(self, line: str, is_match: bool):
        match = re.match(ArtifactRegex.ANCHOR, line)
        assert bool(match) is is_match


class TestDataStructureRegex:
    @pytest.mark.parametrize(
        ["line", "is_match", "relative", "operand"],
        [
            ("ptr $1234", True, None, "$1234"),
            ("rptr $1234", True, "r", "$1234"),
            ("ptr $123456", False, None, None),
            ("ptr !pastagate", True, None, "!pastagate"),
            ("rptr !pastagate", True, "r", "!pastagate"),
            ("ptr pastagate", False, None, False),
            ("ptr .pastagate", False, None, None),
        ],
    )
    def test_pointer(self, line: str, is_match: bool, relative: str | None, operand: str | None):
        match = re.fullmatch(DataStructureRegex.POINTER, line)
        assert bool(match) is is_match
        if is_match:
            assert match.group("relative") == relative
            assert match.group("operand") == operand

    @pytest.mark.parametrize(
        ["line", "is_match"], [("$FF", True), ("$FG", False), ("alfa", True), (".charlie", True), ("!charlie", False)]
    )
    def test_delimiter(self, line: str, is_match: bool):
        assert bool(re.fullmatch(DataStructureRegex.DELIMITER, line)) == is_match

    @pytest.mark.parametrize(
        ["line", "is_match", "operand", "delimiter"],
        [
            ("", False, None, None),
            ("$12", True, "$12", None),
            ("$0123456789ABCDEF", True, "$0123456789ABCDEF", None),
            ("$123", False, None, None),
            ("$123,$FF", False, None, None),
            ("$12,$FF", True, "$12", "$FF"),
            ("$12,$FFF", False, None, None),
            ("bravo", True, "bravo", None),
            ("bravo,$12", True, "bravo", "$12"),
            ("$12,alfa", True, "$12", "alfa"),
            ("bravo,alfa", True, "bravo", "alfa"),
        ],
    )
    def test_blob(self, line: str, is_match: bool, operand: str | None, delimiter: str | None):
        match = re.fullmatch(DataStructureRegex.BLOB, line)
        assert bool(match) == is_match
        if is_match:
            assert match.group("operand") == operand
            assert match.group("delimiter") == delimiter

    @pytest.mark.parametrize(
        ["line", "is_match", "string_type", "string", "delimiter"],
        [
            ('""', False, None, None, None),
            ('"a"', True, None, "a", None),
            ('"a",$00', True, None, "a", "$00"),
            ('"a",alfa', True, None, "a", "alfa"),
            ('"<WHITE>"', True, None, "<WHITE>", None),
            ('"<ATB 0>"', True, None, "<ATB 0>", None),
            ('"<0x00>"', True, None, "<0x00>", None),
            ('"$"', False, None, None, None),
            ("abc", False, None, None, None),
            ('"<>"', False, None, None, None),
            ('"<ATB 0', False, None, None, None),
            ('"a  $00', False, None, None, None),
            ('"a",$FFF', False, None, None, None),
            ('desc "<0xFF>",$88', True, "desc", "<0xFF>", "$88"),
        ],
    )
    def test_string(
        self, line: str, is_match: bool, string_type: str | None, string: str | None, delimiter: str | None
    ):
        match = re.fullmatch(DataStructureRegex.STRING, line)
        assert bool(match) == is_match
        if is_match:
            assert match.group("string_type") == string_type
            assert match.group("string") == string
            assert match.group("delimiter") == delimiter

    def test_array(self):
        assert re.fullmatch(
            DataStructureRegex.ARRAY,
            '$00 | $00,$00 | alfa | bravo,alfa | .charlie | !charlie,$00 | "alice" | "bob",$00 | "charlie",alfa',
        )


class TestInstructionRegex:
    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ("$ABCDEF", True),
            (".ABCDEF", False),
            ("!ABCDEF", False),
            ("@ABCDEF", False),
            ("$abcdef", False),
            (".abcdef", True),
            ("!abcdef", True),
            ("@abcdef", False),
        ],
    )
    def test_op_value(self, value: str, expected: bool):
        match = re.fullmatch(Regex.OP_VALUE, value)
        assert bool(match) is expected

    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ("#$123456", True),
            ("#.alice", True),
            ("#$12,S", False),
            ("#$12,X", False),
            ("#$12,Y", False),
            ("(#$12)", False),
            ("(#$12,X)", False),
            ("(#$12),Y", False),
            ("(#$12,S),Y", False),
            ("[#$12]", False),
            ("[#$12],Y", False),
        ],
    )
    def test_immediate_mode(self, value: str, expected: bool):
        match = re.fullmatch(InstructionRegex.IMMEDIATE_MODE, value)
        assert bool(match) is expected

    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ("$123456", True),
            (".alice", True),
            ("$12,S", True),
            ("$12,X", True),
            ("$12,Y", True),
            ("#$12", False),
            ("($12)", False),
            ("($12,X)", False),
            ("($12),Y", False),
            ("($12,S),Y", False),
            ("[$12]", False),
            ("[$12],Y", False),
        ],
    )
    def test_absolute_mode(self, value: str, expected: bool):
        match = re.fullmatch(InstructionRegex.ABSOLUTE_MODE, value)
        assert bool(match) is expected

    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ("(.alice)", True),
            ("($123456)", True),
            ("($12,X)", True),
            ("($12),Y", True),
            ("($12,S),Y", True),
            ("($12", False),
            ("($12,X", False),
            ("($12,Y", False),
            ("($12,S,Y", False),
            ("($12,S,Y)", False),
            ("(#$12)", False),
            ("($12,Y)", False),
            ("($12),X", False),
            ("($12),S", False),
            ("($12,X),X", False),
            ("($12,X),Y", False),
            ("($12,X),S", False),
            ("($12,Y),X", False),
            ("($12,Y),Y", False),
            ("($12,Y),S", False),
            ("($12,S),X", False),
            ("($12,S),S", False),
        ],
    )
    def test_direct_mode(self, value: str, expected: bool):
        match = re.fullmatch(InstructionRegex.DIRECT_MODE, value)
        assert bool(match) is expected

    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ("[$123456]", True),
            ("[.alice]", True),
            ("[$12],Y", True),
            ("[$12", False),
            ("[$12,Y", False),
            ("[#$12]", False),
            ("[$12],X", False),
            ("[$12],S", False),
            ("[$12,X]", False),
            ("[$12,Y]", False),
            ("[$12,S]", False),
        ],
    )
    def test_direct_long_mode(self, value: str, expected: bool):
        match = re.fullmatch(InstructionRegex.DIRECT_LONG_MODE, value)
        assert bool(match) is expected

    @pytest.mark.parametrize(
        ["value", "expected"],
        [
            ("#$12", True),
            ("$12", True),
            ("$12,S", True),
            ("$12,X", True),
            ("$12,Y", True),
            ("($12)", True),
            ("($12,X)", True),
            ("($12),Y", True),
            ("($12,S),Y", True),
            ("[$12]", True),
            ("[$12],Y", True),
            ("#$12,S", False),
            ("#$12,X", False),
            ("#$12,Y", False),
            ("(#$12)", False),
            ("(#$12,X)", False),
            ("(#$12),Y", False),
            ("(#$12,S),Y", False),
            ("[#$12]", False),
            ("[#$12],Y", False),
            ("($12", False),
            ("($12,X", False),
            ("($12,Y", False),
            ("($12,S,Y", False),
            ("($12,S,Y)", False),
            ("($12,Y)", False),
            ("($12),X", False),
            ("($12),S", False),
            ("($12,X),X", False),
            ("($12,X),Y", False),
            ("($12,X),S", False),
            ("($12,Y),X", False),
            ("($12,Y),Y", False),
            ("($12,Y),S", False),
            ("($12,S),X", False),
            ("($12,S),S", False),
            ("[$12", False),
            ("[$12,Y", False),
            ("[$12],X", False),
            ("[$12],S", False),
            ("[$12,X]", False),
            ("[$12,Y]", False),
            ("[$12,S]", False),
            ("#$12,#$34", True),
        ],
    )
    def test_operand(self, value: str, expected: bool):
        match = re.fullmatch(InstructionRegex.OPERAND, value)
        assert bool(match) is expected

    @pytest.mark.parametrize(
        ["line", "command", "operand"],
        [
            ("AAA", "AAA", None),
            ("AAA $12", "AAA", "$12"),
            ("AAA #$12", "AAA", "#$12"),
            ("AAA #$12,#$34", "AAA", "#$12,#$34"),
            ("AAA $12,S", "AAA", "$12,S"),
            ("AAA $12,X", "AAA", "$12,X"),
            ("AAA $12,Y", "AAA", "$12,Y"),
            ("AAA ($12)", "AAA", "($12)"),
            ("AAA ($12),Y", "AAA", "($12),Y"),
            ("AAA ($12,S),Y", "AAA", "($12,S),Y"),
            ("AAA ($12,X)", "AAA", "($12,X)"),
            ("AAA [$12]", "AAA", "[$12]"),
            ("AAA [$12],Y", "AAA", "[$12],Y"),
        ],
    )
    def test_instruction(self, line: str, command: str, operand: str):
        match = re.match(InstructionRegex.INSTRUCTION, line)
        assert match.group("command") == command
        assert match.group("operand") == operand
