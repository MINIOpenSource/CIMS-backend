#! -*- coding:utf-8 -*-


#region 导入辅助库
import argparse
import asyncio
import json
from json import JSONDecodeError
import os
import sys
#endregion


class CLI:
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
