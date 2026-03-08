from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class UserRead(BaseModel):
    id: int
    phone: str
    email: EmailStr
    is_admin: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
