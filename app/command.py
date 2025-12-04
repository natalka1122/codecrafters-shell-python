import os
import shlex
from typing import Iterator, Optional

from app.exceptions import EmptyCommandError

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
BACKSLASH = "\\"
NEW_LINE = "\n"
BACKTICK = "`"
DOLLAR_SIGN = "$"
HOME_DIR = "~"
SPACE = " "
PIPE = "|"
HOME = os.getenv("HOME", "")


class CommandParser:
    def __init__(self, line: str) -> None:
        self.add_new_item = True
        self.inside_single_quote = False
        self.inside_double_quote = False
        self.is_after_backslash = False
        result: list[str] = []
        for symbol in line:
            if self.inside_single_quote:
                use_symbol = self._process_inside_single_quote(symbol)
            elif self.inside_double_quote:
                use_symbol = self._process_inside_double_quote(symbol)
            else:
                use_symbol = self._process_regular(symbol)

            if use_symbol is not None:
                if self.add_new_item:
                    result.append(use_symbol)
                    self.add_new_item = False
                else:
                    result[-1] += use_symbol
        self.tokens = result

    def __len__(self) -> int:
        return len(self.tokens)

    def __iter__(self) -> Iterator[str]:
        return iter(self.tokens)

    def __getitem__(self, index: int) -> str:
        return self.tokens[index]

    def _process_inside_single_quote(self, symbol: str) -> Optional[str]:
        if not self.inside_single_quote:
            raise NotImplementedError
        if symbol == SINGLE_QUOTE:
            self.inside_single_quote = False
            return None
        return symbol

    def _process_inside_double_quote(self, symbol: str) -> Optional[str]:
        prepend = ""
        if self.is_after_backslash:
            self.is_after_backslash = False
            if symbol in [DOUBLE_QUOTE, BACKSLASH, DOLLAR_SIGN, BACKTICK, NEW_LINE]:
                return symbol
            prepend = BACKSLASH
        if symbol == DOUBLE_QUOTE:
            self.inside_double_quote = False
            return None
        if symbol == BACKSLASH:
            self.is_after_backslash = True
            return None
        if symbol == HOME_DIR:
            return f"{prepend}{HOME}"
        return f"{prepend}{symbol}"

    def _process_regular(self, symbol: str) -> Optional[str]:  # noqa: WPS212
        if self.is_after_backslash:
            self.is_after_backslash = False
            return symbol
        if symbol == SINGLE_QUOTE:
            self.inside_single_quote = True
            return None
        if symbol == DOUBLE_QUOTE:
            self.inside_double_quote = True
            return None
        if symbol == BACKSLASH:
            self.is_after_backslash = True
            return None
        if symbol == SPACE:
            self.add_new_item = True
            return None
        if symbol == HOME_DIR:
            return HOME
        return symbol


class CommandOne:  # noqa: WPS230
    def __init__(self, incoming_tokens: list[str]) -> None:
        self.incoming_tokens = incoming_tokens
        if len(self.incoming_tokens) == 0:
            raise EmptyCommandError
        self.stdout_file: Optional[str] = None
        self.stderr_file: Optional[str] = None
        self.stdout_add: bool = False
        self.stderr_add: bool = False
        self.tokens: list[str] = []
        self.skip_next = False
        for i, token in enumerate(self.incoming_tokens):
            self._process_incoming_token(i, token)
        if len(self.tokens) == 0:
            raise EmptyCommandError
        self.cmd_type = self.tokens[0]
        self.args = self.tokens[1:]
        self.text = " ".join(shlex.quote(arg) for arg in self.tokens)

    def __getitem__(self, index: int) -> str:
        return self.tokens[index]

    def __repr__(self) -> str:
        return str(self.tokens)

    def _process_incoming_token(self, i: int, token: str) -> None:
        if self.skip_next:
            self.skip_next = False
            return
        if token in [">", "1>"]:
            self.stdout_file = self.incoming_tokens[i + 1]
            self.skip_next = True
            return
        if token in [">>", "1>>"]:
            self.stdout_file = self.incoming_tokens[i + 1]
            self.stdout_add = True
            self.skip_next = True
            return
        if token == "2>":
            self.stderr_file = self.incoming_tokens[i + 1]
            self.skip_next = True
            return
        if token == "2>>":
            self.stderr_file = self.incoming_tokens[i + 1]
            self.stderr_add = True
            self.skip_next = True
            return
        self.tokens.append(token)


class CommandFull:
    def __init__(self, line: str) -> None:
        self.commands: list[CommandOne] = []
        tokens = CommandParser(line)
        current_command: list[str] = []
        for token in tokens:
            if token == PIPE:
                self.commands.append(CommandOne(current_command))
                current_command = []
                continue
            current_command.append(token)
        self.commands.append(CommandOne(current_command))
        self.last_command = self.commands[-1]

    def __repr__(self) -> str:
        return str(self.commands)
