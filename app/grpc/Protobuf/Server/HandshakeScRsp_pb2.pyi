from Protobuf.Enum import Retcode_pb2 as _Retcode_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class HandshakeScBeginHandShakeRsp(_message.Message):
    __slots__ = ("Retcode", "Message", "ChallengeTokenDecrypted", "ServerPublicKey")
    RETCODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    CHALLENGETOKENDECRYPTED_FIELD_NUMBER: _ClassVar[int]
    SERVERPUBLICKEY_FIELD_NUMBER: _ClassVar[int]
    Retcode: _Retcode_pb2.Retcode
    Message: str
    ChallengeTokenDecrypted: str
    ServerPublicKey: str
    def __init__(self, Retcode: _Optional[_Union[_Retcode_pb2.Retcode, str]] = ..., Message: _Optional[str] = ..., ChallengeTokenDecrypted: _Optional[str] = ..., ServerPublicKey: _Optional[str] = ...) -> None: ...

class HandshakeScCompleteHandshakeRsp(_message.Message):
    __slots__ = ("Retcode", "Message", "SessionId")
    RETCODE_FIELD_NUMBER: _ClassVar[int]
    MESSAGE_FIELD_NUMBER: _ClassVar[int]
    SESSIONID_FIELD_NUMBER: _ClassVar[int]
    Retcode: _Retcode_pb2.Retcode
    Message: str
    SessionId: str
    def __init__(self, Retcode: _Optional[_Union[_Retcode_pb2.Retcode, str]] = ..., Message: _Optional[str] = ..., SessionId: _Optional[str] = ...) -> None: ...
