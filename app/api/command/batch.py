"""批量资源原子操作。

支持单次请求内处理多个资源操作。
"""

import json
import logging

from datetime import datetime, timezone
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.database import get_db
from app.api.schemas.batch import BatchRequest, BatchOperationAction
from .model_map import MODEL_MAP
import app.api.command as _cmd_pkg

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/batch")
async def process_batch(req: BatchRequest, db: AsyncSession = Depends(get_db)):
    """顺序执行一组资源操作并返回结果。"""
    res = []
    try:
        for op in req.operations:
            model = MODEL_MAP.get(op.resource_type)
            if not model:
                res.append({"action": op.action, "name": op.name, "status": "skipped"})
                continue
            record = (
                await db.execute(select(model).where(model.name == op.name))
            ).scalar_one_or_none()
            if op.action == BatchOperationAction.delete and record:
                await db.delete(record)
            elif op.action in [BatchOperationAction.write, BatchOperationAction.create]:
                rc = record or model(name=op.name)
                rc.content = json.dumps(op.payload or {})
                rc.version = (getattr(rc, "version", None) or 0) + 1
                rc.updated_at = datetime.now(timezone.utc)
                db.add(rc)
            elif op.action == BatchOperationAction.update and record:
                cur = json.loads(record.content) if record.content else {}
                record.content = json.dumps(
                    _cmd_pkg.dict_deep_merge(cur, op.payload or {})
                )
                record.version = (record.version or 0) + 1
                record.updated_at = datetime.now(timezone.utc)
            res.append({"action": op.action, "name": op.name, "status": "success"})
        await db.commit()
        return {"status": "success", "results": res}
    except Exception as exc:
        await db.rollback()
        logger.exception("批量操作异常: %s", exc)
        return {"status": "error", "message": "内部错误，请联系管理员"}
