"""
Prometheus 指标收集
"""
from prometheus_client import Counter, Histogram, Gauge, Info
from prometheus_fastapi_instrumentator import Instrumentator
from fastapi import FastAPI

# API 请求指标
http_requests_total = Counter(
    "wishub_skill_http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)

# API 请求延迟
http_request_duration_seconds = Histogram(
    "wishub_skill_http_request_duration_seconds",
    "HTTP request latency",
    ["method", "endpoint"]
)

# Skill 调用指标
skill_invocations_total = Counter(
    "wishub_skill_invocations_total",
    "Total skill invocations",
    ["skill_id", "language", "status"]
)

# Skill 调用延迟
skill_invocation_duration_seconds = Histogram(
    "wishub_skill_invocation_duration_seconds",
    "Skill invocation latency",
    ["skill_id", "language"]
)

# Skill 注册指标
skill_registrations_total = Counter(
    "wishub_skill_registrations_total",
    "Total skill registrations",
    ["language", "status"]
)

# Docker 容器指标
docker_containers_active = Gauge(
    "wishub_skill_docker_containers_active",
    "Active Docker containers"
)

docker_containers_total = Counter(
    "wishub_skill_docker_containers_total",
    "Total Docker containers created"
)

# 数据库指标
db_query_duration_seconds = Histogram(
    "wishub_skill_db_query_duration_seconds",
    "Database query latency",
    ["operation"]
)

# 缓存指标
cache_operations_total = Counter(
    "wishub_skill_cache_operations_total",
    "Total cache operations",
    ["operation", "status"]
)

# 存储指标
storage_operations_total = Counter(
    "wishub_skill_storage_operations_total",
    "Total storage operations",
    ["operation", "status"]
)

# Elasticsearch 指标
es_query_duration_seconds = Histogram(
    "wishub_skill_es_query_duration_seconds",
    "Elasticsearch query latency",
    ["index"]
)

# 连接状态指标
postgres_connection_status = Gauge(
    "wishub_skill_postgres_connection_status",
    "PostgreSQL connection status (1=connected, 0=disconnected)"
)

minio_connection_status = Gauge(
    "wishub_skill_minio_connection_status",
    "MinIO connection status (1=connected, 0=disconnected)"
)

elasticsearch_connection_status = Gauge(
    "wishub_skill_elasticsearch_connection_status",
    "Elasticsearch connection status (1=connected, 0=disconnected)"
)

redis_connection_status = Gauge(
    "wishub_skill_redis_connection_status",
    "Redis connection status (1=connected, 0=disconnected)"
)

docker_connection_status = Gauge(
    "wishub_skill_docker_connection_status",
    "Docker connection status (1=connected, 0=disconnected)"
)

# 应用信息
app_info = Info(
    "wishub_skill_app_info",
    "Application information"
)


def setup_metrics(app: FastAPI) -> Instrumentator:
    """
    设置 Prometheus 指标收集

    Args:
        app: FastAPI 应用实例

    Returns:
        Instrumentator 实例
    """
    # 配置 FastAPI Instrumentator
    instrumentator = Instrumentator(
        should_group_status_codes=False,
        should_ignore_untemplated=True,
        should_instrument_requests_inprogress=True,
        should_instrument_requests=True,
        excluded_handlers=["/metrics", "/health", "/"],
        env_var_name="ENABLE_METRICS",
        inprogress_name="wishub_skill_http_requests_inprogress",
        inprogress_labels=True,
    )

    instrumentator.instrument(app)

    return instrumentator


def record_skill_invocation(skill_id: str, language: str, status: str,
                           duration: float) -> None:
    """
    记录 Skill 调用指标

    Args:
        skill_id: Skill ID
        language: 编程语言
        status: 调用状态
        duration: 调用耗时（秒）
    """
    skill_invocations_total.labels(
        skill_id=skill_id,
        language=language,
        status=status
    ).inc()
    skill_invocation_duration_seconds.labels(
        skill_id=skill_id,
        language=language
    ).observe(duration)


def record_skill_registration(language: str, status: str) -> None:
    """
    记录 Skill 注册指标

    Args:
        language: 编程语言
        status: 注册状态
    """
    skill_registrations_total.labels(language=language, status=status).inc()


def update_docker_containers(active_count: int) -> None:
    """
    更新 Docker 容器计数

    Args:
        active_count: 活跃容器数
    """
    docker_containers_active.set(active_count)


def increment_docker_containers() -> None:
    """增加 Docker 容器计数"""
    docker_containers_total.inc()


def record_cache_operation(operation: str, status: str) -> None:
    """
    记录缓存操作指标

    Args:
        operation: 操作类型
        status: 操作状态
    """
    cache_operations_total.labels(operation=operation, status=status).inc()


def record_storage_operation(operation: str, status: str) -> None:
    """
    记录存储操作指标

    Args:
        operation: 操作类型
        status: 操作状态
    """
    storage_operations_total.labels(operation=operation, status=status).inc()


def update_connection_status(service: str, connected: bool) -> None:
    """
    更新服务连接状态

    Args:
        service: 服务名称 (postgres, minio, elasticsearch, redis, docker)
        connected: 是否连接
    """
    status_gauge = {
        "postgres": postgres_connection_status,
        "minio": minio_connection_status,
        "elasticsearch": elasticsearch_connection_status,
        "redis": redis_connection_status,
        "docker": docker_connection_status,
    }.get(service)

    if status_gauge:
        status_gauge.set(1 if connected else 0)


def set_app_info(version: str) -> None:
    """
    设置应用信息

    Args:
        version: 应用版本
    """
    app_info.info({
        "name": "wishub-skill",
        "version": version
    })
