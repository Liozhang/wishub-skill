"""
Routes Package
"""
from .skill_register import router as register_router
from .skill_invoke import router as invoke_router
from .skill_discovery import router as discovery_router
from .skill_orchestration import router as orchestration_router

__all__ = [
    "register_router",
    "invoke_router",
    "discovery_router",
    "orchestration_router",
]
