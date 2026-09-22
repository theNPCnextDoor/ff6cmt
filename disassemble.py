import json
import tomllib

from lib.assembly.artifact.memory_map import MemoryMap
from lib.assembly.data_structure.instruction.operand import Operand
from src.lib.assembly.artifact.flags import Flags
from src.lib.assembly.artifact.variable import Constant
from src.lib.assembly.bytes import Bytes
from src.lib.assembly.data_structure.string.string import StringTypes
from src.lib.assembly.script.script import Script
from src.lib.assembly.script.helpers import ScriptSection, ScriptMode, SubSection, ArrayPattern
from src.lib.misc.exception import UnrecognizedArrayPattern


def disassemble(configs: dict) -> None:
    sections = []
    memory_map = MemoryMap.from_line(configs["mapping_mode"])
    for el in configs["sections"]:
        anchor = el.get("anchor", None)
        delimiter = el.get("delimiter", None)
        flags = el.get("flags", None)
        string_type = el.get("string_type", None)

        section = ScriptSection(
            start=el["start"],
            end=el["end"],
            mode=getattr(ScriptMode, el["mode"]),
            length=el.get("length", None),
            delimiter=Bytes.from_int(delimiter) if delimiter is not None else None,
            anchor=Operand(memory_map.to_address(anchor)) if anchor is not None else None,
            flags=Flags(m=flags["m"], x=flags["x"]) if flags is not None else None,
            string_type=StringTypes.get_by_name(string_type) if string_type is not None else None
        )

        subsections = list()
        if pattern := el.get("pattern", None):
            section.attributes["pattern"] = pattern
            var_file = el.get("var_file", "variables.json")
            with open(var_file) as f:
                var_dict = json.load(f)
                variables = dict()
                for var_type, var_list in var_dict.items():
                    variables[var_type] = dict()
                    for k, name in var_list.items():
                        value = Bytes.from_str(k)
                        variables[var_type][int(value)] = Constant(value, name)

                section.variables = variables
            if pattern == ArrayPattern.TREASURE_CHESTS:
                for _ in range(5):
                    subsections.append(SubSection(mode=ScriptMode.BLOBS, length=1))
            else:
                raise UnrecognizedArrayPattern(f"Unrecognized ArrayPattern '{pattern}'.")

        elif elements := el.get("subsections", list()):
            for s in elements:
                subsection = SubSection(
                    mode=getattr(ScriptMode, s["mode"]),
                    length=s.get("length", None),
                    delimiter=s.get("delimiter", None),
                )
                if subsection.mode == ScriptMode.STRINGS:
                    section.attributes["string_type"] = StringTypes.get_by_name(el.get("string_type", None))

                subsections.append(subsection)

        section.attributes["sub_sections"] = subsections
        sections.append(section)

    sections.sort()

    script = Script.disassemble(filename=configs["source"], sections=sections, mapping_mode=configs["mapping_mode"])
    script.dump(filename=configs["destination"], debug=configs.get("debug", False))


if __name__ == "__main__":
    with open("config.toml") as f:
        configs = tomllib.loads(f.read())["disassembly"]
    disassemble(configs)
