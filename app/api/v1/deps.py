"""Dependency injection for API endpoints."""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, status

from app.core.security import verify_api_key, verify_token
from app.memory import memory_manager
from app.memory.manager import MemoryManager


async def get_api_key(x_api_key: Annotated[str | None, Header()] = None) -> str:
    """Validate API key from header."""
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required",
        )
    if not verify_api_key(x_api_key):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API key",
        )
    return x_api_key


async def get_current_user(authorization: Annotated[str | None, Header()] = None) -> dict:
    """Extract and validate JWT token from Authorization header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Bearer token required",
        )
    token = authorization.replace("Bearer ", "")
    try:
        payload = verify_token(token)
        return payload
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )


def get_memory_manager() -> MemoryManager:
    """Get memory manager instance."""
    return memory_manager


# Type aliases for dependency injection
ApiKeyDep = Annotated[str, Depends(get_api_key)]
CurrentUserDep = Annotated[dict, Depends(get_current_user)]
MemoryManagerDep = Annotated[MemoryManager, Depends(get_memory_manager)]
