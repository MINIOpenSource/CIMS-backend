"""账户上下文中间件。

从 URL 路径 /accounts/{account_id}/... 提取账户标识，
查库验证后设置 tenant_ctx / schema_ctx。

可通过 require_membership 参数决定是否校验 AccountMember 成员资格：
- MgrAPI：require_membership=True（普通用户仅可操作已加入的账户）
- AdminAPI：require_membership=False（超管可进入任意账户上下文）
"""

import logging
import re

from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from starlette.responses import JSONResponse

from app.core.tenant.context import tenant_ctx, schema_ctx
from app.models.engine import AsyncSessionLocal
from app.core.security.codes import (
    ERR_RESOURCE_LOCKED,
    ERR_AUTH_MISSING,
    ERR_TENANT_NO_ACCESS,
)

logger = logging.getLogger(__name__)

# 匹配 /accounts/{account_id}/... 的正则
_ACCOUNT_PATH_RE = re.compile(r"^/accounts/([^/]+)(?:/|$)")


class AccountContextMiddleware(BaseHTTPMiddleware):
    """从 URL 路径提取 account_id 并设置租户上下文。"""

    def __init__(self, app, require_membership: bool = True):
        """初始化中间件。

        Args:
            app: ASGI 应用实例。
            require_membership: 是否校验用户的 AccountMember 成员资格。
        """
        super().__init__(app)
        self._require_membership = require_membership

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """匹配路径、校验账户并注入租户上下文。"""
        # 放行 CORS 预检请求
        if request.method == "OPTIONS":
            return await call_next(request)

        path = request.url.path
        match = _ACCOUNT_PATH_RE.match(path)

        # 非 /accounts/{id}/... 路径直接放行
        if not match:
            return await call_next(request)

        account_id = match.group(1)

        # 查库验证账户存在且激活
        from app.models.account import Account

        async with AsyncSessionLocal() as db:
            from sqlalchemy import select

            result = await db.execute(select(Account).where(Account.id == account_id))
            account = result.scalar_one_or_none()

        if not account or not account.is_active:
            return JSONResponse(
                status_code=403,
                content={"code": ERR_RESOURCE_LOCKED, "msg": "账户异常"},
            )

        # 成员资格校验（跳过 /command 子路径，其使用独立的传统令牌认证）
        remaining_path = path[match.end() - 1 :]  # 从 account_id 后的 / 开始
        needs_membership = self._require_membership and "/command" not in remaining_path
        if needs_membership:
            user_id = getattr(request.state, "current_user_id", None)
            if not user_id:
                return JSONResponse(
                    status_code=401, content={"code": ERR_AUTH_MISSING, "msg": "未验证"}
                )
            from app.models.account_member import AccountMember

            async with AsyncSessionLocal() as db:
                from sqlalchemy import select

                result = await db.execute(
                    select(AccountMember).where(
                        AccountMember.user_id == user_id,
                        AccountMember.account_id == account_id,
                    )
                )
                member = result.scalar_one_or_none()
            if not member:
                return JSONResponse(
                    status_code=403,
                    content={"code": ERR_TENANT_NO_ACCESS, "msg": "越权访问"},
                )

        # 设置租户上下文
        t_tok = tenant_ctx.set(account.id)
        s_tok = schema_ctx.set(f"tenant_{account.slug}")
        try:
            request.state.tenant_id = account.id
            request.state.account_slug = account.slug
            return await call_next(request)
        finally:
            schema_ctx.reset(s_tok)
            tenant_ctx.reset(t_tok)
