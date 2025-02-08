from fastapi import Request, Response, status
from fastapi.responses import ORJSONResponse
from pydantic import BaseModel, Field

class CommonResponse(BaseModel):
    message: str = Field(...)


async def general_exception_handler(req: Request, exc: Exception) -> Response:
    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=CommonResponse(message= "error").model_dump()
    )