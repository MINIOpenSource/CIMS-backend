from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class HeartBeat(_message.Message):
    __slots__ = ("isOnline",)
    ISONLINE_FIELD_NUMBER: _ClassVar[int]
    isOnline: bool
    def __init__(self, isOnline: bool = ...) -> None: ...
