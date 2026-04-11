"""HTTP 多租户路由中间件。

拦截请求、解析主机名，确保账户和 Schema 上下文就绪。
仅用于 Client API（通过 Host 头中的子域名 slug 解析租户）。
"""

from fastapi import Request, Response
from starlette.middleware.base import (
    BaseHTTPMiddleware,
    RequestResponseEndpoint,
)
from app.core.tenant.host_parser import extract_slug_from_host
from app.core.tenant.resolver import resolve_account
from app.core.tenant.context import tenant_ctx, schema_ctx
from app.models.engine import AsyncSessionLocal
from starlette.responses import JSONResponse
from app.core.security.codes import ERR_TENANT_NO_ACCESS, ERR_RESOURCE_LOCKED

# 无需租户上下文的路径
_NO_TENANT = {"/", "/get"}


class TenantMiddleware(BaseHTTPMiddleware):
    """路由器级别的二级域名拦截处理。"""

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """带域名解析和 Schema 路由的拦截逻辑。"""
        # 放行 CORS 预检请求，避免 OPTIONS 被拦截导致跨域失败
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path
        if path in _NO_TENANT:
            return await call_next(request)
        slug = extract_slug_from_host(request.headers.get("host", ""))
        if not slug:
            return JSONResponse(
                status_code=403,
                content={"code": ERR_TENANT_NO_ACCESS, "msg": "未识别出租户"},
            )
        async with AsyncSessionLocal() as db:
            account = await resolve_account(slug, db)
        if not account:
            return JSONResponse(
                status_code=403,
                content={"code": ERR_RESOURCE_LOCKED, "msg": "服务不可用"},
            )
        t_tok = tenant_ctx.set(account.id)
        s_tok = schema_ctx.set(f"tenant_{slug}")
        try:
            request.state.tenant_id = account.id
            request.state.tenant_slug = slug
            return await call_next(request)
        finally:
            schema_ctx.reset(s_tok)
            tenant_ctx.reset(t_tok)
