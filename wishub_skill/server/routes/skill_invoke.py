"""
Skill Invocation Routes
"""
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime

from wishub_skill.protocol.models import (
    SkillInvokeRequest,
    SkillInvokeResponse
)
from wishub_skill.server.runtime import runtime_engine
from wishub_skill.server.database import Skill, SkillExecution, get_db
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
    "/invoke",
    response_model=SkillInvokeResponse,
    summary="调用 Skill",
    description="执行指定的 Skill 并返回结果"
)
async def invoke_skill(
    request: SkillInvokeRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> SkillInvokeResponse:
    """
    Skill 调用端点

    Args:
        request: Skill 调用请求
        db: 数据库会话
        api_key: API 密钥

    Returns:
        Skill 调用响应
    """
    task_id = str(uuid.uuid4())
    start_time = datetime.utcnow()

    try:
        # 1. 查询 Skill
        result = await db.execute(
            select(Skill).where(Skill.skill_id == request.skill_id)
        )
        skill = result.scalar_one_or_none()

        if not skill:
            logger.warning(f"Skill 不存在: {request.skill_id}")
            return SkillInvokeResponse(
                status="error",
                message=f"Skill 不存在: {request.skill_id}",
                error={
                    "code": "SKILL_001",
                    "details": "Skill ID 未找到"
                }
            )

        # 2. 验证输入参数
        if skill.input_schema:
            # TODO: 实现 JSON Schema 验证
            pass

        # 3. 创建执行记录
        execution = SkillExecution(
            task_id=task_id,
            skill_id=request.skill_id,
            status="pending",
            inputs=request.inputs,
            created_at=start_time
        )
        db.add(execution)
        await db.commit()

        # 4. 执行 Skill
        if request.is_async:
            # 异步执行
            logger.info(f"异步执行 Skill: {request.skill_id}")
            return SkillInvokeResponse(
                status="pending",
                task_id=task_id,
                message="任务已提交，正在后台执行"
            )
        else:
            # 同步执行
            logger.info(f"同步执行 Skill: {request.skill_id}")

            # 更新状态为运行中
            execution.status = "running"
            execution.started_at = datetime.utcnow()
            await db.commit()

            try:
                # 调用运行时引擎
                result = await runtime_engine.execute_skill(
                    skill=skill,
                    inputs=request.inputs,
                    timeout=request.timeout or skill.timeout
                )

                # 计算执行时间
                end_time = datetime.utcnow()
                execution_time = (end_time - start_time).total_seconds()

                # 更新执行记录
                if result["status"] == "success":
                    execution.status = "success"
                    execution.outputs = result.get("outputs")
                elif result["status"] == "timeout":
                    execution.status = "timeout"
                    execution.error_message = result.get("error")
                else:
                    execution.status = "error"
                    execution.error_message = result.get("error")

                execution.completed_at = end_time
                execution.container_id = result.get("container_id")

                await db.commit()

                logger.info(f"Skill 执行完成: {request.skill_id} (状态: {result['status']})")

                return SkillInvokeResponse(
                    status="success" if result["status"] == "success" else result["status"],
                    task_id=task_id,
                    outputs=result.get("outputs"),
                    execution_time=execution_time,
                    message="执行成功" if result["status"] == "success" else result.get("error")
                )

            except Exception as e:
                logger.error(f"Skill 执行失败: {e}")

                execution.status = "error"
                execution.error_message = str(e)
                execution.completed_at = datetime.utcnow()
                await db.commit()

                return SkillInvokeResponse(
                    status="error",
                    task_id=task_id,
                    error={
                        "code": "SKILL_002",
                        "details": str(e)
                    }
                )

    except Exception as e:
        logger.error(f"Skill 调用失败: {e}")

        # 更新执行记录为错误状态
        try:
            execution.status = "error"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            await db.commit()
        except:
            pass

        return SkillInvokeResponse(
            status="error",
            task_id=task_id,
            error={
                "code": "SKILL_999",
                "details": str(e)
            }
        )


@router.get(
    "/task/{task_id}",
    response_model=SkillInvokeResponse,
    summary="获取任务状态",
    description="查询异步任务的执行状态和结果"
)
async def get_task_status(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> SkillInvokeResponse:
    """获取任务状态"""
    try:
        # 查询执行记录
        result = await db.execute(
            select(SkillExecution).where(SkillExecution.task_id == task_id)
        )
        execution = result.scalar_one_or_none()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="任务不存在"
            )

        # 计算执行时间
        execution_time = None
        if execution.completed_at and execution.started_at:
            execution_time = (execution.completed_at - execution.started_at).total_seconds()

        return SkillInvokeResponse(
            status=execution.status,
            task_id=task_id,
            outputs=execution.outputs,
            execution_time=execution_time,
            message=execution.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取任务状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
