"""客户端真实 IP 提取工具。

统一处理 Nginx 反向代理场景下的 IP 解析，
同时支持 FastAPI（HTTP）和 gRPC 两种传输方式。

Nginx 通过以下方式传递客户端真实 IP：
  - HTTP：X-Forwarded-For / X-Real-IP 请求头
  - gRPC：x-forwarded-for / x-real-ip 元数据
"""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from starlette.requests import Request
    import grpc


def _parse_forwarded_for(value: str) -> str:
    """从 X-Forwarded-For 头中提取第一个（最原始的）客户端 IP。

    X-Forwarded-For 格式: client, proxy1, proxy2
    """
    if not value:
        return ""
    return value.split(",")[0].strip()


def get_client_ip_from_request(request: "Request") -> str:
    """从 FastAPI/Starlette Request 中提取客户端真实 IP。

    优先读取反向代理设置的头部，回退到直连 IP。
    """
    # 优先使用 X-Forwarded-For（标准多级代理头）
    forwarded = request.headers.get("x-forwarded-for", "")
    ip = _parse_forwarded_for(forwarded)
    if ip:
        return ip

    # 其次使用 X-Real-IP（Nginx 常用单值头）
    real_ip = request.headers.get("x-real-ip", "")
    if real_ip:
        return real_ip.strip()

    # 回退到直连地址
    return request.client.host if request.client else ""


def get_client_ip_from_grpc(context: "grpc.aio.ServicerContext") -> str:
    """从 gRPC 上下文中提取客户端真实 IP。

    Nginx 在 gRPC 反代时会将 x-forwarded-for / x-real-ip
    作为 metadata 传递给后端。
    """
    metadata = dict(context.invocation_metadata())

    # 优先使用 x-forwarded-for
    forwarded = metadata.get("x-forwarded-for", "")
    ip = _parse_forwarded_for(forwarded)
    if ip:
        return ip

    # 其次使用 x-real-ip
    real_ip = metadata.get("x-real-ip", "")
    if real_ip:
        return real_ip.strip()

    # 回退到 gRPC peer 地址
    peer = context.peer() or ""
    if peer and ":" in peer:
        parts = peer.split(":")
        if len(parts) >= 2:
            return parts[1]
    return ""
