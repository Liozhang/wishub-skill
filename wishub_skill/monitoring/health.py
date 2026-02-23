"""
健康检查模块
"""
from enum import Enum
from typing import Dict, Any
import httpx

from wishub_skill.monitoring.metrics import update_connection_status
from wishub_skill.monitoring.logging_config import get_logger

logger = get_logger(__name__)


class HealthStatus(str, Enum):
    """健康状态"""
    HEALTHY = "healthy"
    UNHEALTHY = "unhealthy"
    DEGRADED = "degraded"


class DependencyHealth:
    """依赖服务健康状态"""

    def __init__(self, name: str, status: HealthStatus,
                 latency_ms: float = 0, message: str = ""):
        self.name = name
        self.status = status
        self.latency_ms = latency_ms
        self.message = message

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "message": self.message
        }


async def check_postgres(db_session) -> DependencyHealth:
    """
    检查 PostgreSQL 健康状态

    Args:
        db_session: 数据库会话

    Returns:
        DependencyHealth 实例
    """
    import time

    start_time = time.time()
    try:
        # 执行简单查询
        result = await db_session.execute("SELECT 1")
        result.fetchone()
        latency_ms = (time.time() - start_time) * 1000

        update_connection_status("postgres", True)
        logger.info("PostgreSQL health check passed", latency_ms=latency_ms)

        return DependencyHealth(
            name="postgres",
            status=HealthStatus.HEALTHY,
            latency_ms=latency_ms
        )
    except Exception as e:
        update_connection_status("postgres", False)
        logger.error("PostgreSQL health check failed", error=str(e))

        return DependencyHealth(
            name="postgres",
            status=HealthStatus.UNHEALTHY,
            message=str(e)
        )


async def check_minio(minio_client, bucket_name: str) -> DependencyHealth:
    """
    检查 MinIO 健康状态

    Args:
        minio_client: MinIO 客户端
        bucket_name: 存储桶名称

    Returns:
        DependencyHealth 实例
    """
    import time

    start_time = time.time()
    try:
        # 检查存储桶是否存在
        minio_client.bucket_exists(bucket_name)
        latency_ms = (time.time() - start_time) * 1000

        update_connection_status("minio", True)
        logger.info("MinIO health check passed", latency_ms=latency_ms)

        return DependencyHealth(
            name="minio",
            status=HealthStatus.HEALTHY,
            latency_ms=latency_ms
        )
    except Exception as e:
        update_connection_status("minio", False)
        logger.error("MinIO health check failed", error=str(e))

        return DependencyHealth(
            name="minio",
            status=HealthStatus.UNHEALTHY,
            message=str(e)
        )


async def check_elasticsearch(es_client, index: str) -> DependencyHealth:
    """
    检查 Elasticsearch 健康状态

    Args:
        es_client: Elasticsearch 客户端
        index: 索引名称

    Returns:
        DependencyHealth 实例
    """
    import time

    start_time = time.time()
    try:
        # 检查集群健康状态
        health = es_client.cluster.health()
        latency_ms = (time.time() - start_time) * 1000

        if health["status"] in ("green", "yellow"):
            update_connection_status("elasticsearch", True)
            logger.info("Elasticsearch health check passed",
                       status=health["status"], latency_ms=latency_ms)

            return DependencyHealth(
                name="elasticsearch",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms
            )
        else:
            update_connection_status("elasticsearch", True)
            logger.warning("Elasticsearch health degraded",
                          status=health["status"])

            return DependencyHealth(
                name="elasticsearch",
                status=HealthStatus.DEGRADED,
                latency_ms=latency_ms,
                message=f"Cluster status: {health['status']}"
            )
    except Exception as e:
        update_connection_status("elasticsearch", False)
        logger.error("Elasticsearch health check failed", error=str(e))

        return DependencyHealth(
            name="elasticsearch",
            status=HealthStatus.UNHEALTHY,
            message=str(e)
        )


async def check_redis(redis_client) -> DependencyHealth:
    """
    检查 Redis 健康状态

    Args:
        redis_client: Redis 客户端

    Returns:
        DependencyHealth 实例
    """
    import time

    start_time = time.time()
    try:
        # 执行 PING 命令
        await redis_client.ping()
        latency_ms = (time.time() - start_time) * 1000

        update_connection_status("redis", True)
        logger.info("Redis health check passed", latency_ms=latency_ms)

        return DependencyHealth(
            name="redis",
            status=HealthStatus.HEALTHY,
            latency_ms=latency_ms
        )
    except Exception as e:
        update_connection_status("redis", False)
        logger.error("Redis health check failed", error=str(e))

        return DependencyHealth(
            name="redis",
            status=HealthStatus.UNHEALTHY,
            message=str(e)
        )


async def check_docker(docker_client) -> DependencyHealth:
    """
    检查 Docker 健康状态

    Args:
        docker_client: Docker 客户端

    Returns:
        DependencyHealth 实例
    """
    import time

    start_time = time.time()
    try:
        # 检查 Docker 版本
        docker_client.version()
        latency_ms = (time.time() - start_time) * 1000

        update_connection_status("docker", True)
        logger.info("Docker health check passed", latency_ms=latency_ms)

        return DependencyHealth(
            name="docker",
            status=HealthStatus.HEALTHY,
            latency_ms=latency_ms
        )
    except Exception as e:
        update_connection_status("docker", False)
        logger.error("Docker health check failed", error=str(e))

        return DependencyHealth(
            name="docker",
            status=HealthStatus.UNHEALTHY,
            message=str(e)
        )


async def perform_health_checks(
    db_session,
    minio_client,
    minio_bucket: str,
    es_client,
    es_index: str,
    redis_client,
    docker_client
) -> Dict[str, Dict[str, Any]]:
    """
    执行所有健康检查

    Args:
        db_session: 数据库会话
        minio_client: MinIO 客户端
        minio_bucket: MinIO 存储桶名称
        es_client: Elasticsearch 客户端
        es_index: Elasticsearch 索引名称
        redis_client: Redis 客户端
        docker_client: Docker 客户端

    Returns:
        健康检查结果字典
    """
    logger.info("starting_health_checks")

    results = {}

    # 检查 PostgreSQL
    postgres_health = await check_postgres(db_session)
    results[postgres_health.name] = postgres_health.to_dict()

    # 检查 MinIO
    if minio_client:
        minio_health = await check_minio(minio_client, minio_bucket)
        results[minio_health.name] = minio_health.to_dict()

    # 检查 Elasticsearch
    if es_client:
        es_health = await check_elasticsearch(es_client, es_index)
        results[es_health.name] = es_health.to_dict()

    # 检查 Redis
    if redis_client:
        redis_health = await check_redis(redis_client)
        results[redis_health.name] = redis_health.to_dict()

    # 检查 Docker
    if docker_client:
        docker_health = await check_docker(docker_client)
        results[docker_health.name] = docker_health.to_dict()

    # 确定整体健康状态
    all_healthy = all(
        dep["status"] == HealthStatus.HEALTHY.value
        for dep in results.values()
    )

    if all_healthy:
        logger.info("all_health_checks_passed")
    else:
        logger.warning("some_health_checks_failed", results=results)

    return results


def get_overall_status(dependencies: Dict[str, Dict[str, Any]]) -> HealthStatus:
    """
    获取整体健康状态

    Args:
        dependencies: 依赖服务健康检查结果

    Returns:
        整体健康状态
    """
    statuses = [dep["status"] for dep in dependencies.values()]

    if all(s == HealthStatus.HEALTHY.value for s in statuses):
        return HealthStatus.HEALTHY
    elif any(s == HealthStatus.UNHEALTHY.value for s in statuses):
        return HealthStatus.UNHEALTHY
    else:
        return HealthStatus.DEGRADED
