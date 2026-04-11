# CIMS API 文档

## 概述

CIMS 提供四个独立端口的 API 服务：

| 端口 | 名称 | 用途 |
|------|------|------|
| `27041` | Client API | ClassIsland 客户端获取配置和资源 |
| `27042` | Management API | 用户认证、账户管理、资源管理、客户端控制 |
| `27043` | Admin API | 超级管理员全局用户/账户/系统管理 |
| `27044` | gRPC | Cyrene_MSP 协议（注册、命令推送、心跳） |

---

## OOBE 引导配置 `:27043`

仅在系统尚未初始化时，通过 Admin 端口 (`27043`) 暴露。常规运行态将对其进行 HTTP 503 阻拦。

### `POST /oobe/verify`

验证后台启动时下发的终端配套码并颁发临时认证 Token。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `passcode` | Form | string | ✅ | 终端随机生出的 8 位大写字母与数字组合 |

**响应** — `{"token": "UUID 临时权限令牌"}`

### `POST /oobe/configure`

收录系统前置必备配参落盘，完成建库操作和超管分配，无碍执行后主动触发自身程序冷重启。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `token` | Form | string | ✅ | `verify` 返回的临时 Token |
| `db_url` | Form | string | ✅ | PostgreSQL 连接串 |
| `redis_url` | Form | string | ✅ | Redis 连接串 |
| `domain` | Form | string | ✅ | Root Domain |
| `username` | Form | string | ✅ | 预设超管账号 |
| `email` | Form | string | ✅ | 密保或系统通联邮箱 |
| `password` | Form | string | ✅ | 初始化登录密码 |

**响应** — `{"msg": "初始化完毕，系统重启中"}`

---

## Client API `:27041`

### `GET /`

服务状态检测。

**响应**

```json
{"message": "CIMS Client API 运行中"}
```

### `GET /api/v1/client/{client_uid}/manifest`

获取客户端配置清单。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `client_uid` | path | string | ✅ | 客户端唯一标识 |

**响应** — Manifest JSON，包含各资源类型的名称列表。

### `GET /api/v1/client/{resource_type}`

获取指定资源（302 重定向到令牌下载地址）。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `resource_type` | path | string | ✅ | 合法值: `ClassPlan`, `TimeLayout`, `Subjects`, `Policy`, `DefaultSettings`, `Components`, `Credentials` |
| `name` | query | string | ✅ | 资源文件名 |

### `GET /get`

通过令牌获取资源 JSON 内容。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `token` | query | string | ✅ | 一次性资源访问令牌 |

**响应** — 资源 JSON 内容。

### `GET /api/v1/management-config`

获取 ManagementPreset 引导配置。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `class_identity` | query | string | ❌ | 班级标识（匹配预注册客户端） |

**响应**

```json
{
  "IsManagementEnabled": true,
  "ManagementServerKind": 1,
  "ManagementServer": "https://{slug}.example.com",
  "ManagementServerGrpc": "https://{slug}.example.com",
  "ClassIdentity": "",
  "PreRegisteredLabel": "三年一班",
  "ManifestUrlTemplate": ""
}
```

---

## Management API `:27042`

> 所有端点（除 `/user/apply` 和 `/user/auth`）需要 `Authorization: Bearer {token}` 请求头。

### Token 管理

#### `POST /token/refresh`

刷新当前会话令牌。

**响应**

```json
{"token": "新的会话令牌"}
```

#### `POST /token/verify`

验证令牌有效性。

**响应**

```json
{"valid": true, "user_id": "uuid"}
```

#### `POST /token/deactivate`

注销当前令牌（登出）。

**响应**

```json
{"status": "success", "message": "已登出"}
```

### 用户

#### `POST /user/apply`

申请注册新用户。注册后进入 Pending 状态，需管理员审核。

**请求体**

```json
{
  "email": "user@example.com",
  "password": "至少12位密码",
  "username": "可选",
  "display_name": "可选"
}
```

#### `POST /user/auth`

用户登录，获取会话令牌。

**请求体**

```json
{"email": "user@example.com", "password": "密码"}
```

**响应（正常）** — `{"token": "会话令牌"}`

**响应（需 2FA）** — `{"requires_2fa": true, "temp_token": "临时令牌"}`

#### `GET /user/availability/mail`

检查邮箱是否可用（未被占用）。无需认证。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `value` | query | string | ✅ | 待检查的邮箱地址 |

**响应** — `{"available": true|false}`

#### `GET /user/availability/username`

检查用户名是否可用（未被占用、非系统保留且格式合法）。无需认证。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `value` | query | string | ✅ | 待检查的用户名（3-64位） |

**响应** — `{"available": true|false, "reason": "不可用原因(可选)"}`

#### `GET /user/info`

获取当前用户信息。

**响应** — `UserOut`

### 2FA (TOTP) `/user/2fa/totp/...`

#### `POST /user/2fa/totp/enable`

启用 TOTP。返回密钥和恢复码。

#### `POST /user/2fa/totp/confirm`

确认绑定（提交首次 TOTP 码）。

**请求体** — `{"code": "123456"}`

#### `POST /user/2fa/totp/disable`

禁用 TOTP。

**请求体** — `{"password": "当前密码"}`

#### `POST /user/2fa/totp/verify`

登录时验证 TOTP。

**请求体** — `{"temp_token": "临时令牌", "code": "123456"}`

**响应** — `{"token": "正式会话令牌"}`

#### `POST /user/2fa/totp/recover`

使用恢复码登录。

**请求体** — `{"temp_token": "临时令牌", "recovery_code": "恢复码"}`

### 用户信息 `/user/info/...`

#### `GET /user/info/`

获取用户信息（同 `GET /user/info`）。

#### `POST /user/info/email`

修改邮箱。

**请求体** — `{"email": "new@example.com"}`

#### `POST /user/info/username`

修改用户名。

**请求体** — `{"username": "new_username"}`

#### `POST /user/info/password/change`

修改密码（需旧密码）。

**请求体** — `{"old_password": "旧密码", "new_password": "至少12位新密码"}`

#### `POST /user/info/password/reset`

重置密码（自助流程）。

### 账户管理

#### `GET /account/availability/slug`

检查账户 URL 标识 (Slug) 是否可用。需登录。

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `value` | query | string | ✅ | 待检查的 Slug（3-64位） |

**响应** — `{"available": true|false, "reason": "不可用原因(可选)"}`

#### `GET /account/list`

列出当前用户有权访问的所有账户。

**响应** — `AccountOut[]`

#### `POST /account/search`

搜索账户。

| 参数 | 位置 | 类型 | 说明 |
|------|------|------|------|
| `q` | query | string | 搜索关键字 |

#### `POST /account/apply`

申请创建新账户。

**请求体** — `{"name": "学校名称", "slug": "可选"}`

#### `DELETE /account/{account_id}`

删除/停用账户。

#### `GET /account/{account_id}/info`

获取账户详情。

**响应** — `AccountOut`

#### `POST /account/{account_id}/info/slug`

修改账户 slug。

**请求体** — `{"slug": "new-slug-name"}`

### 资源管理 `/account/{account_id}/{resource_type}/...`

#### `GET /{resource_type}/list`

列出所有资源文件名。

#### `POST /{resource_type}/search`

搜索资源。

#### `POST /{resource_type}/create`

创建资源。

#### `POST /{resource_type}/upload`

上传资源。

#### `DELETE /{resource_type}/{resource_id}`

删除资源。

#### `POST /{resource_type}/{resource_id}/rename`

重命名资源。

#### `POST /{resource_type}/{resource_id}`

覆盖写入资源。

#### `GET /{resource_type}/{resource_id}`

下载资源。

> 当前实现仍使用 `?name=` 查询参数模式而非路径参数：
>
> - `GET /{resource_type}/create?name={name}` — 创建空资源
> - `GET /{resource_type}/token?name={name}` — 签发访问令牌
> - `PUT|POST /{resource_type}/write?name={name}` — 覆盖写入
> - `PATCH /{resource_type}/update?name={name}` — 增量合并更新
> - `GET|DELETE /{resource_type}/delete?name={name}` — 删除资源

### 客户端管理 `/account/{account_id}/client/...`

#### `GET /client/list`

列出已注册客户端 UID。

#### `GET /client/search`

搜索客户端。

#### `GET /client/{client_id}`

查询客户端注册详情及在线状态。

**响应**

```json
{
  "uid": "client-uid",
  "name": "client-id",
  "mac": "AA:BB:CC:DD:EE:FF",
  "status": "online",
  "registered_at": "2026-01-01T00:00:00Z"
}
```

#### `DELETE /client/{client_id}`

删除客户端。

#### `POST /client/{client_id}/rename`

重命名客户端。

#### `GET /client/{client_id}/status`

获取客户端在线状态。

#### `POST /client/{client_id}/disconnect`

断开客户端连接。

#### `POST /client/{client_id}/disable`

禁用客户端。

#### `POST /client/{client_id}/enable`

启用客户端。

#### `POST /client/{client_id}/config`

修改客户端使用的档案组。

#### `POST /client/{client_id}/command/restart`

重启客户端应用。

#### `POST /client/{client_id}/command/update-data`

强制客户端同步最新数据。

#### `POST /client/{client_id}/command/send-notification`

发送通知。

**请求体**

```json
{
  "title": "标题",
  "content": "内容",
  "icon": "info",
  "tts": false,
  "urgent": false
}
```

#### `GET /client/{client_id}/command/get-config`

请求客户端上报运行时配置。

| 参数 | 位置 | 类型 | 说明 |
|------|------|------|------|
| `config_type` | query | int | 配置类型枚举 |

### 配对码管理 `/account/{account_id}/pairing/...`

#### `GET /pairing/list`

列出配对码。

#### `GET /pairing/search`

搜索配对码。

#### `POST /pairing/{pairing_id}/reject`

拒绝配对码。

#### `POST /pairing/{pairing_id}/approve`

批准配对码。

#### `POST /pairing/enable`

启用配对码功能。

#### `POST /pairing/disable`

禁用配对码功能。

### 预注册客户端 `/account/{account_id}/pre-registration/...`

#### `GET /pre-registration/list`

列出预注册客户端。

#### `GET /pre-registration/search`

搜索预注册客户端。

#### `GET /pre-registration/{pre_reg_id}`

获取预注册客户端信息。

#### `DELETE /pre-registration/{pre_reg_id}`

删除预注册客户端。

#### `POST /pre-registration/{pre_reg_id}/rename`

重命名预注册客户端。

#### `POST /pre-registration/{pre_reg_id}/enable`

启用预注册客户端。

#### `POST /pre-registration/{pre_reg_id}/disable`

禁用预注册客户端。

#### `GET /pre-registration/{pre_reg_id}/ManagementPreset.json`

下载引导配置。

#### `POST /pre-registration/{pre_reg_id}/config`

修改预注册客户端使用的档案组。

#### `POST /pre-registration/create`

创建预注册客户端。

**请求体** — `{"label": "三年一班", "class_identity": "3-1"}`

### 访问控制 `/account/{account_id}/access/...`

#### `GET /access/list`

列出具权用户。

#### `GET /access/search`

搜索具权用户。

#### `GET /access/{user_id}`

获取具权用户信息。

#### `DELETE /access/{user_id}`

移除成员（204 No Content）。

#### `POST /access/{user_id}/rename`

重命名具权用户。

#### `POST /access/{user_id}`

修改具权用户的权限。

**请求体** — `{"role_in_account": "admin"}`

### 邀请 `/account/{account_id}/invitation/...`

#### `GET /invitation/list`

列出邀请列表。

#### `POST /invitation/create`

创建邀请。

**请求体**

```json
{
  "role_in_account": "member",
  "max_uses": 1,
  "expires_at": "2026-12-31T23:59:59Z"
}
```

#### `GET /invitation/search`

搜索邀请。

#### `DELETE /invitation/{invitation_id}`

删除邀请。

#### `POST /invitation/{invitation_id}/rename`

重命名邀请。

#### `GET /invitation/{invitation_id}`

获取邀请信息。

### 批量操作

#### `POST /account/bulk`

执行批量资源操作。

**请求体**

```json
{
  "operations": [
    {
      "action": "write",
      "resource_type": "ClassPlan",
      "name": "文件名",
      "payload": {}
    }
  ]
}
```

| action | 说明 |
|--------|------|
| `create` | 创建资源 |
| `write` | 覆盖写入 |
| `update` | 增量合并 |
| `delete` | 删除资源 |

---

## Admin API `:27043`

> 所有端点需要超级管理员认证（`Authorization: Bearer {admin_secret}`）。

### 用户管理

#### `GET /user/list`

分页查询所有用户。

| 参数 | 位置 | 类型 | 说明 |
|------|------|------|------|
| `offset` | query | int | 偏移量（默认 0） |
| `limit` | query | int | 条数（默认 20） |

**响应** — `UserOut[]`

#### `GET /user/search`

搜索用户。

| 参数 | 位置 | 类型 | 说明 |
|------|------|------|------|
| `q` | query | string | 搜索关键字 |

#### `POST /user/create`

直接创建用户（跳过审核）。

**请求体**

```json
{
  "email": "user@example.com",
  "password": "至少12位密码",
  "username": "可选",
  "display_name": "可选"
}
```

#### `GET /user/{user_id}`

获取用户信息。

**响应** — `UserOut`

#### `POST /user/{user_id}`

修改用户信息。

**请求体**

```json
{
  "display_name": "新名称",
  "role_code": "normal",
  "is_active": true,
  "can_create_account": true
}
```

#### `DELETE /user/{user_id}`

删除用户。

#### `POST /user/{user_id}/rename`

重命名用户。

**请求体** — `{"name": "新用户名"}`

#### `POST /user/{user_id}/password/reset`

重置用户密码（无需旧密码）。

**请求体** — `{"new_password": "至少12位新密码"}`

#### `POST /user/{user_id}/password/change`

修改用户密码（需验证旧密码）。

**请求体** — `{"old_password": "旧密码", "new_password": "新密码"}`

### 用户 2FA 管理

#### `POST /user/{user_id}/2fa/enable`

为用户启用 TOTP。

#### `POST /user/{user_id}/2fa/disable`

禁用用户 TOTP。

#### `POST /user/{user_id}/2fa/verify`

验证用户 TOTP。

#### `POST /user/{user_id}/2fa/reset`

重置用户 TOTP 密钥。

### 用户审核

#### `GET /user/pending/list`

列出待审核用户。

| 参数 | 位置 | 类型 | 说明 |
|------|------|------|------|
| `offset` | query | int | 偏移量（默认 0） |
| `limit` | query | int | 条数（默认 50） |

#### `POST /user/pending/approve/{user_id}`

批准用户注册。

#### `POST /user/pending/reject/{user_id}`

拒绝用户注册。

### 账户管理

#### `GET /account`

列出所有账户（跨租户）。复用 Management API 的 `/account` 接口，但具备所有权限。允许 `?role={user_id}` 以某个用户身份操作。

**响应** — `AccountOut[]`

### 系统设置

#### `GET /settings`

获取所有系统设置。

**响应** — 键值对 JSON。

#### `POST /settings`

修改系统设置。

> 仅允许以下 key：`registration_open`, `require_approval`, `max_accounts_per_user`, `default_role`, `motd`。

**请求体** — 键值对 JSON。

### 批量操作

#### `POST /bulk`

执行批量资源操作（同 Management API `/account/bulk`）。

---

## gRPC `:27044`

### `ClientRegister`

客户端注册。

**请求** — `ClientRegisterCsReq`

| 字段 | 类型 | 说明 |
|------|------|------|
| `uid` | string | 客户端唯一标识 |
| `client_id` | string | 客户端 ID |
| `mac` | string | MAC 地址 |
| `ip` | string | IP 地址 |
| `pairing_code` | string | 配对码 |

**响应** — `ClientRegisterScRsp`

| 字段 | 类型 | 说明 |
|------|------|------|
| `RetCode` | enum | 返回码（Success/Fail） |
| `ServerPublicKey` | bytes | 服务器公钥 |

### `ClientCommand` (双向流)

命令通道。

**客户端发送** — `ClientCommandDeliverCsReq`（命令响应 / Ping）

**服务端推送** — `ClientCommandDeliverScRsp`

| 字段 | 类型 | 说明 |
|------|------|------|
| `RetCode` | enum | 返回码 |
| `Type` | enum | 命令类型 (`RestartApp`, `DataUpdated`, `SendNotification`, `GetClientConfig`) |
| `Payload` | bytes | Protobuf 序列化的命令负载 |

### `HeartBeat`

心跳保活。客户端定期发送心跳，服务端回复确认。

---

## 通用数据模型

### UserOut

```json
{
  "id": "uuid",
  "username": "user_a1b2c3d4",
  "email": "user@example.com",
  "display_name": "显示名称",
  "role_code": "normal",
  "is_active": true,
  "can_create_account": false,
  "created_at": "2026-01-01T00:00:00Z"
}
```

### AccountOut

```json
{
  "id": "uuid",
  "name": "账户名称",
  "slug": "org-a1b2c3d4",
  "api_key": "API密钥",
  "is_active": true,
  "created_at": "2026-01-01T00:00:00Z"
}
```

### StatusResponse

```json
{
  "status": "success|error",
  "message": "操作结果描述"
}
```
