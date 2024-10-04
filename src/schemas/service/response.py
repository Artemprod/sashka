from typing import List, Union

from pydantic import BaseModel




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

