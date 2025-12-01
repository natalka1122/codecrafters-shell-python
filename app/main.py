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
        sys.stdout.write(f"{user_input}: command not found\n")


if __name__ == "__main__":
    main()
