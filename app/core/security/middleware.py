"""FastAPI 提供防 CC 高频拦截与异常 IP 限流中间件支撑。"""

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from .tracker import check_ip_blocked, record_ip_failure, monitor_global_frequency
from .state import get_cc_state
from .codes import ERR_CC_ACTIVE, ERR_IP_BLOCKED


class CCProtectMiddleware(BaseHTTPMiddleware):
    """用于应用侧的整体防护：阻断非法 IP 以及遭遇全域攻击时降级服务。"""

    async def dispatch(self, request, call_next):
        """挂载过滤清洗规则与异常频率溯源记录机制。"""
        ip = request.client.host if request.client else "unknown"
        if check_ip_blocked(ip):
            return JSONResponse(
                status_code=429, content={"code": ERR_IP_BLOCKED, "msg": "异常封禁"}
            )

        monitor_global_frequency()

        # 判断全局遭受狂暴并发时，拦截敏感交互点
        path = request.url.path.lower()
        if get_cc_state() and any(k in path for k in ["login", "register"]):
            if "authorization" not in request.headers:
                return JSONResponse(
                    status_code=503, content={"code": ERR_CC_ACTIVE, "msg": "通道受阻"}
                )

        resp = await call_next(request)
        if resp.status_code >= 400:
            record_ip_failure(ip)

        return resp
