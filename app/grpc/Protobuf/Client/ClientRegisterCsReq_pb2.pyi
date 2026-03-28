from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ClientRegisterCsReq(_message.Message):
    __slots__ = ("ClientUid", "ClientId", "ClientMac")
    CLIENTUID_FIELD_NUMBER: _ClassVar[int]
    CLIENTID_FIELD_NUMBER: _ClassVar[int]
    CLIENTMAC_FIELD_NUMBER: _ClassVar[int]
    ClientUid: str
    ClientId: str
    ClientMac: str
    def __init__(self, ClientUid: _Optional[str] = ..., ClientId: _Optional[str] = ..., ClientMac: _Optional[str] = ...) -> None: ...
