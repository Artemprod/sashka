from typing import List
from typing import Union

from pydantic import BaseModel

from src.schemas.service.user import UserDTOQueue


class SuccessResponse(BaseModel):
    status: str = "success"
    data: List["UserDTOQueue"]

    class Config:
        from_attributes = True


class ErrorResponse(BaseModel):
    status: str = "error"
    error_message: str

    class Config:
        from_attributes = True


class ResponseModel(BaseModel):
    response: Union[SuccessResponse, ErrorResponse]

    class Config:
        from_attributes = True


ResponseModel.model_rebuild()
