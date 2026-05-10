# API Version Compatibility Layer

一个基于 Python + FastAPI 的 API 版本兼容层服务演示项目。

## 功能特性

1. **版本路由** - 支持通过请求头 `X-API-Version` 或 URL 前缀 `/v2/users` 指定版本，默认使用最新版本
2. **声明式版本配置** - 在 `app/versions.py` 中定义每个版本的字段映射规则，新增版本只需加配置
3. **自动字段降级** - 内部业务逻辑始终按最新版本（v3）处理，响应时自动转换字段
4. **废弃通知** - 已废弃版本自动注入 `X-Deprecated: true` 和 `X-Sunset-Date` 响应头
5. **迁移指南 API** - `/api/versions` 查看所有版本，`/api/versions/{v}/changelog` 查看变更日志

## 版本差异说明

| 版本 | 状态 | 用户字段 |
|------|------|----------|
| v1 | deprecated (sunset: 2025-12-31) | `id`, `full_name`, `email`, `created_at` |
| v2 | deprecated (sunset: 2026-06-30) | `id`, `first_name`, `last_name`, `email`, `created_at` |
| v3 | active | `id`, `first_name`, `last_name`, `display_name`, `email`, `created_at` |

## 安装与启动

```bash
# 安装依赖
pip install -r requirements.txt

# 启动服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

服务启动后访问 http://localhost:8000/docs 查看 Swagger 文档。

## API 使用示例

### 创建用户

**v1 (使用 full_name):**
```bash
curl -X POST http://localhost:8000/users \
  -H "X-API-Version: 1" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "John Doe", "email": "john@example.com"}'
```

**v2 (使用 first_name + last_name):**
```bash
curl -X POST http://localhost:8000/users \
  -H "X-API-Version: 2" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Jane", "last_name": "Smith", "email": "jane@example.com"}'
```

**v3 (最新版本，含 display_name):**
```bash
curl -X POST http://localhost:8000/users \
  -H "X-API-Version: 3" \
  -H "Content-Type: application/json" \
  -d '{"first_name": "Alice", "last_name": "Johnson", "display_name": "AJ", "email": "alice@example.com"}'
```

### URL 前缀方式指定版本

```bash
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -d '{"full_name": "URL Test", "email": "url@example.com"}'
```

### 获取用户列表

**v1 响应（自动转换为 full_name）:**
```bash
curl http://localhost:8000/users -H "X-API-Version: 1"
```

**v3 响应（完整字段）:**
```bash
curl http://localhost:8000/users -H "X-API-Version: 3"
```

### 获取单个用户

```bash
curl http://localhost:8000/users/1 -H "X-API-Version: 2"
```

### 更新用户

```bash
curl -X PUT http://localhost:8000/users/1 \
  -H "X-API-Version: 1" \
  -H "Content-Type: application/json" \
  -d '{"full_name": "John Updated"}'
```

### 删除用户

```bash
curl -X DELETE http://localhost:8000/users/1
```

### 查看版本信息

```bash
# 所有版本列表
curl http://localhost:8000/api/versions

# v1 变更日志
curl http://localhost:8000/api/versions/1/changelog
```

### 废弃响应头示例

访问 v1 接口时，响应头会包含：
```
X-Deprecated: true
X-Sunset-Date: 2025-12-31
X-API-Version: 1
```

## 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
.
├── app/
│   ├── __init__.py
│   ├── main.py          # FastAPI 主应用和路由
│   ├── versions.py      # 版本配置（字段映射、状态、changelog）
│   ├── database.py      # 数据库模型和连接
│   ├── schemas.py       # Pydantic 模型
│   ├── transformer.py   # 字段转换工具
│   └── middleware.py    # 版本中间件和依赖
├── tests/
│   ├── __init__.py
│   └── test_versioning.py
├── requirements.txt
└── README.md
```

## 新增版本指南

1. 在 `app/versions.py` 的 `VERSIONS` 字典中添加新版本配置：
   - 定义 `fields` 列表
   - 添加必要的 `field_transforms` 转换函数
   - 设置 `status` 和 `sunset_date`
   - 编写 `changelog`

2. 如有需要，在 `app/schemas.py` 中添加新版本的请求模型

3. 如有特殊的请求体解析逻辑，在 `app/transformer.py` 的 `parse_body_for_version` 中添加

4. 路由代码无需修改！
