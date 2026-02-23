"""
WisHub Skill Pytest Configuration
"""
import pytest
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from wishub_skill.server.app import app


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """创建测试客户端"""
    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test"
    ) as ac:
        yield ac


@pytest.fixture
def sample_skill_invoke_request():
    """示例 Skill 调用请求"""
    return {
        "skill_id": "skill_custom",
        "inputs": {"name": "test"},
        "timeout": 30
    }


@pytest.fixture
def sample_skill_registration_request():
    """示例 Skill 注册请求"""
    return {
        "skill_id": "skill_custom",
        "skill_name": "自定义技能",
        "version": "1.0.0",
        "language": "python",
        "code": "ZGVmIGV4ZWN1dGUoaW5wdXRzKToKICAgIHJldHVybiB7InJlc3VsdCI6ICJoZWxsbyJ9",
        "timeout": 30
    }
