from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class AdminUserRead(BaseModel):
    id: int
    phone: str
    email: EmailStr
    is_admin: bool
    created_at: datetime
    orders_count: int
    total_spent: float
    last_order_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
