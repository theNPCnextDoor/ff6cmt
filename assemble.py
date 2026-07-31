import tomllib
from pathlib import Path

from src.lib.common.script.script import Script


def assemble(configs: dict):
    script_files = []

    for filename in configs["scripts"]:
        file = Path(filename)

        if file.is_dir():
            scripts = [f for f in file.iterdir() if f.is_file()]
            script_files += scripts
        else:
            script_files.append(file)

    script = Script.parse(*script_files)
    script.assemble(input_path=configs["source"], output_path=configs["destination"])


if __name__ == "__main__":
    with open("config.toml") as f:
        configs = tomllib.loads(f.read())["assembly"]
    assemble(configs)
