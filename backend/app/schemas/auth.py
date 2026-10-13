from typing import Optional
from pydantic import BaseModel, Field, ConfigDict


class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    username: str
    role: str
    hospital_id: Optional[str] = None


class LoginResponse(BaseModel):
    user: UserOut
    redirect_to: str


class MeResponse(BaseModel):
    user: UserOut
    redirect_to: str
