from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AppCrashed(_message.Message):
    __slots__ = ("Stacktrace",)
    STACKTRACE_FIELD_NUMBER: _ClassVar[int]
    Stacktrace: str
    def __init__(self, Stacktrace: _Optional[str] = ...) -> None: ...
