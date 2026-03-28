from google.protobuf.internal import enum_type_wrapper as _enum_type_wrapper
from google.protobuf import descriptor as _descriptor
from typing import ClassVar as _ClassVar

DESCRIPTOR: _descriptor.FileDescriptor

class AuditEvents(int, metaclass=_enum_type_wrapper.EnumTypeWrapper):
    __slots__ = ()
    DefaultEvent: _ClassVar[AuditEvents]
    AuthorizeSuccess: _ClassVar[AuditEvents]
    AuthorizeFailed: _ClassVar[AuditEvents]
    AppSettingsUpdated: _ClassVar[AuditEvents]
    ClassChangeCompleted: _ClassVar[AuditEvents]
    ClassPlanUpdated: _ClassVar[AuditEvents]
    TimeLayoutUpdated: _ClassVar[AuditEvents]
    SubjectUpdated: _ClassVar[AuditEvents]
    AppCrashed: _ClassVar[AuditEvents]
    AppStarted: _ClassVar[AuditEvents]
    AppExited: _ClassVar[AuditEvents]
    PluginInstalled: _ClassVar[AuditEvents]
    PluginUninstalled: _ClassVar[AuditEvents]
DefaultEvent: AuditEvents
AuthorizeSuccess: AuditEvents
AuthorizeFailed: AuditEvents
AppSettingsUpdated: AuditEvents
ClassChangeCompleted: AuditEvents
ClassPlanUpdated: AuditEvents
TimeLayoutUpdated: AuditEvents
SubjectUpdated: AuditEvents
AppCrashed: AuditEvents
AppStarted: AuditEvents
AppExited: AuditEvents
PluginInstalled: AuditEvents
PluginUninstalled: AuditEvents
