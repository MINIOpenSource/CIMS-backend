from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class ClassChangeCompleted(_message.Message):
    __slots__ = ("ClassPlanId", "ChangeMode", "SourceClassIndex", "SourceClassSubjectId", "TargetClassIndex", "TargetClassSubjectId", "WriteToSourceClassPlan")
    CLASSPLANID_FIELD_NUMBER: _ClassVar[int]
    CHANGEMODE_FIELD_NUMBER: _ClassVar[int]
    SOURCECLASSINDEX_FIELD_NUMBER: _ClassVar[int]
    SOURCECLASSSUBJECTID_FIELD_NUMBER: _ClassVar[int]
    TARGETCLASSINDEX_FIELD_NUMBER: _ClassVar[int]
    TARGETCLASSSUBJECTID_FIELD_NUMBER: _ClassVar[int]
    WRITETOSOURCECLASSPLAN_FIELD_NUMBER: _ClassVar[int]
    ClassPlanId: str
    ChangeMode: int
    SourceClassIndex: int
    SourceClassSubjectId: str
    TargetClassIndex: int
    TargetClassSubjectId: str
    WriteToSourceClassPlan: bool
    def __init__(self, ClassPlanId: _Optional[str] = ..., ChangeMode: _Optional[int] = ..., SourceClassIndex: _Optional[int] = ..., SourceClassSubjectId: _Optional[str] = ..., TargetClassIndex: _Optional[int] = ..., TargetClassSubjectId: _Optional[str] = ..., WriteToSourceClassPlan: bool = ...) -> None: ...
