import os
from typing import Iterator, Optional

SINGLE_QUOTE = "'"
DOUBLE_QUOTE = '"'
BACKSLASH = "\\"
NEW_LINE = "\n"
BACKTICK = "`"
DOLLAR_SIGN = "$"
HOME_DIR = "~"
SPACE = " "
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

    def _process_regular(self, symbol: str) -> Optional[str]:
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


class Command:
    def __init__(self, line: str) -> None:
        tokens = CommandParser(line)
        self.stdout: Optional[str] = None
        self.stderr: Optional[str] = None
        self.stdout_add: bool = False
        self.stderr_add: bool = False
        self.tokens: list[str] = []
        skip_next = False
        for i, token in enumerate(tokens):
            if skip_next:
                skip_next = False
                continue
            if token in [">", "1>"]:
                if i >= len(tokens) - 1:
                    raise NotImplementedError
                self.stdout = tokens[i + 1]
                skip_next = True
                continue
            if token == "2>":
                if i >= len(tokens) - 1:
                    raise NotImplementedError
                self.stderr = tokens[i + 1]
                skip_next = True
                continue
            self.tokens.append(token)
        self.cmd_type = self.tokens[0]
        self.args = self.tokens[1:]

    def __getitem__(self, index: int) -> str:
        return self.tokens[index]
