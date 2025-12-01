import sys


def main():
    while True:
        sys.stdout.write("$ ")
        user_input = input()
        if user_input.strip() == "exit":
            break
        sys.stdout.write(f"{user_input}: command not found\n")


if __name__ == "__main__":
    main()
