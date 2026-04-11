"""gRPC 租户识别与会话鉴权拦截器。

从 metadata 中解析租户和 session 令牌，并设置 Schema 上下文。
"""

import grpc
import functools
import logging
from app.core.tenant.context import tenant_ctx, schema_ctx
from app.core.tenant.resolver import resolve_account
from app.core.tenant.host_parser import extract_slug_from_host
from app.models.database import AsyncSessionLocal
from app.core.security.state import get_cc_state

logger = logging.getLogger(__name__)

# 不需要 session 鉴权的方法名后缀白名单
_AUTH_EXEMPT = {"Register", "BeginHandshake", "CompleteHandshake"}


class TenantInterceptor(grpc.aio.ServerInterceptor):
    """Server-side gRPC 租户解析与令牌校验。"""

    def __init__(self, session_manager=None):
        """初始化拦截器，注入会话管理器。"""
        self._sm = session_manager

    async def intercept_service(self, continuation, handler_call_details):
        """提取 tenant-id 并对非白名单方法校验 session。"""
        method = handler_call_details.method or ""
        short_name = method.rsplit("/", 1)[-1]

        # 遭遇 CC 时阻止全新链路建立
        if get_cc_state() and short_name in _AUTH_EXEMPT:
            raise grpc.aio.AbortError(
                grpc.StatusCode.UNAVAILABLE, "网络拥堵防御已开启，拒绝新人"
            )

        metadata = dict(handler_call_details.invocation_metadata)
        authority = (
            metadata.get("x-forwarded-host")
            or metadata.get("host")
            or metadata.get(":authority", "")
        )
        # 尝试从 Host 或多个可能的 Metadata Key 中提取租户标识
        slug = (
            extract_slug_from_host(authority)
            or metadata.get("tenant-id")
            or metadata.get("tenant_id")
            or metadata.get("tenant-slug")
            or metadata.get("tenant_slug")
        )

        tenant_id = None
        if slug:
            async with AsyncSessionLocal() as db:
                account = await resolve_account(slug, db)
            if account:
                tenant_id = account.id

        # 检查是否为豁免方法

        # 提取 session ID (支持 'session' 或 'authorization' 头)
        sid = metadata.get("session") or metadata.get("authorization", "")
        if sid.startswith("Bearer "):
            sid = sid[7:]

        if short_name not in _AUTH_EXEMPT and self._sm:
            if not sid or not await self._sm.validate_session(sid):
                raise grpc.aio.AbortError(
                    grpc.StatusCode.UNAUTHENTICATED, "session 无效或缺失"
                )

            # 如果元数据没带租户，尝试从 session 中恢复
            if not tenant_id and sid:
                tenant_id = await self._sm.get_session_tenant(sid)

        handler = await continuation(handler_call_details)
        if handler is None:
            return None

        # 包装 Behavior 以确保 ContextVar 在处理方法任务中生效
        def wrapper(behavior):
            @functools.wraps(behavior)
            async def wrapped_behavior(request_or_iterator, context):
                t1, t2 = None, None
                if tenant_id:
                    t1 = tenant_ctx.set(tenant_id)
                    # 如果有 slug 则设置 schema，否则可能只能依赖 tenant_id
                    if slug:
                        t2 = schema_ctx.set(f"tenant_{slug}")
                try:
                    return await behavior(request_or_iterator, context)
                finally:
                    if t1:
                        tenant_ctx.reset(t1)
                    if t2:
                        schema_ctx.reset(t2)

            return wrapped_behavior

        # 根据处理程序类型重新构建（unary_unary, unary_stream 等）
        if handler.unary_unary:
            return grpc.unary_unary_rpc_method_handler(
                wrapper(handler.unary_unary),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        if handler.unary_stream:
            return grpc.unary_stream_rpc_method_handler(
                wrapper(handler.unary_stream),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        if handler.stream_unary:
            return grpc.stream_unary_rpc_method_handler(
                wrapper(handler.stream_unary),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        if handler.stream_stream:
            return grpc.stream_stream_rpc_method_handler(
                wrapper(handler.stream_stream),
                request_deserializer=handler.request_deserializer,
                response_serializer=handler.response_serializer,
            )
        return handler
