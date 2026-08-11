class Regex:
    COMMENTED_LINE = r'[^";]*("[^"]+"[^";]*)?(?P<comment>(;.*)?)'
    NOT_HEXA = r"(?![0-9A-F])"
    BYTE = r"[0-9A-F]{2}"
    WORD = rf"[0-9A-F]{{4}}{NOT_HEXA}"
    DATA = rf"({BYTE}){{1,3}}{NOT_HEXA}"
    CHAR = r"[0-9a-zA-Z!?/:“”\'\-.,…;#+\(\)%~=¨↑→↙× _]|<[xA-Z0-9 ]+>"
    VARIABLE = r"[a-z][0-9a-z_]+"
    SNES_ADDRESS = rf"[4-9A-F][0-9A-F]{WORD}"
    OP_VALUE = rf"(\${DATA}|[.!]?{VARIABLE})"


class ArtifactRegex:
    ANCHOR = rf"#(?P<value>\${Regex.SNES_ADDRESS}|{Regex.VARIABLE})"
    ANIMATION_SETTINGS = rf"anim_settings: (?P<speed>{Regex.OP_VALUE}), ?(?P<alignment>{Regex.OP_VALUE})"
    MEMORY_MAP = r"map: (?P<mapping_mode>(Lo|Hi|ExHi)ROM)"
    FLAGS = r"m *= *(?P<m_flag>(8|16)), *x *= *(?P<x_flag>(8|16))"
    LABEL = rf"^@(?P<name>{Regex.VARIABLE}) *(= *(?P<snes_address>\${Regex.SNES_ADDRESS}))?"
    THREAD_COUNTER = r"threads: (?P<threads>\d+)"
    VARIABLE_DECLARATION = rf"let (?P<name>{Regex.VARIABLE}) *= *(?P<operand>\$({Regex.BYTE}){{1,2}})"


class DataStructureRegex:
    ANIMATION_INSTRUCTION = (
        rf"(?P<command>[A-Z][A-Z_0-9?]{{3,}})( (?P<operands>({Regex.OP_VALUE}( {Regex.OP_VALUE})*)))?"
    )
    DELIMITER = rf"(\.?{Regex.VARIABLE}|\${Regex.BYTE}){Regex.NOT_HEXA}"
    BLOB = rf"(?P<operand>([.!]?{Regex.VARIABLE}|\$({Regex.BYTE})+){Regex.NOT_HEXA})(,(?P<delimiter>{DELIMITER}))?"
    STRING = rf'((?P<string_type>desc) )?"(?P<string>({Regex.CHAR})+)"(,(?P<delimiter>{DELIMITER}))?'
    ARRAY_PART = rf'((([.!]?{Regex.VARIABLE}|\$({Regex.BYTE})+){Regex.NOT_HEXA})(,{DELIMITER})?|(desc )?"({Regex.CHAR})+"(,{DELIMITER})?)'
    ARRAY = rf"({ARRAY_PART} *\| *)+{ARRAY_PART}"
    POINTER = rf"(?P<relative>r)?ptr (?P<operand>(\${Regex.WORD})|!{Regex.VARIABLE})"


class InstructionRegex:
    IMMEDIATE_MODE = rf"#{Regex.OP_VALUE}"
    ABSOLUTE_MODE = rf"{Regex.OP_VALUE}(,[SXY])?"
    DIRECT_MODE = rf"\({Regex.OP_VALUE}(,X\)|\),Y|,S\),Y|\))"
    DIRECT_LONG_MODE = rf"\[{Regex.OP_VALUE}\](,Y)?"
    OPERAND = rf"{IMMEDIATE_MODE}(,{IMMEDIATE_MODE})?|{DIRECT_MODE}|{DIRECT_LONG_MODE}|{ABSOLUTE_MODE}"
    INSTRUCTION = rf"(?P<command>[A-Z]{{3}})( (?P<operand>{OPERAND}))?"
