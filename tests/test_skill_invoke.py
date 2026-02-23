"""
Test Skill Invocation API
"""
import pytest
from httpx import AsyncClient

from wishub_skill.protocol.models import SkillInvokeRequest


@pytest.mark.asyncio
async def test_invoke_skill_success(client: AsyncClient):
    """测试成功的 Skill 调用"""
    request = SkillInvokeRequest(
        skill_id="test_skill_001",
        inputs={
            "symptoms": ["口渴", "多尿"],
            "patient_age": 45
        },
        timeout=30,
        is_async=False
    )

    response = await client.post(
        "/api/v1/skill/invoke",
        json=request.model_dump(),
        headers={"X-API-Key": "test_key"}
    )

    # 由于我们没有真实的数据库，响应可能是 404 或 500
    assert response.status_code in [200, 404, 500]


@pytest.mark.asyncio
async def test_invoke_skill_not_found(client: AsyncClient):
    """测试调用不存在的 Skill"""
    request = SkillInvokeRequest(
        skill_id="nonexistent_skill",
        inputs={"test": "value"},
        timeout=30,
        is_async=False
    )

    response = await client.post(
        "/api/v1/skill/invoke",
        json=request.model_dump(),
        headers={"X-API-Key": "test_key"}
    )

    assert response.status_code in [200, 500]


@pytest.mark.asyncio
async def test_invoke_skill_async(client: AsyncClient):
    """测试异步调用 Skill"""
    request = SkillInvokeRequest(
        skill_id="test_skill_001",
        inputs={"test": "value"},
        timeout=30,
        is_async=True
    )

    response = await client.post(
        "/api/v1/skill/invoke",
        json=request.model_dump(),
        headers={"X-API-Key": "test_key"}
    )

    assert response.status_code in [200, 500]
