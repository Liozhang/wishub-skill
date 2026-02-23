"""
Skill Orchestration Routes
"""
import logging
import uuid
from typing import Dict, Any, List, Set
from datetime import datetime
from collections import defaultdict, deque

from fastapi import APIRouter, HTTPException, status, Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from wishub_skill.protocol.models import (
    SkillOrchestrationRequest,
    SkillOrchestrationResponse,
    WorkflowDefinition,
    WorkflowStep,
    ExecutionMode
)
from wishub_skill.server.runtime import runtime_engine
from wishub_skill.server.database import Skill, Workflow, WorkflowExecution, get_db
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
    "/orchestrate",
    response_model=SkillOrchestrationResponse,
    summary="Skill 编排",
    description="执行 Skill 工作流编排"
)
async def orchestrate_skills(
    request: SkillOrchestrationRequest,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> SkillOrchestrationResponse:
    """
    Skill 编排端点

    支持顺序、并行和混合执行模式。

    Args:
        request: Skill 编排请求
        db: 数据库会话
        api_key: API 密钥

    Returns:
        Skill 编排响应
    """
    execution_id = str(uuid.uuid4())
    start_time = datetime.utcnow()

    try:
        # 1. 验证工作流定义
        if not request.workflow.steps:
            raise ValueError("工作流必须包含至少一个步骤")

        # 2. 检查依赖循环
        has_cycle = _check_cyclic_dependencies(request.workflow.steps)
        if has_cycle:
            return SkillOrchestrationResponse(
                status="error",
                message="工作流存在循环依赖",
                error={
                    "code": "WORKFLOW_002",
                    "details": "检测到循环依赖"
                }
            )

        # 3. 保存工作流定义
        workflow = Workflow(
            workflow_id=request.workflow_id,
            name=request.workflow.name,
            description=request.workflow.description,
            workflow_definition=request.workflow.model_dump(),
            execution_mode=request.execution_mode.value,
            timeout=request.timeout
        )
        db.add(workflow)
        await db.commit()

        # 4. 创建执行记录
        execution = WorkflowExecution(
            execution_id=execution_id,
            workflow_id=request.workflow_id,
            status="running",
            created_at=start_time
        )
        db.add(execution)
        await db.commit()

        # 5. 执行工作流
        logger.info(
            f"执行工作流: {request.workflow_id} "
            f"(模式: {request.execution_mode}, 步骤数: {len(request.workflow.steps)})"
        )

        try:
            results = await _execute_workflow(
                steps=request.workflow.steps,
                mode=request.execution_mode,
                db=db
            )

            end_time = datetime.utcnow()
            execution_time = (end_time - start_time).total_seconds()

            # 更新执行记录
            execution.status = "success"
            execution.results = results
            execution.execution_time = execution_time
            execution.completed_at = end_time
            await db.commit()

            logger.info(f"工作流执行成功: {request.workflow_id}")

            return SkillOrchestrationResponse(
                status="success",
                execution_id=execution_id,
                results=results,
                execution_time=execution_time,
                message="工作流执行成功"
            )

        except Exception as e:
            logger.error(f"工作流执行失败: {e}")

            execution.status = "error"
            execution.error_message = str(e)
            execution.completed_at = datetime.utcnow()
            await db.commit()

            return SkillOrchestrationResponse(
                status="error",
                execution_id=execution_id,
                message="执行失败",
                error={
                    "code": "WORKFLOW_003",
                    "details": str(e)
                }
            )

    except Exception as e:
        logger.error(f"工作流编排失败: {e}")
        return SkillOrchestrationResponse(
            status="error",
            message="编排失败",
            error={
                "code": "WORKFLOW_999",
                "details": str(e)
            }
        )


async def _execute_workflow(
    steps: List[WorkflowStep],
    mode: ExecutionMode,
    db: AsyncSession
) -> Dict[str, Any]:
    """
    执行工作流

    Args:
        steps: 工作流步骤列表
        mode: 执行模式
        db: 数据库会话

    Returns:
        各步骤的执行结果
    """
    results = {}
    completed_steps: Set[str] = set()

    if mode == ExecutionMode.SEQUENTIAL:
        # 顺序执行
        for step in steps:
            logger.info(f"执行步骤: {step.step_id}")
            result = await _execute_step(step, db, results)
            results[step.step_id] = result
            completed_steps.add(step.step_id)

    elif mode == ExecutionMode.PARALLEL:
        # 并行执行（假设所有步骤无依赖）
        import asyncio

        tasks = []
        for step in steps:
            if not step.depends_on:
                task = _execute_step(step, db, results)
                tasks.append((step.step_id, task))
            else:
                # 有依赖的步骤需要特殊处理
                results[step.step_id] = await _execute_step(step, db, results)

        # 并行执行无依赖的步骤
        executed_results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        for (step_id, _), result in zip(tasks, executed_results):
            results[step_id] = result

    elif mode == ExecutionMode.HYBRID:
        # 混合执行（DAG 调度）
        results = await _execute_dag(steps, db)

    return results


async def _execute_dag(
    steps: List[WorkflowStep],
    db: AsyncSession
) -> Dict[str, Any]:
    """
    按 DAG 顺序执行工作流

    Args:
        steps: 工作流步骤列表
        db: 数据库会话

    Returns:
        各步骤的执行结果
    """
    results = {}
    completed: Set[str] = set()

    # 构建依赖图
    dependency_map = defaultdict(list)
    reverse_map = defaultdict(list)

    for step in steps:
        for dep in step.depends_on or []:
            dependency_map[dep].append(step)
            reverse_map[step.step_id].append(dep)

    # 初始化待执行队列（无依赖的步骤）
    queue = deque([
        step for step in steps
        if not step.depends_on
    ])

    import asyncio

    while queue:
        # 获取当前可执行的步骤
        current_steps = []
        while queue:
            current_steps.append(queue.popleft())

        # 并行执行当前步骤
        tasks = []
        for step in current_steps:
            task = _execute_step(step, db, results)
            tasks.append((step.step_id, task))

        executed_results = await asyncio.gather(
            *[task for _, task in tasks],
            return_exceptions=True
        )

        for (step_id, _), result in zip(tasks, executed_results):
            results[step_id] = result
            completed.add(step_id)

            # 检查依赖此步骤的步骤是否可以执行
            for dependent_step in dependency_map[step_id]:
                deps = reverse_map[dependent_step.step_id]
                if all(dep in completed for dep in deps):
                    queue.append(dependent_step)

    return results


async def _execute_step(
    step: WorkflowStep,
    db: AsyncSession,
    context: Dict[str, Any]
) -> Dict[str, Any]:
    """
    执行单个步骤

    Args:
        step: 工作流步骤
        db: 数据库会话
        context: 上下文（包含前置步骤的结果）

    Returns:
        执行结果
    """
    try:
        # 查询 Skill
        result = await db.execute(
            select(Skill).where(Skill.skill_id == step.skill_id)
        )
        skill = result.scalar_one_or_none()

        if not skill:
            raise ValueError(f"Skill 不存在: {step.skill_id}")

        # 解析输入（支持引用前置步骤的结果）
        resolved_inputs = _resolve_inputs(step.inputs, context)

        # 执行 Skill
        execution_result = await runtime_engine.execute_skill(
            skill=skill,
            inputs=resolved_inputs,
            timeout=skill.timeout
        )

        return execution_result

    except Exception as e:
        logger.error(f"步骤执行失败: {step.step_id} - {e}")
        return {
            "status": "error",
            "error": str(e)
        }


def _resolve_inputs(inputs: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """
    解析输入（支持引用前置步骤的结果）

    Args:
        inputs: 原始输入
        context: 上下文

    Returns:
        解析后的输入
    """
    import re

    def resolve_value(value):
        if isinstance(value, str):
            # 匹配 {{step_id.field}} 格式
            pattern = r'\{\{(\w+)\.(\w+)\}\}'
            matches = re.findall(pattern, value)

            for step_id, field in matches:
                if step_id in context and context[step_id].get("status") == "success":
                    outputs = context[step_id].get("outputs", {})
                    if field in outputs:
                        value = value.replace(f"{{{{{step_id}.{field}}}}}", str(outputs[field]))

        return value

    if isinstance(inputs, dict):
        return {key: resolve_value(val) for key, val in inputs.items()}
    elif isinstance(inputs, list):
        return [resolve_value(item) for item in inputs]
    else:
        return resolve_value(inputs)


def _check_cyclic_dependencies(steps: List[WorkflowStep]) -> bool:
    """
    检查工作流是否存在循环依赖

    Args:
        steps: 工作流步骤列表

    Returns:
        是否存在循环依赖
    """
    # 构建依赖图
    graph = {step.step_id: step.depends_on or [] for step in steps}

    # 检测循环（使用 DFS）
    def visit(node, visited, rec_stack):
        visited.add(node)
        rec_stack.add(node)

        for neighbor in graph.get(node, []):
            if neighbor not in visited:
                if visit(neighbor, visited, rec_stack):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(node)
        return False

    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    for node in graph:
        if node not in visited:
            if visit(node, visited, rec_stack):
                return True

    return False


@router.get(
    "/workflow/{execution_id}",
    summary="获取工作流执行状态",
    description="查询工作流执行的进度和结果"
)
async def get_workflow_status(
    execution_id: str,
    db: AsyncSession = Depends(get_db),
    api_key: str = Depends(verify_api_key)
) -> SkillOrchestrationResponse:
    """获取工作流执行状态"""
    try:
        # 查询执行记录
        result = await db.execute(
            select(WorkflowExecution).where(
                WorkflowExecution.execution_id == execution_id
            )
        )
        execution = result.scalar_one_or_none()

        if not execution:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="工作流执行不存在"
            )

        return SkillOrchestrationResponse(
            status=execution.status,
            execution_id=execution_id,
            results=execution.results,
            execution_time=execution.execution_time,
            message=execution.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取工作流状态失败: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
