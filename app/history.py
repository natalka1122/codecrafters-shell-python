import readline
from contextlib import suppress

from app.types import CommandResult


class AppendHistory:
    def __init__(self) -> None:
        self.processed = 0

    def __call__(self, filename: str) -> CommandResult:
        current_length = readline.get_current_history_length()
        readline.append_history_file(current_length - self.processed, filename)
        self.processed = readline.get_current_history_length()
        return None, None


append_history = AppendHistory()


def read_history(filename: str) -> CommandResult:
    with suppress(OSError):
        readline.read_history_file(filename)
    append_history.processed = readline.get_current_history_length()
    return None, None


def write_history(filename: str) -> CommandResult:
    readline.write_history_file(filename)
    return None, None
