"""
Skill Database Models
"""
from sqlalchemy import Column, String, Integer, Float, Text, DateTime, ForeignKey, JSON
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

Base = declarative_base()


class Skill(Base):
    """Skill 模型"""
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, autoincrement=True)
    skill_id = Column(String(255), unique=True, nullable=False, index=True)
    skill_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    version = Column(String(50), nullable=False)
    language = Column(String(50), nullable=False)

    # 代码存储
    code_url = Column(String(512), nullable=True)  # MinIO URL
    dependencies = Column(JSON, nullable=True)

    # Schema
    input_schema = Column(JSON, nullable=True)
    output_schema = Column(JSON, nullable=True)

    # 配置
    timeout = Column(Integer, default=30)

    # 元数据
    author = Column(String(255), nullable=True)
    license = Column(String(50), nullable=True)
    category = Column(String(100), nullable=True)

    # 统计
    downloads = Column(Integer, default=0)
    rating = Column(Float, default=0.0)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关系
    versions = relationship("SkillVersion", back_populates="skill", cascade="all, delete-orphan")
    executions = relationship("SkillExecution", back_populates="skill", cascade="all, delete-orphan")


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


class SkillExecution(Base):
    """Skill 执行记录"""
    __tablename__ = "skill_executions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    task_id = Column(String(255), unique=True, nullable=False, index=True)
    skill_id = Column(String(255), ForeignKey("skills.skill_id"), nullable=False, index=True)

    # 执行状态
    status = Column(String(50), default="pending")  # pending, running, success, error, timeout
    inputs = Column(JSON, nullable=True)
    outputs = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    # 执行信息
    execution_time = Column(Float, nullable=True)  # 秒
    container_id = Column(String(255), nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)

    # 关系
    skill = relationship("Skill", back_populates="executions")


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
    workflow_id = Column(String(255), nullable=False)

    status = Column(String(50), default="running")  # running, success, error, timeout
    results = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)

    execution_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
