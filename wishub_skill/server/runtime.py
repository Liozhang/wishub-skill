"""
Skill Runtime Engine (Docker Sandbox)
"""
import logging
import base64
import docker
import asyncio
import uuid
from typing import Dict, Any, Optional
from docker.errors import DockerException, ContainerError, ImageNotFound
from pathlib import Path

from wishub_skill.config import settings
from wishub_skill.server.database import Skill, SkillLanguage

logger = logging.getLogger(__name__)


class RuntimeEngine:
    """Skill 运行时引擎 - Docker 沙箱"""

    def __init__(self):
        """初始化运行时引擎"""
        self.client = docker.from_env()

        # 语言特定的 Docker 镜像
        self.language_images = {
            SkillLanguage.PYTHON: "python:3.11-slim",
            SkillLanguage.TYPESCRIPT: "node:20-slim",
            SkillLanguage.GO: "golang:1.21-alpine",
            SkillLanguage.JAVA: "openjdk:21-slim",
            SkillLanguage.RUST: "rust:1.75-slim",
        }

    async def execute_skill(
        self,
        skill: Skill,
        inputs: Dict[str, Any],
        timeout: int = 30
    ) -> Dict[str, Any]:
        """
        在 Docker 沙箱中执行 Skill

        Args:
            skill: Skill 对象
            inputs: 输入参数
            timeout: 超时时间（秒）

        Returns:
            执行结果字典
        """
        task_id = str(uuid.uuid4())
        container_name = f"skill_{skill.skill_id}_{task_id[:8]}"

        logger.info(
            f"准备执行 Skill: {skill.skill_id} (语言: {skill.language}, "
            f"容器: {container_name})"
        )

        try:
            # 1. 下载并解码代码
            code = await self._download_code(skill.code_url)

            # 2. 准备执行命令
            command = self._build_command(skill.language, inputs)

            # 3. 启动容器
            image = self.language_images.get(skill.language)
            if not image:
                raise ValueError(f"不支持的语言: {skill.language}")

            logger.info(f"使用镜像: {image}")

            # 4. 执行（在单独的线程中运行以支持超时）
            result = await asyncio.to_thread(
                self._run_container,
                container_name,
                image,
                code,
                command,
                timeout
            )

            logger.info(f"Skill 执行成功: {skill.skill_id}")

            return {
                "task_id": task_id,
                "status": "success",
                "outputs": result,
                "container_id": container_name
            }

        except ContainerError as e:
            logger.error(f"容器执行错误: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
        except asyncio.TimeoutError:
            logger.warning(f"执行超时: {skill.skill_id}")
            await self._cleanup_container(container_name)
            return {
                "task_id": task_id,
                "status": "timeout",
                "error": f"执行超时（{timeout}秒）"
            }
        except Exception as e:
            logger.error(f"执行失败: {e}")
            return {
                "task_id": task_id,
                "status": "error",
                "error": str(e)
            }
        finally:
            # 清理容器
            await self._cleanup_container(container_name)

    async def _download_code(self, code_url: str) -> str:
        """
        从 MinIO 下载代码

        Args:
            code_url: MinIO 对象 URL

        Returns:
            解码后的代码
        """
        # TODO: 实现从 MinIO 下载
        # 这里先返回空字符串，后续集成 MinIO
        logger.warning("MinIO 集成待实现，使用本地代码")
        return ""

    def _build_command(self, language: SkillLanguage, inputs: Dict[str, Any]) -> list:
        """
        构建执行命令

        Args:
            language: 编程语言
            inputs: 输入参数

        Returns:
            命令列表
        """
        import json

        if language == SkillLanguage.PYTHON:
            # Python: 将输入作为 JSON 参数传递
            inputs_json = json.dumps(inputs)
            return [
                "python",
                "-c",
                f"import sys, json; inputs = json.loads('{inputs_json}'); "
                f"exec(open('/app/skill.py').read(), globals())"
            ]
        elif language == SkillLanguage.TYPESCRIPT:
            # TypeScript: 使用 ts-node
            inputs_json = json.dumps(inputs)
            return [
                "npx",
                "-y",
                "ts-node",
                "-e",
                f"const inputs = JSON.parse('{inputs_json}'); "
                f"eval(require('fs').readFileSync('/app/skill.ts', 'utf8'));"
            ]
        elif language == SkillLanguage.GO:
            # Go: 编译并运行
            return [
                "sh",
                "-c",
                f"echo '{json.dumps(inputs)}' > /app/inputs.json && "
                f"go run /app/skill.go"
            ]
        else:
            raise ValueError(f"不支持的语言: {language}")

    def _run_container(
        self,
        container_name: str,
        image: str,
        code: str,
        command: list,
        timeout: int
    ) -> Dict[str, Any]:
        """
        运行容器

        Args:
            container_name: 容器名称
            image: 镜像名称
            code: 代码内容
            command: 执行命令
            timeout: 超时时间

        Returns:
            执行结果
        """
        try:
            # 拉取镜像（如果不存在）
            try:
                self.client.images.get(image)
            except ImageNotFound:
                logger.info(f"拉取镜像: {image}")
                self.client.images.pull(image)

            # 创建并启动容器
            container = self.client.containers.run(
                image=image,
                name=container_name,
                command=command,
                detach=False,
                remove=False,
                mem_limit="512m",
                cpu_shares=512,
                network_disabled=True,  # 禁用网络以提高安全性
                environment={
                    "WISHUB_SKILL": "true"
                }
            )

            # 获取输出
            logs = container.logs(stdout=True, stderr=True).decode('utf-8')

            return {
                "stdout": logs,
                "exit_code": container.attrs['State']['ExitCode']
            }

        finally:
            # 确保容器被清理
            try:
                container = self.client.containers.get(container_name)
                container.remove(force=True)
            except:
                pass

    async def _cleanup_container(self, container_name: str):
        """清理容器"""
        try:
            await asyncio.to_thread(
                self.client.containers.get(container_name).remove,
                force=True
            )
        except:
            pass

    async def health_check(self) -> bool:
        """检查运行时引擎健康状态"""
        try:
            self.client.ping()
            return True
        except DockerException as e:
            logger.error(f"Docker 健康检查失败: {e}")
            return False


# 全局运行时引擎实例
runtime_engine = RuntimeEngine()
