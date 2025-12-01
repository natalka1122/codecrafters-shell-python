import sys


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
                else:
                    sys.stdout.write(f"{cmd}: not found\n")
            continue
        sys.stdout.write(f"{user_input}: command not found\n")


if __name__ == "__main__":
    main()
