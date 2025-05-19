# ClassIsland 集控与客户端 API 及配置文件文档

本文档旨在说明 ClassIsland 客户端与其集控后端（CIMS-backend）之间的 API 交互，以及相关的配置文件结构。

## 概述

ClassIsland 客户端通过 HTTP API 从集控后端获取配置清单（Manifest）和具体的配置文件。集控后端同时提供 gRPC 服务用于客户端注册和实时指令下发。此外，集控后端还有一个内部 HTTP API 用于管理服务器本身。

## 1. 客户端 API (供 ClassIsland 客户端实例使用)

这些 API 由 `ManagementServer/api.py` (或 `ManagementServer.vercel/api.py`) 提供。

### 1.1 获取客户端配置清单 (Manifest)

客户端首先请求此接口以获取其专属的配置资源清单。

*   **Endpoint**: `GET /api/v1/client/{client_uid}/manifest`
*   **Path Parameters**:
    *   `client_uid` (string, 必选): 客户端的唯一标识符 (UUID)。
*   **Query Parameters**:
    *   `version` (integer, 可选): 客户端当前配置的版本号（通常是时间戳）。服务器用此判断是否需要更新。如果未提供，服务器通常会返回最新的配置。
*   **请求示例**:
    `GET /api/v1/client/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx/manifest?version=1678886400`
*   **响应格式**: `application/json`
*   **响应成功 (200 OK)**:
    ```json
    {
        "ClassPlanSource": { // 课表源信息
            "Value": "/api/v1/client/ClassPlan?name=default_classplan", // 获取课表的URL路径
            "Version": 1678886401 // 课表版本
        },
        "TimeLayoutSource": { // 时间表源信息
            "Value": "/api/v1/client/TimeLayout?name=default_timelayout",
            "Version": 1678886402
        },
        "SubjectsSource": { // 科目源信息
            "Value": "/api/v1/client/Subjects?name=default_subjects",
            "Version": 1678886403
        },
        "DefaultSettingsSource": { // 默认客户端设置源信息
            "Value": "/api/v1/client/DefaultSettings?name=default_settings",
            "Version": 1678886404
        },
        "PolicySource": { // 策略源信息
            "Value": "/api/v1/client/Policy?name=default_policy",
            "Version": 1678886405
        },
        "ServerKind": 0, // 服务器类型 (0: Serverless, 1: ManagementServer)
        "OrganizationName": "我的学校" // 组织名称
    }
    ```
    *   `Value` 字段中的 URL 是相对于服务器 API Host 的路径。客户端需要将服务器的 Host 和 Port （以及可能的 http/https 前缀）与此路径拼接。
    *   如果 `profile_config` 中未找到 `client_uid` 对应的配置，则会使用默认的资源名称（如 `default_classplan`）。

### 1.2 获取具体配置文件

客户端根据 Manifest 中获取到的 URL 来请求具体的配置文件。

*   **Endpoint**: `GET /api/v1/client/{resource_type}`
*   **Path Parameters**:
    *   `resource_type` (string, 必选): 资源类型，例如 `ClassPlan`, `TimeLayout`, `Subjects`, `DefaultSettings`, `Policy`。
*   **Query Parameters**:
    *   `name` (string, 必选): 资源文件的名称 (不含扩展名)，例如 `default_classplan`。
*   **请求示例**:
    `GET /api/v1/client/ClassPlan?name=default_classplan`
*   **响应格式**: `application/json`
*   **响应成功 (200 OK)**:
    响应体是对应资源类型的 JSON 内容。具体结构见下文“配置文件结构说明”。
    例如，请求 `/api/v1/client/Policy?name=default_policy` 会返回 `ManagementPolicy` 结构的 JSON。
*   **响应失败**:
    *   `404 Not Found`: 如果请求的资源不存在。

## 2. 命令 API (供服务器管理使用)

这些 API 由 `ManagementServer/command.py` 提供，用于服务器的内部管理和维护。

### 2.1 配置文件管理 (`/command/datas/{resource_type}/...`)

*   `resource_type` 可以是: `ClassPlan`, `DefaultSettings`, `Policy`, `Subjects`, `TimeLayout`, `ProfileConfig`, `Clients`, `ClientStatus`。

    *   **创建配置文件**: `GET /command/datas/{resource_type}/create?name=<filename>`
        *   创建一个新的空配置文件。
        *   响应: JSON `{"status": "success/error", "message": "..."}`

    *   **删除配置文件**: `DELETE /command/datas/{resource_type}/delete?name=<filename>` (也支持GET)
        *   删除指定的配置文件。
        *   响应: JSON `{"status": "success/error", "message": "..."}`

    *   **列出配置文件**: `GET /command/datas/{resource_type}/list`
        *   列出指定资源类型下的所有配置文件名。
        *   响应: JSON `["filename1", "filename2", ...]`

    *   **重命名配置文件**: `PUT /command/datas/{resource_type}/rename?name=<old_name>&target=<new_name>`
        *   重命名配置文件。
        *   响应: JSON `{"status": "success/error", "message": "..."}`

    *   **写入配置文件**: `PUT /command/datas/{resource_type}/write?name=<filename>` (也支持POST, GET)
        *   **Request Body**: 对应资源类型的 JSON 内容。
        *   响应: JSON `{"status": "success/error", "message": "..."}`

### 2.2 服务器管理 (`/command/server/...`)

    *   **获取服务器配置**: `GET /command/server/settings`
        *   响应: 服务器 `settings.json` 的内容。

    *   **更新服务器配置**: `PUT /command/server/settings` (也支持POST)
        *   **Request Body**: 新的服务器 `settings.json` 内容。
        *   响应: JSON `{"status": "success"}`

    *   **获取服务器信息**: `GET /command/server/info` (旧版本为 `/command/server/version`)
        *   响应: JSON `{"version": "backend_version_string"}`

    *   **下载集控预设配置**: `GET /command/download/preset` (旧版本为 `/command/server/ManagementPreset.json`)
        *   下载一个包含默认配置的 `cims_preset_config.zip` 文件。
        *   响应: `application/zip`

    *   **导出服务器数据**: `GET /command/export/data` (旧版本为 `/command/server/export`)
        *   下载包含所有服务器数据的 `cims_export_YYYYMMDD_HHMMSS.zip` 文件。
        *   响应: `application/zip`

### 2.3 客户端管理 (`/command/clients/...`)

    *   **列出已注册客户端**: `GET /command/clients/list`
        *   响应: JSON `["client_uid_1", "client_uid_2", ...]` (从 `Datas/Clients.json` 读取)

    *   **获取客户端状态**: `GET /command/clients/status`
        *   响应: JSON 列表，每个对象包含:
            ```json
            [
              {
                "uid": "client_uid_1",
                "name": "client_id_from_registration_or_Clients.json",
                "status": "online/offline/unknown", // "unknown"表示仅在Clients.json中存在
                "lastHeartbeat": "YYYY-MM-DDTHH:MM:SS.ffffffZ", // ISO 8601 格式, UTC
                "ip": "client_ip_address" // 从gRPC元数据中获取
              }
            ]
            ```

    *   **获取单个客户端详情**: `GET /command/client/{client_uid}/details`
        *   响应: JSON 对象，合并 `/status` 的信息与 `Datas/ProfileConfig.json` 中对应客户端的配置。
            ```json
            {
              "uid": "client_uid_1",
              "name": "client_id_1",
              "status": "online",
              "lastHeartbeat": "...",
              "ip": "...",
              "profileConfig": { // 来自 ProfileConfig.json
                "ClassPlan": "plan_name_for_client_1",
                "TimeLayout": "layout_name_for_client_1",
                // ... 其他资源类型
              },
              "isPreRegistered": true/false // 如果在 pre_registers 中找到
            }
            ```

    *   **预注册客户端**: `POST /command/clients/pre_register` (也支持PUT, GET)
        *   **Request Body**:
            ```json
            {
              "id": "client_uid_to_pre_register",
              "config": {
                "ClassPlan": "plan_name",
                "TimeLayout": "layout_name",
                // ...
              }
            }
            ```
        *   响应: JSON `{"status": "success"}`

    *   **列出预注册客户端**: `GET /command/clients/pre_registered/list`
        *   响应: JSON `[{"id": "client_uid", "config": {...}}, ...]`

    *   **删除预注册客户端**: `DELETE /command/clients/pre_registered/delete?client_id=<client_uid>`
        *   响应: JSON `{"status": "success/error", "message": "..."}`

    *   **更新预注册客户端配置**: `PUT /command/clients/pre_registered/update`
        *   **Request Body**: 同预注册。
        *   响应: JSON `{"status": "success/error", "message": "..."}`

### 2.4 指令下发 (`/command/client/{client_uid}/...`)

    *   **重启客户端应用**: `GET /command/client/{client_uid}/restart`
        *   通过 gRPC 向客户端发送 `RestartApp` 指令。
        *   响应: JSON `{"status": "success/error", "message": "..."}`

    *   **通知客户端更新数据**: `GET /command/client/{client_uid}/update_data`
        *   通过 gRPC 向客户端发送 `DataUpdated` 指令。
        *   响应: JSON `{"status": "success/error", "message": "..."}`

    *   **发送通知到客户端**: `POST /command/client/{client_uid}/send_notification`
        *   **Request Body** (SendNotification protobuf 消息的 JSON 表示):
            ```json
            {
                "message_mask": "遮罩文本",
                "message_content": "通知正文内容",
                "overlay_icon_left": 0,  // 通常不用
                "overlay_icon_right": 0, // 通常不用
                "is_emergency": false,   // 是否紧急
                "is_speech_enabled": true,
                "is_effect_enabled": true,
                "is_sound_enabled": true,
                "is_topmost": true,
                "duration_seconds": 10.0, // 单次显示时长（秒）
                "repeat_counts": 1        // 重复次数
            }
            ```
        *   通过 gRPC 向客户端发送 `SendNotification` 指令。
        *   响应: JSON `{"status": "success/error", "message": "..."}`

    *   **批量操作**: `POST /command/client/batch_action`
        *   **Request Body**:
            ```json
            {
                "action": "restartApp" | "updateData" | "sendNotification",
                "clients": ["client_uid_1", "client_uid_2"],
                "payload": { /* 如果 action 是 sendNotification，则这里是 SendNotification 的 JSON */ }
            }
            ```
        *   响应: JSON 数组，每个元素对应一个客户端的操作结果 `[{"uid": "...", "status": "success/error", "message": "..."}, ...]`

### 2.5 其他

    *   **刷新服务器配置**: `GET /api/refresh`
        *   重新加载服务器的 `settings.json`。
        *   响应: 无内容 (200 OK)

## 3. gRPC API

由 `ManagementServer/gRPC.py` 和 `Protobuf/` 目录下的 `.proto` 文件定义。

### 3.1 Service: `ClientRegister`

    *   **RPC: `Register`**
        *   **Request**: `ClientRegisterCsReq`
            ```protobuf
            message ClientRegisterCsReq {
                string clientUid = 1; // 客户端唯一ID (UUID)
                string clientId = 2;  // 用户定义的客户端ID (可选)
            }
            ```
        *   **Response**: `ClientRegisterScRsp`
            ```protobuf
            message ClientRegisterScRsp {
                Enum.Retcode retcode = 1; // 返回码
                string message = 2;       // 消息
            }
            ```
        *   **逻辑**:
            1.  检查 `clients.json` 中是否存在该 `clientUid`。
            2.  如果不存在，则将其添加到 `clients.json`，并使用 `client_id` (如果提供) 或 `client_uid` 的前8位作为名称。
            3.  如果客户端在 `pre_registers.json` 中，则将其配置应用到 `profile_config.json` 并从 `pre_registers.json` 中移除。
            4.  返回 `Registered` (首次) 或 `Success` (已存在)。

    *   **RPC: `UnRegister`**
        *   **Request**: `ClientRegisterCsReq` (同上)
        *   **Response**: `ClientRegisterScRsp` (同上)
        *   **逻辑**:
            1.  从 `clients.json` 和 `profile_config.json` 中移除该客户端信息。
            2.  返回 `Success`。

### 3.2 Service: `ClientCommandDeliver`

    *   **RPC: `ListenCommand`** (双向流)
        *   客户端通过 gRPC Metadata 发送 `cuid` (客户端UID)。
        *   **Client -> Server**: `stream ClientCommandDeliverScReq`
            ```protobuf
            message ClientCommandDeliverScReq {
              Enum.CommandTypes Type = 2; // 通常是 Ping
              bytes Payload = 3;          // 通常是 HeartBeat 消息序列化后的字节
            }
            ```
            *   `HeartBeat.proto`:
                ```protobuf
                message HeartBeat {
                    bool isOnline = 1; // 通常为 true
                }
                ```
        *   **Server -> Client**: `stream ClientCommandDeliverScRsp`
            ```protobuf
            message ClientCommandDeliverScRsp {
                Enum.Retcode RetCode = 1;
                Enum.CommandTypes Type = 2; // 例如 Pong, RestartApp, SendNotification, DataUpdated
                bytes Payload = 3;          // 如果 Type 是 SendNotification，则是 SendNotification 消息序列化后的字节
            }
            ```
            *   `SendNotification.proto`:
                ```protobuf
                message SendNotification {
                  string MessageMask=1;
                  string MessageContent=2;
                  int32 OverlayIconLeft=3;
                  int32 OverlayIconRight=4;
                  bool IsEmergency=5;
                  bool IsSpeechEnabled=6;
                  bool IsEffectEnabled=7;
                  bool IsSoundEnabled=8;
                  bool IsTopmost=9;
                  double DurationSeconds=10;
                  int32 RepeatCounts=11;
                }
                ```
        *   **逻辑**:
            1.  服务器维护一个活动客户端连接的字典。
            2.  客户端连接后，定期发送 `Ping` + `HeartBeat`。
            3.  服务器收到 `Ping` 后，更新客户端状态 (最后心跳时间、IP)，并回复 `Pong`。
            4.  当有指令 (如通过 Command API 发送的) 需要下发给特定客户端时，服务器通过此流将指令发送给对应的客户端。
            5.  如果连接断开或超时，服务器将客户端标记为离线。

### 3.3 枚举 (Enums)

    *   **`CommandTypes.proto`**:
        *   `DefaultCommand` (0)
        *   `ServerConnected` (1): 服务器连接成功 (客户端可能未使用)
        *   `Ping` (2): 客户端心跳请求
        *   `Pong` (3): 服务器心跳响应
        *   `RestartApp` (4): 指令客户端重启
        *   `SendNotification` (5): 指令客户端发送通知
        *   `DataUpdated` (6): 指令客户端其配置数据已更新

    *   **`Retcode.proto`**:
        *   `None` (0)
        *   `Success` (200): 操作成功
        *   `ServerInternalError` (500): 服务器内部错误
        *   `InvalidRequest` (404): 无效请求 (gRPC 中通常用作资源未找到等)
        *   `Registered` (10001): (ClientRegister) 客户端首次注册成功
        *   `ClientNotFound` (10002): (ClientRegister) 客户端未找到 (例如在 UnRegister 时)

## 4. 配置文件结构说明

所有配置文件均存储在服务器的 `Datas/` 目录下，并按资源类型分子目录。

### 4.1 服务器设置 (`settings.json`)

位于服务器根目录。

```json
{
    "api": {
        "host": "0.0.0.0",    // API 服务监听的主机
        "port": 50050,        // API 服务监听的端口
        "prefix": "http"      // API 服务URL前缀 (http 或 https)
    },
    "gRPC": {
        "host": "0.0.0.0",    // gRPC 服务监听的主机
        "port": 50051         // gRPC 服务监听的端口
    },
    "command": {
        "host": "0.0.0.0",    // Command API 服务监听的主机
        "port": 50052         // Command API 服务监听的端口
    },
    "organization_name": "我的学校" // 组织名称，会显示在客户端
}
```

### 4.2 客户端注册信息 (`Datas/Clients.json`)

存储已注册的客户端信息。

```json
{
    "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx": { // Client UID
        "name": "Client-001" // 用户定义的客户端ID或UID前8位
    },
    // ... 更多客户端
}
```

### 4.3 客户端状态 (`Datas/ClientStatus.json`)

存储客户端的在线状态和心跳信息。

```json
{
    "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx": { // Client UID
        "lastHeartbeat": "YYYY-MM-DDTHH:MM:SS.ffffffZ", // ISO 8601 UTC
        "ip": "192.168.1.100",
        "isOnline": true/false // 根据心跳判断
    },
    // ... 更多客户端
}
```

### 4.4 客户端配置文件映射 (`Datas/ProfileConfig.json`)

定义每个客户端使用哪些具体的配置文件。

```json
{
    "profile_config": {
        "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx": { // Client UID
            "ClassPlan": "plan_name_1",         // 使用名为 plan_name_1.json 的课表
            "TimeLayout": "layout_name_1",      // 使用名为 layout_name_1.json 的时间表
            "Subjects": "subjects_name_1",      // ...
            "DefaultSettings": "settings_name_1",
            "Policy": "policy_name_1"
        }
        // ... 更多客户端的配置映射
    },
    "pre_registers": { // 预注册的客户端
        "yyyyyyyy-yyyy-yyyy-yyyy-yyyyyyyyyyyy": { // Client UID
            "id": "Optional-Client-ID-Name",      // 可选的客户端易记名称
            "config": {                           // 该客户端注册时自动应用的配置
                "ClassPlan": "plan_name_for_pre_reg",
                // ...
            }
        }
    }
}
```

### 4.5 课表 (`Datas/ClassPlan/<name>.json`)

结构与 ClassIsland 客户端的 `Profile.ClassPlans` 中的单个 `ClassPlan` 对象类似。

```json
{
    "TimeLayoutId": "guid_of_timelayout",
    "TimeRule": { // 触发规则
        "WeekDay": 1, // 0=周日, 1=周一, ...
        "WeekCountDiv": 0, // 0=不分单双周, 1=第一周/单周, 2=第二周/双周 ...
        "WeekCountDivTotal": 0 // 0 或 2=双周轮换, 3=三周轮换, 4=四周轮换
    },
    "Classes": [ // 课程列表，顺序对应时间表中上课类型的时间点
        {
            "SubjectId": "guid_of_subject",
            "IsChangedClass": false, // 是否为临时换课标记
            "AttachedObjects": { /* ... */ } // 附加设置
        }
        // ... 更多课程
    ],
    "Name": "高一(1)班课表",
    "IsOverlay": false,
    "OverlaySourceId": null,
    "OverlaySetupTime": "YYYY-MM-DDTHH:MM:SSZ",
    "IsEnabled": true,
    "AssociatedGroup": "guid_of_classplan_group", // 课表组ID
    "AttachedObjects": { /* ... */ } // 附加设置
}
```

### 4.6 时间表 (`Datas/TimeLayout/<name>.json`)

结构与 ClassIsland 客户端的 `Profile.TimeLayouts` 中的单个 `TimeLayout` 对象类似。

```json
{
    "Name": "夏季作息时间",
    "Layouts": [
        {
            "StartSecond": "YYYY-MM-DDT08:00:00Z", // 时间的日期部分不重要，主要用时间部分
            "EndSecond": "YYYY-MM-DDT08:45:00Z",
            "TimeType": 0, // 0=上课, 1=课间, 2=分割线, 3=行动
            "IsHideDefault": false,
            "DefaultClassId": "guid_of_default_subject_for_this_slot",
            "BreakName": "课间休息", // 仅当 TimeType=1 时有效
            "ActionSet": { // 仅当 TimeType=3 时有效 (见 ActionSet 结构)
                /* ... */
            },
            "AttachedObjects": { /* ... */ }
        }
        // ... 更多时间点
    ],
    "AttachedObjects": { /* ... */ }
}
```

### 4.7 科目 (`Datas/Subjects/<name>.json`)

结构与 ClassIsland 客户端的 `Profile.Subjects` 对象类似（是一个以科目GUID为键，科目对象为值的字典）。

```json
{
    "guid_of_subject_1": {
        "Name": "语文",
        "Initial": "语",
        "TeacherName": "张老师",
        "IsOutDoor": false,
        "AttachedObjects": { /* ... */ }
    },
    "guid_of_subject_2": {
        // ...
    }
}
```

### 4.8 课表组 (`Datas/ClassPlanGroup/<name>.json`)

这个文件不是由服务器直接分发，而是 `Profile.json` 的一部分。但如果服务器要管理课表组，其结构与 ClassIsland 客户端 `Profile.ClassPlanGroups` 中的单个 `ClassPlanGroup` 对象类似。
在服务器端，课表组信息通常内嵌在 `ClassPlan` 的 `AssociatedGroup` 字段（GUID）中，并在客户端 `Profile.json` 中查找具体信息。
服务器可以分发一个完整的 `Profile.json` 文件作为 `DefaultSettings` 或自定义资源类型的一部分，其中就包含 `ClassPlanGroups`。

```json
// 这是 Profile.json 中 ClassPlanGroups 的一部分
{
    // ...其他Profile属性
    "ClassPlanGroups": {
        "ACAF4EF0-E261-4262-B941-34EA93CB4369": { // DefaultGroupGuid
            "Name": "默认课表组",
            "IsGlobal": false
        },
        "00000000-0000-0000-0000-000000000000": { // GlobalGroupGuid
            "Name": "全局课表群",
            "IsGlobal": true
        },
        "guid_of_custom_group_1": {
            "Name": "高一年级",
            "IsGlobal": false
        }
    }
    // ...
}
```

### 4.9 预定日程 (`Datas/OrderedSchedule/<name>.json`)

这个文件不是由服务器直接分发，而是 `Profile.json` 的一部分。
在服务器端，预定日程信息通常内嵌在 `Profile.json` 的 `OrderedSchedules` 字段中。
服务器可以分发一个完整的 `Profile.json` 文件作为 `DefaultSettings` 或自定义资源类型的一部分，其中就包含 `OrderedSchedules`。

```json
// 这是 Profile.json 中 OrderedSchedules 的一部分
{
    // ...其他Profile属性
    "OrderedSchedules": {
        "YYYY-MM-DDTHH:MM:SSZ": { // 日期键 (通常只有日期部分有效)
            "ClassPlanId": "guid_of_class_plan_for_this_date"
        }
        // ... 更多预定
    }
    // ...
}
```

### 4.10 默认客户端设置 (`Datas/DefaultSettings/<name>.json`)

结构与 ClassIsland 客户端的 `Settings.json` (`ClassIsland.Models.Settings`) 对象类似。包含客户端的各种行为和外观设置。

```json
{
    "Theme": 2, // 0=跟随系统, 1=亮色, 2=暗色
    "IsCustomBackgroundColorEnabled": false,
    "BackgroundColor": "ARGB Hex, e.g., #FF000000",
    "PrimaryColor": "ARGB Hex",
    "SecondaryColor": "ARGB Hex",
    "SingleWeekStartTime": "YYYY-MM-DDTHH:MM:SSZ",
    // ... 大量其他客户端设置，参考 ClassIsland/Models/Settings.cs
    "WindowDockingLocation": 1, // 0-5
    "Opacity": 0.5,
    "Scale": 1.0,
    "CurrentComponentConfig": "Default", // 组件配置方案名
    "IsAutomationEnabled": false,
    "CurrentAutomationConfig": "Default", // 自动化配置方案名
    // ...
}
```

### 4.11 策略 (`Datas/Policy/<name>.json`)

结构与 ClassIsland 客户端的 `ManagementPolicy.cs` 对象类似。

```json
{
    "DisableProfileEditing": false,           // 禁止编辑档案（所有内容）
    "DisableProfileClassPlanEditing": false,  // 禁止编辑课表
    "DisableProfileTimeLayoutEditing": false, // 禁止编辑时间表
    "DisableProfileSubjectsEditing": false,   // 禁止编辑科目
    "DisableSettingsEditing": false,          // 禁止编辑应用设置
    "DisableSplashCustomize": false,        // 禁止自定义启动画面
    "DisableDebugMenu": true,               // 禁用调试菜单
    "AllowExitManagement": true,            // 允许客户端主动退出集控
    "DisableEasterEggs": false              // 禁用彩蛋
}
```

### 4.12 行动 (`Action.cs`, `ActionSet.cs`)

通常嵌套在 `TimeLayoutItem` (当 `TimeType` 为3时) 或自动化工作流中。

```json
// ActionSet 结构
{
    "IsEnabled": true,
    "Name": "我的行动组",
    "Guid": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx", // 内部标识
    "IsOn": false, // 运行时状态，标记是否已触发但未恢复
    "IsRevertEnabled": true, // 是否启用规则不再满足时的自动恢复
    "Actions": [
        // Action 结构数组
        {
            "Id": "classisland.os.run", // 行动类型ID
            "Settings": { // 特定于行动类型的设置
                "Value": "notepad.exe",
                "Args": ""
            }
        },
        {
            "Id": "classisland.settings.theme",
            "Settings": {
                "Value": 1 // 0=系统, 1=亮, 2=暗
            }
        }
    ]
}
```

### 4.13 规则集 (`Ruleset.cs`, `RuleGroup.cs`, `Rule.cs`)

用于自动化和组件隐藏等条件判断。

```json
// Ruleset 结构
{
    "Mode": 0, // 0=Or (任意组满足), 1=And (所有组满足)
    "IsReversed": false, // 是否反转整个规则集的判断结果
    "Groups": [
        // RuleGroup 结构数组
        {
            "Rules": [
                // Rule 结构数组
                {
                    "IsReversed": false, // 是否反转此规则的判断结果
                    "Id": "classisland.lessons.timeState", // 规则ID
                    "Settings": { // 特定于规则的设置
                        "State": 1 // 0=None, 1=OnClass, 2=Prepare, 3=Breaking, 4=AfterSchool
                    }
                },
                {
                    "Id": "classisland.windows.className",
                    "Settings": {
                        "Text": "Notepad",
                        "UseRegex": false
                    }
                }
            ],
            "Mode": 1, // 0=Or (任意规则满足), 1=And (所有规则满足)
            "IsReversed": false, // 是否反转此规则组的判断结果
            "IsEnabled": true
        }
        // ...更多规则组
    ]
}
```

### 4.14 附加设置 (`AttachableSettingsObject` 的 `AttachedObjects` 属性)

这是一个通用的键值对结构，用于在各种配置对象（如`Subject`, `TimeLayoutItem`, `ClassPlan`, `TimeLayout`）上附加额外的、由插件或核心功能定义的特定设置。

*   **键 (string)**: 附加设置的唯一 GUID。
*   **值 (object)**: 对应附加设置的具体配置对象。其结构由定义该附加设置的模块/插件决定。

**通用结构**:
```json
"AttachedObjects": {
    "GUID_OF_ATTACHED_SETTING_1": {
        "IsAttachSettingsEnabled": true, // 或 false，控制此附加设置是否在此对象上生效
        // ...特定于此附加设置的其他属性
        "SomeProperty": "SomeValue",
        "AnotherProperty": 123
    },
    "GUID_OF_ATTACHED_SETTING_2": {
        "IsAttachSettingsEnabled": false,
        // ...
    }
}
```
例如，在 `Subject` 对象中，一个用于课程提醒的附加设置可能如下：
```json
// In a Subject object
"AttachedObjects": {
    "08F0D9C3-C770-4093-A3D0-02F3D90C24BC": { // ClassNotificationAttachedSettings GUID
        "IsAttachSettingsEnabled": true,
        "IsClassOnNotificationEnabled": true,
        "IsClassOnPreparingNotificationEnabled": true,
        "IsClassOffNotificationEnabled": false,
        "ClassPreparingDeltaTime": 30,
        "ClassOnPreparingText": "请准备好上这门特别的课！"
    }
}
```
客户端会根据优先级（如：科目 > 时间点 > 课表 > 时间表 > 全局默认）来决定最终应用的附加设置。

## 5. 注意事项

*   **URL 模板**: 服务器端的 `ManagementServerConnection` 和 `ServerlessConnection` 中的 `DecorateUrl` 方法会替换 URL 模板中的 `{cuid}` (客户端唯一ID), `{id}` (客户端自定义ID), 和 `{host}` (服务器主机名)。
*   **版本控制**: Manifest 中的 `Version` 字段以及每个资源条目的 `Version` 用于客户端判断是否需要下载新配置。
*   **错误处理**:
    *   HTTP API: 标准 HTTP 状态码。
    *   gRPC API: `Retcode` 枚举。
*   **数据存储**: 服务器端所有可分发的数据文件（课表、时间表等）都存储在 `Datas/` 目录下的对应子目录中，文件名即为资源名 (如 `default.json`，`custom_plan.json`)。
