"""Authentication middleware."""

from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.security import verify_api_key


class APIKeyMiddleware(BaseHTTPMiddleware):
    """Middleware to validate API key on protected routes."""

    PROTECTED_PREFIXES = ["/api/v1/memory", "/api/v1/search", "/api/v1/patient"]
    EXCLUDED_PATHS = ["/", "/docs", "/redoc", "/openapi.json", "/api/v1/health"]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip auth for excluded paths
        if any(path.startswith(exc) for exc in self.EXCLUDED_PATHS):
            return await call_next(request)

        # Check if path needs protection
        if any(path.startswith(prefix) for prefix in self.PROTECTED_PREFIXES):
            api_key = request.headers.get("X-API-Key")
            if not api_key or not verify_api_key(api_key):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or missing API key",
                )

        return await call_next(request)
