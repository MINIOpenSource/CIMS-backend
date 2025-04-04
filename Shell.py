#! -*- coding:utf-8 -*-


#region 导入辅助库
import argparse
import asyncio
import json
from json import JSONDecodeError
import os
import sys
import msvcrt
#endregion


#region 预置控制字符
BLACK_CHARACTER = "\033[30m"
RED_CHARACTER = "\033[31m"
GREEN_CHARACTER = "\033[32m"
YELLOW_CHARACTER = "\033[33m"
BLUE_CHARACTER = "\033[34m"
MAGENTA_CHARACTER = "\033[35m"
CYAN_CHARACTER = "\033[36m"
WHITE_CHARACTER = "\033[37m"

BLACK_BACKGROUND = "\033[40m"
RED_BACKGROUND = "\033[41m"
GREEN_BACKGROUND = "\033[42m"
YELLOW_BACKGROUND = "\033[43m"
BLUE_BACKGROUND = "\033[44m"
MAGENTA_BACKGROUND = "\033[45m"
CYAN_BACKGROUND = "\033[46m"
WHITE_BACKGROUND = "\033[47m"

BRIGHT_BLACK_CHARACTER = "\033[90m"
BRIGHT_RED_CHARACTER = "\033[91m"
BRIGHT_GREEN_CHARACTER = "\033[92m"
BRIGHT_YELLOW_CHARACTER = "\033[93m"
BRIGHT_BLUE_CHARACTER = "\033[94m"
BRIGHT_MAGENTA_CHARACTER = "\033[95m"
BRIGHT_CYAN_CHARACTER = "\033[96m"
BRIGHT_WHITE_CHARACTER = "\033[97m"

BRIGHT_BLACK_BACKGROUND = "\033[100m"
BRIGHT_RED_BACKGROUND = "\033[101m"
BRIGHT_GREEN_BACKGROUND = "\033[102m"
BRIGHT_YELLOW_BACKGROUND = "\033[103m"
BRIGHT_BLUE_BACKGROUND = "\033[104m"
BRIGHT_MAGENTA_BACKGROUND = "\033[105m"
BRIGHT_CYAN_BACKGROUND = "\033[106m"
BRIGHT_WHITE_BACKGROUND = "\033[107m"

RESET = "\033[0m"

HIGHLIGHT = "\033[1m"
UNDERLINE = "\033[4m"
BLINK = "\033[5m"
REVERSE = "\033[7m"

FRAME = "\033[51m"
ENCIRCLE = "\033[52m"
OVERLINE = "\033[53m"

MOVE_UP = lambda n: "\033[%dA" % n
MOVE_DOWN = lambda n: "\033[%dB" % n
MOVE_LEFT = lambda n: "\033[%dC" % n
MOVE_RIGHT = lambda n: "\033[%dD" % n

SET_MOUSE_PLACE = lambda y, x: "\033[{};{}H".format(y, x)

CLEAR = "\033[2J"

CLEAR_LINE_AFTER = "\033[K"

MOUSE_DISAPPEAR = "\033?25l"
MOUSE_APPEAR = "\033?25h"

ascii_format = lambda _str: _str.format(BLACK_CHARACTER=BLACK_CHARACTER,
                                        RED_CHARACTER=RED_CHARACTER,
                                        GREEN_CHARACTER=GREEN_CHARACTER)
#endregion


#region 尝试获取窗口尺寸
try:
    columns, lines = os.get_terminal_size()
except OSError:
    print(f"{MAGENTA_BACKGROUND}{BRIGHT_RED_CHARACTER}{UNDERLINE}{HIGHLIGHT}Get terminal size failed, Shell will be closed.{RESET}")
    sys.exit(0)
#endregion


print(f"{CLEAR}{SET_MOUSE_PLACE(0,0)}Loading Server...")


class ServerConnectingFailed(ConnectionRefusedError):
    def __init__(self, *args, **kwargs):
        pass


class IncompletedError(NameError):
    def __init__(self, *args, **kwargs):
        pass


class Shell:
    def __init__(self,
                 *args,
                 address:str="127.0.0.1",
                 port:int=50052,
                 ascii_ctrl:bool=True,
                 **kwargs):
        self.address:str = address
        self.port:int = port
        self.ascii_ctrl:bool = ascii_ctrl
        self.args = args
        self.kwargs = kwargs

        self.websocket = None

    def input_(self, __param:str):
        __input:list[bytes] = []
        while __input[-1] not in (b'\r', b'\n'):
            raise IncompletedError

