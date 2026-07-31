import json
import tomllib

from src.lib.assembly.artifact.flags import Flags
from src.lib.assembly.artifact.variable import Constant
from src.lib.common.bytes import Bytes
from src.lib.assembly.data_structure.string.string import StringTypes
from src.lib.common.script.script import Script
from src.lib.common.script.helpers import ScriptSection, ScriptMode, SubSection, ArrayPattern
from src.lib.misc.exception import UnrecognizedArrayPattern


def disassemble(configs: dict) -> None:
    sections = []
    for el in configs["sections"]:
        section = ScriptSection(
            start=el["start"],
            end=el["end"],
            mode=getattr(ScriptMode, el["mode"]),
            length=el.get("length", None),
            delimiter=el.get("delimiter", None),
        )

        if flags := el.get("flags", None):
            section.attributes["flags"] = Flags(m=flags["m"], x=flags["x"])

        if section.mode == ScriptMode.STRINGS:
            section.attributes["string_type"] = StringTypes.get_by_name(el.get("string_type", None))

        section.attributes["threads"] = {int(k, 16): int(v) for k, v in el.get("threads", dict()).items()}

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
