from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class Retcode(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    Unspecified: _ClassVar[Retcode]
    Success: _ClassVar[Retcode]
    ServerInternalError: _ClassVar[Retcode]
    InvalidRequest: _ClassVar[Retcode]
    HandshakeClientRejected: _ClassVar[Retcode]
    Registered: _ClassVar[Retcode]
    ClientNotFound: _ClassVar[Retcode]
    PairingRequired: _ClassVar[Retcode]
Unspecified: Retcode
Success: Retcode
ServerInternalError: Retcode
InvalidRequest: Retcode
HandshakeClientRejected: Retcode
Registered: Retcode
ClientNotFound: Retcode
PairingRequired: Retcode
