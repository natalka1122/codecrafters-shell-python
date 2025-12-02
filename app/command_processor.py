import os
import readline
import subprocess
from contextlib import suppress
from pathlib import Path
from types import MappingProxyType
from typing import Callable, Mapping, Optional

from app.command import Command
from app.command_type import CommandType
from app.exceptions import ExitError

CommandResult = tuple[list[str], list[str]]


ArgsHandler = Callable[[Command], CommandResult]

PATH = os.getenv("PATH", "")


class AppendHistory:
    def __init__(self) -> None:
        self.processed = 0

    def __call__(self, filename: str) -> CommandResult:
        current_length = readline.get_current_history_length()
        readline.append_history_file(current_length - self.processed, filename)
        self.processed = readline.get_current_history_length()
        return [], []


append_history = AppendHistory()


def find_executable_file(file_name: str) -> Optional[Path]:
    for path_dir in PATH.split(os.pathsep):
        file_path = Path(path_dir) / file_name
        if os.access(file_path, os.X_OK):
            return file_path
    return None


def do_exit(command: Command) -> CommandResult:
    raise ExitError


def do_echo(command: Command) -> CommandResult:
    return [" ".join(command.args)], []


def do_type(command: Command) -> CommandResult:
    stdout: list[str] = []
    stderr: list[str] = []
    for cmd in command.args:
        if cmd in DEFAULT_HANDLERS:
            stdout.append(f"{cmd} is a shell builtin")
            continue
        file_path = find_executable_file(cmd)
        if file_path is None:
            stderr.append(f"{cmd}: not found")
        else:
            stdout.append(f"{cmd} is {file_path}")
    return stdout, stderr


def do_run_file(command: Command) -> CommandResult:
    file_name = command.cmd_type
    if file_name in DEFAULT_HANDLERS:
        raise NotImplementedError(f"{file_name} is a shell builtin")
    file_path = find_executable_file(file_name)
    if file_path is None:
        return [], [f"{file_name}: not found"]
    else:
        result = subprocess.run(command.tokens, capture_output=True, text=True)
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        return [stdout] if stdout else [], [stderr] if stderr else []


def do_pwd(command: Command) -> CommandResult:
    return [os.getcwd()], []


def read_history(filename: str) -> CommandResult:
    with suppress(OSError):
        readline.read_history_file(filename)
    append_history.processed = readline.get_current_history_length()
    return [], []


def write_history(filename: str) -> CommandResult:
    readline.write_history_file(filename)
    return [], []


def do_history(command: Command) -> CommandResult:
    if len(command.args) == 2:
        if command.args[0] == "-r":
            return read_history(command.args[1])
        if command.args[0] == "-w":
            return write_history(command.args[1])
        if command.args[0] == "-a":
            return append_history(command.args[1])
        return [], ["NotImplementedError"]

    result: list[str] = []
    length = readline.get_current_history_length()
    if len(command.args) > 0:
        start_index = max(0, length - int(command.args[0]))
    else:
        start_index = 0
    for index in range(start_index + 1, length):
        result.append(f"    {index}  {readline.get_history_item(index)}")
    result.append(f"    {length}  {command.text}")
    return result, []


def do_cd(command: Command) -> CommandResult:
    new_dir = command.args[0]
    try:
        os.chdir(new_dir)
    except FileNotFoundError:
        return [], [f"cd: {new_dir}: No such file or directory"]
    return [], []


DEFAULT_HANDLERS: Mapping[str, ArgsHandler] = MappingProxyType(
    {
        CommandType.CD: do_cd,
        CommandType.ECHO: do_echo,
        CommandType.EXIT: do_exit,
        CommandType.HISTORY: do_history,
        CommandType.TYPE: do_type,
        CommandType.PWD: do_pwd,
    }
)


def processor(command: Command) -> CommandResult:
    handler = DEFAULT_HANDLERS.get(command.cmd_type, do_run_file)
    return handler(command)
