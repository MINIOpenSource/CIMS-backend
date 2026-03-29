from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class AppSettingsUpdated(_message.Message):
    __slots__ = ("PropertyName",)
    PROPERTYNAME_FIELD_NUMBER: _ClassVar[int]
    PropertyName: str
    def __init__(self, PropertyName: _Optional[str] = ...) -> None: ...
