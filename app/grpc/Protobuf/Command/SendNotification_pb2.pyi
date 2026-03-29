from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class SendNotification(_message.Message):
    __slots__ = ("MessageMask", "MessageContent", "OverlayIconLeft", "OverlayIconRight", "IsEmergency", "IsSpeechEnabled", "IsEffectEnabled", "IsSoundEnabled", "IsTopmost", "DurationSeconds", "RepeatCounts")
    MESSAGEMASK_FIELD_NUMBER: _ClassVar[int]
    MESSAGECONTENT_FIELD_NUMBER: _ClassVar[int]
    OVERLAYICONLEFT_FIELD_NUMBER: _ClassVar[int]
    OVERLAYICONRIGHT_FIELD_NUMBER: _ClassVar[int]
    ISEMERGENCY_FIELD_NUMBER: _ClassVar[int]
    ISSPEECHENABLED_FIELD_NUMBER: _ClassVar[int]
    ISEFFECTENABLED_FIELD_NUMBER: _ClassVar[int]
    ISSOUNDENABLED_FIELD_NUMBER: _ClassVar[int]
    ISTOPMOST_FIELD_NUMBER: _ClassVar[int]
    DURATIONSECONDS_FIELD_NUMBER: _ClassVar[int]
    REPEATCOUNTS_FIELD_NUMBER: _ClassVar[int]
    MessageMask: str
    MessageContent: str
    OverlayIconLeft: int
    OverlayIconRight: int
    IsEmergency: bool
    IsSpeechEnabled: bool
    IsEffectEnabled: bool
    IsSoundEnabled: bool
    IsTopmost: bool
    DurationSeconds: float
    RepeatCounts: int
    def __init__(self, MessageMask: _Optional[str] = ..., MessageContent: _Optional[str] = ..., OverlayIconLeft: _Optional[int] = ..., OverlayIconRight: _Optional[int] = ..., IsEmergency: bool = ..., IsSpeechEnabled: bool = ..., IsEffectEnabled: bool = ..., IsSoundEnabled: bool = ..., IsTopmost: bool = ..., DurationSeconds: _Optional[float] = ..., RepeatCounts: _Optional[int] = ...) -> None: ...
