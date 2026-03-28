# 开发环境设置

本文档详细说明如何搭建 CIMS-backend 的完整开发环境。

---

## 先决条件

| 依赖 | 版本要求 | 说明 |
|------|----------|------|
| [Python](https://www.python.org/) | 3.10+ | 运行时 |
| [uv](https://docs.astral.sh/uv/) | 最新 | Python 包管理器（替代 pip + venv） |
| [PostgreSQL](https://www.postgresql.org/) | 18+ | 主数据库 |
| [Redis](https://redis.io/) | 7+ | 缓存 / 会话存储 |
| [Docker](https://www.docker.com/) | 可选 | 推荐用于快速启动 PG 和 Redis |

---

## 基础设施搭建

### 使用 Docker（推荐）

```bash
# PostgreSQL
docker run -d --name cims-postgres \
  --shm-size=256m \
  -e POSTGRES_USER=postgresql \
  -e POSTGRES_PASSWORD=password \
  -p 127.0.0.1:5432:5432 \
  postgres:18-alpine

# Redis
docker run -d --name cims-redis \
  -p 127.0.0.1:6379:6379 \
  redis:7-alpine redis-server --requirepass password

# 创建数据库
docker exec -it cims-postgres psql -U postgresql -c "CREATE DATABASE cims;"
```

### 手动安装

如果不使用 Docker，请手动安装 PostgreSQL 和 Redis 并确保：

- PostgreSQL 监听 `localhost:5432`，用户 `postgresql`，密码 `password`，数据库 `cims`
- Redis 监听 `localhost:6379`，密码 `password`

> 以上默认值与 `.env.example` 一致，可按需修改。

---

## 环境变量

复制模板文件并按需修改：

```bash
cp .env.example .env
```

完整变量列表：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `DATABASE_URL` | `postgresql+psycopg://postgresql:password@localhost:5432/cims` | PostgreSQL 连接串（异步驱动 psycopg） |
| `REDIS_URL` | `redis://:password@localhost:6379/0` | Redis 连接串 |
| `CIMS_BASE_DOMAIN` | `localhost` | 多租户基础域名（子域名将会是 `<slug>.<domain>`） |
| `CIMS_ADMIN_SECRET` | `change-me` | 超级管理员密钥（用于 Admin API 登录） |
| `CIMS_CLIENT_PORT` | `27041` | Client API 监听端口 |
| `CIMS_MANAGEMENT_PORT` | `27042` | Management API 监听端口 |
| `CIMS_ADMIN_PORT` | `27043` | Admin API 监听端口 |
| `CIMS_GRPC_PORT` | `27044` | gRPC 服务监听端口 |
| `CIMS_KEY_FILE` | `cims_server.key` | PGP 服务器密钥文件路径（用于 gRPC Handshake） |

---

## 安装与启动

### 1. 克隆仓库

```bash
git clone https://github.com/MINIOpenSource/CIMS-backend.git
cd CIMS-backend
```

### 2. 安装依赖

```bash
# 安装所有依赖（含开发依赖：black、ruff、pytest 等）
uv sync --all-groups
```

### 3. 启动开发服务器

```bash
uv run cims
```

启动后同时监听四个端口：

| 端口 | 服务 | 说明 |
|------|------|------|
| `:27041` | Client API | 面向 ClassIsland 客户端 |
| `:27042` | Management API | 用户管理、认证、账户操作 |
| `:27043` | Admin API | 超管后台、系统设置 |
| `:27044` | gRPC | Cyrene_MSP 协议（注册/命令/配置/审计） |

首次启动会自动在 PostgreSQL 中通过 SQLAlchemy `create_all()` 创建所有数据表。

---

## Protobuf 代码生成

当修改了 `api/Protobuf/` 目录下的 `.proto` 源文件后，需要重新生成 Python 代码：

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

生成结果位于 `app/grpc/api/Protobuf/`，包含三类文件：

| 文件后缀 | 说明 |
|----------|------|
| `*_pb2.py` | Protobuf 消息类 |
| `*_pb2_grpc.py` | gRPC 服务桩代码 |
| `*_pb2.pyi` | 类型存根（IDE 类型提示） |

---

## 测试

> **前提**：需要运行中的 PostgreSQL 和 Redis 实例。测试运行时会使用当前配置的数据库。

### 运行测试

```bash
# 运行全部测试
uv run pytest

# 显示详细输出
uv run pytest -v

# 查看覆盖率（含未覆盖行号）
uv run pytest --cov=app --cov-report=term-missing

# 仅运行某个测试文件
uv run pytest tests/test_api.py

# 仅运行匹配名称的测试
uv run pytest -k "test_admin_create"

# 生成 HTML 覆盖率报告
uv run pytest --cov=app --cov-report=html
# 报告输出至 htmlcov/index.html
```

### 测试套件结构

| 文件 | 覆盖范围 |
|------|----------|
| `conftest.py` | 测试 Fixtures（数据库初始化、测试租户创建） |
| `test_api.py` | Client API、Command API、资源文件管理 |
| `test_admin_tenant.py` | Admin API、租户 CRUD、Auth 中间件、Redis、资源令牌 |
| `test_grpc.py` | gRPC 五项服务、SessionManager、在线状态 |
| `test_coverage.py` | 边界情况、异常路径、覆盖率补充 |

### 覆盖率排除

以下文件/目录在覆盖率统计中被排除（见 `pyproject.toml [tool.coverage.run]`）：

- `app/grpc/api/Protobuf/*` — 自动生成的代码
- `app/main.py` — 入口启动逻辑

---

## 代码质量

### 格式化与 Lint

```bash
# 代码格式化
uv run black .

# 格式检查（不修改文件）
uv run black --check .

# Lint 检查
uv run ruff check .

# Lint 自动修复
uv run ruff check --fix .

# 类型检查
uv run pyright
```

### CI 流水线

项目配置了 GitHub Actions CI（`.github/workflows/python-ci.yml`），每次推送和 PR 会自动执行：

1. 代码格式检查（black --check）
2. Lint 检查（ruff check）
3. 类型检查（pyright）
4. 测试运行（pytest）

---

## 项目架构概览

```
请求流程：

ClassIsland 客户端
    │
    ├── HTTP (:27041) ──► Client API ──► 资源文件 / Manifest
    │
    └── gRPC (:27044) ──► Cyrene_MSP 服务 ──┬── 注册
                                             ├── 握手
                                             ├── 命令推送  ◄──┐
                                             ├── 配置上传     │
                                             └── 审计上报     │
                                                              │
管理后台                                                       │
    │                                                         │
    ├── HTTP (:27042) ──► Management API ──┬── 认证/账户        │
    │                                      ├── 资源管理        │
    │                                      └── 指令下发 ───────┘
    │
    └── HTTP (:27043) ──► Admin API ──┬── 全局用户管理
                                      ├── 系统设置
                                      └── 批量操作

共享基础设施：
    ├── PostgreSQL ──► 持久化（ORM via SQLAlchemy）
    ├── Redis ────────► 缓存 / 会话 / 令牌
    └── PGP ──────────► 密钥管理（gRPC Handshake）
```

---

## IDE 推荐配置

### VS Code

推荐安装以下扩展：

- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) — Python 语言支持
- [Pylance](https://marketplace.visualstudio.com/items?itemName=ms-python.vscode-pylance) — 类型检查 & IntelliSense
- [Ruff](https://marketplace.visualstudio.com/items?itemName=charliermarsh.ruff) — Lint & 格式化
- [Even Better TOML](https://marketplace.visualstudio.com/items?itemName=tamasfe.even-better-toml) — pyproject.toml 语法高亮

推荐 `.vscode/settings.json`：

```json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "[python]": {
    "editor.defaultFormatter": "charliermarsh.ruff",
    "editor.formatOnSave": true
  },
  "python.analysis.typeCheckingMode": "basic"
}
```

### PyCharm

- 内置 Python 支持，无需额外配置
- 建议启用 Ruff 插件并将 Black 设置为外部格式化工具
- 将 `app/grpc/api/Protobuf/` 目录标记为 **Generated Sources Root**

---

## 常见问题

### Q: 启动时提示连不上数据库？

确认 PostgreSQL 正在运行且连接信息与 `DATABASE_URL` 一致：

```bash
# 检查容器状态
docker ps | grep cims-postgres

# 测试连接
docker exec -it cims-postgres psql -U postgresql -d cims -c "SELECT 1;"
```

### Q: Redis 连接超时？

确认 Redis 正在运行且密码正确：

```bash
docker ps | grep cims-redis
docker exec -it cims-redis redis-cli -a password PING
```

### Q: gRPC Handshake 失败，提示找不到密钥文件？

确保 `CIMS_KEY_FILE` 指向的文件存在。首次运行时需要生成服务器密钥：

```bash
# 密钥文件会在首次 Handshake 时自动生成
# 或手动指定路径:
export CIMS_KEY_FILE=/path/to/your/cims_server.key
```

### Q: 测试运行很慢？

- 确认使用了 `hiredis` 加速 Redis（`uv sync --all-groups` 会自动安装）
- 检查 PostgreSQL 的 `shared_buffers` 配置是否合理
- 使用 `-x` 参数在首个失败时停止：`uv run pytest -x`
