"""
WisHub Skill Main Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from wishub_skill.config import settings
from wishub_skill.protocol.models import HealthCheckResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动
    print(f"🚀 {settings.APP_NAME} v{settings.APP_VERSION} 启动中...")
    yield
    # 关闭
    print(f"👋 {settings.APP_NAME} 已关闭")


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
    return HealthCheckResponse(
        status="healthy",
        version=settings.APP_VERSION,
        dependencies={
            "postgres": "ok",
            "minio": "ok",
            "elasticsearch": "ok",
            "redis": "ok"
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
