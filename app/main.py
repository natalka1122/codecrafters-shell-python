import os
import sys
from contextlib import suppress
from typing import Optional

from app.command import Command
from app.command_processor import processor
from app.exceptions import ExitError

SHELL_BUILTIN: frozenset[str] = frozenset(("type", "echo", "exit", "pwd", "cd"))
PATH = os.environ.get("PATH", "")


def write(line: str, is_stdout: bool, filename: Optional[str]) -> None:
    if filename:
        with open(filename, "w") as text_file:
            text_file.write(line)
    elif is_stdout:
        sys.stdout.write(line)
    else:
        sys.stderr.write(line)


def write_all(
    stdout_lines: list[str],
    stderr_lines: list[str],
    stdout_file: Optional[str] = None,
    stderr_file: Optional[str] = None,
) -> None:
    stdout = "\n".join(stdout_lines)
    stdout += "\n" if stdout else ""
    try:
        write(stdout, True, stdout_file)
    except IsADirectoryError:
        stderr_lines = [f"bash: {stdout_file}: Is a directory"]
        stderr_file = None
    stderr = "\n".join(stderr_lines)
    stderr += "\n" if stderr else ""
    try:
        write(stderr, True, stderr_file)
    except IsADirectoryError:
        write(f"bash: {stderr}: Is a directory\n", True, None)


def main() -> None:
    with suppress(KeyboardInterrupt, ExitError):
        while True:  # noqa: WPS457
            sys.stdout.write("$ ")
            line = input().strip()
            command = Command(line)
            stdout, stderr = processor(command)
            write_all(
                stdout_lines=stdout,
                stderr_lines=stderr,
                stdout_file=command.stdout,
                stderr_file=command.stderr,
            )


if __name__ == "__main__":
    main()
