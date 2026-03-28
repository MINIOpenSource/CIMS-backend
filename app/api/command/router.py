"""命令系统主路由。

聚合数据 CRUD、PATCH 更新、批量操作及客户端实时控制接口。
此路由仅在 gRPC command 上下文中使用，
不再被 account_resource / account_client 复用。
"""

from fastapi import APIRouter
from .data_crud import router as crud_r
from .data_delete import router as del_r
from .data_token import router as token_r
from .data_write import router as write_r
from .data_patch import router as patch_r
from .client_status import router as status_r
from .client_control import router as control_r
from .client_notification import router as notify_r
from .client_config import router as config_r
from .batch import router as batch_r

router = APIRouter()

# 挂载资源管理接口（按 NewAPI.md 的资源路径挂在顶层）
router.include_router(crud_r)
router.include_router(del_r)
router.include_router(token_r)
router.include_router(write_r)
router.include_router(patch_r)
router.include_router(batch_r)

# 挂载客户端监控与控制接口
router.include_router(status_r)
router.include_router(control_r)
router.include_router(notify_r)
router.include_router(config_r)
