from Protobuf.Enum import ConfigTypes_pb2 as _ConfigTypes_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class GetClientConfig(_message.Message):
    __slots__ = ("RequestGuid", "ConfigType")
    REQUESTGUID_FIELD_NUMBER: _ClassVar[int]
    CONFIGTYPE_FIELD_NUMBER: _ClassVar[int]
    RequestGuid: str
    ConfigType: _ConfigTypes_pb2.ConfigTypes
    def __init__(self, RequestGuid: _Optional[str] = ..., ConfigType: _Optional[_Union[_ConfigTypes_pb2.ConfigTypes, str]] = ...) -> None: ...
