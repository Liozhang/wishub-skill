"""
WisHub Skill Protocol Models
"""
from typing import Dict, Any, Optional, List
from pydantic import BaseModel, Field
from enum import Enum


class SkillLanguage(str, Enum):
    """Skill 编程语言"""
    PYTHON = "python"
    TYPESCRIPT = "typescript"
    GO = "go"
    JAVA = "java"
    RUST = "rust"


class ExecutionMode(str, Enum):
    """执行模式"""
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"
    HYBRID = "hybrid"


# Skill Invoke
class SkillInvokeRequest(BaseModel):
    """Skill 调用请求"""
    skill_id: str = Field(..., description="Skill ID")
    skill_version: Optional[str] = Field(
        default=None,
        description="Skill 版本 (可选)"
    )
    inputs: Dict[str, Any] = Field(
        ...,
        description="Skill 输入参数"
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="超时时间（秒）"
    )
    is_async: bool = Field(
        default=False,
        description="是否异步执行"
    )


class SkillInvokeResponse(BaseModel):
    """Skill 调用响应"""
    status: str = Field(..., description="状态: success/pending/error")
    task_id: Optional[str] = Field(
        default=None,
        description="任务 ID (异步模式)"
    )
    outputs: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Skill 输出结果"
    )
    execution_time: Optional[float] = Field(
        default=None,
        description="执行时间（秒）"
    )
    message: Optional[str] = Field(
        default=None,
        description="消息"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="错误信息"
    )


# Skill Register
class SkillRegistrationRequest(BaseModel):
    """Skill 注册请求"""
    skill_id: str = Field(..., description="Skill ID (唯一)")
    skill_name: str = Field(..., description="Skill 名称")
    description: Optional[str] = Field(
        default=None,
        description="Skill 描述"
    )
    version: str = Field(
        ...,
        description="版本号 (SemVer 格式: x.y.z)"
    )
    language: SkillLanguage = Field(
        ...,
        description="编程语言"
    )
    code: str = Field(
        ...,
        description="Skill 代码 (Base64 编码)"
    )
    dependencies: Optional[List[str]] = Field(
        default=None,
        description="依赖列表"
    )
    input_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="输入 Schema"
    )
    output_schema: Optional[Dict[str, Any]] = Field(
        default=None,
        description="输出 Schema"
    )
    timeout: int = Field(
        default=30,
        ge=1,
        le=300,
        description="默认超时时间（秒）"
    )
    author: Optional[str] = Field(
        default=None,
        description="作者"
    )
    license: Optional[str] = Field(
        default=None,
        description="许可证"
    )


class SkillRegistrationResponse(BaseModel):
    """Skill 注册响应"""
    status: str = Field(..., description="状态: success/error")
    skill_id: Optional[str] = Field(
        default=None,
        description="Skill ID"
    )
    version: Optional[str] = Field(
        default=None,
        description="版本号"
    )
    registration_time: Optional[str] = Field(
        default=None,
        description="注册时间"
    )
    message: Optional[str] = Field(
        default=None,
        description="消息"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="错误信息"
    )


# Skill Discovery
class SkillDiscoveryRequest(BaseModel):
    """Skill 发现请求"""
    query: Optional[str] = Field(
        default=None,
        description="搜索关键词"
    )
    category: Optional[str] = Field(
        default=None,
        description="分类"
    )
    language: Optional[str] = Field(
        default=None,
        description="编程语言"
    )
    author: Optional[str] = Field(
        default=None,
        description="作者"
    )
    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="返回数量限制"
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="偏移量"
    )


class SkillInfo(BaseModel):
    """Skill 信息"""
    skill_id: str = Field(..., description="Skill ID")
    skill_name: str = Field(..., description="Skill 名称")
    description: Optional[str] = Field(
        default=None,
        description="描述"
    )
    version: str = Field(..., description="版本号")
    category: Optional[str] = Field(
        default=None,
        description="分类"
    )
    language: str = Field(..., description="编程语言")
    author: Optional[str] = Field(
        default=None,
        description="作者"
    )
    downloads: int = Field(
        default=0,
        description="下载次数"
    )
    rating: float = Field(
        default=0.0,
        ge=0.0,
        le=5.0,
        description="评分"
    )


class SkillDiscoveryResponse(BaseModel):
    """Skill 发现响应"""
    status: str = Field(..., description="状态: success/error")
    skills: Optional[List[SkillInfo]] = Field(
        default=None,
        description="Skill 列表"
    )
    total: Optional[int] = Field(
        default=None,
        description="总数"
    )
    message: Optional[str] = Field(
        default=None,
        description="消息"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="错误信息"
    )


# Skill Orchestration
class WorkflowStep(BaseModel):
    """工作流步骤"""
    step_id: str = Field(..., description="步骤 ID")
    skill_id: str = Field(..., description="Skill ID")
    inputs: Dict[str, Any] = Field(
        ...,
        description="输入参数"
    )
    depends_on: Optional[List[str]] = Field(
        default=None,
        description="依赖的步骤 ID"
    )


class WorkflowDefinition(BaseModel):
    """工作流定义"""
    name: str = Field(..., description="工作流名称")
    description: Optional[str] = Field(
        default=None,
        description="工作流描述"
    )
    steps: List[WorkflowStep] = Field(
        ...,
        description="工作流步骤列表"
    )


class SkillOrchestrationRequest(BaseModel):
    """Skill 编排请求"""
    workflow_id: str = Field(..., description="工作流 ID")
    workflow: WorkflowDefinition = Field(
        ...,
        description="工作流定义"
    )
    execution_mode: ExecutionMode = Field(
        default=ExecutionMode.SEQUENTIAL,
        description="执行模式"
    )
    timeout: int = Field(
        default=300,
        ge=1,
        le=3600,
        description="超时时间（秒）"
    )


class SkillOrchestrationResponse(BaseModel):
    """Skill 编排响应"""
    status: str = Field(..., description="状态: success/running/error")
    execution_id: Optional[str] = Field(
        default=None,
        description="执行 ID"
    )
    results: Optional[Dict[str, Any]] = Field(
        default=None,
        description="执行结果"
    )
    execution_time: Optional[float] = Field(
        default=None,
        description="执行时间（秒）"
    )
    message: Optional[str] = Field(
        default=None,
        description="消息"
    )
    error: Optional[Dict[str, Any]] = Field(
        default=None,
        description="错误信息"
    )


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str = Field(..., description="状态: healthy/unhealthy")
    version: str = Field(..., description="版本号")
    dependencies: Dict[str, str] = Field(
        default_factory=dict,
        description="依赖状态"
    )
