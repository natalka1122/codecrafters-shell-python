import os
import sys
from pathlib import Path


def main() -> None:
    while True:
        sys.stdout.write("$ ")
        user_input = input()
        if user_input.strip() == "exit":
            break
        user_input_split = user_input.split(" ")
        if user_input_split[0] == "echo":
            sys.stdout.write(" ".join(user_input_split[1:]) + "\n")
            continue
        if user_input_split[0] == "type":
            for cmd in user_input_split[1:]:
                if cmd in ["type", "echo", "exit"]:
                    sys.stdout.write(f"{cmd} is a shell builtin\n")
                    continue
                path = os.environ.get("PATH", "")
                is_found = False
                for path_dir in path.split(os.pathsep):
                    file_path = Path(path_dir) / cmd
                    if os.access(file_path, os.X_OK):
                        is_found = True
                        sys.stdout.write(f"{cmd} is {file_path}\n")
                        break
                if not is_found:
                    sys.stdout.write(f"{cmd}: not found\n")
            continue
        sys.stdout.write(f"{user_input}: command not found\n")


if __name__ == "__main__":
    main()
