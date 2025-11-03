"""Middleware configuration for the API"""
from fastapi import Request
from fastapi.responses import JSONResponse


ALLOWED_LIST = ["/"]
SECRET_TOKEN = "my-secret-token"


async def token_validation_middleware(request: Request, call_next):
    """
    Validate token header for protected endpoints

    Args:
        request: FastAPI request object
        call_next: Next middleware/handler in the chain

    Returns:
        Response from next handler or 401 error
    """
    if request.url.path in ALLOWED_LIST:
        return await call_next(request)

    token = request.headers.get("token")
    if token != SECRET_TOKEN:
        return JSONResponse(
            status_code=401,
            content={"detail": "Invalid or missing token"}
        )

    return await call_next(request)
