from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    slug: str = Field(min_length=2, max_length=120)
    name_uz: str = Field(min_length=2, max_length=120)
    name_en: str = Field(min_length=2, max_length=120)
    name_ru: str = Field(min_length=2, max_length=120)
    description_uz: str = ""
    description_en: str = ""
    description_ru: str = ""


class CategoryCreate(CategoryBase):
    pass


class CategoryRead(CategoryBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
