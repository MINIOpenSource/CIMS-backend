from Protobuf.Enum import CommandTypes_pb2 as _CommandTypes_pb2
from Protobuf.Enum import Retcode_pb2 as _Retcode_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ClientCommandDeliverScRsp(_message.Message):
    __slots__ = ("RetCode", "Type", "Payload")
    RETCODE_FIELD_NUMBER: _ClassVar[int]
    TYPE_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    RetCode: _Retcode_pb2.Retcode
    Type: _CommandTypes_pb2.CommandTypes
    Payload: bytes
    def __init__(self, RetCode: _Optional[_Union[_Retcode_pb2.Retcode, str]] = ..., Type: _Optional[_Union[_CommandTypes_pb2.CommandTypes, str]] = ..., Payload: _Optional[bytes] = ...) -> None: ...
