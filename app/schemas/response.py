from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    data: T | None = None
    message: str
    status: Literal["success", "error"]

    @classmethod
    def success(cls, data: T, message: str = "Success") -> "APIResponse[T]":
        return cls(data=data, message=message, status="success")

    @classmethod
    def error(cls, message: str) -> "APIResponse[None]":
        return cls(data=None, message=message, status="error")
