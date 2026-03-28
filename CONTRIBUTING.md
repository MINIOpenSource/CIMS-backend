# 贡献指南

欢迎为 CIMS-backend 贡献代码！无论是修复 Bug、完善文档还是新增功能，你的贡献都非常有价值。

---

## 贡献流程

### 1. Fork & 创建分支

```bash
# Fork 后克隆你的仓库
git clone https://github.com/<你的用户名>/CIMS-backend.git
cd CIMS-backend

# 从 main 创建功能分支
git checkout -b feature/your-feature-name
```

### 2. 搭建开发环境

按照 [DEVELOPMENT.md](DEVELOPMENT.md) 完成环境搭建（需要 PostgreSQL 和 Redis）。

### 3. 进行修改

- 编写代码，确保遵循下文的 [代码规范](#代码规范)
- 如果修改了 `.proto` 文件，需要 [重新生成 Protobuf 代码](#protobuf-代码生成)
- 如果新增了数据库模型，**必须**遵循 [多租户约定](#多租户开发约定)
- 如有必要，更新对应的文档（README / APIDocument 等）

### 4. 验证改动

```bash
# 格式化
uv run black .

# Lint 检查（自动修复可加 --fix）
uv run ruff check .

# 运行全部测试
uv run pytest

# 查看覆盖率
uv run pytest --cov=app --cov-report=term-missing
```

### 5. 提交 Pull Request

确保 CI 全绿后，提交 PR 至 `main` 分支并等待维护者审查。

---

## 多租户开发约定

CIMS 采用行级多租户隔离，开发时需严格遵循以下规则：

| 规则 | 说明 |
|------|------|
| **模型必须包含 `tenant_id`** | 所有新增的 SQLAlchemy 模型必须包含 `tenant_id` 字段，并将其纳入复合主键或唯一约束 |
| **查询必须过滤 `tenant_id`** | 所有数据库查询语句必须使用 `.where(Model.tenant_id == tenant_id)` 进行行级过滤 |
| **获取租户 ID** | 在 API 端点中通过 `get_tenant_id()` 获取当前请求所属的租户 ID |
| **Redis Key 前缀** | 会话管理和资源令牌的 Redis Key 必须以 `tenant_id` 为前缀，避免跨租户数据泄露 |
| **gRPC Interceptor** | gRPC 服务通过 `TenantInterceptor` 自动从 `:authority` 或 `tenant-id` metadata 中解析租户 |

### 示例：新增一个租户隔离模型

```python
# app/models/your_model.py
from sqlalchemy import Column, String, ForeignKey
from app.models.base import Base

class YourModel(Base):
    __tablename__ = "your_table"

    id = Column(String, primary_key=True)
    tenant_id = Column(String, primary_key=True)  # ← 必须
    name = Column(String, nullable=False)
```

---

## 代码规范

### 工具链

| 工具 | 用途 | 命令 |
|------|------|------|
| [black](https://black.readthedocs.io/) | 代码格式化 | `uv run black .` |
| [ruff](https://docs.astral.sh/ruff/) | Lint 检查 | `uv run ruff check .` |
| [pyright](https://github.com/microsoft/pyright) | 类型检查 | `uv run pyright` |
| [pytest](https://docs.pytest.org/) | 测试 | `uv run pytest` |

### 编码约定

- **文件长度**：单文件建议不超过 35 行（黑线 50 行），确保模块职责单一
- **注释语言**：所有代码注释和 docstring 使用**中文**
- **文件编码**：UTF-8，Unix 换行符（LF）
- **Import 顺序**：标准库 → 第三方库 → 项目内部模块（ruff 会自动排序）
- **异步优先**：数据库和 Redis 操作统一使用 `async/await`

### 提交信息约定

使用 [Conventional Commits](https://www.conventionalcommits.org/) 格式：

```
<type>(<scope>): <description>

[optional body]
```

常用 type：

| Type | 说明 |
|------|------|
| `feat` | 新功能 |
| `fix` | Bug 修复 |
| `refactor` | 重构（不改变外部行为） |
| `docs` | 文档变更 |
| `test` | 测试相关 |
| `ci` | CI/CD 变更 |
| `chore` | 杂项（依赖更新等） |

---

## Protobuf 代码生成

修改 `api/Protobuf/` 下的 `.proto` 文件后，运行以下命令重新生成 Python 代码：

```bash
uv run python -m grpc_tools.protoc \
  -Iapi/ \
  --python_out=app/grpc \
  --grpc_python_out=app/grpc \
  --pyi_out=app/grpc \
  api/Protobuf/Service/*.proto \
  api/Protobuf/Client/*.proto \
  api/Protobuf/Server/*.proto \
  api/Protobuf/Enum/*.proto \
  api/Protobuf/Command/*.proto \
  api/Protobuf/AuditEvent/*.proto
```

生成的文件位于 `app/grpc/api/Protobuf/`，包含：

- `*_pb2.py` — Protobuf 消息类
- `*_pb2_grpc.py` — gRPC 服务桩
- `*_pb2.pyi` — 类型存根（供 IDE 提示）

> ⚠️ 生成的文件不应手动编辑，它们会被代码生成覆盖。

---

## 测试

> **前提**：需要运行中的 PostgreSQL 和 Redis 实例（可用 Docker 快速启动，见 [DEVELOPMENT.md](DEVELOPMENT.md#使用-docker推荐)）。

```bash
# 运行全部测试
uv run pytest

# 运行并查看覆盖率（含未覆盖行号）
uv run pytest --cov=app --cov-report=term-missing

# 仅运行特定测试文件
uv run pytest tests/test_api.py

# 仅运行匹配名称的测试
uv run pytest -k "test_admin_create"
```

### 测试文件说明

| 文件 | 覆盖范围 |
|------|----------|
| `test_api.py` | Client API、Command API、资源管理 |
| `test_admin_tenant.py` | Admin API、租户 CRUD、Auth 中间件、Redis、资源令牌 |
| `test_grpc.py` | gRPC 五项服务、SessionManager、在线状态 |
| `test_coverage.py` | 边界情况补充、异常路径覆盖 |

---

## 提交 Issue

如果你发现了 Bug 或有功能建议，请在 GitHub 上提交 Issue，并尽量包含以下信息：

- 清晰的标题和详细描述
- 复现步骤（Bug）或使用场景（功能建议）
- 相关的日志输出或错误截图
- 运行环境信息（OS、Python 版本、依赖版本）

---

## Pull Request 清单

提交 PR 前，请确认以下事项：

- [ ] 代码通过 `uv run black --check .`
- [ ] 代码通过 `uv run ruff check .`
- [ ] 所有测试通过 `uv run pytest`
- [ ] 新增功能已编写对应测试
- [ ] 相关文档已更新
- [ ] 提交信息遵循 Conventional Commits 格式
