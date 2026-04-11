"""全局安全与错误响应状态码定义。"""

# CC 与频率限制类
ERR_CC_ACTIVE = 100503  # 服务因 CC 保护降级，限制相关接口
ERR_IP_BLOCKED = 100429  # IP 短时内产生过多失败响应，已被封禁

# HTTP 与通用业务类
ERR_SERVER_INF = 100500  # 服务器内部未知错误
ERR_SYSTEM_OOBE = 1005031  # 系统尚未完成初始装配（OOBE态）
ERR_VALIDATION = 100422  # 请求参数格式验证失败
ERR_NOT_FOUND = 100404  # 请求的资源不存在
ERR_GENERIC = 100400  # 通用业务异常

# 鉴权与会话级别细分 (100401x)
ERR_AUTH_MISSING = 1004010  # 缺少鉴权 Token
ERR_AUTH_EXPIRED = 1004011  # 鉴权 Token 已过期
ERR_AUTH_INVALID = 1004012  # 鉴权 Token 无效或被篡改
ERR_AUTH_REVOKED = 1004013  # 鉴权已被撤销

# 权限与访问控制细分 (100403x)
ERR_PERM_DENIED = 1004030  # 权限不足
ERR_TENANT_NO_ACCESS = 1004031  # 无权访问目标租户/账户
ERR_RESOURCE_LOCKED = 1004032  # 资源受限或账户已被停用
