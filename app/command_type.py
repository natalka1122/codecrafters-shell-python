from enum import StrEnum


class CommandType(StrEnum):
    CD = "cd"
    ECHO = "echo"
    EXIT = "exit"
    PWD = "pwd"
    TYPE = "type"
