# API 版本兼容层服务

基于 Python + FastAPI 的 API 版本兼容层，支持多版本路由、自动字段转换、废弃通知等功能。

## 功能特性

1. **版本路由** - 支持通过 `X-API-Version 请求头或 URL 前缀指定版本
2. **声明式版本配置** - 配置文件定义字段映射规则
3. **自动字段降级** - 内部使用最新版本数据结构，响应时自动转换
4. **废弃通知** - 旧版本自动注入废弃响应头
5. **迁移指南 API** - 版本列表和变更日志

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动服务

```bash
uvicorn main:app --reload
```

服务默认运行在 http://localhost:8000

### 访问 API 文档

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## 版本使用示例

### 指定版本的两种方式

1. **通过请求头：
```bash
curl -H "X-API-Version: 1" http://localhost:8000/users
```

2. **通过 URL 前缀：
```bash
curl http://localhost:8000/v1/users
```

### 各版本用户结构

**v1:**
```json
{
  "id": 1,
  "full_name": "张三"
}
```

**v2:**
```json
{
  "id": 1,
  "first_name": "张",
  "last_name": "三"
}
```

**v3 (最新):**
```json
{
  "id": 1,
  "first_name": "张",
  "last_name": "三",
  "display_name": "张同学"
}
```

### 创建用户 (v1)
```bash
curl -X POST http://localhost:8000/v1/users \
  -H "Content-Type: application/json" \
  -d '{"full_name": "张三"}'
```

### 创建用户 (v3)
```bash
curl -X POST http://localhost:8000/v3/users \
  -H "Content-Type: application/json" \
  -d '{"first_name": "张", "last_name": "三", "display_name": "张同学"}'
```

### 查看版本列表
```bash
curl http://localhost:8000/api/versions
```

### 查看版本变更日志
```bash
curl http://localhost:8000/api/versions/2/changelog
```

## 运行测试

```bash
pytest tests/ -v
```
