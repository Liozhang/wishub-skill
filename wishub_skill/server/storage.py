"""
Storage Client (MinIO)
"""
import logging
import base64
from typing import Optional
from minio import Minio
from minio.error import S3Error

from wishub_skill.config import settings

logger = logging.getLogger(__name__)


class StorageClient:
    """MinIO 存储客户端"""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        access_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        bucket_name: Optional[str] = None,
        secure: Optional[bool] = None,
        lazy_init: bool = False
    ):
        """
        初始化 MinIO 客户端

        Args:
            endpoint: MinIO 端点
            access_key: 访问密钥
            secret_key: 密钥
            bucket_name: 存储桶名称
            secure: 是否使用 HTTPS
            lazy_init: 是否延迟初始化（用于测试）
        """
        self.endpoint = endpoint or settings.MINIO_ENDPOINT
        self.access_key = access_key or settings.MINIO_ACCESS_KEY
        self.secret_key = secret_key or settings.MINIO_SECRET_KEY
        self.bucket_name = bucket_name or settings.MINIO_BUCKET
        self.secure = secure if secure is not None else settings.MINIO_SECURE

        self.client = Minio(
            self.endpoint,
            access_key=self.access_key,
            secret_key=self.secret_key,
            secure=self.secure
        )

        # 只有在非延迟初始化模式下才确保存储桶存在
        if not lazy_init:
            self._ensure_bucket()

    def _ensure_bucket(self):
        """确保存储桶存在"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                logger.info(f"已创建存储桶: {self.bucket_name}")
        except S3Error as e:
            logger.error(f"创建存储桶失败: {e}")
            raise

    def upload_code(
        self,
        skill_id: str,
        version: str,
        code_b64: str
    ) -> str:
        """
        上传代码到 MinIO

        Args:
            skill_id: Skill ID
            version: 版本号
            code_b64: Base64 编码的代码

        Returns:
            代码文件 URL
        """
        try:
            # 解码 Base64
            code_bytes = base64.b64decode(code_b64)

            # 构建对象名称
            object_name = f"{skill_id}/{version}/skill.py"

            # 上传文件
            self.client.put_object(
                bucket_name=self.bucket_name,
                object_name=object_name,
                data=code_bytes,
                length=len(code_bytes),
                content_type="text/x-python"
            )

            # 构建下载 URL
            url = f"http://{self.endpoint}/{self.bucket_name}/{object_name}"
            logger.info(f"代码上传成功: {url}")

            return url

        except Exception as e:
            logger.error(f"代码上传失败: {e}")
            raise RuntimeError(f"代码上传失败: {str(e)}")

    def download_code(self, skill_id: str, version: str) -> bytes:
        """
        从 MinIO 下载代码

        Args:
            skill_id: Skill ID
            version: 版本号

        Returns:
            代码字节
        """
        try:
            object_name = f"{skill_id}/{version}/skill.py"

            response = self.client.get_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )

            code = response.read()
            logger.info(f"代码下载成功: {skill_id}/{version}")

            return code

        except S3Error as e:
            logger.error(f"代码下载失败: {e}")
            raise RuntimeError(f"代码下载失败: {str(e)}")

    def delete_code(self, skill_id: str, version: str):
        """
        从 MinIO 删除代码

        Args:
            skill_id: Skill ID
            version: 版本号
        """
        try:
            object_name = f"{skill_id}/{version}/skill.py"

            self.client.remove_object(
                bucket_name=self.bucket_name,
                object_name=object_name
            )

            logger.info(f"代码删除成功: {skill_id}/{version}")

        except S3Error as e:
            logger.warning(f"代码删除失败: {e}")


# 全局存储客户端实例（延迟初始化）
storage_client = StorageClient(lazy_init=True)
