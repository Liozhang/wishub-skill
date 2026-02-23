# wishub-skill

WisHub Skill Protocol Server - 技能注册、发现、调用和编排

[![CI](https://github.com/Liozhang/wishub-skill/actions/workflows/ci.yml/badge.svg)](https://github.com/Liozhang/wishub-skill/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org/)

## 功能特性

- ✅ Skill 调用协议
- ✅ Skill 注册协议
- ✅ Skill 发现协议
- ✅ Docker 沙箱隔离
- ✅ PostgreSQL 存储
- ✅ FastAPI 服务
- ✅ DAG 工作流编排

## 快速开始

### 使用 Docker Compose

```bash
# 克隆仓库
git clone https://github.com/Liozhang/wishub-skill.git
cd wishub-skill

# 启动服务
docker-compose up -d

# 访问 API 文档
open http://localhost:8000/docs
```

## API 使用示例

### 注册 Skill

```bash
curl -X POST http://localhost:8000/api/v1/skill/register \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "skill_custom",
    "skill_name": "自定义技能",
    "version": "1.0.0",
    "language": "python",
    "code": "ZGVmIGV4ZWN1dGUoaW5wdXRzKToKICAgIHJldHVybiB7InJlc3VsdCI6ICJoZWxsbyJ9",
    "timeout": 30
  }'
```

### 调用 Skill

```bash
curl -X POST http://localhost:8000/api/v1/skill/invoke \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "skill_id": "skill_custom",
    "inputs": {"name": "test"}
  }'
```

## 本地开发

### 快速启动

使用提供的本地启动脚本，快速设置开发环境：

```bash
# 首次使用：设置开发环境
./scripts/local.sh setup

# 启动开发服务器
./scripts/local.sh start

# 访问 API 文档
open http://localhost:8000/docs
```

### 手动安装

如果需要手动设置开发环境：

```bash
# 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖
pip install -r requirements.txt

# 设置环境变量
cp .env.example .env
# 编辑 .env 文件，配置数据库连接信息

# 启动开发服务器
uvicorn wishub_skill.server.app:app --host 0.0.0.0 --port 8000 --reload
```

### 开发命令

```bash
# 运行测试
./scripts/local.sh test

# 安装依赖
./scripts/local.sh install

# 安装开发依赖
./scripts/local.sh install-dev

# 清理虚拟环境
./scripts/local.sh clean
```

### 运行测试

```bash
# 使用本地脚本
./scripts/local.sh test

# 或使用 pytest
pytest tests/ -v

# 带覆盖率
pytest tests/ --cov=wishub_skill --cov-report=html
```

### 代码格式化

```bash
# 使用本地脚本
./scripts/local.sh format

# 或手动运行
black wishub_skill/ tests/
ruff check --fix wishub_skill/ tests/
```

### 环境变量配置

复制 `.env.example` 到 `.env` 并配置：

```env
# API 配置
APP_NAME=wishub-skill
APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000
API_PREFIX=/api/v1

# 认证配置
AUTH_REQUIRED=false
AUTH_HEADER=X-API-Key

# PostgreSQL 配置
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=wishub
POSTGRES_PASSWORD=wishub
POSTGRES_DB=wishub_skill

# Redis 配置
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# MinIO 配置
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET=wishub-skill-storage

# Elasticsearch 配置
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX=skills

# 日志配置
LOG_LEVEL=DEBUG
```

## 许可证

MIT License - see [LICENSE](LICENSE) file for details.

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)
