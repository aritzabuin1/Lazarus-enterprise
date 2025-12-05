from fastapi import Request, status
from fastapi.responses import JSONResponse
from app.logger import logger

class AppError(Exception):
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code

async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, AppError):
        logger.warning(f"AppError: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"error": exc.message}
        )
    
    logger.error(f"Unhandled Exception: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal Server Error"}
    )
