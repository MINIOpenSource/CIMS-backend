"""gRPC 租户识别与会话鉴权拦截器。

从 metadata 中解析租户和 session 令牌，并设置 Schema 上下文。
"""

import grpc
from app.core.tenant.context import tenant_ctx, schema_ctx
from app.core.tenant.resolver import resolve_account
from app.core.tenant.host_parser import extract_slug_from_host
from app.models.database import AsyncSessionLocal

# 不需要 session 鉴权的方法名后缀白名单
_AUTH_EXEMPT = {"Register", "BeginHandshake", "CompleteHandshake"}


class TenantInterceptor(grpc.aio.ServerInterceptor):
    """Server-side gRPC 租户解析与令牌校验。"""

    def __init__(self, session_manager=None):
        """初始化拦截器，注入会话管理器。"""
        self._sm = session_manager

    async def intercept_service(self, continuation, handler_call_details):
        """提取 tenant-id 并对非白名单方法校验 session。"""
        metadata = dict(handler_call_details.invocation_metadata)
        authority = metadata.get(":authority", "")
        slug = extract_slug_from_host(authority) or metadata.get("tenant-id")

        if slug:
            async with AsyncSessionLocal() as db:
                account = await resolve_account(slug, db)
            if account:
                tenant_ctx.set(account.id)
                schema_ctx.set(f"tenant_{slug}")

        # 检查是否为豁免方法
        method = handler_call_details.method or ""
        short_name = method.rsplit("/", 1)[-1]
        if short_name not in _AUTH_EXEMPT and self._sm:
            sid = metadata.get("session", "")
            if not sid or not await self._sm.validate_session(sid):
                raise grpc.aio.AbortError(
                    grpc.StatusCode.UNAUTHENTICATED, "session 无效或缺失"
                )

        return await continuation(handler_call_details)
