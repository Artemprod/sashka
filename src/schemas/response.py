from typing import Annotated, Optional, List, Union

from pydantic import BaseModel, Field

from src.schemas.user import UserDTOQueue


class SuccessResponse(BaseModel):
    status: str = "success"
    data: List["UserDTOQueue"]


class ErrorResponse(BaseModel):
    status: str = "error"
    error_message: str

class ResponseModel(BaseModel):
    response: Union[SuccessResponse, ErrorResponse]

SuccessResponse.model_rebuild()
ErrorResponse.model_rebuild()
ResponseModel.model_rebuild()
UserDTOQueue.model_rebuild()