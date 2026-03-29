from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AuthorizeEvent(_message.Message):
    __slots__ = ("Level",)
    LEVEL_FIELD_NUMBER: _ClassVar[int]
    Level: int
    def __init__(self, Level: _Optional[int] = ...) -> None: ...
