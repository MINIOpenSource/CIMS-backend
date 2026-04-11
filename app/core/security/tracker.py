"""CC 追踪与 IP 单黑名单验证核心逻辑。"""

import time
from .state import set_cc_state, get_ip_failures_dict, get_global_requests

# 限频防御配置指引
IP_FAIL_MAX = 5  # 窗口内单一 IP 允许极度失败的最大阈值
CC_GLOBAL_MAX = 2000  # 触发 CC 拦截的综合请求频率阈值
WINDOW_SEC = 60  # 计算窗口时间（秒）


def _clean_old(queue, now: float):
    """清理全局队列中超时的历史请求时间节点。"""
    while queue and queue[0] < now - WINDOW_SEC:
        queue.popleft()


def check_ip_blocked(ip: str) -> bool:
    """实时判定给定 IP 是否因为高频异常响应被列入管控封禁。"""
    now = time.time()
    fails = get_ip_failures_dict().setdefault(ip, [])
    while fails and fails[0] < now - WINDOW_SEC:
        fails.pop(0)
    return len(fails) >= IP_FAIL_MAX


def record_ip_failure(ip: str):
    """于数据库登录失效或其余非标准路径出错时登记一次。"""
    get_ip_failures_dict().setdefault(ip, []).append(time.time())


def monitor_global_frequency():
    """每次收到请求时测算整体水位线，并在暴增时激化全局保护态。"""
    now = time.time()
    reqs = get_global_requests()
    reqs.append(now)
    _clean_old(reqs, now)
    set_cc_state(len(reqs) > CC_GLOBAL_MAX)
