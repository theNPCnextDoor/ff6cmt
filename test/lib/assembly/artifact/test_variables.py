import pytest

from src.lib.assembly.artifact.variable import Constant, Variable, Label
from src.lib.assembly.artifact.variables import Variables
from src.lib.misc.exception import VariableConflict
from src.lib.common.bytes import Bytes
from test.lib.conftest import ALFA, CHARLIE, VARIABLES, BRAVO, DELTA, ECHO, addr


class TestVariables:
    def test_append(self):
        variables = Variables()
        variables.append(ALFA)
        variables.append(CHARLIE)
        assert variables == Variables(ALFA, CHARLIE)

    def test_append_raises_variable_conflict_because_of_existing_address(self):
        variables = Variables(CHARLIE)
        with pytest.raises(VariableConflict) as e:
            variables.append(CHARLIE)
        assert "address" in str(e.value).lower()

    def test_append_raises_variable_conflict_because_of_existing_name(self):
        variables = Variables(ALFA)
        with pytest.raises(VariableConflict) as e:
            variables.append(Constant(addr(0), "alfa"))
        assert "name" in str(e.value).lower()

    @pytest.mark.parametrize(["name", "variable"], [("alfa", ALFA), ("charlie", CHARLIE), ("non_existing", None)])
    def test_find_by_name(self, name: str, variable: Variable | None):
        assert VARIABLES.find_by_name(name) == variable

    @pytest.mark.parametrize(["address", "label"], [(0xD23456, CHARLIE), (0x7EFFFF, None)])
    def test_find_by_address(self, address: int, label: Label | None):
        variables = Variables(*VARIABLES)
        assert variables.find_by_address(addr(address)) == label

    def test_sort(self):
        variables = Variables(*VARIABLES[::-1])

        assert variables == Variables(DELTA, BRAVO, ALFA, ECHO, CHARLIE)

        variables.sort()

        assert variables == Variables(ALFA, BRAVO, DELTA, ECHO, CHARLIE)

    @pytest.mark.parametrize(
        ["variable", "expected"], [(ALFA, True), (CHARLIE, True), (Constant(Bytes.from_int(0), "non_existing"), False)]
    )
    def test_contains(self, variable: Variable, expected: bool):
        assert (variable in VARIABLES) is expected
