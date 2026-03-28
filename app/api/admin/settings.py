"""系统设置路由。

提供平台级系统设置的读取和修改。
仅允许白名单内的配置项写入。
"""

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth.dependencies import require_role
from app.models.session import get_db
from app.models.system_config import SystemConfig
from app.api.schemas.settings import SettingsUpdate

router = APIRouter()
_sa = require_role(100)


@router.get("")
async def get_settings(
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """获取所有系统设置。"""
    rows = (await db.execute(select(SystemConfig))).scalars().all()
    return {r.key: r.value for r in rows}


@router.post("")
async def update_settings(
    body: SettingsUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(_sa),
):
    """修改系统设置（仅白名单键）。"""
    now = datetime.now(timezone.utc)
    for key, value in body.items.items():
        stmt = select(SystemConfig).where(SystemConfig.key == key)
        cfg = (await db.execute(stmt)).scalar_one_or_none()
        if cfg:
            cfg.value = str(value)
            cfg.updated_at = now
        else:
            db.add(SystemConfig(key=key, value=str(value), updated_at=now))
    await db.commit()
    return {"message": "设置已更新"}
