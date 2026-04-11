"""非浸入式 OOBE 占位接管应用层。

用于在未初始化时接管所有端口，将外部不合规的路由 100% 拦截并返回 503，
同时暴露一个无碍主进程和中间件体系的 OOBE 配置路由。
"""

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api.admin.admin_oobe import router as oobe_router
from app.core.security.codes import ERR_SYSTEM_OOBE


def _create_stub() -> FastAPI:
    """生成一只只返回 503 的占位应用。"""
    app = FastAPI(title="CIMS (OOBE Stub)", docs_url=None, redoc_url=None)

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def _catch_all(request: Request, path: str):
        return JSONResponse(
            status_code=503,
            content={
                "code": ERR_SYSTEM_OOBE,
                "msg": "系统尚未初始化，请完成 OOBE 配置",
            },
        )

    return app


def _create_admin() -> FastAPI:
    """生成管理端口专用的 OOBE 应用。"""
    app = FastAPI(title="CIMS Admin (OOBE Mode)", docs_url=None, redoc_url=None)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.include_router(oobe_router)

    @app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
    async def _catch_all(request: Request, path: str):
        return JSONResponse(
            status_code=503,
            content={"code": ERR_SYSTEM_OOBE, "msg": "系统未初始化，仅开放 OOBE 接口"},
        )

    return app


oobe_stub_app = _create_stub()
oobe_admin_app = _create_admin()
