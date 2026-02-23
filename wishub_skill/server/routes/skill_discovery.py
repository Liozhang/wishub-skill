"""
Skill Discovery Routes
"""
import logging
from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from sqlalchemy.sql import func

from wishub_skill.protocol.models import (
    SkillDiscoveryRequest,
    SkillDiscoveryResponse,
    SkillInfo
)
from wishub_skill.server.database import Skill, get_db
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
    "/discovery",
    response_model=SkillDiscoveryResponse,
    summary="Skill 发现",
    description="搜索和发现可用的 Skills"
)
async def discover_skills(
    request: SkillDiscoveryRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> SkillDiscoveryResponse:
    """
    Skill 发现端点

    支持按关键词、分类、语言、作者等条件搜索 Skills。

    Args:
        request: Skill 发现请求
        db: 数据库会话
        api_key: API 密钥

    Returns:
        Skill 发现响应
    """
    try:
        # 构建查询
        query = select(Skill)

        # 添加过滤条件
        conditions = []

        if request.query:
            # 全文搜索
            search_term = f"%{request.query}%"
            conditions.append(
                or_(
                    Skill.skill_name.ilike(search_term),
                    Skill.description.ilike(search_term),
                    Skill.skill_id.ilike(search_term)
                )
            )

        if request.category:
            conditions.append(Skill.category == request.category)

        if request.language:
            conditions.append(Skill.language == request.language)

        if request.author:
            conditions.append(Skill.author == request.author)

        if conditions:
            query = query.where(and_(*conditions))

        # 获取总数
        count_query = select(func.count()).select_from(
            query.subquery()
        )
        total_result = await db.execute(count_query)
        total = total_result.scalar()

        # 分页
        query = query.offset(request.offset).limit(request.limit)

        # 执行查询
        result = await db.execute(query)
        skills = result.scalars().all()

        # 转换为 SkillInfo 列表
        skill_infos: List[SkillInfo] = []
        for skill in skills:
            skill_infos.append(SkillInfo(
                skill_id=skill.skill_id,
                skill_name=skill.skill_name,
                description=skill.description,
                version=skill.version,
                category=skill.category,
                language=skill.language,
                author=skill.author,
                downloads=skill.downloads,
                rating=skill.rating
            ))

        logger.info(f"发现 {len(skill_infos)} 个 Skills (总数: {total})")

        return SkillDiscoveryResponse(
            status="success",
            skills=skill_infos,
            total=total
        )

    except Exception as e:
        logger.error(f"Skill 发现失败: {e}")
        return SkillDiscoveryResponse(
            status="error",
            message="搜索失败",
            error={
                "code": "SKILL_DISC_999",
                "details": str(e)
            }
        )


@router.get(
    "/categories",
    summary="获取所有分类",
    description="列出所有 Skill 分类"
)
async def list_categories(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取所有分类"""
    try:
        # 查询所有不同的分类
        result = await db.execute(
            select(Skill.category).where(Skill.category.isnot(None)).distinct()
        )
        categories = [row[0] for row in result.all()]

        return {
            "status": "success",
            "categories": categories,
            "count": len(categories)
        }

    except Exception as e:
        logger.error(f"获取分类失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get(
    "/languages",
    summary="获取所有编程语言",
    description="列出所有支持的编程语言"
)
async def list_languages(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """获取所有编程语言"""
    try:
        # 查询所有不同的编程语言
        result = await db.execute(
            select(Skill.language).distinct()
        )
        languages = [row[0] for row in result.all()]

        return {
            "status": "success",
            "languages": languages,
            "count": len(languages)
        }

    except Exception as e:
        logger.error(f"获取编程语言失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
