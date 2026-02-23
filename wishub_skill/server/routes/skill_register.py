"""
Skill Registration Routes
"""
import logging
import base64
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from wishub_skill.protocol.models import (
    SkillRegistrationRequest,
    SkillRegistrationResponse
)
from wishub_skill.server.storage import storage_client
from wishub_skill.server.database import Skill, get_db, SkillVersion
from wishub_skill.config import settings

logger = logging.getLogger(__name__)

# 创建路由
router = APIRouter(prefix="/skill", tags=["Skill"])


async def verify_api_key(x_api_key: str = Header(..., alias="X-API-Key")):
    """验证 API 密钥"""
    if settings.AUTH_REQUIRED:
        if not x_api_key:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="缺少或无效的 API 密钥"
            )
    return x_api_key


@router.post(
    "/register",
    response_model=SkillRegistrationResponse,
    summary="注册 Skill",
    description="上传并注册一个新的 Skill"
)
async def register_skill(
    request: SkillRegistrationRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> SkillRegistrationResponse:
    """
    Skill 注册端点

    接收 Skill 代码并注册到系统中。

    Args:
        request: Skill 注册请求
        db: 数据库会话
        api_key: API 密钥

    Returns:
        Skill 注册响应

    Raises:
        HTTPException: 如果发生错误
    """
    try:
        # 1. 检查 Skill 是否已存在
        result = await db.execute(
            select(Skill).where(Skill.skill_id == request.skill_id)
        )
        existing_skill = result.scalar_one_or_none()

        if existing_skill:
            logger.warning(f"Skill 已存在: {request.skill_id}")
            return SkillRegistrationResponse(
                status="error",
                message=f"Skill 已存在: {request.skill_id}",
                error={
                    "code": "SKILL_REG_001",
                    "details": "Skill ID 已被使用"
                }
            )

        # 2. 解码 Base64 代码
        try:
            code_bytes = base64.b64decode(request.code)
            code_str = code_bytes.decode('utf-8')
            logger.info(f"代码解码成功: {len(code_str)} 字符")
        except Exception as e:
            logger.error(f"代码解码失败: {e}")
            return SkillRegistrationResponse(
                status="error",
                message="代码格式无效",
                error={
                    "code": "SKILL_REG_003",
                    "details": "Base64 解码失败"
                }
            )

        # 3. 上传代码到 MinIO
        try:
            code_url = storage_client.upload_code(
                skill_id=request.skill_id,
                version=request.version,
                code_b64=request.code
            )
            logger.info(f"代码上传成功: {code_url}")
        except Exception as e:
            logger.error(f"代码上传失败: {e}")
            return SkillRegistrationResponse(
                status="error",
                message="代码上传失败",
                error={
                    "code": "SKILL_REG_999",
                    "details": str(e)
                }
            )

        # 4. 创建 Skill 记录
        from datetime import datetime

        skill = Skill(
            skill_id=request.skill_id,
            skill_name=request.skill_name,
            description=request.description,
            version=request.version,
            language=request.language.value,
            code_url=code_url,
            dependencies=request.dependencies,
            input_schema=request.input_schema,
            output_schema=request.output_schema,
            timeout=request.timeout,
            author=request.author,
            license=request.license,
            category=request.category
        )

        # 5. 创建 Skill 版本记录
        skill_version = SkillVersion(
            skill_id=request.skill_id,
            version=request.version,
            code_url=code_url,
            dependencies=request.dependencies,
            input_schema=request.input_schema,
            output_schema=request.output_schema
        )

        # 6. 保存到数据库
        db.add(skill)
        db.add(skill_version)
        await db.commit()
        await db.refresh(skill)

        logger.info(f"Skill 注册成功: {request.skill_id} v{request.version}")

        return SkillRegistrationResponse(
            status="success",
            skill_id=skill.skill_id,
            version=skill.version,
            registration_time=skill.created_at.isoformat(),
            message="Skill 注册成功"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skill 注册失败: {e}")
        await db.rollback()

        # 清理已上传的代码
        try:
            storage_client.delete_code(request.skill_id, request.version)
        except:
            pass

        return SkillRegistrationResponse(
            status="error",
            message="注册失败",
            error={
                "code": "SKILL_REG_999",
                "details": str(e)
            }
        )


@router.delete(
    "/{skill_id}",
    summary="删除 Skill",
    description="删除指定的 Skill"
)
async def delete_skill(
    skill_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
):
    """删除 Skill"""
    try:
        # 查找 Skill
        result = await db.execute(
            select(Skill).where(Skill.skill_id == skill_id)
        )
        skill = result.scalar_one_or_none()

        if not skill:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Skill 不存在"
            )

        # 删除数据库记录
        await db.delete(skill)
        await db.commit()

        # 删除存储的代码
        storage_client.delete_code(skill_id, skill.version)

        logger.info(f"Skill 删除成功: {skill_id}")

        return {
            "status": "success",
            "message": f"Skill {skill_id} 已删除"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Skill 删除失败: {e}")
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"删除失败: {str(e)}"
        )
