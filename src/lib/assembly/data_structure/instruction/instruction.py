import logging
import re
from typing import Self

from src.lib.assembly.artifact.variables import Variables
from src.lib.common.operand import Operand, OperandType
from src.lib.misc.exception import TooManyCandidatesException, NoCandidateException
from src.lib.assembly.artifact.flags import Flags, RegisterWidth
from src.lib.assembly.artifact.variable import Label
from src.lib.assembly.data_structure.instruction.opcodes import Opcodes
from src.lib.common.data_structure import DataStructure
from src.lib.common.bytes import Bytes


class Instruction(DataStructure):
    """
    Instructions are commands read by the processor. They contain an opcode and, usually, an operand. In this framework,
    moving block instructions (MVP and MVN) are considered having two operands.
    """

    def __init__(self, opcode: Bytes, operands: list[Operand] | None = None):
        """
        Instantiates an instruction.
        :param opcode: The command to be interpreted by the processor.
        :param operands: The data to be interpreted by the processor.
        """
        operands = operands or list()
        self.opcode = opcode
        self.operands = operands

    @classmethod
    def from_line(
        cls, command: str, address: Bytes, flags: Flags, operand: str | None = None, variables: Variables | None = None
    ) -> Self:
        """
        Converts a string from a regex match into an instruction.
        :param command: The command of the instruction, represented by 3 capital letters.
        :param operand: The data of the instruction, which may spans between 0 and 3 bytes inclusively.
        :param address: The address of the instruction in the ROM.
        :param flags: 'm' and 'x' flags, which provides the width of the accumulator and the X and Y registers.
        :param variables: A list of existing variables.
        :return: An instruction.
        """
        if command.startswith("MV"):
            chunks = operand.split(",")
        else:
            chunks = [operand] if operand else list()

        operands = list()

        if len(chunks) == 0:
            mode = ""
            length = 0
            operands = None
        elif len(chunks) == 1:
            operand_type = cls._command_to_operand_type(command)
            operands.append(
                Operand.from_line(
                    value=chunks[0], parent_address=address, operand_type=operand_type, variables=variables
                )
            )

            mode = operands[0].mode
            length = len(operands[0])
        else:
            operand_type = OperandType.DEFAULT
            mode = "#_,#_"
            length = 2

            for chunk in chunks:
                operands.append(
                    Operand.from_line(
                        value=chunk, parent_address=address, operand_type=operand_type, variables=variables
                    )
                )

        opcode = cls._find_opcode(command=command, mode=mode, length=length, flags=flags)

        instruction = cls(opcode=opcode, operands=operands)
        logging.debug(f"Created {repr(instruction)}.")
        return instruction

    @classmethod
    def from_bytes(
        cls, value: bytes, address: Bytes = None, flags: Flags = None, variables: Variables | None = None
    ) -> Self:
        """
        Converts bytes into an instruction. The method takes the next four bytes in the ROM and will determine how many
        are actually needed for the instruction depending on the opcode and the flags. 24-bit operands written as an
        address will be converted to their corresponding address in the ROM.
        :param value: The byte of the opcode and the next three bytes, which is the largest operand possible.
        :param address: The address of the instruction in the ROM.
        :param flags: 'm' and 'x' flags, which provides the width of the accumulator and the X and Y registers.
        :param variables: A list of existing variables.
        :return: An instruction.
        """
        flags = flags or Flags()
        opcode = Bytes.from_int(value[0])
        mode = Opcodes[int(opcode)]["mode"]
        command = Opcodes[int(value[0])]
        operand_type = cls._command_to_operand_type(command["command"])
        length = (
            command["length"]
            - (1 if flags.m == RegisterWidth.EIGHT_BITS else 0) * command["m"]
            - (1 if flags.x == RegisterWidth.EIGHT_BITS else 0) * command["x"]
        )
        operands = list()
        if mode == "#_,#_":
            operands.append(Operand.from_bytes(value[1:2], "#_", operand_type, address, variables))
            operands.append(Operand.from_bytes(value[2:3], "#_", operand_type, address, variables))
        elif length:
            operands.append(Operand.from_bytes(value[1 : length + 1], mode, operand_type, address, variables))

        instruction = Instruction(opcode=opcode, operands=operands)
        logging.debug(f"Created {repr(instruction)}.")
        return instruction

    @staticmethod
    def _command_to_operand_type(command: str) -> OperandType:
        """
        Converts the command into an operand type.
        :param command: The command, as a string.
        :return: An operand type.
        """
        if command in ("JMP", "JSR"):
            return OperandType.JUMPING
        if command in ("JML", "JSL"):
            return OperandType.LONG_JUMPING
        if command in ("BCC", "BCS", "BEQ", "BMI", "BNE", "BPL", "BRA"):
            return OperandType.BRANCHING
        if command == "BRL":
            return OperandType.LONG_BRANCHING
        return OperandType.DEFAULT

    def __bytes__(self) -> bytes:
        """
        Converts an instructions into bytes.
        :return: A bytes array.
        """
        output = bytes(self.opcode)
        for operand in self.operands:
            output += bytes(operand)
        return output

    @staticmethod
    def _find_opcode(command: str, mode: str, length: int, flags: Flags) -> Bytes:
        """
        Determines the opcode of the instruction.
        :param command: The command of the instruction, as a string.
        :param mode: The way that the processor should interpret the operand.
        :param length: The length of the operand.
        :param flags: 'm' and 'x' flags, which provides the width of the accumulator and the X and Y registers.
        :return: The opcode, as a Bytes object.
        :raises TooManyCandidatesException: Raised in the event that multiple opcode candidates correspond to the
        command, mode and length.
        :raises NoCandidateException: Raised in the event that no candidate fits the command, mode and length.
        """
        candidates = list()
        for code, operation in Opcodes.items():
            if operation["command"] == command and operation["mode"] == mode:
                effective_length = (
                    operation["length"]
                    - operation["m"] * (1 if flags.m == RegisterWidth.EIGHT_BITS else 0)
                    - operation["x"] * (1 if flags.x == RegisterWidth.EIGHT_BITS else 0)
                )
                if effective_length == length:
                    candidates.append(code)

        if len(candidates) > 1:
            message = f"More than one candidate for {command=} and {mode=}. {candidates=}"
            logging.error(message)
            raise TooManyCandidatesException(message)
        if len(candidates) == 0:
            message = f"No candidate was found for {command=}, {mode=} and {length=}."
            logging.error(message)
            raise NoCandidateException(message)

        return Bytes([candidates[0]])

    def is_flag_setter(self) -> bool:
        """
        Determines if an instruction is used by the processor to set the 'm' or 'x' flags.
        :return: Whether the command is 'REP' or 'SEP'.
        """
        return Opcodes[int(self.opcode)]["command"] in ["REP", "SEP"]

    def set_flags(self, flags: Flags) -> Flags:
        """
        Returns the new values of the 'm' and 'x' flags after encountering a flag setter instruction.
        :param flags: A Flags object.
        :return: A new Flags object.
        """
        flag_state = 8 if Opcodes[int(self.opcode)]["command"] == "SEP" else 16
        if int(self.operands[0].value) & 0x10:
            flags.x = flag_state
        if int(self.operands[0].value) & 0x20:
            flags.m = flag_state
        return flags

    def __len__(self) -> int:
        """
        :return: The number of bytes to which the instruction corresponds.
        """
        length = 1
        length += sum([len(operand) for operand in self.operands])
        return length

    def __eq__(self, other: Self) -> bool:
        """
        :param other: The second instruction.
        :return: Whether the values of the fields of the instruction are the same.
        """
        return self.opcode == other.opcode and self.operands == other.operands

    def __str__(self) -> str:
        """
        Converts an instruction into a string.
        :return: A string.
        """
        output = Opcodes[int(self.opcode)]["command"]
        if self.operands:
            output += " "
            output += ",".join([str(operand) for operand in self.operands])
        return output

    def to_line(
        self, show_address: bool = False, address: Bytes | None = None, labels: list[Label] | None = None
    ) -> str:
        """
        Converts an instruction into the exact string which will be put in a script.
        :param show_address: Whether the address of the instruction should be added as a comment.
        :param address: The address of the Instruction.
        :param labels: A list of labels. Unused.
        :return: A script line.
        """
        output = f"  {self}"
        output += f" ; ${address}" if show_address else ""
        return output

    def __repr__(self) -> str:
        """
        :return: A string representation of the instruction displayed by the IDE or in error messages.
        """
        hexa = str(self.opcode)
        for operand in self.operands:
            hexa += str(operand.value)
        output = f"Instruction(as_str='{str(self)}', as_bytes={bytes(self)}, as_hexa=0x{hexa}"

        if self.operands:
            if self.operands[0].variable:
                output += f", operand_var_1={repr(self.operands[0].variable)}"
            if len(self.operands) == 2 and self.operands[1].variable:
                output += f", operand_var_2={repr(self.operands[1].variable)}"
        output += ")"
        return output

    @property
    def labels(self) -> list[Label]:
        """
        :return: A list of the operands' variables, if they are labels.
        """
        output = list()
        for operand in self.operands:
            if operand.variable and isinstance(operand.variable, Label):
                output.append(operand.variable)
        return output

    @classmethod
    def find_length(cls, command: str, operand: str | None = None, variables: Variables | None = None) -> int:
        """
        Finds the length of the Instruction when the Label associated with it has yet to be defined. This is used so
        that we can continue to parse the script with the proper positions for the cursor.
        :param operand: The operand of the instruction, as a string.
        :param variables: The Variables list.
        :param command: The command of the instruction.
        :return: The integer of the instruction, including the opcode and the operand.
        """
        operand_type = cls._command_to_operand_type(command)
        stripped_value = re.sub(r"[#()\[\],SXY]", "", operand) if operand else ""

        if not operand:
            length = 0
        # If the instruction is a moving block instruction, the length is always 3.
        elif operand.count("#") == 2:
            length = 2

        # If the instruction is a branching or long branching instruction, the length is either 2 or 3.
        elif operand_type == OperandType.BRANCHING:
            length = 1
        elif operand_type == OperandType.LONG_BRANCHING:
            length = 2

        # If the operand contains a prefix, we can determine its length.
        elif "$" in stripped_value:
            length = len(stripped_value.replace("$", "")) // 2
        elif "." in stripped_value:
            length = 1
        elif "!" in stripped_value:
            length = 2

        # If it doesn't exist, then it's guaranteed that it is a variable so we need to determine its value.
        elif variable := variables.find_by_name(re.sub(r"[.!]", "", stripped_value)):
            length = len(variable.value)
        else:
            # If we can't identify the variable, we assume it's a label that will be declared later in the script.
            logging.warning(f"Can't find variable named '{stripped_value}'. Assuming it is a label yet to be declared.")
            length = 3

        length += 1
        logging.debug(f"Instruction '{command}{' ' + operand if operand else ''}' length is {length}.")
        return length
