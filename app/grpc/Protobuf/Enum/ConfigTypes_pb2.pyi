from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class ConfigTypes(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    UnspecifiedConfig: _ClassVar[ConfigTypes]
    AppSettings: _ClassVar[ConfigTypes]
    Profile: _ClassVar[ConfigTypes]
    CurrentComponent: _ClassVar[ConfigTypes]
    CurrentAutomation: _ClassVar[ConfigTypes]
    Logs: _ClassVar[ConfigTypes]
    PluginList: _ClassVar[ConfigTypes]
UnspecifiedConfig: ConfigTypes
AppSettings: ConfigTypes
Profile: ConfigTypes
CurrentComponent: ConfigTypes
CurrentAutomation: ConfigTypes
Logs: ConfigTypes
PluginList: ConfigTypes
