from Protobuf.Enum import CommandTypes_pb2 as _CommandTypes_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ClientCommandDeliverScReq(_message.Message):
    __slots__ = ("Type", "Payload")
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    Type: _CommandTypes_pb2.CommandTypes
    Payload: bytes
    def __init__(self, Type: _Optional[_Union[_CommandTypes_pb2.CommandTypes, str]] = ..., Payload: _Optional[bytes] = ...) -> None: ...
