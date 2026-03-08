from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.category import CategoryRead


class ProductBase(BaseModel):
    category_id: int
    name_uz: str = Field(min_length=2, max_length=150)
    name_en: str = Field(min_length=2, max_length=150)
    name_ru: str = Field(min_length=2, max_length=150)
    description_uz: str = Field(min_length=3)
    description_en: str = Field(min_length=3)
    description_ru: str = Field(min_length=3)
    price: float = Field(gt=0)
    image_url: str = Field(min_length=5, max_length=500)
    stock: int = Field(ge=0)


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    created_at: datetime
    category: CategoryRead

    model_config = ConfigDict(from_attributes=True)
