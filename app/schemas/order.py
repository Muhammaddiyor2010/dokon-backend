from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CheckoutItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0, le=100)


class CheckoutRequest(BaseModel):
    customer_name: str = Field(min_length=2, max_length=120)
    customer_phone: str = Field(min_length=9, max_length=15)
    location: str = Field(min_length=5, max_length=255)
    items: list[CheckoutItem] = Field(min_length=1)


class OrderItemRead(BaseModel):
    product_id: int
    quantity: int
    price: float

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    customer_name: str
    customer_phone: str
    location: str
    total_price: float
    status: str
    created_at: datetime
    items: list[OrderItemRead]

    model_config = ConfigDict(from_attributes=True)
