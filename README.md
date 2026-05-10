# API Versioner — 声明式 API 版本兼容层服务

基于 Python + FastAPI 的 API 版本兼容层服务，支持声明式版本配置、自动字段降级、废弃通知和迁移指南。

## 架构说明

- **内部业务逻辑始终使用最新版本（v3）的数据结构**
- 响应时根据客户端请求版本自动做字段转换/裁剪/重命名
- 新增版本只需在 `app/version_config.py` 中添加配置，无需改路由代码

### 三个版本的用户数据差异

| 字段 | v1 | v2 | v3 |
|---|---|---|---|
| id | ✅ | ✅ | ✅ |
| full_name | ✅ | ❌ | ❌ |
| first_name | ❌ | ✅ | ✅ |
| last_name | ❌ | ✅ | ✅ |
| display_name | ❌ | ❌ | ✅ |
| email | ✅ | ✅ | ✅ |

## 启动方式

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --port 8000

# 运行测试
pytest -v
```

启动后访问 http://localhost:8000/docs 查看交互式 API 文档。

## 版本指定方式

1. **请求头** `X-API-Version: 2`
2. **URL 前缀** `/v2/users`
3. **都不指定** → 默认使用最新版本（v3）

## curl 示例

### 创建用户

```bash
# v3 (默认) — 使用 first_name + last_name + display_name
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -d '{"first_name":"Alice","last_name":"Smith","display_name":"Ali","email":"alice@example.com"}'

# v2 — 使用 first_name + last_name（通过请求头）
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -H "X-API-Version: 2" \
  -d '{"first_name":"Bob","last_name":"Jones","email":"bob@example.com"}'

# v1 — 使用 full_name（通过请求头）
curl -X POST http://localhost:8000/users \
  -H "Content-Type: application/json" \
  -H "X-API-Version: 1" \
  -d '{"full_name":"Carol White","email":"carol@example.com"}'

# v1 — 使用 URL 前缀
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -d '{"full_name":"Dave Brown","email":"dave@example.com"}'
```

### 查询用户

```bash
# 默认（v3）— 返回完整字段
curl http://localhost:8000/users/1

# v2 — 通过请求头，返回 first_name + last_name，无 display_name
curl -H "X-API-Version: 2" http://localhost:8000/users/1

# v1 — 通过请求头，返回 full_name（由 first_name + last_name 拼接）
curl -H "X-API-Version: 1" http://localhost:8000/users/1

# v2 — 通过 URL 前缀
curl http://localhost:8000/v2/users/1
```

### 列出所有用户

```bash
curl http://localhost:8000/users
curl -H "X-API-Version: 1" http://localhost:8000/users
curl http://localhost:8000/v2/users
```

### 更新用户

```bash
# v3
curl -X PUT http://localhost:8000/users/1 \
  -H "Content-Type: application/json" \
  -d '{"display_name":"New Name"}'

# v1 — full_name 自动拆分
curl -X PUT http://localhost:8000/v1/users/1 \
  -H "Content-Type: application/json" \
  -d '{"full_name":"New First New Last"}'
```

### 删除用户

```bash
curl -X DELETE http://localhost:8000/users/1
```

### 迁移指南 API

```bash
# 查看所有版本及状态
curl http://localhost:8000/api/versions

# 查看某版本变更说明
curl http://localhost:8000/api/versions/1/changelog
curl http://localhost:8000/api/versions/2/changelog
curl http://localhost:8000/api/versions/3/changelog
```

### 废弃通知

v1 和 v2 已标记为 deprecated，使用这些版本时响应会自动包含：

```
X-Deprecated: true
X-Sunset-Date: 2025-12-31   (v1)
X-Sunset-Date: 2026-06-30   (v2)
```

所有响应都包含 `X-API-Version` 头标识实际使用的版本号。

## 项目结构

```
app/
  __init__.py
  main.py              # FastAPI 入口，中间件注册
  database.py          # SQLite + SQLAlchemy 配置
  models.py            # ORM 模型（始终用 v3 结构）
  schemas.py           # 各版本 Pydantic 模型
  version_config.py    # 声明式版本映射规则（核心）
  version_middleware.py # 版本路由 + 废弃头注入
  routers/
    users.py           # 用户 CRUD 路由
    versions.py        # 版本迁移指南路由
  services/
    user_service.py    # 用户业务逻辑
tests/
  test_api.py          # API 集成测试
  test_version_config.py # 版本映射单元测试
requirements.txt
pytest.ini
```
