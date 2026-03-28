"""账户资源管理路由。

提供资源的列表、搜索、创建、上传、删除、重命名、覆盖写入和下载。
复用 command 模块的数据 CRUD 逻辑。
"""

from fastapi import APIRouter

from app.api.command.data_crud import router as crud_r
from app.api.command.data_delete import router as del_r
from app.api.command.data_token import router as token_r
from app.api.command.data_write import router as write_r
from app.api.command.data_patch import router as patch_r
from app.api.command.batch import router as batch_r

router = APIRouter()

# 资源 CRUD 操作
router.include_router(crud_r)
router.include_router(del_r)
router.include_router(token_r)
router.include_router(write_r)
router.include_router(patch_r)
router.include_router(batch_r)
