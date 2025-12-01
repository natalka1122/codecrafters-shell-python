import os
import subprocess
import sys
from pathlib import Path
from typing import Callable, Optional

SHELL_BUILTIN = ["type", "echo", "exit"]
PATH = os.environ.get("PATH", "")


def is_executable(x: Path) -> bool:
    return os.access(x, os.X_OK)


def do_echo(data: list[str]) -> None:
    sys.stdout.write(" ".join(data[1:]) + "\n")


def find_file(file_name: str, filter: Optional[Callable[[Path], bool]]) -> Optional[Path]:
    for path_dir in PATH.split(os.pathsep):
        file_path = Path(path_dir) / file_name
        if filter is None or filter(file_path):
            return file_path
    return None


def do_not_found(data: list[str]) -> None:
    sys.stdout.write(f"{data[0]}: command not found\n")


def do_type(data: list[str]) -> None:
    for cmd in data[1:]:
        if cmd in SHELL_BUILTIN:
            sys.stdout.write(f"{cmd} is a shell builtin\n")
            continue
        file_path = find_file(cmd, filter=is_executable)
        if file_path is None:
            sys.stdout.write(f"{cmd}: not found\n")
        else:
            sys.stdout.write(f"{cmd} is {file_path}\n")


def do_run_file(data: list[str]) -> None:
    subprocess.run(data)


def do_pwd() -> None:
    sys.stdout.write(f"{os.getcwd()}\n")


def main() -> None:
    while True:
        sys.stdout.write("$ ")
        user_input_str = input()
        user_input = user_input_str.split(" ")
        if user_input[0] == "exit":
            break
        if user_input[0] == "echo":
            do_echo(user_input)
        elif user_input[0] == "type":
            do_type(user_input)
        elif user_input[0] == "pwd":
            do_pwd()
        else:
            file_name = find_file(user_input[0], filter=is_executable)
            if file_name is None:
                do_not_found(user_input)
            else:
                do_run_file(user_input)


if __name__ == "__main__":
    main()
