import os
import readline
import sys
from contextlib import suppress
from pathlib import Path
from typing import Optional

from app.command import Command
from app.command_processor import DEFAULT_HANDLERS, processor
from app.exceptions import ExitError

PATH = os.environ.get("PATH", "")
HISTFILE = os.environ.get("HISTFILE", "")


def write(line: str, is_stdout: bool, is_add: bool, filename: Optional[str]) -> None:
    if filename:
        write_mode = "a" if is_add else "w"
        with open(filename, write_mode) as text_file:
            text_file.write(line)
    elif is_stdout:
        sys.stdout.write(line)
    else:
        sys.stderr.write(line)


def write_all(
    stdout_lines: list[str],
    stderr_lines: list[str],
    command: Command,
) -> None:
    stdout = "\n".join(stdout_lines)
    stdout += "\n" if stdout else ""
    try:
        write(stdout, True, command.stdout_add, filename=command.stdout_file)
    except IsADirectoryError:
        stderr_lines = [f"bash: {command.stdout_file}: Is a directory"]
        command.stderr_file = None

    stderr = "\n".join(stderr_lines)
    stderr += "\n" if stderr else ""
    try:
        write(stderr, False, command.stderr_add, command.stderr_file)
    except IsADirectoryError:
        write(f"bash: {command.stderr_file}: Is a directory\n", True, False, None)


def completer(text: str, state: int) -> str | None:
    shell_builtin = [f"{opt} " for opt in DEFAULT_HANDLERS.keys() if opt.startswith(text)]
    if state < len(shell_builtin):
        return shell_builtin[state]

    index = len(shell_builtin)
    matches: list[str] = []
    for path_dir in PATH.split(os.pathsep):
        matches.extend(map(lambda x: x.name, Path(path_dir).glob(f"{text}*")))
    matches.sort()
    if state - index < len(matches):
        result = matches[state - index]
        if len(matches) == 1:
            return f"{result} "
        else:
            return str(result)
    return None


def main() -> None:
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set bell-style audible")
    if HISTFILE:
        processor(Command(f"history -r {HISTFILE}"))

    with suppress(KeyboardInterrupt, ExitError):
        while True:  # noqa: WPS457
            line = input("$ ").strip()  # noqa: WPS421
            command = Command(line)
            stdout, stderr = processor(command)
            write_all(stdout_lines=stdout, stderr_lines=stderr, command=command)

    if HISTFILE:
        processor(Command(f"history -a {HISTFILE}"))


if __name__ == "__main__":
    main()
