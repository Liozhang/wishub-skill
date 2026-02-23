"""
WisHub Skill Protocol Models Tests
"""
import pytest
from wishub_skill.protocol.models import (
    SkillLanguage,
    ExecutionMode,
    SkillInvokeRequest,
    SkillInvokeResponse,
    SkillRegistrationRequest,
    SkillInfo,
    WorkflowStep,
    WorkflowDefinition
)


def test_skill_language_enum():
    """测试 SkillLanguage 枚举"""
    assert SkillLanguage.PYTHON == "python"
    assert SkillLanguage.TYPESCRIPT == "typescript"
    assert SkillLanguage.GO == "go"


def test_execution_mode_enum():
    """测试 ExecutionMode 枚举"""
    assert ExecutionMode.SEQUENTIAL == "sequential"
    assert ExecutionMode.PARALLEL == "parallel"
    assert ExecutionMode.HYBRID == "hybrid"


def test_skill_invoke_request_valid():
    """测试有效的 SkillInvokeRequest"""
    request = SkillInvokeRequest(
        skill_id="skill_custom",
        inputs={"name": "test"}
    )

    assert request.skill_id == "skill_custom"
    assert request.inputs == {"name": "test"}
    assert request.timeout == 30
    assert request.async is False


def test_skill_invoke_request_async():
    """测试异步 SkillInvokeRequest"""
    request = SkillInvokeRequest(
        skill_id="skill_custom",
        inputs={"name": "test"},
        timeout=60,
        async=True
    )

    assert request.timeout == 60
    assert request.async is True


def test_skill_invoke_response_success():
    """测试成功的 SkillInvokeResponse"""
    response = SkillInvokeResponse(
        status="success",
        outputs={"result": "hello"},
        execution_time=1.23
    )

    assert response.status == "success"
    assert response.outputs == {"result": "hello"}
    assert response.execution_time == 1.23


def test_skill_invoke_response_pending():
    """测试待处理的 SkillInvokeResponse"""
    response = SkillInvokeResponse(
        status="pending",
        task_id="task_001"
    )

    assert response.status == "pending"
    assert response.task_id == "task_001"


def test_skill_registration_request_valid():
    """测试有效的 SkillRegistrationRequest"""
    request = SkillRegistrationRequest(
        skill_id="skill_custom",
        skill_name="自定义技能",
        version="1.0.0",
        language=SkillLanguage.PYTHON,
        code="ZGVmIGV4ZWN1dGUoaW5wdXRzKToKICAgIHJldHVybiB7InJlc3VsdCI6ICJoZWxsbyJ9"
    )

    assert request.skill_id == "skill_custom"
    assert request.version == "1.0.0"
    assert request.language == SkillLanguage.PYTHON


def test_skill_info():
    """测试 SkillInfo"""
    info = SkillInfo(
        skill_id="skill_custom",
        skill_name="自定义技能",
        version="1.0.0",
        language="python",
        downloads=1234,
        rating=4.5
    )

    assert info.skill_id == "skill_custom"
    assert info.downloads == 1234
    assert info.rating == 4.5


def test_workflow_step():
    """测试 WorkflowStep"""
    step = WorkflowStep(
        step_id="step_1",
        skill_id="skill_custom",
        inputs={"text": "Hello"}
    )

    assert step.step_id == "step_1"
    assert step.skill_id == "skill_custom"


def test_workflow_step_with_dependencies():
    """测试带依赖的 WorkflowStep"""
    step = WorkflowStep(
        step_id="step_2",
        skill_id="skill_custom",
        inputs={"data": "{{step_1.result}}"},
        depends_on=["step_1"]
    )

    assert step.depends_on == ["step_1"]


def test_workflow_definition():
    """测试 WorkflowDefinition"""
    workflow = WorkflowDefinition(
        name="测试工作流",
        description="这是一个测试工作流",
        steps=[
            WorkflowStep(
                step_id="step_1",
                skill_id="skill_custom",
                inputs={"text": "Hello"}
            )
        ]
    )

    assert workflow.name == "测试工作流"
    assert len(workflow.steps) == 1
