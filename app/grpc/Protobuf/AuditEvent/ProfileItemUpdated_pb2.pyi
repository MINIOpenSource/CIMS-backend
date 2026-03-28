from Protobuf.Enum import ListItemUpdateOperations_pb2 as _ListItemUpdateOperations_pb2
from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class ProfileItemUpdated(_message.Message):
    __slots__ = ("ItemId", "Operation")
    ITEMID_FIELD_NUMBER: _ClassVar[int]
    OPERATION_FIELD_NUMBER: _ClassVar[int]
    ItemId: str
    Operation: _ListItemUpdateOperations_pb2.ListItemUpdateOperations
    def __init__(self, ItemId: _Optional[str] = ..., Operation: _Optional[_Union[_ListItemUpdateOperations_pb2.ListItemUpdateOperations, str]] = ...) -> None: ...
