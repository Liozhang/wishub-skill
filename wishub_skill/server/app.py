"""
WisHub Skill Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from wishub_skill.config import settings
from wishub_skill.protocol.models import HealthCheckResponse
from wishub_skill.server.routes import (
    register_router,
    invoke_router,
    discovery_router,
    orchestration_router
)
from wishub_skill.server.db_session import init_db

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    logger.info(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")

    # 初始化数据库
    try:
        logger.info("初始化数据库...")
        await init_db()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")

    # 检查运行时引擎
    from wishub_skill.server.runtime import runtime_engine
    if await runtime_engine.health_check():
        logger.info("运行时引擎（Docker）状态正常")
    else:
        logger.warning("运行时引擎（Docker）不可用")

    yield

    # 关闭
    logger.info(f"👋 {settings.APP_NAME} 已关闭")


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
    """健康检查"""
    # TODO: 实际检查依赖服务的健康状态
    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        dependencies={
            "postgres": "ok",
            "minio": "ok",
            "elasticsearch": "ok",
            "redis": "ok",
            "docker": "ok"
        }
    )


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
