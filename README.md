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

## 开发

### 运行测试

```bash
pytest tests/
```

## 许可证

MIT License - see [LICENSE](LICENSE) file for details.

## 贡献

欢迎贡献！请查看 [CONTRIBUTING.md](CONTRIBUTING.md)
