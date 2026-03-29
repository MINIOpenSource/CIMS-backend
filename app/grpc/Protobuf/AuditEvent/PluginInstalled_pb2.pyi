from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class PluginInstalled(_message.Message):
    __slots__ = ("PluginId", "Version")
    PLUGINID_FIELD_NUMBER: _ClassVar[int]
    VERSION_FIELD_NUMBER: _ClassVar[int]
    PluginId: str
    Version: str
    def __init__(self, PluginId: _Optional[str] = ..., Version: _Optional[str] = ...) -> None: ...
