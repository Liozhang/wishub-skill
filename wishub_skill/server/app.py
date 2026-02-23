"""
WisHub Skill Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from contextlib import asynccontextmanager
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from wishub_skill.config import settings
from wishub_skill.protocol.models import HealthCheckResponse
from wishub_skill.server.routes import (
    register_router,
    invoke_router,
    discovery_router,
    orchestration_router
)
from wishub_skill.server.db_session import init_db
from wishub_skill.monitoring.logging_config import setup_logging, get_logger
from wishub_skill.monitoring.metrics import setup_metrics, set_app_info
from wishub_skill.monitoring.health import perform_health_checks, get_overall_status

# 配置结构化日志
setup_logging(
    log_level=settings.LOG_LEVEL,
    json_format=settings.APP_ENV != "development"
)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info(
        "starting",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        environment=settings.APP_ENV
    )

    # 设置应用信息指标
    set_app_info(settings.APP_VERSION)

    # 初始化数据库
    try:
        logger.info("initializing_database")
        await init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_initialization_failed", error=str(e))

    # 检查运行时引擎
    from wishub_skill.server.runtime import runtime_engine
    if await runtime_engine.health_check():
        logger.info("runtime_engine_healthy")
    else:
        logger.warning("runtime_engine_unavailable")

    yield

    # 关闭
    logger.info("shutting_down", app_name=settings.APP_NAME)


# 创建 FastAPI 应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="WisHub Skill Protocol Server - 技能注册、发现、调用和编排",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 设置 Prometheus 指标
setup_metrics(app)

# 注册路由
app.include_router(register_router, prefix=settings.API_PREFIX)
app.include_router(invoke_router, prefix=settings.API_PREFIX)
app.include_router(discovery_router, prefix=settings.API_PREFIX)
app.include_router(orchestration_router, prefix=settings.API_PREFIX)


@app.get("/", tags=["Root"])
async def root():
    """根路径"""
    return {
        "name": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "status": "running"
    }


@app.get("/health", response_model=HealthCheckResponse, tags=["Health"])
async def health_check():
    """
    健康检查

    检查依赖服务的健康状态，包括：
    - PostgreSQL 数据库
    - MinIO 对象存储
    - Elasticsearch 搜索引擎
    - Redis 缓存
    - Docker 运行时
    """
    # 获取各服务客户端
    from wishub_skill.server.db_session import get_async_session
    from wishub_skill.server.storage import get_minio_client
    from wishub_skill.server.search import get_es_client
    from wishub_skill.server.cache import get_redis_client
    from wishub_skill.server.runtime import get_docker_client

    # 执行健康检查
    dependencies = await perform_health_checks(
        db_session=await get_async_session().__anext__(),
        minio_client=get_minio_client(),
        minio_bucket=settings.MINIO_BUCKET,
        es_client=get_es_client(),
        es_index=settings.ELASTICSEARCH_INDEX,
        redis_client=get_redis_client(),
        docker_client=get_docker_client()
    )

    # 获取整体状态
    overall_status = get_overall_status(dependencies)

    return HealthCheckResponse(
        status=overall_status.value,
        version=settings.APP_VERSION,
        dependencies=dependencies
    )


@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """
    Prometheus 指标端点

    提供以下指标：
    - HTTP 请求计数和延迟
    - Skill 调用计数和延迟
    - Skill 注册统计
    - Docker 容器统计
    - 数据库查询延迟
    - 缓存和存储操作统计
    - Elasticsearch 查询延迟
    - 各服务连接状态
    - 应用信息
    """
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.get(f"{settings.API_PREFIX}/openapi.json", tags=["API"])
async def get_openapi():
    """获取 OpenAPI 规范"""
    return app.openapi()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG
    )
