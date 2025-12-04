import os
import sys
from pathlib import Path
from typing import Optional

PATH = os.getenv("PATH", "")


def find_executable_file(file_name: str) -> Optional[Path]:
    for path_dir in PATH.split(os.pathsep):
        file_path = Path(path_dir) / file_name
        if os.access(file_path, os.X_OK):
            return file_path
    return None


def join_or_none(lines: list[str]) -> Optional[str]:
    return "{}\n".format("\n".join(lines)) if lines else None


def completer(text: str, state: int) -> str | None:  # noqa: WPS210
    from app.builtin import DEFAULT_HANDLERS

    shell_builtin = [f"{opt} " for opt in DEFAULT_HANDLERS.keys() if opt.startswith(text)]
    if state < len(shell_builtin):
        return shell_builtin[state]

    index = len(shell_builtin)
    matches: list[str] = []
    for path_dir in PATH.split(os.pathsep):
        search_path = Path(path_dir).glob(f"{text}*")
        matches.extend(map(lambda x: x.name, search_path))
    matches.sort()
    if state - index < len(matches):
        result = matches[state - index]
        if len(matches) == 1:
            return f"{result} "
        else:
            return result
    return None


def writeln_to_file(line: Optional[str], filename: str) -> None:
    with open(filename, "a") as file:
        if line:
            file.write(line)


def writeln(line: Optional[str], is_stdout: bool, filename: Optional[str]) -> None:
    if filename:
        writeln_to_file(line, filename)
    elif line:
        if is_stdout:
            sys.stdout.write(line)
        else:
            sys.stderr.write(line)


def clear_file_if_needed(filename: str, is_add: bool) -> None:
    if not is_add:
        with open(filename, "w") as file:
            file.write("")
