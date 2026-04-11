"""全域统一异常拦截与自定义 RPC 格式架构输出定义。"""

import logging
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException
from .codes import (
    ERR_SERVER_INF,
    ERR_VALIDATION,
    ERR_GENERIC,
    ERR_NOT_FOUND,
    ERR_PERM_DENIED,
    ERR_AUTH_INVALID,
)

logger = logging.getLogger(__name__)


async def _custom_http_exc(req: Request, exc: HTTPException):
    """拦截常规 HTTP 终止反馈，支持动态下发更细的错误码。"""
    c = ERR_GENERIC
    if exc.status_code == 404:
        c = ERR_NOT_FOUND
    elif exc.status_code == 401:
        c = ERR_AUTH_INVALID
    elif exc.status_code == 403:
        c = ERR_PERM_DENIED

    msg = getattr(exc, "detail", "系统未指明失效缘由")

    # 允许在项目中利用 detail 传递自定义状态，例如：
    # raise HTTPException(401, detail={"code": 1004011, "msg": "过期的凭据"})
    if isinstance(msg, dict) and "code" in msg:
        c = msg.get("code")
        msg = msg.get("msg", "请求异常")

    return JSONResponse(status_code=exc.status_code, content={"code": c, "msg": msg})


async def _custom_val_exc(req: Request, exc: RequestValidationError):
    """拒止 Pydantic 边界越位爆破探针，减缩暴露面。"""
    return JSONResponse(
        status_code=422, content={"code": ERR_VALIDATION, "msg": "参数失范"}
    )


async def _custom_global_exc(req: Request, exc: Exception):
    """兜底层级外推防护罩，隐秘封装后端全链路抛错溯源追踪路径。"""
    logger.exception("出现未知逻辑穿透与系统层瘫痪: %s", exc)
    return JSONResponse(
        status_code=500, content={"code": ERR_SERVER_INF, "msg": "逻辑熔断"}
    )


def apply_app_safeguards(app: FastAPI):
    """统一向装载中台灌注自定义式 RPC 级故障屏障与拦截机制。"""
    app.add_exception_handler(HTTPException, _custom_http_exc)
    app.add_exception_handler(RequestValidationError, _custom_val_exc)
    app.add_exception_handler(Exception, _custom_global_exc)
