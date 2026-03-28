from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class CommandTypes(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DefaultCommand: _ClassVar[CommandTypes]
    Ping: _ClassVar[CommandTypes]
    Pong: _ClassVar[CommandTypes]
    RestartApp: _ClassVar[CommandTypes]
    SendNotification: _ClassVar[CommandTypes]
    DataUpdated: _ClassVar[CommandTypes]
    GetClientConfig: _ClassVar[CommandTypes]
DefaultCommand: CommandTypes
Ping: CommandTypes
Pong: CommandTypes
RestartApp: CommandTypes
SendNotification: CommandTypes
DataUpdated: CommandTypes
GetClientConfig: CommandTypes
