"""终端在线心跳状态检测。

利用 Redis 实现分布式的在线状态维持、IP 抓取以及租户维度的批量查询。
"""

from app.core.config import REDIS_DB_SESSION
from app.core.redis.accessor import get_redis
from .peer_parser import parse_grpc_peer_ip

ONLINE_TTL = 60


async def set_online(tid: str, cuid: str, ip_raw: str = ""):
    """标记客户端在线并记录 IP。"""
    rd = get_redis(REDIS_DB_SESSION)
    key = f"online:{tid}:{cuid}"
    await rd.hset(key, mapping={"status": "online", "ip": ip_raw})
    await rd.expire(key, ONLINE_TTL)


async def set_offline(tid: str, cuid: str):
    """显式移除客户端在线记录。"""
    await get_redis(REDIS_DB_SESSION).delete(f"online:{tid}:{cuid}")


async def get_tenant_online_ips(tid: str) -> set[str]:
    """获取指定租户下所有在线客户端的清洗后 IP 集合。"""
    rd, prefix = get_redis(REDIS_DB_SESSION), f"online:{tid}:"
    ips = set()
    async for key in rd.scan_iter(match=f"{prefix}*"):  # pragma: no cover
        data = await rd.hgetall(key)
        raw_ip = data.get("ip", "")
        # 兼容旧格式（ipv4:x.x.x.x:port）和新格式（直接 IP）
        ip = (
            parse_grpc_peer_ip(raw_ip)
            if raw_ip.startswith(("ipv4:", "ipv6:"))
            else raw_ip
        )
        if ip:
            ips.add(ip)
    return ips


async def get_full_client_status(tid: str) -> list:
    """获取租户下所有设备状态（用于控制台展示）。"""
    rd, prefix = get_redis(REDIS_DB_SESSION), f"online:{tid}:"
    res = []
    async for key in rd.scan_iter(match=f"{prefix}*"):
        data = await rd.hgetall(key)
        res.append(
            {"uid": key[len(prefix) :], "status": "online", "ip": data.get("ip", "")}
        )
    return res
