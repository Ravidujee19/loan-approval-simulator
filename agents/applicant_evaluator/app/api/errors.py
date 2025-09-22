# standardized error schema & handlers

from fastapi import Request
from fastapi.responses import JSONResponse


def error_response(code: str, message: str, status: int = 400, details: dict | None = None):
    payload = {"error": {"code": code, "message": message, "details": details or {}}}
    return JSONResponse(status_code=status, content=payload)


async def http_422_handler(request: Request, exc):
    return error_response("validation_error", "Invalid request", 422, {"detail": exc.errors()})
