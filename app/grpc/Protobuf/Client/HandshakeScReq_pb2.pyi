from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class HandshakeScBeginHandShakeReq(_message.Message):
    __slots__ = ("ClientUid", "ClientMac", "ChallengeTokenEncrypted", "RequestedServerKeyId")
    CLIENTUID_FIELD_NUMBER: _ClassVar[int]
    CLIENTMAC_FIELD_NUMBER: _ClassVar[int]
    CHALLENGETOKENENCRYPTED_FIELD_NUMBER: _ClassVar[int]
    REQUESTEDSERVERKEYID_FIELD_NUMBER: _ClassVar[int]
    ClientUid: str
    ClientMac: str
    ChallengeTokenEncrypted: str
    RequestedServerKeyId: int
    def __init__(self, ClientUid: _Optional[str] = ..., ClientMac: _Optional[str] = ..., ChallengeTokenEncrypted: _Optional[str] = ..., RequestedServerKeyId: _Optional[int] = ...) -> None: ...

class HandshakeScCompleteHandshakeReq(_message.Message):
    __slots__ = ("Accepted",)
    ACCEPTED_FIELD_NUMBER: _ClassVar[int]
    Accepted: bool
    def __init__(self, Accepted: bool = ...) -> None: ...
