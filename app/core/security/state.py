"""CC 攻击防护与全局请求状态管理。"""

from collections import deque

# 全局布尔标志：当前是否处于 CC 攻击防护状态
_is_cc_attack_active: bool = False
# 用于高频检测的全局请求时间序列
_global_requests = deque()
# 记录单个 IP 连续失败响应时间的字典: { "ip": [ timestamp1, ... ] }
_ip_failures = {}


def get_cc_state() -> bool:
    """获取当前是否处于 CC 高频攻击保护。"""
    return _is_cc_attack_active


def set_cc_state(state: bool):
    """设置当前 CC 保护状态。"""
    global _is_cc_attack_active
    _is_cc_attack_active = state


def get_ip_failures_dict() -> dict:
    """获取所有记录 IP 失败时间的引用。"""
    return _ip_failures


def get_global_requests() -> deque:
    """获取记录全局请求时间戳的引用。"""
    return _global_requests
