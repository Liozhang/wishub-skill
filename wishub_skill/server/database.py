"""
Skill Database Models - 性能优化版本
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON, Index, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from typing import AsyncGenerator

from wishub_skill.config import settings
from datetime import datetime

Base = declarative_base()

# 异步引擎
async_engine = create_async_engine(
    settings.DATABASE_URL.replace("postgresql://", "postgresql+asyncpg://"),
    echo=settings.DEBUG,
    future=True
)

# 异步会话工厂
AsyncSessionLocal = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """获取数据库会话（依赖注入）"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            try:
                await session.commit()
            except Exception:
                # 如果事务已经回滚，忽略 commit 错误
                pass
            await session.close()


class Skill(Base):
    """Skill 模型"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(String(255), unique=True, nullable=False, index=True)
    skill_name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)
    language = Column(String(50), nullable=False, index=True)

    # 代码存储
    code_url = Column(String(512), nullable=True)  # MinIO URL
    dependencies = Column(JSON, nullable=True)

    # Schema
    input_schema = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)

    # 配置
    timeout = Column(Integer, default=30)

    # 元数据
    author = Column(String(255), nullable=True, index=True)
    license = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True, index=True)

    # 统计
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    versions = relationship("SkillVersion", back_populates="skill", cascade="all, delete-orphan")
    executions = relationship("SkillExecution", back_populates="skill", cascade="all, delete-orphan")

    # 性能优化：复合索引
    __table_args__ = (
        Index('idx_skill_language_category', 'language', 'category'),
        Index('idx_skill_author_created', 'author', 'created_at'),
        Index('idx_skill_downloads_rating', 'downloads', 'rating'),
    )


class SkillVersion(Base):
    """Skill 版本模型"""
    __tablename__ = "skill_versions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(String(255), ForeignKey("skills.skill_id"), nullable=False, index=True)
    version = Column(String(50), nullable=False)

    code_url = Column(String(512), nullable=False)
    dependencies = Column(JSON, nullable=True)
    input_schema = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)

    # 关系
    skill = relationship("Skill", back_populates="versions")

    # 性能优化：复合索引
    __table_args__ = (
        Index('idx_version_skill_created', 'skill_id', 'created_at'),
    )


class SkillExecution(Base):
    """Skill 执行记录"""
    __tablename__ = "skill_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    skill_id = Column(String(255), ForeignKey("skills.skill_id"), nullable=False, index=True)

    # 执行状态
    status = Column(String(50), default="pending", index=True)  # pending, running, success, error, timeout
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # 执行信息
    execution_time = Column(Float, nullable=True)  # 秒
    container_id = Column(String(255), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    skill = relationship("Skill", back_populates="executions")

    # 性能优化：复合索引
    __table_args__ = (
        Index('idx_execution_skill_status', 'skill_id', 'status'),
        Index('idx_execution_status_created', 'status', 'created_at'),
    )


class Workflow(Base):
    """工作流模型"""
    __tablename__ = "workflows"

    id = Column(Integer, primary_key=True, autoincrement=True)
    workflow_id = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    workflow_definition = Column(JSON, nullable=False)
    execution_mode = Column(String(50), default="sequential")
    timeout = Column(Integer, default=300)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class WorkflowExecution(Base):
    """工作流执行记录"""
    __tablename__ = "workflow_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    execution_id = Column(String(255), unique=True, nullable=False, index=True)
    workflow_id = Column(String(255), nullable=False, index=True)

    status = Column(String(50), default="running", index=True)  # running, success, error, timeout
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    execution_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    # 性能优化：复合索引
    __table_args__ = (
        Index('idx_workflow_execution_status', 'workflow_id', 'status'),
        Index('idx_workflow_status_created', 'status', 'created_at'),
    )
