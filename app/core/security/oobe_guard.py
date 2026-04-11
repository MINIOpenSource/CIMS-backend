"""OOBE 初始化安全守卫器。

提供 OOBE 生命周期阶段配对码与临时放行 Token 的内存态维护功能。
"""

import logging
import random
import string
import uuid

logger = logging.getLogger(__name__)

# 内存持有一致性的配对码与提权 Token
OOBE_PASSCODE: str = ""
OOBE_TOKEN: str = ""


def generate_oobe_codes() -> None:
    """生成并在终端安全日志中打印 OOBE 配对码，并生成配置阶段 Token。"""
    global OOBE_PASSCODE, OOBE_TOKEN
    pool = string.ascii_uppercase + string.digits
    OOBE_PASSCODE = "".join(random.choices(pool, k=8))
    OOBE_TOKEN = str(uuid.uuid4())
    logger.critical("========== [注意] 首次启动 ==========")
    logger.critical("系统尚未初始化，进入 OOBE 初始化接管态。")
    logger.critical("OOBE 通行配对码：%s", OOBE_PASSCODE)
    logger.critical("=====================================")


def verify_oobe_passcode(code: str) -> bool:
    """校验端上的 8 位字母数字组合是否是本次分配。"""
    code = code.strip().upper()
    return bool(OOBE_PASSCODE) and code == OOBE_PASSCODE


def verify_oobe_token(token: str) -> bool:
    """检查向 /configure 执行变更配置权所持有的生命周期 UUID。"""
    token = token.strip()
    return bool(OOBE_TOKEN) and token == OOBE_TOKEN
