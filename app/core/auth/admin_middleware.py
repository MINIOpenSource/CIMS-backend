"""管理端令牌认证中间件。

通过 Redis 会话令牌验证用户身份，
将已认证的 user_id 注入 request.state。
兼容旧版 command 域令牌以保持 /command/* 路由可用。
"""

import logging

from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import JSONResponse

from app.core.config import REDIS_DB_AUTH
from app.core.redis.accessor import get_redis
from app.core.tenant.context import get_tenant_id

logger = logging.getLogger(__name__)

# 免认证路径白名单
_EXEMPT = {"/", "/user/auth", "/user/apply"}
_DENY = JSONResponse(status_code=403, content={"detail": "权限不足"})
_NO_AUTH = JSONResponse(status_code=401, content={"detail": "未认证"})


class AdminAuthMiddleware(BaseHTTPMiddleware):
    """管理端会话令牌认证拦截器。"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """验证 Bearer Token 并注入用户身份。"""
        # 放行 CORS 预检请求
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path
        if path in _EXEMPT:
            return await call_next(request)
        # 提取 Bearer Token
        auth = request.headers.get("authorization", "")
        if not auth.startswith("Bearer "):
            return _NO_AUTH
        token = auth[7:]
        # 尝试新式会话令牌
        from app.core.auth.dependencies import (
            resolve_user_from_token,
        )

        user_id = await resolve_user_from_token(token)
        if user_id:
            request.state.current_user_id = user_id
            return await call_next(request)
        # 回退：旧式 command 域令牌（/account/{id}/... 路径）
        if path.startswith("/account/"):
            ok = await _check_legacy_token(token, path)
            if ok:
                return await call_next(request)
        client_ip = request.client.host if request.client else "unknown"
        logger.warning("认证失败：ip=%s path=%s", client_ip, path)
        return _DENY


async def _check_legacy_token(token: str, path: str = "") -> bool:
    """检查旧式 auth:{tenant_id}:{token} 格式的令牌。

    优先从 tenant_ctx 获取 tenant_id，
    若不存在则尝试从 URL 路径 /accounts/{account_id}/... 提取。
    """
    import re

    rd = get_redis(REDIS_DB_AUTH)
    tid = None
    try:
        tid = get_tenant_id()
    except RuntimeError:
        pass
    if not tid and path:
        m = re.match(r"/account/([^/]+)/", path)
        if m:
            tid = m.group(1)
    if not tid:
        return False
    key = f"auth:{tid}:{token}"
    data = await rd.hgetall(key)
    return bool(data and data.get("scope") == "command")
