"""全局应用配置。

使用 pydantic-settings 解析环境变量与 .env 文件，
并保留 .cims/config.json 对 DATABASE_URL 的覆盖能力。

配置优先级：.cims/config.json > 环境变量 > .env 默认值。
"""

import json
import logging
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

logger = logging.getLogger(__name__)


_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


# ---- pydantic-settings 配置类 ----


class CIMSSettings(BaseSettings):
    """CIMS 全局配置，自动从环境变量与 .env 文件加载。"""

    model_config = SettingsConfigDict(
        env_file=str(_PROJECT_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # 数据库 / Redis
    database_url: str = ""
    redis_url: str = ""

    # 多租户托管
    cims_base_domain: str = "miniclassisland.com"

    # 四端口分配
    cims_client_port: int = 27041
    cims_management_port: int = 27042
    cims_admin_port: int = 27043
    cims_grpc_port: int = 27044

    # GPG 密钥文件
    cims_key_file: str = "cims_server.key"

    # 超级管理员密钥
    cims_admin_secret: str = "change-me"


_settings = CIMSSettings()


# ---- .cims/config.json 覆盖 ----
_CONFIG_DIR = _PROJECT_ROOT / ".cims"
_CONFIG_FILE = _CONFIG_DIR / "config.json"


def _load_file_config() -> dict:
    """从 .cims/config.json 加载数据库连接配置。"""
    if _CONFIG_FILE.exists():
        with open(_CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


_file_cfg = _load_file_config()

# ---- 模块级常量（保持现有接口不变）----

DATABASE_URL: str = _file_cfg.get("database_url") or _settings.database_url
REDIS_URL: str = _settings.redis_url

# Redis 逻辑 DB 分配
REDIS_DB_AUTH: int = 0
REDIS_DB_SESSION: int = 1
REDIS_DB_CACHE: int = 2

# 多租户托管配置
BASE_DOMAIN: str = _settings.cims_base_domain
DEFAULT_SCHEMA: str = "public"

# 分区服务端口分配
CLIENT_PORT: int = _settings.cims_client_port
MANAGEMENT_PORT: int = _settings.cims_management_port
ADMIN_PORT: int = _settings.cims_admin_port
GRPC_PORT: int = _settings.cims_grpc_port

# GPG 密钥文件路径
KEY_FILE: str = _settings.cims_key_file


def validate_config() -> None:
    """在服务启动前校验关键配置，缺失时快速失败。

    仅由 serve 命令调用——init / help 等 CLI 子命令不会触发此检查。
    """
    if not DATABASE_URL:
        raise RuntimeError(
            "必须通过 .cims/config.json、.env 或 DATABASE_URL 环境变量提供数据库连接"
        )
    if not REDIS_URL:
        raise RuntimeError("必须通过 .env 或 REDIS_URL 环境变量提供 Redis 连接")
