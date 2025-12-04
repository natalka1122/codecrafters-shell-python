import os
import readline
from types import MappingProxyType
from typing import Callable, Mapping

from app.command import CommandOne
from app.command_type import CommandType
from app.exceptions import ExitError, NotBuildinError
from app.history import append_history, read_history, write_history
from app.service_functions import find_executable_file, join_or_none
from app.types import CommandResult

ArgsHandler = Callable[[CommandOne], CommandResult]


def do_cd(command: CommandOne) -> CommandResult:
    new_dir = command.args[0]
    try:
        os.chdir(new_dir)
    except FileNotFoundError:
        return None, f"cd: {new_dir}: No such file or directory\n"
    return None, None


def do_echo(command: CommandOne) -> CommandResult:
    return "{}\n".format(" ".join(command.args)), None


def do_exit(command: CommandOne) -> CommandResult:
    raise ExitError


def do_history(command: CommandOne) -> CommandResult:
    if len(command.args) == 2:
        if command.args[0] == "-r":
            return read_history(command.args[1])
        if command.args[0] == "-w":
            return write_history(command.args[1])
        if command.args[0] == "-a":
            return append_history(command.args[1])
        return None, "NotImplementedError"

    length = readline.get_current_history_length()
    if len(command.args) > 0:
        start_index = max(0, length - int(command.args[0]))
    else:
        start_index = 0
    result: list[str] = []
    for index in range(start_index + 1, length):
        result.append(f"    {index}  {readline.get_history_item(index)}")
    result.append(f"    {length}  {command.text}")
    return join_or_none(result), None


def do_type(command: CommandOne) -> CommandResult:  # noqa: WPS210
    stdout_list: list[str] = []
    stderr_list: list[str] = []
    for cmd in command.args:
        if cmd in DEFAULT_HANDLERS:
            stdout_list.append(f"{cmd} is a shell builtin")
            continue
        file_path = find_executable_file(cmd)
        if file_path is None:
            stderr_list.append(f"{cmd}: not found")
        else:
            stdout_list.append(f"{cmd} is {file_path}")
    return join_or_none(stdout_list), join_or_none(stderr_list)


def do_pwd(command: CommandOne) -> CommandResult:
    return "{}\n".format(os.getcwd()), None


def process_builtin(command: CommandOne) -> CommandResult:
    handler = DEFAULT_HANDLERS.get(command.cmd_type)
    if handler is None:
        file_name = command[0]
        file_path = find_executable_file(file_name)
        if file_path is None:
            return None, f"{file_name}: command not found\n"
        raise NotBuildinError
    return handler(command)


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
