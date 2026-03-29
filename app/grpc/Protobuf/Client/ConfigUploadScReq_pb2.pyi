from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ConfigUploadScReq(_message.Message):
    __slots__ = ("RequestGuidId", "Payload")
    REQUESTGUIDID_FIELD_NUMBER: _ClassVar[int]
    PAYLOAD_FIELD_NUMBER: _ClassVar[int]
    RequestGuidId: str
    Payload: str
    def __init__(self, RequestGuidId: _Optional[str] = ..., Payload: _Optional[str] = ...) -> None: ...
