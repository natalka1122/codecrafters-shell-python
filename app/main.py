import os
import sys
from contextlib import suppress
from typing import Optional

from app.command import Command
from app.command_processor import processor
from app.exceptions import ExitError

SHELL_BUILTIN: frozenset[str] = frozenset(("type", "echo", "exit", "pwd", "cd"))
PATH = os.environ.get("PATH", "")


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


def main() -> None:
    with suppress(KeyboardInterrupt, ExitError):
        while True:  # noqa: WPS457
            sys.stdout.write("$ ")
            line = input().strip()
            command = Command(line)
            stdout, stderr = processor(command)
            write_all(stdout_lines=stdout, stderr_lines=stderr, command=command)


if __name__ == "__main__":
    main()
