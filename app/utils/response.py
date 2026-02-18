from typing import Any, Optional
from fastapi.responses import JSONResponse
from datetime import datetime

def success_response(data: Any = None, message: str = "Success") -> JSONResponse:
    return JSONResponse(
        status_code=200,
        content={
            "success": True,
            "data": data,
            "message": message,
            "timestamp": datetime.now().isoformat()
        }
    )

def error_response(message: str, code: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=code,
        content={
            "success": False,
            "error": message,
            "code": code,
            "timestamp": datetime.now().isoformat()
        }
    )
