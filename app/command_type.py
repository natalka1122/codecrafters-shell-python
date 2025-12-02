from enum import StrEnum


class CommandType(StrEnum):
    CD = "cd"
    ECHO = "echo"
    EXIT = "exit"
    HISTORY = "history"
    PWD = "pwd"
    TYPE = "type"
