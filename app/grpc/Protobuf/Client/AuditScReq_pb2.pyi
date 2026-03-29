from Protobuf.Enum import AuditEvents_pb2 as _AuditEvents_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class AuditScReq(_message.Message):
    __slots__ = ("Event", "Payload", "TimestampUtc")
    EVENT_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    TIMESTAMPUTC_FIELD_NUMBER: _ClassVar[int]
    Event: _AuditEvents_pb2.AuditEvents
    Payload: bytes
    TimestampUtc: int
    def __init__(self, Event: _Optional[_Union[_AuditEvents_pb2.AuditEvents, str]] = ..., Payload: _Optional[bytes] = ..., TimestampUtc: _Optional[int] = ...) -> None: ...
