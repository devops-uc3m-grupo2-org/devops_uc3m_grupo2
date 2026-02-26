from pydantic import BaseModel, EmailStr
from pydantic import ConfigDict


class UserCreate(BaseModel):
    name: str
    email: EmailStr


class UserRead(BaseModel):
    id: int
    name: str
    email: EmailStr

    model_config = ConfigDict(from_attributes=True)
