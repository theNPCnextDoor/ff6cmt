import logging
from typing import Self

from src.lib.assembly.artifact.variable import Label, Variable
from src.lib.assembly.bytes import Bytes
from src.lib.misc.exception import VariableConflict


class Variables:
    """
    Variables consists of two lists. One for simple variables, the other for labels. Labels are used to name an address
    in the ROM, which are 3 bytes. Simple variables contains 1 or 2-bytes values.
    """

    def __init__(self, *variables: Variable):
        self._labels = list()
        self._constants = list()
        for variable in variables:
            self.append(variable)
        self._index = 0

    def append(self, variable: Variable) -> None:
        """
        First detects if the new variable is conflicting with the known ones. Then, appends the variable either in
        the simple variable list or the label one.
        :param variable: The Variable or Label to be added.
        :return: None.
        """
        if isinstance(variable, Label):
            self._labels.append(variable)
        else:
            self._constants.append(variable)

    def detect_conflicts(self) -> None:
        """
        Checks if all variables have different names and all labels have different addresses.
        :return: None.
        :raises VariableConflict: Raised when a conflict is detected.
        """
        variables = self.all()
        for variable in variables:
            conflicting_labels = [label for label in variables if label.value == variable.value]
            if isinstance(variable, Label) and len(conflicting_labels) > 1:
                message = (
                    f"Address conflict. There are multiple labels targeting the same address {repr(variable.value)}: "
                    f"{', '.join([label.name for label in conflicting_labels])}"
                )
                logging.error(message)
                raise VariableConflict(message)

            if len([var for var in variables if var.name == variable.name]) > 1:
                message = f"Name conflict. Variable '{variable.name}' already exists."
                logging.error(message)
                raise VariableConflict(message)

    def find_by_name(self, name: str) -> Variable | None:
        """
        Returns the variable by its name.
        :param name: The name of the variable.
        :return: The variable if found. None otherwise.
        """
        for variable in self.all():
            if variable.name == name:
                return variable
        return None

    def find_by_address(self, address: Bytes) -> Label | None:
        """
        Return the label by its address.
        :param address: The address of the label.
        :return: The label if found. None otherwise.
        """
        for label in self._labels:
            if label.value == address:
                return label
        return None

    def sort(self) -> None:
        """
        Sorts the simple variables by name and the labels by their address.
        :return: None.
        """
        self._constants.sort(key=lambda x: x.name)
        self._labels.sort(key=lambda x: x.value)

    def all(self) -> list[Variable]:
        """
        :return: A list containing all simple variables and labels.
        """
        return self._constants + self._labels

    @property
    def constants(self) -> Self:
        """
        :return: A Variables object only containing this Variable object's Constants.
        """
        return type(self)(*self._constants)

    def __contains__(self, item: Variable) -> bool:
        """
        Checks if variable exists in list.
        :param item: The variable to check.
        :return: True if found.
        """
        for var in self.all():
            if item == var:
                return True
        return False

    def __eq__(self, other: Self) -> bool:
        return self.all() == other.all()

    def __iter__(self) -> Self:
        return self

    def __next__(self):
        if self._index < len(self.all()):
            item = self.all()[self._index]
            self._index += 1
            return item
        else:
            raise StopIteration

    def __len__(self):
        return len(self.all())

    def __getitem__(self, item):
        return self.all()[item]
