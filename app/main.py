import asyncio
import os
import readline
from contextlib import suppress
from typing import Optional

from app.async_command_processor import process_full
from app.command import CommandFull, CommandOne
from app.exceptions import EmptyCommandError, ExitError
from app.history import append_history, read_history
from app.service_functions import completer, writeln

PATH = os.environ.get("PATH", "")
HISTFILE = os.environ.get("HISTFILE", "")


def write_all(
    stdout: Optional[str],
    stderr: Optional[str],
    command: CommandOne,
) -> None:
    try:
        writeln(stdout, is_stdout=True, filename=command.stdout_file)
    except IsADirectoryError:
        stderr = f"bash: {command.stdout_file}: Is a directory"
        command.stderr_file = None

    try:
        writeln(stderr, is_stdout=False, filename=command.stderr_file)
    except IsADirectoryError:
        writeln(f"bash: {command.stderr_file}: Is a directory\n", is_stdout=True, filename=None)


async def wrapper(command: CommandFull) -> None:
    async for stdout, stderr in process_full(command):
        write_all(stdout=stdout, stderr=stderr, command=command.last_command)


def main() -> None:
    readline.set_completer(completer)
    readline.parse_and_bind("tab: complete")
    readline.parse_and_bind("set bell-style audible")

    if HISTFILE:
        read_history(HISTFILE)

    with suppress(KeyboardInterrupt, ExitError):
        while True:  # noqa: WPS457
            line = input("$ ").strip()  # noqa: WPS421
            try:
                command = CommandFull(line)
            except EmptyCommandError:
                continue
            asyncio.run(wrapper(command))

    if HISTFILE:
        append_history(HISTFILE)


if __name__ == "__main__":
    main()
